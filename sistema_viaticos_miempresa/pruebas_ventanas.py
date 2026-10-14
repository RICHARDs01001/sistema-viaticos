# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_ventanas.py — Comprueba que las ventanas Qt se construyan y carguen datos.

Se ejecuta sin servidor de base de datos (usa datos falsos) y sin pantalla
(plataforma «offscreen»): sirve para detectar de inmediato un error de armado o un
cambio de nombre en las funciones de la base.

    python pruebas_ventanas.py
"""
import os
import sys
import traceback

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QListWidget

import database as db

ROLES = []


def _falsos():
    """Datos de mentira: las ventanas no deben tocar ninguna base real."""
    db.init_db = lambda: True
    db.es_postgres = lambda: False
    db.resumen_viaticos = lambda estado=None: []
    db.numeraciones = lambda: []
    db.anio_actual = lambda: 2026
    db.numero_visible = lambda n: n
    db.etiqueta_numero = lambda n: str(n)
    db.listar_gastos = lambda n: []
    db.totales_gastos = lambda n: {k: 0.0 for k in ("hospedaje", "combustible", "buses",
                                                    "taxis", "alimentacion", "peaje",
                                                    "otros", "total")}
    db.listar_respaldos = lambda n: []
    db.filas_numero = lambda n: []
    db.listar_empleados = lambda: ["PERSONAL DE EJEMPLO DOS",
                                   "PERSONAL DE EJEMPLO SEIS",
                                   "PERSONAL DE EJEMPLO TRES",
                                   "PERSONAL DE EJEMPLO CUATRO",
                                   "PERSONAL DE EJEMPLO CINCO",
                                   "TENELEMA OCHOA JUAN PABLO"]
    db.listar_clientes = lambda: ["MUNICIPALIDAD DE CUENCA", "MIEMPRESA"]
    db.listar_vehiculos = lambda: [{"placa": "AB1234", "tipo": "CAMIONETA",
                                    "chofer": "TENELEMA OCHOA JUAN PABLO"}]
    db.listar_cantones = lambda p: ["CUENCA", "GIRÓN", "GUALACEO"]
    db.listar_bitacora = lambda *a, **k: []
    db.usuarios_bitacora = lambda: []
    db.acciones_bitacora = lambda: []
    db.resumen_respaldos = lambda *a, **k: {"tabla": [], "mensaje": ""}
    db.listar_todos_respaldos = lambda *a, **k: []
    db.contar_respaldos = lambda *a, **k: {"total": 0}
    db.registrar_bitacora = lambda *a, **k: None
    db.DIR_DATOS = getattr(db, "DIR_DATOS", None)
    try:
        import migracion
        migracion.resumen_local = lambda: {"viajes": 0, "empleados": 0, "clientes": 0,
                                           "respaldos": 0, "bitacora": 0}
    except Exception:
        pass
    try:
        import reportes
        reportes.imprimir_justificacion = lambda *a, **k: None
    except Exception:
        pass


def _probar(nombre, fabrica, capturar=False):
    try:
        ventana = fabrica()
        if capturar:
            _captura(ventana, nombre)
        ROLES.append((nombre, "OK"))
        return ventana
    except Exception:
        ROLES.append((nombre, "FALLA"))
        print("\n--- %s ---" % nombre)
        traceback.print_exc()
        return None


def _captura(ventana, nombre):
    """Guarda una imagen de la ventana para revisar cómo quedó el diseño."""
    import re
    from PySide6.QtWidgets import QWidget
    carpeta = os.path.join("documentacion", "capturas")
    os.makedirs(carpeta, exist_ok=True)
    archivo = os.path.join(carpeta, re.sub(r"[^A-Za-z0-9]+", "_", nombre).strip("_") + ".png")
    ventana.show()
    QApplication.processEvents()
    lienzo = ventana.grab() if isinstance(ventana, QWidget) else None
    if lienzo is not None:
        lienzo.save(archivo)
        print("  captura: %s" % archivo)


def main():
    capturar = "--capturar" in sys.argv
    app = QApplication(sys.argv)
    import qt_tema as T
    T.aplicar_tema(app)

    # La paleta tiene que ser CLARA aunque Windows esté en modo oscuro: los controles
    # sin estilo propio (listas, árboles, calendario) heredan estos colores.
    print("Paleta: ventana %s · campos %s · texto %s"
          % (app.palette().window().color().name(), app.palette().base().color().name(),
             app.palette().windowText().color().name()))
    lista = QListWidget()
    ROLES.append(("Paleta clara de listas", "OK" if lista.palette().base().color().name()
                  == app.palette().base().color().name() else "FALLA"))

    _falsos()
    usuario = {"nombre": "JUSTIFICA1", "usuario": "justifica1", "rol": db.ROL_SUPER}
    comun = {"nombre": "JUSTIFICA1", "usuario": "justifica1", "rol": "USUARIO"}

    for nombre, archivo, clase in [
            ("Respaldos", "q_respaldos", "RespaldosWindow"),
            ("Usuarios", "q_usuarios", "UsuariosWindow"),
            ("Parámetros y catálogos", "q_admin", "AdminWindow"),
            ("Bitácora", "q_bitacora", "BitacoraWindow"),
            ("Conexión", "q_conexion", "ConexionWindow"),
            ("Justificación", "q_ajustes", "AjustesWindow"),
            ("Viáticos", "q_viaje", "ViajeWindow")]:
        try:
            modulo = __import__(archivo)
        except Exception as ex:
            ROLES.append((nombre, "pendiente (%s)" % type(ex).__name__))
            continue
        ventana = getattr(modulo, clase)
        sesion = usuario if nombre in ("Respaldos", "Usuarios", "Parámetros y catálogos",
                                       "Bitácora", "Conexión") else comun
        _probar(nombre, lambda v=ventana, s=sesion: v(usuario=s), capturar=capturar)

    ancho = max(len(n) for n, _ in ROLES)
    print()
    for nombre, estado in ROLES:
        print("  %-*s  %s" % (ancho, nombre, estado))
    fallas = [n for n, e in ROLES if e == "FALLA"]
    print("\n%d de %d ventanas correctas." % (len(ROLES) - len(fallas), len(ROLES)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
