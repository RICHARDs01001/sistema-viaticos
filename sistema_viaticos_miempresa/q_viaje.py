# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_viaje.py — Viáticos originales y ajustes (PySide6).

Mismas funciones que `ui_viaje.py`, en dos pestañas:
  «📝 Nuevo / editar viático»: datos generales, fechas y horarios, encargado, chofer,
     destino con km por cantón, efectivo sugerido de combustible, acompañantes
     (auto/bus), vista previa calculada, guardar, imprimir/PDF y limpiar.
  «📋 Historial»: filtros por texto, provincia y estado; ajustes del viático elegido;
     detalle del original y de cada ajuste; editar, ajustar, anular, ver justificado,
     imprimir (original, ajuste o general) y exportar a Excel lo que se ve.

Los cálculos siguen siendo los de `calculos.py` (no se cambió ninguna regla).
"""
from datetime import date as _fecha, datetime as _fechahora, time as _dtime, timedelta
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QTabWidget, QVBoxLayout, QWidget

import database as db
import qt_comunes as C
import qt_tema as T
import reportes
from calculos import DatosViaje, calcular, cajero_del_grupo, hora_limite, horas_texto

HORAS = ["%02d:%02d" % (h, m) for h in range(24) for m in (0, 15, 30, 45)]

KM_APROX = {
    "CUENCA": 15, "GIRÓN": 60, "GUALACEO": 45, "CHORDALEG": 50, "PAUTE": 40,
    "GUACHAPALA": 55, "EL PAN": 55, "SEVILLA DE ORO": 70, "PUCARÁ": 90, "SIGSIG": 65,
    "OÑA": 95, "SANTA ISABEL": 70, "AZOGUES": 30, "CAÑAR": 60, "LA TRONCAL": 120,
    "LOJA": 220, "CATAMAYO": 250, "ZARUMA": 260, "MACHALA": 180, "PIÑAS": 220,
    "SANTA ROSA": 200, "HUAQUILLAS": 230, "PASAJE": 190, "GUAYAQUIL": 200,
    "MILAGRO": 190, "DURÁN": 205, "SALINAS": 245, "MANTA": 400, "PORTOVIEJO": 350,
    "MONTECRISTI": 395, "BABAHOYO": 250, "QUEVEDO": 280, "SANTO DOMINGO": 330,
    "ESMERALDAS": 450, "QUITO": 470, "LATACUNGA": 300, "AMBATO": 330, "RIOBAMBA": 260,
    "CHAMBO": 255, "GUARANDA": 190, "MACAS": 190, "SUCÚA": 240, "TENA": 380,
}

# Horas de viaje (solo ida): las del documento que revisó la empresa cantón por cantón
# (y las que ella misma registra en sus viáticos reales). Están en
# `database.HORAS_CUENCA` (junto a la tabla de kilómetros) para que las use también la
# herramienta que arma el Excel «TIEMPOS DE VIAJE MIEMPRESA.xlsx» sin abrir la interfaz.
# Se pueden ajustar cantón por cantón en **Parámetros → 🗺️ Provincias y km**.
HORAS_APROX = db.HORAS_APROX

# Colores de las filas especiales (los mismos de la interfaz anterior).
FONDO_ZEBRA = QColor("#EEF3FA")
FONDO_TOTAL = QColor("#FFF2B8")
FONDO_GENERAL = QColor(T.AMARILLO)      # el mismo amarillo fuerte del informe
FONDO_SEP = QColor("#FFDD7A")


def fmt(v):
    v = float(v or 0)
    return "-" if abs(v) < 0.005 else "$%.2f" % v


def fmt_f(iso):
    if not iso:
        return ""
    try:
        y, m, d = str(iso).split("-")
        return "%s/%s/%s" % (d, m, y)
    except Exception:
        return str(iso)


def _col(clave, titulo, ancho, izquierda=False):
    return (clave, titulo, ancho, Qt.AlignLeft if izquierda else Qt.AlignRight)

# Detalle del viático: las mismas 25 columnas del Excel oficial.
# Las fechas llevan 92 px y las horas 58 px: así «23/09/2026» se lee completo en la
# vista previa (antes la columna quedaba corta y el dato salía recortado).
COLS_DETALLE = [
    _col("n", "N°", 30), _col("empleado", "Empleado", 158, True),
    _col("lugar", "Lugar", 112, True), _col("f_sal", "F.Salida", 96),
    _col("h_sal", "H.Sal", 60), _col("f_reg", "F.Regreso", 96),
    _col("h_reg", "H.Reg", 60), _col("f_lt", "F.Lleg.Trab", 96),
    _col("h_lt", "H.Lleg", 60), _col("f_st", "F.Sal.Trab", 96),
    _col("h_st", "H.Sal.Trab", 62), _col("dias", "Días", 38), _col("km", "Km", 44),
    _col("des", "Desay.", 60), _col("alm", "Almuer.", 62), _col("mer", "Merien.", 62),
    _col("txs", "Taxi S.", 58), _col("txr", "Taxi R.", 58), _col("hos", "Hosp.", 62),
    _col("agua", "Agua", 52), _col("comb", "Combust.", 74),
    _col("tra", "Transp./Otros", 78), _col("peaje", "Parq./Peaje", 70),
    _col("total", "TOTAL", 78), _col("cajero", "CAJERO", 78)]

# Historial de viáticos.
COLS_HIST = [
    _col("numero", "N°", 60), _col("salida", "Salida", 85),
    _col("regreso", "Regreso", 85), _col("responsable", "Responsable", 170, True),
    _col("empleados", "Empleados", 260, True), _col("lugar", "Lugar", 150, True),
    _col("ajustes", "Ajus.", 55), _col("total", "Total", 80),
    _col("cajero", "Cajero", 80), _col("estado", "Estado", 95)]

def sep_vals(texto):
    """Fila separadora («═ ORIGINAL ═», «═ AJUSTE N° 1 ═»)."""
    fila = {c[0]: "" for c in COLS_DETALLE}
    fila["empleado"] = texto
    return fila


def vals_fila(i, f):
    """Una fila del detalle, con el mismo formato del Excel."""
    return {"n": i, "empleado": f.get("nombre_empleado", ""),
            "lugar": f.get("lugar_trabajo", ""),
            "f_sal": fmt_f(f.get("fecha_salida")), "h_sal": f.get("hora_salida", ""),
            "f_reg": fmt_f(f.get("fecha_regreso")), "h_reg": f.get("hora_regreso", ""),
            "f_lt": fmt_f(f.get("fecha_llegada_trabajo")),
            "h_lt": f.get("hora_llegada_trabajo", ""),
            "f_st": fmt_f(f.get("fecha_salida_trabajo")),
            "h_st": f.get("hora_salida_trabajo", ""),
            "dias": f.get("dias_viaje", ""), "km": f.get("km_recorridos", "") or "",
            "des": fmt(f.get("desayuno")), "alm": fmt(f.get("almuerzo")),
            "mer": fmt(f.get("merienda")), "txs": fmt(f.get("taxi_salida")),
            "txr": fmt(f.get("taxi_regreso")), "hos": fmt(f.get("hospedaje")),
            "agua": fmt(f.get("agua")), "comb": fmt(f.get("combustible")),
            "tra": fmt(f.get("otros")), "peaje": fmt(f.get("parqueadero_peaje")),
            "total": fmt(f.get("total")), "cajero": fmt(f.get("valor_cajero"))}


def vals_totales(filas, titulo="TOTALES"):
    """Fila de totales de un bloque del detalle (original, un ajuste o el general)."""
    fila = {c[0]: "" for c in COLS_DETALLE}
    fila["empleado"] = titulo
    for clave, campo in (("des", "desayuno"), ("alm", "almuerzo"), ("mer", "merienda"),
                         ("txs", "taxi_salida"), ("txr", "taxi_regreso"),
                         ("hos", "hospedaje"), ("agua", "agua"), ("comb", "combustible"),
                         ("tra", "otros"), ("peaje", "parqueadero_peaje"),
                         ("total", "total"), ("cajero", "valor_cajero")):
        fila[clave] = fmt(sum(float(x.get(campo) or 0) for x in filas))
    return fila


def _par_fecha_hora(valor, fecha_defecto, hora_defecto):
    """(fecha, hora) propias de un viajero, o las del viático si no tiene.

    Se guardan como ["2026-09-23", "22:00"] en el horario de cada acompañante.
    """
    if not valor:
        return fecha_defecto, hora_defecto
    try:
        f, h = valor
        hh, mm = str(h).split(":")[:2]
        return _fecha.fromisoformat(str(f)), _dtime(int(hh), int(mm))
    except Exception:
        return fecha_defecto, hora_defecto


def _km_desde_cuenca(cant, prov):
    """Km ida desde Cuenca: primero la tabla de la base, si no la aproximada."""
    try:
        km = db.km_para(cant)
        if km:
            return km
        km = db.km_para(prov)
        if km:
            return km
    except Exception:
        pass
    return KM_APROX.get(cant) or KM_APROX.get(prov) or 0


def _horas_desde_cuenca(cant, prov):
    """Horas de viaje (ida) del destino: primero lo registrado, después lo aproximado."""
    for clave in (cant, prov):
        if not clave:
            continue
        try:
            horas = db.horas_para(clave)
        except Exception:
            horas = None
        if horas:
            return float(horas)
    return float(HORAS_APROX.get(cant) or HORAS_APROX.get(prov) or 0)


def _pintar(tabla, posiciones, fondo):
    """Pinta de un color las filas especiales del detalle (zebra, sep, total)."""
    fuente = QFont()
    fuente.setBold(True)
    for fila in posiciones:
        for col in range(tabla.columnCount()):
            item = tabla.item(fila, col)
            if item is not None:
                item.setBackground(fondo)
                item.setFont(fuente)

def _horario_de_fila(fila, base):
    """Horario propio guardado en la fila de un viajero (solo lo que difiere).

    Si el acompañante viaja en BUS sale antes o llega más tarde que el encargado: sus
    fechas y horas quedan guardadas en su propia fila y se vuelven a cargar al editar.
    """
    horario = {}
    for clave, campo_f, campo_h in (("salida", "fecha_salida", "hora_salida"),
                                    ("llegada", "fecha_llegada_trabajo",
                                     "hora_llegada_trabajo"),
                                    ("salida_trab", "fecha_salida_trabajo",
                                     "hora_salida_trabajo"),
                                    ("regreso", "fecha_regreso", "hora_regreso")):
        f = (fila.get(campo_f) or "")
        h = (fila.get(campo_h) or "")
        if f and h and (f != (base.get(campo_f) or "") or h != (base.get(campo_h) or "")):
            horario[clave] = [f, h]
    return horario or None


def _fila_de_los_gastos(filas, base):
    """La fila que lleva el km, el parqueadero/peaje y el combustible del viaje.

    En la pantalla esos datos se escriben **una sola vez** y quedan guardados en la fila
    del **chofer** (el que recibe el efectivo de la gasolina) y, si no hay chofer en el
    viático, en la del **encargado**. Al abrir un viático guardado para editarlo hay que
    leerlos de ahí: antes se leían de la primera fila —la del encargado— y, cuando el
    chofer era otra persona, al guardar la edición **el km, el parqueadero/peaje y el
    combustible volvían a cero** (y con ellos cambiaba el total del viaje).

    En viáticos viejos, guardados antes de que se marcara al chofer, se usa la fila que
    de verdad tenga esos valores.
    """
    def _plata(x):
        return (float(x.get("km_recorridos") or 0)
                + float(x.get("parqueadero_peaje") or 0)
                + float(x.get("combustible") or 0))

    marcada = next((x for x in filas if x.get("es_chofer")), None)
    if marcada is not None and _plata(marcada) > 0:
        return marcada
    return max(filas, key=_plata, default=base)


# Las comidas que la empresa cuenta en el camino. Cada una suma sus horas (1 de
# fábrica) cuando su hora límite cae **dentro** del viaje; se configuran en
# Parámetros → «Estimado de viaje».
COMIDAS_VIAJE = (("el desayuno", "hora_limite_desayuno", "horas_desayuno_viaje"),
                 ("el almuerzo", "hora_limite_almuerzo", "horas_almuerzo_viaje"),
                 ("la merienda", "hora_limite_merienda", "horas_merienda_viaje"))


def recorrido_de_viaje(km, velocidad, horas=None):
    """Horas de **recorrido** (solo el camino), redondeadas hacia arriba a la hora entera.

    Se toman de `horas` —lo que **de verdad** se tarda hasta ese destino, de la tabla
    de rutas o de los viáticos reales de la empresa— y, si ese dato no está, de los km
    y la velocidad del vehículo. En los dos casos se redondea hacia arriba: de Cuenca a
    Guayaquil son 3 h 30 en Google y ellos registran **4**; a Quito son 9 h 30 y quedan
    **10**. Devuelve 0 si no hay ni horas del destino ni km/velocidad.
    """
    try:
        km = float(km or 0)
        velocidad = float(velocidad or 0)
        horas = float(horas or 0)
    except (TypeError, ValueError):
        return 0
    if horas > 0:
        return max(1, int(math.ceil(horas - 1e-9)))
    if km > 0 and velocidad > 0:
        return max(1, int(math.ceil(km / velocidad - 1e-9)))
    return 0


def comidas_del_viaje(p, salida, fin):
    """[(comida, horas, hora límite)] de las comidas que caen dentro del viaje.

    Es la regla de la empresa: al que sale a las 10:00 y llega a las 13:00 se le
    registra la llegada a las **14:00** (una hora por el almuerzo), al que vuelve a las
    22:00 se le registra a las **23:00** (la merienda del camino) y el viaje de
    madrugada lleva una hora más por el desayuno (02:00 → 14:00 se registra **16:00**
    por el desayuno y el almuerzo). Se revisa **día por día** porque el viaje puede
    cruzar la medianoche.
    """
    comidas = []
    for nombre, clave_limite, clave_horas in COMIDAS_VIAJE:
        try:
            horas = float((p or {}).get(clave_horas) or 0)
        except (TypeError, ValueError):
            horas = 0.0
        if horas <= 0:
            continue
        limite = hora_limite((p or {}).get(clave_limite))
        dia = salida.date()
        while dia <= fin.date():            # el viaje puede cruzar la medianoche
            if salida <= _fechahora.combine(dia, limite) <= fin:
                comidas.append((nombre, horas, limite.strftime("%H:%M")))
                break
            dia += timedelta(days=1)
    return comidas


def detalle_viaje(km, velocidad, p, salida=None, horas=None):
    """(horas totales, recorrido, [(comida, horas, hora límite)]) de **un tramo**.

    El recorrido se redondea hacia arriba a la hora entera y después se suman las horas
    de las comidas que caen dentro del viaje, contando **desde la salida de este
    tramo**: la ida se cuenta desde la salida de Miempresa y la vuelta desde la salida
    del trabajo (así el que vuelve a las 18:00 con 4 h de camino registra las 23:00 por
    la merienda y no las 22:00).
    """
    recorrido = recorrido_de_viaje(km, velocidad, horas)
    if recorrido <= 0 or salida is None:
        return recorrido, recorrido, []
    fin = salida + timedelta(hours=recorrido)
    comidas = comidas_del_viaje(p, salida, fin)
    return recorrido + sum(h for _n, h, _l in comidas), recorrido, comidas


def duracion_de_viaje(km, velocidad, p, salida=None, horas=None):
    """Horas que dura el viaje: el recorrido + las horas de las comidas que caen dentro.

    Es la misma regla de `detalle_viaje`, sin el detalle. Devuelve 0 si no hay ni horas
    del destino ni km/velocidad.
    """
    return detalle_viaje(km, velocidad, p, salida, horas)[0]


def texto_estimado(titulo, salida, total, recorrido, comidas, llegada):
    """Explicación de un tramo del estimado, como se la muestra al usuario.

    Ejemplo: «Ida — salida de Miempresa: 24/09 18:00 / 4 h de recorrido + 1 h por la
    merienda (21:00, en el camino) = 5 h / llegada a Miempresa: 24/09 23:00».
    """
    detalle = "%d h de recorrido" % recorrido
    for nombre, horas, limite in comidas:
        detalle += " + %g h por %s (%s, en el camino)" % (horas, nombre, limite)
    return ("%s: %s\n   %s = %d h\n   llegada: %s"
            % (titulo, salida.strftime("%d/%m %H:%M"), detalle, total,
               llegada.strftime("%d/%m %H:%M")))


class DialogoHorario(C.Ventana):
    """Horario propio de un viajero (el del BUS no sale ni llega a la misma hora).

    El sistema calcula las comidas y el hospedaje con las horas de cada persona, así
    que aquí se ponen las horas de este viajero y su total sale distinto al del resto.
    """

    # El mismo orden de la pantalla: primero el viaje a Miempresa y después lo del
    # trabajo, así «Salida de Miempresa» y «Llegada a Miempresa» quedan en la misma
    # columna del formulario.
    ETIQUETAS = (("salida", "Salida de Miempresa:"),
                 ("regreso", "Llegada a Miempresa:"),
                 ("llegada", "Llegada al trabajo:"),
                 ("salida_trab", "Salida del trabajo:"))

    def __init__(self, padre, nombre, horario, base, km, velocidad, horas=None):
        super().__init__(titulo="Horario del viajero — %s" % nombre, padre=padre,
                         ancho=680, alto=440, empezar_maximizada=False)
        self.horario = {}
        self.nombre = nombre
        self.base = base or {}
        self.km = float(km or 0)
        self.velocidad = float(velocidad or 0)
        self.horas = float(horas or 0)      # horas de viaje del destino (si se saben)
        self.campos = {}
        tarjeta = C.Tarjeta("Fechas y horas de %s" % nombre)
        filas = []
        for clave, etiqueta in self.ETIQUETAS:
            fecha = C.CampoFecha(ancho=145)
            hora = C.CampoHora("08:00", ancho=95)
            datos = (horario or {}).get(clave) or self.base.get(clave)
            if datos and datos[0] and datos[1]:
                fecha.set_valor(datos[0])
                hora.set_valor(datos[1])
            self.campos[clave] = (fecha, hora)
            filas.append([(etiqueta, fecha), ("Hora:", hora)])
        tarjeta.agregar(C.rejilla(filas, esp=8))
        tarjeta.agregar(C.fila(
            C.boton_secundario("⏱  Estimar viaje", self.estimar),
            C.boton_secundario("↩  Las horas del viático", self.usar_del_viatico),
            None, esp=8))
        self.agregar(tarjeta)
        barra = C.margenes(QHBoxLayout(), esp=8)
        barra.addWidget(C.boton_amarillo("💾  Guardar horario", self.guardar))
        barra.addWidget(C.boton_secundario("✖  Cancelar", self.reject))
        barra.addStretch(1)
        self.agregar_fila(barra)

    # ---------- campos ----------
    def _leer(self, clave):
        fecha, hora = self.campos[clave]
        return (fecha.valor() or "").strip(), (hora.valor() or "").strip()

    def _escribir(self, clave, cuando):
        fecha, hora = self.campos[clave]
        fecha.set_valor(cuando.date().isoformat())
        hora.set_valor(cuando.strftime("%H:%M"))

    def _cuando(self, clave):
        f, h = self._leer(clave)
        if not f or not h:
            return None
        try:
            hh, mm = [int(x) for x in h.split(":")[:2]]
            return _fechahora.combine(_fecha.fromisoformat(f), _dtime(hh, mm))
        except Exception:
            return None

    # ---------- acciones ----------
    def usar_del_viatico(self):
        """Deja las cuatro horas iguales a las del viático (sin horario propio)."""
        for clave in self.campos:
            datos = self.base.get(clave)
            if datos:
                fecha, hora = self.campos[clave]
                fecha.set_valor(datos[0] or "")
                hora.set_valor(datos[1] or "")

    def estimar(self):
        """Calcula la llegada al trabajo y la llegada a Miempresa de este viajero.

        Se registran la salida de Miempresa y la salida del trabajo; el sistema
        escribe las dos llegadas con los km, la velocidad del medio y las horas que se
        suman por las comidas que caen en el camino. Cada tramo se cuenta **desde su
        propia salida**: así el que vuelve de noche (sale del trabajo a las 18:00 con
        4 h de camino) registra las **23:00** por la merienda y no las 22:00.
        """
        if self.km <= 0 or self.velocidad <= 0:
            C.aviso(self, "Estimar viaje",
                    "Faltan los km del cantón o la velocidad del medio de transporte.")
            return
        salida = self._cuando("salida")
        salida_trab = self._cuando("salida_trab")
        if salida is None and salida_trab is None:
            C.aviso(self, "Estimar viaje",
                    "Complete la salida de Miempresa y la salida del trabajo "
                    "(fecha y hora).")
            return
        p = db.cargar_parametros()
        lineas = []
        for inicio, clave, titulo in ((salida, "llegada", "Ida — salida de Miempresa"),
                                      (salida_trab, "regreso",
                                       "Vuelta — salida del trabajo")):
            if inicio is None:
                continue
            total, recorrido, comidas = detalle_viaje(self.km, self.velocidad, p,
                                                      inicio, self.horas)
            if not total:
                continue
            llegada = inicio + timedelta(hours=total)
            self._escribir(clave, llegada)
            lineas.append(texto_estimado(titulo, inicio, total, recorrido, comidas,
                                         llegada))
        C.informar(self, "Estimar viaje",
                   "Tiempo de viaje estimado (recorrido + comidas del camino)\n\n%s\n\n"
                   "Puede escribir otras horas: cada viajero puede salir o llegar a "
                   "otra hora." % "\n\n".join(lineas))

    def guardar(self):
        """Guarda solo lo que sea distinto del horario del viático."""
        self.horario = {}
        for clave in self.campos:
            f, h = self._leer(clave)
            base = self.base.get(clave) or ("", "")
            if f and h and (f, h) != ((base[0] or "").strip(), (base[1] or "").strip()):
                self.horario[clave] = [f, h]
        self.accept()


class ViajeWindow(C.Ventana):
    """Ventana de viáticos: pestaña de captura + pestaña de historial."""

    def __init__(self, master=None, usuario=None):
        usuario = usuario or {}
        super().__init__(
            titulo="Viáticos — Sistema de Viáticos", usuario=usuario, padre=master,
            ancho=1360, alto=920, empezar_maximizada=True,
            info=C.etiqueta_sesion(usuario))
        self.pasajeros = []                # acompañantes: {nombre, medio, extra}
        self.edit_numero = None            # viático que se está editando
        self.edit_ajuste_numero = None     # ajuste que se está editando
        self._combustible_sugerido = 0.0
        self._km_orig_ajuste = 0.0
        self._salida_bloqueada = False
        self._hist_firma = None
        # Memoria temporal: `_borrador_base` es cómo estaba el formulario al abrirlo (o al
        # cargar un viático) y `_borrador_guardado`, si en la base hay algo de este usuario.
        self._borrador_base = None
        self._borrador_guardado = False
        self.pestanas = QTabWidget()
        self.pestanas.addTab(self._tab_nuevo(), "  📝 Nuevo / editar viático  ")
        self.pestanas.addTab(self._tab_historial(), "  📋 Historial  ")
        self.agregar(self.pestanas, 1)
        self.refrescar_historial()
        self._actualizar_numero()
        # Refresco de fondo cada 15 s: los viáticos creados en otra computadora
        # aparecen solos, sin cerrar y abrir.
        self._refresco = QTimer(self)
        self._refresco.timeout.connect(lambda: self.refrescar_historial(automatico=True))
        self._refresco.start(15000)
        # Memoria temporal: lo que se va escribiendo se guarda solo cada 20 s (y al cerrar
        # la ventana) en la tabla `borradores`, por usuario. Si el sistema se cierra por
        # error —o se apaga la computadora—, al volver a entrar el sistema le ofrece a esa
        # persona lo que estaba llenando (ver `_recuperar_borrador`).
        self._recordar_base()
        self._memoria = QTimer(self)
        self._memoria.timeout.connect(self._guardar_borrador)
        self._memoria.start(20000)
        # El aviso de «quedó algo a medio llenar» sale con la ventana ya dibujada.
        QTimer.singleShot(700, self._avisar_borrador_pendiente)

    # ================= FORMULARIO =================
    def _tab_nuevo(self):
        pag = QWidget()
        lay = C.margenes(QVBoxLayout(pag), esp=8)

        # --- botones de la captura ---
        barra = C.margenes(QHBoxLayout(), esp=6)
        self.btn_guardar = C.boton_amarillo("💾  GUARDAR VIÁTICO", self.guardar)
        barra.addWidget(self.btn_guardar)
        barra.addWidget(C.boton_primario("🖨  IMPRIMIR / PDF", self.imprimir))
        barra.addWidget(C.boton_primario("📊  EXCEL", self.exportar_excel_formulario))
        barra.addWidget(C.boton_secundario("🧹  LIMPIAR / CANCELAR", self.limpiar))
        # Memoria temporal: vuelve a poner en el formulario lo que quedó a medio llenar
        # (por si el sistema se cerró por error antes de guardar el viático).
        barra.addWidget(C.boton_secundario(
            "🕘  RECUPERAR LO ÚLTIMO", self._boton_recuperar,
            herramienta="Vuelve a traer lo que estaba llenando cuando se cerró el "
                        "sistema sin guardar (lo guarda solo cada 20 segundos)"))
        barra.addStretch(1)
        self.lbl_estado = C.etiqueta("", clave=True)
        barra.addWidget(self.lbl_estado)
        lay.addLayout(barra)

        # --- datos generales ---
        cab = C.Tarjeta("Datos generales del viático")
        self.lbl_numero = C.etiqueta("", titulo="pagina")
        self.cb_responsable = C.ComboAuto(db.listar_empleados, ancho=250)
        self.cb_cliente = C.ComboAuto(db.listar_clientes, ancho=250)
        self.cb_vehiculo = C.ComboAuto(self._opc_veh, ancho=230,
                                       cb=lambda _t: self._recalcular_horas())
        self.txt_ord1 = C.campo("", ancho=110)
        self.txt_ord2 = C.campo("", ancho=110)
        self.txt_efectivo = C.campo("0", ancho=110, cb=lambda _t: self._refrescar_prev())
        self.txt_obs = C.campo("", placeholder="Observaciones del viático")
        self.txt_recibo = C.campo("", ancho=90)
        self.txt_recibo2 = C.campo("", ancho=90)
        self.txt_recibo3 = C.campo("", ancho=90)
        fila = C.margenes(QHBoxLayout(), esp=14)
        fila.addWidget(self.lbl_numero)
        fila.addWidget(C.rejilla([
            [("Creado por:", self.cb_responsable), ("Cliente y proyecto:", self.cb_cliente)],
            [("Placa vehículo:", self.cb_vehiculo), ("⛽ Orden Comb. 1:", self.txt_ord1)],
            [("⛽ Orden Comb. 2:", self.txt_ord2), ("💵 Efectivo Comb. $:", self.txt_efectivo)],
        ], esp=8))
        fila.addWidget(C.rejilla([
            [("Recibo N° 1:", self.txt_recibo)],
            [("Recibo N° 2:", self.txt_recibo2)],
            [("Recibo N° 3:", self.txt_recibo3)],
        ], esp=8))
        fila.addStretch(1)
        cab.agregar_fila(fila)

        # Las observaciones van en su propia fila, a todo el ancho de la tarjeta: el
        # campo queda grande, como estaba antes.
        fila_obs = C.margenes(QHBoxLayout(), esp=8)
        fila_obs.addWidget(C.etiqueta("Observaciones:", clave=True))
        fila_obs.addWidget(self.txt_obs, 1)
        cab.agregar_fila(fila_obs)
        lay.addWidget(cab)

        # --- fechas, horarios y combustible sugerido ---
        fec = C.Tarjeta("Fechas, horarios y combustible sugerido")
        self.cal_salida = C.CampoFecha(ancho=135, cb=lambda _v: self._recalcular_horas())
        self.cal_regreso = C.CampoFecha(ancho=135, cb=lambda _v: self._refrescar_prev())
        self.cal_lleg = C.CampoFecha(ancho=135, cb=lambda _v: self._refrescar_prev())
        self.cal_saltr = C.CampoFecha(ancho=135, cb=lambda _v: self._recalcular_horas())
        self.cb_hsalida = C.CampoHora("08:00", ancho=90, cb=lambda _v: self._recalcular_horas())
        self.cb_hregreso = C.CampoHora("18:00", ancho=90, cb=lambda _v: self._refrescar_prev())
        self.cb_hlleg = C.CampoHora("08:00", ancho=90, cb=lambda _v: self._refrescar_prev())
        self.cb_hsaltr = C.CampoHora("18:00", ancho=90, cb=lambda _v: self._recalcular_horas())

        # El efectivo sugerido va aquí al lado de las fechas: es solo un valor y el
        # botón USAR, así no queda lejos ni ocupa una tarjeta aparte.
        self.lbl_sugerido_val = C.etiqueta("$0.00")
        self.lbl_sugerido_val.setObjectName("valorSugerido")
        caja_sug = C.Tarjeta()
        caja_sug.setObjectName("tarjetaSugerido")
        fila_sug = C.margenes(QHBoxLayout(), esp=10)
        fila_sug.addWidget(C.etiqueta("Efectivo sugerido", clave=True))
        fila_sug.addWidget(self.lbl_sugerido_val)
        fila_sug.addWidget(C.boton_amarillo("USAR", self._usar_combustible))
        caja_sug.agregar_fila(fila_sug)

        fila = C.margenes(QHBoxLayout(), esp=16)
        # Dos columnas: a la izquierda el viaje completo a Miempresa (salida y
        # llegada) y a la derecha las horas del trabajo (llegada y salida). Ellos
        # registran las dos salidas y el sistema calcula las dos llegadas.
        fila.addWidget(C.rejilla([
            [("Salida de Miempresa:", self.cal_salida), ("Hora:", self.cb_hsalida)],
            [("Llegada a Miempresa:", self.cal_regreso), ("Hora:", self.cb_hregreso)],
        ], esp=6))
        fila.addWidget(C.rejilla([
            [("Llegada al trabajo:", self.cal_lleg), ("Hora:", self.cb_hlleg)],
            [("Salida del trabajo:", self.cal_saltr), ("Hora:", self.cb_hsaltr)],
        ], esp=6))
        # El sistema calcula solo las dos llegadas (`_recalcular_horas`) con los km del
        # cantón, la velocidad del vehículo y las horas de las comidas (Parámetros).
        # Este botón repite el cálculo y muestra el detalle.
        fila.addWidget(C.boton_secundario("⏱  Estimar viaje", self._estimar_manual))
        fila.addWidget(caja_sug)
        fila.addStretch(1)
        fec.agregar_fila(fila)
        lay.addWidget(fec)

        # --- encargado, chofer y destino | empleados adicionales (doble formulario) ---
        enc = C.Tarjeta("👤 Encargado, chofer y destino   |   👥 Empleados adicionales")
        self.cb_encargado = C.ComboAuto(db.listar_empleados, ancho=175,
                                        cb=lambda _t: self._al_cambiar_encargado())
        self.cb_chofer = C.ComboAuto(db.listar_empleados, ancho=175,
                                     cb=lambda _t: self._refrescar_prev())
        self.cb_provincia = C.ComboAuto(db.listar_provincias, ancho=140,
                                        cb=lambda _t: self._al_provincia())
        self.cb_canton = C.ComboAuto(self._opc_cantones, ancho=140,
                                     cb=lambda _t: self._al_canton())
        self.txt_lugar = C.campo("", ancho=200, mayusculas=True,
                                 cb=lambda _t: self._refrescar_prev())
        self.txt_km = C.campo("0", ancho=80, cb=lambda _t: self._recalcular_horas())
        self.txt_peaje = C.campo("0", ancho=80, cb=lambda _t: self._refrescar_prev())
        self.txt_otros = C.campo("0", ancho=80, cb=lambda _t: self._refrescar_prev())
        self.lbl_km = C.etiqueta("", ayuda=True)      # distancias de la tabla
        self.lbl_km.setWordWrap(False)

        # Los acompañantes tienen su propio formulario, a la derecha y separado por una
        # línea: queda como dos formularios en la misma tarjeta.
        self.cb_pas = C.ComboAuto(self._opc_pasajeros, ancho=170)
        self.cb_medio = C.combo(["AUTO", "BUS"], "AUTO", ancho=80)
        self.txt_extra = C.campo("0", ancho=80)
        self.lbl_medio = C.etiqueta("", ayuda=True)
        self.lst_pas = QListWidget()
        self.lst_pas.setMinimumHeight(T.px(52, 38))
        self.lst_pas.setMaximumHeight(T.px(60, 44))

        viaje = C.rejilla([
            [("Empleado encargado:", self.cb_encargado), ("Provincia:", self.cb_provincia),
             ("Cantón:", self.cb_canton)],
            [("Chofer:", self.cb_chofer), ("Lugar / referencia:", self.txt_lugar)],
            [("Km:", C.fila(self.txt_km, self.lbl_km, None, esp=6)),
             ("Parq./Peaje:", self.txt_peaje), ("Transp./Otros:", self.txt_otros)],
        ], esp=8)
        adicionales = C.columna(
            C.rejilla([
                [("Empleado:", self.cb_pas)],
                [("Medio:", self.cb_medio), ("Extra $:", self.txt_extra)],
            ], esp=6),
            C.fila(C.boton_primario("➕  Agregar", self.agregar_pasajero),
                   C.boton_secundario("🗑  Quitar", self.quitar_pasajero),
                   None, esp=6),
            self.lbl_medio, self.lst_pas, esp=4)

        fila = C.margenes(QHBoxLayout(), esp=12)
        fila.addWidget(viaje)
        fila.addWidget(C.linea(horizontal=False))
        fila.addWidget(adicionales, 1)
        enc.agregar_fila(fila)
        lay.addWidget(enc)

        # --- vista previa ---
        self.tabla_prev = C.Tabla(COLS_DETALLE, ordenar=False, alto_filas=22,
                                  estirar_ultima=False)
        self.tabla_prev.setMinimumHeight(T.px(132, 96))
        pv = C.Tarjeta("Vista previa — original o ajuste actual")
        pv.agregar(self.tabla_prev, 1)
        # Línea de explicación: dice por qué un concepto (el taxi, por ejemplo) salió en
        # cero, para que no parezca una falla del cálculo.
        self.lbl_avisos = C.etiqueta("", ayuda=True)
        pv.agregar(self.lbl_avisos)
        lay.addWidget(pv, 1)
        self._refrescar_chofer()
        self._responsable_por_defecto()
        self._poner_fechas_hoy()          # las fechas arrancan en el día de hoy
        self._actualizar_medio()
        return pag

    def _poner_fechas_hoy(self):
        """Las cuatro fechas del viaje arrancan en el día de hoy.

        Igual que antes: se abre en el día actual y de ahí se escoge la fecha que se
        necesite (así no hay que escribirla desde cero).
        """
        for caja in (self.cal_salida, self.cal_regreso, self.cal_lleg, self.cal_saltr):
            caja.blockSignals(True)
            caja.hoy()
            caja.blockSignals(False)
        self._refrescar_prev()

    # ---------- sesión y opciones ----------
    def _responsable_por_defecto(self):
        """El viático queda «Creado por» el usuario que inició sesión."""
        nombre = ((self.usuario or {}).get("nombre")
                  or (self.usuario or {}).get("usuario") or "")
        if nombre:
            self.cb_responsable.set_valor(nombre)

    def _opc_veh(self):
        return ["%s  %s" % (v["placa"], v["tipo"]) for v in db.listar_vehiculos()]

    def _opc_cantones(self):
        return db.listar_cantones((self.cb_provincia.valor() or "").strip().upper())

    def _opc_pasajeros(self):
        ya = {p["nombre"] for p in self.pasajeros}
        enc = (self.cb_encargado.valor() or "").strip().upper()
        if enc:
            ya.add(enc)
        return [n for n in db.listar_empleados() if n not in ya]

    def _al_cambiar_encargado(self):
        self.cb_pas.refrescar_opciones()
        self._actualizar_medio()
        self._refrescar_prev()

    def _actualizar_medio(self):
        """Pone el medio de transporte que corresponde y lo bloquea si hace falta.

        El encargado siempre viaja en AUTO, así que en el auto caben 2 acompañantes
        más. Cuando ya se llenó, el sistema elige BUS y bloquea la lista para que no
        se pueda marcar AUTO por error; si se quita un acompañante, vuelve a AUTO.
        """
        en_auto = 1 + sum(1 for p in self.pasajeros if p["medio"] == "AUTO")
        lleno = en_auto >= 3
        C.poner_combo(self.cb_medio, "BUS" if lleno else "AUTO")
        self.cb_medio.setEnabled(not lleno)
        if lleno:
            self.lbl_medio.setText("Auto lleno (3 con el encargado): los demás van en BUS.")
            self.lbl_medio.setVisible(True)
            self.cb_medio.setToolTip("El auto está lleno: los demás acompañantes van en BUS.")
        else:
            self.lbl_medio.setText("")
            self.lbl_medio.setVisible(False)
            self.cb_medio.setToolTip("En AUTO caben 3 personas contando al encargado.")

    def _refrescar_chofer(self):
        self.cb_chofer.refrescar_opciones()

    def _sugerir_combustible(self):
        """Efectivo sugerido = km × tarifa.

        En un ajuste el lugar y la ruta no cambian, así que se sugiere el mismo
        combustible del viático original; se puede pulsar USAR o escribir otro valor.
        """
        km = self._km_orig_ajuste or self._num(self.txt_km)
        p = db.cargar_parametros()
        tarifa = float(p.get("valor_combustible_km", 0.25) or 0.25)
        self._combustible_sugerido = round(km * tarifa, 2)
        self.lbl_sugerido_val.setText("$%.2f" % self._combustible_sugerido)
        return self._combustible_sugerido

    def _usar_combustible(self):
        self.txt_efectivo.setText("%.2f" % self._sugerir_combustible())
        self._refrescar_prev()

    # ---------- estimado del tiempo de viaje ----------
    def _velocidad_estimada(self, p=None):
        """Velocidad promedio (km/h) del medio en que se viaja.

        Sale de Parámetros: el bus va más despacio que el automóvil y el camión o
        camioneta otro tanto.
        """
        p = p or db.cargar_parametros()
        tipo = (self.cb_vehiculo.valor() or "").upper()
        if "BUS" in tipo:
            return float(p.get("velocidad_bus") or 45)
        if "CAMION" in tipo or "GRUA" in tipo or "GRÚA" in tipo:
            return float(p.get("velocidad_camion") or 55)
        return float(p.get("velocidad_automovil") or 70)

    def _va_en_bus(self):
        """¿El vehículo elegido es un BUS?

        Solo informa el medio en que se viaja: el estimado de viaje es el mismo para
        todos los vehículos. Antes los del bus no se calculaban (sus horas se
        registraban a mano) y ahora el BUS se calcula igual que los demás: hace el
        mismo viaje y tarda lo mismo.
        """
        return "BUS" in (self.cb_vehiculo.valor() or "").upper()

    def _horas_del_destino(self):
        """Horas de viaje (ida) del destino elegido; 0 si no se sabe."""
        return _horas_desde_cuenca((self.cb_canton.valor() or "").strip().upper(),
                                   (self.cb_provincia.valor() or "").strip().upper())

    def _km_para_estimar(self):
        """Km con los que se estima el viaje (con respaldo si el formulario no los trae).

        En un **ajuste** el campo Km vale 0 a propósito (los km ya se pagaron en el
        viático original), así que antes el estimado se quedaba sin km, no podía calcular
        y salía el aviso «Faltan los km del cantón o la velocidad del vehículo» aunque el
        destino estuviera elegido. Ahora, si el formulario no trae km, se usa el del
        **cantón** (Parámetros → Rutas) y, si tampoco hubiera, el del viático original.
        """
        km = self._num(self.txt_km)
        if km > 0:
            return km
        km_canton = db.km_para((self.cb_canton.valor() or "").strip().upper())
        if km_canton:
            return float(km_canton)
        return float(getattr(self, "_km_orig_ajuste", 0) or 0)

    def _detalle_tramo(self, p, salida):
        """(horas, recorrido, comidas) del tramo que empieza a esa hora (o `recorrido`)."""
        if salida is None:
            return None
        return detalle_viaje(self._km_para_estimar(), self._velocidad_estimada(p), p,
                             salida, self._horas_del_destino())

    def _recalcular_horas(self):
        """Calcula las llegadas al cambiar la salida, los km o el vehículo.

        El vendedor registra la **salida de Miempresa** y la **salida del trabajo**; el
        sistema escribe la **llegada al trabajo** y la **llegada a Miempresa**. El
        cálculo es el mismo para **todos los vehículos, incluido el BUS**: el bus hace
        el mismo viaje y tarda lo mismo (primero las horas del cantón y, si no las
        tuviera, los km ÷ la velocidad del bus, Parámetros → «Estimado de viaje»). Las
        horas quedan escritas y se pueden corregir a mano.
        """
        if getattr(self, "_calculando", False):
            return                     # el propio cálculo mueve los campos: no repetir
        self._calculando = True
        try:
            self._estimar_viaje(avisar=False)
        finally:
            self._calculando = False
        self._refrescar_prev()

    def _estimar_manual(self):
        """Botón «Estimar viaje»: vuelve a calcular y muestra el detalle."""
        self._estimar_viaje(avisar=True)
        self._refrescar_prev()

    def _estimar_viaje(self, avisar=True):
        """Escribe la llegada al trabajo y la llegada a Miempresa.

        Cada tramo se calcula **desde su propia salida**: la ida desde la salida de
        Miempresa y la vuelta desde la salida del trabajo. El tiempo sale de las horas
        del cantón (tabla de distancias) o de los km ÷ la velocidad del vehículo,
        redondeado hacia arriba a la hora entera, más una hora por cada comida que cae
        dentro del viaje: el que sale a las 10:00 y llega a las 13:00 queda en **14:00**
        por el almuerzo y el que sale del trabajo a las 18:00 y llega a las 22:00 queda
        en **23:00** por la merienda (Parámetros → «Estimado de viaje»). Es una
        sugerencia: queda escrita y se puede corregir a mano. Con esas horas el sistema
        calcula las comidas día por día (el que va y vuelve el mismo día no come lo mismo
        que el que se queda).
        """
        p = db.cargar_parametros()
        recorrido = recorrido_de_viaje(self._km_para_estimar(), self._velocidad_estimada(p),
                                       self._horas_del_destino())
        if not recorrido:
            if avisar:
                canton = ((self.cb_canton.valor() or "").strip().upper()
                          or (self.cb_provincia.valor() or "").strip().upper()
                          or "el destino")
                C.aviso(self, "Estimar viaje",
                        "No se pudo calcular el tiempo de viaje.\n\n"
                        "Para «%s» no hay horas ni km en Parámetros → Rutas, y el vehículo\n"
                        "elegido no tiene velocidad configurada.\n\n"
                        "Revíselo en Parámetros → Rutas (escriba las horas o los km de ese\n"
                        "cantón) o en Parámetros → velocidades de viaje.\n\n"
                        "La provincia y el cantón ya están elegidos: no hace falta volver a\n"
                        "escribirlos." % canton)
            return None
        salida = self._cuando(self.cal_salida, self.cb_hsalida)
        salida_trab = self._cuando(self.cal_saltr, self.cb_hsaltr)
        if salida is None and salida_trab is None:
            if avisar:
                C.aviso(self, "Estimar viaje",
                        "Complete la salida de Miempresa y la salida del trabajo\n"
                        "(fecha y hora) para calcular las llegadas.")
            return None
        lineas = []
        if salida is not None:
            total, camino, comidas = self._detalle_tramo(p, salida)
            llegada = salida + timedelta(hours=total)
            self.cal_lleg.set_valor(llegada.date().isoformat())
            self.cb_hlleg.set_valor(llegada.strftime("%H:%M"))
            lineas.append(texto_estimado("Ida — salida de Miempresa", salida, total,
                                         camino, comidas, llegada))
        if salida_trab is not None:
            total, camino, comidas = self._detalle_tramo(p, salida_trab)
            regreso = salida_trab + timedelta(hours=total)
            self.cal_regreso.set_valor(regreso.date().isoformat())
            self.cb_hregreso.set_valor(regreso.strftime("%H:%M"))
            lineas.append(texto_estimado("Vuelta — salida del trabajo", salida_trab, total,
                                         camino, comidas, regreso))
        if avisar:
            C.informar(self, "Estimar viaje",
                       "Tiempo de viaje estimado (recorrido + comidas del camino)\n\n%s\n\n"
                       "Puede escribir otras horas si el viaje fue distinto."
                       % "\n\n".join(lineas))
        return total

    def _cuando(self, caja_fecha, caja_hora):
        """(fecha + hora) de un par de campos, o None si falta alguno."""
        f = (caja_fecha.valor() or "").strip()
        h = (caja_hora.valor() or "").strip()
        if not f or not h:
            return None
        try:
            hh, mm = [int(x) for x in h.split(":")[:2]]
            return _fechahora.combine(_fecha.fromisoformat(f), _dtime(hh, mm))
        except Exception:
            return None

    def _al_provincia(self):
        cantones = self._opc_cantones()
        actual = (self.cb_canton.valor() or "").strip().upper()
        self.cb_canton.refrescar_opciones()
        if actual not in cantones:
            self.cb_canton.set_valor("")
            self.txt_lugar.clear()
            self.txt_km.setText("0")
            self.lbl_km.setText("")
        self._refrescar_prev()

    def _al_canton(self):
        prov = (self.cb_provincia.valor() or "").strip().upper()
        cant = (self.cb_canton.valor() or "").strip().upper()
        if not prov or not cant:
            return
        self.txt_lugar.setText("%s, %s" % (cant, prov))
        km = _km_desde_cuenca(cant, prov)
        self.txt_km.setText(str(int(km)))
        horas = _horas_desde_cuenca(cant, prov)
        self.lbl_km.setText("tabla: %d km%s"
                            % (int(km),
                               " · %s de viaje" % horas_texto(horas) if horas else ""))
        self._refrescar_prev()

    # ---------- número del viático ----------
    def _actualizar_numero(self):
        if self.edit_numero and self.edit_ajuste_numero:
            self.lbl_numero.setText("VIÁTICO N° %s\nAJUSTE N° %s"
                                    % (db.numero_visible(self.edit_numero),
                                       self.edit_ajuste_numero))
            self.btn_guardar.setText("💾  GUARDAR AJUSTE")
        elif self.edit_numero:
            self.lbl_numero.setText("VIÁTICO N° %s\nORIGINAL — EDITANDO"
                                    % db.numero_visible(self.edit_numero))
            self.btn_guardar.setText("💾  GUARDAR VIÁTICO")
        else:
            proximo = db.proximo_numero()
            self.lbl_numero.setText("VIÁTICO N° %s\nAÑO %s"
                                    % (db.numero_visible(proximo), db.anio_de(proximo)))
            self.btn_guardar.setText("💾  GUARDAR VIÁTICO")

    @staticmethod
    def _num(caja):
        try:
            return float((caja.text() or "0").strip())
        except ValueError:
            return 0.0

    @staticmethod
    def _hora(texto):
        h, m = (texto or "").strip().split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Revise las horas (formato HH:MM).")
        return _dtime(int(h), int(m))

    # ---------- acompañantes ----------
    def agregar_pasajero(self):
        nombre = (self.cb_pas.valor() or "").strip().upper()
        medio = (self.cb_medio.currentText() or "AUTO").strip().upper() or "AUTO"
        if not nombre:
            C.aviso(self, "Pasajeros", "Seleccione o escriba un empleado.")
            return
        if nombre == (self.cb_encargado.valor() or "").strip().upper():
            C.aviso(self, "Pasajeros", "Ese empleado ya es el encargado.")
            return
        if any(nombre == p["nombre"] for p in self.pasajeros):
            C.aviso(self, "Pasajeros", "Ese pasajero ya está en la lista.")
            return
        # 1 = el encargado siempre va en el auto
        en_auto = 1 + sum(1 for p in self.pasajeros if p["medio"] == "AUTO")
        if medio == "AUTO" and en_auto >= 3:
            C.aviso(self, "Pasajeros",
                    "En el auto no pueden viajar más de 3 personas, incluido el "
                    "encargado.\nSi viaja más personal, seleccione BUS.")
            return
        self.pasajeros.append({"nombre": nombre, "medio": medio,
                               "extra": self._num(self.txt_extra)})
        self._refrescar_pas()
        self._refrescar_chofer()
        self._actualizar_medio()
        self._refrescar_prev()
        self.cb_pas.set_valor("")
        self.txt_extra.setText("0")
        self._guardar_borrador()         # la lista nueva queda en la memoria temporal

    def quitar_pasajero(self):
        i = self.lst_pas.currentRow()
        if i < 0:
            return
        self.pasajeros.pop(i)
        self._refrescar_pas()
        self._refrescar_chofer()
        self._actualizar_medio()
        self._refrescar_prev()
        self._guardar_borrador()         # la lista nueva queda en la memoria temporal

    def _refrescar_pas(self):
        self.lst_pas.clear()
        for p in self.pasajeros:
            reloj = ""      # (se quitó el ⏱ del horario propio por viajero: la lista va sin marca)
            self.lst_pas.addItem("%s%s   —   %s   —   extra $%.2f"
                                 % (p["nombre"], reloj, p["medio"], p["extra"]))

    # (se quitó el «⏱ Horario…» del viajero: el horario propio por viajero ya no se usa
    #  en la pantalla. Se deja el comentario para no cambiar la numeración del archivo.)

    # ---------- cálculo (mismas reglas de calculos.py) ----------
    def _construir_filas(self, avisar=False):
        """Arma las filas del viático (o del ajuste). None si hay un error."""
        try:
            nombre = (self.cb_encargado.valor() or "").strip().upper()
            if not nombre:
                raise ValueError("Seleccione el empleado encargado.")
            chofer = (self.cb_chofer.valor() or "").strip().upper()
            if chofer and chofer not in db.listar_empleados():
                raise ValueError("Seleccione un chofer válido.")
            if avisar and not chofer:
                raise ValueError("Seleccione un chofer.")
            # Quién recibe el efectivo del combustible, los km y el parqueadero/peaje: el
            # chofer y, si no hay chofer o el chofer no viaja en este viático, el
            # ENCARGADO (que es quien recibe el dinero). Antes, sin chofer, esos valores
            # se quedaban en cero sin avisar y el total no los mostraba.
            companeros = [p["nombre"] for p in self.pasajeros]
            lleva_gastos = (chofer if chofer and (chofer == nombre or chofer in companeros)
                            else nombre)
            medio_enc = "AUTO"        # el encargado siempre viaja en el vehículo
            pas_chofer = next((p for p in self.pasajeros if p["nombre"] == chofer), None) \
                if chofer else None
            if pas_chofer and pas_chofer["medio"] != "AUTO":
                raise ValueError("El chofer debe viajar en AUTO.")
            if chofer and chofer != nombre and pas_chofer is None:
                en_auto = 1 + sum(1 for p in self.pasajeros if p["medio"] == "AUTO")
                if en_auto >= 3:
                    raise ValueError("El chofer no está en la lista y el auto ya tiene "
                                     "3 personas. Agregue al chofer como acompañante.")
                self.pasajeros.append({"nombre": chofer, "medio": "AUTO", "extra": 0.0})
                self._refrescar_pas()
            lugar = (self.txt_lugar.text() or "").strip().upper()
            if not lugar:
                raise ValueError("Elija provincia y cantón para tener el lugar de trabajo.")
            hs, hr = self._hora(self.cb_hsalida.valor()), self._hora(self.cb_hregreso.valor())
            hlt, hst = self._hora(self.cb_hlleg.valor()), self._hora(self.cb_hsaltr.valor())
            fs, fr = self.cal_salida.valor(), self.cal_regreso.valor()
            if not fs or not fr:
                raise ValueError("Complete las fechas de salida y regreso.")
            fs_d, fr_d = _fecha.fromisoformat(fs), _fecha.fromisoformat(fr)
            if fr_d < fs_d:
                raise ValueError("La fecha de regreso no puede ser anterior a la de salida.")
            flt, fst = self.cal_lleg.valor(), self.cal_saltr.valor()
            prov = (self.cb_provincia.valor() or "").strip().upper()
            cant = (self.cb_canton.valor() or "").strip().upper()
            km = self._num(self.txt_km)
            peaje = self._num(self.txt_peaje)
            otros = self._num(self.txt_otros)
            efectivo = self._num(self.txt_efectivo)
        except ValueError as ex:
            if avisar:
                C.error(self, "Datos inválidos", str(ex))
            return None

        p = db.cargar_parametros()
        base = {"lugar_trabajo": lugar, "provincia": prov, "canton": cant,
                "orden_combustible_2": (self.txt_ord2.text() or "").strip(),
                "efectivo_combustible": efectivo,
                "ajuste_numero": self.edit_ajuste_numero or 0,
                "fecha_salida": fs_d.isoformat(), "hora_salida": hs.strftime("%H:%M"),
                "fecha_regreso": fr_d.isoformat(), "hora_regreso": hr.strftime("%H:%M"),
                "fecha_llegada_trabajo": (flt or fs),
                "hora_llegada_trabajo": hlt.strftime("%H:%M"),
                "fecha_salida_trabajo": (fst or fr),
                "hora_salida_trabajo": hst.strftime("%H:%M")}
        if self.edit_ajuste_numero:
            return self._filas_ajuste(base, nombre, chofer, medio_enc, fr_d, hr, avisar,
                                      efectivo, peaje, otros)

        es_chofer_enc = int(lleva_gastos == nombre)
        v = DatosViaje(nombre_empleado=nombre, lugar_trabajo=lugar, fecha_salida=fs_d,
                       hora_salida=hs, fecha_regreso=fr_d, hora_regreso=hr,
                       fecha_llegada_trabajo=_fecha.fromisoformat(base["fecha_llegada_trabajo"]),
                       hora_llegada_trabajo=hlt,
                       fecha_salida_trabajo=_fecha.fromisoformat(base["fecha_salida_trabajo"]),
                       hora_salida_trabajo=hst,
                       km_recorridos=km if es_chofer_enc else 0.0,
                       parqueadero_peaje=peaje if es_chofer_enc else 0.0,
                       otros=otros,
                       combustible_efectivo=efectivo if es_chofer_enc else 0.0)
        reg = calcular(v, p)
        filas = [{**base, "nombre_empleado": nombre, "es_encargado": 1,
                  "es_chofer": es_chofer_enc, "medio_transporte": medio_enc,
                  "extra_transporte": 0.0,
                  "km_recorridos": km if es_chofer_enc else 0.0,
                  "parqueadero_peaje": peaje if es_chofer_enc else 0.0,
                  "otros": otros, **reg}]
        for pas in self.pasajeros:
            es_chofer_pas = int(pas["nombre"] == lleva_gastos)
            # Si el viajero tiene su propio horario (el que va en BUS sale antes o
            # llega más tarde que el que va en el vehículo de la empresa) se usan sus
            # horas: las comidas y el hospedaje de esa persona salen de ahí.
            horario = pas.get("horario") or {}
            p_sal = _par_fecha_hora(horario.get("salida"), fs_d, hs)
            p_lle = _par_fecha_hora(horario.get("llegada"),
                                    _fecha.fromisoformat(base["fecha_llegada_trabajo"]), hlt)
            p_str = _par_fecha_hora(horario.get("salida_trab"),
                                    _fecha.fromisoformat(base["fecha_salida_trabajo"]), hst)
            p_reg = _par_fecha_hora(horario.get("regreso"), fr_d, hr)
            vp = DatosViaje(
                nombre_empleado=pas["nombre"], lugar_trabajo=lugar,
                fecha_salida=p_sal[0], hora_salida=p_sal[1],
                fecha_regreso=p_reg[0], hora_regreso=p_reg[1],
                fecha_llegada_trabajo=p_lle[0], hora_llegada_trabajo=p_lle[1],
                fecha_salida_trabajo=p_str[0], hora_salida_trabajo=p_str[1],
                km_recorridos=km if es_chofer_pas else 0.0,
                parqueadero_peaje=peaje if es_chofer_pas else 0.0,
                otros=pas["extra"],
                combustible_efectivo=efectivo if es_chofer_pas else 0.0)
            rp = calcular(vp, p)
            filas.append({**base, "nombre_empleado": pas["nombre"], "es_encargado": 0,
                          "es_chofer": es_chofer_pas, "medio_transporte": pas["medio"],
                          "extra_transporte": pas["extra"],
                          "km_recorridos": km if es_chofer_pas else 0.0,
                          "parqueadero_peaje": peaje if es_chofer_pas else 0.0,
                          "otros": pas["extra"],
                          "fecha_salida": p_sal[0].isoformat(),
                          "hora_salida": p_sal[1].strftime("%H:%M"),
                          "fecha_regreso": p_reg[0].isoformat(),
                          "hora_regreso": p_reg[1].strftime("%H:%M"),
                          "fecha_llegada_trabajo": p_lle[0].isoformat(),
                          "hora_llegada_trabajo": p_lle[1].strftime("%H:%M"),
                          "fecha_salida_trabajo": p_str[0].isoformat(),
                          "hora_salida_trabajo": p_str[1].strftime("%H:%M"),
                          **rp})
        # El retiro del cajero lo hace una sola persona (el encargado) y lleva el dinero de
        # todo el grupo, así que el redondeo se hace UNA vez sobre el total del viático:
        # antes se redondeaba la cuenta de cada viajero por separado y la suma salía más
        # alta que el total (183 → 185 + 116 → 120 + 116 → 120 daban 425 con un total de
        # 415). El valor queda en la fila del encargado.
        cajero_del_grupo(filas, p)
        return filas

    def _filas_ajuste(self, base, nombre, chofer, medio_enc, fr, hr, avisar=False,
                      efectivo=0.0, peaje=0.0, otros=0.0):
        """Días adicionales del ajuste: comidas, hospedaje y agua.

        En el ajuste también se puede enviar más efectivo para combustible (o usar el
        sugerido) y registrar parqueadero/peaje y otros gastos del encargado. Sin
        taxis ni transporte extra de los acompañantes.
        """
        orig = db.filas_originales(self.edit_numero)
        if not orig:
            if avisar:
                C.error(self, "Ajuste", "No se encontró el viático original.")
            return None
        fr_o = max(_fecha.fromisoformat(r["fecha_regreso"]) for r in orig)
        ndias = (fr - fr_o).days
        if ndias < 1:
            if avisar:
                C.error(self, "Ajuste",
                        "El regreso del ajuste debe ser al menos 1 día después del "
                        "regreso original (%s), que es hasta donde ya se entregó viático."
                        % fr_o.strftime("%d/%m/%Y"))
                return None
            ndias = 0
        p = db.cargar_parametros()
        des = p["valor_desayuno"] * ndias
        alm = p["valor_almuerzo"] * ndias
        mer = (p["valor_merienda"] * ndias) if hr >= p["hora_limite_merienda"] else 0.0
        hos = p["valor_hospedaje"] * ndias
        agua = p["valor_agua"] * ndias
        total = round(des + alm + mer + hos + agua, 2)
        base.update(fecha_salida=(fr_o + timedelta(days=1)).isoformat(),
                    hora_salida="00:00", ajuste_numero=self.edit_ajuste_numero)
        # El cajero del ajuste se calcula al final, una sola vez sobre el total del ajuste
        # (`cajero_del_grupo`), igual que en el viático original.
        calc = {"dias_viaje": ndias, "desayuno": des, "almuerzo": alm, "merienda": mer,
                "taxi_salida": 0.0, "taxi_regreso": 0.0, "hospedaje": hos, "agua": agua,
                "combustible": 0.0, "total": total, "valor_cajero": 0.0}
        extra_comb = round(float(efectivo or 0), 2)
        extra_peaje = round(float(peaje or 0), 2)
        extra_otros = round(float(otros or 0), 2)
        # Igual que en el viático original: si no hay chofer (o el chofer no viaja en este
        # viático), el efectivo del combustible y el parqueadero/peaje los lleva el
        # ENCARGADO (antes se perdían en silencio).
        companeros = [p["nombre"] for p in self.pasajeros]
        lleva_gastos = (chofer if chofer and (chofer == nombre or chofer in companeros)
                        else nombre)

        def row(nom, enc, medio):
            es_chofer_fila = int(nom == lleva_gastos)
            comb = extra_comb if es_chofer_fila else 0.0
            peaj = extra_peaje if es_chofer_fila else 0.0
            otro = extra_otros if enc else 0.0
            total_fila = round(total + comb + peaj + otro, 2)
            return {**base, "nombre_empleado": nom, "es_encargado": enc,
                    "es_chofer": es_chofer_fila, "medio_transporte": medio,
                    "extra_transporte": 0.0, "km_recorridos": 0.0,
                    "parqueadero_peaje": peaj, "otros": otro,
                    **{**calc, "combustible": comb, "total": total_fila}}

        filas = [row(nombre, 1, medio_enc)]
        for pas in self.pasajeros:
            filas.append(row(pas["nombre"], 0, pas["medio"]))
        # El cajero del ajuste también es uno solo: el retiro lo hace el encargado y lleva el
        # dinero de todos, así que se redondea el total del ajuste una sola vez (y no la
        # cuenta de cada viajero, que sumaba más que el total).
        cajero_del_grupo(filas, p)
        return filas

    # ---------- vista previa ----------
    def _refrescar_prev(self):
        """Pinta la vista previa y sugiere el efectivo de combustible.

        En un viático nuevo se ven las personas con la fila de **TOTALES** resaltada.
        En un ajuste se ve igual que en el PDF: primero el original con sus totales,
        después cada ajuste anterior, después el ajuste que se está digitando y al
        final el **TOTAL GENERAL** de todo lo entregado.
        """
        self._sugerir_combustible()
        nuevos = self._construir_filas() or []
        salida = []
        tipos = []                    # "sep" | "dato" | "total" | "general"

        def bloque(filas, rotulo=None):
            if rotulo is not None:
                salida.append(sep_vals(rotulo))
                tipos.append("sep")
            for i, fila in enumerate(filas, 1):
                salida.append(vals_fila(i, fila))
                tipos.append("dato")
            if filas:
                salida.append(vals_totales(filas))
                tipos.append("total")

        if self.edit_ajuste_numero and self.edit_numero:
            todos = []
            for rotulo, filas in self._bloques_guardados():
                todos.extend(filas)
                bloque(filas, rotulo)
            bloque(nuevos, "═ AJUSTE N° %s · NUEVO ═" % self.edit_ajuste_numero)
            todos.extend(nuevos)
            if todos:
                salida.append(vals_totales(todos, "TOTAL GENERAL"))
                tipos.append("general")
        else:
            bloque(nuevos)

        self.tabla_prev.poner(salida)
        zebra = 0
        for pos, tipo in enumerate(tipos):
            if tipo == "sep":
                _pintar(self.tabla_prev, [pos], FONDO_SEP)
                zebra = 0
            elif tipo == "total":
                _pintar(self.tabla_prev, [pos], FONDO_TOTAL)
            elif tipo == "general":
                _pintar(self.tabla_prev, [pos], FONDO_GENERAL)
            else:
                if zebra % 2 == 0:
                    _pintar(self.tabla_prev, [pos], FONDO_ZEBRA)
                zebra += 1
        rotulo = getattr(self, "lbl_avisos", None)
        if rotulo is not None:
            rotulo.setText(self._explicar_conceptos(nuevos))

    def _explicar_conceptos(self, filas):
        """Explica por qué un concepto salió en cero (los taxis y el combustible).

        Se revisa la fila del encargado, que es la que marca las horas del viaje. Así, si
        el taxi de regreso no se sumó, la ventana misma dice el motivo: se paga desde la
        hora límite (21:00 de fábrica) y el viaje está registrado a otra hora.
        """
        if not filas:
            return ""
        if self.edit_ajuste_numero:
            return ("En un AJUSTE solo se pagan los días, las comidas, el hospedaje y el "
                    "agua: los taxis, el combustible y el parqueadero/peaje van en el "
                    "viático original.")
        f = filas[0]
        p = db.cargar_parametros()

        def cero(campo):
            return abs(float(f.get(campo) or 0)) < 0.005

        def hh(valor):
            return str(valor or "")[:5] or "—"

        avisos = []
        if cero("taxi_salida"):
            avisos.append("Taxi de salida $0: se paga si sale a las %s o antes (sale a las %s)"
                          % (hh(p.get("hora_limite_taxi_salida")), f.get("hora_salida", "—")))
        if cero("taxi_regreso"):
            avisos.append("Taxi de regreso $0: se paga si vuelve a las %s o después "
                          "(vuelve a las %s)"
                          % (hh(p.get("hora_limite_taxi_regreso")), f.get("hora_regreso", "—")))
        if cero("combustible"):
            avisos.append("Combustible $0: escriba los km del viaje o el efectivo en "
                          "«💵 Efectivo Comb. $»")
        return "   ·   ".join(avisos)

    def _bloques_guardados(self):
        """Bloques ya guardados del viático: el original y cada ajuste.

        Devuelve [(rótulo, filas), ...] para poder mostrar la vista previa igual que
        el PDF cuando se está haciendo un ajuste.
        """
        bloques = []
        try:
            guardadas = db.filas_numero(self.edit_numero)
        except Exception:
            return bloques
        grupos = {}
        for fila in guardadas:
            grupos.setdefault(int(fila.get("ajuste_numero") or 0), []).append(fila)
        for ajuste in sorted(grupos):
            rotulo = "═ ORIGINAL ═" if not ajuste else "═ AJUSTE N° %d ═" % ajuste
            bloques.append((rotulo, grupos[ajuste]))
        return bloques

    # ---------- memoria temporal (lo que se está llenando) ----------
    # La vendedora llena el viático, se va a buscar un dato y alguien cierra el sistema (o
    # se apaga la computadora): al volver a entrar con **su usuario**, el sistema le ofrece
    # lo que estaba llenando. Se guarda solo, cada 20 segundos y al cerrar la ventana, **en
    # la base y por usuario** (`borradores`), así se recupera igual en esta PC o en otra si
    # el sistema trabaja contra el servidor. Al guardar el viático, al limpiar el formulario
    # o al pasar los días, el borrador se borra solo.
    def _clave_formulario(self):
        """Estado completo del formulario en texto, para guardarlo y volverlo a cargar."""
        return {
            "edit_numero": self.edit_numero,
            "edit_ajuste_numero": self.edit_ajuste_numero,
            "responsable": (self.cb_responsable.valor() or "").strip(),
            "cliente": (self.cb_cliente.valor() or "").strip(),
            "vehiculo": (self.cb_vehiculo.valor() or "").strip(),
            "ord1": self.txt_ord1.text().strip(), "ord2": self.txt_ord2.text().strip(),
            "efectivo": self.txt_efectivo.text().strip(),
            "obs": self.txt_obs.text().strip(),
            "recibo": self.txt_recibo.text().strip(),
            "recibo2": self.txt_recibo2.text().strip(),
            "recibo3": self.txt_recibo3.text().strip(),
            "encargado": (self.cb_encargado.valor() or "").strip(),
            "chofer": (self.cb_chofer.valor() or "").strip(),
            "provincia": (self.cb_provincia.valor() or "").strip(),
            "canton": (self.cb_canton.valor() or "").strip(),
            "lugar": self.txt_lugar.text().strip(),
            "km": self.txt_km.text().strip(), "peaje": self.txt_peaje.text().strip(),
            "otros": self.txt_otros.text().strip(), "extra": self.txt_extra.text().strip(),
            "salida": [self.cal_salida.valor(), self.cb_hsalida.valor()],
            "regreso": [self.cal_regreso.valor(), self.cb_hregreso.valor()],
            "llego": [self.cal_lleg.valor(), self.cb_hlleg.valor()],
            "sali_trabajo": [self.cal_saltr.valor(), self.cb_hsaltr.valor()],
            "pasajeros": [dict(p) for p in self.pasajeros],
        }

    def _recordar_base(self):
        """Anota cómo está el formulario ahora (para saber después si se escribió algo)."""
        self._borrador_base = self._clave_formulario()

    @staticmethod
    def _es_cero(texto) -> bool:
        """¿Ese monto vale cero (o no es un número)?"""
        try:
            return abs(float(str(texto or "0").replace(",", ".") or 0)) < 0.005
        except ValueError:
            return True

    def _hay_contenido(self, estado) -> bool:
        """¿Ese estado tiene algo escrito (más que el formulario recién abierto)?"""
        estado = estado or {}
        return bool(estado.get("encargado") or estado.get("cliente") or estado.get("lugar")
                    or estado.get("obs") or estado.get("ord1") or estado.get("ord2")
                    or estado.get("recibo") or estado.get("recibo2") or estado.get("recibo3")
                    or estado.get("vehiculo") or estado.get("pasajeros")
                    or not self._es_cero(estado.get("km"))
                    or not self._es_cero(estado.get("efectivo"))
                    or not self._es_cero(estado.get("otros")))

    def _hay_algo_que_recordar(self, estado) -> bool:
        """¿Vale la pena guardar lo que hay ahora?

        Solo si hay algo escrito **y** distinto de como estaba el formulario al abrirlo: así,
        abrir la pantalla y cerrarla sin tocar nada no deja un aviso para la próxima vez.
        """
        return bool(self._hay_contenido(estado) and estado != (self._borrador_base or {}))

    def _guardar_borrador(self) -> bool:
        """Guarda lo que hay escrito (memoria temporal). Devuelve si guardó algo."""
        try:
            estado = self._clave_formulario()
            if self._hay_algo_que_recordar(estado):
                if db.guardar_borrador(self.usuario, estado, "viatico"):
                    self._borrador_guardado = True
                    return True
                return False
            # No hay nada escrito: si había un borrador (se recuperó y se limpió), se borra.
            if self._borrador_guardado:
                db.borrar_borrador(self.usuario, "viatico")
                self._borrador_guardado = False
            return False
        except Exception as ex:
            print("No se pudo guardar la memoria temporal: %s" % ex)
            return False

    @staticmethod
    def _cuando_guardado(texto) -> str:
        """«hoy a las 14:05», «ayer a las 09:30» o «el 28/09/2026 a las 09:30»."""
        try:
            cuando = _fechahora.strptime(str(texto or "")[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return "la última vez que entró a esta pantalla"
        hora = cuando.strftime("%H:%M")
        hoy = _fecha.today()
        if cuando.date() == hoy:
            return "hoy a las %s" % hora
        if cuando.date() == hoy - timedelta(days=1):
            return "ayer a las %s" % hora
        return "el %s a las %s" % (cuando.strftime("%d/%m/%Y"), hora)

    @staticmethod
    def _resumen_estado(estado) -> str:
        """Línea corta para que el usuario reconozca lo que dejó a medio llenar."""
        estado = estado or {}
        partes = []
        if estado.get("encargado"):
            partes.append("Encargado: %s" % estado["encargado"])
        if estado.get("lugar") or estado.get("canton"):
            partes.append("Destino: %s" % (estado.get("lugar") or estado.get("canton")))
        if not ViajeWindow._es_cero(estado.get("km")):
            partes.append("%s km" % estado["km"])
        if estado.get("cliente"):
            partes.append("Cliente: %s" % estado["cliente"])
        cuantos = len(estado.get("pasajeros") or [])
        if cuantos:
            partes.append("%d acompañante(s)" % cuantos)
        if estado.get("edit_numero"):
            partes.append("(se estaba editando el viático N° %s)"
                          % db.numero_visible(estado["edit_numero"]))
        return "\n".join(partes) or "Quedaron algunos datos escritos."

    def _aplicar_estado(self, estado) -> bool:
        """Vuelve a poner en el formulario lo que se había guardado.

        Deja en `self._nota_recuperado` lo que haya que avisarle al usuario (por ejemplo,
        que el viático que se estaba editando ya se guardó en otra parte).
        """
        if not estado:
            return False
        self._nota_recuperado = ""
        self._calculando = True
        try:
            for caja, clave in ((self.txt_ord1, "ord1"), (self.txt_ord2, "ord2"),
                                (self.txt_efectivo, "efectivo"), (self.txt_obs, "obs"),
                                (self.txt_recibo, "recibo"), (self.txt_recibo2, "recibo2"),
                                (self.txt_recibo3, "recibo3"), (self.txt_lugar, "lugar"),
                                (self.txt_km, "km"), (self.txt_peaje, "peaje"),
                                (self.txt_otros, "otros"), (self.txt_extra, "extra")):
                caja.setText(str(estado.get(clave) or ""))
            self.cb_responsable.set_valor(estado.get("responsable") or "")
            self.cb_cliente.set_valor(estado.get("cliente") or "")
            self.cb_vehiculo.set_valor(estado.get("vehiculo") or "")
            self.cb_provincia.set_valor(estado.get("provincia") or "")
            self.cb_canton.refrescar_opciones()
            self.cb_canton.set_valor(estado.get("canton") or "")
            self.cb_encargado.set_valor(estado.get("encargado") or "")
            self.pasajeros = [dict(p) for p in (estado.get("pasajeros") or [])]
            self._refrescar_pas()
            self.cb_chofer.refrescar_opciones()
            self.cb_chofer.set_valor(estado.get("chofer") or "")
            self._actualizar_medio()
            for campo_f, campo_h, clave in ((self.cal_salida, self.cb_hsalida, "salida"),
                                             (self.cal_regreso, self.cb_hregreso, "regreso"),
                                             (self.cal_lleg, self.cb_hlleg, "llego"),
                                             (self.cal_saltr, self.cb_hsaltr,
                                              "sali_trabajo")):
                par = list(estado.get(clave) or []) + ["", ""]
                campo_f.set_valor(par[0] or "")
                campo_h.set_valor(par[1] or "")
            self.edit_numero = estado.get("edit_numero") or None
            self.edit_ajuste_numero = estado.get("edit_ajuste_numero") or None
            if self.edit_numero and not self._viatico_pendiente(self.edit_numero):
                # El viático que se estaba editando ya se guardó en otra parte (o se anuló):
                # se recupera como viático nuevo, para no pisar nada de lo que ya está.
                self._nota_recuperado = (
                    "\n\nOJO: el viático N° %s ya no está pendiente, así que lo recuperado "
                    "queda como viático NUEVO." % db.numero_visible(self.edit_numero))
                self.edit_numero = None
                self.edit_ajuste_numero = None
            self._actualizar_numero()
            self._bloquear_salida(self.edit_ajuste_numero is not None)
        finally:
            self._calculando = False
        self._refrescar_prev()
        # Lo recuperado se sigue guardando solo mientras la ventana esté abierta.
        self._borrador_base = {}
        self._borrador_guardado = True
        return True

    @staticmethod
    def _viatico_pendiente(numero) -> bool:
        """¿Ese viático sigue existiendo y pendiente (o sea que se puede seguir editando)?"""
        try:
            filas = db.filas_originales(numero)
        except Exception:
            return True
        return bool(filas) and filas[0]["estado"] == "PENDIENTE"

    def _recuperar_borrador(self, silencioso=False) -> bool:
        """Trae de vuelta lo que este usuario dejó a medio llenar.

        Con `silencioso=True` (el aviso que sale solo al abrir la ventana) no dice nada si
        no hay nada guardado; desde el botón «🕘 RECUPERAR LO ÚLTIMO» sí lo explica.
        """
        try:
            info = db.leer_borrador(self.usuario, "viatico")
        except Exception:
            info = None
        estado = (info or {}).get("datos") or {}
        if not info or not self._hay_contenido(estado):
            if not silencioso:
                C.informar(self, "Recuperar lo último",
                           "No hay nada guardado a medias para su usuario.\n\n"
                           "El sistema guarda solo lo que se escribe en esta pantalla (cada "
                           "20 segundos) y lo borra apenas el viático se guarda.")
            return False
        self._borrador_guardado = True
        cuando = self._cuando_guardado(info.get("actualizado_el"))
        texto = ("Quedó un viático a medio llenar (%s):\n\n%s\n\n"
                 % (cuando, self._resumen_estado(estado)))
        if self._hay_contenido(self._clave_formulario()):
            texto += ("OJO: lo que hay ahora en el formulario se reemplaza con lo "
                      "guardado.\n\n")
        texto += "¿Quiere que el sistema lo vuelva a poner en el formulario?"
        if not C.confirmar(self, "Recuperar lo que estaba llenando", texto,
                           si="Sí, recuperarlo", no="No, seguir como está"):
            return False
        if not self._aplicar_estado(estado):
            return False
        self.lbl_estado.setText("Recuperado lo que estaba llenando (%s)." % cuando)
        db.registrar_bitacora(self.usuario, "RECUPERÓ LO QUE ESTABA LLENANDO", "viáticos",
                              "", "Volvió a cargar en el formulario la captura del %s"
                              % cuando)
        C.informar(self, "Recuperado",
                   "Sus datos volvieron al formulario (%s).\n\nRevíselos y guarde el "
                   "viático cuando esté listo.%s"
                   % (cuando, getattr(self, "_nota_recuperado", "")))
        return True

    def _boton_recuperar(self):
        """Botón «🕘 RECUPERAR LO ÚLTIMO» (de la barra de la captura)."""
        self._recuperar_borrador(silencioso=False)

    def _avisar_borrador_pendiente(self):
        """Aviso que sale solo al abrir la ventana: si quedó algo a medio llenar, lo ofrece."""
        if not self.isVisible():
            return
        self._recuperar_borrador(silencioso=True)

    def _borrar_borrador(self):
        """Olvida el borrador de este usuario (el viático ya se guardó o se limpió)."""
        if not self._borrador_guardado:
            return
        try:
            db.borrar_borrador(self.usuario, "viatico")
        except Exception:
            pass
        self._borrador_guardado = False

    def closeEvent(self, evento):
        """Al cerrar la ventana se guarda lo que quedó escrito (memoria temporal)."""
        self._guardar_borrador()
        super().closeEvent(evento)

    # ---------- guardar / imprimir ----------
    def _cab(self):
        return {"responsable": (self.cb_responsable.valor() or "").strip().upper(),
                "cliente_proyecto": (self.cb_cliente.valor() or "").strip().upper(),
                "orden_combustible": (self.txt_ord1.text() or "").strip(),
                "placa": (self.cb_vehiculo.valor() or "").strip().upper(),
                "observaciones": (self.txt_obs.text() or "").strip().upper(),
                "recibo_viatico": (self.txt_recibo.text() or "").strip(),
                "recibo_viatico_2": (self.txt_recibo2.text() or "").strip(),
                "recibo_viatico_3": (self.txt_recibo3.text() or "").strip()}

    def _bitacora(self, accion, numero, cab, filas, nota=""):
        """Registra en el informe de actividad lo que se hizo con el viático."""
        enc = next((f["nombre_empleado"] for f in filas if f.get("es_encargado")), "")
        lugar = (filas[0].get("lugar_trabajo") or "") if filas else ""
        total = sum(float(f.get("total") or 0) for f in filas)
        detalle = ("Creado por %s · encargado %s · %s · %d persona(s) · total $%.2f"
                   % (cab.get("responsable") or "-", enc or "-", lugar, len(filas), total))
        if nota:
            detalle += " · " + nota
        db.registrar_bitacora(self.usuario, accion, "viáticos",
                              "N° %s" % db.etiqueta_numero(numero), detalle)

    def _cliente_valido(self, cliente, avisar=False):
        """Revisa que el cliente escrito esté en la lista (Parámetros → Clientes).

        Antes, cualquier nombre que se escribiera en «Cliente y proyecto» se guardaba
        solo en la base de clientes; ahora hay que **elegirlo de la lista**, así no se
        llenan de nombres mal escritos. Si no está, el viático no se guarda y se avisa
        cómo agregarlo.
        """
        cliente = (cliente or "").strip().upper()
        if not cliente:
            return True
        try:
            if db.existe_cliente(cliente):
                return True
        except Exception:
            return True
        if avisar:
            C.error(self, "Cliente no válido",
                    "El cliente «%s» no está en la lista de clientes.\n\n"
                    "Elíjalo de la lista desplegable, o pídale al superusuario que lo\n"
                    "agregue en PARÁMETROS → 🧑‍💼 Clientes (también puede importar la\n"
                    "lista completa desde el Excel de clientes)." % cliente)
        return False

    def guardar(self):
        filas = self._construir_filas(avisar=True)
        if not filas:
            return
        cab = self._cab()
        if not self._cliente_valido(cab["cliente_proyecto"], avisar=True):
            return
        guardado_num = self.edit_numero
        if self.edit_numero and self.edit_ajuste_numero:
            db.actualizar_ajuste_viaje(self.edit_numero, self.edit_ajuste_numero, cab, filas)
            self._bitacora("EDITÓ AJUSTE", guardado_num, cab, filas,
                           "ajuste N° %s" % self.edit_ajuste_numero)
            C.informar(self, "Guardado",
                       "Ajuste N° %s del viático N° %s actualizado."
                       % (self.edit_ajuste_numero, db.numero_visible(self.edit_numero)))
            self.lbl_estado.setText("Último guardado: viático %s, ajuste %s"
                                    % (db.numero_visible(self.edit_numero),
                                       self.edit_ajuste_numero))
        elif self.edit_numero:
            db.actualizar_viaje(self.edit_numero, cab, filas)
            self._bitacora("EDITÓ VIÁTICO", guardado_num, cab, filas, "viático original")
            C.informar(self, "Guardado",
                       "Viático original N° %s actualizado."
                       % db.numero_visible(self.edit_numero))
            self.lbl_estado.setText("Último guardado: N° %s"
                                    % db.numero_visible(self.edit_numero))
        else:
            n = db.guardar_viaje(cab, filas)
            guardado_num = n
            self._bitacora("CREÓ VIÁTICO", n, cab, filas, "viático original")
            C.informar(self, "Guardado",
                       "VIÁTICO N° %s del año %s guardado con %d empleado(s)."
                       % (db.numero_visible(n), db.anio_de(n), len(filas)))
            self.lbl_estado.setText("Último guardado: N° %s" % db.numero_visible(n))
        self.limpiar()
        self.refrescar_historial()
        self.pestanas.setCurrentIndex(1)
        if guardado_num:
            self.tabla_hist.seleccionar_donde("crudo", str(guardado_num))
            self._ver_detalle()

    def imprimir(self):
        filas = self._construir_filas(avisar=True)
        if not filas:
            return
        num = self.edit_numero or db.proximo_numero()
        reportes.imprimir_viatico(num, self._cab(), filas)

    def limpiar(self):
        """Deja el formulario listo para un viático nuevo."""
        self._borrar_borrador()          # lo que se estaba llenando ya no hace falta
        self.pasajeros = []
        self.edit_numero = None
        self.edit_ajuste_numero = None
        self._km_orig_ajuste = 0.0
        self._refrescar_pas()
        self._refrescar_prev()
        for caja in (self.txt_ord1, self.txt_ord2, self.txt_obs, self.txt_lugar,
                     self.txt_recibo, self.txt_recibo2, self.txt_recibo3):
            caja.clear()
        for combo in (self.cb_responsable, self.cb_vehiculo, self.cb_encargado,
                      self.cb_provincia, self.cb_canton, self.cb_pas, self.cb_chofer,
                      self.cb_cliente):
            combo.set_valor("")
        self._actualizar_medio()
        for caja in (self.txt_km, self.txt_otros, self.txt_extra, self.txt_efectivo):
            caja.setText("0")
        self.txt_peaje.setText("%.2f" % float(
            db.cargar_parametros().get("valor_parqueadero_peaje", 0) or 0))
        self.lbl_km.setText("")
        self._sugerir_combustible()
        self._refrescar_chofer()
        self._poner_fechas_hoy()
        self._bloquear_salida(False)
        self._actualizar_numero()
        self._responsable_por_defecto()
        self._recordar_base()            # formulario en blanco: no hay nada que recordar

    def nuevo_desde_historial(self):
        self.limpiar()
        self.pestanas.setCurrentIndex(0)

    # ================= HISTORIAL =================
    def _tab_historial(self):
        pag = QWidget()
        lay = C.margenes(QVBoxLayout(pag), esp=10)

        # --- filtros y exportación ---
        filtros = C.Tarjeta()
        fila = C.margenes(QHBoxLayout(), esp=8)
        self.txt_buscar = C.campo("", ancho=240,
                                  placeholder="N° , empleado, lugar, responsable…",
                                  cb=lambda _t: self.refrescar_historial())
        self.cb_prov_hist = C.combo(["Todas"] + list(db.listar_provincias()), "Todas",
                                    ancho=180, cb=lambda _t: self.refrescar_historial())
        self.cb_est_hist = C.combo(["Todos", "PENDIENTE", "JUSTIFICADO", "ANULADO"],
                                   "Todos", ancho=150,
                                   cb=lambda _t: self.refrescar_historial())
        fila.addWidget(C.etiqueta("🔍 Buscar:", clave=True))
        fila.addWidget(self.txt_buscar)
        fila.addWidget(C.etiqueta("Provincia:", clave=True))
        fila.addWidget(self.cb_prov_hist)
        fila.addWidget(C.etiqueta("Estado:", clave=True))
        fila.addWidget(self.cb_est_hist)
        fila.addWidget(C.boton_primario("🔄  Actualizar", self.refrescar_historial))
        fila.addStretch(1)
        filtros.agregar_fila(fila)

        # las acciones del viático elegido van en la misma tarjeta de arriba
        fila = C.margenes(QHBoxLayout(), esp=6)
        fila.addWidget(C.boton_secundario("✏️  Editar original", self.editar_seleccionado))
        fila.addWidget(C.boton_primario("➕  Ajustar viático", self.ajustar_seleccionado))
        fila.addWidget(C.boton_secundario("✏️  Editar ajuste", self.editar_ajuste_seleccionado))
        fila.addWidget(C.boton_secundario("🚫  Anular", self.anular_seleccionado))
        fila.addWidget(C.boton_primario("🆕  Nuevo viático", self.nuevo_desde_historial))
        fila.addWidget(C.boton_secundario("👁  Ver justificado",
                                         self.ver_justificado_seleccionado))
        # El ajuste con el que se imprime, se exporta o se edita (la lista de abajo ya
        # muestra el original, cada ajuste y su total).
        fila.addSpacing(T.px(12))
        fila.addWidget(C.etiqueta("📋  Ajuste:", clave=True))
        self.cb_ajuste = C.combo([], "—", ancho=110)
        self.cb_ajuste.setToolTip("Ajuste para imprimir, exportar o editar")
        fila.addWidget(self.cb_ajuste)
        fila.addStretch(1)
        filtros.agregar_fila(fila)

        # imprimir y exportar van en pares: lo que se imprime también se saca a Excel
        fila = C.margenes(QHBoxLayout(), esp=6)
        fila.addWidget(C.etiqueta("🖨  Imprimir / PDF:", clave=True))
        fila.addWidget(C.boton_borde("Original", self.imprimir_hist_original))
        fila.addWidget(C.boton_borde("Ajuste", self.imprimir_hist_ajuste))
        fila.addWidget(C.boton_amarillo("General", self.imprimir_hist_general))
        fila.addSpacing(T.px(16))
        fila.addWidget(C.etiqueta("📊  Excel:", clave=True))
        fila.addWidget(C.boton_primario("Original", self.exportar_excel_original))
        fila.addWidget(C.boton_primario("Ajuste", self.exportar_excel_ajuste))
        fila.addWidget(C.boton_primario("General", self.exportar_excel_general))
        fila.addStretch(1)
        filtros.agregar_fila(fila)
        lay.addWidget(filtros)

        # --- viáticos generales ---
        self.tabla_hist = C.Tabla(COLS_HIST, ordenar=False, alto_filas=24)
        self.tabla_hist.setMinimumHeight(T.px(150, 110))
        self.tabla_hist.agregar_manejadores(al_seleccionar=lambda _f: self._ver_detalle())
        mid = C.Tarjeta("Viáticos")
        mid.agregar(self.tabla_hist, 1)
        lay.addWidget(mid, 1)

        # --- detalle del viático: el original, cada ajuste y sus totales ---
        self.tabla_det = C.Tabla(COLS_DETALLE, ordenar=False, alto_filas=24,
                                 estirar_ultima=False)
        self.tabla_det.setMinimumHeight(T.px(185, 130))
        det = C.Tarjeta("Detalle — original y ajustes")
        det.agregar(self.tabla_det, 1)
        lay.addWidget(det, 1)
        return pag

    # ---------- historial ----------
    def refrescar_historial(self, automatico=False):
        """Llena la lista del historial.

        `automatico=True` es para el refresco de fondo: si la lista quedó igual, no
        la vuelve a dibujar (así no parpadea mientras se trabaja).
        """
        texto = (self.txt_buscar.text() or "").strip().upper()
        prov = self.cb_prov_hist.currentText()
        est = self.cb_est_hist.currentText()
        try:
            conteo = db.conteo_ajustes()      # una sola consulta para todos
            resumen = db.resumen_viaticos()
        except Exception as ex:
            if not automatico:
                C.error(self, "Actualizar historial",
                        "No se pudo leer la base de datos:\n\n%s" % ex)
            return
        filas = []
        for r in resumen:
            n = r["viatico_numero"]
            emps = r["empleados"] or ""
            lugares = r["lugares"] or ""
            if texto and not (texto in str(n) or texto in emps.upper()
                              or texto in lugares.upper()
                              or texto in (r["responsable"] or "").upper()
                              or texto in (r["cliente_proyecto"] or "").upper()):
                continue
            if prov != "Todas" and prov not in lugares:
                continue
            if est != "Todos" and r["estado"] != est:
                continue
            filas.append({"crudo": str(n), "numero": db.numero_visible(n),
                          "salida": fmt_f(r["fecha_salida"]),
                          "regreso": fmt_f(r["fecha_regreso"]),
                          "responsable": r["responsable"] or "",
                          "empleados": emps, "lugar": lugares,
                          "ajustes": conteo.get(n, 0), "total": fmt(r["total"]),
                          "cajero": fmt(r["valor_cajero"]), "estado": r["estado"]})
        firma = tuple((f["crudo"], f["estado"], f["empleados"], f["total"]) for f in filas)
        if automatico and firma == self._hist_firma:
            return                             # no cambió nada: no se redibuja
        self._hist_firma = firma
        self.tabla_hist.poner(filas)
        if filas:
            self.tabla_hist.seleccionar_donde("crudo", filas[0]["crudo"])
            self._ver_detalle()

    def _numero_seleccionado(self):
        fila = self.tabla_hist.seleccion()
        if not fila:
            return None
        try:
            return int(str(fila.get("crudo")))
        except (TypeError, ValueError):
            return None

    def _poner_ajustes(self, numero):
        """Llena la lista de ajustes que se pueden imprimir, exportar o editar."""
        self.cb_ajuste.blockSignals(True)
        self.cb_ajuste.clear()
        self.cb_ajuste.addItem("—")
        for a in (db.ajustes_viaje(numero) if numero else []):
            self.cb_ajuste.addItem(str(a["ajuste_numero"]))
        self.cb_ajuste.setCurrentIndex(0)
        self.cb_ajuste.blockSignals(False)
        return self.cb_ajuste

    def _ajuste_elegido(self, n, titulo, verbo):
        """Ajuste elegido en la lista del historial (si no hay, se pregunta cuál)."""
        ajustes = db.ajustes_viaje(n)
        if not ajustes:
            C.aviso(self, titulo, "Este viático no tiene ajustes.")
            return None
        numeros = [int(a["ajuste_numero"]) for a in ajustes]
        texto = (self.cb_ajuste.currentText() or "").strip()
        if texto.isdigit() and int(texto) in numeros:
            return int(texto)
        opciones = "\n".join(
            "Ajuste %s: %s - %s" % (a["ajuste_numero"], fmt_f(a["fecha_salida"]),
                                    fmt_f(a["fecha_regreso"])) for a in ajustes)
        elegido = C.preguntar_valor(self, titulo,
                                    "Número de ajuste a %s:\n\n%s" % (verbo, opciones),
                                    valor=ajustes[0]["ajuste_numero"], decimales=0)
        return None if elegido is None else int(elegido)

    def _ver_detalle(self):
        """Muestra el detalle completo del viático elegido (original y ajustes)."""
        self.tabla_det.limpiar()
        n = self._numero_seleccionado()
        self._poner_ajustes(n)
        if n is None:
            return
        salida = []
        grupos = {}
        for fila in db.filas_numero(n):
            grupos.setdefault(int(fila.get("ajuste_numero") or 0), []).append(fila)
        i = 0
        for ajuste in sorted(grupos):
            salida.append(sep_vals("═ ORIGINAL ═" if ajuste == 0
                                   else "═ AJUSTE N° %s · NUEVO ═" % ajuste))
            for fila in grupos[ajuste]:
                i += 1
                salida.append(vals_fila(i, fila))
        if grupos:
            todas = [f for g in grupos.values() for f in g]
            salida.append(vals_totales(todas))
        self.tabla_det.poner(salida)
        for pos, fila in enumerate(salida):
            if str(fila.get("empleado", "")).startswith("═"):
                _pintar(self.tabla_det, [pos], FONDO_SEP)
            elif fila.get("empleado") == "TOTALES":
                _pintar(self.tabla_det, [pos], FONDO_TOTAL)

    # ---------- exportar a Excel cada viático (igual que se imprime) ----------
    def _cabecera_viatico(self, numero, cab, filas, r0):
        """Datos de la cabecera, como en el viático impreso."""
        encargado = next((f["nombre_empleado"] for f in filas if f.get("es_encargado")), "—")
        chofer = next((f["nombre_empleado"] for f in filas if f.get("es_chofer")), "—")
        recibos = " / ".join([x for x in (cab.get("recibo_viatico"),
                                          cab.get("recibo_viatico_2"),
                                          cab.get("recibo_viatico_3")) if x]) or "—"
        return [
            ("Viático N°", db.numero_visible(numero)),
            ("Estado", r0.get("estado") or "—"),
            ("Creado por", cab.get("responsable") or "—"),
            ("Cliente y proyecto", cab.get("cliente_proyecto") or "—"),
            ("Encargado", encargado),
            ("Chofer", chofer),
            ("Lugar de trabajo", r0.get("lugar_trabajo") or "—"),
            ("Provincia / cantón", "%s / %s" % (r0.get("provincia") or "—",
                                                r0.get("canton") or "—")),
            ("Vehículo", cab.get("placa") or "—"),
            ("Orden combustible 1", cab.get("orden_combustible") or "—"),
            ("Orden combustible 2", cab.get("orden_combustible_2") or "—"),
            ("Efectivo combustible", fmt(cab.get("efectivo_combustible"))),
            ("Km recorridos", r0.get("km_recorridos") or 0),
            ("Parqueadero / peaje", fmt(r0.get("parqueadero_peaje"))),
            ("Recibos", recibos),
            ("Salida Miempresa", "%s %s" % (fmt_f(r0.get("fecha_salida")),
                                             r0.get("hora_salida") or "")),
            ("Regreso Miempresa", "%s %s" % (fmt_f(r0.get("fecha_regreso")),
                                              r0.get("hora_regreso") or "")),
            ("Llegada al trabajo", "%s %s" % (fmt_f(r0.get("fecha_llegada_trabajo")),
                                              r0.get("hora_llegada_trabajo") or "")),
            ("Salida del trabajo", "%s %s" % (fmt_f(r0.get("fecha_salida_trabajo")),
                                              r0.get("hora_salida_trabajo") or "")),
            ("Observaciones", cab.get("observaciones") or "—"),
            ("Justificado por", r0.get("justificado_por") or "—"),
            ("Nota de cierre", r0.get("nota_justificacion") or "—"),
        ]

    def _guardar_excel_viatico(self, numero, cab, filas, titulo, nombre):
        """Arma el Excel de un viático: cabecera + detalle + totales."""
        if not filas:
            C.aviso(self, "Exportar", "No hay datos para exportar.")
            return None
        ruta = C.pedir_ruta_guardar(self, nombre)
        if not ruta:
            return None
        bloques = [("titulo", titulo),
                   ("datos", self._cabecera_viatico(numero, cab, filas, filas[0])),
                   ("salto",),
                   ("tabla", COLS_DETALLE,
                    [vals_fila(i, f) for i, f in enumerate(filas, 1)]),
                   ("totales", COLS_DETALLE, [vals_totales(filas)])]
        try:
            C.exportar_excel_documento(ruta, bloques,
                                       "Viático %s" % db.numero_visible(numero))
        except Exception as ex:
            C.error(self, "Exportar a Excel", str(ex))
            return None
        C.informar(self, "Exportar a Excel",
                   "Se guardó el archivo:\n%s\n\nViático N° %s · %d persona(s)."
                   % (ruta, db.numero_visible(numero), len(filas)))
        return ruta

    def exportar_excel_general(self):
        """Excel del viático elegido con su original y todos sus ajustes."""
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Exportar", "Seleccione un viático del historial.")
            return None
        filas = db.filas_numero(n)
        if not filas:
            return None
        return self._guardar_excel_viatico(
            n, self._cab_desde_fila(filas[0]), filas,
            "VIÁTICO N° %s — ORIGINAL Y AJUSTES" % db.numero_visible(n),
            "viatico_%s.xlsx" % db.numero_visible(n))

    def exportar_excel_original(self):
        """Excel del viático original (solo el original)."""
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Exportar", "Seleccione un viático del historial.")
            return None
        filas = db.filas_originales(n)
        if not filas:
            C.aviso(self, "Exportar", "No existe el viático original.")
            return None
        return self._guardar_excel_viatico(
            n, self._cab_desde_fila(filas[0]), filas,
            "VIÁTICO N° %s — ORIGINAL" % db.numero_visible(n),
            "viatico_%s_original.xlsx" % db.numero_visible(n))

    def exportar_excel_ajuste(self):
        """Excel de un ajuste del viático elegido (el que esté marcado en la lista)."""
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Exportar", "Seleccione un viático del historial.")
            return None
        ajuste = self._ajuste_elegido(n, "Exportar ajuste", "exportar")
        if ajuste is None:
            return None
        filas = db.filas_numero(n, ajuste)
        if not filas:
            C.aviso(self, "Exportar", "No existe ese ajuste.")
            return None
        return self._guardar_excel_viatico(
            n, self._cab_desde_fila(filas[0]), filas,
            "VIÁTICO N° %s — AJUSTE N° %s" % (db.numero_visible(n), ajuste),
            "viatico_%s_ajuste_%s.xlsx" % (db.numero_visible(n), ajuste))

    def exportar_excel_formulario(self):
        """Excel de lo que está en pantalla (el viático nuevo o en edición)."""
        filas = self._construir_filas(avisar=True)
        if not filas:
            return None
        numero = self.edit_numero or db.proximo_numero()
        if self.edit_numero and self.edit_ajuste_numero:
            titulo = "VIÁTICO N° %s — AJUSTE N° %s" % (db.numero_visible(numero),
                                                       self.edit_ajuste_numero)
            nombre = "viatico_%s_ajuste_%s.xlsx" % (db.numero_visible(numero),
                                                    self.edit_ajuste_numero)
        else:
            titulo = "VIÁTICO N° %s — ORIGINAL" % db.numero_visible(numero)
            nombre = "viatico_%s.xlsx" % db.numero_visible(numero)
        return self._guardar_excel_viatico(numero, self._cab(), filas, titulo, nombre)

    # ---------- cargar un viático en el formulario ----------
    def _cargar_formulario(self, filas, numero, ajuste_numero=None):
        """Carga un viático guardado en el formulario.

        Mientras se cargan los campos **no se recalcula nada**: las horas que quedan
        son las que se registraron y se guardaron (si no, al abrir un viático viejo el
        sistema le cambiaría las horas con el estimado).
        """
        self._calculando = True
        try:
            return self._cargar_formulario_datos(filas, numero, ajuste_numero)
        finally:
            self._calculando = False

    def _cargar_formulario_datos(self, filas, numero, ajuste_numero=None):
        if not filas:
            return False
        # La fila del encargado trae los datos generales (fechas, lugar, cabecera): se
        # busca por su marca y no por la posición, para no depender del orden guardado.
        r0 = next((x for x in filas if x.get("es_encargado")), filas[0])
        # El km y el parqueadero/peaje van en la fila del que recibe el efectivo (el
        # chofer), que puede no ser el encargado (ver `_fila_de_los_gastos`).
        r_gastos = _fila_de_los_gastos(filas, r0)
        # Cuando se empieza un ajuste nuevo los datos vienen del ORIGINAL: el
        # combustible, el peaje y otros del original ya se entregaron antes, así que
        # el ajuste arranca en cero y se registran solo los valores nuevos.
        nuevo_ajuste = bool(ajuste_numero) and int(r0.get("ajuste_numero") or 0) == 0
        # En un ajuste interesa el km del viaje original para sugerir el combustible.
        self._km_orig_ajuste = 0.0
        if ajuste_numero:
            originales = db.filas_originales(numero) or filas
            self._km_orig_ajuste = max(
                [float(x.get("km_recorridos") or 0) for x in originales] or [0.0])
        self.cb_responsable.set_valor(r0["responsable"] or "")
        self.cb_cliente.set_valor(r0["cliente_proyecto"] or "")
        self.txt_ord1.setText(r0["orden_combustible"] or "")
        self.txt_ord2.setText(r0.get("orden_combustible_2") or "")
        self.txt_efectivo.setText("0" if nuevo_ajuste
                                  else str(r0.get("efectivo_combustible") or 0))
        self.cb_vehiculo.set_valor(r0["placa"] or "")
        self.txt_obs.setText(r0["observaciones"] or "")
        self.txt_recibo.setText(r0.get("recibo_viatico") or "")
        self.txt_recibo2.setText(r0.get("recibo_viatico_2") or "")
        self.txt_recibo3.setText(r0.get("recibo_viatico_3") or "")
        encargado = next((x["nombre_empleado"] for x in filas if x.get("es_encargado")),
                         r0["nombre_empleado"])
        self.cb_encargado.set_valor(encargado)
        prov = (r0.get("provincia") or "").strip().upper()
        cant = (r0.get("canton") or "").strip().upper()
        if prov:
            self.cb_provincia.set_valor(prov)
            self.cb_canton.refrescar_opciones()
        if cant:
            self.cb_canton.set_valor(cant)
        self.txt_lugar.setText(r0["lugar_trabajo"] or "")
        self.txt_km.setText(str(r_gastos.get("km_recorridos") or 0))
        self.txt_peaje.setText("0" if nuevo_ajuste
                               else str(r_gastos.get("parqueadero_peaje") or 0))
        self.txt_otros.setText("0" if nuevo_ajuste else str(r0["otros"] or 0))
        self.pasajeros = [{
            "nombre": x["nombre_empleado"],
            "medio": x.get("medio_transporte") or "AUTO",
            "extra": (x.get("extra_transporte")
                      if x.get("extra_transporte") is not None
                      else (x.get("otros") or 0)),
            # El horario propio de cada viajero (si lo tiene) se conserva al editar.
            "horario": _horario_de_fila(x, r0),
        } for x in filas if x["nombre_empleado"] != encargado]
        chofer_row = next((x for x in filas if x.get("es_chofer")), None)
        self._refrescar_pas()
        self._refrescar_chofer()
        self.cb_chofer.set_valor(chofer_row["nombre_empleado"] if chofer_row else "")
        self._actualizar_medio()
        for campo, clave in ((self.cal_salida, "fecha_salida"),
                             (self.cal_regreso, "fecha_regreso"),
                             (self.cal_lleg, "fecha_llegada_trabajo"),
                             (self.cal_saltr, "fecha_salida_trabajo")):
            if r0.get(clave):
                campo.set_valor(r0[clave])
        for campo, clave in ((self.cb_hsalida, "hora_salida"),
                             (self.cb_hregreso, "hora_regreso"),
                             (self.cb_hlleg, "hora_llegada_trabajo"),
                             (self.cb_hsaltr, "hora_salida_trabajo")):
            if r0.get(clave):
                campo.set_valor(r0[clave])
        self.edit_numero = numero
        self.edit_ajuste_numero = ajuste_numero
        self._actualizar_numero()
        self._bloquear_salida(ajuste_numero is not None)
        self._refrescar_prev()
        self.pestanas.setCurrentIndex(0)
        self._recordar_base()            # así, cerrar sin tocar nada no deja borrador
        return True

    def _bloquear_salida(self, bloquear):
        """En modo ajuste la salida queda deshabilitada (ya se entregó el original)."""
        self._salida_bloqueada = bool(bloquear)
        self.cal_salida.setEnabled(not bloquear)
        self.cb_hsalida.setEnabled(not bloquear)

    # ---------- acciones del historial ----------
    def ver_justificado_seleccionado(self):
        """Abre la pantalla de justificación con el viático seleccionado cargado."""
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Ver justificado", "Seleccione un viático de la lista.")
            return
        if not db.filas_numero(n):
            C.aviso(self, "Ver justificado",
                    "No se encontró el viático N° %s." % db.etiqueta_numero(n))
            return
        from q_ajustes import AjustesWindow
        AjustesWindow(self, self.usuario, numero=n).exec()

    def editar_seleccionado(self):
        n = self._numero_seleccionado()
        if n is None:
            return
        filas = db.filas_originales(n)
        if filas and filas[0]["estado"] != "PENDIENTE":
            C.aviso(self, "Editar", "Solo se editan viáticos PENDIENTES.")
            return
        self._cargar_formulario(filas, n, None)

    def ajustar_seleccionado(self):
        n = self._numero_seleccionado()
        if n is None:
            return
        filas = db.filas_originales(n)
        if filas and filas[0]["estado"] != "PENDIENTE":
            C.aviso(self, "Ajustar",
                    "Solo se pueden agregar ajustes a viáticos PENDIENTES.")
            return
        if not self._cargar_formulario(filas, n, db.proximo_ajuste(n)):
            return

    def editar_ajuste_seleccionado(self):
        n = self._numero_seleccionado()
        if n is None:
            return
        ajuste = self._ajuste_elegido(n, "Editar ajuste", "editar")
        if ajuste is None:
            return
        filas = db.filas_numero(n, ajuste)
        if filas and filas[0]["estado"] != "PENDIENTE":
            C.aviso(self, "Editar", "Solo se editan viáticos PENDIENTES.")
            return
        self._cargar_formulario(filas, n, ajuste)

    def anular_seleccionado(self):
        n = self._numero_seleccionado()
        if n is None:
            return
        if not C.confirmar_peligro(
                self, "Anular",
                "¿Anular completo el viático N° %s, incluidos sus ajustes?"
                % db.etiqueta_numero(n), si="Sí, anular"):
            return
        db.anular_viaje(n)
        db.registrar_bitacora(self.usuario, "ANULÓ VIÁTICO", "viáticos",
                              "N° %s" % db.etiqueta_numero(n),
                              "Anulado con todos sus ajustes")
        self.refrescar_historial()
        self._ver_detalle()

    def _cab_desde_fila(self, r0):
        """Cabecera del viático tal como está guardado (para reimprimir)."""
        return {"responsable": r0["responsable"], "cliente_proyecto": r0["cliente_proyecto"],
                "orden_combustible": r0["orden_combustible"] or "",
                "orden_combustible_2": r0.get("orden_combustible_2") or "",
                "efectivo_combustible": r0.get("efectivo_combustible") or 0,
                "placa": r0["placa"] or "", "observaciones": r0["observaciones"] or "",
                "recibo_viatico": r0.get("recibo_viatico") or "",
                "recibo_viatico_2": r0.get("recibo_viatico_2") or "",
                "recibo_viatico_3": r0.get("recibo_viatico_3") or ""}

    def imprimir_hist_original(self):
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Imprimir", "Seleccione un viático del historial.")
            return
        filas = db.filas_originales(n)
        if not filas:
            C.aviso(self, "Imprimir", "No existe el viático original.")
            return
        reportes.imprimir_viatico(n, self._cab_desde_fila(filas[0]), filas)

    def imprimir_hist_ajuste(self):
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Imprimir", "Seleccione un viático del historial.")
            return
        ajuste = self._ajuste_elegido(n, "Imprimir ajuste", "imprimir")
        if ajuste is None:
            return
        filas = db.filas_numero(n, ajuste)
        if not filas:
            C.aviso(self, "Imprimir", "No existe ese ajuste.")
            return
        reportes.imprimir_viatico(n, self._cab_desde_fila(filas[0]), filas)

    def imprimir_hist_general(self):
        n = self._numero_seleccionado()
        if n is None:
            C.aviso(self, "Imprimir", "Seleccione un viático del historial.")
            return
        filas = db.filas_numero(n)
        if not filas:
            return
        reportes.imprimir_viatico(n, self._cab_desde_fila(filas[0]), filas, general=True)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
