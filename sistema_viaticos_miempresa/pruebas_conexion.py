# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_conexion.py — Prueba de la conexión reutilizable (bd.py), SIN tocar datos reales.

Se ejecuta así:

    python pruebas_conexion.py

Trabaja con una base SQLite dentro de una carpeta temporal (se crea al empezar y se borra
al terminar), así que los datos de trabajo no se tocan.

Comprueba lo que tiene que seguir cumpliéndose desde que la conexión se reutiliza:

  - que **no** se abra una conexión por consulta (se abre una y se va prestando),
  - que cerrar y volver a pedir la conexión siga funcionando,
  - que lo que se confirma (`commit`) se guarde y lo que no, no,
  - que una consulta que falla **no** deje la conexión inservible para las siguientes,
  - que la configuración (`config.json`) se lea una sola vez,
  - y que se pueda guardar y volver a leer un viático completo.
"""
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEMP = tempfile.mkdtemp(prefix="viaticos_conexion_")
os.environ["VIATICOS_MOTOR"] = "sqlite"
os.environ["VIATICOS_DATA"] = _TEMP
os.environ["VIATICOS_RESPALDOS"] = "carpeta"

_fallos = []


def revisar(nombre, condicion, detalle=""):
    ok = bool(condicion)
    if not ok:
        _fallos.append(nombre)
    print(("OK    " if ok else "FALLA ") + nombre
          + (("  ->  %s" % (detalle,)) if detalle != "" else ""))
    return ok


def _fila_viaje(db):
    """Fila del viático con lo mínimo que la tabla exige (según su propio esquema)."""
    conn = db.conectar()
    columnas = conn.execute("PRAGMA table_info(viajes)").fetchall()
    conn.close()
    fila = {}
    for c in columnas:
        if not c["notnull"] or c["name"] in ("id", "viatico_numero", "ajuste_numero"):
            continue
        fila[c["name"]] = 0 if c["type"].upper() in ("REAL", "INTEGER", "NUMERIC") else ""
    fila.update({"nombre_empleado": "PRUEBA CONEXION", "fecha_salida": "2026-09-30",
                 "hora_salida": "08:00", "fecha_regreso": "2026-09-30",
                 "hora_regreso": "18:00", "lugar_trabajo": "CUENCA", "km": 10,
                 "total": 10.0, "valor_cajero": 0, "es_encargado": 1})
    return fila


def main():
    import bd
    import configuracion as cfg
    import database as db

    db.init_db()
    bd.reiniciar_estadisticas()

    # 1) leer varias veces no debe abrir una conexión por consulta
    db.listar_empleados()
    db.listar_empleados()
    db.cargar_parametros()
    est = bd.estadisticas()
    revisar("La conexión se reutiliza (no se abre una por consulta)",
            est["aperturas"] <= 1 and est["reusos"] >= 2, str(est))
    revisar("Los catálogos se recuerdan unos segundos (no se vuelve a consultar)",
            est["consultas"] <= 2, "%d consulta(s) para 3 lecturas" % est["consultas"])

    # 2) cerrar y volver a pedir la conexión
    conn = db.conectar()
    conn.execute("SELECT 1").fetchone()
    conn.close()
    otra = db.conectar()
    revisar("Cerrar y volver a pedir la conexión sigue funcionando",
            otra.execute("SELECT COUNT(*) AS n FROM provincias").fetchone()["n"] > 0)
    otra.close()

    # 3) lo confirmado se guarda
    db.agregar_empleado("PRUEBA CONEXION")
    revisar("Lo que se confirma (commit) queda guardado",
            "PRUEBA CONEXION" in db.listar_empleados())

    # 4) lo que no se confirma se pierde (igual que antes)
    conn = db.conectar()
    conn.execute("INSERT INTO empleados(nombre) VALUES ('NO CONFIRMADO')")
    conn.close()                       # sin commit: se descarta
    revisar("Lo que no se confirma no queda en la base",
            "NO CONFIRMADO" not in db.listar_empleados())

    # 5) una consulta que falla no daña la conexión (en PostgreSQL la dejaría «abortada»)
    try:
        db.conectar().execute("SELECT * FROM tabla_que_no_existe")
    except Exception:
        pass
    try:
        db.listar_empleados()
        revisar("Una consulta que falla no daña la conexión", True)
    except Exception as ex:
        revisar("Una consulta que falla no daña la conexión", False, str(ex))

    # 6) guardar y volver a leer un viático
    cab = {"responsable": "PRUEBA", "cliente_proyecto": "MIEMPRESA", "placa": "AB1234",
           "observaciones": "", "recibo_viatico": "", "recibo_viatico_2": "",
           "recibo_viatico_3": ""}
    numero = db.guardar_viaje(cab, [_fila_viaje(db)])
    revisar("Se guarda y se vuelve a leer un viático", bool(db.filas_numero(numero)),
            "N° %s" % numero)

    # 7) la configuración no se relee del disco en cada consulta
    cfg.leer()
    revisar("La configuración (config.json) queda en memoria", cfg._CACHE is not None,
            cfg.motor())

    bd.cerrar_reserva()
    print("\n%s" % ("TODO OK" if not _fallos else "FALLOS: %s" % _fallos))
    return 1 if _fallos else 0


if __name__ == "__main__":
    try:
        codigo = main()
    finally:
        shutil.rmtree(_TEMP, ignore_errors=True)
        print("(La base de prueba se creó y se borró en %s: los datos de trabajo no se "
              "tocaron.)" % _TEMP)
    sys.exit(codigo)
