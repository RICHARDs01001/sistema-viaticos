# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""configuracion.py — Configuración del sistema y de la conexión a la base de datos.

El sistema está pensado para trabajar con **una sola base central** (PostgreSQL en el
servidor) a la que se conectan todas las computadoras. Por eso la configuración por
defecto ya viene apuntando al servidor: **basta con copiar el `.exe` a cada
máquina**, sin llevar ningún archivo extra.

Si existe un archivo `config.json` junto al programa (o junto al `.exe`), lo que
diga ese archivo manda sobre los valores de abajo. Así se puede cambiar de servidor
sin volver a empaquetar, ya sea desde la pantalla del sistema o editando:

{
  "motor": "postgres",
  "postgres": {
    "host": "192.168.1.4", "puerto": 2345, "base": "viaticos",
    "usuario": "miempresa", "clave": "miempresa"
  },
  "respaldos": { "modo": "base", "carpeta": "" },
  "interfaz": { "zoom": 0, "dpi_consciente": true }
}

`interfaz.zoom`: 0 = automático (según la pantalla de esa PC). Si se pone 0.8,
                 0.7, 0.6… toda la letra y los controles se encogen (útil en
                 monitores chicos o con el escalado de Windows al 125 %).

`respaldos.modo`:
  - "base"    → los archivos se guardan dentro de la base central (recomendado
                cuando las máquinas no comparten una carpeta).
  - "carpeta" → los archivos se guardan en una carpeta (local o compartida) y en
                la base solo queda la ruta. `carpeta` puede ser una ruta de red
                como \\\\SERVIDOR\\viaticos_respaldos

Si la base central no responde al abrir el sistema, aparece la pantalla
«No se pudo abrir la base de datos» para escribir otra IP o para trabajar en
local (ver `ui_conexion.asegurar_conexion`).

Variables de entorno (útiles para pruebas): VIATICOS_MOTOR, VIATICOS_PG_HOST,
VIATICOS_PG_PUERTO, VIATICOS_PG_BASE, VIATICOS_PG_USUARIO, VIATICOS_PG_CLAVE,
VIATICOS_RESPALDOS, VIATICOS_RESPALDOS_DIR, VIATICOS_DATA, VIATICOS_CONFIG.
"""
import copy
import json
import os
import sys
from pathlib import Path

NOMBRE_ARCHIVO = "config.json"

# La configuración se lee del disco **una sola vez** y queda en memoria (ver `leer`).
# `_CARPETA_DATOS` hace lo mismo con la carpeta de datos locales.
_CACHE = None
_CARPETA_DATOS = None

MOTOR_SQLITE = "sqlite"
MOTOR_POSTGRES = "postgres"

# Equipo donde corre la base de datos central (el que tiene PostgreSQL encendido).
# Esta es la dirección que usan todas las máquinas que solo llevan el .exe.
SERVIDOR = "192.168.1.4"
CLAVE_SERVIDOR = "miempresa"

DEFECTO = {
    "motor": MOTOR_POSTGRES,
    "postgres": {
        "host": SERVIDOR,
        "puerto": 2345,
        "base": "viaticos",
        "usuario": "miempresa",
        "clave": CLAVE_SERVIDOR,
    },
    "respaldos": {"modo": "base", "carpeta": ""},
    "sede": "",
    # Tamaño de la interfaz (tema.py). «zoom» 0 = automático según la pantalla de
    # esta PC; si se pone 0.8, 0.7, 0.6… se encoge toda la letra y los controles.
    # «dpi_consciente» en false desactiva el aviso de escalado a Windows.
    "interfaz": {"zoom": 0, "dpi_consciente": True},
}


def carpeta_app() -> Path:
    """Carpeta donde vive la aplicación: la del código o la del .exe empaquetado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ruta_config() -> Path:
    """Ruta del archivo de configuración (se puede forzar con VIATICOS_CONFIG)."""
    forzada = os.environ.get("VIATICOS_CONFIG")
    if forzada:
        return Path(forzada)
    return carpeta_app() / NOMBRE_ARCHIVO


def ruta_config_usuario() -> Path:
    """Configuración guardada en el perfil de Windows (`%APPDATA%\\Miempresa`).

    Se usa **solo** si la carpeta del programa (o la del `.exe`) no se puede escribir:
    por ejemplo si el sistema quedó instalado dentro de «Archivos de programa» o en una
    carpeta de red de solo lectura. Así, la dirección del servidor y el tamaño de
    pantalla que se configuran la primera vez en esa computadora **igual se guardan** y
    se vuelven a leer en el siguiente arranque.
    """
    base = (os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
            or str(Path.home()))
    carpeta = Path(base) / "Miempresa"
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return carpeta / NOMBRE_ARCHIVO


def carpeta_recursos() -> Path:
    """Carpeta de los archivos que viajan DENTRO del programa (por ejemplo `excel\\`).

    Cuando el sistema corre como `.exe` de un solo archivo, PyInstaller los descomprime
    en una carpeta temporal (`sys._MEIPASS`); si corre desde el código, están junto a
    los `.py`. Se usa para la carga inicial de los catálogos (clientes y tiempos de
    viaje) que van con el programa.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", str(carpeta_app())))
    return Path(__file__).resolve().parent


def dir_datos() -> Path:
    """Carpeta de datos locales (base SQLite y respaldos en modo carpeta).

    Se resuelve **una sola vez** y queda en memoria: antes se buscaba el archivo
    `data_path.txt` y se creaba la carpeta en cada consulta a la base (y la base local
    se consulta muchas veces por segundo).
    """
    global _CARPETA_DATOS
    if _CARPETA_DATOS is not None:
        return _CARPETA_DATOS
    ruta = os.environ.get("VIATICOS_DATA")
    if not ruta:
        f = carpeta_app().parent / "data_path.txt"
        if f.exists():
            ruta = f.read_text(encoding="utf-8").strip() or None
    base = Path(ruta) if ruta else carpeta_app() / "data"
    base.mkdir(parents=True, exist_ok=True)
    _CARPETA_DATOS = base
    return base


def _mezclar(base, nuevos):
    """Combina diccionarios respetando los valores ya definidos."""
    salida = dict(base)
    for clave, valor in (nuevos or {}).items():
        if isinstance(valor, dict) and isinstance(salida.get(clave), dict):
            salida[clave] = _mezclar(salida[clave], valor)
        elif valor is not None:
            salida[clave] = valor
    return salida


def leer() -> dict:
    """Configuración completa (archivo + variables de entorno).

    Se lee **una sola vez** y queda en memoria. Antes cada consulta volvía a abrir y
    leer `config.json` del disco (se llama en cada conexión a la base y en cada
    «cálculo» de la pantalla, así que se sentía al teclear). `guardar()` refresca esta
    copia, de modo que lo que se cambie en la pantalla de conexión se ve al instante.
    """
    global _CACHE
    if _CACHE is None:
        _CACHE = _leer_del_disco()
    return copy.deepcopy(_CACHE)


def olvidar_cache():
    """Vuelve a leer del disco en la próxima consulta (si otra copia la cambió)."""
    global _CACHE, _CARPETA_DATOS
    _CACHE = None
    _CARPETA_DATOS = None


def _leer_del_disco() -> dict:
    """Lee la configuración del archivo y le encima las variables de entorno."""
    datos = dict(DEFECTO)
    ruta = ruta_config()
    if not ruta.exists():
        alterna = ruta_config_usuario()
        if alterna.exists():
            ruta = alterna
    if ruta.exists():
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8") or "{}")
            datos = _mezclar(datos, contenido)
        except Exception as ex:
            print(f"config.json ilegible ({ex}); se usa la configuración por defecto.")
    env = os.environ.get("VIATICOS_MOTOR")
    if env:
        datos["motor"] = env.strip().lower()
    pg = datos["postgres"]
    for clave, var in (("host", "VIATICOS_PG_HOST"), ("base", "VIATICOS_PG_BASE"),
                       ("usuario", "VIATICOS_PG_USUARIO"), ("clave", "VIATICOS_PG_CLAVE")):
        if os.environ.get(var):
            pg[clave] = os.environ[var].strip()
    if os.environ.get("VIATICOS_PG_PUERTO"):
        try:
            pg["puerto"] = int(os.environ["VIATICOS_PG_PUERTO"].strip())
        except ValueError:
            pass
    for clave in ("host", "base", "usuario", "clave"):
        if isinstance(pg.get(clave), str):
            pg[clave] = pg[clave].strip()
    if os.environ.get("VIATICOS_RESPALDOS"):
        datos["respaldos"]["modo"] = os.environ["VIATICOS_RESPALDOS"].strip().lower()
    if os.environ.get("VIATICOS_RESPALDOS_DIR"):
        datos["respaldos"]["carpeta"] = os.environ["VIATICOS_RESPALDOS_DIR"]
    return datos


def guardar(datos: dict):
    """Escribe la configuración en `config.json` (sin perder lo ya guardado).

    Primero se intenta junto al programa (o al `.exe`). Si esa carpeta no se puede
    escribir, se guarda en el perfil de Windows (`%APPDATA%\\Miempresa`) para que la
    configuración de esa computadora **no se pierda**.
    """
    ruta = ruta_config()
    if not ruta.exists():
        alterna = ruta_config_usuario()
        if alterna.exists():
            ruta = alterna
    actual = {}
    if ruta.exists():
        try:
            actual = json.loads(ruta.read_text(encoding="utf-8") or "{}")
        except Exception:
            actual = {}
    unido = _mezclar(_mezclar(DEFECTO, actual), datos)
    texto = json.dumps(unido, indent=2, ensure_ascii=False)
    try:
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        ruta = ruta_config_usuario()
        ruta.write_text(texto, encoding="utf-8")
    olvidar_cache()          # lo que se acaba de guardar manda desde ahora
    return ruta


def motor() -> str:
    """'sqlite' o 'postgres'."""
    m = str(leer().get("motor", MOTOR_SQLITE)).strip().lower()
    return MOTOR_POSTGRES if m in ("postgres", "postgresql", "pg", "central") else MOTOR_SQLITE


def es_postgres() -> bool:
    return motor() == MOTOR_POSTGRES


def modo_respaldos() -> str:
    """'base' (dentro de la base de datos) o 'carpeta' (archivo en disco)."""
    modo = str(leer().get("respaldos", {}).get("modo", "carpeta")).strip().lower()
    return "base" if modo in ("base", "bd", "db") else "carpeta"


def carpeta_respaldos() -> Path:
    """Carpeta donde se guardan los respaldos (local o compartida)."""
    ruta = (leer().get("respaldos", {}).get("carpeta") or "").strip()
    base = Path(ruta) if ruta else dir_datos() / "respaldos"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return base


def describir() -> str:
    """Texto corto para mostrar en la pantalla de conexión."""
    d = leer()
    if str(d.get("motor", "")).strip().lower() != MOTOR_POSTGRES:
        return f"Base LOCAL (SQLite): {dir_datos() / 'viaticos.db'}"
    pg = d["postgres"]
    extra = ("respaldos dentro de la base" if modo_respaldos() == "base"
             else f"respaldos en {carpeta_respaldos()}")
    return (f"Base CENTRAL PostgreSQL: {pg['usuario']}@{pg['host']}:{pg['puerto']}/"
            f"{pg['base']} · {extra}")

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
