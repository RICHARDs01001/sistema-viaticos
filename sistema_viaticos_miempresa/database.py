# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""database.py — Persistencia del sistema de viáticos.

Trabaja igual con la base local (SQLite, carpeta `data`) o con la base central
del servidor (PostgreSQL). Toda la conexión pasa por `bd.py`, así que la lógica
de la aplicación no cambia.
"""
import binascii
import hashlib
import hmac
import json
import os
import re
import sys
import sqlite3
from datetime import datetime as _fechahora, time, timedelta
from pathlib import Path
from time import monotonic as _reloj     # reloj del sistema (no confundir con `time`)

import bd
import configuracion as cfg

# --------------------------------------------------------------- memoria corta
# Los catálogos (empleados, clientes, vehículos, provincias, cantones y rutas) y los
# valores de Parámetros se piden **muchísimas** veces por pantalla: cada tecleo del
# formulario necesita los parámetros y los km del cantón. Antes eso era una consulta (y
# una conexión) cada vez, y contra el servidor central se sentía la pausa.
# Ahora esos datos se guardan unos segundos en memoria: la pantalla va al instante y la
# base central recibe muchas menos consultas. Todo lo que se **graba** desde el sistema
# borra lo guardado (ver `olvidar_cache`), así que nunca se ve un dato viejo propio.
_SEGUNDOS_MEMORIA = 30                  # cuánto se recuerdan los catálogos y los parámetros
_MEMORIA = {}


def _memoria(clave, segundos, fabrica):
    """Valor guardado en memoria; se vuelve a leer cuando pasa el tiempo indicado."""
    ahora = _reloj()
    guardado = _MEMORIA.get(clave)
    if guardado is not None and (segundos is None or ahora - guardado[0] < segundos):
        return guardado[1]
    valor = fabrica()
    _MEMORIA[clave] = (ahora, valor)
    return valor


def olvidar_cache(*claves):
    """Borra lo guardado en memoria (todo, o solo lo que se indique).

    Se llama desde lo que graba en esas tablas, para que el dato nuevo se vea al
    instante y no espere a que pasen los `_SEGUNDOS_MEMORIA`.
    """
    if not claves:
        _MEMORIA.clear()
        return
    for clave in claves:
        if clave.endswith(":"):              # todo lo que empiece por ese texto
            for k in [k for k in _MEMORIA if k.startswith(clave)]:
                del _MEMORIA[k]
        else:
            _MEMORIA.pop(clave, None)


def _copiar(valor):
    """Devuelve una copia de lo guardado, para que nadie lo modifique sin querer."""
    if isinstance(valor, dict):
        return dict(valor)
    if isinstance(valor, list):
        return list(valor)
    return valor

TIPOS_VEHICULO = ["CAMIONETA", "CAMION", "CAMION GRUA", "AUTOMOVIL", "MOTO", "BUS", "OTRO"]

# Km aprox. DESDE CUENCA (ida) hacia cada cantón. Se puede ajustar con set_distancia().
# Versión 8.6: son los **km del documento revisado** («DISTANCIAS DOC.docx», que la
# empresa revisó cantón por cantón); los arma `herramientas\preparar_distancias_doc.py`.
# YANTZAZA queda con los km que la empresa dejó a mano (215). Los seis cantones que el
# documento no trae (CHUMBLÍN, HUAMBI, CUENCA e ISABELA / SAN CRISTÓBAL / SANTA CRUZ)
# conservan los km de siempre.
KM_CUENCA = {
    # AZUAY
    "CUENCA": 10, "GIRÓN": 44, "GUALACEO": 38, "CHORDALEG": 44, "PAUTE": 42, "GUACHAPALA": 49,
    "EL PAN": 61, "SEVILLA DE ORO": 77, "PUCARÁ": 126, "SIGSIG": 62, "OÑA": 102,
    "CHUMBLÍN": 80, "SANTA ISABEL": 77,
    # BOLÍVAR
    "GUARANDA": 272, "CHILLANES": 256, "CHIMBO": 267, "ECHEANDÍA": 298, "SAN MIGUEL": 251,
    "CALUMA": 268, "LAS NAVES": 305,
    # CAÑAR
    "AZOGUES": 32, "BIBLIÁN": 38, "CAÑAR": 68, "EL TAMBO": 76, "LA TRONCAL": 149,
    "SUSCAL": 92, "DÉLEG": 26,
    # CARCHI
    "TULCÁN": 715, "BOLÍVAR": 658, "ESPEJO": 682, "MIRA": 668, "MONTÚFAR": 674,
    "SAN PEDRO DE HUACA": 688,
    # CHIMBORAZO
    "RIOBAMBA": 258, "ALAUSÍ": 169, "CHAMBO": 266, "CHUNCHI": 134, "GUAMOTE": 208,
    "GUANO": 265, "PALLATANGA": 284, "PENIPE": 280, "CUMANDÁ": 198,
    # COTOPAXI
    "LATACUNGA": 358, "LA MANÁ": 485, "PANGUA": 365, "PUJILÍ": 366, "SALCEDO": 344,
    "SAQUISILÍ": 372, "SIGCHOS": 442,
    # EL ORO
    "MACHALA": 168, "ARENILLAS": 216, "BALSAS": 218, "CHILLA": 148, "EL GUABO": 158,
    "HUAQUILLAS": 239, "MARCABELÍ": 228, "PASAJE": 145, "PIÑAS": 175, "PORTOVELO": 172,
    "SANTA ROSA": 189, "ZARUMA": 170,
    # ESMERALDAS
    "ESMERALDAS": 628, "ATACAMES": 658, "MUISNE": 652, "QUININDÉ": 536, "SAN LORENZO": 746,
    "RIOVERDE": 684,
    # GALÁPAGOS
    "SAN CRISTÓBAL": 1000, "ISABELA": 1000, "SANTA CRUZ": 1000,
    # GUAYAS
    "GUAYAQUIL": 196, "ALFREDO BAQUERIZO MORENO": 184, "BALAO": 156, "BALZAR": 328,
    "COLIMES": 284, "DAULE": 238, "DURÁN": 188, "EL EMPALME": 354, "EL TRIUNFO": 136,
    "ISIDRO AYORA": 264, "LOMAS DE SARGENTILLO": 254, "MARCELINO MARIDUEÑA": 152,
    "MILAGRO": 182, "NARANJAL": 124, "NARANJITO": 162, "NOBOL": 234, "PALESTINA": 272,
    "PEDRO CARBO": 282, "PLAYAS": 292, "SALITRE": 242, "SAMBORONDÓN": 212, "SANTA LUCÍA": 256,
    "SIMÓN BOLÍVAR": 176, "YAGUACHI": 178,
    # IMBABURA
    "IBARRA": 588, "ANTONIO ANTE": 574, "COTACACHI": 578, "OTAVALO": 562, "PIMAMPIRO": 632,
    "SAN MIGUEL DE URCUQUÍ": 604,
    # LOJA
    "LOJA": 212, "CALVAS": 315, "CATAMAYO": 236, "CELICA": 346, "CHAGUARPAMBA": 292,
    "ESPÍNDOLA": 364, "GONZANAMÁ": 284, "MACARÁ": 392, "OLMEDO": 256, "PALTAS": 304,
    "PUYANGO": 386, "QUILANGA": 302, "SARAGURO": 142, "SOZORANGA": 354, "ZAPOTILLO": 448,
    # LOS RÍOS
    "BABAHOYO": 232, "BABA": 252, "BUENA FE": 362, "MOCACHE": 342, "MONTALVO": 214,
    "PALENQUE": 322, "PUEBLOVIEJO": 268, "QUEVEDO": 346, "QUINSALOMA": 308, "URDANETA": 265,
    "VENTANAS": 286, "VINCES": 274,
    # MANABÍ
    "PORTOVIEJO": 386, "24 DE MAYO": 358, "CHONE": 445, "EL CARMEN": 464,
    "FLAVIO ALFARO": 488, "JAMA": 552, "JARAMIJÓ": 396, "JIPIJAPA": 334, "JUNÍN": 422,
    "MANTA": 392, "MONTECRISTI": 384, "PAJÁN": 312, "PEDERNALES": 548, "PICHINCHA": 356,
    "ROCAFUERTE": 402, "SAN VICENTE": 445, "SUCRE": 442, "TOSAGUA": 428,
    # MORONA SANTIAGO
    "MACAS": 242, "GUALAQUIZA": 172, "LIMÓN INDANZA": 126, "LOGROÑO": 214, "HUAMBI": 240,
    "PALORA": 354, "SANTIAGO": 168, "SUCÚA": 218, "TAISHA": 322, "TIWINTZA": 224,
    # NAPO
    "TENA": 412, "ARCHIDONA": 422, "CARLOS JULIO AROSEMENA TOLA": 388, "EL CHACO": 524,
    "QUIJOS": 486,
    # ORELLANA
    "FRANCISCO DE ORELLANA": 564, "AGUARICO": 564, "LA JOYA DE LOS SACHAS": 602,
    "LORETO": 512,
    # PASTAZA
    "PUYO": 338, "ARAJUNO": 402, "MERA": 322, "SANTA CLARA": 364,
    # PICHINCHA
    "QUITO": 468, "CAYAMBE": 536, "MEJÍA": 434, "PEDRO MONCAYO": 528,
    "PEDRO VICENTE MALDONADO": 592, "PUERTO QUITO": 618, "RUMIÑAHUI": 454,
    "SAN MIGUEL DE LOS BANCOS": 555,
    # SANTA ELENA
    "SANTA ELENA": 318, "LA LIBERTAD": 323, "SALINAS": 330,
    # SANTO DOMINGO DE LOS TSÁCHILAS
    "SANTO DOMINGO": 374, "LA CONCORDIA": 416,
    # SUCUMBÍOS
    "NUEVA LOJA": 675, "CASCALES": 650, "CUYABENO": 750, "GONZALO PIZARRO": 620,
    "PUTUMAYO": 835, "SHUSHUFINDI": 715, "SUCUMBÍOS": 792,
    # TUNGURAHUA
    "AMBATO": 290, "BAÑOS": 280, "CEVALLOS": 275, "MOCHA": 258, "PATATE": 294, "QUERO": 278,
    "TISALEO": 272,
    # ZAMORA CHINCHIPE
    "ZAMORA": 262, "CENTINELA DEL CÓNDOR": 247, "CHINCHIPE": 370, "EL PANGUI": 205,
    "NANGARITZA": 290, "PALANDA": 338, "YACUAMBI": 196, "YANTZAZA": 215,
}

# Cantones que se agregaron al catálogo **después** de que las bases ya existían (versión
# 8.4): su km de partida, para que las bases que ya estaban creadas —la central y la de
# cada PC— los reciban solos, sin escribirlos a mano. Ver `_reparar_catalogo_cantones`.
DISTANCIAS_NUEVAS = {"YANTZAZA": 215}

# Horas de viaje (solo IDA) desde Cuenca hacia cada destino: **las del documento
# revisado** («DISTANCIAS DOC.docx»). Para cada cantón se mezclan sus dos tiempos —en
# auto y en autobús— y queda el punto medio, redondeado a 5 minutos (versión 8.1);
# YANTZAZA conserva lo que la empresa dejó a mano (215 km · 5 h).
#
# Este diccionario es la semilla: se usa cuando la base todavía no tiene el dato (una
# base nueva, o una PC que no alcanza el Excel que viaja con el programa). Los valores
# se guardan y se editan cantón por cantón en la tabla `distancias` (columna `horas`)
# desde **Parámetros → 🗺️ Provincias y km**, y se pueden cargar en bloque con el Excel
# «TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx» (botón 📥 Importar Excel de esa pestaña).
# Los cantones que no estén aquí estiman su tiempo con los km y la velocidad del
# vehículo (Parámetros → velocidades de viaje).
HORAS_CUENCA = {
    # AZUAY
    "GIRÓN": 1, "GUALACEO": 1, "CHORDALEG": 1.17, "PAUTE": 1.17, "GUACHAPALA": 1.33,
    "EL PAN": 1.58, "SEVILLA DE ORO": 2, "PUCARÁ": 3.25, "SIGSIG": 1.5, "OÑA": 2.17,
    "SANTA ISABEL": 1.75,
    # BOLÍVAR
    "GUARANDA": 6.17, "CHILLANES": 5.75, "CHIMBO": 6, "ECHEANDÍA": 6.83, "SAN MIGUEL": 5.75,
    "CALUMA": 6.33, "LAS NAVES": 7,
    # CAÑAR
    "AZOGUES": 0.67, "BIBLIÁN": 0.83, "CAÑAR": 1.5, "EL TAMBO": 1.67, "LA TRONCAL": 3.33,
    "SUSCAL": 2.25, "DÉLEG": 0.83,
    # CARCHI
    "TULCÁN": 13.75, "BOLÍVAR": 12.67, "ESPEJO": 13.5, "MIRA": 12.83, "MONTÚFAR": 13,
    "SAN PEDRO DE HUACA": 13.25,
    # CHIMBORAZO
    "RIOBAMBA": 5.33, "ALAUSÍ": 3.67, "CHAMBO": 5.67, "CHUNCHI": 2.83, "GUAMOTE": 4.25,
    "GUANO": 5.67, "PALLATANGA": 5.83, "PENIPE": 6, "CUMANDÁ": 4.17,
    # COTOPAXI
    "LATACUNGA": 6.75, "LA MANÁ": 9, "PANGUA": 7.67, "PUJILÍ": 7, "SALCEDO": 6.33,
    "SAQUISILÍ": 7.08, "SIGCHOS": 8.67,
    # EL ORO
    "MACHALA": 3.75, "ARENILLAS": 4.67, "BALSAS": 4.92, "CHILLA": 4.5, "EL GUABO": 3.5,
    "HUAQUILLAS": 5, "MARCABELÍ": 5.17, "PASAJE": 3.17, "PIÑAS": 4.17, "PORTOVELO": 4.33,
    "SANTA ROSA": 4, "ZARUMA": 4.33,
    # ESMERALDAS
    "ESMERALDAS": 11.67, "ATACAMES": 12.42, "MUISNE": 12.67, "QUININDÉ": 9.75,
    "SAN LORENZO": 13.83, "RIOVERDE": 12.83,
    # GUAYAS
    "GUAYAQUIL": 4, "ALFREDO BAQUERIZO MORENO": 3.75, "BALAO": 3.25, "BALZAR": 6.67,
    "COLIMES": 5.83, "DAULE": 4.83, "DURÁN": 3.75, "EL EMPALME": 7.17, "EL TRIUNFO": 2.83,
    "ISIDRO AYORA": 5.33, "LOMAS DE SARGENTILLO": 5.17, "MARCELINO MARIDUEÑA": 3.17,
    "MILAGRO": 3.67, "NARANJAL": 2.67, "NARANJITO": 3.33, "NOBOL": 4.83, "PALESTINA": 5.67,
    "PEDRO CARBO": 5.83, "PLAYAS": 5.5, "SALITRE": 5.08, "SAMBORONDÓN": 4.33,
    "SANTA LUCÍA": 5.25, "SIMÓN BOLÍVAR": 3.67, "YAGUACHI": 3.5,
    # IMBABURA
    "IBARRA": 10.67, "ANTONIO ANTE": 10.33, "COTACACHI": 10.58, "OTAVALO": 10.08,
    "PIMAMPIRO": 11.5, "SAN MIGUEL DE URCUQUÍ": 11.25,
    # LOJA
    "LOJA": 4.25, "CALVAS": 6.67, "CATAMAYO": 4.67, "CELICA": 7.17, "CHAGUARPAMBA": 6,
    "ESPÍNDOLA": 7.92, "GONZANAMÁ": 6, "MACARÁ": 7.83, "OLMEDO": 5.5, "PALTAS": 6.17,
    "PUYANGO": 7.92, "QUILANGA": 6.67, "SARAGURO": 2.67, "SOZORANGA": 7.5, "ZAPOTILLO": 9,
    # LOS RÍOS
    "BABAHOYO": 4.83, "BABA": 5.5, "BUENA FE": 7.33, "MOCACHE": 6.83, "MONTALVO": 4.42,
    "PALENQUE": 6.67, "PUEBLOVIEJO": 5.58, "QUEVEDO": 6.83, "QUINSALOMA": 6.33,
    "URDANETA": 5.67, "VENTANAS": 6, "VINCES": 5.83,
    # MANABÍ
    "PORTOVIEJO": 7.42, "24 DE MAYO": 7, "CHONE": 8.67, "EL CARMEN": 8.83,
    "FLAVIO ALFARO": 9.5, "JAMA": 10.67, "JARAMIJÓ": 7.67, "JIPIJAPA": 6.33, "JUNÍN": 8.17,
    "MANTA": 7.5, "MONTECRISTI": 7.25, "PAJÁN": 5.92, "PEDERNALES": 10.25, "PICHINCHA": 7.25,
    "ROCAFUERTE": 7.83, "SAN VICENTE": 8.83, "SUCRE": 8.58, "TOSAGUA": 8.33,
    # MORONA SANTIAGO
    "MACAS": 6, "GUALAQUIZA": 4.42, "LIMÓN INDANZA": 3.67, "LOGROÑO": 5.5, "PALORA": 8.17,
    "SANTIAGO": 4.67, "SUCÚA": 5.5, "TAISHA": 7.92, "TIWINTZA": 6.33,
    # NAPO
    "TENA": 8.67, "ARCHIDONA": 8.83, "CARLOS JULIO AROSEMENA TOLA": 8.17, "EL CHACO": 11.17,
    "QUIJOS": 10.33,
    # ORELLANA
    "FRANCISCO DE ORELLANA": 12, "AGUARICO": 12.25, "LA JOYA DE LOS SACHAS": 12.83,
    "LORETO": 10.67,
    # PASTAZA
    "PUYO": 6.83, "ARAJUNO": 8.33, "MERA": 6.33, "SANTA CLARA": 7.33,
    # PICHINCHA
    "QUITO": 8.5, "CAYAMBE": 9.83, "MEJÍA": 7.58, "PEDRO MONCAYO": 9.67,
    "PEDRO VICENTE MALDONADO": 11.17, "PUERTO QUITO": 11.67, "RUMIÑAHUI": 8.08,
    "SAN MIGUEL DE LOS BANCOS": 10.42,
    # SANTA ELENA
    "SANTA ELENA": 5.83, "LA LIBERTAD": 6, "SALINAS": 6.17,
    # SANTO DOMINGO DE LOS TSÁCHILAS
    "SANTO DOMINGO": 7, "LA CONCORDIA": 7.83,
    # SUCUMBÍOS
    "NUEVA LOJA": 13.75, "CASCALES": 13.25, "CUYABENO": 15.25, "GONZALO PIZARRO": 12.67,
    "PUTUMAYO": 17.33, "SHUSHUFINDI": 14.67, "SUCUMBÍOS": 16.17,
    # TUNGURAHUA
    "AMBATO": 5.5, "BAÑOS": 5.33, "CEVALLOS": 5.17, "MOCHA": 4.75, "PATATE": 5.67,
    "QUERO": 5.25, "TISALEO": 5.17,
    # ZAMORA CHINCHIPE
    "ZAMORA": 5.33, "CENTINELA DEL CÓNDOR": 5.25, "CHINCHIPE": 9.33, "EL PANGUI": 4.33,
    "NANGARITZA": 6.42, "PALANDA": 7.92, "YACUAMBI": 5, "YANTZAZA": 5,
}
# Nombre anterior (el que usaba q_viaje para estimar la llegada).
HORAS_APROX = HORAS_CUENCA

PROV_CANT = {
    "AZUAY": ["CUENCA", "GIRÓN", "GUALACEO", "CHORDALEG", "PAUTE", "GUACHAPALA",
              "EL PAN", "SEVILLA DE ORO", "PUCARÁ", "SIGSIG", "OÑA", "CHUMBLÍN", "SANTA ISABEL"],
    "BOLÍVAR": ["GUARANDA", "CHILLANES", "CHIMBO", "ECHEANDÍA", "SAN MIGUEL", "CALUMA", "LAS NAVES"],
    "CAÑAR": ["AZOGUES", "BIBLIÁN", "CAÑAR", "EL TAMBO", "LA TRONCAL", "SUSCAL", "DÉLEG"],
    "CARCHI": ["TULCÁN", "BOLÍVAR", "ESPEJO", "MIRA", "MONTÚFAR", "SAN PEDRO DE HUACA"],
    "CHIMBORAZO": ["RIOBAMBA", "ALAUSÍ", "CHAMBO", "CHUNCHI", "GUAMOTE", "GUANO",
                   "PALLATANGA", "PENIPE", "CUMANDÁ"],
    "COTOPAXI": ["LATACUNGA", "LA MANÁ", "PANGUA", "PUJILÍ", "SALCEDO", "SAQUISILÍ", "SIGCHOS"],
    "EL ORO": ["MACHALA", "ARENILLAS", "BALSAS", "CHILLA", "EL GUABO", "HUAQUILLAS",
               "MARCABELÍ", "PASAJE", "PIÑAS", "PORTOVELO", "SANTA ROSA", "ZARUMA"],
    "ESMERALDAS": ["ESMERALDAS", "ATACAMES", "MUISNE", "QUININDÉ", "SAN LORENZO", "RIOVERDE"],
    "GALÁPAGOS": ["SAN CRISTÓBAL", "ISABELA", "SANTA CRUZ"],
    "GUAYAS": ["GUAYAQUIL", "ALFREDO BAQUERIZO MORENO", "BALAO", "BALZAR", "COLIMES", "DAULE",
               "DURÁN", "EL EMPALME", "EL TRIUNFO", "ISIDRO AYORA", "LOMAS DE SARGENTILLO",
               "MARCELINO MARIDUEÑA", "MILAGRO", "NARANJAL", "NARANJITO", "NOBOL", "PALESTINA",
               "PEDRO CARBO", "PLAYAS", "SALITRE", "SAMBORONDÓN", "SANTA LUCÍA",
               "SIMÓN BOLÍVAR", "YAGUACHI"],
    "IMBABURA": ["IBARRA", "ANTONIO ANTE", "COTACACHI", "OTAVALO", "PIMAMPIRO",
                 "SAN MIGUEL DE URCUQUÍ"],
    "LOJA": ["LOJA", "CALVAS", "CATAMAYO", "CELICA", "CHAGUARPAMBA", "ESPÍNDOLA", "GONZANAMÁ",
             "MACARÁ", "OLMEDO", "PALTAS", "PUYANGO", "QUILANGA", "SARAGURO", "SOZORANGA",
             "ZAPOTILLO"],
    "LOS RÍOS": ["BABAHOYO", "BABA", "BUENA FE", "MOCACHE", "MONTALVO", "PALENQUE",
                 "PUEBLOVIEJO", "QUEVEDO", "QUINSALOMA", "URDANETA", "VENTANAS", "VINCES"],
    "MANABÍ": ["PORTOVIEJO", "24 DE MAYO", "BOLÍVAR", "CHONE", "EL CARMEN", "FLAVIO ALFARO",
               "JAMA", "JARAMIJÓ", "JIPIJAPA", "JUNÍN", "MANTA", "MONTECRISTI", "OLMEDO",
               "PAJÁN", "PEDERNALES", "PICHINCHA", "ROCAFUERTE", "SAN VICENTE", "SUCRE", "TOSAGUA"],
    "MORONA SANTIAGO": ["MACAS", "GUALAQUIZA", "LIMÓN INDANZA", "LOGROÑO", "HUAMBI", "PALORA",
                        "SANTIAGO", "SUCÚA", "TAISHA", "TIWINTZA"],
    "NAPO": ["TENA", "ARCHIDONA", "CARLOS JULIO AROSEMENA TOLA", "EL CHACO", "QUIJOS"],
    "ORELLANA": ["FRANCISCO DE ORELLANA", "AGUARICO", "LA JOYA DE LOS SACHAS", "LORETO"],
    "PASTAZA": ["PUYO", "ARAJUNO", "MERA", "SANTA CLARA"],
    "PICHINCHA": ["QUITO", "CAYAMBE", "MEJÍA", "PEDRO MONCAYO", "PEDRO VICENTE MALDONADO",
                  "PUERTO QUITO", "RUMIÑAHUI", "SAN MIGUEL DE LOS BANCOS"],
    "SANTA ELENA": ["SANTA ELENA", "LA LIBERTAD", "SALINAS"],
    "SANTO DOMINGO DE LOS TSÁCHILAS": ["SANTO DOMINGO", "LA CONCORDIA"],
    "SUCUMBÍOS": ["NUEVA LOJA", "CASCALES", "CUYABENO", "GONZALO PIZARRO", "PUTUMAYO",
                  "SHUSHUFINDI", "SUCUMBÍOS"],
    "TUNGURAHUA": ["AMBATO", "BAÑOS", "CEVALLOS", "MOCHA", "PATATE", "QUERO", "TISALEO"],
    "ZAMORA CHINCHIPE": ["ZAMORA", "CENTINELA DEL CÓNDOR", "CHINCHIPE", "EL PANGUI",
                         "NANGARITZA", "PALANDA", "YACUAMBI", "YANTZAZA"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS empleados(
    id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS vehiculos(
    id INTEGER PRIMARY KEY, placa TEXT UNIQUE NOT NULL, tipo TEXT, chofer TEXT);
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE NOT NULL, clave TEXT NOT NULL,
    nombre TEXT, rol TEXT NOT NULL DEFAULT 'justifica',
    creado_el TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS parametros(
    id INTEGER PRIMARY KEY CHECK (id = 1),
    hora_limite_desayuno TEXT, valor_desayuno REAL,
    hora_limite_almuerzo TEXT, valor_almuerzo REAL,
    hora_limite_merienda TEXT, valor_merienda REAL,
    hora_limite_taxi_salida TEXT, valor_taxi_salida REAL,
    hora_limite_taxi_regreso TEXT, valor_taxi_regreso REAL,
    valor_hospedaje REAL, valor_agua REAL, valor_combustible_km REAL,
    valor_parqueadero_peaje REAL, redondeo_cajero REAL,
    velocidad_automovil REAL, velocidad_camion REAL, velocidad_bus REAL,
    horas_desayuno_viaje REAL DEFAULT 1, horas_almuerzo_viaje REAL DEFAULT 1,
    horas_merienda_viaje REAL DEFAULT 1,
    hospedaje_por_fechas REAL DEFAULT 1, taxi_regreso_madrugada REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS provincias(
    id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS cantones(
    id INTEGER PRIMARY KEY, provincia_id INTEGER NOT NULL REFERENCES provincias(id),
    nombre TEXT NOT NULL, UNIQUE(provincia_id, nombre));
CREATE TABLE IF NOT EXISTS distancias(
    canton TEXT PRIMARY KEY, km REAL NOT NULL, horas REAL);
CREATE TABLE IF NOT EXISTS viajes(
    id INTEGER PRIMARY KEY,
    viatico_numero INTEGER NOT NULL,
    responsable TEXT, cliente_proyecto TEXT, orden_combustible TEXT, placa TEXT,
    observaciones TEXT, recibo_viatico TEXT,
    recibo_viatico_2 TEXT, recibo_viatico_3 TEXT, recibo_ajuste TEXT,
    nombre_empleado TEXT NOT NULL, lugar_trabajo TEXT NOT NULL,
    provincia TEXT, canton TEXT,
    es_encargado INTEGER DEFAULT 0,
    es_chofer INTEGER DEFAULT 0,
    tipo_registro TEXT DEFAULT 'ORIGINAL',
    ajuste_numero INTEGER DEFAULT 0,
    medio_transporte TEXT DEFAULT 'AUTO',
    extra_transporte REAL DEFAULT 0,
    orden_combustible_2 TEXT,
    efectivo_combustible REAL DEFAULT 0,
    fecha_salida TEXT NOT NULL, hora_salida TEXT NOT NULL,
    fecha_regreso TEXT NOT NULL, hora_regreso TEXT NOT NULL,
    fecha_llegada_trabajo TEXT, hora_llegada_trabajo TEXT,
    fecha_salida_trabajo TEXT, hora_salida_trabajo TEXT,
    km_recorridos REAL DEFAULT 0, parqueadero_peaje REAL DEFAULT 0, otros REAL DEFAULT 0,
    dias_viaje INTEGER,
    desayuno REAL, almuerzo REAL, merienda REAL,
    taxi_salida REAL, taxi_regreso REAL, hospedaje REAL, agua REAL,
    combustible REAL, total REAL, valor_cajero REAL,
    estado TEXT DEFAULT 'PENDIENTE',
    justificado_por TEXT, justificado_el TEXT, nota_justificacion TEXT,
    devolucion_monto REAL DEFAULT 0, devolucion_observacion TEXT,
    pago_empleado_monto REAL DEFAULT 0, elaborado_por TEXT,
    creado_el TEXT DEFAULT (datetime('now','localtime')));
CREATE INDEX IF NOT EXISTS idx_viajes_numero ON viajes(viatico_numero);
CREATE TABLE IF NOT EXISTS ajustes(
    id INTEGER PRIMARY KEY, viatico_numero INTEGER NOT NULL,
    nombre_empleado TEXT, fecha TEXT, hora TEXT, concepto TEXT, otros_gastos REAL DEFAULT 0,
    creado_el TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS gastos(
    id INTEGER PRIMARY KEY,
    viatico_numero INTEGER NOT NULL,
    fecha TEXT, numero_comprobante TEXT, tipo TEXT, ruc TEXT,
    proveedor TEXT, lugar TEXT,
    hospedaje REAL DEFAULT 0, combustible REAL DEFAULT 0, buses REAL DEFAULT 0,
    taxis REAL DEFAULT 0, alimentacion REAL DEFAULT 0, peaje REAL DEFAULT 0,
    otros REAL DEFAULT 0, total REAL DEFAULT 0,
    valor_factura REAL DEFAULT 0, nota TEXT,
    creado_el TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS respaldos(
    id INTEGER PRIMARY KEY, viatico_numero INTEGER NOT NULL,
    nombre_archivo TEXT NOT NULL, ruta TEXT,
    empleado TEXT, concepto TEXT, gasto_id INTEGER,
    contenido BLOB,
    creado_el TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS clientes(
    id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS seq(nombre TEXT PRIMARY KEY, valor INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS bitacora(
    id INTEGER PRIMARY KEY,
    fecha TEXT DEFAULT (datetime('now','localtime')),
    usuario TEXT, usuario_nombre TEXT, rol TEXT,
    accion TEXT NOT NULL, entidad TEXT, referencia TEXT, detalle TEXT);
CREATE INDEX IF NOT EXISTS idx_bitacora_fecha ON bitacora(fecha);
CREATE TABLE IF NOT EXISTS renumeracion(
    viejo INTEGER PRIMARY KEY, nuevo INTEGER NOT NULL,
    creado_el TEXT DEFAULT (datetime('now','localtime')));
-- Memoria temporal: lo que cada usuario lleva escrito en la pantalla de viáticos se
-- guarda aquí solo (cada 20 segundos y al cerrar la ventana), **por usuario**, para que
-- nadie pierda la captura si el sistema se cierra por error. Se borra al guardar el
-- viático, al limpiar el formulario y al pasar los días (ver `borrar_borradores_viejos`).
CREATE TABLE IF NOT EXISTS borradores(
    usuario TEXT PRIMARY KEY, pantalla TEXT NOT NULL DEFAULT 'viatico',
    datos TEXT NOT NULL,
    actualizado_el TEXT DEFAULT (datetime('now','localtime')));
-- Índices para que las consultas sigan siendo rápidas con el uso diario y con varias
-- computadoras trabajando a la vez (van al final: las tablas ya están creadas).
CREATE INDEX IF NOT EXISTS idx_viajes_fecha ON viajes(fecha_salida);
CREATE INDEX IF NOT EXISTS idx_viajes_estado ON viajes(estado);
CREATE INDEX IF NOT EXISTS idx_gastos_numero ON gastos(viatico_numero);
CREATE INDEX IF NOT EXISTS idx_ajustes_numero ON ajustes(viatico_numero);
CREATE INDEX IF NOT EXISTS idx_respaldos_numero ON respaldos(viatico_numero);
CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(usuario);
"""

PARAM_COLS = ["hora_limite_desayuno", "valor_desayuno", "hora_limite_almuerzo", "valor_almuerzo",
              "hora_limite_merienda", "valor_merienda", "hora_limite_taxi_salida",
              "valor_taxi_salida", "hora_limite_taxi_regreso", "valor_taxi_regreso",
              "valor_hospedaje", "valor_agua", "valor_combustible_km",
              "valor_parqueadero_peaje", "redondeo_cajero",
              "velocidad_automovil", "velocidad_camion", "velocidad_bus",
              "horas_desayuno_viaje", "horas_almuerzo_viaje", "horas_merienda_viaje",
              "hospedaje_por_fechas", "taxi_regreso_madrugada"]
# Las tres velocidades (km/h) y las tres «horas extra» (las que se suman al viaje por el
# desayuno, el almuerzo y la merienda que caen en el camino) se usan solo para
# **estimar** la hora de llegada al trabajo y la de llegada a Miempresa: no entran en
# ningún valor del viático.
# `hospedaje_por_fechas`: 1 = como el Excel (noches = fecha regreso − fecha salida);
#     0 = noches reales (llegada al trabajo → salida del trabajo).
# `taxi_regreso_madrugada`: 0 = como el Excel (solo el regreso de noche); 1 = también
#     se paga el taxi al que vuelve antes de la hora límite de la mañana.
PARAMS_INICIALES = ["06:00", 3.0, "13:00", 3.0, "21:00", 3.0, "06:00", 3.0, "21:00", 3.0,
                    15.0, 1.0, 0.25, 10.0, 5.0, 70.0, 55.0, 45.0, 1.0, 1.0, 1.0, 1.0, 0.0]

VIAJE_COLS = ["viatico_numero", "responsable", "cliente_proyecto", "orden_combustible",
              "placa", "observaciones", "recibo_viatico", "recibo_viatico_2",
              "recibo_viatico_3", "recibo_ajuste", "nombre_empleado",
              "lugar_trabajo", "provincia", "canton", "es_encargado",
              "es_chofer", "tipo_registro", "ajuste_numero",
              "medio_transporte", "extra_transporte", "orden_combustible_2",
              "efectivo_combustible", "fecha_salida", "hora_salida", "fecha_regreso",
              "hora_regreso", "fecha_llegada_trabajo", "hora_llegada_trabajo",
              "fecha_salida_trabajo", "hora_salida_trabajo",
              "km_recorridos", "parqueadero_peaje", "otros", "dias_viaje",
              "desayuno", "almuerzo", "merienda", "taxi_salida", "taxi_regreso",
              "hospedaje", "agua", "combustible", "total", "valor_cajero",
              "devolucion_monto", "devolucion_observacion"]

# Columnas de `viajes` que la pantalla del viático **no** escribe: las llena el cierre de
# la justificación y la auditoría (quién lo elaboró, la plata del cierre, la devolución y
# el estado). Al **editar** un viático hay que devolverles su valor después de reemplazar
# las filas; si no, la edición borraba el cierre y el viático quedaba como recién creado
# (`pago_empleado_monto` y `elaborado_por` se perdían).
VIAJE_COLS_CIERRE = ["estado", "justificado_por", "justificado_el", "nota_justificacion",
                     "devolucion_monto", "devolucion_observacion", "pago_empleado_monto",
                     "elaborado_por"]

# Listado de personal de la empresa. En la plantilla son **de ejemplo**: el listado
# real se carga con Parámetros → 👥 Empleados → 📥 Importar Excel (o se edita a mano).
EMPLEADOS_SEMILLA = [
    "PERSONAL DE EJEMPLO UNO", "PERSONAL DE EJEMPLO DOS", "PERSONAL DE EJEMPLO TRES",
    "PERSONAL DE EJEMPLO CUATRO", "PERSONAL DE EJEMPLO CINCO", "PERSONAL DE EJEMPLO SEIS"]

# Catálogo de vehículos (plantilla: placas y choferes de ejemplo).
VEHICULOS_SEMILLA = [
    ("AAA-0001", "CAMIONETA", "PERSONAL DE EJEMPLO UNO"),
    ("AAA-0002", "CAMIONETA", "PERSONAL DE EJEMPLO DOS"),
    ("AAA-0003", "CAMION GRUA", "PERSONAL DE EJEMPLO TRES"),
    ("AAA-0004", "CAMION", "PERSONAL DE EJEMPLO CUATRO")]

# Los 4 usuarios que crean viáticos (vendedoras), el que justifica y el superusuario.
# El superusuario NO aparece en ninguna lista ni pantalla: solo entra escribiendo su clave.
ROL_VENDEDOR = "vendedor"
ROL_JUSTIFICA = "justifica"
ROL_SUPER = "super"
ROLES_VALIDOS = (ROL_VENDEDOR, ROL_JUSTIFICA, ROL_SUPER)
ETIQUETA_ROL = {ROL_VENDEDOR: "VENDEDOR(A)", ROL_JUSTIFICA: "JUSTIFICACIÓN",
                ROL_SUPER: "SUPERUSUARIO", "admin": "ADMINISTRADOR"}

USUARIOS_SEMILLA = [
    ("VENDEDOR1", "1234", "PERSONAL DE EJEMPLO UNO", ROL_VENDEDOR),
    ("VENDEDOR2", "1234", "PERSONAL DE EJEMPLO DOS", ROL_VENDEDOR),
    ("VENDEDOR3", "1234", "PERSONAL DE EJEMPLO TRES", ROL_VENDEDOR),
    ("VENDEDOR4", "1234", "PERSONAL DE EJEMPLO CUATRO", ROL_VENDEDOR),
    ("JUSTIFICA1", "1234", "PERSONAL DE EJEMPLO CINCO", ROL_JUSTIFICA),
    ("MIEMPRESA", "miempresa", "MIEMPRESA", ROL_SUPER),
]
# Nombre completo (como consta en el listado de personal) para cada usuario.
# Solo se aplica si el usuario todavía tiene el nombre corto, para no pisar un
# nombre cambiado a mano por el superusuario.
NOMBRE_CORTO_A_COMPLETO = {
    "VENDEDOR1": "PERSONAL DE EJEMPLO UNO",
    "VENDEDOR2": "PERSONAL DE EJEMPLO DOS",
    "VENDEDOR3": "PERSONAL DE EJEMPLO TRES",
    "VENDEDOR4": "PERSONAL DE EJEMPLO CUATRO",
    "JUSTIFICA1": "PERSONAL DE EJEMPLO CINCO",
}
# Usuarios antiguos que ya no se usan: se retiran al migrar (solo si siguen intactos).
USUARIOS_OBSOLETOS = [("admin", "ADMINISTRADOR", "admin"),
                      ("justifica", "JUSTIFICACIÓN", "justifica")]


def carpeta_app() -> Path:
    """Carpeta donde vive la aplicación: la del código o la del .exe si está empaquetada."""
    return cfg.carpeta_app()


def recurso(nombre) -> Path:
    """Ruta de un archivo incluido en el paquete (funciona con código y con .exe)."""
    base = getattr(sys, "_MEIPASS", None)
    return (Path(base) if base else carpeta_app()) / nombre


def dir_datos() -> Path:
    """Carpeta de datos local (base SQLite y respaldos en modo carpeta)."""
    return cfg.dir_datos()


def conectar() -> bd.Conexion:
    """Conexión a la base configurada (SQLite local o PostgreSQL central)."""
    return bd.conectar()


def cerrar_conexiones():
    """Cierra las conexiones guardadas (al cambiar de servidor o al salir del sistema)."""
    bd.cerrar_reserva()


def motor() -> str:
    return bd.motor()


def es_postgres() -> bool:
    return bd.es_postgres()


def descripcion_conexion() -> str:
    """Texto corto de la conexión actual (para mostrar en pantalla)."""
    return cfg.describir()


def probar_conexion(datos=None):
    """Prueba la conexión a la base configurada. Devuelve (ok, mensaje)."""
    return bd.probar_conexion(datos)


def _next(conn, nombre, anio=None):
    """Consecutivo atómico por año (seguro aunque haya varias máquinas).

    Para los viáticos la secuencia se lleva por año (`viatico_2026`), así que
    cada año vuelve a empezar en 1 automáticamente.
    """
    if nombre == "viatico":
        anio = int(anio or anio_actual())
        secuencia = f"viatico_{anio}"
        # Nunca entregar un número que ya exista en ese año: si el contador
        # quedó atrás se pone al día con el mayor viático guardado del año.
        fila = conn.execute("SELECT COALESCE(MAX(viatico_numero),0) AS maximo FROM viajes "
                            "WHERE viatico_numero>=? AND viatico_numero<?",
                            (clave_viatico(anio, 0), clave_viatico(anio + 1, 0))).fetchone()
        maximo = int(valor_de(fila, "maximo", 0) or 0)
        siguiente = (maximo % FACTOR_ANIO) + 1 if maximo else 1
        # El contador guarda el ÚLTIMO número usado. Se CREA si no existe (por
        # ejemplo en una base recién copiada) y se pone al día con el mayor viático
        # guardado del año: así nunca se entrega un número que ya esté usado.
        # (Antes solo se hacía el UPDATE y, si la fila no existía, el contador
        # arrancaba en 0 y el sistema repetía el N° 1.)
        conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                     (secuencia, siguiente - 1))
        conn.execute("UPDATE seq SET valor=? WHERE nombre=? AND valor<?",
                     (siguiente - 1, secuencia, siguiente - 1))
        valor = conn.proximo_valor(secuencia)
        return clave_viatico(anio, valor)
    return conn.proximo_valor(nombre)


def hora_local() -> str:
    """Fecha y hora local en el mismo formato de texto que guardan las tablas."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------- numeración de viáticos por año ----------------
# Cada año la numeración vuelve a empezar en 1 (como en el manejo manual del
# Excel). Para que no se mezclen los viáticos de distintos años, el número que
# se guarda internamente es "año * FACTOR_ANIO + consecutivo" y lo que se
# muestra al usuario es solo el consecutivo del año (por ejemplo 1, 2, 3…).
FACTOR_ANIO = 1000


def anio_actual() -> int:
    from datetime import date
    return date.today().year


def anio_de_fecha(fecha) -> int:
    """Año de una fecha 'aaaa-mm-dd' (o del texto que venga)."""
    try:
        return int(str(fecha)[:4])
    except (TypeError, ValueError):
        return anio_actual()


def valor_de(fila, columna, defecto=None):
    """Lee una columna de una fila de la base.

    Sirve igual para `sqlite3.Row` (que no tiene `.get`) y para los
    diccionarios que devuelve PostgreSQL.
    """
    if not fila:
        return defecto
    try:
        valor = fila[columna]
    except (KeyError, IndexError, TypeError):
        return defecto
    return defecto if valor is None else valor


def clave_viatico(anio, numero) -> int:
    """Número interno único para el viático `numero` del año `anio`."""
    return int(anio) * FACTOR_ANIO + int(numero)


def anio_de(clave) -> int:
    """Año de un número interno de viático (0 si es de una numeración antigua)."""
    try:
        return int(clave) // FACTOR_ANIO
    except (TypeError, ValueError):
        return 0


def numero_visible(clave) -> int:
    """El número de viático que ve el usuario (1, 2, 3… dentro del año)."""
    try:
        return int(clave) % FACTOR_ANIO
    except (TypeError, ValueError):
        return 0


def etiqueta_numero(clave) -> str:
    """Texto del número de viático para informes y rótulos: «001/2026»."""
    anio = anio_de(clave)
    if not anio:
        return str(clave)
    return f"{numero_visible(clave):03d}/{anio}"


def db_etiqueta_archivo(clave) -> str:
    """Número de viático para nombres de archivo: «001-2026»."""
    anio = anio_de(clave)
    if not anio:
        return str(clave)
    return f"{numero_visible(clave):03d}-{anio}"


def _esquema() -> str:
    """Esquema de las tablas en el dialecto del motor configurado."""
    if not bd.es_postgres():
        return SCHEMA
    esquema = SCHEMA
    esquema = re.sub(r"\bid INTEGER PRIMARY KEY\b",
                     "id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", esquema)
    esquema = esquema.replace("DEFAULT (datetime('now','localtime'))",
                              "DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')")
    esquema = esquema.replace("contenido BLOB", "contenido BYTEA")
    return esquema


def init_db():
    conn = conectar()
    with conn:
        conn.executescript(_esquema())
        nuevas_columnas = [] if bd.es_postgres() else [
            "ALTER TABLE viajes ADD COLUMN otros REAL DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN estado TEXT DEFAULT 'PENDIENTE'",
            "ALTER TABLE viajes ADD COLUMN recibo_viatico TEXT",
            "ALTER TABLE viajes ADD COLUMN provincia TEXT",
            "ALTER TABLE viajes ADD COLUMN canton TEXT",
            "ALTER TABLE viajes ADD COLUMN es_encargado INTEGER DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN medio_transporte TEXT DEFAULT 'AUTO'",
            "ALTER TABLE viajes ADD COLUMN extra_transporte REAL DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN orden_combustible_2 TEXT",
            "ALTER TABLE viajes ADD COLUMN efectivo_combustible REAL DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN recibo_viatico_2 TEXT",
            "ALTER TABLE viajes ADD COLUMN recibo_viatico_3 TEXT",
            "ALTER TABLE viajes ADD COLUMN recibo_ajuste TEXT",
            "ALTER TABLE viajes ADD COLUMN es_chofer INTEGER DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN tipo_registro TEXT DEFAULT 'ORIGINAL'",
            "ALTER TABLE viajes ADD COLUMN ajuste_numero INTEGER DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN devolucion_monto REAL DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN devolucion_observacion TEXT",
            "ALTER TABLE viajes ADD COLUMN pago_empleado_monto REAL DEFAULT 0",
            "ALTER TABLE viajes ADD COLUMN elaborado_por TEXT",
            "ALTER TABLE respaldos ADD COLUMN empleado TEXT",
            "ALTER TABLE respaldos ADD COLUMN concepto TEXT",
            "ALTER TABLE respaldos ADD COLUMN gasto_id INTEGER",
            "ALTER TABLE gastos ADD COLUMN valor_factura REAL DEFAULT 0",
            "ALTER TABLE gastos ADD COLUMN nota TEXT",
            "ALTER TABLE usuarios ADD COLUMN creado_el TEXT",
            "ALTER TABLE parametros ADD COLUMN velocidad_automovil REAL DEFAULT 70",
            "ALTER TABLE parametros ADD COLUMN velocidad_camion REAL DEFAULT 55",
            "ALTER TABLE parametros ADD COLUMN velocidad_bus REAL DEFAULT 45",
            "ALTER TABLE parametros ADD COLUMN horas_desayuno_viaje REAL DEFAULT 1",
            "ALTER TABLE parametros ADD COLUMN horas_almuerzo_viaje REAL DEFAULT 1",
            "ALTER TABLE parametros ADD COLUMN horas_merienda_viaje REAL DEFAULT 1",
            "ALTER TABLE parametros ADD COLUMN hospedaje_por_fechas REAL DEFAULT 1",
            "ALTER TABLE parametros ADD COLUMN taxi_regreso_madrugada REAL DEFAULT 0",
            "ALTER TABLE distancias ADD COLUMN horas REAL",
        ]
        for sql in nuevas_columnas:
            try:
                conn.execute(sql)
            except Exception:
                pass
        if bd.es_postgres():
            # La base central se crea completa desde el inicio. Si viene de una
            # versión anterior, se agregan las columnas que falten (se consulta
            # el catálogo antes para no abortar la transacción).
            faltantes = []
            for tabla, columna, tipo in (("respaldos", "contenido", "BYTEA"),
                                         ("viajes", "pago_empleado_monto", "REAL DEFAULT 0"),
                                         ("viajes", "elaborado_por", "TEXT"),
                                         ("parametros", "velocidad_automovil", "REAL DEFAULT 70"),
                                         ("parametros", "velocidad_camion", "REAL DEFAULT 55"),
                                         ("parametros", "velocidad_bus", "REAL DEFAULT 45"),
                                         ("parametros", "horas_desayuno_viaje",
                                          "REAL DEFAULT 1"),
                                         ("parametros", "horas_almuerzo_viaje",
                                          "REAL DEFAULT 1"),
                                         ("parametros", "horas_merienda_viaje",
                                          "REAL DEFAULT 1"),
                                         ("parametros", "hospedaje_por_fechas", "REAL DEFAULT 1"),
                                         ("parametros", "taxi_regreso_madrugada",
                                          "REAL DEFAULT 0")):
                hay = conn.execute("SELECT 1 FROM information_schema.columns "
                                   "WHERE table_name=? AND column_name=?",
                                   (tabla, columna)).fetchone()
                if not hay:
                    faltantes.append(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
            for sql in faltantes:
                conn.execute(sql)
        _migrar_usuarios(conn)
        _migrar_numeracion_por_anio(conn)
        _reparar_rutas_respaldos(conn)
        if not conn.execute("SELECT 1 FROM parametros LIMIT 1").fetchone():
            marcas = ",".join("?" * len(PARAM_COLS))
            conn.execute(f"INSERT INTO parametros(id, {', '.join(PARAM_COLS)}) VALUES (1, {marcas})",
                         PARAMS_INICIALES)
        # Valores que cambiaron con una revisión anterior de la empresa:
        #   · el redondeo del cajero pasó a múltiplo de 5 (51 → 55, 56 → 60);
        #   · la merienda pasó a contar hasta las 21:00, que es la hora del Excel nuevo;
        #   · y las velocidades con las que se estima la llegada/salida del trabajo.
        # Se aplican **una sola vez** (queda la marca «ajustes_parametros» en la tabla
        # seq). Así, si después el superusuario los cambia a mano en Parámetros, el
        # siguiente arranque ya NO los revierte.
        if not conn.execute("SELECT 1 FROM seq WHERE nombre='ajustes_parametros'").fetchone():
            ajustes = [("redondeo_cajero", None, 5.0), ("redondeo_cajero", 10, 5.0),
                       ("hora_limite_merienda", None, "21:00"),
                       ("velocidad_automovil", None, 70.0),
                       ("velocidad_camion", None, 55.0),
                       ("velocidad_bus", None, 45.0)]
            for columna, antes, ahora in ajustes:
                if antes is None:
                    conn.execute(f"UPDATE parametros SET {columna}=? WHERE {columna} IS NULL",
                                 (ahora,))
                else:
                    conn.execute(f"UPDATE parametros SET {columna}=? WHERE {columna}=?",
                                 (ahora, antes))
            conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                         ("ajustes_parametros", 1))
        # Revisión que dejó los parámetros **idénticos al Excel nuevo de la empresa**
        # (se aplica una sola vez, con su propia marca; de ahí en adelante el
        # superusuario manda desde Parámetros → tarifas y horas):
        #   · merienda hasta las 21:00 → el que vuelve a las 21:00 o después la lleva
        #     (antes estaba a las 20:00 y esas meriendas no se pagaban);
        #   · redondeo del cajero al múltiplo de 5 (51 → 55 y 56 → 60);
        #   · combustible a $0,25 por km, como el Excel;
        #   · hospedaje por las fechas del viaje (noches = regreso − salida), como el
        #     Excel (se puede volver a las noches reales desde Parámetros).
        if not conn.execute("SELECT 1 FROM seq WHERE nombre='ajustes_parametros_excel'").fetchone():
            ajustes = [("hora_limite_merienda", None, "21:00"),
                       ("hora_limite_merienda", "20:00", "21:00"),
                       ("redondeo_cajero", None, 5.0), ("redondeo_cajero", 10, 5.0),
                       ("redondeo_cajero", 0, 5.0),
                       ("valor_combustible_km", None, 0.25),
                       ("valor_combustible_km", 0.1, 0.25),
                       ("valor_parqueadero_peaje", None, 10.0),
                       ("hospedaje_por_fechas", None, 1.0),
                       ("taxi_regreso_madrugada", None, 0.0)]
            for columna, antes, ahora in ajustes:
                if antes is None:
                    conn.execute(f"UPDATE parametros SET {columna}=? WHERE {columna} IS NULL",
                                 (ahora,))
                else:
                    conn.execute(f"UPDATE parametros SET {columna}=? WHERE {columna}=?",
                                 (ahora, antes))
            conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                         ("ajustes_parametros_excel", 1))
        if not conn.execute("SELECT 1 FROM empleados LIMIT 1").fetchone():
            conn.executemany(bd.insert_ignorar("empleados", ["nombre"], "nombre"),
                             [(n,) for n in EMPLEADOS_SEMILLA])
        if not conn.execute("SELECT 1 FROM vehiculos LIMIT 1").fetchone():
            conn.executemany(bd.insert_ignorar("vehiculos", ["placa", "tipo", "chofer"], "placa"),
                             VEHICULOS_SEMILLA)
        if not conn.execute("SELECT 1 FROM provincias LIMIT 1").fetchone():
            for prov, cantones in PROV_CANT.items():
                conn.execute(bd.insert_ignorar("provincias", ["nombre"], "nombre"), (prov,))
                pid = conn.execute("SELECT id FROM provincias WHERE nombre=?",
                                   (prov,)).fetchone()["id"]
                conn.executemany(bd.insert_ignorar("cantones", ["provincia_id", "nombre"],
                                                   "provincia_id, nombre"),
                                 [(pid, c) for c in cantones])
        if not conn.execute("SELECT 1 FROM distancias LIMIT 1").fetchone():
            conn.executemany(bd.insert_ignorar("distancias", ["canton", "km"], "canton"),
                             [(k, v) for k, v in KM_CUENCA.items()])
        if not conn.execute("SELECT 1 FROM seq WHERE nombre='viatico'").fetchone():
            conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                         ("viatico", 137))
        # Lista de clientes y tiempos de viaje que viajan con el programa: se cargan una
        # sola vez (cuando la base está vacía) y quedan guardados para todas las PC.
        _cargar_catalogos_iniciales(conn)
        # Versión 8.3: a las bases que ya estaban creadas hay que meterles los cantones que
        # se agregaron al catálogo después (YANTZAZA). Va al final, después de la siembra,
        # para no estorbar la carga inicial de una base nueva.
        _reparar_catalogo_cantones(conn)
        # Memoria temporal: se descartan los borradores viejos (los de alguien que nunca
        # volvió a entrar y que ya no sirven para nada). Los del día se conservan.
        borrar_borradores_viejos(conn=conn)
    conn.close()


# ---------------- carga inicial de catálogos (una sola vez) ----------------
# Catálogos que viajan con el programa: qué archivo se usa cuando en `excel\\` hay varios
# que encajan. Es el nombre que deja la herramienta (`preparar_distancias_doc.py` para los
# tiempos de viaje) y el de la lista de clientes de la empresa.
PREFERIDOS_RECURSOS = {
    "TIEMPOS DE VIAJE": "TIEMPOS DE VIAJE MIEMPRESA (NUEVO)",
    "LISTA DE CLIENTES": "LISTA DE CLIENTES MIEMPRESA",
}


def _archivo_de_recursos(parte_nombre, extensiones=(".xlsx", ".xlsm", ".xls")):
    """Ruta del Excel que viaja con el sistema (carpeta `excel\\`). None si no está.

    Se busca primero en la carpeta de recursos (los archivos que van dentro del `.exe`)
    y después junto al programa: así funciona igual si el sistema corre desde el código
    o empaquetado, y también si el superusuario deja los Excel al lado del `.exe`.

    Si en la carpeta hay **varios** archivos que encajan, se usa el de nombre preferido
    (ver `PREFERIDOS_RECURSOS`) y solo si ese no está se toma el primero en orden
    alfabético. Antes ganaba siempre el alfabético y, por ejemplo, una copia que hubiera
    quedado de un guardado en Excel («TIEMPOS DE VIAJE PU (2).xlsx») le ganaba al archivo
    bueno de la herramienta: la carga inicial de un servidor nuevo traía esos datos.
    """
    if not parte_nombre:
        return None
    buscadas = []
    for base in (cfg.carpeta_recursos(), cfg.carpeta_app()):
        for sub in ("excel", ""):
            carpeta = (base / sub) if sub else base
            if carpeta not in buscadas:
                buscadas.append(carpeta)
    claves = [parte_nombre.upper()]
    preferido = PREFERIDOS_RECURSOS.get(parte_nombre.upper())
    if preferido and preferido.upper() != parte_nombre.upper():
        claves.insert(0, preferido.upper())      # primero el archivo bueno, por su nombre
    for clave in claves:
        for carpeta in buscadas:
            try:
                archivos = sorted(carpeta.iterdir())
            except OSError:
                continue
            for archivo in archivos:
                if (archivo.is_file() and archivo.suffix.lower() in extensiones
                        and clave in archivo.name.upper()):
                    return archivo
    return None


def _cargar_catalogos_iniciales(conn):
    """Carga, **una sola vez**, los catálogos que van con el programa.

    Cuando la base está vacía (instalación nueva o servidor nuevo) se importan la lista
    de clientes y los tiempos de viaje desde los Excel de la carpeta `excel\\`. Quedan
    **dentro de la base de datos**, así que todas las computadoras los ven sin volver a
    importarlos; y como queda la marca en la tabla `seq`, no se repite en cada arranque
    ni pisa lo que después se edite a mano en Parámetros.
    """
    if (not conn.execute("SELECT 1 FROM seq WHERE nombre='catalogo_clientes'").fetchone()
            and not conn.execute("SELECT 1 FROM clientes LIMIT 1").fetchone()):
        ruta = _archivo_de_recursos("LISTA DE CLIENTES")
        if ruta:
            try:
                _insertar_clientes(conn, _leer_excel_columna(
                    ruta, ("CLIENTE", "RAZON SOCIAL", "RAZÓN SOCIAL", "NOMBRE")))
                conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                             ("catalogo_clientes", 1))
            except Exception:
                pass
    if (not conn.execute("SELECT 1 FROM seq WHERE nombre='catalogo_tiempos'").fetchone()
            and not conn.execute("SELECT 1 FROM distancias WHERE horas IS NOT NULL "
                                 "AND horas > 0 LIMIT 1").fetchone()):
        ruta = _archivo_de_recursos("TIEMPOS DE VIAJE")
        if ruta:
            try:
                _insertar_distancias(conn, _leer_excel_distancias(ruta))
                conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                             ("catalogo_tiempos", 1))
            except Exception:
                pass


def _reparar_catalogo_cantones(conn):
    """Agrega al catálogo los cantones de fábrica que le falten a una base ya existente.

    `PROV_CANT` es la lista de provincias y cantones que ofrece el formulario, y se siembra
    **solo cuando la base está vacía**. Si después se agrega un cantón nuevo a esa lista
    (versión 8.4: **YANTZAZA**), las bases que ya estaban creadas —la central y la de cada
    PC— no se enteran y el cantón queda fuera del formulario, de los Excel y de los `.sql`
    (que fue justo lo que pasó). Esto se los agrega, con su marca en `seq` para que se haga
    una sola vez por base, y **sin pisar** nada: si el cantón ya tiene sus km y sus horas
    puestos a mano (como YANTZAZA en la central: 215 km y 5 h), se respetan los de la base.
    """
    try:
        if conn.execute("SELECT 1 FROM seq WHERE nombre='catalogo_cantones_8_4'").fetchone():
            return
        for provincia, cantones in PROV_CANT.items():
            conn.execute(bd.insert_ignorar("provincias", ["nombre"], "nombre"), (provincia,))
            pid = conn.execute("SELECT id FROM provincias WHERE nombre=?",
                               (provincia,)).fetchone()["id"]
            conn.executemany(bd.insert_ignorar("cantones", ["provincia_id", "nombre"],
                                               "provincia_id, nombre"),
                             [(pid, c) for c in cantones])
        # Los km y las horas de los cantones que entraron al catálogo después: solo se
        # escriben si le faltan al cantón (los que ya tiene la base no se tocan).
        for canton, km in DISTANCIAS_NUEVAS.items():
            fila = conn.execute("SELECT km, horas FROM distancias WHERE canton=?",
                                (canton,)).fetchone()
            horas = HORAS_CUENCA.get(canton)
            if not fila:
                conn.execute(bd.insert_ignorar("distancias", ["canton", "km", "horas"],
                                               "canton"), (canton, km, horas))
            elif not fila["horas"] and horas:
                conn.execute("UPDATE distancias SET horas=? WHERE canton=?", (horas, canton))
        conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                     ("catalogo_cantones_8_4", 1))
        olvidar_cache("provincias", "cantones:")
    except Exception as ex:
        print(f"No se pudo completar el catálogo de cantones: {ex}")


def _migrar_numeracion_por_anio(conn):
    """Convierte la numeración antigua (1, 2, 3…) a la nueva por año (año*1000+n).

    Se ejecuta una sola vez por base y solo toca los viáticos con numeración
    antigua (los que ya tienen la numeración por año no se modifican).
    """
    try:
        if conn.execute("SELECT 1 FROM seq WHERE nombre='numeracion_por_anio'").fetchone():
            return
        antiguos = [dict(x) for x in conn.execute(
            "SELECT viatico_numero, MIN(fecha_salida) AS fecha FROM viajes "
            "WHERE viatico_numero < 1000 GROUP BY viatico_numero ORDER BY viatico_numero")]
        if antiguos:
            # Continuar después del mayor número ya usado en cada año.
            contador = {}
            for fila in conn.execute("SELECT viatico_numero FROM viajes "
                                     "WHERE viatico_numero >= 1000"):
                anio = anio_de(fila["viatico_numero"])
                if anio:
                    contador[anio] = max(contador.get(anio, 0),
                                         numero_visible(fila["viatico_numero"]))
            mapa = []
            for r in antiguos:
                anio = anio_de_fecha(r["fecha"])
                contador[anio] = contador.get(anio, 0) + 1
                mapa.append((int(r["viatico_numero"]), clave_viatico(anio, contador[anio])))
            # Primero a negativos, para que los números nuevos no choquen con los
            # que todavía están por convertir.
            for viejo, _ in mapa:
                for tabla in ("viajes", "gastos", "respaldos", "ajustes"):
                    try:
                        conn.execute(f"UPDATE {tabla} SET viatico_numero=? "
                                     f"WHERE viatico_numero=?", (-viejo, viejo))
                    except Exception:
                        pass
            for viejo, nuevo in mapa:
                for tabla in ("viajes", "gastos", "respaldos", "ajustes"):
                    try:
                        conn.execute(f"UPDATE {tabla} SET viatico_numero=? "
                                     f"WHERE viatico_numero=?", (nuevo, -viejo))
                    except Exception:
                        pass
                # Se guarda el cambio de número para poder reparar los archivos
                # (respaldos) que quedaran con el número anterior.
                conn.execute(bd.insert_actualizar("renumeracion", ["viejo", "nuevo"],
                                                  ["viejo"]), (viejo, nuevo))
            # Contadores por año según lo que quedó
            for anio, cantidad in contador.items():
                conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                             (f"viatico_{anio}", cantidad))
                conn.execute("UPDATE seq SET valor=? WHERE nombre=?",
                             (cantidad, f"viatico_{anio}"))
            # Si los respaldos están en carpetas, la carpeta se renombra al número
            # nuevo y se corrigen las rutas guardadas.
            if cfg.modo_respaldos() == "carpeta":
                base = cfg.carpeta_respaldos()
                for viejo, nuevo in mapa:
                    vieja, nueva = base / f"viatico_{viejo}", base / f"viatico_{nuevo}"
                    if not vieja.exists() or nueva.exists():
                        continue
                    try:
                        vieja.rename(nueva)
                    except OSError:
                        continue
                    filas = [dict(x) for x in conn.execute(
                        "SELECT id, ruta FROM respaldos WHERE viatico_numero=?", (nuevo,))]
                    for f in filas:
                        ruta = f["ruta"] or ""
                        if str(vieja) in ruta:
                            conn.execute("UPDATE respaldos SET ruta=? WHERE id=?",
                                         (ruta.replace(str(vieja), str(nueva)), f["id"]))
        conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                     ("numeracion_por_anio", 1))
    except Exception as ex:
        print(f"No se pudo migrar la numeración: {ex}")


def _reparar_rutas_respaldos(conn):
    """Corrige rutas de respaldos cuando la carpeta del sistema cambió de lugar.

    Si un registro apunta a una ruta que ya no existe, pero el archivo está en
    la carpeta actual de datos, se actualiza la ruta. No elimina nada.
    En modo "base" los archivos viven dentro de la base, así que no hay nada
    que reparar.
    """
    if cfg.modo_respaldos() != "carpeta":
        return
    # 0) Respaldos que quedaron con la numeración antigua: si el viático se
    #    renumeró por año, se corrige con la tabla de renumeración.
    try:
        pares = {int(x["viejo"]): int(x["nuevo"]) for x in conn.execute(
            "SELECT viejo, nuevo FROM renumeracion")}
    except Exception:
        pares = {}
    if pares:
        for f in [dict(x) for x in conn.execute(
                "SELECT id, viatico_numero FROM respaldos")]:
            viejo = int(f["viatico_numero"] or 0)
            if viejo in pares:
                existe = conn.execute("SELECT 1 FROM viajes WHERE viatico_numero=? LIMIT 1",
                                      (viejo,)).fetchone()
                if not existe:
                    conn.execute("UPDATE respaldos SET viatico_numero=? WHERE id=?",
                                 (pares[viejo], f["id"]))

    # 1) Rutas de respaldos que apuntan a otra ubicación (carpeta movida).
    try:
        filas = [dict(x) for x in conn.execute(
            "SELECT id, viatico_numero, nombre_archivo, ruta FROM respaldos")]
    except Exception:
        return
    for r in filas:
        ruta = r.get("ruta") or ""
        if ruta and os.path.exists(ruta):
            continue
        nombre = os.path.basename(ruta) or (r.get("nombre_archivo") or "")
        if not nombre:
            continue
        candidato = dir_datos() / "respaldos" / f"viatico_{r['viatico_numero']}" / nombre
        if candidato.exists():
            conn.execute("UPDATE respaldos SET ruta=? WHERE id=?",
                         (str(candidato), r["id"]))
    # 2) PDF completo que está en disco pero sin registro (carpeta movida o
    #    justificación hecha con una versión anterior) -> se registra.
    # 3) Registros cuyo archivo ya no existe y que están dentro del completo ->
    #    se retiran para que la lista de respaldos no muestre entradas rotas.
    base = dir_datos() / "respaldos"
    if not base.exists():
        return
    for carpeta in sorted(base.iterdir()):
        if not carpeta.is_dir() or not carpeta.name.startswith("viatico_"):
            continue
        try:
            num = int(carpeta.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        completo = carpeta / f"VIATICO_{num}_COMPLETO.pdf"
        if not completo.exists():
            continue
        # Si ese archivo ya está registrado (con cualquier número) no se duplica.
        ya = conn.execute("SELECT 1 FROM respaldos WHERE ruta=?",
                          (str(completo),)).fetchone()
        hay = conn.execute("SELECT 1 FROM respaldos WHERE viatico_numero=? AND ruta=?",
                           (num, str(completo))).fetchone()
        if not ya and not hay:
            conn.execute("INSERT INTO respaldos(viatico_numero, nombre_archivo, ruta, empleado, "
                         "concepto, gasto_id) VALUES (?,?,?,?,?,?)",
                         (num, completo.name, str(completo), None, "PDF CONSOLIDADO", None))
        for f in conn.execute("SELECT id, ruta FROM respaldos WHERE viatico_numero=?",
                              (num,)).fetchall():
            ruta = f["ruta"] or ""
            if os.path.abspath(ruta) == os.path.abspath(str(completo)):
                continue
            if not ruta or not os.path.exists(ruta):
                conn.execute("DELETE FROM respaldos WHERE id=?", (f["id"],))
    # 4) El mismo archivo registrado dos veces (pasa al renumerar viáticos):
    #    se conserva el registro con el número más alto (numeración por año).
    filas = [dict(x) for x in conn.execute(
        "SELECT id, ruta, viatico_numero FROM respaldos ORDER BY id")]
    vistos, borrar = {}, []
    for f in filas:
        clave = os.path.abspath(f["ruta"] or "") or f"id:{f['id']}"
        if clave in vistos:
            previo = vistos[clave]
            if int(f["viatico_numero"] or 0) > int(previo["viatico_numero"] or 0):
                borrar.append(previo["id"])
                vistos[clave] = f
            else:
                borrar.append(f["id"])
        else:
            vistos[clave] = f
    for id_ in borrar:
        conn.execute("DELETE FROM respaldos WHERE id=?", (id_,))

    # 5) Carpetas con numeración antigua: si todos sus archivos ya pertenecen a un
    #    viático con número por año, se renombra la carpeta y se corrigen las rutas.
    base = cfg.carpeta_respaldos()
    if not base.exists():
        return
    todas = [dict(x) for x in conn.execute("SELECT id, ruta, viatico_numero FROM respaldos")]
    for carpeta in sorted(base.iterdir()):
        if not carpeta.is_dir() or not carpeta.name.startswith("viatico_"):
            continue
        try:
            num = int(carpeta.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if num >= 1000:
            continue
        dentro = [f for f in todas if (f["ruta"] or "").startswith(str(carpeta) + os.sep)]
        if not dentro:
            continue
        claves = {int(f["viatico_numero"] or 0) for f in dentro}
        if len(claves) != 1 or next(iter(claves)) < 1000:
            continue
        destino = base / f"viatico_{claves.pop()}"
        if destino.exists():
            continue
        try:
            carpeta.rename(destino)
        except OSError:
            continue
        for f in dentro:
            conn.execute("UPDATE respaldos SET ruta=? WHERE id=?",
                         ((f["ruta"] or "").replace(str(carpeta), str(destino)), f["id"]))


def _migrar_usuarios(conn):
    """Crea los usuarios del sistema y retira los antiguos (admin/justifica).

    Se ejecuta en cada arranque: agrega los que falten sin tocar los que ya
    existen, de manera que no se pierde ninguna clave cambiada a mano.
    """
    existentes = [dict(x) for x in conn.execute("SELECT usuario, nombre, rol FROM usuarios")]
    for usuario, nombre, rol in USUARIOS_OBSOLETOS:
        hay = any((x["usuario"] or "").upper() == usuario.upper() and x["rol"] == rol
                  and (x["nombre"] or "").upper() == nombre.upper() for x in existentes)
        if hay:
            conn.execute("DELETE FROM usuarios WHERE usuario=?", (usuario,))
    claves = {(x["usuario"] or "").upper() for x in existentes}
    for usuario, clave, nombre, rol in USUARIOS_SEMILLA:
        if usuario.upper() in claves:
            continue
        conn.execute(bd.insert_ignorar("usuarios", ["usuario", "clave", "nombre", "rol",
                                                    "creado_el"], "usuario"),
                     (usuario, cifrar_clave(clave), nombre, rol, hora_local()))
    # Nombre completo del personal en los usuarios que aún tengan el nombre corto.
    for usuario, completo in NOMBRE_CORTO_A_COMPLETO.items():
        conn.execute("UPDATE usuarios SET nombre=? WHERE UPPER(usuario)=? AND "
                     "(nombre IS NULL OR UPPER(nombre)=?)",
                     (completo, usuario.upper(), usuario.upper()))
    # Claves que quedaran escritas en texto (bases anteriores): se cifran aquí, una
    # sola vez, al abrir el sistema. A partir de ese momento nadie puede leerlas.
    for fila in [dict(x) for x in conn.execute("SELECT usuario, clave FROM usuarios")]:
        if not es_clave_cifrada(fila.get("clave")):
            conn.execute("UPDATE usuarios SET clave=? WHERE usuario=?",
                         (cifrar_clave(fila.get("clave")), fila.get("usuario")))



# ---------------- catálogos ----------------
def listar_empleados():
    return _copiar(_memoria("empleados", _SEGUNDOS_MEMORIA, _leer_empleados))


def _leer_empleados():
    conn = conectar()
    r = [x["nombre"] for x in conn.execute("SELECT nombre FROM empleados ORDER BY nombre")]
    conn.close()
    return r

def agregar_empleado(nombre):
    with conectar() as c:
        c.execute(bd.insert_ignorar("empleados", ["nombre"], "nombre"), (nombre.upper(),))
    olvidar_cache("empleados")

def eliminar_empleado(nombre):
    conn = conectar()
    with conn:
        n = conn.execute("DELETE FROM empleados WHERE nombre=?", (nombre,)).rowcount
    conn.close()
    olvidar_cache("empleados")
    return n > 0

def listar_vehiculos():
    return _copiar(_memoria("vehiculos", _SEGUNDOS_MEMORIA, _leer_vehiculos))


def _leer_vehiculos():
    conn = conectar()
    r = [dict(x) for x in conn.execute("SELECT placa, tipo, chofer FROM vehiculos ORDER BY placa")]
    conn.close()
    return r


def buscar_vehiculo_por_placa(placa):
    conn = conectar()
    r = conn.execute("SELECT * FROM vehiculos WHERE placa=?", (placa,)).fetchone()
    conn.close()
    return dict(r) if r else None

def agregar_vehiculo(placa, tipo, chofer):
    with conectar() as c:
        c.execute(bd.insert_actualizar("vehiculos", ["placa", "tipo", "chofer"], ["placa"]),
                  (placa.upper(), tipo, chofer))
    olvidar_cache("vehiculos")

def eliminar_vehiculo(placa):
    conn = conectar()
    with conn:
        n = conn.execute("DELETE FROM vehiculos WHERE placa=?", (placa,)).rowcount
    conn.close()
    olvidar_cache("vehiculos")
    return n > 0

def listar_provincias():
    return _copiar(_memoria("provincias", _SEGUNDOS_MEMORIA, _leer_provincias))


def _leer_provincias():
    conn = conectar()
    r = [x["nombre"] for x in conn.execute("SELECT nombre FROM provincias ORDER BY nombre")]
    conn.close()
    return r


def listar_clientes():
    return _copiar(_memoria("clientes", _SEGUNDOS_MEMORIA, _leer_clientes))


def _leer_clientes():
    conn = conectar()
    r = [x["nombre"] for x in conn.execute("SELECT nombre FROM clientes ORDER BY nombre")]
    conn.close()
    return r

def agregar_cliente(nombre):
    with conectar() as c:
        c.execute(bd.insert_ignorar("clientes", ["nombre"], "nombre"), (nombre.upper(),))
    olvidar_cache("clientes")

def eliminar_cliente(nombre):
    conn = conectar()
    with conn:
        n = conn.execute("DELETE FROM clientes WHERE nombre=?", (nombre,)).rowcount
    conn.close()
    olvidar_cache("clientes")
    return n > 0


ENCABEZADOS_EXCEL = {"NOMBRE", "NOMBRES", "NOMBRE COMPLETO", "NOMBRES COMPLETOS",
                     "EMPLEADO", "EMPLEADOS", "CLIENTE", "CLIENTES",
                     "LISTA DE EMPLEADOS", "LISTA DE CLIENTES",
                     "N°", "NO", "NUM", "#", "TEXTO", "TEXT"}


def _leer_excel_columna(ruta, palabras_clave=()):
    """Devuelve los textos de la columna de nombres/clientes de un Excel.

    Primero busca una fila de encabezado cuya celda contenga alguna de las
    `palabras_clave` (por ejemplo NOMBRE o CLIENTE) y lee esa misma columna
    hacia abajo. Si no la encuentra, usa la primera columna con datos, que es
    el comportamiento anterior (listas simples de una sola columna).
    """
    try:
        import openpyxl
    except Exception:
        raise RuntimeError("Falta la librería 'openpyxl'.\nInstale con:  pip install openpyxl")
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    hoja = wb[wb.sheetnames[0]]
    filas = []
    for i, fila in enumerate(hoja.iter_rows(values_only=True)):
        if i >= 30000:          # por seguridad en hojas con filas vacías de sobra
            break
        filas.append(["" if c is None else str(c).strip() for c in fila])
    try:
        wb.close()
    except Exception:
        pass

    claves = [k.upper() for k in palabras_clave]
    col = None
    inicio = 0
    # Se busca la fila de encabezados: aquella con más títulos que coincidan
    # EXACTAMENTE con las palabras clave (así no confunde "Lista de Clientes"
    # del título con la columna "Cliente").
    mejor = 0
    for i, fila in enumerate(filas[:60]):
        aciertos = [j for j, c in enumerate(fila) if c and c.upper() in claves]
        if len(aciertos) > mejor:
            mejor = len(aciertos)
            col = aciertos[0]
            inicio = i + 1
    if col is None:
        # Sin encabezado exacto: primera celda cuyo texto contenga la palabra.
        for i, fila in enumerate(filas[:60]):
            for j, c in enumerate(fila):
                if c and any(k in c.upper() for k in claves):
                    col, inicio = j, i + 1
                    break
            if col is not None:
                break

    valores = []
    if col is not None:
        for fila in filas[inicio:]:
            texto = fila[col] if col < len(fila) else ""
            if texto and texto.upper() not in ENCABEZADOS_EXCEL:
                valores.append(texto)
        return valores

    for fila in filas:
        for celda in fila:
            if celda and celda.upper() not in ENCABEZADOS_EXCEL:
                valores.append(celda)
                break
    return valores


def importar_empleados_excel(ruta):
    """Importa nombres de empleados desde un Excel (columna «Nombre»). Devuelve agregados."""
    nombres = [n.upper() for n in _leer_excel_columna(ruta, ("NOMBRE", "NOMBRES", "EMPLEADO",
                                                             "PERSONAL", "APELLIDO"))]
    agregados = 0
    with conectar() as c:
        for n in nombres:
            n = n.strip()
            if not n or len(n) < 4:
                continue
            cur = c.execute(bd.insert_ignorar("empleados", ["nombre"], "nombre"), (n,))
            agregados += cur.rowcount
    olvidar_cache("empleados")
    return len(nombres), agregados


def importar_clientes_excel(ruta):
    """Importa la lista de clientes desde un Excel (columna «Cliente»). Devuelve agregados.

    No duplica: los clientes que ya están en la lista se dejan como están.
    """
    nombres = [n.upper() for n in _leer_excel_columna(ruta, ("CLIENTE", "RAZON SOCIAL",
                                                             "RAZÓN SOCIAL", "NOMBRE"))]
    with conectar() as c:
        agregados = _insertar_clientes(c, nombres)
    return len(nombres), agregados


def _insertar_clientes(conn, nombres):
    """Agrega a la tabla de clientes los nombres que no estaban. Devuelve cuántos."""
    agregados = 0
    for n in nombres:
        n = (n or "").strip().upper()
        if not n or len(n) < 3:
            continue
        agregados += conn.execute(bd.insert_ignorar("clientes", ["nombre"], "nombre"),
                                  (n,)).rowcount
    olvidar_cache("clientes")
    return agregados


def _a_numero(valor):
    """Número de una celda de Excel (acepta 250, «250 km», «3,5»). None si no es número."""
    if valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("$", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _leer_excel_distancias(ruta):
    """Filas (cantón, km, horas) del Excel de tiempos de viaje.

    Detecta las columnas por el encabezado («Cantón», «Km», «Horas de viaje») en las
    primeras filas; si no los encuentra, usa las tres primeras columnas. Las horas son
    opcionales: un cantón sin horas queda con los km y el sistema estima el tiempo con
    la velocidad del vehículo.
    """
    try:
        import openpyxl
    except Exception:
        raise RuntimeError("Falta la librería 'openpyxl'.\nInstale con:  pip install openpyxl")
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    hoja = wb[wb.sheetnames[0]]
    filas = []
    for i, fila in enumerate(hoja.iter_rows(values_only=True)):
        if i >= 30000:
            break
        filas.append(list(fila))
    try:
        wb.close()
    except Exception:
        pass

    col_canton = col_km = col_horas = None
    inicio = 0
    # La fila de encabezados es la primera en la que aparece el cantón **y** los km;
    # las horas se toman de esa misma fila (así no se confunde con un título que diga
    # «TIEMPOS DE VIAJE» antes de los encabezados de verdad).
    for i, fila in enumerate(filas[:30]):
        cand = {"canton": None, "km": None, "horas": None}
        for j, celda in enumerate(fila):
            texto = ("" if celda is None else str(celda)).strip().upper()
            if not texto:
                continue
            if cand["canton"] is None and ("CANT" in texto or "CIUDAD" in texto
                                           or texto == "DESTINO"):
                cand["canton"] = j
            elif cand["km"] is None and (texto.startswith("KM") or "DISTANCIA" in texto):
                cand["km"] = j
            elif cand["horas"] is None and ("HORA" in texto or "TIEMPO" in texto):
                cand["horas"] = j
        if cand["canton"] is not None and cand["km"] is not None:
            col_canton, col_km, col_horas = cand["canton"], cand["km"], cand["horas"]
            inicio = i + 1
            break
    if col_canton is None or col_km is None:
        col_canton, col_km = 0, 1
        if col_horas is None:
            col_horas = 2
        inicio = 0

    salida = []
    for fila in filas[inicio:]:
        canton = (str(fila[col_canton]) if col_canton < len(fila) and fila[col_canton]
                  else "").strip().upper()
        if not canton or canton in ENCABEZADOS_EXCEL or canton in ("CANTÓN", "CANTON",
                                                                  "CIUDAD", "DESTINO",
                                                                  "TOTAL"):
            continue
        km = _a_numero(fila[col_km] if col_km < len(fila) else None)
        horas = (_a_numero(fila[col_horas])
                 if col_horas is not None and col_horas < len(fila) else None)
        if km is None or km <= 0:
            continue
        salida.append((canton, km, None if horas is None or horas <= 0 else horas))
    return salida


def _insertar_distancias(conn, filas):
    """Guarda los km y las horas de cada cantón (crea el cantón si no estaba)."""
    cambios = 0
    for canton, km, horas in filas:
        if conn.execute("SELECT 1 FROM distancias WHERE canton=?", (canton,)).fetchone():
            if horas is None:
                conn.execute("UPDATE distancias SET km=? WHERE canton=?", (km, canton))
            else:
                conn.execute("UPDATE distancias SET km=?, horas=? WHERE canton=?",
                             (km, horas, canton))
        else:
            conn.execute(bd.insert_ignorar("distancias", ["canton", "km", "horas"],
                                           "canton"), (canton, km, horas))
        cambios += 1
    olvidar_cache("distancias", "cantones:")
    return cambios


def importar_distancias_excel(ruta):
    """Importa los km y las horas de viaje de los cantones desde un Excel.

    Es el mismo formato de los Excel de tiempos de viaje que van con el sistema
    («TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx»; columnas Cantón, Km y Horas de viaje).
    Devuelve (filas leídas, guardadas).
    """
    filas = _leer_excel_distancias(ruta)
    with conectar() as c:
        cambios = _insertar_distancias(c, filas)
    return len(filas), cambios


def existe_cliente(nombre):
    """True si el cliente está en la lista de clientes.

    Los viáticos solo aceptan clientes que estén en la lista (Parámetros → Clientes):
    así no se crean clientes nuevos sin querer al guardar un viático.
    """
    nombre = (nombre or "").strip().upper()
    if not nombre:
        return False
    conn = conectar()
    r = conn.execute("SELECT 1 FROM clientes WHERE UPPER(nombre)=?", (nombre,)).fetchone()
    conn.close()
    return r is not None


def listar_cantones(provincia):
    """Cantones de una provincia (se recuerdan unos segundos: casi nunca cambian)."""
    return _copiar(_memoria("cantones:" + (provincia or ""), _SEGUNDOS_MEMORIA,
                            lambda: _leer_cantones(provincia)))


def _leer_cantones(provincia):
    conn = conectar()
    r = [x["nombre"] for x in conn.execute(
        "SELECT c.nombre FROM cantones c JOIN provincias p ON p.id=c.provincia_id "
        "WHERE p.nombre=? ORDER BY c.nombre", (provincia,))]
    conn.close()
    return r

def listar_usuarios(incluir_super=False):
    """Usuarios visibles en pantalla.

    La clave **no** se devuelve: en la base está cifrada. Se informa si el usuario
    ya tiene clave guardada (`tiene_clave`) para que la pantalla lo pueda mostrar.

    Con `incluir_super=True` aparece también el superusuario. La pantalla de usuarios
    lo pide así para que él pueda **cambiar su propia clave**: su usuario, su nombre y
    su rol no se tocan desde ahí y tampoco se puede eliminar.
    """
    roles = ((ROL_VENDEDOR, ROL_JUSTIFICA, ROL_SUPER) if incluir_super
             else (ROL_VENDEDOR, ROL_JUSTIFICA))
    marcas = ", ".join("?" * len(roles))
    conn = conectar()
    r = []
    for x in conn.execute(
            f"SELECT usuario, nombre, rol, clave, creado_el FROM usuarios "
            f"WHERE rol IN ({marcas}) ORDER BY rol DESC, nombre", roles):
        fila = dict(x)
        fila["tiene_clave"] = bool((fila.get("clave") or "").strip())
        fila["clave"] = ""
        r.append(fila)
    conn.close()
    return r

def existe_usuario(usuario):
    conn = conectar()
    row = conn.execute("SELECT 1 FROM usuarios WHERE UPPER(usuario)=?",
                       ((usuario or "").strip().upper(),)).fetchone()
    conn.close()
    return row is not None

# ---------------- claves de los usuarios (se guardan cifradas) ----------------
# En la base NO queda la clave legible: se guarda como  sha256$<sal>$<resumen>,
# que sirve para comprobar la clave pero no para leerla (tampoco se ve en los
# respaldos de la base). Las claves que ya existían escritas en texto se cifran
# solas la primera vez que se abre el sistema después de esta actualización.
PREFIJO_CLAVE = "sha256$"


def _resumen_clave(clave, sal):
    """Resumen sha256 de la clave con su sal (el mismo cálculo al guardar y al validar)."""
    datos = (str(sal) + (clave or "").strip()).encode("utf-8")
    return hashlib.sha256(datos).hexdigest()


def cifrar_clave(clave):
    """Devuelve la clave lista para guardar (cifrada y con una sal al azar)."""
    clave = (clave or "").strip()
    if es_clave_cifrada(clave):
        return clave
    sal = binascii.hexlify(os.urandom(8)).decode("ascii")
    return "%s%s$%s" % (PREFIJO_CLAVE, sal, _resumen_clave(clave, sal))


def es_clave_cifrada(valor):
    """True si lo que está guardado ya viene cifrado."""
    return (isinstance(valor, str) and valor.startswith(PREFIJO_CLAVE)
            and valor.count("$") == 2)


def clave_correcta(guardada, clave):
    """Compara la clave escrita con la guardada (cifrada o, en bases viejas, en texto)."""
    if not guardada:
        return False
    if es_clave_cifrada(guardada):
        sal = guardada.split("$")[1]
        return hmac.compare_digest(guardada, "%s%s$%s" % (PREFIJO_CLAVE, sal,
                                                          _resumen_clave(clave, sal)))
    return hmac.compare_digest(str(guardada).strip(), (clave or "").strip())


def agregar_usuario(usuario, clave, nombre="", rol=ROL_VENDEDOR):
    """Crea un usuario. Devuelve su nombre de usuario o None si ya existía."""
    usuario = (usuario or "").strip().upper()
    nombre = (nombre or usuario).strip().upper()
    clave = (clave or "").strip()
    if not usuario or not clave:
        raise ValueError("El usuario y la clave son obligatorios.")
    if rol not in ROLES_VALIDOS:
        raise ValueError("Rol no válido.")
    if existe_usuario(usuario):
        return None
    with conectar() as c:
        c.execute("INSERT INTO usuarios(usuario, clave, nombre, rol, creado_el) "
                  "VALUES (?,?,?,?,?)",
                  (usuario, cifrar_clave(clave), nombre, rol, hora_local()))
    return usuario

def actualizar_usuario(usuario, clave=None, nombre=None, rol=None, permitir_super=False):
    """Cambia clave, nombre o rol de un usuario.

    Del **superusuario** solo se puede cambiar la clave (y solo si `permitir_super` es
    True, que es como lo pide la pantalla de usuarios cuando el propio superusuario
    cambia su clave): su nombre y su rol no se tocan desde aquí, y tampoco se puede
    eliminar.
    """
    usuario = (usuario or "").strip().upper()
    conn = conectar()
    fila = conn.execute("SELECT rol FROM usuarios WHERE UPPER(usuario)=?", (usuario,)).fetchone()
    if fila is None:
        conn.close()
        return False
    es_super = (fila["rol"] == ROL_SUPER)
    campos, args = [], []
    if clave:
        campos.append("clave=?")
        args.append(cifrar_clave(clave))
    if not es_super:
        if nombre:
            campos.append("nombre=?")
            args.append(nombre.strip().upper())
        if rol in ROLES_VALIDOS:
            campos.append("rol=?")
            args.append(rol)
    elif not permitir_super:
        conn.close()
        return False
    if not campos:
        conn.close()
        return False
    with conn:
        n = conn.execute(f"UPDATE usuarios SET {', '.join(campos)} "
                         f"WHERE UPPER(usuario)=?", args + [usuario]).rowcount
    conn.close()
    return n > 0

def eliminar_usuario(usuario):
    conn = conectar()
    with conn:
        n = conn.execute("DELETE FROM usuarios WHERE UPPER(usuario)=? AND rol NOT IN (?, ?)",
                         ((usuario or "").strip().upper(), "admin", ROL_SUPER)).rowcount
    conn.close()
    return n > 0

def login(usuario, clave):
    """Valida usuario y clave.

    Acepta el usuario completo o su primer nombre (por ejemplo "JUSTIFICA1" entra
    como "JUSTIFICA1"), y también entrar escribiendo solamente la clave (así
    ingresa el superusuario). La clave se compara contra la guardada, que está
    cifrada; si la base venía de una versión anterior y la clave estaba en texto,
    se cifra en este mismo ingreso. No devuelve nada si la clave no coincide.
    """
    u = (usuario or "").strip().upper()
    c = (clave or "").strip()
    if not u or not c:
        return None
    patron = (u.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    conn = conectar()
    try:
        candidatos = [dict(x) for x in conn.execute(
            "SELECT usuario, nombre, rol, clave FROM usuarios WHERE "
            "UPPER(usuario)=? OR UPPER(nombre)=? OR UPPER(usuario) LIKE ? ESCAPE '\\' "
            "ORDER BY CASE WHEN UPPER(usuario)=? THEN 0 ELSE 1 END", (u, u, patron, u))]
        elegido = next((f for f in candidatos if clave_correcta(f.get("clave"), c)), None)
        if elegido is None:
            # Igual que antes: se puede entrar escribiendo solo la clave.
            todos = [dict(x) for x in conn.execute(
                "SELECT usuario, nombre, rol, clave FROM usuarios")]
            elegido = next((f for f in todos if clave_correcta(f.get("clave"), c)), None)
    finally:
        conn.close()
    if elegido is None:
        return None
    # Si la clave todavía estaba en texto (base anterior), se cifra ahora.
    if not es_clave_cifrada(elegido.get("clave")):
        with conectar() as c2:
            c2.execute("UPDATE usuarios SET clave=? WHERE UPPER(usuario)=?",
                       (cifrar_clave(c), (elegido.get("usuario") or "").upper()))
    return {"usuario": elegido.get("usuario"), "nombre": elegido.get("nombre"),
            "rol": elegido.get("rol")}


# ---------------- bitácora (informe de actividad) ----------------
def registrar_bitacora(usuario, accion, entidad="", referencia="", detalle=""):
    """Anota una acción en la bitácora. Nunca interrumpe el trabajo del usuario.

    `usuario` puede ser el diccionario de la sesión o un nombre de texto.
    """
    try:
        if isinstance(usuario, dict):
            user = usuario.get("usuario") or usuario.get("nombre") or ""
            nombre = usuario.get("nombre") or user
            rol = usuario.get("rol") or ""
        else:
            user = nombre = str(usuario or "")
            rol = ""
        with conectar() as c:
            c.execute("INSERT INTO bitacora(usuario, usuario_nombre, rol, accion, entidad, "
                      "referencia, detalle) VALUES (?,?,?,?,?,?,?)",
                      (user, nombre, rol, (accion or "").upper(), entidad or "",
                       str(referencia or ""), detalle or ""))
    except Exception as ex:
        print(f"No se pudo registrar en la bitácora: {ex}")

def listar_bitacora(usuario=None, accion=None, desde=None, hasta=None, texto=None, limite=None):
    """Movimientos registrados, del más reciente al más antiguo."""
    conn = conectar()
    q = "SELECT * FROM bitacora WHERE 1=1"
    args = []
    if usuario:
        q += " AND (usuario=? OR usuario_nombre=?)"; args += [usuario, usuario]
    if accion:
        q += " AND accion=?"; args.append(accion)
    if desde:
        q += f" AND {bd.fecha_dia('fecha')}>=?"; args.append(desde)
    if hasta:
        q += f" AND {bd.fecha_dia('fecha')}<=?"; args.append(hasta)
    if texto:
        t = f"%{texto.strip().upper()}%"
        q += (" AND (UPPER(accion) LIKE ? OR UPPER(detalle) LIKE ? OR UPPER(entidad) LIKE ? "
              "OR UPPER(referencia) LIKE ? OR UPPER(usuario_nombre) LIKE ?)")
        args += [t, t, t, t, t]
    q += " ORDER BY id DESC"
    if limite:
        q += " LIMIT ?"; args.append(int(limite))
    r = [dict(x) for x in conn.execute(q, args)]
    conn.close()
    return r

def usuarios_bitacora():
    conn = conectar()
    r = [x["usuario_nombre"] for x in conn.execute(
        "SELECT DISTINCT usuario_nombre FROM bitacora WHERE usuario_nombre<>'' "
        "ORDER BY usuario_nombre")]
    conn.close()
    return r

def acciones_bitacora():
    conn = conectar()
    r = [x["accion"] for x in conn.execute(
        "SELECT DISTINCT accion FROM bitacora ORDER BY accion")]
    conn.close()
    return r


# ---------------- distancias y horas de viaje (desde Cuenca) ----------------
def _rutas():
    """(mapa por cantón, lista ordenada) de la tabla de rutas.

    Son ~200 filas y se consultan a cada rato (cada tecleo del formulario pide el km y
    las horas del cantón), así que se leen de una sola vez y se recuerdan unos segundos.
    """
    return _memoria("distancias", _SEGUNDOS_MEMORIA, _leer_rutas)


def _leer_rutas():
    conn = conectar()
    try:
        filas = [dict(x) for x in conn.execute(
            "SELECT canton, km, horas FROM distancias ORDER BY canton")]
    except Exception:
        # Base vieja, sin la columna de las horas: se leen solo los km.
        filas = [dict(x) for x in conn.execute(
            "SELECT canton, km FROM distancias ORDER BY canton")]
        for f in filas:
            f["horas"] = None
    conn.close()
    mapa = {str(f["canton"]).strip().upper(): (f.get("km"), f.get("horas")) for f in filas}
    return mapa, filas


def km_para(canton):
    """Km ida desde Cuenca para un cantón. None si no está registrado."""
    if not canton:
        return None
    datos = _rutas()[0].get(canton.strip().upper())
    return datos[0] if datos else None

def horas_para(canton):
    """Horas de viaje (ida) registradas para un cantón. None si no hay dato.

    Se editan en Parámetros → Rutas, junto a los km. Si la base viene de antes (sin
    la columna) devuelve None y el programa usa su tabla aproximada.
    """
    if not canton:
        return None
    datos = _rutas()[0].get(canton.strip().upper())
    if not datos or not datos[1]:
        return None
    try:
        return float(datos[1])
    except (TypeError, ValueError):
        return None

def set_distancia(canton, km, horas=None):
    """Guarda los km y, si se indica, las horas de viaje del cantón."""
    with conectar() as c:
        c.execute("INSERT INTO distancias(canton, km, horas) VALUES (?,?,?) "
                  "ON CONFLICT(canton) DO UPDATE SET km=excluded.km, "
                  "horas=COALESCE(excluded.horas, distancias.horas)",
                  (canton.strip().upper(), float(km),
                   None if horas in (None, "") else float(horas)))
    olvidar_cache("distancias", "cantones:")

def listar_distancias():
    """Rutas registradas (cantón, km, horas), en orden alfabético."""
    return [dict(f) for f in _rutas()[1]]


def asegurar_provincia(nombre):
    """Agrega la provincia al catálogo si todavía no está. True si la agregó.

    Se usa al guardar los km de un cantón nuevo desde Parámetros y al reparar el catálogo
    (ver `_reparar_catalogo_cantones`).
    """
    nombre = (nombre or "").strip().upper()
    if not nombre:
        return False
    with conectar() as c:
        if c.execute("SELECT 1 FROM provincias WHERE nombre=?", (nombre,)).fetchone():
            return False
        c.execute(bd.insert_ignorar("provincias", ["nombre"], "nombre"), (nombre,))
    olvidar_cache("provincias")
    return True


def asegurar_canton(provincia, canton):
    """Agrega el cantón al catálogo de esa provincia si todavía no está. True si lo agregó.

    Es lo que hace que un cantón **escrito a mano** en Parámetros → 🗺️ Provincias y km
    (YANTZAZA entró así) quede después en la lista desplegable del formulario de viáticos y
    en la de esa misma pantalla: antes se guardaban los km, pero el cantón no existía para el
    formulario y había que volver a escribirlo cada vez.
    """
    provincia = (provincia or "").strip().upper()
    canton = (canton or "").strip().upper()
    if not canton:
        return False
    asegurar_provincia(provincia)
    with conectar() as c:
        fila = c.execute("SELECT id FROM provincias WHERE nombre=?", (provincia,)).fetchone()
        if not fila:
            return False            # sin provincia no se puede ubicar el cantón
        pid = fila["id"]
        if c.execute("SELECT 1 FROM cantones WHERE provincia_id=? AND nombre=?",
                     (pid, canton)).fetchone():
            return False
        c.execute(bd.insert_ignorar("cantones", ["provincia_id", "nombre"],
                                    "provincia_id, nombre"), (pid, canton))
    olvidar_cache("cantones:" + provincia, "provincias")
    return True


# ---------------- parámetros ----------------
def cargar_parametros():
    """Parámetros del sistema (valores de pantalla). Se recuerdan unos segundos.

    Se piden en casi todo cálculo de la pantalla (combustible, horarios, estimado del
    viaje...), así que se guardan en memoria; al grabar desde Parámetros se borran.
    """
    return _copiar(_memoria("parametros", _SEGUNDOS_MEMORIA, _leer_parametros))


def _leer_parametros():
    conn = conectar()
    # Se leen todas las columnas de la fila de parámetros: si la base viene de una
    # versión anterior (sin las velocidades del estimado) igual funciona, porque los
    # que falten toman su valor de fábrica aquí abajo.
    row = conn.execute("SELECT * FROM parametros WHERE id=1").fetchone()
    conn.close()
    d = dict(row) if row else {}
    for clave, valor in zip(PARAM_COLS, PARAMS_INICIALES):
        if d.get(clave) is None:
            d[clave] = valor
    for k in list(d):
        if k.startswith("hora_"):
            h, m = str(d[k]).split(":")
            d[k] = time(int(h), int(m))
    return d

def guardar_parametros(d):
    vals = [d[k].strftime("%H:%M") if isinstance(d[k], time) else float(d[k]) for k in PARAM_COLS]
    with conectar() as c:
        c.execute(f"UPDATE parametros SET {', '.join(c2 + '=?' for c2 in PARAM_COLS)} WHERE id=1",
                  vals)
    olvidar_cache("parametros")


# ---------------- viajes ----------------
def guardar_viaje(cab, filas, numero=None, ajuste_numero=0, anio=None):
    """Guarda el viático original o un ajuste del mismo número."""
    conn = conectar()
    try:
        with conn:
            if numero is None:
                # El año sale de la fecha del viaje (así un viático de diciembre
                # registrado en enero conserva la numeración de su año).
                fecha = (filas[0].get("fecha_salida") if filas else None) or ""
                anio = anio or anio_de_fecha(fecha) or anio_actual()
                n = _next(conn, "viatico", anio)
            else:
                n = numero

            cols = ", ".join(VIAJE_COLS)
            marcas = ",".join("?" * len(VIAJE_COLS))
            for fl in filas:
                vals = {"viatico_numero": n, **cab, **fl,
                        "ajuste_numero": ajuste_numero,
                        "tipo_registro": "ORIGINAL" if ajuste_numero == 0 else "AJUSTE"}
                conn.execute(f"INSERT INTO viajes({cols}) VALUES ({marcas})",
                             [vals.get(c) for c in VIAJE_COLS])
        return n
    finally:
        conn.close()


def _estado_viaje(conn, numero):
    """El cierre del viático: estado, justificación, plata de la devolución y firma."""
    cols = ", ".join(VIAJE_COLS_CIERRE)
    row = conn.execute("SELECT " + cols + " FROM viajes WHERE viatico_numero=? LIMIT 1",
                       (numero,)).fetchone()
    return dict(row) if row else {}


def _restaurar_cierre(conn, numero, cierre):
    """Devuelve el cierre del viático tal como estaba, tras reemplazar sus filas.

    La edición borra las filas del viático y las vuelve a escribir con lo que hay en la
    pantalla, que no toca el cierre: después hay que reponer el estado, la justificación,
    la devolución, el pago al empleado y la firma.
    """
    valores = {c: (cierre or {}).get(c) for c in VIAJE_COLS_CIERRE}
    if not valores.get("estado"):
        valores["estado"] = "PENDIENTE"
    asignaciones = ", ".join("%s=?" % c for c in VIAJE_COLS_CIERRE)
    conn.execute("UPDATE viajes SET " + asignaciones + " WHERE viatico_numero=?",
                 [valores[c] for c in VIAJE_COLS_CIERRE] + [numero])


def _insertar_filas(conn, numero, cab, filas, ajuste_numero):
    cols = ", ".join(VIAJE_COLS)
    marcas = ",".join("?" * len(VIAJE_COLS))
    for fl in filas:
        vals = {"viatico_numero": numero, **cab, **fl,
                "ajuste_numero": ajuste_numero,
                "tipo_registro": "ORIGINAL" if ajuste_numero == 0 else "AJUSTE"}
        conn.execute(f"INSERT INTO viajes({cols}) VALUES ({marcas})",
                     [vals.get(c) for c in VIAJE_COLS])


def actualizar_viaje(numero, cab, filas):
    """Reemplaza únicamente el viático original (ajuste_numero=0)."""
    conn = conectar()
    try:
        with conn:
            row = _estado_viaje(conn, numero)
            conn.execute("DELETE FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)=0",
                         (numero,))
            _insertar_filas(conn, numero, cab, filas, 0)
            _restaurar_cierre(conn, numero, row)
    finally:
        conn.close()


def guardar_ajuste_viaje(numero, cab, filas):
    ajuste = proximo_ajuste(numero)
    guardar_viaje(cab, filas, numero=numero, ajuste_numero=ajuste)
    return ajuste


def actualizar_ajuste_viaje(numero, ajuste_numero, cab, filas):
    conn = conectar()
    try:
        with conn:
            row = _estado_viaje(conn, numero)
            conn.execute("DELETE FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)=?",
                         (numero, ajuste_numero))
            _insertar_filas(conn, numero, cab, filas, ajuste_numero)
            _restaurar_cierre(conn, numero, row)
    finally:
        conn.close()


def proximo_ajuste(numero):
    conn = conectar()
    row = conn.execute("SELECT COALESCE(MAX(COALESCE(ajuste_numero,0)),0)+1 AS n FROM viajes "
                       "WHERE viatico_numero=?", (numero,)).fetchone()
    conn.close()
    return int(row["n"] if row else 1)


def eliminar_ajuste(numero, ajuste_numero):
    with conectar() as c:
        c.execute("DELETE FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)=?",
                  (numero, ajuste_numero))


def filas_originales(numero):
    conn = conectar()
    r = [dict(x) for x in conn.execute(
        "SELECT * FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)=0 ORDER BY id",
        (numero,))]
    conn.close()
    return r


def conteo_ajustes():
    """Cuántos ajustes tiene cada viático, en UNA sola consulta.

    Se usa para llenar el historial sin abrir una conexión por viático: eso era lo
    que hacía que la lista tardara en actualizarse cuando había varias computadoras
    trabajando contra la base central.
    """
    conn = conectar()
    try:
        filas = conn.execute("SELECT viatico_numero, COUNT(DISTINCT ajuste_numero) AS n "
                             "FROM viajes WHERE COALESCE(ajuste_numero,0) > 0 "
                             "GROUP BY viatico_numero").fetchall()
        return {int(f["viatico_numero"]): int(f["n"]) for f in filas}
    finally:
        conn.close()


def ajustes_viaje(numero):
    conn = conectar()
    rows = [dict(x) for x in conn.execute(
        "SELECT ajuste_numero, MIN(fecha_salida) fecha_salida, MAX(fecha_regreso) fecha_regreso, "
        "MAX(recibo_ajuste) recibo_ajuste, MAX(orden_combustible) orden_combustible, "
        "MAX(efectivo_combustible) efectivo_combustible, SUM(total) total, "
        "SUM(valor_cajero) valor_cajero "
        "FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)>0 "
        "GROUP BY ajuste_numero ORDER BY ajuste_numero", (numero,))]
    conn.close()
    return rows


def actualizar_recibos(numero, r1, r2, r3):
    """Permite completar/corregir los números de recibo desde la justificación."""
    with conectar() as c:
        c.execute("UPDATE viajes SET recibo_viatico=?, recibo_viatico_2=?, recibo_viatico_3=? "
                  "WHERE viatico_numero=?", (r1, r2, r3, numero))


def guardar_pago_empleado(numero, monto):
    with conectar() as c:
        c.execute("UPDATE viajes SET pago_empleado_monto=? WHERE viatico_numero=?", (monto, numero))


def guardar_devolucion(numero, monto, observacion):
    with conectar() as c:
        c.execute("UPDATE viajes SET devolucion_monto=?, devolucion_observacion=? "
                  "WHERE viatico_numero=?", (float(monto or 0), observacion, numero))


def proximo_numero(anio=None):
    """Número interno del próximo viático del año indicado (por defecto, el actual)."""
    anio = int(anio or anio_actual())
    conn = conectar()
    s = conn.execute("SELECT valor FROM seq WHERE nombre=?", (f"viatico_{anio}",)).fetchone()
    a = (int(s["valor"]) + 1) if s else 1
    b = conn.execute("SELECT COALESCE(MAX(viatico_numero),0) AS maximo FROM viajes "
                     "WHERE viatico_numero>=? AND viatico_numero<?",
                     (clave_viatico(anio, 0), clave_viatico(anio + 1, 0))).fetchone()["maximo"]
    b = (int(b or 0) % FACTOR_ANIO) + 1 if b else 1
    conn.close()
    return clave_viatico(anio, max(a, b))


def numeraciones():
    """Resumen por año: viáticos registrados y cuál sería el próximo número."""
    conn = conectar()
    filas = [dict(x) for x in conn.execute(
        "SELECT viatico_numero, COUNT(*) AS filas FROM viajes GROUP BY viatico_numero")]
    conn.close()
    por_anio = {}
    for f in filas:
        anio = anio_de(f["viatico_numero"])
        if not anio:
            continue
        datos = por_anio.setdefault(anio, {"anio": anio, "viaticos": 0, "ultimo": 0})
        datos["viaticos"] += 1
        datos["ultimo"] = max(datos["ultimo"], numero_visible(f["viatico_numero"]))
    for datos in por_anio.values():
        datos["siguiente"] = proximo_numero(datos["anio"]) % FACTOR_ANIO
    if not por_anio:
        anio = anio_actual()
        por_anio[anio] = {"anio": anio, "viaticos": 0, "ultimo": 0,
                          "siguiente": proximo_numero(anio) % FACTOR_ANIO}
    return [por_anio[a] for a in sorted(por_anio, reverse=True)]


def fijar_inicio(numero, anio=None):
    """Define desde qué número empieza la numeración de un año (superusuario).

    Deja el contador listo para que el próximo viático de ese año sea `numero`.
    Si ya hay viáticos en ese año, nunca baja del siguiente número libre.
    """
    anio = int(anio or anio_actual())
    numero = max(int(numero), 1)
    conn = conectar()
    try:
        with conn:
            fila = conn.execute("SELECT COALESCE(MAX(viatico_numero),0) AS maximo FROM viajes "
                                "WHERE viatico_numero>=? AND viatico_numero<?",
                                (clave_viatico(anio, 0), clave_viatico(anio + 1, 0))).fetchone()
            maximo = int(valor_de(fila, "maximo", 0) or 0)
            existente = (maximo % FACTOR_ANIO) + 1 if maximo else 1
            valor = max(numero, existente)
            conn.execute(bd.insert_ignorar("seq", ["nombre", "valor"], "nombre"),
                         (f"viatico_{anio}", valor - 1))
            conn.execute("UPDATE seq SET valor=? WHERE nombre=?",
                         (valor - 1, f"viatico_{anio}"))
    finally:
        conn.close()
    return clave_viatico(anio, valor)


def listar_viajes(estado=None):
    conn = conectar()
    q, args = "SELECT * FROM viajes", ()
    if estado:
        q += " WHERE estado=?"; args = (estado,)
    q += " ORDER BY viatico_numero DESC"
    r = [dict(x) for x in conn.execute(q, args)]
    conn.close()
    return r

def listar_viaticos_unico():
    """Un registro por viático (resumen), del más nuevo al más viejo.

    Ojo: en PostgreSQL `SELECT * ... GROUP BY` no es válido, por eso aquí todas las
    columnas van dentro de una función de agregación.
    """
    conn = conectar()
    r = [dict(x) for x in conn.execute(
        "SELECT viatico_numero, MIN(fecha_salida) fecha_salida, "
        "MAX(fecha_regreso) fecha_regreso, MAX(responsable) responsable, "
        "MAX(cliente_proyecto) cliente_proyecto, MAX(placa) placa, "
        "MAX(estado) estado, "
        f"{bd.agrupar('nombre_empleado')} empleados, "
        "COUNT(*) filas, SUM(total) total "
        "FROM viajes GROUP BY viatico_numero ORDER BY viatico_numero DESC")]
    conn.close()
    return r

def filas_numero(numero, ajuste_numero=None):
    conn = conectar()
    if ajuste_numero is None:
        r = [dict(x) for x in conn.execute(
            "SELECT * FROM viajes WHERE viatico_numero=? ORDER BY COALESCE(ajuste_numero,0), id",
            (numero,))]
    else:
        r = [dict(x) for x in conn.execute(
            "SELECT * FROM viajes WHERE viatico_numero=? AND COALESCE(ajuste_numero,0)=? ORDER BY id",
            (numero, ajuste_numero))]
    conn.close()
    return r

def obtener_viaje(numero):
    conn = conectar()
    r = conn.execute("SELECT * FROM viajes WHERE viatico_numero=?", (numero,)).fetchone()
    conn.close()
    return dict(r) if r else None

def guardar_elaborado_por(numero, nombre):
    with conectar() as c:
        c.execute("UPDATE viajes SET elaborado_por=? WHERE viatico_numero=?", (nombre, numero))


def guardar_nota_cierre(numero, nota):
    with conectar() as c:
        c.execute("UPDATE viajes SET nota_justificacion=? WHERE viatico_numero=?", (nota, numero))


def justificar(numero, usuario, nota):
    with conectar() as c:
        c.execute(f"UPDATE viajes SET estado='JUSTIFICADO', justificado_por=?, "
                  f"justificado_el={bd.ahora()}, nota_justificacion=? "
                  f"WHERE viatico_numero=?", (usuario, nota, numero))

def anular_viaje(numero):
    with conectar() as c:
        c.execute("UPDATE viajes SET estado='ANULADO' WHERE viatico_numero=?", (numero,))


def reactivar_viaje(numero):
    """Devuelve un viático JUSTIFICADO a PENDIENTE para corregir su justificación."""
    with conectar() as c:
        c.execute("UPDATE viajes SET estado='PENDIENTE', justificado_por=NULL, "
                  "justificado_el=NULL WHERE viatico_numero=? AND estado='JUSTIFICADO'", (numero,))


# ---------------- ajustes ----------------
def guardar_ajuste(numero, empleado, fecha, hora, concepto, otros):
    with conectar() as c:
        c.execute("INSERT INTO ajustes(viatico_numero, nombre_empleado, fecha, hora, concepto, "
                  "otros_gastos) VALUES (?,?,?,?,?,?)",
                  (numero, empleado, fecha, hora, concepto, otros))

def listar_ajustes(numero):
    conn = conectar()
    r = [dict(x) for x in conn.execute(
        "SELECT * FROM ajustes WHERE viatico_numero=? ORDER BY id", (numero,))]
    conn.close()
    return r


# ---------------- gastos de justificación ----------------
CAMPOS_GASTO = ["fecha", "numero_comprobante", "tipo", "ruc", "proveedor", "lugar",
                "hospedaje", "combustible", "buses", "taxis", "alimentacion",
                "peaje", "otros", "total", "nota"]
# Campos que se guardan como número (nota y los de texto quedan fuera).
CAMPOS_GASTO_NUM = ["hospedaje", "combustible", "buses", "taxis", "alimentacion",
                    "peaje", "otros", "total"]

def guardar_gasto(numero, datos):
    datos = dict(datos)
    for k in CAMPOS_GASTO_NUM:
        datos[k] = float(datos.get(k) or 0)
    cols = ", ".join(CAMPOS_GASTO)
    marcas = ",".join("?" * len(CAMPOS_GASTO))
    with conectar() as c:
        cur = c.execute(
            f"INSERT INTO gastos(viatico_numero, {cols}) VALUES (?, {marcas}) RETURNING id",
            [numero] + [datos.get(k) for k in CAMPOS_GASTO])
        fila = cur.fetchone()
        return (fila["id"] if fila else None) or cur.lastrowid

def actualizar_gasto(id_gasto, datos):
    datos = dict(datos)
    for k in CAMPOS_GASTO_NUM:
        datos[k] = float(datos.get(k) or 0)
    with conectar() as c:
        c.execute(f"UPDATE gastos SET {', '.join(k + '=?' for k in CAMPOS_GASTO)} WHERE id=?",
                  [datos.get(k) for k in CAMPOS_GASTO] + [id_gasto])

def eliminar_gasto(id_gasto):
    with conectar() as c:
        c.execute("DELETE FROM gastos WHERE id=?", (id_gasto,))
        c.execute("UPDATE respaldos SET gasto_id=NULL WHERE gasto_id=?", (id_gasto,))

def listar_gastos(numero):
    conn = conectar()
    r = [dict(x) for x in conn.execute(
        "SELECT * FROM gastos WHERE viatico_numero=? ORDER BY fecha, id", (numero,))]
    conn.close()
    return r

def totales_gastos(numero):
    campos = ["hospedaje", "combustible", "buses", "taxis", "alimentacion", "peaje", "otros", "total"]
    conn = conectar()
    row = conn.execute(
        "SELECT " + ", ".join(f"COALESCE(SUM({c}),0) AS {c}" for c in campos) +
        " FROM gastos WHERE viatico_numero=?", (numero,)).fetchone()
    conn.close()
    return {c: float(row[c]) for c in campos} if row else {c: 0.0 for c in campos}

def resumen_viaticos(estado=None):
    conn = conectar()
    args = ()
    where = ""
    if estado:
        where = " WHERE estado=?"
        args = (estado,)
    rows = [dict(x) for x in conn.execute(
        "SELECT viatico_numero, MIN(fecha_salida) fecha_salida, MAX(fecha_regreso) fecha_regreso, "
        "MAX(responsable) responsable, MAX(cliente_proyecto) cliente_proyecto, "
        "MAX(placa) placa, MAX(estado) estado, "
        f"{bd.agrupar('nombre_empleado')} empleados, "
        f"{bd.agrupar('lugar_trabajo')} lugares, "
        "SUM(total) total, SUM(valor_cajero) valor_cajero "
        "FROM viajes" + where + " GROUP BY viatico_numero ORDER BY viatico_numero DESC", args)]
    conn.close()
    return rows


# ---------------- respaldos ----------------
# El archivo puede guardarse de dos maneras (config: "respaldos"."modo"):
#   "carpeta" → en disco (local o carpeta compartida del servidor) y en la base
#               solo queda la ruta.
#   "base"    → los bytes del PDF dentro de la base central; no hace falta
#               carpeta compartida y todas las máquinas ven los mismos archivos.
COLS_RESPALDO = ("id, viatico_numero, nombre_archivo, ruta, empleado, concepto, "
                 "gasto_id, creado_el")


def _carpeta_viatico(numero, crear=True):
    """Carpeta de respaldos de un viático (modo carpeta)."""
    base = cfg.carpeta_respaldos()
    destino = Path(base) / f"viatico_{numero}"
    if crear:
        destino.mkdir(parents=True, exist_ok=True)
    return destino


def _nombre_libre(carpeta, nombre):
    """Devuelve un nombre que no exista todavía dentro de la carpeta."""
    destino = Path(carpeta) / nombre
    if not destino.exists():
        return nombre
    base, ext = os.path.splitext(nombre)
    k = 1
    while destino.exists():
        destino = Path(carpeta) / f"{base}_{k}{ext}"
        k += 1
    return destino.name


# Compresión de las facturas/fotos que se adjuntan: lado más largo en píxeles y
# calidad JPEG. 1600 px se lee perfecto en pantalla y al imprimir, y deja una foto
# de celular (12 MP) en ~250 KB en vez de varios MB.
LADO_MAX = 1600
CALIDAD_JPEG = 72


def _a_pdf(ruta_origen, carpeta):
    """Copia el archivo a la carpeta, convirtiendo imágenes a PDF. Devuelve la ruta.

    Las fotos y escaneos se **comprimen** antes de guardarlos: el lado más largo se
    reduce a `LADO_MAX` px y se guardan como JPEG de calidad `CALIDAD_JPEG`. Una foto
    de celular (12 MP, varios MB) queda en ~250 KB y la factura se sigue leyendo
    perfectamente para contabilidad; así ni la base ni el respaldo crecen de más.
    (`thumbnail` solo encoge: una imagen que ya es chica no se toca.)
    """
    nombre = os.path.basename(ruta_origen)
    ext = os.path.splitext(nombre)[1].lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"):
        destino = Path(carpeta) / _nombre_libre(carpeta, os.path.splitext(nombre)[0] + ".pdf")
        from PIL import Image
        img = Image.open(ruta_origen)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((LADO_MAX, LADO_MAX), Image.LANCZOS)
        img.save(str(destino), "PDF", resolution=100, quality=CALIDAD_JPEG)
    else:
        destino = Path(carpeta) / _nombre_libre(carpeta, nombre)
        import shutil
        shutil.copyfile(ruta_origen, destino)
    return destino


def agregar_respaldo(numero, ruta_origen, empleado=None, concepto=None, gasto_id=None):
    """Adjunta un respaldo. Las imágenes (jpg/png/…) se convierten automáticamente a PDF."""
    if cfg.modo_respaldos() == "base":
        import tempfile
        with tempfile.TemporaryDirectory(prefix="respaldo_") as tmp:
            pdf = _a_pdf(ruta_origen, tmp)
            contenido = pdf.read_bytes()
            nombre = pdf.name
    else:
        pdf = _a_pdf(ruta_origen, _carpeta_viatico(numero))
        contenido = None
        nombre = pdf.name
        ruta = str(pdf)
    with conectar() as c:
        if contenido is None:
            c.execute("INSERT INTO respaldos(viatico_numero, nombre_archivo, ruta, empleado, "
                      "concepto, gasto_id) VALUES (?,?,?,?,?,?)",
                      (numero, nombre, ruta, empleado, concepto, gasto_id))
        else:
            c.execute("INSERT INTO respaldos(viatico_numero, nombre_archivo, ruta, empleado, "
                      "concepto, gasto_id, contenido) VALUES (?,?,?,?,?,?,?)",
                      (numero, nombre, None, empleado, concepto, gasto_id, contenido))
    return nombre


def contenido_respaldo(id_):
    """Bytes del archivo guardado dentro de la base (None si está en carpeta)."""
    conn = conectar()
    row = conn.execute("SELECT contenido FROM respaldos WHERE id=?", (id_,)).fetchone()
    conn.close()
    if not row:
        return None
    datos = row["contenido"]
    return bytes(datos) if datos is not None else None


def ruta_para_abrir(respaldo):
    """Devuelve una ruta de archivo real para ver/abrir un respaldo.

    Si el archivo está dentro de la base, se escribe una copia temporal.
    """
    ruta = respaldo.get("ruta") if isinstance(respaldo, dict) else None
    if ruta and os.path.exists(ruta):
        return ruta
    datos = contenido_respaldo(respaldo.get("id")) if isinstance(respaldo, dict) else None
    if not datos:
        return None
    import tempfile
    carpeta = Path(tempfile.gettempdir()) / "viaticos_respaldos"
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / (respaldo.get("nombre_archivo") or f"respaldo_{respaldo.get('id')}.pdf")
    try:
        destino.write_bytes(datos)
    except OSError:
        destino = carpeta / f"respaldo_{respaldo.get('id')}.pdf"
        destino.write_bytes(datos)
    return str(destino)

def listar_respaldos(numero, empleado=None, concepto=None, gasto_id=None):
    conn = conectar()
    q = f"SELECT {COLS_RESPALDO} FROM respaldos WHERE viatico_numero=?"
    args = [numero]
    if empleado:
        q += " AND empleado=?"; args.append(empleado)
    if concepto:
        q += " AND concepto=?"; args.append(concepto)
    if gasto_id is not None:
        q += " AND gasto_id=?"; args.append(gasto_id)
    r = [dict(x) for x in conn.execute(q + " ORDER BY id", args)]
    conn.close()
    return r

def eliminar_respaldo(id_):
    conn = conectar()
    row = conn.execute("SELECT ruta FROM respaldos WHERE id=?", (id_,)).fetchone()
    with conn:
        conn.execute("DELETE FROM respaldos WHERE id=?", (id_,))
    conn.close()
    if row and row["ruta"]:
        try:
            os.remove(row["ruta"])
        except OSError:
            pass


def listar_respaldos_completo(numero):
    """Respaldos del viático (registrados + archivos que estén en la carpeta).

    En modo "base" solo existen los registros; en modo "carpeta" se agregan los
    archivos que estén en disco sin registro (por ejemplo de versiones anteriores).
    """
    registros = listar_respaldos(numero)
    if cfg.modo_respaldos() == "base":
        return registros
    vistos = {os.path.abspath(r["ruta"]).lower() for r in registros if r.get("ruta")}
    carpeta = _carpeta_viatico(numero, crear=False)
    extras = []
    if carpeta.exists():
        for f in sorted(carpeta.iterdir()):
            if f.is_file() and os.path.abspath(str(f)).lower() not in vistos:
                extras.append({"id": None, "viatico_numero": numero,
                               "nombre_archivo": f.name, "ruta": str(f),
                               "empleado": "", "concepto": "EN CARPETA",
                               "gasto_id": None, "creado_el": ""})
    return registros + extras


def listar_todos_respaldos():
    """Todos los respaldos (para la ventana 📁 RESPALDOS)."""
    conn = conectar()
    registros = [dict(x) for x in conn.execute(
        f"SELECT {COLS_RESPALDO} FROM respaldos ORDER BY viatico_numero, id")]
    conn.close()
    for r in registros:
        if not r.get("concepto"):
            r["concepto"] = "EN CARPETA" if r.get("ruta") else "EN LA BASE"
    if cfg.modo_respaldos() == "base":
        registros.sort(key=lambda r: (-r["viatico_numero"],
                                      (r.get("nombre_archivo") or "").lower()))
        return registros
    vistos = {os.path.abspath(r["ruta"]).lower() for r in registros if r.get("ruta")}
    base = cfg.carpeta_respaldos()
    extras = []
    if base.exists():
        for carpeta in sorted(base.iterdir()):
            if not carpeta.is_dir() or not carpeta.name.startswith("viatico_"):
                continue
            try:
                num = int(carpeta.name.split("_", 1)[1])
            except (IndexError, ValueError):
                continue
            for f in sorted(carpeta.iterdir()):
                if f.is_file() and os.path.abspath(str(f)).lower() not in vistos:
                    extras.append({"id": None, "viatico_numero": num,
                                   "nombre_archivo": f.name, "ruta": str(f),
                                   "empleado": "", "concepto": "EN CARPETA",
                                   "gasto_id": None, "creado_el": ""})
    todos = registros + extras
    todos.sort(key=lambda r: (-r["viatico_numero"], (r.get("nombre_archivo") or "").lower()))
    return todos


def consolidar_respaldos_pdf(numero):
    """Une TODOS los respaldos del viático en un único PDF y borra los individuales.

    Así en la carpeta de respaldos queda un solo archivo por viático
    (`VIATICO_n_COMPLETO.pdf`) tal como se pidió: si se subieron 10 imágenes,
    no se conservan los 10 PDF sueltos.

    Con el viático ya justificado, el completo anterior se usa como primera
    parte de la nueva unión para no perder ninguna factura previa. Funciona
    igual si los respaldos están en una carpeta o dentro de la base.
    """
    nombre_completo = f"VIATICO_{db_etiqueta_archivo(numero)}_COMPLETO.pdf"
    registros = listar_respaldos_completo(numero)
    completo = next((r for r in registros
                     if (r.get("nombre_archivo") or "").upper() == nombre_completo.upper()),
                    None)
    sueltos = [r for r in registros if r is not completo]
    if not sueltos:
        # Nada nuevo que unir: el completo que ya existe se conserva tal cual.
        return (ruta_para_abrir(completo) if completo else None)

    import tempfile
    with tempfile.TemporaryDirectory(prefix=f"union_{numero}_") as tmp:
        fuentes = []
        if completo:
            ruta_previa = ruta_para_abrir(completo)
            if ruta_previa:
                fuentes.append(ruta_previa)
        for i, r in enumerate(sueltos):
            ruta = ruta_para_abrir(r)
            if not ruta:
                continue
            if not str(ruta).lower().endswith(".pdf"):
                continue
            if completo and os.path.abspath(ruta) == os.path.abspath(ruta_para_abrir(completo) or ""):
                continue
            fuentes.append(ruta)
        if not fuentes:
            return None
        try:
            from PyPDF2 import PdfMerger
        except Exception:
            from PyPDF2 import PdfFileMerger as PdfMerger
        temporal = Path(tmp) / nombre_completo
        unido = False
        merger = PdfMerger()
        try:
            for p in fuentes:
                merger.append(p)
            merger.write(str(temporal))
            unido = temporal.exists() and temporal.stat().st_size > 0
        finally:
            merger.close()
        if not unido:
            # No se pudo unir: se conservan los respaldos individuales.
            return None
        contenido = temporal.read_bytes()

    if cfg.modo_respaldos() == "base":
        with conectar() as c:
            if completo and completo.get("id"):
                c.execute("UPDATE respaldos SET contenido=?, nombre_archivo=?, concepto=? "
                          "WHERE id=?",
                          (contenido, nombre_completo, "PDF CONSOLIDADO", completo["id"]))
            else:
                c.execute("INSERT INTO respaldos(viatico_numero, nombre_archivo, ruta, empleado, "
                          "concepto, gasto_id, contenido) VALUES (?,?,?,?,?,?,?)",
                          (numero, nombre_completo, None, None, "PDF CONSOLIDADO", None,
                           contenido))
            for r in sueltos:
                if r.get("id"):
                    c.execute("DELETE FROM respaldos WHERE id=?", (r["id"],))
        return f"base:{numero}"

    # modo carpeta: se escribe el archivo y se borran los individuales
    dest_dir = _carpeta_viatico(numero)
    dest = dest_dir / nombre_completo
    temporal2 = dest_dir / f"{nombre_completo}.tmp.pdf"
    temporal2.write_bytes(contenido)
    try:
        os.replace(str(temporal2), str(dest))
    except OSError:
        try:
            os.remove(str(temporal2))
        except OSError:
            pass
        return None
    for r in sueltos:
        if r.get("ruta"):
            try:
                os.remove(r["ruta"])
            except OSError:
                pass
    with conectar() as c:
        for r in sueltos:
            if r.get("id"):
                c.execute("DELETE FROM respaldos WHERE id=?", (r["id"],))
        row = c.execute("SELECT id FROM respaldos WHERE viatico_numero=? AND ruta=?",
                        (numero, str(dest))).fetchone()
        if row:
            c.execute("UPDATE respaldos SET nombre_archivo=?, concepto=? WHERE id=?",
                      (dest.name, "PDF CONSOLIDADO", row["id"]))
        else:
            c.execute("INSERT INTO respaldos(viatico_numero, nombre_archivo, ruta, empleado, "
                      "concepto, gasto_id) VALUES (?,?,?,?,?,?)",
                      (numero, dest.name, str(dest), None, "PDF CONSOLIDADO", None))
    return str(dest)


# ---------------- memoria temporal (lo que se está llenando) ----------------
# Para que nadie pierda la captura: mientras la pantalla de viáticos está abierta, lo que
# va escrito se guarda solo (cada 20 segundos y al cerrar la ventana) en la tabla
# `borradores`, **por usuario**. Si el sistema se cierra por error —o se apaga la
# computadora—, la persona vuelve a entrar con su clave y el sistema le ofrece recuperar
# lo que estaba haciendo: en la misma PC o en cualquier otra, porque el borrador queda en
# la base (la central, si trabaja contra el servidor). Al guardar el viático o al limpiar
# el formulario el borrador se borra solo, así que nunca sale un aviso por algo ya guardado.
DIAS_BORRADOR = 30                  # los borradores más viejos que esto se descartan


def _clave_borrador(usuario) -> str:
    """Nombre con el que se guarda el borrador: el usuario de la sesión (o un texto).

    Se usa el **usuario** (el de la clave) y no el nombre completo, que es el que la
    persona escribe al entrar: así lo que dejó a medio llenar lo recupera ella misma, en
    esta computadora o en otra.
    """
    if isinstance(usuario, dict):
        nombre = usuario.get("usuario") or usuario.get("nombre") or ""
    else:
        nombre = usuario or ""
    return str(nombre).strip().upper()


def guardar_borrador(usuario, datos, pantalla="viatico") -> bool:
    """Guarda (o reemplaza) lo que un usuario lleva escrito. Nunca interrumpe el trabajo.

    Es una ayuda, no un dato del viático: si falla (servidor caído a mitad de la captura,
    por ejemplo) se anota en la consola y el usuario sigue trabajando tranquilo.
    """
    clave = _clave_borrador(usuario)
    if not clave:
        return False
    try:
        texto = json.dumps(datos or {}, ensure_ascii=False)
    except Exception as ex:
        print(f"No se pudo preparar el borrador: {ex}")
        return False
    try:
        with conectar() as c:
            c.execute("DELETE FROM borradores WHERE usuario=?", (clave,))
            c.execute("INSERT INTO borradores(usuario, pantalla, datos) VALUES (?,?,?)",
                      (clave, (pantalla or "viatico"), texto))
        return True
    except Exception as ex:
        print(f"No se pudo guardar el borrador: {ex}")
        return False


def leer_borrador(usuario, pantalla=None):
    """Lo que ese usuario dejó a medio llenar, o None si no hay nada.

    Devuelve {"datos": {...}, "pantalla": "...", "actualizado_el": "AAAA-MM-DD HH:MM:SS"}.
    `datos` es lo que la pantalla de viáticos armó con `_estado_formulario()`.
    """
    clave = _clave_borrador(usuario)
    if not clave:
        return None
    try:
        conn = conectar()
        q = "SELECT pantalla, datos, actualizado_el FROM borradores WHERE usuario=?"
        args = [clave]
        if pantalla:
            q += " AND pantalla=?"
            args.append(pantalla)
        fila = conn.execute(q, args).fetchone()
        conn.close()
        if not fila:
            return None
        return {"datos": json.loads(fila["datos"] or "{}"),
                "pantalla": fila["pantalla"] or "viatico",
                "actualizado_el": fila["actualizado_el"] or ""}
    except Exception as ex:
        print(f"No se pudo leer el borrador: {ex}")
        return None


def borrar_borrador(usuario, pantalla=None) -> int:
    """Olvida lo que ese usuario tenía a medio llenar (al guardar el viático o al limpiar)."""
    clave = _clave_borrador(usuario)
    if not clave:
        return 0
    try:
        with conectar() as c:
            if pantalla:
                r = c.execute("DELETE FROM borradores WHERE usuario=? AND pantalla=?",
                              (clave, pantalla))
            else:
                r = c.execute("DELETE FROM borradores WHERE usuario=?", (clave,))
        return int(getattr(r, "rowcount", 0) or 0)
    except Exception as ex:
        print(f"No se pudo borrar el borrador: {ex}")
        return 0


def usuarios_con_borrador():
    """Quiénes tienen algo a medio llenar (usuario, pantalla y cuándo se guardó)."""
    try:
        conn = conectar()
        r = [dict(x) for x in conn.execute(
            "SELECT usuario, pantalla, actualizado_el FROM borradores "
            "ORDER BY actualizado_el DESC")]
        conn.close()
        return r
    except Exception:
        return []


def borrar_borradores_viejos(dias=DIAS_BORRADOR, conn=None) -> int:
    """Descarta los borradores de más de `dias` días y devuelve cuántos borró.

    La memoria temporal es para no perder el trabajo del día: no tiene sentido guardar
    capturas a medias para siempre (menos en la central, que la ven todas las PC). Corre
    al abrir el sistema (ver `init_db`), que ya trae su propia conexión abierta: por eso
    se le puede pasar (`conn`); si no, abre una. Se comparan los textos de la fecha, así
    funciona igual en SQLite y en PostgreSQL.
    """
    try:
        limite = (_fechahora.now() - timedelta(days=int(dias or DIAS_BORRADOR))
                  ).strftime("%Y-%m-%d %H:%M:%S")
        sql, args = "DELETE FROM borradores WHERE actualizado_el < ?", (limite,)
        if conn is not None:
            r = conn.execute(sql, args)
        else:
            with conectar() as c:
                r = c.execute(sql, args)
        return int(getattr(r, "rowcount", 0) or 0)
    except Exception:
        return 0


# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
