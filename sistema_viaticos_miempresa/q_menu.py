# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_menu.py — Menú principal (PySide6): barra lateral con los módulos del sistema.

Es el mismo menú de `ui_menu.py` (los mismos módulos, los mismos permisos por rol y
la misma opción de salir); cambia el dibujo: barra lateral, tarjetas y botones
grandes en lugar de la lista de botones de Tkinter.

Cada módulo se abre en su propia ventana (`QDialog`) y, al cerrarla, se vuelve a
este menú. Los módulos se cargan al abrirlos, así el menú aparece rápido.
"""
import importlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

import configuracion as cfg
import database as db
import q_login
import qt_comunes as C
import qt_tema as T

# clave · icono · título · descripción · ¿se muestra en la barra lateral?
# «conexion» no se muestra (el superusuario la abre con Ctrl+Alt+B): la pantalla de
# conexión aparece sola cuando el servidor no responde, así que no hace falta el botón.
MODULOS = [
    ("viaje", "📝", "Generar / revisar / ajustar viáticos",
     "Crear viáticos, ajustarlos, anularlos y ver el historial", True),
    ("ajustes", "🧾", "Justificar viáticos",
     "Gastos, facturas, cierre y devoluciones", True),
    ("respaldos", "📁", "Respaldos",
     "Comprobantes y facturas guardados", True),
    ("admin", "⚙️", "Parámetros, empleados, vehículos y rutas",
     "Catálogos, sedes y distancias", True),
    ("bitacora", "🕵", "Informe de actividad (auditoría)",
     "Qué hizo cada usuario, con fecha y detalle", True),
    ("usuarios", "👥", "Usuarios del sistema",
     "Altas, cambios de clave y bajas", True),
    ("conexion", "🔌", "Conexión / base de datos",
     "Servidor central, migración y respaldos de la base", False),
]

# Quién puede abrir cada módulo: la clave se pide AL ABRIR la ventana, así el menú
# se ve desde el primer momento y cada área queda protegida.
#   · viáticos y respaldos → cualquier usuario del sistema (vendedoras y justificación);
#   · justificar viáticos  → solo la persona de justificación y el superusuario;
#   · parámetros, auditoría, usuarios y conexión → solo el superusuario.
# Si algún día la persona de justificación también debe tocar los parámetros, agregue
# db.ROL_JUSTIFICA a la tupla de "admin" y el sistema se lo pedirá a ella igual.
PERMISOS_MODULO = {
    "viaje": (db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER),
    "ajustes": (db.ROL_JUSTIFICA, db.ROL_SUPER),
    "respaldos": (db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER),
    "admin": (db.ROL_SUPER,),
    "bitacora": (db.ROL_SUPER,),
    "usuarios": (db.ROL_SUPER,),
    "conexion": (db.ROL_SUPER,),
}

# Atajo de la pantalla de Conexión (no está en la barra lateral): Ctrl+Alt+B.
ATAJO_CONEXION = "Ctrl+Alt+B"


# clave · (archivo del módulo nuevo, nombre de la clase)
ARCHIVOS_MODULO = {
    "viaje": ("q_viaje", "ViajeWindow"),
    "ajustes": ("q_ajustes", "AjustesWindow"),
    "respaldos": ("q_respaldos", "RespaldosWindow"),
    "admin": ("q_admin", "AdminWindow"),
    "bitacora": ("q_bitacora", "BitacoraWindow"),
    "usuarios": ("q_usuarios", "UsuariosWindow"),
    "conexion": ("q_conexion", "ConexionWindow"),
}


class MenuPrincipal(QMainWindow):
    """Ventana principal: barra lateral con los módulos + pantalla de inicio."""

    def __init__(self, usuario=None):
        super().__init__()
        # El menú se abre SIN sesión: cada ventana pide su clave al abrirse.
        self.usuario = usuario or {"usuario": "", "nombre": "", "rol": ""}
        self.es_super = self.usuario.get("rol") == db.ROL_SUPER
        self.salir_app = False
        self.botones = {}
        self._sesion_guardada = None      # si marcó «no volver a pedir la clave»
        self.setWindowTitle("Sistema de Viáticos — Miempresa")
        self.setMinimumSize(T.px(880, 600), T.px(560, 420))
        self.resize(T.px(1180), T.px(720))

        central = QWidget()
        central.setObjectName("fondo")
        raiz = C.margenes(QHBoxLayout(central), 0, 0, 0, 0, 0)
        raiz.addWidget(self._barra_lateral())
        self.paginas = QStackedWidget()
        self.paginas.addWidget(self._pagina_inicio())
        raiz.addWidget(self.paginas, 1)
        self.setCentralWidget(central)
        self.poner_seccion("inicio")

    # ------------------------------------------------------- barra lateral
    def _barra_lateral(self):
        barra = QFrame()
        barra.setObjectName("barraLateral")
        barra.setFixedWidth(T.px(232, 180))
        lay = C.margenes(QVBoxLayout(barra), 14, 16, 14, 14, 12)

        logo = T.logo_pixmap(52)
        if logo is not None:
            lbl_logo = QLabel()
            lbl_logo.setPixmap(logo)
            lbl_logo.setAlignment(Qt.AlignCenter)
            lay.addWidget(lbl_logo)

        # La sesión en uso: se muestra (no se elige) igual que en la cabecera de antes.
        # Al principio dice que todavía no hay nadie identificado, porque el menú se
        # abre sin entrar y la clave se pide al abrir cada ventana.
        self.cb_sesion = C.combo([self._texto_sesion()], ancho=200)
        self.cb_sesion.setEnabled(True)
        self.cb_sesion.setToolTip("Sesión abierta en este equipo")
        lay.addWidget(self.cb_sesion)

        grupo = QButtonGroup(barra)
        grupo.setExclusive(True)
        b_inicio = C.boton_menu("🏠  Inicio", lambda: self.poner_seccion("inicio"))
        grupo.addButton(b_inicio)
        self.botones["inicio"] = b_inicio
        lay.addWidget(b_inicio)
        for clave, icono, titulo, _desc, visible in MODULOS:
            if not visible:
                continue      # «Conexión» se abre con el atajo, no con un botón
            b = C.boton_menu("%s  %s" % (icono, titulo), lambda _c=False, k=clave: self.abrir_modulo(k))
            b.setToolTip(titulo)
            grupo.addButton(b)
            self.botones[clave] = b
            lay.addWidget(b)

        lay.addStretch(1)
        lay.addWidget(C.linea())
        self.lbl_sesion_nombre = C.etiqueta(self.usuario.get("nombre") or "Sin identificar",
                                           clave=True)
        lay.addWidget(self.lbl_sesion_nombre)
        self.lbl_sesion_rol = C.etiqueta(self._texto_rol(), ayuda=True)
        lay.addWidget(self.lbl_sesion_rol)
        base = "BASE CENTRAL" if db.es_postgres() else "BASE LOCAL"
        lay.addWidget(C.etiqueta(base + " · " + cfg.describir()[:40], ayuda=True))
        b_olvidar = C.boton_secundario("🔒  Olvidar la clave")
        b_olvidar.setToolTip("Vuelve a pedir la clave en la próxima ventana que se abra.")
        b_olvidar.clicked.connect(self.olvidar_sesion)
        lay.addWidget(b_olvidar)
        b_salir = C.boton_secundario("🚪  Salir del sistema")
        b_salir.clicked.connect(self.salir)
        lay.addWidget(b_salir)
        return barra

    # ------------------------------------------------------------- sesión
    def _texto_sesion(self):
        """Lo que se muestra en la barra: la sesión abierta o que no hay ninguna."""
        etiqueta = C.etiqueta_sesion(self.usuario) if self.usuario.get("usuario") else ""
        return etiqueta or "Sin sesión — pida una clave al abrir"

    def _texto_rol(self):
        rol = db.ETIQUETA_ROL.get(self.usuario.get("rol"), self.usuario.get("rol") or "")
        return rol or "El menú no pide clave: cada ventana la pide al abrirse"

    def _refrescar_sesion(self):
        """Repinta la sesión (barra lateral, pantalla de inicio y título)."""
        self.es_super = self.usuario.get("rol") == db.ROL_SUPER
        nombre = self.usuario.get("nombre") or self.usuario.get("usuario") or ""
        self.setWindowTitle("Sistema de Viáticos — %s" % (nombre or "Miempresa"))
        if hasattr(self, "lbl_sesion_nombre"):
            self.lbl_sesion_nombre.setText(nombre or "Sin identificar")
            self.lbl_sesion_rol.setText(self._texto_rol())
        if hasattr(self, "cb_sesion"):
            C.poner_combo(self.cb_sesion, self._texto_sesion())
        for kpi, valor, nota in ((getattr(self, "kpi_usuario", None),
                                  self.usuario.get("usuario") or "—",
                                  nombre or "Nadie ha ingresado todavía"),
                                 (getattr(self, "kpi_rol", None),
                                  db.ETIQUETA_ROL.get(self.usuario.get("rol"),
                                                      self.usuario.get("rol") or "—"),
                                  "Permisos de esta sesión")):
            if kpi is not None:
                kpi.lbl_valor.setText(valor)
                kpi.lbl_rotulo.setToolTip(nota)
        return self

    def olvidar_sesion(self):
        """Deja el menú sin sesión (la próxima ventana vuelve a pedir la clave)."""
        if self.usuario.get("usuario"):
            db.registrar_bitacora(self.usuario, "CERRÓ SESIÓN", "sesion",
                                  self.usuario.get("usuario", ""),
                                  "Olvidó la clave en el equipo")
        self._sesion_guardada = None
        self.usuario = {"usuario": "", "nombre": "", "rol": ""}
        self._refrescar_sesion()
        C.informar(self, "Sesión", "Listo: la próxima ventana volverá a pedir la clave.")
        return self

    # -------------------------------------------------------- pantalla inicio
    def _pagina_inicio(self):
        pag = C.Pagina("Sistema de Viáticos",
                       "Elija un módulo en la barra de la izquierda. Los permisos de cada "
                       "usuario se respetan igual que siempre.")
        nombre = self.usuario.get("nombre") or self.usuario.get("usuario") or ""
        saludo = ("Bienvenido(a), %s" % nombre) if nombre else "Bienvenido(a) al sistema"
        pag.agregar(C.Aviso(saludo,
                            "Empiece por «Generar / revisar / ajustar viáticos» para crear "
                            "un viático y por «Justificar viáticos» para cargar los gastos, "
                            "las facturas y cerrar el viático. Al abrir cualquier módulo el "
                            "sistema pedirá la clave del área."))

        # --- datos de la sesión (los recuadros se reparten el ancho de la pantalla) ---
        kpis = C.margenes(QHBoxLayout(), esp=8)
        rol = db.ETIQUETA_ROL.get(self.usuario.get("rol"), self.usuario.get("rol") or "")
        from datetime import date
        self.kpi_usuario = C.Kpi("Usuario", self.usuario.get("usuario") or "—",
                                 nombre or "Nadie ha ingresado todavía", estirar=True)
        self.kpi_rol = C.Kpi("Rol", rol or "—", "Permisos de esta sesión", estirar=True)
        for kpi in (self.kpi_usuario, self.kpi_rol,
                    C.Kpi("Base de datos", "Central" if db.es_postgres() else "Local",
                          "PostgreSQL del servidor" if db.es_postgres()
                          else "SQLite de esta máquina", estirar=True),
                    C.Kpi("Fecha", date.today().strftime("%d/%m/%Y"), "Hoy", estirar=True)):
            kpis.addWidget(kpi)
        pag.agregar_fila(kpis)

        # --- resumen de viáticos (tablero; los accesos ya están en la barra lateral) ---
        try:
            resumen = db.resumen_viaticos()
        except Exception:
            resumen = []
        cuenta = {}
        for r in resumen:
            estado = (r.get("estado") or "—").upper()
            cuenta[estado] = cuenta.get(estado, 0) + 1
        tarjeta = C.Tarjeta("Resumen de viáticos")
        fila = C.margenes(QHBoxLayout(), esp=8)
        for kpi in (C.Kpi("Viáticos", str(len(resumen)), "En total", estirar=True),
                    C.Kpi("Pendientes", str(cuenta.get("PENDIENTE", 0)), "Por justificar",
                          estirar=True),
                    C.Kpi("Justificados", str(cuenta.get("JUSTIFICADO", 0)), "Cerrados",
                          estirar=True),
                    C.Kpi("Anulados", str(cuenta.get("ANULADO", 0)), "Dados de baja",
                          estirar=True)):
            fila.addWidget(kpi)
        tarjeta.agregar_fila(fila)
        pag.agregar(tarjeta)

        # --- los dos atajos que más se usan (el resto está en la barra de la izquierda) ---
        atajos = C.margenes(QHBoxLayout(), esp=8)
        b1 = C.boton("📝  Generar / revisar / ajustar viáticos",
                     lambda: self.abrir_modulo("viaje"), "menuGrande")
        b1.setMinimumHeight(T.px(46, 34))
        atajos.addWidget(b1, 1)
        b2 = C.boton("🧾  Justificar viáticos",
                     lambda: self.abrir_modulo("ajustes"), "menuGrande")
        b2.setMinimumHeight(T.px(46, 34))
        atajos.addWidget(b2, 1)
        pag.agregar_fila(atajos)
        pag.agregar(C.etiqueta("Sesión: %s · %s · %s"
                               % (C.etiqueta_sesion(self.usuario),
                                  "BASE CENTRAL" if db.es_postgres() else "BASE LOCAL",
                                  cfg.describir()), ayuda=True))
        pag.agregar_estirar()
        self._indices = {"inicio": 0}
        return pag

    # ------------------------------------------------------------- navegación
    def poner_seccion(self, nombre):
        """Marca el botón de la barra lateral y muestra la pantalla indicada."""
        boton = self.botones.get(nombre)
        if boton is not None:
            boton.setChecked(True)
        self.paginas.setCurrentIndex(self._indices.get(nombre, 0))
        return self

    # ------------------------------------------------- autorización por área
    def _nombres_roles(self, roles):
        return ", ".join(db.ETIQUETA_ROL.get(r, r) for r in roles)

    def _sesion_valida(self, roles):
        """True si la sesión ya abierta (o la que se recordó) puede entrar al área."""
        if self._sesion_guardada and self._sesion_guardada.get("rol") in roles:
            self.usuario = dict(self._sesion_guardada)
            self._refrescar_sesion()
            return True
        return bool(self.usuario.get("usuario") and self.usuario.get("rol") in roles)

    def autorizar(self, clave):
        """Pide la clave y comprueba el rol antes de abrir un módulo.

        El menú se ve sin entrar: la clave se pide aquí, al abrir cada ventana, y
        solo pasa quien tenga el rol de esa área (ver PERMISOS_MODULO).
        """
        roles = PERMISOS_MODULO.get(clave)
        if not roles:
            C.aviso(self, "Módulo desconocido", "No hay permisos definidos para «%s»." % clave)
            return False
        titulo = dict((m[0], m[2]) for m in MODULOS).get(clave, clave)
        if self._sesion_valida(roles):
            return True
        sesion, recordar = q_login.pedir_sesion(
            self, titulo="Ingreso — %s" % titulo,
            motivo="Para abrir «%s» escriba su clave.\nPuede ingresar: %s."
                   % (titulo, self._nombres_roles(roles)),
            roles=roles)
        if not sesion:
            return False
        self._sesion_guardada = dict(sesion) if recordar else None
        self.usuario = dict(sesion)
        self._refrescar_sesion()
        db.registrar_bitacora(sesion, "INICIÓ SESIÓN", "sesion", clave,
                              "Ingresó para abrir «%s»" % titulo)
        return True

    def abrir_modulo(self, clave):
        """Pide la clave del área y abre la ventana del módulo elegido."""
        archivo, clase = ARCHIVOS_MODULO.get(clave, (None, None))
        if not archivo:
            return None
        if not self.autorizar(clave):
            self.poner_seccion("inicio")
            return None
        try:
            modulo = importlib.import_module(archivo)
        except Exception as ex:
            C.aviso(self, "Módulo no disponible",
                    "El módulo «%s» todavía no está en la interfaz nueva.\n\n"
                    "Mientras tanto puede usar ese módulo con la interfaz anterior: "
                    "cierre el sistema, ábralo con INICIAR.bat y entre a ese módulo.\n\n"
                    "Detalle técnico: %s.py — %s" % (clave, archivo, ex))
            self.poner_seccion("inicio")
            return None
        Ventana = getattr(modulo, clase, None)
        if Ventana is None:
            C.aviso(self, "Módulo no disponible",
                    "En %s.py no existe la clase %s." % (archivo, clase))
            self.poner_seccion("inicio")
            return None
        try:
            ventana = Ventana(self, self.usuario)
        except TypeError:
            ventana = Ventana(self.usuario)
        try:
            ventana.exec()
        except Exception as ex:
            C.error(self, "Error en el módulo", str(ex))
        finally:
            self.poner_seccion("inicio")
            self.raise_()
            self.activateWindow()
        return ventana

    def salir(self):
        """Cierra el sistema (igual que el botón SALIR del menú anterior)."""
        self.salir_app = True
        self.close()

    def keyPressEvent(self, evento):
        """Ctrl+Alt+B abre la pantalla de Conexión, que no está en la barra lateral."""
        if (evento.key() == Qt.Key_B and evento.modifiers() & Qt.ControlModifier
                and evento.modifiers() & Qt.AltModifier):
            self.abrir_modulo("conexion")
            return
        super().keyPressEvent(evento)


# Nombre anterior del menú, para no romper ninguna llamada existente.
MainMenu = MenuPrincipal

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
