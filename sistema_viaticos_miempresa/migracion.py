# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""migracion.py — Lleva los datos locales (SQLite) a la base central (PostgreSQL).

Se usa desde la pantalla «Conexión / Base de datos» del superusuario, o desde la
consola con:  python migracion.py

Qué copia:
  - empleados, vehículos, parámetros, provincias, cantones, distancias, clientes,
    usuarios, secuencias;
  - viáticos con sus ajustes, justificaciones y gastos;
  - la bitácora (informe de actividad);
  - los respaldos: si localmente están en carpeta, se leen los archivos y se
    guardan dentro de la base central (o en la carpeta configurada).

No borra nada del equipo: solo lee la base local y escribe en la central.
Antes de escribir, vacía las tablas de la central para que el resultado sea una
copia exacta (pida confirmación desde la pantalla).
"""
import os
import sqlite3
import sys
from pathlib import Path

import bd
import configuracion as cfg

TABLAS = ["empleados", "vehiculos", "parametros", "provincias", "cantones", "distancias",
          "clientes", "usuarios", "viajes", "ajustes", "gastos", "respaldos", "bitacora",
          "seq"]


def _conectar_sqlite_local() -> sqlite3.Connection:
    ruta = cfg.dir_datos() / "viaticos.db"
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró la base local: {ruta}")
    conn = sqlite3.connect(str(ruta))
    conn.row_factory = sqlite3.Row
    return conn


def _columnas(conn_sqlite, tabla):
    try:
        return [f["name"] for f in conn_sqlite.execute(f"PRAGMA table_info({tabla})")]
    except sqlite3.Error:
        return []


def _reiniciar_secuencia(conn, tabla):
    """Ajusta el contador del id en PostgreSQL tras copiar con ids explícitos.

    Solo se hace en las tablas que tienen columna `id`. Es importante comprobarlo
    ANTES: si el `setval` falla (por ejemplo en `seq` o en `distancias`, que no
    tienen `id`), PostgreSQL deja la transacción en error y **se pierde todo lo
    que se acababa de copiar de esa tabla** (así se perdieron los contadores en la
    primera migración, y por eso un viático nuevo repitió el N° 001/2026).
    """
    if not bd.es_postgres():
        return
    try:
        fila = conn.execute("SELECT 1 FROM information_schema.columns "
                            "WHERE table_name=? AND column_name='id'",
                            (tabla,)).fetchone()
        if not fila:
            return
        conn.execute(f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                     f"COALESCE((SELECT MAX(id) FROM {tabla}), 1))")
    except Exception as ex:
        print(f"No se pudo reiniciar el contador de {tabla}: {ex}")


def _existe_tabla(conn, tabla):
    try:
        if bd.es_postgres():
            fila = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_name=?",
                                (tabla,)).fetchone()
        else:
            fila = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                (tabla,)).fetchone()
        return bool(fila)
    except Exception:
        return False


def migrar(destino_postgres=True, incluir_respaldos=True, progreso=None):
    """Copia la base local a la central. Devuelve un resumen (dict)."""
    def avisar(texto):
        if progreso:
            progreso(texto)

    if not bd.es_postgres():
        raise RuntimeError("La configuración actual no apunta a la base central "
                           "(config.json → \"motor\": \"postgres\").")

    import database as db          # se importa aquí para evitar ciclos
    avisar("Preparando la base central (tablas y catálogos)…")
    db.init_db()

    origen = _conectar_sqlite_local()
    conn = bd.conectar()
    existentes = [t for t in TABLAS if _existe_tabla(conn, t)]

    # 1) Vaciar la base central. TRUNCATE ... CASCADE resuelve las dependencias
    #    (provincias/cantones, viajes/ajustes) sin dejar la transacción a medias.
    avisar("Vaciando la base central para dejar una copia exacta…")
    with conn:
        if bd.es_postgres():
            if existentes:
                conn.execute("TRUNCATE " + ", ".join(existentes) + " RESTART IDENTITY CASCADE")
        else:
            for tabla in reversed(existentes):
                conn.execute(f"DELETE FROM {tabla}")

    # 2) Copiar en orden de dependencias (padres primero).
    resumen = {}
    for tabla in TABLAS:
        if tabla not in existentes:
            continue
        cols = _columnas(origen, tabla)
        if not cols:
            continue
        filas = [dict(f) for f in origen.execute(f"SELECT * FROM {tabla}")]
        if tabla == "respaldos" and not incluir_respaldos:
            filas = []
        with conn:
            for fila in filas:
                datos = {k: fila.get(k) for k in cols if k != "contenido"}
                if tabla == "respaldos":
                    datos["contenido"] = _contenido_respaldo(fila)
                columnas = [c for c in cols if c in datos]
                marcas = ", ".join("?" * len(columnas))
                conn.execute(f"INSERT INTO {tabla}({', '.join(columnas)}) "
                             f"VALUES ({marcas})",
                             [datos[c] for c in columnas])
            _reiniciar_secuencia(conn, tabla)
        # Comprobación: si algo falló y la transacción se deshizo, se avisa con un
        # error claro en vez de dejar la base central a medias en silencio (eso fue
        # lo que pasó con los contadores de la tabla `seq`).
        copiadas = int(conn.execute(f"SELECT COUNT(*) AS n FROM {tabla}").fetchone()["n"])
        if copiadas != len(filas):
            raise RuntimeError(
                f"La tabla «{tabla}» quedó con {copiadas} registro(s) en la base "
                f"central en vez de {len(filas)}: la copia no se completó.")
        resumen[tabla] = len(filas)
        avisar(f"{tabla}: {len(filas)} registro(s) copiados")
    origen.close()
    conn.close()
    return resumen


def _contenido_respaldo(fila):
    """Bytes del archivo (si está en carpeta se lee del disco)."""
    contenido = fila.get("contenido")
    if contenido:
        return bytes(contenido)
    ruta = fila.get("ruta") or ""
    if ruta and os.path.exists(ruta):
        return Path(ruta).read_bytes()
    return None


def resumen_local():
    """Cuenta los registros de la base local (para mostrarlos antes de migrar)."""
    try:
        origen = _conectar_sqlite_local()
    except FileNotFoundError as ex:
        return {"error": str(ex)}
    datos = {}
    for tabla in TABLAS:
        try:
            datos[tabla] = origen.execute(f"SELECT COUNT(*) AS n FROM {tabla}").fetchone()["n"]
        except sqlite3.Error:
            datos[tabla] = 0
    origen.close()
    return datos


if __name__ == "__main__":
    print("Conexión de destino:", cfg.describir())
    print("Datos locales:", resumen_local())
    if "--si" in sys.argv:
        print(migrar(progreso=print))
    else:
        print("Agregue --si para ejecutar la migración.")

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
