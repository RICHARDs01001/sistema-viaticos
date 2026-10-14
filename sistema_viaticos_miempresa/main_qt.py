# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""main_qt.py — Punto de entrada del Sistema de Viáticos (PySide6).

Es el mismo arranque de siempre, en el mismo orden:

  1) Se asegura que la base de datos responda (la central del servidor o, si no
     hay servidor, la local de esta máquina).
  2) Se abre el **menú principal sin pedir clave**: así el menú se ve desde el
     primer momento y nadie queda afuera por no recordar su usuario.
  3) Al pulsar cualquier módulo, el sistema **pide la clave de esa área** y
     comprueba el rol (viáticos y respaldos: cualquier usuario; justificación:
     la persona de justificación y el superusuario; parámetros, auditoría,
     usuarios y conexión: solo el superusuario). Cada ingreso y cada cierre de
     sesión quedan en la bitácora.

Con  set VIATICOS_SELFTEST=1  hace un autodiagnóstico y deja el informe en
autodiagnostico.txt (sirve para revisar el .exe recién empaquetado).
"""
import os
import traceback

import database as db
import qt_tema as T


def _asegurar_conexion():
    """Deja lista la base de datos antes de mostrar el ingreso.

    Usa la pantalla de conexión nueva (`q_conexion.py`): es la que permite cambiar la
    dirección del servidor o trabajar en local sin tocar config.json a mano.
    """
    import q_conexion
    import q_login
    app = q_login.crear_app()
    return bool(q_conexion.asegurar_conexion(app))


def _aviso_error(detalle):
    """Muestra el error en pantalla (el .exe no tiene consola)."""
    try:
        import qt_comunes as C
        import q_login
        q_login.crear_app()
        C.error(None, "Error al iniciar el sistema",
                "Ocurrió un error inesperado:\n\n" + str(detalle)[-1500:])
    except Exception:
        try:
            print(detalle)
        except Exception:
            pass


def autodiagnostico():
    """Revisa que dentro del .exe esté todo lo necesario.

    Se ejecuta con  set VIATICOS_SELFTEST=1  y deja el resultado en el archivo
    autodiagnostico.txt, junto al ejecutable (no hay consola en el .exe).
    """
    import platform
    import sys
    import time
    import configuracion as cfg

    lineas = []

    def apuntar(titulo, funcion, aviso=False):
        """Anota el resultado de una comprobación.

        `aviso=True` es para lo que depende del servidor (si el servidor no está
        encendido no es un problema del programa): se marca como AVISO y no cuenta
        como falla.
        """
        try:
            lineas.append("%-26s OK     %s" % (titulo, funcion()))
        except Exception as ex:
            etiqueta = "AVISO " if aviso else "FALLA "
            lineas.append("%-26s %s %s: %s" % (titulo, etiqueta, type(ex).__name__,
                                               str(ex).replace("\n", " ")[:90]))

    lineas.append("Sistema de Viáticos — autodiagnóstico")
    lineas.append("Fecha: %s" % time.strftime("%d/%m/%Y %H:%M:%S"))
    lineas.append("Python: %s" % platform.python_version())
    lineas.append("Programa: %s" % getattr(sys, "executable", ""))
    lineas.append("Carpeta de datos: %s" % cfg.dir_datos())
    lineas.append("-" * 70)
    apuntar("PySide6 (interfaz)", lambda: __import__("PySide6").__version__)
    apuntar("Autor del sistema", lambda: __import__("autor").creditos())
    apuntar("Firma del autor", lambda: "completa" if __import__("autor").firmado()
            else "*** falta ***")
    apuntar("Base de datos", lambda: db.init_db() or "lista", aviso=True)
    apuntar("Conexión en uso", lambda: cfg.describir())
    apuntar("Empleados", lambda: len(db.listar_empleados()), aviso=True)
    apuntar("Clientes", lambda: len(db.listar_clientes()), aviso=True)
    apuntar("Viáticos", lambda: len(db.resumen_viaticos()), aviso=True)
    apuntar("Datos del cálculo", lambda: len(db.cargar_parametros()), aviso=True)
    apuntar("openpyxl (Excel)", lambda: __import__("openpyxl").__version__)
    apuntar("Pillow (PDF/fotos)", lambda: __import__("PIL").__version__)
    apuntar("psycopg2 (servidor)", lambda: __import__("psycopg2").__version__)
    for modulo in ("qt_tema", "qt_comunes", "q_login", "q_menu", "q_viaje",
                   "q_ajustes", "q_admin", "q_bitacora", "q_respaldos",
                   "q_usuarios", "q_conexion", "reportes", "migracion"):
        apuntar("módulo " + modulo, lambda m=modulo: "cargado" if __import__(m) else "")
    lineas.append("-" * 70)
    fallas = [l for l in lineas if "FALLA" in l]
    lineas.append("RESULTADO: %s" % ("todo correcto" if not fallas
                                     else "%d problema(s)" % len(fallas)))
    destino = os.path.join(os.path.dirname(os.path.abspath(sys.executable)),
                           "autodiagnostico.txt")
    try:
        with open(destino, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lineas) + "\n")
        lineas.append("Informe guardado en: %s" % destino)
    except Exception as ex:
        lineas.append("No se pudo guardar el informe: %s" % ex)
    print("\n".join(lineas))
    return 0


def main():
    if not _asegurar_conexion():
        return 0
    import q_login
    import q_menu
    app = q_login.crear_app()
    # El menú se abre sin clave: cada ventana pide la suya al abrirse (q_menu).
    ventana = q_menu.MenuPrincipal()
    ventana.show()
    try:
        app.exec()
    finally:
        # Al cerrar el sistema se sueltan las conexiones guardadas (si no, el servidor
        # las vería como «abiertas» hasta que se dé cuenta solo).
        db.cerrar_conexiones()
    return 0


if __name__ == "__main__":
    # Antes de crear cualquier ventana: avisar a Windows que el programa ya se
    # encarga del escalado de la pantalla (si no, la estira y todo queda grande).
    T.preparar_dpi()
    if os.environ.get("VIATICOS_SELFTEST"):
        autodiagnostico()
    else:
        try:
            main()
        except Exception:
            _aviso_error(traceback.format_exc())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
