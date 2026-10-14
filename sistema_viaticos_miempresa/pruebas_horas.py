# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
# -*- coding: utf-8 -*-
"""Prueba en pantalla (offscreen): cálculo automático de llegadas y colores del resumen."""
import io
import os
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
SIS = BASE
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, SIS)
os.chdir(SIS)

from PySide6.QtWidgets import QApplication          # noqa: E402

app = QApplication([])

import q_viaje as QV                                # noqa: E402
import qt_tema as T                                 # noqa: E402
import calculos as CAL                              # noqa: E402

salida = io.open(os.path.join(BASE, "pruebas_horas_resultado.txt"), "w", encoding="utf-8")
fallos = []


def w(t=""):
    salida.write(str(t) + "\n")


def revisar(cond, texto):
    w(("  OK    " if cond else "  FALLA ") + texto)
    if not cond:
        fallos.append(texto)


# Parámetros de fábrica, para que esta prueba no dependa de la base de datos.
P = {"hora_limite_desayuno": "06:00", "hora_limite_almuerzo": "13:00",
     "hora_limite_merienda": "21:00", "horas_desayuno_viaje": 1.0,
     "horas_almuerzo_viaje": 1.0, "horas_merienda_viaje": 1.0}


def tramo(hora, recorrido):
    """(total, recorrido, comidas, llegada) de un tramo que sale a esa hora.

    El recorrido se da en horas (así la prueba no depende de los km ni del vehículo).
    """
    inicio = datetime(2026, 9, 24, *[int(x) for x in hora.split(":")])
    total, camino, comidas = QV.detalle_viaje(0, 0, P, inicio, recorrido)
    return total, camino, comidas, (inicio + timedelta(hours=total))


w("A) Regla de las comidas: la que cae dentro del viaje suma sus horas (1 h de fábrica)")
CASOS = (
    ("sale 10:00 y llega 13:00 → 14:00 por el almuerzo", "10:00", 3, "14:00",
     ["el almuerzo"]),
    ("vuelve a las 22:00 → 23:00 por la merienda del camino", "18:00", 4, "23:00",
     ["la merienda"]),
    ("llega al lugar a las 08:00 → 09:00 por el desayuno", "05:00", 3, "09:00",
     ["el desayuno"]),
    ("viaje largo 02:00 → 14:00 → 16:00 por el desayuno y el almuerzo", "02:00", 12,
     "16:00", ["el desayuno", "el almuerzo"]),
    ("sale 13:30 (el almuerzo ya pasó antes de salir) → no se suma nada", "13:30", 4,
     "17:30", []),
    ("cruce de medianoche 20:00 → 02:00 con la merienda", "20:00", 6, "03:00",
     ["la merienda"]),
)
for etiqueta, hora, horas, esperado, comidas_esperadas in CASOS:
    total, camino, comidas, llegada = tramo(hora, horas)
    detalle = " + ".join("%g h por %s" % (h, n) for n, h, _l in comidas) or "ninguna comida"
    w("   %s" % etiqueta)
    w("     salida %s: %d h de recorrido + %s = %d h → %s"
      % (hora, camino, detalle, total, llegada.strftime("%d/%m %H:%M")))
    revisar(llegada.strftime("%H:%M") == esperado,
            "llegada %s (%s)" % (esperado, etiqueta))
    revisar([n for n, _h, _l in comidas] == comidas_esperadas,
            "comidas contadas: %s" % ([n for n, _h, _l in comidas] or "ninguna"))

w()
w("B) el formulario escribe las dos llegadas, cada tramo con su propia salida")
ventana = QV.ViajeWindow(usuario={"usuario": "PRUEBA", "nombre": "PRUEBA", "rol": "admin"})
ventana.show()
app.processEvents()

w("   ida: a Guayaquil (196 km · 4 h de tabla → 4 h) saliendo 02:00")
ventana.cb_provincia.set_valor("GUAYAS")
ventana._al_provincia()
ventana.cb_canton.set_valor("GUAYAQUIL")
ventana._al_canton()
revisar((ventana.txt_km.text() or "").strip() in ("196", "196.0"),
        "los km del cantón se pusieron solos: %s" % ventana.txt_km.text())
revisar("h de viaje" in ventana.lbl_km.text() or "de viaje" in ventana.lbl_km.text(),
        "el aviso muestra las horas: %s" % ventana.lbl_km.text())
revisar(ventana.lbl_km.text() == "tabla: 196 km · 4 h 00 min de viaje",
        "el aviso muestra las horas como se leen (no 4.0): %s" % ventana.lbl_km.text())
ventana.cal_salida.set_valor("2026-09-24")
ventana.cb_hsalida.set_valor("02:00")
ventana.cal_saltr.set_valor("2026-09-24")
ventana.cb_hsaltr.set_valor("14:00")
ventana._recalcular_horas()
app.processEvents()
w("     llegada al trabajo : %s %s" % (ventana.cal_lleg.valor(), ventana.cb_hlleg.valor()))
w("     llegada Miempresa: %s %s" % (ventana.cal_regreso.valor(), ventana.cb_hregreso.valor()))
revisar(ventana.cal_lleg.valor() == "2026-09-24" and ventana.cb_hlleg.valor() == "07:00",
        "llegada al trabajo = 24/09 07:00 (4 h de recorrido + 1 h del desayuno)")
revisar(ventana.cal_regreso.valor() == "2026-09-24" and ventana.cb_hregreso.valor() == "18:00",
        "llegada a Miempresa = 24/09 18:00 (sale del trabajo 14:00 + 4 h; ninguna comida "
        "cae en ese tramo)")

w("   vuelta: sale del trabajo 18:00 (la merienda de las 21:00 cae en el camino)")
ventana.cb_hsaltr.set_valor("18:00")
ventana._recalcular_horas()
app.processEvents()
w("     llegada Miempresa: %s %s" % (ventana.cal_regreso.valor(), ventana.cb_hregreso.valor()))
revisar(ventana.cal_regreso.valor() == "2026-09-24" and ventana.cb_hregreso.valor() == "23:00",
        "llegada a Miempresa = 24/09 23:00 (18:00 + 4 h + 1 h de la merienda)")
revisar(ventana.cb_hlleg.valor() == "07:00",
        "la ida no cambió al cambiar el horario de la vuelta (%s)" % ventana.cb_hlleg.valor())

w()
w("C) el BUS también se calcula solo: el mismo tiempo de viaje que los demás")
ventana.cb_vehiculo.set_valor("BUS-01  BUS")
app.processEvents()
revisar(ventana._va_en_bus(), "el vehículo elegido se reconoce como BUS (%s)"
        % ventana.cb_vehiculo.valor())
ventana.cal_salida.set_valor("2026-09-24")
ventana.cb_hsalida.set_valor("02:00")
ventana.cal_saltr.set_valor("2026-09-24")
ventana.cb_hsaltr.set_valor("14:00")
ventana._recalcular_horas()
app.processEvents()
w("     ida en BUS    : %s %s" % (ventana.cal_lleg.valor(), ventana.cb_hlleg.valor()))
w("     vuelta en BUS : %s %s" % (ventana.cal_regreso.valor(), ventana.cb_hregreso.valor()))
revisar(ventana.cal_lleg.valor() == "2026-09-24" and ventana.cb_hlleg.valor() == "07:00",
        "en BUS la llegada al trabajo = 24/09 07:00, igual que en los demás "
        "(4 h de recorrido + 1 h del desayuno)")
revisar(ventana.cal_regreso.valor() == "2026-09-24" and ventana.cb_hregreso.valor() == "18:00",
        "en BUS la llegada a Miempresa = 24/09 18:00 (sale del trabajo 14:00 + 4 h; "
        "ninguna comida cae en ese tramo)")
ventana.cb_hsaltr.set_valor("18:00")
ventana._recalcular_horas()
app.processEvents()
w("     vuelta en BUS : %s %s" % (ventana.cal_regreso.valor(), ventana.cb_hregreso.valor()))
revisar(ventana.cal_regreso.valor() == "2026-09-24" and ventana.cb_hregreso.valor() == "23:00",
        "en BUS la vuelta de las 18:00 llega 23:00 (4 h + 1 h de la merienda): el BUS "
        "ya no se deja sin calcular (antes sus horas se escribían a mano)")
revisar(QV.recorrido_de_viaje(200, 45, 0) == 5,
        "si el cantón no tuviera horas, el BUS usa su velocidad (200 km ÷ 45 km/h → 5 h)")
auto = QV.DialogoHorario(ventana, "PRUEBA", None, {}, 200, 40, 3.5)
revisar(auto.horas == 3.5, "(el diálogo del horario del viajero sigue igual): 3.5 h")

w()
w("D) el detalle del estimado dice cuál comida y a qué hora")
_explicacion = QV.texto_estimado("Vuelta — salida del trabajo",
                                  datetime(2026, 9, 24, 18, 0), 5, 4,
                                  [("la merienda", 1.0, "21:00")],
                                  datetime(2026, 9, 24, 23, 0))
w("   %s" % _explicacion.replace("\n", "\n   "))
revisar("1 h por la merienda (21:00" in _explicacion,
        "el detalle dice la comida y su hora límite")
revisar("23:00" in _explicacion, "el detalle dice la hora de llegada")

w()
w("E) colores del resumen: TOTALES suave y TOTAL GENERAL amarillo fuerte")
filas = [{"nombre_empleado": "UNO", "lugar_trabajo": "GUAYAQUIL, GUAYAS",
          "fecha_salida": "2026-09-24", "hora_salida": "02:00", "fecha_regreso": "2026-09-24",
          "hora_regreso": "23:00", "dias_viaje": 1, "km_recorridos": 200, "desayuno": 3,
          "almuerzo": 3, "merienda": 3, "taxi_salida": 0, "taxi_regreso": 3, "hospedaje": 0,
          "agua": 1, "combustible": 50, "otros": 0, "parqueadero_peaje": 0, "total": 63,
          "valor_cajero": 65}]
contenido = [QV.vals_fila(1, filas[0]), QV.vals_totales(filas, "TOTAL VIÁTICO ORIGINAL"),
             QV.vals_totales(filas, "TOTAL GENERAL")]
ventana.tabla_prev.poner(contenido)
QV._pintar(ventana.tabla_prev, [1], QV.FONDO_TOTAL)
QV._pintar(ventana.tabla_prev, [2], QV.FONDO_GENERAL)
app.processEvents()
color_total = ventana.tabla_prev.item(1, 3).background().color().name()
color_general = ventana.tabla_prev.item(2, 3).background().color().name()
w("   TOTALES = %s · TOTAL GENERAL = %s" % (color_total, color_general))
revisar(color_total.lower() == "#fff2b8", "la fila de TOTALES queda en amarillo suave")
revisar(color_general.lower() == T.AMARILLO.lower(),
        "la fila de TOTAL GENERAL queda en el amarillo fuerte del informe (%s)" % T.AMARILLO)
foto = ventana.tabla_prev.grab()
imagen = foto.toImage()
amarillos = 0
for y in range(0, min(imagen.height(), 120)):
    for x in range(0, min(imagen.width(), 400), 3):
        c = imagen.pixelColor(x, y)
        if c.red() > 230 and c.green() > 170 and c.blue() < 130:
            amarillos += 1
revisar(amarillos > 0, "el amarillo se ve dibujado en la pantalla (%d puntos)" % amarillos)

w()
w("F) las horas se muestran como se leen («5 h 40 min») y se pueden escribir de las dos formas")
for valor, esperado, corto in ((5.67, "5 h 40 min", "5:40"), (6, "6 h 00 min", "6:00"),
                               (4.5, "4 h 30 min", "4:30"), (13.75, "13 h 45 min", "13:45"),
                               (0, "", "")):
    w("   %g h → «%s»  (en el campo se escribe «%s»)" % (valor, esperado, corto))
    revisar(CAL.horas_texto(valor) == esperado,
            "%g h se muestra como «%s» (no 5.67)" % (valor, esperado))
    revisar(CAL.horas_texto(valor, sufijo=False) == corto,
            "%g h se escribe como «%s»" % (valor, corto))
for escrito, esperado in (("5:40", 5.67), ("5 h 40 min", 5.67), ("5.67", 5.67),
                          ("5,5", 5.5), ("6", 6.0), ("0", 0.0), ("", None),
                          ("cinco", None), (None, None)):
    obtenido = CAL.horas_de_texto(escrito)
    w("   se escribe «%s» → %s" % (escrito, "nada" if obtenido is None
                                   else "%.2f h" % obtenido))
    revisar((obtenido is None) if esperado is None else round(obtenido, 2) == esperado,
            "escribiendo «%s» se entienden %s h" % (escrito, esperado))

w()
w("RESULTADO: %d fallos" % len(fallos))
for f in fallos:
    w("  · " + f)
salida.close()
print("listo, fallos=%d" % len(fallos))

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
