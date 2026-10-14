# -*- coding: utf-8 -*-
"""limpiar_y_firmar.py — Deja el proyecto firmado por el autor y la carpeta limpia.

Hace, en este orden:
  1. Pone la CABECERA de autoría en todos los .py y .bat del proyecto.
  2. Pone la firma al final de cada .py.
  3. Pone la cabecera de autoría en todos los .md (documentación).
  4. Crea/actualiza  CREDITOS.md  y  DOCUMENTACION.md .
  5. Crea  version_info.txt  (Autor/Compañía/Copyright del .exe) y lo engancha al .spec.
  6. Borra la documentación que ya no sirve y la basura (__pycache__, build, temporales).

Es idempotente: si lo vuelve a ejecutar, no duplica nada.
Uso:  python herramientas\\limpiar_y_firmar.py
"""
import io
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RAIZ, "sistema_viaticos_miempresa")

AUTOR = "Richard Esteban Salazar Guillén"
CORREO = "richards0101789@gmail.com"
CELULAR = "+593 981239086"
PROGRAMA = "Sistema de Viáticos Miempresa"
ANIO = "2026"

CAB_PY = """# =====================================================================
#  %(programa)s
#  Autor:    %(autor)s
#  Contacto: %(correo)s  ·  %(celular)s
#  (c) %(anio)s %(autor)s — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
""" % {"programa": PROGRAMA, "autor": AUTOR, "correo": CORREO, "celular": CELULAR, "anio": ANIO}

PIE_PY = """
# ---------------------------------------------------------------------
#  (c) %(anio)s %(autor)s
#  %(correo)s  ·  %(celular)s  ·  %(programa)s
# ---------------------------------------------------------------------
""" % {"anio": ANIO, "autor": AUTOR, "correo": CORREO, "celular": CELULAR, "programa": PROGRAMA}

CAB_MD = """<!--
  %(programa)s
  Autor:    %(autor)s
  Contacto: %(correo)s  ·  %(celular)s
  (c) %(anio)s %(autor)s — Todos los derechos reservados.
-->

""" % {"programa": PROGRAMA, "autor": AUTOR, "correo": CORREO, "celular": CELULAR, "anio": ANIO}

VERSION_INFO = """# Metadatos del ejecutable (Propiedades -> Detalles).
# Los usa Sistema_Viaticos.spec para que el .exe diga quién lo hizo.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(6, 2, 0, 0), prodvers=(6, 2, 0, 0), mask=0x3f, flags=0x0,
    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', '%(autor)s'),
        StringStruct('FileDescription', '%(programa)s'),
        StringStruct('FileVersion', '6.2.0.0'),
        StringStruct('InternalName', 'Sistema_Viaticos'),
        StringStruct('LegalCopyright', '(c) %(anio)s %(autor)s - Todos los derechos reservados.'),
        StringStruct('OriginalFilename', 'Sistema_Viaticos.exe'),
        StringStruct('ProductName', '%(programa)s'),
        StringStruct('ProductVersion', '6.2'),
        StringStruct('Comments', 'Autor: %(autor)s | %(correo)s | %(celular)s')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
""" % {"autor": AUTOR, "programa": PROGRAMA, "correo": CORREO, "celular": CELULAR, "anio": ANIO}


def leer(ruta):
    with io.open(ruta, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def escribir(ruta, texto):
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)


def archivos(carpeta, extensiones, saltar=("__pycache__", "build", "dist", "_cap")):
    for raiz, dirs, nombres in os.walk(carpeta):
        dirs[:] = [d for d in dirs if d not in saltar and not d.startswith(".")]
        for n in sorted(nombres):
            if n.lower().endswith(extensiones):
                yield os.path.join(raiz, n)


def firmar_texto(ruta, cabecera, comentario):
    """Pone la cabecera de autoría (si falta). True si cambió el archivo."""
    texto = leer(ruta)
    if AUTOR in texto[:900]:
        return False
    lineas = texto.split("\n")
    # En los .bat la cabecera va DESPUÉS de "@echo off" para que no se imprima.
    if comentario == "rem" and lineas and lineas[0].strip().lower().startswith("@echo"):
        texto = lineas[0] + "\n" + cabecera + "\n".join(lineas[1:])
    else:
        texto = cabecera + texto
    escribir(ruta, texto)
    return True


def firmar_python(ruta):
    """Cabecera arriba + firma al final (sin duplicar)."""
    cambio = firmar_texto(ruta, CAB_PY, "#")
    texto = leer(ruta)
    if AUTOR not in texto[-700:]:
        escribir(ruta, texto.rstrip("\n") + "\n" + PIE_PY)
        cambio = True
    return cambio


def cab_bat():
    return CAB_PY.replace("#", "rem", 1).replace("\n#", "\nrem")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("=" * 70)
    print("  %s — firma del autor y limpieza" % PROGRAMA)
    print("  Autor: %s · %s · %s" % (AUTOR, CORREO, CELULAR))
    print("=" * 70)

    py = (list(archivos(APP, (".py",)))
          + list(archivos(os.path.join(RAIZ, "herramientas"), (".py",))))
    bat = (list(archivos(APP, (".bat",)))
           + list(archivos(os.path.join(RAIZ, "servidor"), (".bat",))))
    n_py = sum(1 for r in py if firmar_python(r))
    n_bat = sum(1 for r in bat if firmar_texto(r, cab_bat(), "rem"))
    print("1) Cabecera + firma puesta en %d de %d archivos .py" % (n_py, len(py)))
    print("2) Cabecera puesta en %d de %d archivos .bat" % (n_bat, len(bat)))

    md = [p for p in archivos(RAIZ, (".md",)) if "herramientas" not in p]
    n_md = sum(1 for r in md if firmar_texto(r, CAB_MD, "<!--"))
    print("3) Cabecera puesta en %d de %d documentos .md" % (n_md, len(md)))

    # ---- 4: CREDITOS.md ---------------------------------------------------
    escribir(os.path.join(RAIZ, "CREDITOS.md"), CAB_MD + """# Créditos y autoría

| Dato | Valor |
| --- | --- |
| **Programa** | %(programa)s |
| **Autor y desarrollador** | **%(autor)s** |
| **Correo** | %(correo)s |
| **Celular / WhatsApp** | %(celular)s |
| **Año** | %(anio)s |
| **Derechos** | © %(anio)s %(autor)s — Todos los derechos reservados |

Prohibida su copia, reproducción o distribución sin autorización escrita del autor.

## Qué hizo el autor

El sistema completo: el análisis de las reglas de la empresa, la base de datos (SQLite
local y PostgreSQL central), la interfaz (PySide6), los cálculos del viático (comidas,
taxis, hospedaje, agua, combustible, peaje y redondeo de cajero), los informes en PDF,
los Excel por documento, la justificación con facturas, la bitácora de actividad, los
respaldos dentro de la base, la migración de datos y el empaquetado en un solo `.exe`.

## Dónde está la firma

- **Cabecera y pie en todos** los archivos de código (`.py`) y de arranque (`.bat`).
- **Cabecera en todos** los documentos (`.md`), incluido `LEEME_PRIMERO.md`.
- **Metadatos del ejecutable** (`Sistema_Viaticos.exe` → clic derecho → Propiedades →
  Detalles): Autor, Compañía y Copyright.
- **Bitácora del sistema:** cada movimiento queda registrado con su usuario y su fecha.

> La autoría **no se ve en ninguna pantalla** del programa: vive en el código, en la
> documentación y en las propiedades del ejecutable.
""" % {"programa": PROGRAMA, "autor": AUTOR, "correo": CORREO, "celular": CELULAR, "anio": ANIO})
    print("4) CREDITOS.md escrito")

    # ---- 5: metadatos del .exe -------------------------------------------
    escribir(os.path.join(APP, "version_info.txt"), VERSION_INFO)
    spec = os.path.join(APP, "Sistema_Viaticos.spec")
    texto = leer(spec)
    if "version_info.txt" not in texto:
        escribir(spec, texto.replace("    icon=['icono.ico'],",
                                     "    icon=['icono.ico'],\n    version='version_info.txt',"))
        print("5) version_info.txt creado y enganchado en Sistema_Viaticos.spec")
    else:
        print("5) version_info.txt creado (el .spec ya lo usaba)")

    # ---- 6: limpieza ------------------------------------------------------
    obsoletos = ["PASOS_EN_EL_SERVIDOR.md",
                 "EN_EL_SERVIDOR_PASO_A_PASO_1.md", "PRUEBA_EN_2_PCS.md",
                 "PRUEBA_LAPTOP_SERVIDOR.md", "SERVIDOR_POSTGRES.md"]
    sueltos = ["Sistema_Viaticos_2026-09-23.zip", "autodiagnostico.txt"]
    borrados = []
    for nombre in obsoletos:
        ruta = os.path.join(RAIZ, "documentacion", nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
            borrados.append("documentacion/" + nombre)
    for nombre in sueltos:
        ruta = os.path.join(RAIZ, nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
            borrados.append(nombre)
    for ruta in (os.path.join(APP, "build"), os.path.join(APP, "_cap"),
                 os.path.join(APP, "dist", "autodiagnostico.txt")):
        if os.path.isdir(ruta):
            shutil.rmtree(ruta, ignore_errors=True)
            borrados.append(os.path.relpath(ruta, RAIZ))
        elif os.path.exists(ruta):
            os.remove(ruta)
            borrados.append(os.path.relpath(ruta, RAIZ))
    for raiz, dirs, nombres in os.walk(RAIZ):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(raiz, d), ignore_errors=True)
                borrados.append(os.path.relpath(os.path.join(raiz, d), RAIZ))
                dirs.remove(d)
        for n in nombres:
            if n.endswith(".pyc") or (n.startswith("_") and n.endswith(".txt")):
                try:
                    os.remove(os.path.join(raiz, n))
                    borrados.append(os.path.relpath(os.path.join(raiz, n), RAIZ))
                except OSError:
                    # Por ejemplo el archivo donde este script está escribiendo el
                    # informe: se deja y se borra a mano (no es un problema).
                    pass
    print("6) Limpieza: %d borrado(s): %s" % (len(borrados), ", ".join(borrados) or "nada"))
    print("=" * 70)
    print("  Listo. Empaquete de nuevo para que el .exe lleve los metadatos del autor.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
