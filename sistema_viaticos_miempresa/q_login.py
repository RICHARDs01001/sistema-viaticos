# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_login.py — Ingreso al sistema (PySide6).

Es la misma pantalla de `ui_login.py`: usuario y clave, el superusuario no se
lista en ninguna parte y solo entra escribiendo su clave. Cambia únicamente el
dibujo (Qt en lugar de Tkinter).

Se usa de dos maneras:
  · al abrir una ventana del menú, con `pedir_sesion(...)`, indicando para qué
    área se pide la clave y qué roles pueden entrar (por ejemplo, solo el
    superusuario para Parámetros, Usuarios, Auditoría o Conexión);
  · con `iniciar_sesion(...)`, para pedir el ingreso sin restricción de área.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout,
)

import configuracion as cfg
import database as db
import qt_comunes as C
import qt_tema as T


def crear_app():
    """Crea (o reutiliza) la aplicación Qt con el tema ya instalado."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    T.aplicar_tema(app)
    return app


class LoginWindow(QDialog):
    """Ventana de ingreso. Deja la sesión en `self.resultado` (o None si cancela).

    `roles` es la lista de roles que pueden entrar por esta ventana (si no se
    indica, entran todos). `motivo` explica para qué se está pidiendo la clave
    (lo usa el menú al abrir cada área). Con `pedir_recordar=True` aparece la
    casilla para no volver a pedir la clave en este equipo.
    """

    def __init__(self, padre=None, titulo=None, motivo="", roles=None,
                 pedir_recordar=False):
        super().__init__(padre)
        self.resultado = None
        self.recordar = False
        self.roles = tuple(roles or db.ROLES_VALIDOS)
        self.motivo = motivo or ""
        self.con_recordar = bool(pedir_recordar)
        self.chk_recordar = None
        self._centrada = False
        base = "BASE CENTRAL" if cfg.es_postgres() else "BASE LOCAL"
        self.setWindowTitle(titulo or ("Ingreso — Sistema de Viáticos Miempresa  ·  " + base))
        self.setModal(True)
        self.setFixedWidth(T.px(430))
        self._build()
        # El alto se ajusta al contenido: la ventana no queda con espacio de sobra.
        self.setFixedHeight(max(T.px(272), self.sizeHint().height()))
        self._centrar()
        self.txt_usuario.setFocus()

    # ---------- construcción ----------
    def _build(self):
        raiz = C.margenes(QVBoxLayout(self), 0, 0, 0, 0, 0)

        cabecera = QFrame()
        cabecera.setStyleSheet("QFrame { background: %s; border: none; }" % T.AZUL)
        ch = C.margenes(QVBoxLayout(cabecera), 18, 10, 18, 8, 1)
        logo = T.logo_pixmap(36)
        if logo is not None:
            lbl_logo = QLabel()
            lbl_logo.setPixmap(logo)
            lbl_logo.setAlignment(Qt.AlignCenter)
            ch.addWidget(lbl_logo)
        lbl_titulo = QLabel("SISTEMA DE VIÁTICOS")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: %dpx; font-weight: 700;"
                                 % T.px(15, 11))
        ch.addWidget(lbl_titulo)
        lbl_sub = QLabel("MIEMPRESA · CUENCA - ECUADOR")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: %s; font-size: %dpx; font-weight: 700;"
                              % (T.AMARILLO, T.px(10, 9)))
        ch.addWidget(lbl_sub)
        raiz.addWidget(cabecera)

        card = QFrame()
        card.setObjectName("tarjeta")
        cc = C.margenes(QVBoxLayout(card), 18, 12, 18, 12, 8)

        # Para qué se pide la clave (lo escribe el menú al abrir cada área).
        if self.motivo:
            lbl_motivo = C.etiqueta(self.motivo, ayuda=True)
            lbl_motivo.setWordWrap(True)
            lbl_motivo.setAlignment(Qt.AlignCenter)
            cc.addWidget(lbl_motivo)

        # Usuario y clave, centrados y con las etiquetas alineadas entre sí.
        self.txt_usuario = C.campo("", ancho=250, placeholder="Escriba su usuario",
                                   mayusculas=True, maximo=30)
        self.txt_clave = C.campo_clave(ancho=250)
        campos = C.rejilla([
            [("Usuario:", self.txt_usuario)],
            [("Clave:", self.txt_clave)],
        ], esp=8, etiqueta_ancho=70)
        fila_campos = C.margenes(QHBoxLayout(), esp=0)
        fila_campos.addStretch(1)
        fila_campos.addWidget(campos)
        fila_campos.addStretch(1)
        cc.addLayout(fila_campos)

        # Casilla para no volver a pedir la clave en esta PC (se olvida al cerrar).
        if self.con_recordar:
            self.chk_recordar = QCheckBox("No volver a pedir la clave en este equipo")
            self.chk_recordar.setToolTip("Solo dura mientras el sistema esté abierto.")
            fila_chk = C.margenes(QHBoxLayout(), esp=0)
            fila_chk.addStretch(1)
            fila_chk.addWidget(self.chk_recordar)
            fila_chk.addStretch(1)
            cc.addLayout(fila_chk)

        self.lbl_error = C.etiqueta("")
        self.lbl_error.setObjectName("error")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        cc.addWidget(self.lbl_error)

        barra = C.margenes(QHBoxLayout(), esp=10)
        barra.addStretch(1)
        barra.addWidget(C.boton_amarillo("🔓  INGRESAR", self._entrar))
        barra.addWidget(C.boton_secundario("✖  SALIR", self._cancelar))
        barra.addStretch(1)
        cc.addLayout(barra)

        self.lbl_base = C.etiqueta("Conectado a: %s" % cfg.describir(), ayuda=True)
        self.lbl_base.setAlignment(Qt.AlignCenter)
        cc.addWidget(self.lbl_base)

        raiz.addWidget(card, 1)

        # Enter = ingresar, Escape = salir (igual que en la versión anterior)
        self.txt_usuario.returnPressed.connect(self._entrar)
        self.txt_clave.returnPressed.connect(self._entrar)

    def _centrar(self):
        """Deja la ventana justo en el centro de la pantalla."""
        pantalla = self.screen().availableGeometry() if self.screen() else None
        if pantalla:
            self.move(pantalla.center().x() - self.width() // 2,
                      pantalla.center().y() - self.height() // 2)

    def showEvent(self, evento):
        """Al mostrarse se centra: así el ingreso sale siempre en medio de la pantalla."""
        super().showEvent(evento)
        if not self._centrada:
            self._centrada = True
            self._centrar()

    # ---------- acciones ----------
    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key_Escape:
            self._cancelar()
            return
        super().keyPressEvent(evento)

    def _entrar(self):
        usuario = (self.txt_usuario.text() or "").strip().upper()
        clave = (self.txt_clave.text() or "").strip()
        if not usuario or not clave:
            self.lbl_error.setText("Escriba su usuario y su clave.")
            return
        sesion = db.login(usuario, clave)
        if not sesion:
            self.lbl_error.setText("Usuario o clave incorrectos. Vuelva a intentarlo.")
            self.txt_clave.clear()
            self.txt_clave.setFocus()
            return
        if sesion.get("rol") not in self.roles:
            # Está bien identificado, pero esa área no es de su rol.
            permitidos = ", ".join(db.ETIQUETA_ROL.get(r, r) for r in self.roles)
            self.lbl_error.setText("Esa área es solo para: %s." % permitidos)
            self.txt_clave.clear()
            self.txt_clave.setFocus()
            return
        self.recordar = bool(self.chk_recordar is not None and self.chk_recordar.isChecked())
        self.resultado = sesion
        self.done(QDialog.Accepted)

    def _cancelar(self):
        self.resultado = None
        self.done(QDialog.Rejected)


def iniciar_sesion(app=None):
    """Muestra el ingreso y devuelve el usuario validado (o None si cancela)."""
    if app is None:
        crear_app()
    ven = LoginWindow()
    ven.exec()
    return ven.resultado


def pedir_sesion(padre=None, titulo=None, motivo="", roles=None, pedir_recordar=True):
    """Pide la clave antes de abrir una ventana del menú.

    Devuelve (sesión, recordar):
      · sesión  → {"usuario", "nombre", "rol"} ya validado, o None si se canceló;
      · recordar → True si el usuario marcó «no volver a pedir la clave en este
        equipo» (el menú lo tiene en cuenta mientras el sistema siga abierto).
    Con `roles` se limita quién puede entrar (por ejemplo, solo el superusuario).
    """
    crear_app()
    ven = LoginWindow(padre, titulo=titulo, motivo=motivo, roles=roles,
                      pedir_recordar=pedir_recordar)
    ven.exec()
    if not ven.resultado:
        return None, False
    return ven.resultado, bool(ven.recordar)


if __name__ == "__main__":
    import sys
    db.init_db()
    print(iniciar_sesion())
    sys.exit(0)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
