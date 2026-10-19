# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""viaticos_148_149.py — Carga los dos viáticos reales ya pagados (N° 148 y 149, semana
del 28/09 al 03/10 de 2026, personal en MACAS) en la base **local** del programa, revisa
que el programa pague exactamente lo mismo que el Excel de la empresa y guarda los PDF.

Qué hace, paso por paso:

1. Copia de seguridad de `sistema_viaticos_miempresa\\data\\viaticos.db` (una por día).
2. Agrega a la lista de empleados los viajeros que falten.
3. Crea (o vuelve a crear) el viático N° 148 y el N° 149 del año 2026 con los datos del
   Excel real: 3 personas a MACAS en el **ABL-3969** y 2 personas en el **ABI-3147**.
   Las filas se arman con las MISMAS reglas de la pantalla de viáticos
   (`q_viaje._construir_filas` + `calculos.calcular`), así que el resultado es el que
   daría el programa al digitar el viático a mano.
4. Compara concepto por concepto lo que paga el programa con lo que ya se pagó según el
   Excel (`ESPERADO`) y deja el informe en
   `documentacion\\VIATICOS_148_149_VERIFICACION.md`.
5. Guarda los PDF en `PDF_VIATICOS_148_149\\`:

     - `viatico_148-2026.pdf`  → el del **programa** (el mismo de 🖨 IMPRIMIR / PDF).
     - `viatico_148-2026_formato_empresa.pdf` → copia del **formato del Excel de la
       empresa** armada con los mismos datos (la arma este informe, no el programa),
       para comparar los dos documentos lado a lado.

Uso:

    python herramientas\\viaticos_148_149.py
    python herramientas\\viaticos_148_149.py --sin-guardar     (solo calcula y compara)

Los PDF se generan con Microsoft Edge (o Google Chrome) en modo invisible, sin abrir
ninguna ventana: es el mismo motor del navegador con el que el sistema imprime.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, time
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
_SISTEMA = _RAIZ / "sistema_viaticos_miempresa"

# La base de este trabajo es la LOCAL (SQLite). Se fuerza por variable de entorno para
# que, aunque `config.json` apunte al servidor, este informe NUNCA escriba en la base
# central.
os.environ["VIATICOS_MOTOR"] = "sqlite"
sys.path.insert(0, str(_SISTEMA))

ANIO = 2026
LUGAR = "MACAS, MORONA SANTIAGO"
PROVINCIA = "MORONA SANTIAGO"
CANTON = "MACAS"
CARPETA_PDF = _RAIZ / "PDF_VIATICOS_148_149"
INFORME = _RAIZ / "documentacion" / "VIATICOS_148_149_VERIFICACION.md"

# Los dos tramos del viaje (las fechas del Excel). Con 4 días de diferencia el programa
# saca los 5 días y las 4 noches que el Excel pagó (116 por persona sin combustible).
TRAMO_ENCARGADO = {"salida": "2026-09-28", "h_salida": "04:00",
                   "llegada": "2026-09-28", "h_llegada": "11:00",
                   "salida_trabajo": "2026-10-02", "h_salida_trabajo": "14:00",
                   "regreso": "2026-10-02", "h_regreso": "21:00"}
TRAMO_ACOMPANANTE = {"salida": "2026-09-29", "h_salida": "04:00",
                     "llegada": "2026-09-29", "h_llegada": "11:00",
                     "salida_trabajo": "2026-10-03", "h_salida_trabajo": "14:00",
                     "regreso": "2026-10-03", "h_regreso": "21:00"}

# Los dos viáticos, tal como quedaron en el Excel de la empresa (lo ya pagado).
VIATICOS = [
    {
        "numero": 148,
        "cab": {"responsable": "PEREZ SINCHI EDISSON PAUL",
                "cliente_proyecto": "LA MERCED",
                "orden_combustible": "2",
                "placa": "ABL-3969",
                "observaciones": "BRANDING DE FACHADA",
                "recibo_viatico": "", "recibo_viatico_2": "", "recibo_viatico_3": ""},
        "personas": [
            {"nombre": "PEREZ SINCHI EDISSON PAUL", "encargado": 1, "chofer": 1,
             "tramo": TRAMO_ENCARGADO, "km": 230, "peaje": 9.50, "efectivo": 57.50},
            {"nombre": "HERNANDEZ REGALADO BRANDON JESUS", "tramo": TRAMO_ACOMPANANTE},
            {"nombre": "YOHANDER HERNANDEZ", "tramo": TRAMO_ACOMPANANTE},
        ],
        # Lo que dice el Excel ya pagado (fila por fila).
        "esperado": [
            {"dias": 5, "km": 230, "des": 15, "alm": 15, "mer": 15, "txs": 3, "txr": 3,
             "hos": 60, "agua": 5, "comb": 57.50, "tra": 0, "peaje": 9.50, "total": 183.00},
            {"dias": 5, "km": 0, "des": 15, "alm": 15, "mer": 15, "txs": 3, "txr": 3,
             "hos": 60, "agua": 5, "comb": 0, "tra": 0, "peaje": 0, "total": 116.00},
            {"dias": 5, "km": 0, "des": 15, "alm": 15, "mer": 15, "txs": 3, "txr": 3,
             "hos": 60, "agua": 5, "comb": 0, "tra": 0, "peaje": 0, "total": 116.00},
        ],
        "esperado_totales": {"des": 45, "alm": 45, "mer": 45, "txs": 9, "txr": 9,
                             "hos": 180, "agua": 15, "comb": 57.50, "tra": 0,
                             "peaje": 9.50, "total": 415.00},
    },
    {
        "numero": 149,
        "cab": {"responsable": "NARVAEZ ORTEGA ELVIS ALEXANDER",
                "cliente_proyecto": "LA MERCED",
                "orden_combustible": "2",
                "placa": "ABI-3147",
                "observaciones": "BRANDING DE FACHADA",
                "recibo_viatico": "", "recibo_viatico_2": "", "recibo_viatico_3": ""},
        "personas": [
            {"nombre": "NARVAEZ ORTEGA ELVIS ALEXANDER", "encargado": 1, "chofer": 1,
             "tramo": TRAMO_ENCARGADO, "km": 230, "peaje": 10.50, "efectivo": 57.50},
            {"nombre": "DAVID YANEZ", "tramo": TRAMO_ACOMPANANTE},
        ],
        "esperado": [
            {"dias": 5, "km": 230, "des": 15, "alm": 15, "mer": 15, "txs": 3, "txr": 3,
             "hos": 60, "agua": 5, "comb": 57.50, "tra": 0, "peaje": 10.50, "total": 184.00},
            {"dias": 5, "km": 0, "des": 15, "alm": 15, "mer": 15, "txs": 3, "txr": 3,
             "hos": 60, "agua": 5, "comb": 0, "tra": 0, "peaje": 0, "total": 116.00},
        ],
        "esperado_totales": {"des": 30, "alm": 30, "mer": 30, "txs": 6, "txr": 6,
                             "hos": 120, "agua": 10, "comb": 57.50, "tra": 0,
                             "peaje": 10.50, "total": 300.00},
    },
]


# --------------------------------------------------------------------- utilidades
def fmt(v):
    """Igual que `reportes.fmt`: «-» cuando el valor es cero."""
    v = float(v or 0)
    return "-" if abs(v) < 0.005 else "%.2f" % v


def fmt_f(iso):
    """Fecha como se ve en el sistema: 28/09/2026."""
    if not iso:
        return ""
    y, m, d = str(iso).split("-")
    return "%s/%s/%s" % (d, m, y)


def _fecha(texto):
    """Fecha ISO de un texto «AAAA-MM-DD»."""
    return date.fromisoformat(str(texto))


def _hora(texto):
    """Hora de un texto «HH:MM»."""
    hh, mm = str(texto).split(":")[:2]
    return time(int(hh), int(mm))


def respaldar_base():
    """Copia la base local antes de escribir en ella (una por día)."""
    import configuracion as cfg
    destino = cfg.dir_datos() / "viaticos.db"
    if not destino.exists():
        return None
    copia = destino.with_name("viaticos.db.bak_%s" % date.today().strftime("%Y%m%d"))
    if copia.exists():
        return copia
    shutil.copy2(destino, copia)
    return copia


# ------------------------------------------------------------------- viáticos
def fila_de_persona(persona, cab, p, efectivo):
    """Fila de un viajero, con las mismas reglas de la pantalla de viáticos.

    Es el equivalente a `q_viaje._construir_filas`: el combustible, el parqueadero/peaje
    y los km van SOLO en la fila del chofer (los acompañantes no reciben combustible) y
    el resto de los valores sale de `calculos.calcular` con los parámetros de la base.
    """
    import calculos as CAL
    t = persona["tramo"]
    es_encargado = 1 if persona.get("encargado") else 0
    es_chofer = 1 if persona.get("chofer") else 0
    km = float(persona.get("km") or 0) if es_chofer else 0.0
    peaje = float(persona.get("peaje") or 0) if es_chofer else 0.0
    plata = float(persona.get("efectivo") or 0) if es_chofer else 0.0
    v = CAL.DatosViaje(nombre_empleado=persona["nombre"], lugar_trabajo=LUGAR,
                       fecha_salida=_fecha(t["salida"]), hora_salida=_hora(t["h_salida"]),
                       fecha_regreso=_fecha(t["regreso"]),
                       hora_regreso=_hora(t["h_regreso"]),
                       fecha_llegada_trabajo=_fecha(t["llegada"]),
                       hora_llegada_trabajo=_hora(t["h_llegada"]),
                       fecha_salida_trabajo=_fecha(t["salida_trabajo"]),
                       hora_salida_trabajo=_hora(t["h_salida_trabajo"]),
                       km_recorridos=km, parqueadero_peaje=peaje, otros=0.0,
                       combustible_efectivo=plata)
    reg = CAL.calcular(v, p)
    # `base` es igual para todas las filas (como en la pantalla: el efectivo de
    # combustible del formulario queda guardado en cada fila).
    base = {"lugar_trabajo": LUGAR, "provincia": PROVINCIA, "canton": CANTON,
            "orden_combustible_2": "", "efectivo_combustible": efectivo,
            "ajuste_numero": 0,
            "fecha_salida": t["salida"], "hora_salida": t["h_salida"],
            "fecha_regreso": t["regreso"], "hora_regreso": t["h_regreso"],
            "fecha_llegada_trabajo": t["llegada"],
            "hora_llegada_trabajo": t["h_llegada"],
            "fecha_salida_trabajo": t["salida_trabajo"],
            "hora_salida_trabajo": t["h_salida_trabajo"]}
    return {**base, "nombre_empleado": persona["nombre"], "es_encargado": es_encargado,
            "es_chofer": es_chofer, "medio_transporte": "AUTO", "extra_transporte": 0.0,
            "km_recorridos": km, "parqueadero_peaje": peaje, "otros": 0.0, **reg}


def filas_del_viatico(datos, p):
    """Todas las filas del viático (encargado y acompañantes)."""
    import calculos as CAL
    efectivo = max([float(x.get("efectivo") or 0) for x in datos["personas"]] or [0.0])
    filas = [fila_de_persona(x, datos["cab"], p, efectivo) for x in datos["personas"]]
    # El cajero es UNO solo por viático y se redondea sobre el TOTAL (versión 7.0): el retiro
    # lo hace una sola persona (el encargado) y lleva el dinero de todo el grupo, así que el
    # valor queda en su fila y las demás van en cero. Antes se redondeaba la cuenta de cada
    # viajero y la suma salía más alta que el total (185 + 120 + 120 = 425 con total de 415).
    CAL.cajero_del_grupo(filas, p)
    return filas


def guardar_viatico(datos, filas):
    """Crea (o vuelve a crear) el viático en la base local. Devuelve la clave interna."""
    import database as db
    numero = db.clave_viatico(ANIO, datos["numero"])
    cab = dict(datos["cab"])
    cab["efectivo_combustible"] = max([float(f.get("efectivo_combustible") or 0)
                                       for f in filas] or [0.0])
    # Se borra y se vuelve a escribir el ORIGINAL (si ya existía) sin tocarle el estado
    # ni la justificación: así el informe se puede volver a correr cuantas veces haga falta.
    db.actualizar_viaje(numero, cab, filas)
    for persona in datos["personas"]:
        db.agregar_empleado(persona["nombre"])
    try:
        db.registrar_bitacora(
            cab.get("responsable") or "ADMINISTRACIÓN", "CREÓ VIÁTICO", "viáticos",
            "N° %s" % db.etiqueta_numero(numero),
            "Cargado desde el Excel real ya pagado · %s · %d persona(s) · total $%.2f"
            % (LUGAR, len(filas), sum(float(f.get("total") or 0) for f in filas)))
    except Exception as ex:                        # la bitácora nunca interrumpe
        print("   (aviso: no se pudo escribir en la bitácora: %s)" % ex)
    return numero


def subir_secuencia(ultimo):
    """Deja el contador del año en el último número usado (así el próximo es 150)."""
    import database as db
    with db.conectar() as c:
        c.execute("UPDATE seq SET valor=? WHERE nombre=? AND valor<?",
                  (ultimo, "viatico_%d" % ANIO, ultimo))


# ------------------------------------------------- formato del Excel de la empresa
COLS_EMPRESA = ("N°", "Nombre del Empleado", "Lugar de Trabajo",
                "Fecha Salida de Miempresa", "Hora Salida del Viaje",
                "Fecha Regreso a Miempresa", "Hora Regreso del Viaje",
                "Fecha Llegada al Lugar de Trabajo", "Hora Llegada al Lugar de Trabajo",
                "Fecha Salida del Trabajo", "Hora Salida del Trabajo", "Días de Viaje",
                "Km Recorridos", "Desayuno", "Almuerzo", "Merienda", "Taxi Salida",
                "Taxi Regreso", "Hospedaje", "Agua", "Combustible", "Transporte",
                "Parqueadero/Peaje", "TOTAL VIÁTICOS", "VALOR A RETIRAR EN CAJERO")

NOTA_EMPRESA = ("Celdas en AZUL: llenar por el usuario. Celdas en NEGRO: se calculan "
                "solas. Ajuste tarifas y horarios en «Parámetros». Seleccione empleados "
                "desde la lista desplegable (editable en «Lista de Empleados»). Si viajan "
                "varias personas, use una fila por cada una. La columna verde «VALOR A "
                "RETIRAR EN CAJERO» redondea el total hacia arriba a valores cerrados.")

CAMPOS_TOT = (("des", "desayuno"), ("alm", "almuerzo"), ("mer", "merienda"),
              ("txs", "taxi_salida"), ("txr", "taxi_regreso"), ("hos", "hospedaje"),
              ("agua", "agua"), ("comb", "combustible"), ("tra", "otros"),
              ("peaje", "parqueadero_peaje"), ("total", "total"),
              ("cajero", "valor_cajero"))


def _html_formato_empresa(numero, datos, filas):
    """Documento HTML con el MISMO formato del Excel de la empresa.

    Este documento NO lo genera el sistema: lo arma el informe con los mismos datos del
    viático para poder mirar lado a lado el PDF del programa y el formato de la empresa.
    """
    import database as db
    cab = datos["cab"]
    vehiculo = db.buscar_vehiculo_por_placa(cab.get("placa", "")) or {}
    totales = {c: 0.0 for c, _ in CAMPOS_TOT}
    celdas = []
    for i, f in enumerate(filas, 1):
        for clave, campo in CAMPOS_TOT:
            totales[clave] += float(f.get(campo) or 0)
        celdas.append(
            "<tr><td class='c'>{n}</td><td>{emp}</td><td class='c'>{lug}</td>"
            "<td class='c'>{fs}</td><td class='c'>{hs}</td><td class='c'>{fr}</td>"
            "<td class='c'>{hr}</td><td class='c'>{fl}</td><td class='c'>{hl}</td>"
            "<td class='c'>{ft}</td><td class='c'>{ht}</td><td class='c azul'>{dias}</td>"
            "<td class='c'>{km}</td><td class='r'>{des}</td><td class='r'>{alm}</td>"
            "<td class='r'>{mer}</td><td class='r'>{txs}</td><td class='r'>{txr}</td>"
            "<td class='r'>{hos}</td><td class='r'>{agua}</td><td class='r'>{comb}</td>"
            "<td class='r'>{tra}</td><td class='r'>{peaje}</td>"
            "<td class='r negrita'>{total}</td><td class='r verde negrita'>{cajero}</td>"
            "</tr>".format(
                n=i, emp=f.get("nombre_empleado", ""), lug=f.get("lugar_trabajo", ""),
                fs=fmt_f(f.get("fecha_salida")), hs=f.get("hora_salida", ""),
                fr=fmt_f(f.get("fecha_regreso")), hr=f.get("hora_regreso", ""),
                fl=fmt_f(f.get("fecha_llegada_trabajo")),
                hl=f.get("hora_llegada_trabajo", ""),
                ft=fmt_f(f.get("fecha_salida_trabajo")),
                ht=f.get("hora_salida_trabajo", ""),
                dias=f.get("dias_viaje", ""),
                km=int(float(f.get("km_recorridos") or 0)),
                des=fmt(f.get("desayuno")), alm=fmt(f.get("almuerzo")),
                mer=fmt(f.get("merienda")), txs=fmt(f.get("taxi_salida")),
                txr=fmt(f.get("taxi_regreso")), hos=fmt(f.get("hospedaje")),
                agua=fmt(f.get("agua")), comb=fmt(f.get("combustible")),
                tra=fmt(f.get("otros")), peaje=fmt(f.get("parqueadero_peaje")),
                total=fmt(f.get("total")), cajero=fmt(f.get("valor_cajero"))))
    km_total = sum(int(float(f.get("km_recorridos") or 0)) for f in filas)
    return _PLANTILLA_EMPRESA % (db.numero_visible(numero), NOTA_EMPRESA,
                                 cab.get("responsable", ""), cab.get("placa", ""),
                                 cab.get("orden_combustible", "") or "-",
                                 db.numero_visible(numero), cab.get("cliente_proyecto", ""),
                                 vehiculo.get("tipo", ""), cab.get("observaciones", ""),
                                 "".join("<th>%s</th>" % c for c in COLS_EMPRESA),
                                 "".join(celdas) + _fila_totales(km_total, totales))


def _fila_totales(km_total, totales):
    """Fila TOTALES del formato de la empresa (mismo orden de columnas)."""
    return ("<tr class='tot'><td></td><td>TOTALES</td><td></td><td></td><td></td>"
            "<td></td><td></td><td></td><td></td><td></td><td></td><td></td>"
            "<td class='c'>%d</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r'>%s</td></tr>"
            % (km_total, fmt(totales["des"]), fmt(totales["alm"]),
               fmt(totales["mer"]), fmt(totales["txs"]), fmt(totales["txr"]),
               fmt(totales["hos"]), fmt(totales["agua"]), fmt(totales["comb"]),
               fmt(totales["tra"]), fmt(totales["peaje"]), fmt(totales["total"]),
               fmt(totales["cajero"])))


_PLANTILLA_EMPRESA = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Viático %s — formato de la empresa</title><style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 9px; margin: 6px; }
  table { border-collapse: collapse; width: 100%%; }
  th, td { border: 1px solid #808080; padding: 2px 3px; }
  th { background: #1F4E79; color: #fff; font-size: 7.5px; text-align: center; }
  td { font-size: 8px; }
  .titulo { background: #1F4E79; color: #fff; font-weight: bold; font-size: 12px;
            text-align: center; padding: 4px; }
  .nota { font-style: italic; font-size: 7.5px; color: #1F4E79; background: #fff; }
  .lbl { background: #1F4E79; color: #fff; font-weight: bold; }
  .c { text-align: center; } .r { text-align: right; }
  .negrita { font-weight: bold; } .azul { background: #DDEBF7; }
  .verde { background: #C6EFCE; }
  .num { background: #FFF2CC; color: #C00000; font-size: 13px; font-weight: bold;
         text-align: center; }
  tr.tot td { background: #1F4E79; color: #fff; font-weight: bold; }
  .firmas { width: 100%%; margin-top: 30px; }
  .firmas td { border: none; text-align: center; font-size: 9px; }
  .linea { border-top: 1px solid #000; width: 45%%; margin: 0 auto 2px; }
</style></head><body>
<table>
  <tr><td class="titulo" colspan="25">REGISTRO DE VIÁTICOS - PERSONAL EN INSTALACIONES (CUENCA)</td></tr>
  <tr><td class="nota" colspan="25">%s</td></tr>
  <tr>
    <td class="lbl">RESPONSABLE DEL VIÁTICO:</td><td colspan="5" class="c">%s</td>
    <td class="lbl">PLACAS VEHÍCULO:</td><td colspan="2" class="c azul">%s</td>
    <td class="lbl">ORDEN DE COMBUSTIBLE:</td><td colspan="2" class="c azul">%s</td>
    <td colspan="8"></td>
    <td colspan="3" class="lbl c">VIÁTICO N°</td>
    <td colspan="3" class="num">%s</td>
  </tr>
  <tr>
    <td class="lbl">CLIENTE Y PROYECTO:</td><td colspan="5" class="c">%s</td>
    <td class="lbl">TIPO DE VEHÍCULO:</td><td colspan="4" class="c azul">%s</td>
    <td colspan="15"></td>
  </tr>
  <tr>
    <td class="lbl">OBSERVACIONES:</td><td colspan="24">%s</td>
  </tr>
  <tr>%s</tr>
  %s
</table>
<table class="firmas"><tr>
  <td><div class="linea"></div>Responsable</td>
  <td><div class="linea"></div>Autoriza</td>
</tr></table>
</body></html>"""


# ------------------------------------------------------------------------ PDF
def navegador():
    """Ruta de Microsoft Edge o de Google Chrome (para pasar el HTML a PDF)."""
    for ruta in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if os.path.exists(ruta):
            return ruta
    return None


def html_a_pdf(html, destino, horizontal=True):
    """Guarda un HTML como PDF, sin abrir ventanas (el navegador en modo invisible)."""
    exe = navegador()
    if not exe:
        raise RuntimeError("No se encontró Microsoft Edge ni Google Chrome para el PDF.")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if horizontal:
        # El informe del sistema tiene 25 columnas: se imprime apaisado, igual que lo
        # haría el usuario en el diálogo de impresión del navegador.
        html = html.replace("</style>",
                            "@page { size: A4 landscape; margin: 6mm; }\n</style>", 1)
    taller = Path(tempfile.gettempdir()) / "viaticos_pdf"
    taller.mkdir(parents=True, exist_ok=True)
    fuente = taller / (destino.stem + ".html")
    fuente.write_text(html, encoding="utf-8")
    comunes = [exe, "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--user-data-dir=%s" % (taller / "perfil")]
    for extra in (["--headless=new", "--no-pdf-header-footer"],
                  ["--headless", "--print-to-pdf-no-header"]):
        if destino.exists():
            destino.unlink()
        subprocess.run(comunes + extra + ["--print-to-pdf=%s" % destino, fuente.as_uri()],
                       capture_output=True, timeout=180)
        if destino.exists() and destino.stat().st_size > 800:
            return destino
    raise RuntimeError("El navegador no generó el PDF «%s»." % destino.name)


def html_del_programa(numero, cab, filas):
    """HTML del informe del programa: el MISMO de 🖨 IMPRIMIR / PDF.

    Se llama a `reportes.imprimir_viatico` (que es el que arma el informe y le pide al
    navegador que lo abra) y se intercepta esa apertura para quedarse con el HTML.
    """
    import reportes
    capturado = []
    original = reportes.webbrowser.open
    reportes.webbrowser.open = lambda url: capturado.append(url) or True
    try:
        reportes.imprimir_viatico(numero, cab, filas)
    finally:
        reportes.webbrowser.open = original
    if not capturado:
        raise RuntimeError("El informe del programa no devolvió el HTML.")
    archivo = capturado[0].replace("file:///", "").replace("file://", "")
    return Path(archivo).read_text(encoding="utf-8")


# ------------------------------------------------------------- comparación
CAMPOS_COMPARA = (("dias", "dias_viaje"), ("km", "km_recorridos"), ("des", "desayuno"),
                  ("alm", "almuerzo"), ("mer", "merienda"), ("txs", "taxi_salida"),
                  ("txr", "taxi_regreso"), ("hos", "hospedaje"), ("agua", "agua"),
                  ("comb", "combustible"), ("tra", "otros"),
                  ("peaje", "parqueadero_peaje"), ("total", "total"))

ROTULOS = {"dias": "Días de viaje", "km": "Km recorridos", "des": "Desayuno",
           "alm": "Almuerzo", "mer": "Merienda", "txs": "Taxi salida",
           "txr": "Taxi regreso", "hos": "Hospedaje", "agua": "Agua",
           "comb": "Combustible", "tra": "Transporte/otros", "peaje": "Parqueadero/peaje",
           "total": "TOTAL VIÁTICOS"}

# Días y km no llevan el signo de dólares.
SIN_PLATA = ("dias", "km")

# Columnas que el formato de la empresa NO totaliza (su fila TOTALES empieza en Desayuno).
NO_TOTALIZA = ("dias", "km")


def comparar(datos, filas):
    """Compara fila por fila lo que paga el programa con lo que ya se pagó (Excel).

    Devuelve (detalle por fila, totales, diferencias).
    """
    detalle, diferencias = [], []
    for i, (f, e) in enumerate(zip(filas, datos["esperado"]), 1):
        linea = {}
        for clave, campo in CAMPOS_COMPARA:
            programa = float(f.get(campo) or 0)
            excel = float(e.get(clave) or 0)
            linea[clave] = (programa, excel)
            if abs(programa - excel) > 0.005:
                diferencias.append("%s · fila %d: %s — programa %.2f, Excel %.2f"
                                   % (f.get("nombre_empleado"), i, ROTULOS[clave],
                                      programa, excel))
        detalle.append(linea)
    totales = {}
    for clave, campo in CAMPOS_COMPARA:
        programa = sum(float(f.get(campo) or 0) for f in filas)
        excel = float(datos["esperado_totales"].get(clave) or 0)
        totales[clave] = (programa, excel)
        # Los días y los km no se totalizan en el formato de la empresa: ahí no hay nada
        # que comparar (por eso la fila TOTALES del Excel arranca en Desayuno).
        if clave not in NO_TOTALIZA and abs(programa - excel) > 0.005:
            diferencias.append("TOTALES: %s — programa %.2f, Excel %.2f"
                               % (ROTULOS[clave], programa, excel))
    return detalle, totales, diferencias


def _txt(clave, valor):
    """Valor para el informe: los km y los días sin decimales y sin dólares."""
    if clave in SIN_PLATA:
        return "%.0f" % float(valor or 0)
    return "$%.2f" % float(valor or 0)


def _celda(clave, programa, excel):
    """Celda «programa / Excel», con un aviso cuando no coinciden."""
    aviso = "" if abs(float(programa) - float(excel)) < 0.005 else " ⚠"
    return "%s / %s%s" % (_txt(clave, programa), _txt(clave, excel), aviso)


# --------------------------------------------------------------------- informe
def informe(resultados, p, base, copia):
    """Escribe el informe de la verificación en Markdown."""
    L = []
    ap = L.append
    ap("# Viáticos reales N° 148 y 149 — el programa contra el Excel ya pagado")
    ap("")
    ap("Verificación hecha **en la base local** (sin tocar el servidor): se volvieron a")
    ap("digitar los dos viáticos que la empresa ya pagó (personal en MACAS) y se comparó")
    ap("concepto por concepto lo que calcula el programa con lo que dice el Excel.")
    ap("La carga la hace `herramientas\\viaticos_148_149.py`.")
    ap("")
    ap("| Dato | Valor |")
    ap("|---|---|")
    ap("| Base usada | `%s` |" % base)
    ap("| Copia de seguridad | `%s` |" % (copia or "—"))
    ap("| Parámetros | desayuno $%.2f · almuerzo $%.2f · merienda $%.2f · taxi $%.2f · "
       "hospedaje $%.2f por noche · agua $%.2f por día · km $%.2f · redondeo del cajero $%.2f |"
       % (p["valor_desayuno"], p["valor_almuerzo"], p["valor_merienda"],
          p["valor_taxi_salida"], p["valor_hospedaje"], p["valor_agua"],
          p["valor_combustible_km"], p.get("redondeo_cajero", 5)))
    ap("| Horas límite | desayuno y taxi de salida %s · almuerzo %s · merienda y taxi de "
       "regreso %s |" % (p["hora_limite_desayuno"], p["hora_limite_almuerzo"],
                         p["hora_limite_merienda"]))
    ap("")
    for r in resultados:
        ap("## Viático N° %d — %s" % (r["numero"], r["cab"]["responsable"]))
        ap("")
        ap("| Dato | Valor |")
        ap("|---|---|")
        ap("| Vehículo | %s |" % r["cab"]["placa"])
        ap("| Orden de combustible | %s |" % r["cab"]["orden_combustible"])
        ap("| Cliente y proyecto | %s |" % r["cab"]["cliente_proyecto"])
        ap("| Observaciones | %s |" % r["cab"]["observaciones"])
        ap("| Personas | %d |" % len(r["filas"]))
        ap("| Total que paga el programa | **$%.2f** |"
           % sum(float(f.get("total") or 0) for f in r["filas"]))
        ap("| Total ya pagado según el Excel | **$%.2f** |"
           % float(r["datos"]["esperado_totales"]["total"]))
        ap("")
        ap("Cada celda va como **programa / Excel** (lo que calcula el sistema / lo que")
        ap("dicen las columnas del Excel ya pagado).")
        ap("")
        ap("| Concepto | %s | %s | %s | TOTALES |"
           % (r["filas"][0]["nombre_empleado"],
              r["filas"][1]["nombre_empleado"] if len(r["filas"]) > 1 else "—",
              r["filas"][2]["nombre_empleado"] if len(r["filas"]) > 2 else "—"))
        ap("|---|---|---|---|---|")
        for clave, _ in CAMPOS_COMPARA:
            celdas = []
            for i in range(3):
                if i < len(r["detalle"]):
                    celdas.append(_celda(clave, *r["detalle"][i][clave]))
                else:
                    celdas.append("")
            if clave in NO_TOTALIZA:
                col_total = "%s / —" % _txt(clave, r["totales"][clave][0])
            else:
                col_total = _celda(clave, *r["totales"][clave])
            ap("| %s | %s | %s | %s | %s |"
               % (ROTULOS[clave], celdas[0], celdas[1], celdas[2], col_total))
        ap("")
        if r["diferencias"]:
            ap("### Diferencias encontradas")
            ap("")
            for d in r["diferencias"]:
                ap("- %s" % d)
        else:
            ap("### Diferencias encontradas")
            ap("")
            ap("**Ninguna**: el programa paga exactamente lo mismo que el Excel, fila por")
            ap("fila y en los totales.")
        ap("")
        ap("### PDF guardados")
        ap("")
        for etiqueta, ruta in r["pdf"]:
            ap("- %s: `%s`" % (etiqueta, ruta))
        ap("")
    ap("## Notas")
    ap("")
    ap("- La columna **«VALOR A RETIRAR EN CAJERO»** del Excel está **vacía** en los dos")
    ap("  viáticos (en el papel sale «-»), mientras que el programa sí la calcula:")
    ap("  redondea **hacia arriba** al múltiplo de $5 (183 → 185 y 116 → 120). Los")
    ap("  **TOTAL VIÁTICOS** son idénticos ($415,00 y $300,00), que es lo que se pagó.")
    ap("  Si se quiere esa columna en blanco hay que apagar el redondeo del cajero")
    ap("  (Parámetros → redondeo 0).")
    ap("- El **combustible** sale de los km del chofer × $0,25 (230 km → $57,50, igual que")
    ap("  el Excel); los acompañantes lo llevan en $0,00 porque no reciben combustible.")
    ap("- El **parqueadero/peaje** lo escribió la empresa a mano ($9,50 en el 148 y $10,50")
    ap("  en el 149): en el programa se digita en el mismo campo del formulario.")
    ap("- Fechas: el programa cuenta los días y las noches con las fechas, así que para que")
    ap("  dé los **5 días y 4 noches** que el Excel pagó, el regreso va 4 días después de la")
    ap("  salida (el encargado sale el 28/09 y regresa el 02/10; los acompañantes salen el")
    ap("  29/09 y regresan el 03/10). La columna «Días de Viaje» del Excel está escrita a")
    ap("  mano: por eso ahí conviven fechas de 5 días con un 5 escrito.")
    ap("- El cliente se guardó como **LA MERCED**, igual que en el Excel. En la lista de")
    ap("  clientes del sistema el nombre completo es *COOPERATIVA DE AHORRO Y CREDITO LA")
    ap("  MERCED*; si se prefiere ese nombre, se cambia en el viático y se vuelve a correr")
    ap("  este informe.")
    ap("")
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text("\n".join(L) + "\n", encoding="utf-8")
    return L


# ------------------------------------------------------------------------ main
def main():
    try:                              # tildes y símbolos correctos en la consola de Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    import configuracion as cfg
    import database as db

    ap = argparse.ArgumentParser(
        description="Carga los viáticos reales N° 148 y 149 en la base local y guarda sus PDF.")
    ap.add_argument("--sin-guardar", action="store_true",
                    help="solo calcula y compara: no escribe nada en la base")
    args = ap.parse_args()

    db.init_db()
    p = db.cargar_parametros()
    base = cfg.dir_datos() / "viaticos.db"
    print("Base LOCAL:        %s" % base)
    print("Navegador para PDF: %s" % (navegador() or "NO ENCONTRADO"))
    copia = None
    if not args.sin_guardar:
        copia = respaldar_base()
        print("Copia de seguridad: %s" % (copia or "(todavía no existía la base)"))

    resultados = []
    for datos in VIATICOS:
        filas = filas_del_viatico(datos, p)
        detalle, totales, diferencias = comparar(datos, filas)
        numero = db.clave_viatico(ANIO, datos["numero"])
        print("\nVIÁTICO N° %d · %s · %s" % (datos["numero"], datos["cab"]["placa"],
                                             datos["cab"]["responsable"]))
        for i, f in enumerate(filas, 1):
            print("   %d) %-34s días %d · km %d · $%.2f"
                  % (i, f["nombre_empleado"], f["dias_viaje"], f["km_recorridos"],
                     f["total"]))
        total_prog = sum(float(f.get("total") or 0) for f in filas)
        total_excel = float(datos["esperado_totales"]["total"])
        print("   TOTAL: programa $%.2f · Excel ya pagado $%.2f · %s"
              % (total_prog, total_excel,
                 "IGUAL, al centavo" if not diferencias else "HAY DIFERENCIAS"))
        for d in diferencias:
            print("   ⚠ %s" % d)
        pdfs = []
        if not args.sin_guardar:
            guardar_viatico(datos, filas)
            guardadas = db.filas_numero(numero)
            cab = dict(guardadas[0])
            cab["efectivo_combustible"] = max([float(f.get("efectivo_combustible") or 0)
                                               for f in guardadas] or [0.0])
            archivo = CARPETA_PDF / ("viatico_%s.pdf" % db.db_etiqueta_archivo(numero))
            html_a_pdf(html_del_programa(numero, cab, guardadas), archivo)
            pdfs.append(("PDF del programa (el de 🖨 IMPRIMIR / PDF)", archivo))
            archivo2 = CARPETA_PDF / ("viatico_%s_formato_empresa.pdf"
                                      % db.db_etiqueta_archivo(numero))
            html_a_pdf(_html_formato_empresa(numero, datos, guardadas), archivo2)
            pdfs.append(("PDF con el formato del Excel de la empresa", archivo2))
            print("   PDF del programa:     %s" % archivo)
            print("   PDF formato empresa:  %s" % archivo2)
        resultados.append({"numero": datos["numero"], "cab": datos["cab"],
                           "datos": datos, "filas": filas, "detalle": detalle,
                           "totales": totales, "diferencias": diferencias, "pdf": pdfs})

    if resultados and not args.sin_guardar:
        subir_secuencia(VIATICOS[-1]["numero"])
        print("\nPróximo N° de viático del año: %s" % db.numero_visible(db.proximo_numero()))
        informe(resultados, p, base, copia)
        print("Informe: %s" % INFORME)

    total_prog = sum(float(f.get("total") or 0) for r in resultados for f in r["filas"])
    total_excel = sum(float(r["datos"]["esperado_totales"]["total"]) for r in resultados)
    print("\nTOTAL de los dos viáticos: programa $%.2f · Excel ya pagado $%.2f"
          % (total_prog, total_excel))
    print("Carpeta de PDF: %s" % CARPETA_PDF)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
