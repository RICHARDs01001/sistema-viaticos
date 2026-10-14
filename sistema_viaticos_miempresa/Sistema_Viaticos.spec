# -*- mode: python ; coding: utf-8 -*-
"""Cómo se arma Sistema_Viaticos.exe (un solo archivo).

Se usa desde EMPAQUETAR_EXE_SERVIDOR.bat -> empaquetar_servidor.py -> PyInstaller.
"""
import os


def _motivo(ex):
    """Texto corto del error al no poder leer un archivo."""
    return ex.strerror or str(ex)


def _catalogo_excel():
    """[(origen, destino)] de la carpeta `excel\\`: los catálogos que van DENTRO del .exe.

    Dentro del ejecutable tienen que viajar los catálogos (tiempos de viaje, lista de
    personal y lista de clientes) porque de ahí los lee la carga inicial de un servidor
    nuevo; si faltan, habría que importarlos a mano en Parámetros.

    Se revisa archivo por archivo para poder saltar los que no sirven:
      · los temporales de Office (`~$algo.xlsx`, `~$algo.docx`) existen MIENTRAS alguien
        tiene ese Excel o ese Word ABIERTO en la carpeta, y Windows no deja leerlos.
        Antes el empaquetado se caía con «PermissionError: ...~$distancias...xlsx» y
        había que cerrar el Excel para poder empaquetar.
      · los archivos que en este momento no se pueden leer (abiertos, sincronizándose,
        etc.) se dejan fuera con un AVISO bien visible, en vez de botar el empaquetado.
    """
    carpeta = os.path.join(globals().get("SPECPATH") or os.getcwd(), "excel")
    if not os.path.isdir(carpeta):
        print("*" * 70)
        print("*** AVISO: no existe la carpeta de catálogos: %s" % carpeta)
        print("***        El .exe saldría SIN los catálogos (tiempos de viaje, personal")
        print("***        y clientes). Revise que esté en la carpeta del programa.")
        print("*" * 70)
        return []
    temporales, bloqueados, incluidos = [], [], []
    for nombre in sorted(os.listdir(carpeta)):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.isfile(ruta):
            continue
        if (nombre.startswith("~$") or nombre.startswith(".")
                or nombre.lower() in ("thumbs.db", "desktop.ini")
                or nombre.lower().endswith(".tmp")):
            temporales.append(nombre)
            continue
        try:
            with open(ruta, "rb"):          # ¿se puede leer ahora mismo?
                pass
        except OSError as ex:
            bloqueados.append((nombre, _motivo(ex)))
            continue
        incluidos.append((ruta, "excel"))
    print("[empaquetado] catálogos dentro del .exe: %d archivo(s) de excel\\"
          % len(incluidos))
    for nombre in temporales:
        print("[empaquetado]   se omite (temporal de Office): excel\\%s" % nombre)
    for nombre, motivo in bloqueados:
        print("*" * 70)
        print("*** AVISO: NO se pudo leer  excel\\%s  (%s)" % (nombre, motivo))
        print("***        Se dejó FUERA del .exe. Cierre el programa que lo tiene")
        print("***        abierto y vuelva a empaquetar para que sí viaje dentro.")
        print("*" * 70)
    return incluidos


a = Analysis(
    ['main_qt.py'],
    pathex=[],
    binaries=[],
    # Los archivos que viajan DENTRO del .exe: el logo y la carpeta `excel\` (tiempos de
    # viaje, lista de personal y lista de clientes). La carpeta se arma con
    # `_catalogo_excel()`, que salta los temporales de Office y los archivos que estén
    # abiertos: así el empaquetado no se cae si alguien tiene un Excel abierto ahí.
    datas=[('image.png', '.')] + _catalogo_excel(),
    # Los módulos de cada pantalla se cargan al abrirlos (importlib con el nombre en
    # una variable), así que PyInstaller no los ve solo: hay que pedirlos aquí. Si no,
    # el .exe abre el menú pero al entrar a un módulo dice «no disponible».
    hiddenimports=['autor', 'bd', 'calculos', 'colores', 'configuracion', 'database', 'migracion',
                   'reportes', 'qt_comunes', 'qt_tema',
                   'q_login', 'q_menu', 'q_conexion', 'q_viaje', 'q_ajustes', 'q_admin',
                   'q_bitacora', 'q_respaldos', 'q_usuarios',
                   'PIL.PdfImagePlugin', 'PIL.Image', 'psycopg2', 'psycopg2.extras',
                   'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # No se incluye la interfaz anterior (Tkinter) ni bibliotecas que no se usan:
    # así el .exe queda más liviano y arranca más rápido.
    excludes=['tkinter', 'unittest', 'pydoc', 'pygame', 'lxml', 'yaml',
              'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtWebEngineQuick', 'PySide6.QtQml', 'PySide6.QtQuick',
              'PySide6.QtQuickWidgets', 'PySide6.QtMultimedia', 'PySide6.QtCharts',
              'PySide6.QtDataVisualization', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
              'PySide6.QtBluetooth', 'PySide6.QtNetworkAuth', 'PySide6.QtNfc',
              'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSql',
              'PySide6.QtTest', 'PySide6.QtDesigner', 'PySide6.QtHelp',
              'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtWebSockets',
              'PySide6.QtWebChannel', 'PySide6.QtPositioning', 'PySide6.QtLocation',
              'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSpatialAudio',
              'PySide6.QtStateMachine', 'PySide6.QtTextToSpeech'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sistema_Viaticos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX COMPRIME los .dll del paquete, pero en un .exe de un solo archivo eso se paga
    # en CADA arranque (hay que descomprimir en memoria antes de poder usarlos) y además
    # algunos antivirus lo marcan como sospechoso. Se deja apagado: el .exe pesa un poco
    # más, pero ABRE MÁS RÁPIDO. Si algún día se quiere el más chico, poner upx=True.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icono.ico'],
    version='version_info.txt',
)
