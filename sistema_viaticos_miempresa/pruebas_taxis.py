# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_taxis.py — Cuándo se paga el taxi (y cuándo NO) en todo el sistema.

    python pruebas_taxis.py

No abre ventanas ni toca la base de trabajo: trabaja con `calculos.calcular()` y
parámetros escritos a mano, así que corre en un segundo y se puede repetir siempre.

Comprueba las cinco cosas que fallaban:

  A) **Viático nuevo**: taxi de salida si sale a las 06:00 o antes; taxi de regreso
     si vuelve a las 21:00 o después; en los bordes (06:00 y 21:00) **sí** se paga.
  B) **Ajuste**: nunca paga taxi de salida (el viajero ya salió en el original); el
     de regreso se paga según la hora, igual que en el viático original.
  C) **Vuelta de madrugada** (opción encendida): se paga al que vuelve antes de las
     06:00, salvo la ida y vuelta en la misma madrugada (sale 04:00, vuelve 05:30):
     ese es el mismo traslado y el taxi de salida ya se pagó.
  D) **Parámetros raros** (`"06:00:00"` de PostgreSQL, `"6:00"`, o una base vieja
     sin las columnas de hora): la hora límite toma su valor de fábrica y el taxi se
     paga como siempre; antes el regreso se pagaba en **todos** los viáticos.
  E) La hora límite del taxi de salida **no** manda en la madrugada: si se cambia a
     las 09:00, el que vuelve a las 08:30 no es «madrugada».
"""
import os
import sys
from datetime import date, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

from calculos import DatosViaje, calcular, hora_limite   # noqa: E402

# Parámetros de fábrica (los mismos de database.PARAMS_INICIALES).
P = {"hora_limite_desayuno": time(6, 0), "valor_desayuno": 3.0,
     "hora_limite_almuerzo": time(13, 0), "valor_almuerzo": 3.0,
     "hora_limite_merienda": time(21, 0), "valor_merienda": 3.0,
     "hora_limite_taxi_salida": time(6, 0), "valor_taxi_salida": 3.0,
     "hora_limite_taxi_regreso": time(21, 0), "valor_taxi_regreso": 3.0,
     "valor_hospedaje": 15.0, "valor_agua": 1.0, "valor_combustible_km": 0.25,
     "redondeo_cajero": 5.0, "hospedaje_por_fechas": 1.0,
     "taxi_regreso_madrugada": 0.0}


def params(**cambios):
    """Parámetros de fábrica con los cambios que pida el caso."""
    p = dict(P)
    p.update(cambios)
    return p


def viaje(sal, hs, reg, hr):
    """Un viático de una persona con esas fechas y horas."""
    return DatosViaje(nombre_empleado="PRUEBA", lugar_trabajo="CUENCA",
                      fecha_salida=sal, hora_salida=hs,
                      fecha_regreso=reg, hora_regreso=hr)


def un_dia(hora_regreso):
    """El viaje de un **ajuste**: empieza a las 00:00 y vuelve ese mismo día."""
    return DatosViaje(nombre_empleado="PRUEBA", lugar_trabajo="CUENCA",
                      fecha_salida=date(2026, 10, 17), hora_salida=time(0, 0),
                      fecha_regreso=date(2026, 10, 17), hora_regreso=hora_regreso)


fallos = []
TOTAL = [0]


def revisar(nombre, resultado, esperado):
    """Compara (taxi_salida, taxi_regreso) con lo que dice la regla."""
    TOTAL[0] += 1
    salida = round(float(resultado.get("taxi_salida") or 0), 2)
    regreso = round(float(resultado.get("taxi_regreso") or 0), 2)
    ok = abs(salida - esperado[0]) < 0.005 and abs(regreso - esperado[1]) < 0.005
    print(("OK    " if ok else "FALLA ") + nombre
          + "  ->  salida $%.2f · regreso $%.2f  (esperado $%.2f · $%.2f)"
          % (salida, regreso, esperado[0], esperado[1]))
    if not ok:
        fallos.append(nombre)
    return ok


def revisar_simple(nombre, condicion, detalle=""):
    """Comprueba una condición cualquiera (lectura de horas límite)."""
    TOTAL[0] += 1
    ok = bool(condicion)
    print(("OK    " if ok else "FALLA ") + nombre
          + (("  ->  %s" % (detalle,)) if detalle != "" else ""))
    if not ok:
        fallos.append(nombre)
    return ok


def main():
    print("A) VIÁTICO NUEVO — ida si sale a las 06:00 o antes; vuelta si llega a las 21:00 o después")
    revisar("sale 05:00 y vuelve 22:00 el mismo día",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 1), time(22, 0)), params()), (3.0, 3.0))
    revisar("sale 08:00 y vuelve 20:00 el mismo día (ningún taxi)",
            calcular(viaje(date(2026, 10, 1), time(8, 0),
                           date(2026, 10, 1), time(20, 0)), params()), (0.0, 0.0))
    revisar("sale 06:00 exacto y vuelve 21:00 exacto (los bordes sí se pagan)",
            calcular(viaje(date(2026, 10, 1), time(6, 0),
                           date(2026, 10, 1), time(21, 0)), params()), (3.0, 3.0))
    revisar("sale 06:15 y vuelve 20:45 (ni uno ni otro)",
            calcular(viaje(date(2026, 10, 1), time(6, 15),
                           date(2026, 10, 1), time(20, 45)), params()), (0.0, 0.0))
    revisar("4 días: sale 05:00 el 1 y vuelve 22:15 el 4",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 4), time(22, 15)), params()), (3.0, 3.0))
    revisar("el taxi se paga una vez por viático, no por día",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 8), time(22, 15)), params()), (3.0, 3.0))

    print("\nB) AJUSTE — el taxi de salida nunca se paga (ya se pagó en el original)")
    revisar("ajuste que vuelve 22:15",
            calcular(un_dia(time(22, 15)), params(), ajuste=True), (0.0, 3.0))
    revisar("ajuste que vuelve 21:00 exacto",
            calcular(un_dia(time(21, 0)), params(), ajuste=True), (0.0, 3.0))
    revisar("ajuste que vuelve 20:00",
            calcular(un_dia(time(20, 0)), params(), ajuste=True), (0.0, 0.0))
    revisar("ajuste que vuelve 05:00 con la madrugada apagada",
            calcular(un_dia(time(5, 0)), params(), ajuste=True), (0.0, 0.0))
    revisar("ajuste que vuelve 05:00 con la madrugada encendida",
            calcular(un_dia(time(5, 0)), params(taxi_regreso_madrugada=1.0),
                     ajuste=True), (0.0, 3.0))

    print("\nC) VUELTA DE MADRUGADA (opción encendida; en el ajuste antes no se pagaba)")
    revisar("viaje de varios días que vuelve 03:00",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 3), time(3, 0)),
                     params(taxi_regreso_madrugada=1.0)), (3.0, 3.0))
    revisar("ida y vuelta la MISMA madrugada (sale 04:00, vuelve 05:30)",
            calcular(viaje(date(2026, 10, 1), time(4, 0),
                           date(2026, 10, 1), time(5, 30)),
                     params(taxi_regreso_madrugada=1.0)), (3.0, 0.0))
    revisar("vuelve 05:30 de varios días con la madrugada apagada",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 3), time(5, 30)), params()), (3.0, 0.0))

    print("\nD) PARÁMETROS COMO LOS GUARDA UNA BASE (texto, con segundos, base vieja)")
    revisar("horas como texto '06:00' y '21:00'",
            calcular(viaje(date(2026, 10, 1), time(8, 0),
                           date(2026, 10, 1), time(20, 0)),
                     params(hora_limite_taxi_salida="06:00",
                            hora_limite_taxi_regreso="21:00")), (0.0, 0.0))
    revisar("horas con segundos '06:00:00' y '21:00:00' (PostgreSQL)",
            calcular(viaje(date(2026, 10, 1), time(8, 0),
                           date(2026, 10, 1), time(20, 0)),
                     params(hora_limite_taxi_salida="06:00:00",
                            hora_limite_taxi_regreso="21:00:00")), (0.0, 0.0))
    revisar("horas sin cero delante '6:00' y '21:00'",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 1), time(22, 0)),
                     params(hora_limite_taxi_salida="6:00",
                            hora_limite_taxi_regreso="21:00")), (3.0, 3.0))
    revisar("base vieja sin las columnas de hora: sale 08:00 y vuelve 20:00",
            calcular(viaje(date(2026, 10, 1), time(8, 0),
                           date(2026, 10, 1), time(20, 0)),
                     {"valor_taxi_salida": 3.0, "valor_taxi_regreso": 3.0}), (0.0, 0.0))
    revisar("base vieja sin las columnas de hora: sale 05:00 y vuelve 22:00",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 1), time(22, 0)),
                     {"valor_taxi_salida": 3.0, "valor_taxi_regreso": 3.0}), (3.0, 3.0))
    revisar("hora límite vacía: se usa la de fábrica (06:00 y 21:00)",
            calcular(viaje(date(2026, 10, 1), time(5, 0),
                           date(2026, 10, 1), time(22, 0)),
                     params(hora_limite_taxi_salida="",
                            hora_limite_taxi_regreso="")), (3.0, 3.0))

    print("\nE) LA HORA LÍMITE DEL TAXI DE SALIDA NO MANDA EN LA MADRUGADA")
    revisar("límite de salida 09:00 y vuelve 08:30 (no es madrugada)",
            calcular(viaje(date(2026, 10, 1), time(10, 0),
                           date(2026, 10, 3), time(8, 30)),
                     params(taxi_regreso_madrugada=1.0,
                            hora_limite_taxi_salida="09:00")), (0.0, 0.0))

    print("\nF) UNA HORA LÍMITE QUE NO SE ENTIENDE NO PUEDE INVERTIR LAS REGLAS")
    revisar("hora límite basura ('xx') en los taxis: se usa la de fábrica",
            calcular(viaje(date(2026, 10, 1), time(8, 0),
                           date(2026, 10, 1), time(20, 0)),
                     params(hora_limite_taxi_salida="xx",
                            hora_limite_taxi_regreso="xx")), (0.0, 0.0))
    revisar_simple("hora_limite('06:00:00') se lee como 06:00",
                   hora_limite("06:00:00") == time(6, 0), hora_limite("06:00:00"))
    revisar_simple("hora_limite('6:00') se lee como 06:00",
                   hora_limite("6:00") == time(6, 0), hora_limite("6:00"))
    revisar_simple("hora_limite(time(21, 30)) queda igual",
                   hora_limite(time(21, 30)) == time(21, 30), hora_limite(time(21, 30)))
    revisar_simple("hora_limite(None, 21:00) devuelve la de fábrica",
                   hora_limite(None, time(21, 0)) == time(21, 0),
                   hora_limite(None, time(21, 0)))


def _terminar():
    print("\n%d comprobación(es), %d fallo(s)" % (TOTAL[0], len(fallos)))
    return 1 if fallos else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # tildes en consola
    except Exception:
        pass
    codigo = 1
    try:
        main()
        codigo = _terminar()
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nLa prueba se detuvo por un error inesperado.")
    if "--sin-pausa" not in sys.argv:
        input("\nPresione Enter para cerrar...")
    sys.exit(codigo)
