# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""empaquetar_servidor.py — Deja el programa apuntando al servidor nuevo y lo empaqueta.

Se llama desde EMPAQUETAR_EXE_SERVIDOR.bat (o a mano). Hace tres cosas:

  1. Deja la IP y el puerto como VALOR DE FÁBRICA en `configuracion.py` (respaldo
     `configuracion.py.bak`): así el `.exe` sale apuntando al servidor por sí solo
     y a las otras PC se copia **únicamente** `dist\\Sistema_Viaticos.exe`.
     Se puede omitir con --sin-fabrica.
  2. Corre PyInstaller con `Sistema_Viaticos.spec` y deja el `.exe` en `dist\\`.
  3. Escribe `dist\\config.json.EJEMPLO`: es SOLO una referencia para revisar la
     dirección (el programa lo ignora). A propósito NO se crea `config.json`, porque
     si se copiara a otra PC pisaría el de esa computadora y le cambiaría el **zoom**
     (el tamaño de pantalla es de cada PC, no del sistema). Si ya existía un
     `dist\\config.json`, el script avisa y con --limpiar-config lo borra.

Uso:
    python empaquetar_servidor.py 192.168.1.123 5432                    empaqueta
    python empaquetar_servidor.py 192.168.1.123 5432 --sin-fabrica      no toca configuracion.py
    python empaquetar_servidor.py 192.168.1.123 5432 --solo-config      NO empaqueta: solo el config.json
    python empaquetar_servidor.py 192.168.1.123 5432 --simular          solo muestra lo que haría

Opciones: --clave · --usuario · --base · --dist <carpeta> · --forzar
    --forzar  permite una IP terminada en .1 (que normalmente es el router).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CONFIGURACION = AQUI / "configuracion.py"
SPEC = AQUI / "Sistema_Viaticos.spec"
NOMBRE_EXE = "Sistema_Viaticos.exe"
NOMBRE_CONFIG = "config.json"
NOMBRE_EJEMPLO = "config.json.EJEMPLO"


def ip_valida(texto):
    partes = str(texto).split(".")
    return len(partes) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in partes)


def buscar(patron, texto, defecto=""):
    m = re.search(patron, texto, re.M)
    return m.group(1) if m else defecto


def escribir_ejemplo(carpeta, datos, simular):
    """Deja la dirección en un archivo de REFERENCIA (el programa NO lee este archivo).

    No se crea `config.json` a propósito: ese archivo es de cada computadora y guarda
    también el zoom de esa PC, así que copiarlo de una máquina a otra le cambiaría el
    tamaño de pantalla a la otra.
    """
    archivo = Path(carpeta) / NOMBRE_EJEMPLO
    if simular:
        print("   [simulado] escribiría %s (solo referencia)" % archivo)
        print("              motor=%s · host=%s · puerto=%s"
              % (datos["motor"], datos["postgres"]["host"], datos["postgres"]["puerto"]))
        return archivo
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("   referencia escrita en: %s" % archivo)
    print("   (NO se crea config.json: ese archivo es de cada PC, ahí va también su zoom)")
    return archivo


def cambiar_fabrica(ip, puerto, clave, simular):
    """Deja la IP y el puerto como valores de fábrica en configuracion.py."""
    try:
        texto = CONFIGURACION.read_text(encoding="utf-8")
    except OSError as ex:
        print("   *** No se pudo leer %s (%s)" % (CONFIGURACION.name, ex))
        return False
    ip_vieja = buscar(r'^SERVIDOR\s*=\s*"([^"]*)"', texto)
    clave_vieja = buscar(r'^CLAVE_SERVIDOR\s*=\s*"([^"]*)"', texto)

    nuevo, cambios = re.subn(r'^SERVIDOR\s*=\s*".*?"', 'SERVIDOR = "%s"' % ip, texto, flags=re.M)
    if ip_vieja:
        nuevo = nuevo.replace('"%s"' % ip_vieja, '"%s"' % ip)   # también el ejemplo del comentario
    nuevo, n = re.subn(r'"puerto":\s*\d+', '"puerto": %d' % puerto, nuevo)
    cambios += n
    if clave and clave != clave_vieja:
        nuevo, n = re.subn(r'^CLAVE_SERVIDOR\s*=\s*".*?"',
                           'CLAVE_SERVIDOR = "%s"' % clave, nuevo, flags=re.M)
        if clave_vieja:
            nuevo = nuevo.replace('"%s"' % clave_vieja, '"%s"' % clave)
        cambios += n

    if cambios == 0:
        print("   configuracion.py ya estaba con esos valores (nada que cambiar).")
        return True
    if simular:
        print("   [simulado] cambiaría %d línea(s) de %s  (IP %s · puerto %d)"
              % (cambios, CONFIGURACION.name, ip, puerto))
        return True
    respaldo = CONFIGURACION.with_name(CONFIGURACION.name + ".bak")
    if not respaldo.exists():
        shutil.copyfile(str(CONFIGURACION), str(respaldo))
        print("   respaldo creado: %s" % respaldo.name)
    CONFIGURACION.write_text(nuevo, encoding="utf-8")
    print('   configuracion.py actualizado (fábrica): SERVIDOR = "%s" · puerto %d' % (ip, puerto))
    return True


def empaquetar(simular):
    if not SPEC.exists():
        print("   *** No se encontró %s" % SPEC)
        return False
    orden = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", SPEC.name]
    print("   ejecutando: %s" % " ".join(orden))
    if simular:
        print("   [simulado] no se empaqueta")
        return True
    resultado = subprocess.run(orden, cwd=str(AQUI))
    if resultado.returncode:
        print("   *** PyInstaller falló (código %d). Revise los mensajes de arriba."
              % resultado.returncode)
        return False
    print("   empaquetado listo.")
    return True


def main():
    p = argparse.ArgumentParser(description="Empaqueta el .exe apuntando al servidor nuevo.")
    p.add_argument("ip", nargs="?", help="IP del servidor (ej. 192.168.1.123)")
    p.add_argument("puerto", nargs="?", type=int, default=5432, help="puerto (por defecto 5432)")
    p.add_argument("--clave", default="miempresa")
    p.add_argument("--usuario", default="miempresa")
    p.add_argument("--base", default="viaticos")
    p.add_argument("--dist", default="dist", help="carpeta de salida (por defecto dist)")
    p.add_argument("--sin-fabrica", action="store_true",
                   help="NO tocar los valores de fábrica de configuracion.py")
    p.add_argument("--fabrica", action="store_true", help=argparse.SUPPRESS)  # ya es lo normal
    p.add_argument("--solo-config", action="store_true", help="no empaquetar: solo la referencia")
    p.add_argument("--limpiar-config", action="store_true",
                   help="borrar dist\\config.json (recomendado: no se reparte y no pisa el zoom)")
    p.add_argument("--simular", action="store_true", help="mostrar lo que haría, sin tocar nada")
    p.add_argument("--forzar", action="store_true", help="permitir una IP terminada en .1")
    a = p.parse_args()

    ip = (a.ip or "").strip()
    if not ip and sys.stdin is not None and sys.stdin.isatty():
        ip = input("IP del servidor: ").strip()
    if not ip_valida(ip):
        print("*** La IP '%s' no es válida (un ejemplo correcto: 192.168.1.123)" % ip)
        return 1
    if not 1 <= a.puerto <= 65535:
        print("*** El puerto %s no es válido" % a.puerto)
        return 1
    if ip.endswith(".1") and not a.forzar:
        print("*** ATENCIÓN: '%s' termina en .1 y en la mayoría de las redes esa IP es EL ROUTER\n"
              "    (la puerta de enlace), no una computadora. Si de verdad es la PC servidor,\n"
              "    vuelva a ejecutar agregando  --forzar  (el .bat lo pregunta)." % ip)
        return 2

    dist = Path(a.dist)
    if not dist.is_absolute():
        dist = AQUI / dist
    datos = {
        "motor": "postgres",
        "postgres": {"host": ip, "puerto": a.puerto, "base": a.base,
                     "usuario": a.usuario, "clave": a.clave},
        "respaldos": {"modo": "base", "carpeta": ""},
        "interfaz": {"zoom": 0},
    }

    print("=" * 62)
    print("  Servidor nuevo : %s : %d" % (ip, a.puerto))
    print("  Base / usuario : %s / %s" % (a.base, a.usuario))
    print("  Carpeta salida : %s" % dist)
    print("  Modo           : %s" % ("SIMULACIÓN (no toca nada)" if a.simular
                                     else ("solo la referencia" if a.solo_config else "empaquetar")))
    print("=" * 62)

    # Un config.json suelto en dist\ es un peligro: si alguien lo copia a otra PC, le
    # pisa el suyo y le cambia el ZOOM (el tamaño de pantalla es de cada computadora).
    sobrante = dist / NOMBRE_CONFIG
    if sobrante.exists():
        if a.limpiar_config and not a.simular:
            sobrante.unlink()
            print("   dist\\config.json BORRADO (así no se reparte ni pisa el zoom de las PC).")
            print()
        else:
            print("   AVISO: existe %s" % sobrante)
            print("          NO lo copie a las PC: pisa el config.json de esa computadora")
            print("          y le cambia el ZOOM (el tamaño de pantalla es de cada PC).")
            print("          Para borrarlo ahora:  --limpiar-config")
            print()

    print("1) archivo de referencia para revisar la dirección (el programa lo ignora):")
    escribir_ejemplo(dist, datos, a.simular)

    if a.sin_fabrica:
        print("2) valor de fábrica en configuracion.py: NO se toca (--sin-fabrica)")
    else:
        print("2) valor de fábrica en configuracion.py (para poder copiar SOLO el .exe):")
        if not cambiar_fabrica(ip, a.puerto, a.clave, a.simular):
            return 1

    if a.solo_config:
        print("3) empaquetado: omitido (--solo-config)")
    else:
        print("3) empaquetado con PyInstaller:")
        if not empaquetar(a.simular):
            return 1
        print("   (la referencia se escribe OTRA VEZ después de empaquetar, porque")
        print("    PyInstaller limpia la carpeta dist)")
        escribir_ejemplo(dist, datos, a.simular)

    print("=" * 62)
    print("  Para repartir: copie a cada PC SOLO  %s" % (dist / NOMBRE_EXE))
    print("  (la IP %s y el puerto %d van DENTRO del .exe)" % (ip, a.puerto))
    print("  Si esa PC ya tenía un config.json al lado del .exe, bórrelo:")
    print("  un config.json viejo manda sobre la IP de fábrica.")
    print("=" * 62)
    print("  Comprobar el .exe (autodiagnóstico):")
    print("     set VIATICOS_SELFTEST=1")
    print("     %s" % (dist / NOMBRE_EXE))
    print("  Debe decir:  OK  conexion -> Conexión correcta · PostgreSQL …")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
