# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_ajustes.py — Reglas de los **ajustes** de viático (días adicionales).

    python pruebas_ajustes.py

Trabaja con una base de prueba temporal (SQLite) y sin abrir ventanas visibles, y
comprueba las tres cosas que fallaban en el viático 164/2026:

  A) **Fechas**: el ajuste N° 2 (y los siguientes) empieza el día siguiente al último
     día del ajuste anterior, no el día siguiente al regreso del original.
  B) **Hospedaje**: se paga **por noche** (las noches entre la salida y el regreso),
     no un día de hospedaje por cada día del ajuste, **más la noche del último día
     entregado** (la del regreso del original o del ajuste anterior), que el viático
     anterior no pagó. Así el original y todos los ajustes suman exactamente las
     noches que hubo entre la primera salida y el último regreso.
  C) **Taxi de regreso**: se paga **una sola vez** en todo el viático. Si el original
     ya lo pagó, los ajustes lo muestran en $0 (el viajero vuelve a su casa al final,
     no una vez por cada ampliación). Si el original no lo pagó porque volvía antes de
     la hora límite y el regreso del ajuste sí llega a esa hora, el ajuste lo paga.
     El taxi de salida nunca se paga en un ajuste (se pagó en el original).

Al terminar borra la carpeta temporal: no toca los datos de trabajo.
"""
import os
import shutil
import sys
import tempfile
from datetime import date, time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # sin pantalla
_TEMP = tempfile.mkdtemp(prefix="viaticos_ajustes_")
os.environ["VIATICOS_MOTOR"] = "sqlite"
os.environ["VIATICOS_DATA"] = _TEMP
os.environ["VIATICOS_RESPALDOS"] = "carpeta"

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

_resultados = []
_mensajes = []          # lo que el sistema habría mostrado en pantalla


def revisar(nombre, condicion, detalle=""):
    ok = bool(condicion)
    _resultados.append(ok)
    print(("OK    " if ok else "FALLA ") + nombre
          + (("  ->  %s" % (detalle,)) if detalle != "" else ""))
    return ok


def _m(valor):
    return "$%.2f" % float(valor or 0)


def main():
    import calculos as CAL
    import database as db
    import qt_comunes as C
    import q_viaje as QV
    from q_login import crear_app

    crear_app()                     # Qt necesita una aplicación, aunque no se vea
    # Sin ventanas modales: la prueba tiene que correr sola. Lo que el sistema
    # avisaría en pantalla se guarda en `_mensajes` para poder mostrarlo al fallar.
    C.informar = lambda *a, **k: None
    C.aviso = lambda *a, **k: _mensajes.append(str(a[-1]) if a else "")
    C.error = lambda *a, **k: _mensajes.append(str(a[-1]) if a else "")
    C.confirmar = lambda *a, **k: True
    C.confirmar_peligro = lambda *a, **k: True

    db.init_db()
    db.agregar_empleado("PEREZ JUAN")      # el chofer/encargado tiene que existir
    p = db.cargar_parametros()
    print("Parámetros: desayuno %s · almuerzo %s · merienda %s · hospedaje %s · agua %s"
          % (_m(p["valor_desayuno"]), _m(p["valor_almuerzo"]), _m(p["valor_merienda"]),
             _m(p["valor_hospedaje"]), _m(p["valor_agua"])))
    print("            taxi de salida %s · taxi de regreso %s (desde las %s)\n"
          % (_m(p["valor_taxi_salida"]), _m(p["valor_taxi_regreso"]),
             str(p.get("hora_limite_taxi_regreso") or "")[:5]))

    # ---------------- viático original (como el 164/2026) ----------------
    # 04/10 05:00 → 11/10 22:15: 8 días, 7 noches, taxis de ida y vuelta.
    v = CAL.DatosViaje(
        nombre_empleado="PEREZ JUAN", lugar_trabajo="GUALACEO, AZUAY",
        fecha_salida=date(2026, 10, 4), hora_salida=time(5, 0),
        fecha_regreso=date(2026, 10, 11), hora_regreso=time(22, 15),
        fecha_llegada_trabajo=date(2026, 10, 4), hora_llegada_trabajo=time(9, 0),
        fecha_salida_trabajo=date(2026, 10, 11), hora_salida_trabajo=time(13, 15),
        km_recorridos=100.0)
    reg = CAL.calcular(v, p)
    original = {"nombre_empleado": v.nombre_empleado, "es_encargado": 1, "es_chofer": 1,
                "medio_transporte": "AUTO", "lugar_trabajo": v.lugar_trabajo,
                "provincia": "AZUAY", "canton": "GUALACEO",
                "fecha_salida": "2026-10-04", "hora_salida": "05:00",
                "fecha_regreso": "2026-10-11", "hora_regreso": "22:15",
                "fecha_llegada_trabajo": "2026-10-04", "hora_llegada_trabajo": "09:00",
                "fecha_salida_trabajo": "2026-10-11", "hora_salida_trabajo": "13:15",
                "km_recorridos": 100.0, **reg}
    numero = db.guardar_viaje({"responsable": "PEREZ JUAN",
                               "cliente_proyecto": "MIEMPRESA"}, [original])
    revisar("El viático original se guardó", len(db.filas_originales(numero)) == 1,
            "N° %s · %d día(s), %d noche(s), total %s"
            % (numero, reg["dias_viaje"],
               round(reg["hospedaje"] / p["valor_hospedaje"]), _m(reg["total"])))

    ventana = QV.ViajeWindow(None, {"nombre": "PRUEBA", "usuario": "prueba",
                                    "rol": db.ROL_SUPER})
    cab = {"responsable": "PEREZ JUAN", "cliente_proyecto": "MIEMPRESA"}

    # ---------------- ajuste N° 1: regreso el 16/10 a las 22:15 ----------------
    ventana._cargar_formulario(db.filas_originales(numero), numero,
                               db.proximo_ajuste(numero))
    revisar("Ajuste 1 · la salida se pone sola el día después del original",
            ventana.cal_salida.valor() == "2026-10-12", ventana.cal_salida.valor())
    ventana.cal_regreso.set_valor("2026-10-16")
    ventana.cb_hregreso.set_valor("22:15")
    _mensajes.clear()
    filas1 = ventana._construir_filas(avisar=True) or []
    if not revisar("Ajuste 1 · se pudo calcular", len(filas1) == 1,
                   " · ".join(_mensajes)):
        return
    a1 = filas1[0]
    noches1 = (date(2026, 10, 16) - date(2026, 10, 11)).days
    revisar("Ajuste 1 · fechas 12/10 → 16/10",
            a1["fecha_salida"] == "2026-10-12" and a1["fecha_regreso"] == "2026-10-16",
            "%s → %s" % (a1["fecha_salida"], a1["fecha_regreso"]))
    revisar("Ajuste 1 · 5 días", a1["dias_viaje"] == 5, a1["dias_viaje"])
    revisar("B) Ajuste 1 · hospedaje por NOCHE ($%d = %d noches: la del 11 que el"
            " original no pagó, más las del 12 al 15)" % (p["valor_hospedaje"] * noches1,
                                                         noches1),
            abs(float(a1["hospedaje"]) - p["valor_hospedaje"] * noches1) < 0.005,
            "%s (%d noches)" % (_m(a1["hospedaje"]), noches1))
    revisar("C) Ajuste 1 · taxi de regreso en $0: el original ya lo pagó (no se duplica)",
            abs(float(a1["taxi_regreso"])) < 0.005, _m(a1["taxi_regreso"]))
    revisar("Ajuste 1 · taxi de salida en cero (ya se pagó en el original)",
            abs(float(a1["taxi_salida"])) < 0.005, _m(a1["taxi_salida"]))
    revisar("Ajuste 1 · llegada y salida del trabajo dentro del período",
            a1["fecha_llegada_trabajo"] == "2026-10-12"
            and a1["fecha_salida_trabajo"] == "2026-10-16",
            "%s / %s" % (a1["fecha_llegada_trabajo"], a1["fecha_salida_trabajo"]))
    total1 = round(sum(float(a1[c]) for c in ("desayuno", "almuerzo", "merienda",
                                              "hospedaje", "agua", "taxi_regreso")), 2)
    revisar("Ajuste 1 · el total es la suma de sus conceptos",
            abs(float(a1["total"]) - total1) < 0.005,
            "%s = %s" % (_m(a1["total"]), _m(total1)))
    db.guardar_ajuste_viaje(numero, cab, filas1)
    print("      ajuste 1 guardado · total %s" % _m(a1["total"]))

    # ---------------- ajuste N° 2: regreso el 17/10 a las 22:15 ----------------
    # Este es el caso que fallaba: la salida tiene que ser el 17/10 (el día después
    # del ajuste 1) y no el 12/10 (el día después del original), que volvía a pagar
    # los días del 12 al 16 y cobraba una noche de más.
    revisar("A) El último día entregado es el del AJUSTE 1 (16/10) y no el del original",
            db.ultimo_regreso_entregado(numero, 2) == date(2026, 10, 16),
            db.ultimo_regreso_entregado(numero, 2))
    ventana._cargar_formulario(db.filas_originales(numero), numero,
                               db.proximo_ajuste(numero))
    revisar("A) Ajuste 2 · la salida se pone sola el día después del ajuste 1",
            ventana.cal_salida.valor() == "2026-10-17", ventana.cal_salida.valor())
    ventana.cal_regreso.set_valor("2026-10-17")
    ventana.cb_hregreso.set_valor("22:15")
    _mensajes.clear()
    filas2 = ventana._construir_filas(avisar=True) or []
    if not revisar("Ajuste 2 · se pudo calcular", len(filas2) == 1,
                   " · ".join(_mensajes)):
        return
    a2 = filas2[0]
    revisar("A) Ajuste 2 · fechas 17/10 → 17/10 (un solo día)",
            a2["fecha_salida"] == "2026-10-17" and a2["fecha_regreso"] == "2026-10-17",
            "%s → %s" % (a2["fecha_salida"], a2["fecha_regreso"]))
    revisar("Ajuste 2 · 1 día", a2["dias_viaje"] == 1, a2["dias_viaje"])
    revisar("B) Ajuste 2 · hospedaje $%d (la noche del 16, que el ajuste 1 no pagó)"
            % p["valor_hospedaje"],
            abs(float(a2["hospedaje"]) - p["valor_hospedaje"]) < 0.005,
            _m(a2["hospedaje"]))
    revisar("C) Ajuste 2 · taxi de regreso en $0 (ya se pagó en el original)",
            abs(float(a2["taxi_regreso"])) < 0.005, _m(a2["taxi_regreso"]))
    revisar("Ajuste 2 · también paga las comidas del día",
            all(abs(float(a2[c]) - p["valor_" + c]) < 0.005
                for c in ("desayuno", "almuerzo", "merienda")),
            "des %s · alm %s · mer %s" % (_m(a2["desayuno"]), _m(a2["almuerzo"]),
                                          _m(a2["merienda"])))
    db.guardar_ajuste_viaje(numero, cab, filas2)
    print("      ajuste 2 guardado · total %s" % _m(a2["total"]))

    # --------- D) el original NO pagó taxi de regreso y el ajuste SÍ ---------
    # El taxi de regreso es «responsivo»: se paga donde corresponde y UNA sola vez.
    # Original 04/10 05:00 → 11/10 19:30 (volvía antes de las 21:00, sin taxi). El ajuste
    # cambia el regreso al 16/10 22:15: ahora sí vuelve a la hora límite, así que el taxi
    # se paga en el AJUSTE; y el ajuste siguiente ya no lo vuelve a pagar.
    v_d = CAL.DatosViaje(
        nombre_empleado="PEREZ JUAN", lugar_trabajo="GUALACEO, AZUAY",
        fecha_salida=date(2026, 10, 4), hora_salida=time(5, 0),
        fecha_regreso=date(2026, 10, 11), hora_regreso=time(19, 30),
        fecha_llegada_trabajo=date(2026, 10, 4), hora_llegada_trabajo=time(9, 0),
        fecha_salida_trabajo=date(2026, 10, 11), hora_salida_trabajo=time(12, 30),
        km_recorridos=100.0)
    reg_d = CAL.calcular(v_d, p)
    original_d = {"nombre_empleado": v_d.nombre_empleado, "es_encargado": 1,
                  "es_chofer": 1, "medio_transporte": "AUTO",
                  "lugar_trabajo": v_d.lugar_trabajo,
                  "provincia": "AZUAY", "canton": "GUALACEO",
                  "fecha_salida": "2026-10-04", "hora_salida": "05:00",
                  "fecha_regreso": "2026-10-11", "hora_regreso": "19:30",
                  "fecha_llegada_trabajo": "2026-10-04", "hora_llegada_trabajo": "09:00",
                  "fecha_salida_trabajo": "2026-10-11", "hora_salida_trabajo": "12:30",
                  "km_recorridos": 100.0, **reg_d}
    numero_d = db.guardar_viaje({"responsable": "PEREZ JUAN",
                                 "cliente_proyecto": "MIEMPRESA"}, [original_d])
    revisar("D) Original que vuelve 19:30 · sin taxi de regreso",
            abs(float(reg_d["taxi_regreso"])) < 0.005, _m(reg_d["taxi_regreso"]))

    ventana_d = QV.ViajeWindow(None, {"nombre": "PRUEBA", "usuario": "prueba",
                                      "rol": db.ROL_SUPER})
    ventana_d._cargar_formulario(db.filas_originales(numero_d), numero_d,
                                 db.proximo_ajuste(numero_d))
    ventana_d.cal_regreso.set_valor("2026-10-16")
    ventana_d.cb_hregreso.set_valor("22:15")
    _mensajes.clear()
    filas_d = ventana_d._construir_filas(avisar=True) or []
    if revisar("D) Ajuste que vuelve 22:15 · se pudo calcular", len(filas_d) == 1,
               " · ".join(_mensajes)):
        d1 = filas_d[0]
        revisar("D) El ajuste SÍ paga el taxi de regreso que el original no pagó",
                abs(float(d1["taxi_regreso"]) - p["valor_taxi_regreso"]) < 0.005,
                _m(d1["taxi_regreso"]))
        revisar("D) Y el total del ajuste incluye ese taxi",
                abs(float(d1["total"]) - round(sum(float(d1[c]) for c in (
                    "desayuno", "almuerzo", "merienda", "hospedaje", "agua",
                    "taxi_regreso")), 2)) < 0.005,
                _m(d1["total"]))
        db.guardar_ajuste_viaje(numero_d, cab, filas_d)
        ventana_d._cargar_formulario(db.filas_originales(numero_d), numero_d,
                                     db.proximo_ajuste(numero_d))
        ventana_d.cal_regreso.set_valor("2026-10-17")
        ventana_d.cb_hregreso.set_valor("22:15")
        _mensajes.clear()
        filas_d2 = ventana_d._construir_filas(avisar=True) or []
        if revisar("D) Ajuste siguiente · se pudo calcular", len(filas_d2) == 1,
                   " · ".join(_mensajes)):
            revisar("D) El ajuste siguiente ya NO vuelve a pagar el taxi de regreso",
                    abs(float(filas_d2[0]["taxi_regreso"])) < 0.005,
                    _m(filas_d2[0]["taxi_regreso"]))
    ventana_d.close()

    # ---------------- resumen de lo entregado en los ajustes ----------------
    ajustes = db.ajustes_viaje(numero)
    revisar("Quedaron los 2 ajustes guardados", len(ajustes) == 2,
            [int(x["ajuste_numero"]) for x in ajustes])
    salidas = [str(x["fecha_salida"])[:10] for x in ajustes]
    revisar("Los días de los ajustes no se repiten", salidas[0] != salidas[1], salidas)
    dias_total = (int(original["dias_viaje"]) + int(a1["dias_viaje"])
                  + int(a2["dias_viaje"]))
    noches_total = sum(round(float(x["hospedaje"] or 0) / p["valor_hospedaje"])
                       for x in (original, a1, a2))
    revisar("El original y sus ajustes pagan los 14 días del viaje (04/10 → 17/10)",
            dias_total == (date(2026, 10, 17) - date(2026, 10, 4)).days + 1, dias_total)
    revisar("El original y sus ajustes pagan las 13 noches del viaje",
            noches_total == (date(2026, 10, 17) - date(2026, 10, 4)).days, noches_total)
    print("\nEntregado en los ajustes: %s"
          % _m(sum(float(x["total"] or 0) for x in ajustes)))
    ventana.close()


def _terminar():
    """Cierra la ventana en pruebas, borra la carpeta temporal y resume el resultado."""
    fallos = _resultados.count(False)
    print("\n%d comprobación(es), %d fallo(s)" % (len(_resultados), fallos))
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
    finally:
        shutil.rmtree(_TEMP, ignore_errors=True)
    if "--sin-pausa" not in sys.argv:
        input("\nPresione Enter para cerrar...")
    sys.exit(codigo)

