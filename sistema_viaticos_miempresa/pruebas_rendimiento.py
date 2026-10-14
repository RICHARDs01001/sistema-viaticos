# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_rendimiento.py — Mide cuánto tarda la pantalla y cuántas consultas hace.

Se ejecuta así:

    python pruebas_rendimiento.py                 (base local de prueba; no toca nada)
    python pruebas_rendimiento.py --servidor      (contra la base central; solo LEE)

Levanta de verdad las ventanas de viáticos, de parámetros y de justificación (sin abrir
ventanas, con la plataforma «offscreen») y cronometra lo que se hace todo el día: elegir
provincia, elegir cantón, abrir la lista de cantones, estimar el viaje, teclear los km,
guardar un viático, refrescar el historial, ver el detalle…

De cada acción informa:

  - consultas : cuántas consultas se le hicieron a la base
  - conex.    : cuántas conexiones hubo que **abrir**. Es lo caro: contra la base central
                cada conexión es un saludo completo por la red (TCP + usuario + clave).
                Antes había una por consulta; ahora debe haber una sola, reutilizada.
  - ms        : lo que tardó la acción

Con `--servidor` se mide contra la base central de `config.json` y **no se guarda nada**
(el paso de guardar se omite: no se escriben datos de prueba en la base de trabajo).

Opciones útiles:

    --comparar                  Hace la medición dos veces (antes y ahora) y las compara:
                                «antes» = abriendo una conexión por consulta (como era),
                                «ahora» = reutilizando la conexión.
    --simular-conexion=25       Suma 25 ms a cada conexión nueva, para ver en esta misma
                                máquina lo que se siente contra el servidor central.
    --ms-conexion=30            Costo estimado de abrir una conexión (para el «ahorro»).

Ejemplo para ver la mejora completa, sin servidor y sin tocar datos reales:

    python pruebas_rendimiento.py --comparar --simular-conexion=25
"""
import os
import sys
import tempfile
import time


def _empieza_entorno(servidor: bool):
    """Prepara el entorno de la prueba y devuelve la carpeta temporal (o None)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")     # sin pantalla
    if servidor:
        return None
    # Base local de prueba, en una carpeta desechable: los datos de trabajo no se tocan.
    temp = tempfile.mkdtemp(prefix="viaticos_rendimiento_")
    os.environ["VIATICOS_MOTOR"] = "sqlite"
    os.environ["VIATICOS_DATA"] = temp
    os.environ["VIATICOS_RESPALDOS"] = "carpeta"
    return temp


def _fila_viaje(**cambios):
    """Fila de viático con lo mínimo que la tabla exige (según su propio esquema)."""
    import database as db

    conn = db.conectar()
    columnas = conn.execute("PRAGMA table_info(viajes)").fetchall()
    conn.close()
    fila = {}
    for c in columnas:
        if c["notnull"] and c["name"] not in ("id", "viatico_numero", "ajuste_numero"):
            fila[c["name"]] = 0 if c["type"].upper() in ("REAL", "INTEGER", "NUMERIC") else ""
    fila.update(cambios)
    return fila


def _sembrar_datos():
    """Datos de mentira para que las pantallas tengan algo que mostrar."""
    import bd
    import database as db

    db.init_db()
    for nombre in ("PERSONAL DE EJEMPLO DOS", "PERSONAL DE EJEMPLO SEIS",
                   "PERSONAL DE EJEMPLO TRES", "PERSONAL DE EJEMPLO CUATRO"):
        db.agregar_empleado(nombre)
    for nombre in ("MUNICIPALIDAD DE CUENCA", "MIEMPRESA", "ETAPA"):
        db.agregar_cliente(nombre)
    db.agregar_vehiculo("AB1234", "CAMIONETA", "TENELEMA OCHOA JUAN PABLO")
    db.set_distancia("MACAS", 242, 6.0)
    db.set_distancia("AZOGUES", 32, 0.67)

    cab = {"responsable": "PERSONAL DE EJEMPLO DOS", "cliente_proyecto": "MIEMPRESA",
           "placa": "AB1234  CAMIONETA", "observaciones": "", "recibo_viatico": "",
           "recibo_viatico_2": "", "recibo_viatico_3": ""}
    for n in range(3):
        dia = "2026-09-%02d" % (10 + n)
        db.guardar_viaje(cab, [_fila_viaje(nombre_empleado="PERSONAL DE EJEMPLO DOS",
                                           fecha_salida=dia, hora_salida="08:00",
                                           fecha_regreso=dia, hora_regreso="18:00",
                                           lugar_trabajo="MACAS", km=242, total=45.5,
                                           valor_cajero=45.5, es_encargado=1)])
    db.registrar_bitacora("prueba", "PRUEBA DE RENDIMIENTO", "viáticos", "-", "datos falsos")
    bd.reiniciar_estadisticas()          # los contadores se cuentan desde aquí


def _mediciones(nombre, funcion, filas, ms_conexion):
    """Cronometra una acción y anota lo que costó."""
    import bd

    bd.reiniciar_estadisticas()
    t0 = time.perf_counter()
    try:
        funcion()
        error = ""
    except Exception as ex:              # una acción que falla no debe parar la medición
        error = "%s: %s" % (type(ex).__name__, ex)
    ms = (time.perf_counter() - t0) * 1000
    est = bd.estadisticas()
    consultas = int(est["consultas"])
    conex = int(est["aperturas"])
    ahorro = max(0.0, (consultas - conex) * ms_conexion)
    filas.append({"accion": nombre, "ms": ms, "consultas": consultas,
                  "conex": conex, "ahorro": ahorro, "error": error})
    print("  %-42s %7.1f ms · %2d consulta(s) · %d conexión(es)%s"
          % (nombre, ms, consultas, conex, ("  ⚠ " + error) if error else ""))


def _simular_latencia(ms):
    """Hace que abrir una conexión cueste lo que cuesta contra el servidor central.

    En la red local, cada conexión nueva al servidor significa un saludo completo
    (TCP + usuario + clave): entre 15 y 40 ms que el usuario siente como pausa. Con esto
    se puede ver, en esta misma máquina, cómo se sentía antes y cómo se siente ahora.
    """
    import bd

    original = bd._abrir_cruda

    def abrir():
        time.sleep(ms / 1000.0)
        return original()

    bd._abrir_cruda = abrir


def _tabla(filas):
    """Imprime el cuadro final."""
    print("\n" + "=" * 96)
    print("%-42s %10s %10s %8s %10s" % ("ACCIÓN", "ms", "consultas", "conex.", "ahorro ms"))
    print("-" * 96)
    for f in filas:
        print("%-42s %10.1f %10d %8d %10.1f"
              % (f["accion"], f["ms"], f["consultas"], f["conex"], f["ahorro"]))
    print("-" * 96)
    print("%-42s %10.1f %10d %8d %10.1f"
          % ("TOTAL", sum(f["ms"] for f in filas), sum(f["consultas"] for f in filas),
             sum(f["conex"] for f in filas), sum(f["ahorro"] for f in filas)))


def _comparar(ahora, antes):
    """Compara las dos vueltas, acción por acción."""
    print("\n" + "=" * 96)
    print("%-42s %12s %12s %10s" % ("ACCIÓN", "antes ms", "ahora ms", "se ahorra"))
    print("-" * 96)
    for f, a in zip(ahora, antes):
        print("%-42s %12.1f %12.1f %10.1f"
              % (f["accion"], a["ms"], f["ms"], max(0.0, a["ms"] - f["ms"])))
    print("-" * 96)
    ta = sum(a["ms"] for a in antes)
    th = sum(f["ms"] for f in ahora)
    ca = sum(a["conex"] for a in antes)
    ch = sum(f["conex"] for f in ahora)
    print("%-42s %12.1f %12.1f %10.1f" % ("TOTAL", ta, th, max(0.0, ta - th)))
    print("\nConexiones abiertas: antes %d · ahora %d" % (ca, ch))
    if ta:
        print("Tiempo total: antes %.0f ms · ahora %.0f ms (%.0f %% menos)"
              % (ta, th, 100.0 * (ta - th) / ta))


def _una_vuelta(usuario, filas, ms_conexion, servidor):
    """Mide las acciones del día (arma las ventanas y las usa, como la gente)."""
    import database as db
    import q_admin
    import q_ajustes
    import q_viaje

    caja = {}

    def guardar_ventana(clave, fabrica):
        caja[clave] = fabrica()

    print("\nAcción                                     tiempo    consultas  conexiones")
    print("-" * 82)
    _mediciones("abrir la ventana de Viáticos",
                lambda: guardar_ventana("v", lambda: q_viaje.ViajeWindow(usuario=usuario)),
                filas, ms_conexion)
    ventana = caja.get("v")
    if ventana is not None:
        _mediciones("elegir provincia (AZUAY)",
                    lambda: ventana.cb_provincia.set_valor("AZUAY"), filas, ms_conexion)
        _mediciones("elegir cantón (MACAS)",
                    lambda: ventana.cb_canton.set_valor("MACAS"), filas, ms_conexion)
        _mediciones("abrir la lista de cantones",
                    lambda: ventana.cb_canton.showPopup(), filas, ms_conexion)
        _mediciones("estimar el viaje (botón del formulario)",
                    lambda: ventana._estimar_manual(), filas, ms_conexion)
        _mediciones("teclear los km (recalcula horas)",
                    lambda: ventana.txt_km.setText("242"), filas, ms_conexion)
        _mediciones("refrescar el historial",
                    lambda: ventana.refrescar_historial(), filas, ms_conexion)
        _mediciones("ver el detalle del primero",
                    lambda: (ventana.tabla_hist.selectRow(0), ventana._ver_detalle()),
                    filas, ms_conexion)

    _mediciones("abrir Parámetros y catálogos",
                lambda: guardar_ventana("admin", lambda: q_admin.AdminWindow(usuario=usuario)),
                filas, ms_conexion)
    admin = caja.get("admin")
    if admin is not None:
        _mediciones("elegir provincia en Rutas",
                    lambda: admin.cb_prov_ruta.set_valor("MORONA SANTIAGO"), filas, ms_conexion)
        _mediciones("elegir cantón en Rutas (km y horas)",
                    lambda: admin.cb_canton_ruta.set_valor("MACAS"), filas, ms_conexion)

    _mediciones("abrir la ventana de Justificación",
                lambda: guardar_ventana("ajustes", lambda: q_ajustes.AjustesWindow(usuario=usuario)),
                filas, ms_conexion)

    if not servidor:
        cab = {"responsable": "PERSONAL DE EJEMPLO DOS",
               "cliente_proyecto": "MIEMPRESA", "placa": "AB1234  CAMIONETA",
               "observaciones": "", "recibo_viatico": "", "recibo_viatico_2": "",
               "recibo_viatico_3": ""}
        nueva = _fila_viaje(nombre_empleado="PERSONAL DE EJEMPLO SEIS",
                            fecha_salida="2026-09-30", hora_salida="07:00",
                            fecha_regreso="2026-09-30", hora_regreso="19:00",
                            lugar_trabajo="AZOGUES", km=32, total=20.0,
                            valor_cajero=20.0, es_encargado=1)
        _mediciones("guardar un viático (base)",
                    lambda: db.guardar_viaje(cab, [nueva]), filas, ms_conexion)
        if ventana is not None:
            _mediciones("ir al historial después de guardar",
                        lambda: (ventana.refrescar_historial(), ventana._ver_detalle()),
                        filas, ms_conexion)
    return filas


def main():
    try:                                  # que los acentos salgan bien en la consola
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    servidor = "--servidor" in sys.argv
    ms_conexion = 20.0
    latencia = 0.0
    for argumento in sys.argv:
        if argumento.startswith("--ms-conexion="):
            ms_conexion = float(argumento.split("=", 1)[1])
        elif argumento.startswith("--simular-conexion="):
            latencia = float(argumento.split("=", 1)[1])
    temp = _empieza_entorno(servidor)

    import configuracion as cfg
    import database as db
    import q_admin
    import q_ajustes
    import q_login
    import q_viaje
    import qt_comunes as C

    q_login.crear_app()
    # Los avisos son ventanas que esperan un clic: en la prueba se reemplazan por nada.
    C.informar = lambda *a, **k: None
    C.aviso = lambda *a, **k: None
    C.error = lambda *a, **k: None
    C.confirmar = lambda *a, **k: True

    if not servidor:
        _sembrar_datos()

    print("Base de la medición: %s" % cfg.describir())
    if servidor:
        print("Modo servidor: solo se lee (el paso de guardar se omite).")
    if latencia:
        print("Se suman %.0f ms a cada conexión nueva (como contra el servidor central)."
              % latencia)

    usuario = {"nombre": "JUSTIFICA1", "usuario": "justifica1", "rol": db.ROL_SUPER}
    comparar = "--comparar" in sys.argv

    if latencia:
        _simular_latencia(latencia)
    filas = []
    if comparar:
        # La misma vuelta, pero abriendo una conexión por consulta (como era antes).
        os.environ["VIATICOS_SIN_RESERVA"] = "1"
        print("\n--- Cómo era ANTES (una conexión por consulta) ---")
        antes = _una_vuelta(usuario, [], ms_conexion, servidor)
        print("\n--- Cómo está AHORA (la conexión se reutiliza) ---")
        os.environ.pop("VIATICOS_SIN_RESERVA", None)
        filas = _una_vuelta(usuario, filas, ms_conexion, servidor)
    else:
        filas = _una_vuelta(usuario, filas, ms_conexion, servidor)

    _tabla(filas)
    if comparar:
        _comparar(filas, antes)

    consultas = sum(f["consultas"] for f in filas)
    conex = sum(f["conex"] for f in filas)
    ahorro = sum(f["ahorro"] for f in filas)
    print("\nConsultas: %d   ·   conexiones abiertas: %d   (antes: una por consulta)"
          % (consultas, conex))
    print("Ahorro estimado con %.1f ms por conexión: %.0f ms (~%.2f s) en estas %d acciones"
          % (ms_conexion, ahorro, ahorro / 1000.0, len(filas)))
    fallas = [(f["accion"], f["error"]) for f in filas if f["error"]]
    print("\n%s" % ("FALLA  %s" % fallas if fallas
                    else "OK    Todas las acciones se completaron sin errores"))
    print("%s" % ("OK    La conexión se reutiliza (%d conexión(es) para %d consultas)"
                  % (conex, consultas) if consultas and conex <= 2
                  else "OJO   Se abrieron más conexiones de las esperadas"))

    db.cerrar_conexiones()
    if temp:
        import shutil
        shutil.rmtree(temp, ignore_errors=True)
        print("(La base de prueba se creó y se borró en %s: los datos de trabajo no se "
              "tocaron.)" % temp)
    return 0


if __name__ == "__main__":
    sys.exit(main())

