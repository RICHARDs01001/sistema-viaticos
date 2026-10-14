# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""bd.py — Capa de conexión: SQLite (local) o PostgreSQL (servidor central).

La aplicación habla siempre por aquí, así que toda la lógica existente sigue
igual: las mismas funciones de `database.py` funcionan con la base local o con
la base central del servidor.

Qué hace esta capa:
  - Abre la conexión que corresponda según `configuracion.motor()`.
  - Traduce los detalles que cambian entre motores (parámetros `?`, `INSERT OR
    IGNORE`, `GROUP_CONCAT`, `date()`, `datetime('now','localtime')`, ...).
  - Devuelve filas que se comportan como diccionario en los dos motores
    (`fila["columna"]`), igual que antes con SQLite.
  - **Reutiliza la conexión**: se abre una sola vez y se va prestando (ver `conectar`).
    Antes cada consulta abría y cerraba la suya, y contra el servidor central eso
    significa negociar de nuevo (red + usuario + clave) cada vez: era lo que hacía que
    la pantalla se sintiera lenta al elegir provincia, cantón o al guardar.
"""
import os
import re
import sqlite3
import threading
import time

import configuracion as cfg

SQLITE = "sqlite"
POSTGRES = "postgres"

# Expresión de "ahora" con el mismo formato de texto que se usaba en SQLite.
AHORA = {
    SQLITE: "datetime('now','localtime')",
    POSTGRES: "to_char(now(), 'YYYY-MM-DD HH24:MI:SS')",
}


class ErrorConexion(Exception):
    """Error de conexión o de configuración de la base de datos."""


# ------------------------------------------------------- reutilizar la conexión
# Antes, cada consulta abría y cerraba su propia conexión. Contra el servidor central
# eso significa negociar de nuevo (red + usuario + clave) en cada consulta, y como la
# pantalla consulta muchas veces por tecleo (los parámetros, los km del cantón, las
# listas de empleados y clientes...), se notaba la pausa: «se queda pensando».
# Ahora la conexión se abre una sola vez y se va **prestando**: la consulta que la pide
# la devuelve al terminar y se vuelve a usar. Da igual escribir `conn = conectar()` que
# `with conectar() as conn:`: todo sigue igual, solo que sin volver a conectarse.
_RESERVA = {}                     # (base, hilo) → {"conn", "motor", "en_uso", "desde"}
_CANDADO = threading.RLock()
# Si la conexión estuvo tanto tiempo sin usarse, se prueba con un «SELECT 1» antes de
# prestartla: los cortafuegos y el propio servidor suelen cortar las conexiones que
# quedan quietas, y es mejor darse cuenta antes que fallar justo al guardar.
_QUIETA_SEGUNDOS = 20
_ESTADISTICAS = {"aperturas": 0, "reusos": 0, "consultas": 0, "espera_seg": 0.0}


def estadisticas() -> dict:
    """Cuántas conexiones se abrieron, cuántas se reutilizaron y cuántas consultas van.

    Sirve para medir el rendimiento (`pruebas_rendimiento.py`) y para revisar que el
    sistema no esté abriendo conexiones de más.
    """
    return dict(_ESTADISTICAS)


def reiniciar_estadisticas():
    """Deja los contadores en cero."""
    _ESTADISTICAS.update({"aperturas": 0, "reusos": 0, "consultas": 0, "espera_seg": 0.0})


def _reserva_activa() -> bool:
    """¿Se reutiliza la conexión?

    Se puede desactivar con la variable de entorno `VIATICOS_SIN_RESERVA=1`: sirve solo
    para **medir** (`pruebas_rendimiento.py --comparar`) cómo era antes, cuando cada
    consulta abría y cerraba su propia conexión.
    """
    return not os.environ.get("VIATICOS_SIN_RESERVA")


def _clave_base():
    """Identifica a qué base se apunta: si cambia la conexión, se abre otra."""
    if cfg.motor() == POSTGRES:
        d = cfg.leer().get("postgres", {}) or {}
        return (POSTGRES, str(d.get("host", "")), str(d.get("puerto", "")),
                str(d.get("base", "")), str(d.get("usuario", "")))
    return (SQLITE, str(cfg.dir_datos() / "viaticos.db"))


def cerrar_reserva():
    """Cierra las conexiones guardadas (al cambiar de servidor o al salir del sistema)."""
    with _CANDADO:
        guardadas = list(_RESERVA.values())
        _RESERVA.clear()
    for datos in guardadas:
        try:
            datos["conn"].close()
        except Exception:
            pass


def _probar_si_estuvo_quieta(clave, conn) -> bool:
    """Prueba la conexión guardada si pasó mucho tiempo sin usarse.

    Devuelve False si ya no sirve (el servidor o un cortafuegos la cortó): en ese caso
    se da de baja para que el sistema abra otra, en vez de fallar al guardar.
    """
    if not clave:
        return True
    with _CANDADO:
        datos = _RESERVA.get(clave)
        if datos is None or datos.get("conn") is not conn:
            return True
        desde = datos.get("desde") or 0.0
    if time.monotonic() - desde < _QUIETA_SEGUNDOS:
        return True
    try:
        if motor() == POSTGRES:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.close()
        else:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        _olvidar_de_reserva(clave, conn)
        return False


def _olvidar_de_reserva(clave, conn):
    """Da de baja una conexión que ya no sirve."""
    with _CANDADO:
        datos = _RESERVA.get(clave)
        if datos is not None and datos.get("conn") is conn:
            del _RESERVA[clave]
    try:
        conn.close()
    except Exception:
        pass


# ----------------------------------------------------------------- utilidades
def motor() -> str:
    return cfg.motor()


def es_postgres() -> bool:
    return motor() == POSTGRES


def ahora() -> str:
    """Expresión SQL para la fecha y hora actual, en formato de texto."""
    return AHORA[motor()]


def agrupar(columna, separador=","):
    """Concatena varios valores en una columna (GROUP_CONCAT / STRING_AGG)."""
    if es_postgres():
        return f"STRING_AGG(DISTINCT {columna}, '{separador}')"
    return f"GROUP_CONCAT(DISTINCT {columna})"


def fecha_dia(expresion):
    """Solo la parte de fecha de un texto 'YYYY-MM-DD HH:MM:SS'."""
    return f"substr({expresion}, 1, 10)"


def insert_ignorar(tabla, columnas, conflicto=None):
    """INSERT que no falla si la fila ya existe (sirve en los dos motores)."""
    marcas = ", ".join("?" * len(columnas))
    objetivo = f" ({conflicto})" if conflicto else ""
    return (f"INSERT INTO {tabla}({', '.join(columnas)}) VALUES ({marcas}) "
            f"ON CONFLICT{objetivo} DO NOTHING")


def insert_actualizar(tabla, columnas, clave, actualizar=None):
    """INSERT que actualiza la fila si ya existe (ON CONFLICT DO UPDATE)."""
    marcas = ", ".join("?" * len(columnas))
    campos = actualizar or [c for c in columnas if c not in clave]
    sets = ", ".join(f"{c}=excluded.{c}" for c in campos)
    return (f"INSERT INTO {tabla}({', '.join(columnas)}) VALUES ({marcas}) "
            f"ON CONFLICT ({', '.join(clave)}) DO UPDATE SET {sets}")


def _a_postgres(sql: str) -> str:
    """Adapta el SQL escrito para SQLite al dialecto de PostgreSQL."""
    # Los '%' escritos dentro del SQL (por ejemplo en un LIKE '%algo%') deben ir
    # dobles, porque psycopg2 usa el '%' como marca de parámetro. Se hace ANTES
    # de cambiar los '?' para no estropear los '%s' que se crean después.
    sql = sql.replace("%", "%%")
    sql = sql.replace("?", "%s")
    sql = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", sql, flags=re.I)
    sql = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", sql, flags=re.I)
    if re.match(r"\s*INSERT\s+INTO", sql, flags=re.I) and "ON CONFLICT" not in sql.upper():
        partes = re.split(r"\bRETURNING\b", sql, flags=re.I)
        sql = partes[0].rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
        if len(partes) > 1:
            sql += " RETURNING " + partes[1]
    sql = re.sub(r"\bdatetime\s*\(\s*'now'\s*,\s*'localtime'\s*\)",
                 "to_char(now(), 'YYYY-MM-DD HH24:MI:SS')", sql, flags=re.I)
    sql = re.sub(r"GROUP_CONCAT\s*\(\s*DISTINCT\s+([^()]+?)\s*\)",
                 r"STRING_AGG(DISTINCT \1, ',')", sql, flags=re.I)
    sql = re.sub(r"GROUP_CONCAT\s*\(\s*([^()]+?)\s*\)", r"STRING_AGG(\1, ',')",
                 sql, flags=re.I)
    sql = re.sub(r"\bdate\s*\(\s*([^()]+?)\s*\)", r"substr(\1, 1, 10)", sql, flags=re.I)
    return sql


# ------------------------------------------------------------------- cursor
class Cursor:
    """Resultado ya materializado: se comporta igual en los dos motores."""

    def __init__(self, filas=None, rowcount=None, ultimo_id=None):
        self._filas = list(filas or [])
        self._i = 0
        self.rowcount = len(self._filas) if rowcount is None else rowcount
        self.lastrowid = ultimo_id

    def fetchone(self):
        if self._i < len(self._filas):
            fila = self._filas[self._i]
            self._i += 1
            return fila
        return None

    def fetchall(self):
        restantes = self._filas[self._i:]
        self._i = len(self._filas)
        return restantes

    def __iter__(self):
        return iter(self.fetchall())


# ----------------------------------------------------------------- conexión
class Conexion:
    """Conexión a la base de datos, con la misma forma que la de SQLite."""

    def __init__(self, motor_, conn, clave=None, prestada=False):
        self.motor = motor_
        self._conn = conn
        self._cerrada = False
        # `prestada`: la conexión viene de la reserva, así que al terminar se devuelve
        # (no se cierra) para que la siguiente consulta la vuelva a usar.
        self._prestada = bool(prestada)
        self._clave = clave

    def _viva(self):
        """Devuelve la conexión lista para usar (pide otra si ya no sirve)."""
        if self._cerrada or self._conn is None:
            self._tomar()
        elif not self._sirve_todavia():
            self._tomar()
        return self._conn

    def _tomar(self):
        """Toma una conexión: de la reserva si hay una libre, o abre una nueva."""
        nueva = conectar()
        self._conn = nueva._conn
        self.motor = nueva.motor
        self._prestada = nueva._prestada
        self._clave = nueva._clave
        self._cerrada = False

    def _sirve_todavia(self) -> bool:
        """¿La conexión guardada todavía sirve?"""
        if self._conn is None:
            return False
        if self.motor == POSTGRES and getattr(self._conn, "closed", 0):
            return False
        return _probar_si_estuvo_quieta(self._clave, self._conn)

    # -- ejecución ----------------------------------------------------
    def execute(self, sql, params=()):
        conn = self._viva()
        inicio = time.perf_counter()
        try:
            if self.motor == POSTGRES:
                cur = conn.cursor()
                cur.execute(_a_postgres(sql), tuple(params or ()))
                filas = list(cur.fetchall()) if cur.description else []
                ultimo = None
                desc = getattr(cur, "description", None)
                if desc and len(desc) == 1 and desc[0][0] == "id" and filas:
                    ultimo = filas[0]["id"]
                return Cursor(filas, cur.rowcount, ultimo)
            cur = conn.execute(sql, tuple(params or ()))
            filas = list(cur.fetchall()) if cur.description else []
            return Cursor(filas, cur.rowcount, cur.lastrowid)
        except Exception:
            self._dejar_sana()
            raise
        finally:
            _ESTADISTICAS["consultas"] += 1
            _ESTADISTICAS["espera_seg"] += time.perf_counter() - inicio

    def executemany(self, sql, secuencia):
        conn = self._viva()
        try:
            if self.motor == POSTGRES:
                cur = conn.cursor()
                cur.executemany(_a_postgres(sql), [tuple(p or ()) for p in secuencia])
                return Cursor([], cur.rowcount)
            cur = conn.executemany(sql, [tuple(p or ()) for p in secuencia])
            return Cursor([], cur.rowcount, cur.lastrowid)
        except Exception:
            self._dejar_sana()
            raise

    def _dejar_sana(self):
        """Deja la conexión sana después de una consulta que falló.

        En PostgreSQL un error deja la transacción en mal estado y, como la conexión
        ahora se comparte, sin esto fallarían todas las consultas siguientes.
        """
        if self.motor == POSTGRES and self._conn is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def executescript(self, script):
        """Crea el esquema completo (varias sentencias separadas por ';')."""
        if self.motor != POSTGRES:
            self._viva().executescript(script)
            return
        conn = self._viva()
        for sentencia in [s.strip() for s in script.split(";")]:
            if sentencia:
                conn.cursor().execute(sentencia)

    # -- transacción --------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        try:
            if tipo is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False

    def commit(self):
        if self._conn is not None and not self._cerrada:
            self._conn.commit()

    def rollback(self):
        if self._conn is not None and not self._cerrada:
            self._conn.rollback()

    def close(self):
        """Termina la consulta: devuelve la conexión a la reserva, o la cierra de verdad.

        Lo que no se haya confirmado (`commit`) se pierde, igual que antes: cerrar a
        medias no deja nada a medio grabar.
        """
        if self._conn is not None and not self._cerrada:
            if self._prestada:
                self._devolver()
            else:
                try:
                    self._conn.close()
                except Exception:
                    pass
        self._cerrada = True

    def _devolver(self):
        """Deja la conexión lista para el siguiente que la pida."""
        conn = self._conn
        pendiente = True
        if self.motor == POSTGRES:
            try:
                estado = getattr(getattr(conn, "info", None), "transaction_status", None)
                # 0 = sin transacción abierta, 2 = en curso, 3 = con error
                pendiente = estado not in (0, 1, 4)
            except Exception:
                pendiente = True
        try:
            if pendiente:
                conn.rollback()          # lo que quedó a medias se deshace
        except Exception:
            _olvidar_de_reserva(self._clave, conn)
            return
        with _CANDADO:
            datos = _RESERVA.get(self._clave)
            if datos is not None and datos.get("conn") is conn:
                datos["en_uso"] = False
                datos["desde"] = time.monotonic()

    # -- utilidades ---------------------------------------------------
    def proximo_valor(self, nombre):
        """Incrementa y devuelve un contador (atómico: seguro con 5 máquinas).

        El incremento se hace con un UPDATE ... RETURNING, que bloquea la fila
        solo durante la transacción en curso; el contador nunca se repite.
        """
        fila = self.execute("SELECT valor FROM seq WHERE nombre=?", (nombre,)).fetchone()
        if not fila:
            self.execute(insert_ignorar("seq", ["nombre", "valor"], "nombre"), (nombre, 0))
        cur = self.execute("UPDATE seq SET valor = valor + 1 WHERE nombre=? RETURNING valor",
                           (nombre,))
        fila = cur.fetchone()
        if not fila:
            raise ErrorConexion(f"No se pudo obtener el consecutivo '{nombre}'.")
        return int(fila["valor"] if isinstance(fila, dict) else fila[0])



# ---------------------------------------------------------------- conexión
def conectar(directa=False) -> Conexion:
    """Conexión a la base configurada, lista para usar (SQLite local o PostgreSQL).

    La conexión se **reutiliza**: se abre una sola vez y se va prestando, así el
    sistema no paga el saludo al servidor (red + usuario + clave) en cada consulta.

    Con `directa=True` se abre una conexión aparte que **no** se guarda: se usa para
    probar otra dirección sin tocar la que está en uso.
    """
    if directa or not _reserva_activa():
        motor_, conn = _abrir_cruda()
        _ESTADISTICAS["aperturas"] += 1
        return Conexion(motor_, conn)
    clave = (_clave_base(), threading.get_ident())
    with _CANDADO:
        datos = _RESERVA.get(clave)
        if datos is not None and not datos.get("en_uso"):
            datos["en_uso"] = True
            _ESTADISTICAS["reusos"] += 1
            return Conexion(datos["motor"], datos["conn"], clave, prestada=True)
    return _abrir_guardada(clave)


def _abrir_guardada(clave) -> Conexion:
    """Abre la conexión y la deja guardada para las consultas siguientes."""
    motor_, conn = _abrir_cruda()
    with _CANDADO:
        anterior = _RESERVA.get(clave)
        if anterior is not None and anterior.get("conn") is not conn:
            try:                                # una conexión que quedó sin devolver
                anterior["conn"].close()
            except Exception:
                pass
        _RESERVA[clave] = {"conn": conn, "motor": motor_, "en_uso": True,
                           "desde": time.monotonic()}
    _ESTADISTICAS["aperturas"] += 1
    return Conexion(motor_, conn, clave, prestada=True)


def _abrir_cruda():
    """Abre la conexión cruda que corresponda. Devuelve (motor, conexión)."""
    if cfg.motor() == POSTGRES:
        return POSTGRES, _cruda_postgres()
    return SQLITE, _cruda_sqlite()


def _cruda_sqlite():
    """Conexión cruda de SQLite (base local)."""
    conn = sqlite3.connect(str(cfg.dir_datos() / "viaticos.db"), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error:
        pass
    return conn


def _conectar_sqlite() -> Conexion:
    """Conexión local suelta (sin guardarla en la reserva)."""
    return Conexion(SQLITE, _cruda_sqlite())


def _cruda_postgres():
    """Conexión cruda al servidor central (PostgreSQL)."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception:
        raise ErrorConexion(
            "Falta el conector de PostgreSQL (psycopg2).\n"
            "Instálelo con:  pip install psycopg2-binary\n"
            "(En el .exe ya viene incluido; vuelva a empaquetar si hace falta.)")
    d = cfg.leer().get("postgres", {})
    try:
        conn = psycopg2.connect(host=str(d.get("host", "localhost")),
                                port=int(d.get("puerto", 5432)),
                                dbname=str(d.get("base", "viaticos")),
                                user=str(d.get("usuario", "miempresa")),
                                password=str(d.get("clave", "")),
                                # Si el servidor está apagado o dormido, en vez de
                                # quedarse colgado se avisa al usuario (y la pantalla de
                                # conexión aparece antes). No se baja más para no fallar
                                # cuando el servidor está ocupado con el respaldo.
                                connect_timeout=6,
                                # La conexión queda abierta mientras se usa el sistema,
                                # así que se pide al sistema operativo que la mantenga
                                # viva: muchos cortafuegos cortan las conexiones que
                                # pasan mucho tiempo sin hablar.
                                keepalives=1, keepalives_idle=30,
                                keepalives_interval=10, keepalives_count=5,
                                application_name="Sistema Viaticos Miempresa",
                                # Si el servidor está saturado o una consulta queda
                                # bloqueada, se avisa en lugar de quedarse colgado.
                                options="-c statement_timeout=60000 -c lock_timeout=30000",
                                cursor_factory=RealDictCursor)
    except Exception as ex:
        raise ErrorConexion(
            "No se pudo conectar a la base central:\n"
            f"{d.get('usuario')}@{d.get('host')}:{d.get('puerto')}/{d.get('base')}\n\n{ex}")
    try:
        conn.autocommit = False
    except Exception:
        pass
    return conn


def _conectar_postgres() -> Conexion:
    """Conexión al servidor suelta (sin guardarla en la reserva)."""
    return Conexion(POSTGRES, _cruda_postgres())


def probar_conexion(datos=None):
    """Prueba la conexión (con los datos indicados o los actuales). (ok, mensaje)."""
    guardado = None
    if datos:
        guardado = cfg.leer()
        cfg.guardar(datos)
    try:
        conn = conectar(directa=True)      # conexión aparte: no toca la que está en uso
        try:
            if cfg.motor() == POSTGRES:
                fila = conn.execute("SELECT version() AS v").fetchone()
                version = (fila["v"] if fila else "").split(" on ")[0]
            else:
                fila = conn.execute("SELECT sqlite_version() AS v").fetchone()
                version = "SQLite " + (fila["v"] if fila else "")
        finally:
            conn.close()
        return True, f"Conexión correcta · {version}"
    except Exception as ex:
        return False, str(ex)
    finally:
        if guardado:
            cfg.guardar(guardado)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
