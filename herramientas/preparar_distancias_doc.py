# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
# -*- coding: utf-8 -*-
"""preparar_distancias_doc.py — Pasa el Word «DISTANCIAS DOC.docx» al formato del sistema.

Entrada: `sistema_viaticos_miempresa\\excel\\DISTANCIAS DOC.docx`, el documento que la
empresa revisó **cantón por cantón**: por cada destino trae la cabecera cantonal, la ruta
terrestre principal, la distancia real y **dos tiempos** (en auto y en autobús).

Qué hace (no toca el .docx y a la base de datos solo la lee):

  1. Lee las tablas del documento (una por provincia) y saca de cada fila el cantón, la
     cabecera, la ruta, los km y los dos tiempos.
  2. Deja **una sola hora por cantón** —como la que ya usa el sistema— calculándola con
     las dos columnas del documento según la regla de `--horas`:
         promedio (por defecto) = punto medio entre el auto y el autobús;
         auto                   = el tiempo del auto;
         auto1                  = el tiempo del auto + 1 h (la regla del Excel anterior);
         bus                    = el tiempo del autobús;
         bus1                   = el tiempo del autobús − 1 h (las paradas del bus).
     Las horas quedan en múltiplos de 5 minutos y se guardan en decimal (6.0 = 6:00),
     que es como las usa el cálculo; en pantalla se ven como «6 h 00 min».
     Con «promedio» MACAS queda en 6:00, así que el viático sale igual que con los 5:40
     que se venían usando (los dos redondean a 6 h de recorrido).
  3. Iguala los nombres al sistema (MORONA → MACAS, NAPO → TENA, PASTAZA → PUYO,
     LAGO AGRIO → NUEVA LOJA, …). Los cantones que el sistema **no** tiene no se cargan:
     quedan anotados en el reporte y en la segunda hoja del Excel.
  4. Deja dos Excel en la carpeta `excel\\`:
       «DISTANCIAS Y TIEMPOS DESDE CUENCA (DOC).xlsx» — todo lo del documento (ruta, km,
         auto, autobús) más las horas que usará el sistema, para revisar y archivar;
       «TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx» — el de tres columnas
         (CANTÓN · KM DESDE CUENCA · HORAS DE VIAJE), con el formato exacto que lee
         PARÁMETROS → 🗺️ Provincias y km → 📥 Importar Excel.
  5. Reporte `herramientas\\distancias_doc_resultado.txt` con el antes/después de cada
     cantón: km, horas en h:min y el **recorrido redondeado a la hora entera**, que es lo
     que de verdad cambia la llegada del viático.
  6. Deja en `servidor\\` los .sql `viaticos_distancias_NUEVO.sql` y
     `viaticos_distancias_ANTES.sql` para cargar los mismos km y horas (o volver atrás) en
     la base central con `psql`, sin abrir el sistema; `cargar_distancias.bat` los carga de
     una sola vez.

Uso:
    python herramientas\\preparar_distancias_doc.py
    python herramientas\\preparar_distancias_doc.py --horas auto
    python herramientas\\preparar_distancias_doc.py --horas auto1 --sql-dir "C:\\otra\\carpeta"
"""
import argparse
import math
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
APP = AQUI.parent / "sistema_viaticos_miempresa"
ENTRADA = APP / "excel" / "DISTANCIAS DOC.docx"
SALIDA_INFO = APP / "excel" / "DISTANCIAS Y TIEMPOS DESDE CUENCA (DOC).xlsx"
SALIDA_SISTEMA = APP / "excel" / "TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx"
REPORTE = AQUI / "distancias_doc_resultado.txt"

# Valores que la empresa dejó **puestos a mano** en el sistema (Parámetros → 🗺️ Provincias
# y km) y que este documento **no** debe pisar. YANTZAZA entró al catálogo en la versión 8.3
# con 215 km y 5 h; el Word dice 231 km y 5 h 30 min, así que se respeta lo de la empresa (y
# el reporte lo marca). Si algún día se decide usar el dato del Word, se borra de aquí.
FIJOS = {"YANTZAZA": {"km": 215, "horas": 5.0}}

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REGLAS = ("promedio", "auto", "auto1", "bus", "bus1")
REGLA = "promedio"
EXPLICACION = {
    "promedio": "punto medio entre el auto y el autobús",
    "auto": "el tiempo del auto del documento",
    "auto1": "el tiempo del auto más 1 h de margen",
    "bus": "el tiempo del autobús del documento",
    "bus1": "el tiempo del autobús menos 1 h (las paradas)",
}

# Nombres del documento que en el sistema se llaman de otra forma. La clave es el nombre
# del documento sin tildes y en mayúsculas; el valor, el nombre tal como lo tiene el
# sistema (los del combo PARÁMETROS → 🗺️ Provincias y km).
ALIAS = {
    "CHORDELEG": "CHORDALEG",                       # en el sistema quedó sin la «o»
    "ALFREDO BAQUERIZO M.": "ALFREDO BAQUERIZO MORENO",
    "CNEL. MARCELINO MARIDUENA": "MARCELINO MARIDUENA",
    "SAN JACINTO DE YAGUACHI": "YAGUACHI",
    "VEINTICUATRO DE MAYO": "24 DE MAYO",
    "MORONA": "MACAS",                              # Morona (Macas) = la cabecera
    "NAPO": "TENA",
    "ORELLANA": "FRANCISCO DE ORELLANA",
    "PASTAZA": "PUYO",
    "LAGO AGRIO": "NUEVA LOJA",
    "BANOS DE AGUA SANTA": "BAÑOS",
}

sys.path.insert(0, str(APP))
os.environ.setdefault("VIATICOS_MOTOR", "sqlite")        # nunca el servidor


# --------------------------------------------------------------- texto del Word
def _texto(el):
    """Texto de un párrafo o de una celda del Word ('' si está vacío)."""
    partes = []
    for p in el.iter(W + "p"):
        trozos = "".join(t.text or "" for t in p.iter(W + "t"))
        if trozos.strip():
            partes.append(trozos.strip())
    return " ".join(partes).strip()


def _sin_tildes(texto):
    """Mayúsculas sin tildes, para comparar nombres («SÍGSIG» = «SIGSIG»)."""
    t = unicodedata.normalize("NFKD", (texto or "").strip().upper())
    return re.sub(r"\s+", " ", "".join(c for c in t if not unicodedata.combining(c)))


def _minutos(celda):
    """Minutos de «1 h 05 min», «55 min» o «6 h 50 min (Auto)». None si no hay dato."""
    h = re.search(r"(\d+)\s*h", celda or "")
    m = re.search(r"(\d+)\s*min", celda or "")
    if not h and not m:
        return None
    return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)


def _km(celda):
    """Km de «182,5 km» o «322 km (Vía)». None si la celda no trae kilómetros."""
    m = re.search(r"([\d.]+(?:,\d+)?)\s*km", celda or "", flags=re.I)
    if not m:
        return None
    return float(m.group(1).replace(".", "").replace(",", "."))


def _hhmm(minutos):
    """«5:40» de 340 minutos (para el reporte y los Excel)."""
    if minutos is None:
        return "—"
    return "%d:%02d" % (int(minutos) // 60, int(minutos) % 60)


def _horas_texto(horas):
    """«5 h 40 min» de 5.67 (el mismo formato de la pantalla del sistema)."""
    total = int(round((horas or 0) * 60))
    return "%d h %02d min" % (total // 60, total % 60)


def _recorrido(horas):
    """Horas de recorrido que usa el viático: las horas **hacia arriba** a la hora entera.

    Es la misma regla de `q_viaje.recorrido_de_viaje` (y después se le suman las comidas
    que caen dentro del viaje). Sirve para que el reporte muestre lo que de verdad
    cambia en la llegada.
    """
    try:
        return max(1, int(math.ceil(float(horas or 0) - 1e-9)))
    except (TypeError, ValueError):
        return 0


def leer_doc(ruta):
    """Filas del documento: [{prov, cantón, cabecera, ruta, km, auto, bus, nota}].

    Cada tabla del Word es una provincia (el título del párrafo anterior la nombra) y la
    primera fila es el encabezado. Los km y los tiempos se leen del texto («182,5 km»,
    «5 h 15 min»), así que no dependen del formato de las celdas.
    """
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    filas, provincia = [], ""
    for hijo in raiz.find(W + "body"):
        if hijo.tag == W + "p":
            m = re.match(r"^\d+\.\s*Provincia de (.+)$", _texto(hijo))
            if m:
                provincia = m.group(1).strip()
        elif hijo.tag == W + "tbl":
            for tr in hijo.findall(W + "tr"):
                celdas = [_texto(tc) for tc in tr.findall(W + "tc")]
                if len(celdas) < 6 or _sin_tildes(celdas[0]).startswith("CANTON"):
                    continue
                notas = [c for c in (celdas[3], celdas[4], celdas[5]) if "(" in c]
                filas.append({
                    "prov": provincia, "canton": celdas[0], "cabecera": celdas[1],
                    "ruta": celdas[2], "km_txt": celdas[3], "auto_txt": celdas[4],
                    "bus_txt": celdas[5], "km": _km(celdas[3]),
                    "auto": _minutos(celdas[4]), "bus": _minutos(celdas[5]),
                    "nota": " ".join(notas).strip(),
                })
    return filas


def horas_de_regla(auto, bus, regla):
    """Las horas (decimales) que se guardan, sacadas de los dos tiempos del documento.

    Se redondean a múltiplos de 5 minutos, que es la precisión con la que se manejan los
    tiempos de viaje (y así lo que se guarda no queda con decimales raros).
    """
    if regla == "auto":
        minutos = auto
    elif regla == "bus":
        minutos = bus
    elif regla == "auto1":
        minutos = auto + 60
    elif regla == "bus1":
        minutos = bus - 60
    else:
        minutos = (auto + bus) / 2.0
    minutos = max(0, int(round(minutos / 5.0)) * 5)
    return round(minutos / 60.0, 2)


def cantones_sistema():
    """{(PROVINCIA, CANTÓN) sin tildes: nombre del sistema} de los del formulario.

    Se leen de la base local; si este equipo no la tiene (por ejemplo el servidor recién
    instalado), se usan los de fábrica (`database.PROV_CANT`).
    """
    import sqlite3
    ruta = APP / "data" / "viaticos.db"
    pares = []
    if ruta.exists():
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % ruta.as_posix(), uri=True)
            pares = [(str(p), str(c)) for p, c in conn.execute(
                "SELECT p.nombre, c.nombre FROM cantones c "
                "JOIN provincias p ON p.id=c.provincia_id")]
            conn.close()
        except Exception as ex:
            print("   (no se pudieron leer los cantones de la base local: %s)" % ex)
    if not pares:
        import database as db                       # no abre la base al importar
        pares = [(prov, canton)
                 for prov, cantones in db.PROV_CANT.items() for canton in cantones]
    return {(_sin_tildes(p), _sin_tildes(c)): c for p, c in pares}


def valores_actuales():
    """{CANTÓN: (km, horas)} de la tabla de rutas de la base local (solo lectura)."""
    import sqlite3
    ruta = APP / "data" / "viaticos.db"
    datos = {}
    if not ruta.exists():
        return datos
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % ruta.as_posix(), uri=True)
        for canton, km, horas in conn.execute("SELECT canton, km, horas FROM distancias"):
            datos[_sin_tildes(str(canton))] = (
                float(km) if km is not None else None,
                float(horas) if horas is not None else None)
        conn.close()
    except Exception as ex:
        print("   (no se pudo leer la tabla de rutas: %s)" % ex)
    return datos


def igualar(prov, canton, sistema, por_canton):
    """Nombre que el sistema usa para ese cantón, o None si el sistema no lo tiene.

    Se prueba en orden: el nombre tal cual con su provincia, la tabla de equivalencias
    (`ALIAS`, por el nombre del cantón) y, al final, el cantón suelto cuando el sistema
    tiene **uno solo** con ese nombre («Sígsig» → SIGSIG, «Sucúa» → SUCÚA).
    """
    clave = (_sin_tildes(prov), _sin_tildes(canton))
    if clave in sistema:
        return sistema[clave]
    parecido = ALIAS.get(clave[1])
    if parecido:
        for _par, nombre in sistema.items():
            if _sin_tildes(nombre) == _sin_tildes(parecido):
                return nombre
        return None
    candidatos = por_canton.get(clave[1]) or []
    return candidatos[0] if len(candidatos) == 1 else None


# ------------------------------------------------------------------- Excel
def _guardar(wb, destino):
    """Guarda el Excel. Si está abierto en Excel, lo deja al lado con «(2)».

    Windows no deja escribir un archivo que está abierto: en ese caso se guarda con otro
    nombre (para no perder el trabajo) y se avisa en pantalla, para cerrarlo y volver a
    correr la herramienta.

    (La escritura en pantalla se hace sin acentos a propósito: la consola de Windows no
    siempre los muestra bien.)
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        wb.save(destino)
        return destino
    except PermissionError:
        alterno = destino.with_name("%s (2)%s" % (destino.stem, destino.suffix))
        wb.save(alterno)
        print("  ATENCION: «%s» esta abierto en Excel; se guardo como «%s»."
              % (destino.name, alterno.name))
        return alterno


def _escribir_texto(ruta, texto):
    """Escribe un archivo de texto; si está abierto en otro programa, avisa y sigue."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        ruta.write_text(texto, encoding="utf-8")
    except PermissionError:
        print("  ATENCION: «%s» esta abierto en otro programa; no se pudo actualizar."
              % ruta.name)
    return ruta


def escribir_sistema(filas, destino, nota):
    """Excel de tres columnas (CANTÓN · KM · HORAS), el que lee «📥 Importar Excel».

    Los encabezados van en la fila 7 —igual que `TIEMPOS DE VIAJE MIEMPRESA.xlsx`— para
    que el botón de Parámetros → 🗺️ Provincias y km lo lea igual.
    """
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = openpyxl.Workbook()
    hoja = wb.active
    hoja.title = "Tiempos de viaje"
    amarillo = PatternFill("solid", fgColor="FFEB9C")
    lado = Side(style="thin", color="B7B7B7")
    borde = Border(left=lado, right=lado, top=lado, bottom=lado)

    hoja["A1"] = "TIEMPOS DE VIAJE DESDE CUENCA — MIEMPRESA (PROPUESTA)"
    hoja["A1"].font = Font(bold=True, size=13)
    hoja["A2"] = nota
    hoja["A3"] = ("Para cargarlo al sistema: PARÁMETROS → 🗺️ Provincias y km → "
                  "📥 Importar Excel.")
    hoja["A4"] = ("Revíselo antes de importar: al importar, estos cantones quedan con los km "
                  "y las horas de este archivo (los de hoy se reemplazan).")
    hoja["A5"] = ("Las horas van en decimal (6 = 6:00) porque así las lee el sistema; en la "
                  "pantalla se ven como «6 h 00 min».")
    hoja["A6"] = ("A las horas de viaje el sistema les suma una hora por cada comida que cae "
                  "dentro del viaje (desayuno 06:00, almuerzo 13:00 y merienda 21:00) y "
                  "redondea el recorrido hacia arriba a la hora entera.")
    for fila in (2, 3, 4, 5, 6):
        hoja.cell(row=fila, column=1).font = Font(size=9, italic=True)

    for j, titulo in enumerate(("CANTÓN", "KM DESDE CUENCA", "HORAS DE VIAJE (IDA)"), start=1):
        c = hoja.cell(row=7, column=j, value=titulo)
        c.font = Font(bold=True)
        c.fill = amarillo
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borde
    for i, (canton, km, horas) in enumerate(filas, start=8):
        for j, valor in enumerate((canton, km, horas), start=1):
            c = hoja.cell(row=i, column=j, value=valor)
            c.border = borde
            if j > 1:
                c.alignment = Alignment(horizontal="center")
        hoja.cell(row=i, column=2).number_format = "0"
        hoja.cell(row=i, column=3).number_format = "0.00"
    hoja.column_dimensions["A"].width = 34
    hoja.column_dimensions["B"].width = 18
    hoja.column_dimensions["C"].width = 22
    hoja.freeze_panes = "A8"
    return _guardar(wb, destino)


def escribir_info(filas, fuera, destino, regla, entrada):
    """Excel con todo lo del documento y, al lado, lo que quedará en el sistema.

    Es el archivo para revisar y archivar: trae tal cual lo que dice el Word (ruta, km y
    los dos tiempos) y el antes/después de lo que hay hoy en el sistema.
    """
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = openpyxl.Workbook()
    hoja = wb.active
    hoja.title = "Distancias desde Cuenca"
    amarillo = PatternFill("solid", fgColor="FFEB9C")
    lado = Side(style="thin", color="B7B7B7")
    borde = Border(left=lado, right=lado, top=lado, bottom=lado)

    hoja["A1"] = "DISTANCIAS Y TIEMPOS DE VIAJE DESDE CUENCA — MIEMPRESA"
    hoja["A1"].font = Font(bold=True, size=13)
    hoja["A2"] = ("Sacado de «%s»: el documento que la empresa revisó cantón por cantón."
                  % entrada.name)
    hoja["A3"] = ("Las horas que usa el sistema salen de los dos tiempos del documento: %s."
                  % EXPLICACION[regla])
    hoja["A4"] = ("Las horas se guardan en decimal (6 = 6:00) y en pantalla se ven como "
                  "«6 h 00 min». El recorrido es lo que de verdad se le suma al viático: las "
                  "horas redondeadas hacia arriba a la hora entera.")
    for fila in (2, 3, 4):
        hoja.cell(row=fila, column=1).font = Font(size=9, italic=True)

    encabezados = ("PROVINCIA", "CANTÓN (COMO LO TIENE EL SISTEMA)", "CABECERA CANTONAL",
                   "RUTA TERRESTRE PRINCIPAL", "DISTANCIA (DOC)", "KM QUE SE CARGAN",
                   "TIEMPO (AUTO)", "TIEMPO (AUTOBÚS)", "HORAS QUE USA EL SISTEMA",
                   "HORAS (DECIMAL)", "KM DE ANTES", "HORAS DE ANTES", "RECORRIDO (H)",
                   "OBSERVACIÓN")
    for j, titulo in enumerate(encabezados, start=1):
        c = hoja.cell(row=6, column=j, value=titulo)
        c.font = Font(bold=True)
        c.fill = amarillo
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borde
    for i, f in enumerate(filas, start=7):
        valores = (f["prov"].title(), f["canton"], f["cabecera"], f["ruta"], f["km_txt"],
                   f["km"], _hhmm(f["auto"]), _hhmm(f["bus"]), _horas_texto(f["horas"]),
                   f["horas"], f["km_hoy"], _horas_texto(f["horas_hoy"]) if f["horas_hoy"]
                   else "—", _recorrido(f["horas"]), f["nota"])
        for j, valor in enumerate(valores, start=1):
            c = hoja.cell(row=i, column=j, value=valor)
            c.border = borde
            if j in (5, 7, 8, 9, 10, 11, 12, 13):
                c.alignment = Alignment(horizontal="center")
        hoja.cell(row=i, column=6).number_format = "0"
        hoja.cell(row=i, column=10).number_format = "0.00"
    for columna, ancho in (("A", 18), ("B", 30), ("C", 20), ("D", 44), ("E", 13), ("F", 14),
                           ("G", 12), ("H", 13), ("I", 21), ("J", 14), ("K", 11), ("L", 13),
                           ("M", 12), ("N", 30)):
        hoja.column_dimensions[columna].width = ancho
    hoja.freeze_panes = "C7"

    hoja2 = wb.create_sheet("Cantones sin cargar")
    hoja2["A1"] = ("CANTONES DEL DOCUMENTO QUE EL SISTEMA TODAVÍA NO OFRECE (%d)"
                   % len(fuera))
    hoja2["A1"].font = Font(bold=True, size=12)
    hoja2["A2"] = ("No se cargan: el formulario no los ofrece, así que no saldrían nunca. "
                   "Los tiempos de acá abajo sirven para agregarlos cuando se decida "
                   "incluirlos en Parámetros (provincias y cantones).")
    hoja2["A2"].font = Font(size=9, italic=True)
    for j, titulo in enumerate(("PROVINCIA", "CANTÓN", "CABECERA CANTONAL", "DISTANCIA (DOC)",
                                "TIEMPO (AUTO)", "TIEMPO (AUTOBÚS)"), start=1):
        c = hoja2.cell(row=4, column=j, value=titulo)
        c.font = Font(bold=True)
        c.fill = amarillo
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borde
    for i, f in enumerate(sorted(fuera, key=lambda x: (x["prov"], x["canton"])), start=5):
        for j, valor in enumerate((f["prov"].title(), f["canton"], f["cabecera"], f["km_txt"],
                                   _hhmm(f["auto"]), _hhmm(f["bus"])), start=1):
            c = hoja2.cell(row=i, column=j, value=valor)
            c.border = borde
            if j > 3:
                c.alignment = Alignment(horizontal="center")
    for columna, ancho in (("A", 22), ("B", 30), ("C", 22), ("D", 14), ("E", 13), ("F", 14)):
        hoja2.column_dimensions[columna].width = ancho

    return _guardar(wb, destino)


# --------------------------------------------------------------------- SQL
def _ahora():
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M")


CABECERA_SQL = """\
-- =====================================================================
--  Sistema de Viáticos Miempresa — km y horas de viaje (rutas desde Cuenca)
--  %(titulo)s
--  Generado:       %(fecha)s
--  Archivo fuente: %(fuente)s
--  Cantones: %(cuantos)d   ·   regla de las horas: %(regla)s
--
--  CÓMO SE USA (en el servidor, con PostgreSQL encendido):
--    1) RESPALDE PRIMERO:
--         cd C:\\MIEMPRESA_VIATICOS\\servidor
--         respaldar_base_nativo.bat miempresa 2345
--       (queda en respaldos_base\\viaticos_AAAAMMDD_HHMMSS.sql)
--    2) Cargue este archivo (los tres «set» son para no dañar tildes ni eñes):
--         chcp 65001
--         set PGPASSWORD=miempresa
--         set PGCLIENTENCODING=UTF8
--         "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" -U miempresa -h 127.0.0.1 ^
--            -p 2345 -d viaticos -v ON_ERROR_STOP=1 -f %(archivo)s
--       (ajuste la versión de PostgreSQL y el puerto a los de su servidor)
--    Más fácil todavía: en la carpeta `servidor\\` está `cargar_distancias.bat`, que
--    hace el respaldo y la carga de una sola vez (y `cargar_distancias.bat
--    viaticos_distancias_ANTES.sql` para volver atrás).
--
--  Solo toca la tabla `distancias`: los km y las horas de las rutas desde Cuenca.
--  No toca viáticos, ajustes, gastos, usuarios ni ningún otro dato.
-- =====================================================================
"""


def _sql_texto(texto):
    """Texto listo para un literal SQL (comillas simples dobladas)."""
    return "'" + str(texto).replace("'", "''") + "'"


def _sql_numero(valor):
    """Número listo para SQL (NULL si no hay dato)."""
    return "NULL" if valor is None else "%g" % float(valor)


def escribir_sql(filas, carpeta, entrada, regla):
    """Escribe en `servidor\\` los dos .sql: los valores nuevos y los de antes.

    Devuelve (ruta_nuevo, ruta_antes). El de «antes» sirve para volver atrás tal como
    estaban las rutas en esta copia de la base; las filas que se agregan (que antes no
    existían) quedan anotadas en el mismo archivo para borrarlas a mano si hiciera falta.
    """
    datos = {"fecha": _ahora(), "fuente": entrada.name, "regla": regla,
             "cuantos": len(filas)}
    ejemplo = ", ".join("%s = %g km y %g h" % (f["canton"], f["km"], f["horas"])
                        for f in filas if f["canton"] in ("MACAS", "AZOGUES"))
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    salidas = []
    for nombre, titulo, usar_antes in (
            ("viaticos_distancias_NUEVO.sql",
             "VALORES NUEVOS (km del documento y horas de la regla elegida)", False),
            ("viaticos_distancias_ANTES.sql",
             "VALORES DE ANTES (para volver atrás si algo no gusta)", True)):
        datos["titulo"], datos["archivo"] = titulo, nombre
        lineas = [CABECERA_SQL % datos, "", "BEGIN;"]
        nuevos = []
        for f in filas:
            if usar_antes:
                if f["km_hoy"] is None:
                    nuevos.append(f["canton"])
                    continue
                km_fila, horas_fila = f["km_hoy"], f["horas_hoy"]
            else:
                km_fila, horas_fila = f["km"], f["horas"]
            lineas.append("INSERT INTO distancias (canton, km, horas) VALUES (%s, %s, %s)"
                          % (_sql_texto(f["canton"]), _sql_numero(km_fila),
                             _sql_numero(horas_fila)))
            lineas.append("  ON CONFLICT (canton) DO UPDATE SET km = EXCLUDED.km, "
                          "horas = EXCLUDED.horas;")
        if nuevos:
            lineas.append("")
            lineas.append("-- Estas rutas NO existían antes: si hay que volver atrás, bórrelas")
            lineas.append("-- descomentando la línea de abajo:")
            lineas.append("-- DELETE FROM distancias WHERE canton IN (%s);"
                          % ", ".join(_sql_texto(c) for c in nuevos))
        lineas.append("COMMIT;")
        lineas.append("")
        lineas.append("-- Comprobación: %s." % ejemplo)
        lineas.append("SELECT canton, km, horas FROM distancias "
                      "WHERE canton IN ('MACAS', 'AZOGUES') ORDER BY canton;")
        _escribir_texto(carpeta / nombre, "\n".join(lineas) + "\n")
        salidas.append(carpeta / nombre)
    return salidas[0], salidas[1]


# --------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(
        description="Pasa el Word «DISTANCIAS DOC.docx» al formato del sistema: una sola "
                    "hora por cantón, sacada del tiempo en auto y del tiempo en autobús.")
    p.add_argument("--entrada", default=str(ENTRADA), help="documento de distancias (.docx)")
    p.add_argument("--horas", choices=REGLAS, default=REGLA,
                   help="cómo se saca la única hora de cada cantón: "
                        + " · ".join("%s = %s" % (r, EXPLICACION[r]) for r in REGLAS)
                        + "   (por defecto %s)" % REGLA)
    p.add_argument("--salida", default=str(SALIDA_SISTEMA),
                   help="Excel de tres columnas para el botón Importar Excel")
    p.add_argument("--salida-info", default=str(SALIDA_INFO),
                   help="Excel con todo lo del documento y el antes/después")
    p.add_argument("--sql-dir", default=str(AQUI.parent / "servidor"),
                   help="carpeta donde se dejan los .sql para cargar en el servidor")
    a = p.parse_args()

    entrada = Path(a.entrada).expanduser()
    if not entrada.exists():
        print("No se encontró el documento: %s" % entrada)
        return 2

    print("Leyendo %s…" % entrada.name)
    sistema = cantones_sistema()
    por_canton = {}
    for clave, nombre in sistema.items():
        por_canton.setdefault(clave[1], []).append(nombre)
    actuales = valores_actuales()
    leidas = leer_doc(entrada)
    print("  cantones en el documento: %d  ·  cantones que ofrece el sistema: %d"
          % (len(leidas), len(sistema)))

    filas, fuera, choques, saltados, igualados = [], [], [], [], []
    usados = {}
    for d in leidas:
        if d["km"] is None or not d["auto"] or not d["bus"]:
            saltados.append(d)              # Cuenca (el origen) y lo que venga sin dato
            continue
        destino = igualar(d["prov"], d["canton"], sistema, por_canton)
        if destino is None:
            fuera.append(d)                 # el sistema no ofrece ese cantón
            continue
        km = int(math.floor(d["km"] + 0.5))          # los km del documento, al entero
        horas = horas_de_regla(d["auto"], d["bus"], a.horas)
        # Los cantones que la empresa dejó fijados a mano no se pisan con el documento
        # (YANTZAZA: 215 km y 5 h, aunque el Word traiga 231 km y 5 h 30 min).
        fijo = FIJOS.get(_sin_tildes(destino))
        if fijo:
            km, horas = fijo["km"], fijo["horas"]
        origen = "%s · %s" % (d["prov"], d["canton"])
        if destino in usados:               # dos filas del documento, el mismo cantón
            choques.append((destino, usados[destino], origen))
            continue
        usados[destino] = origen
        if _sin_tildes(destino) != _sin_tildes(d["canton"]):
            igualados.append((origen, destino))
        km_hoy, horas_hoy = actuales.get(_sin_tildes(destino), (None, None))
        filas.append({"prov": d["prov"], "canton": destino, "cabecera": d["cabecera"],
                      "ruta": d["ruta"], "km_txt": d["km_txt"], "km": km,
                      "km_doc": int(math.floor(d["km"] + 0.5)),
                      "auto": d["auto"], "bus": d["bus"], "horas": horas,
                      "km_hoy": km_hoy, "horas_hoy": horas_hoy,
                      "fijo": bool(fijo), "nota": d["nota"]})
    filas.sort(key=lambda f: f["canton"])

    nota = ("Del documento «%s»: los km son los del documento (los revisó la empresa cantón "
            "por cantón) y la hora de cada cantón sale de sus dos tiempos —auto y autobús— con "
            "la regla «%s» (%s)." % (entrada.name, a.horas, EXPLICACION[a.horas]))
    fijados = [f for f in filas if f.get("fijo")]
    if fijados:
        nota += ("  OJO: %s queda con los km y las horas que la empresa dejó puestos a mano "
                 "en el sistema; este documento no los pisa."
                 % ", ".join(f["canton"] for f in fijados))
    ruta_sistema = escribir_sistema([(f["canton"], f["km"], f["horas"]) for f in filas],
                                    Path(a.salida).expanduser(), nota)
    ruta_info = escribir_info(filas, fuera, Path(a.salida_info).expanduser(), a.horas, entrada)
    ruta_nuevo, ruta_antes = escribir_sql(filas, Path(a.sql_dir).expanduser(), entrada, a.horas)

    sin_doc = sorted(set(actuales) - {_sin_tildes(f["canton"]) for f in filas})
    lineas = [
        "REPORTE — km y horas del documento «%s»" % entrada.name,
        "=" * 112,
        "Documento leído:    %s" % entrada,
        "Reporte hecho:      %s" % _ahora(),
        "Regla de las horas: %s — %s" % (a.horas, EXPLICACION[a.horas]),
        "                    cada cantón queda con UNA hora: los dos tiempos del documento se",
        "                    mezclan y el resultado se redondea a 5 minutos",
        "Cantones leídos: %d   ·   se cargan: %d   ·   el sistema no los tiene: %d   ·   "
        "repetidos: %d   ·   sin datos: %d"
        % (len(leidas), len(filas), len(fuera), len(choques), len(saltados)),
        "",
        "-" * 112,
        "%-30s %-13s %7s %7s   %-26s %-15s %s"
        % ("CANTÓN (como lo tiene el sistema)", "KM (hoy → doc)", "AUTO", "BUS",
           "HORAS (hoy → nuevas)", "RECORRIDO (h)", "de dónde sale"),
        "-" * 112,
    ]
    for f in filas:
        antes_km = "%g" % f["km_hoy"] if f["km_hoy"] is not None else "—"
        antes_h = _horas_texto(f["horas_hoy"]) if f["horas_hoy"] else "—"
        hoy_rec = "%d" % _recorrido(f["horas_hoy"]) if f["horas_hoy"] else "—"
        lineas.append("%-30s %5s → %-5g %7s %7s   %-12s → %-12s %3s → %-3s  %s%s"
                      % (f["canton"][:30], antes_km, f["km"], _hhmm(f["auto"]),
                         _hhmm(f["bus"]), antes_h, _horas_texto(f["horas"]), hoy_rec,
                         "%d" % _recorrido(f["horas"]), usados[f["canton"]],
                         "   ← FIJADO A MANO (el documento dice %g km)" % f["km_doc"]
                         if f.get("fijo") else ""))

    if igualados:
        lineas.append("")
        lineas.append("CANTONES DEL DOCUMENTO QUE EN EL SISTEMA TIENEN OTRO NOMBRE (%d):"
                      % len(igualados))
        for origen, destino in igualados:
            lineas.append("   %-40s → %s" % (origen, destino))
    if choques:
        lineas.append("")
        lineas.append("CANTONES REPETIDOS EN EL DOCUMENTO (el sistema guarda uno solo):")
        for destino, primero, segundo in choques:
            lineas.append("   %-26s se guardó %s  ·  quedó fuera %s"
                          % (destino, primero, segundo))
    if saltados:
        lineas.append("")
        lineas.append("FILAS QUE NO SE CARGAN (%d): son el origen o no traen km/tiempo:"
                      % len(saltados))
        for d in saltados:
            lineas.append("   %-40s %9s   auto %-10s bus %-10s"
                          % ("%s · %s" % (d["prov"], d["canton"]), d["km_txt"], d["auto_txt"],
                             d["bus_txt"]))
    if fuera:
        lineas.append("")
        lineas.append("-" * 112)
        lineas.append("CANTONES QUE EL SISTEMA NO OFRECE (no se cargan): %d" % len(fuera))
        lineas.append("Son cantones reales que no están en la lista del formulario: para "
                      "cargarlos hay")
        lineas.append("que agregarlos al sistema (Parámetros → provincias y cantones) y volver "
                      "a correr")
        lineas.append("esta herramienta. Sus datos están en la hoja «Cantones sin cargar»")
        lineas.append("del Excel de detalle.")
        lineas.append("-" * 112)
        for d in sorted(fuera, key=lambda x: (x["prov"], x["canton"])):
            lineas.append("   %-46s %9s   auto %-10s bus %-10s"
                          % ("%s · %s" % (d["prov"], d["canton"]), d["km_txt"], d["auto_txt"],
                             d["bus_txt"]))
    if fijados:
        lineas.append("")
        lineas.append("-" * 112)
        lineas.append("VALORES FIJADOS A MANO (el documento NO los pisa): %d" % len(fijados))
        lineas.append("La empresa los dejó así en el sistema (PARÁMETROS → Provincias y km) y "
                      "se respetan.")
        lineas.append("Para usar los del documento habría que sacarlos de la lista FIJOS de "
                      "esta herramienta.")
        lineas.append("-" * 112)
        for f in fijados:
            lineas.append("   %-30s %5g km · %-12s   (el documento trae %g km · auto %s · "
                          "bus %s)" % (f["canton"], f["km"], _horas_texto(f["horas"]),
                                       f["km_doc"], _hhmm(f["auto"]), _hhmm(f["bus"])))
    if sin_doc:
        lineas.append("")
        lineas.append("CANTONES DEL SISTEMA QUE EL DOCUMENTO NO TRAE (se quedan como están): %d"
                      % len(sin_doc))
        lineas.append("   " + ", ".join(sin_doc))
    lineas.append("")
    lineas.append("(este reporte no cambia nada: el documento de entrada y la base quedan "
                  "intactos)")
    lineas.append("")
    lineas.append("PARA CARGARLO:")
    lineas.append("   A) En el sistema:  PARÁMETROS → 🗺️ Provincias y km → 📥 Importar Excel →")
    lineas.append("      «%s»." % ruta_sistema.name)
    lineas.append("   B) En la base central del servidor:  servidor\\cargar_distancias.bat")
    lineas.append("      (hace el respaldo y carga «%s»; para volver atrás, "
                  "cargar_distancias.bat %s)" % (ruta_nuevo.name, ruta_antes.name))
    _escribir_texto(REPORTE, "\n".join(lineas) + "\n")

    print("Excel del sistema (3 columnas): %s" % ruta_sistema)
    print("Excel con el detalle:           %s" % ruta_info)
    print("Para el servidor:               %s   ·   %s" % (ruta_nuevo, ruta_antes))
    print("Reporte:                        %s" % REPORTE)
    print("Resumen: %d cantones para cargar · %d fuera (el sistema no los tiene) · "
          "%d repetidos · regla de las horas: %s"
          % (len(filas), len(fuera), len(choques), a.horas))
    for f in filas:
        if f["canton"] in ("MACAS", "AZOGUES"):
            print("   %-9s %4d km · %s  (auto %s + bus %s)"
                  % (f["canton"], f["km"], _horas_texto(f["horas"]), _hhmm(f["auto"]),
                     _hhmm(f["bus"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
