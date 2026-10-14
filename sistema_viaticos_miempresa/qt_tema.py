# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""qt_tema.py — Tema visual del sistema de viáticos para PySide6.

Los colores de marca son EXACTAMENTE los de `tema.py` (AZUL / AMARILLO) para que
la pantalla y los informes impresos (`reportes.py`) se vean iguales. Lo que agrega
este archivo es la capa de diseño de la interfaz nueva:

  - Tokens de color (fondo, tarjetas, bordes, textos, insignias de estado).
  - Escalado (`factor()` / `px()`): respeta `interfaz.zoom` de config.json.
  - `hoja_estilo()`: la hoja de estilo (QSS) completa que usan todas las ventanas.
  - `aplicar_tema(app)`: instala el estilo, la letra y el ícono de la aplicación.

Nada de aquí guarda datos ni habla con la base: es solo presentación.
"""
from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap

# --------------------------------------------------------------------- marca
# Idénticos a tema.py: así la pantalla y los reportes impresos coinciden.
AZUL = "#1F1CFF"          # azul Miempresa (acciones principales)
AZUL_CLARO = "#4B4BFF"    # azul al pasar el mouse
AZUL_SUAVE = "#E8E8FF"    # relleno azul muy claro
AMARILLO = "#FACC00"      # amarillo Miempresa (acción de confirmación)
AMARILLO_HOVER = "#FFD84D"
AMARILLO_SUAVE = "#FFF6CC"
BLANCO = "#FFFFFF"

# ------------------------------------------------------- superficie y texto
FONDO = "#F4F4F9"          # fondo de la página (gris lavanda claro)
TARJETA = "#FFFFFF"        # relleno de las tarjetas
TARJETA_SUAVE = "#FAFAFF"  # franjas de tabla / zonas suaves
BORDE = "#E4E4EF"          # borde normal de tarjeta
BORDE_FUERTE = "#D3D3E4"   # borde de los campos de entrada
TEXTO = "#1F2430"          # texto principal
TEXTO_SUAVE = "#6B7280"    # subtítulos y textos secundarios
TEXTO_TENUE = "#9AA1AE"    # pie de tabla, ayudas

# --------------------------------------------------------- navegación (menú)
MENU_FONDO = "#FFFFFF"
MENU_ITEM = "#4B5563"       # texto del botón de menú
MENU_ITEM_ICONO = "#111827"
SELECCION_FONDO = "#EDEBFD"  # botón de menú activo
SELECCION_BORDE = "#C9C4F2"
SELECCION_TEXTO = "#2A2AA8"

# --------------------------------------------------------------- estados
VERDE, VERDE_FONDO = "#15803D", "#DCFCE7"
NARANJA, NARANJA_FONDO = "#C2410C", "#FFEDD5"
AMBAR, AMBAR_FONDO = "#B45309", "#FEF3C7"
ROJO, ROJO_FONDO = "#B91C1C", "#FEE2E2"
INFORMATIVO, INFORMATIVO_FONDO = "#1D4ED8", "#DBEAFE"
MORADO, MORADO_FONDO = "#6D28D9", "#EDE9FE"
NEUTRO, NEUTRO_FONDO = "#4B5563", "#F3F4F6"

FUENTE = "Segoe UI"
RADIO = 10        # radio de las esquinas (10 px)
ALTO_CONTROL = 34  # alto de las cajas de texto y combos

# Estado del sistema → (color de texto, color de fondo) de la insignia.
ESTADOS_INSIGNIA = {
    "PENDIENTE": (AMBAR, AMBAR_FONDO),
    "EN PROCESO": (INFORMATIVO, INFORMATIVO_FONDO),
    "JUSTIFICADO": (VERDE, VERDE_FONDO),
    "CERRADO": (VERDE, VERDE_FONDO),
    "APROBADO": (VERDE, VERDE_FONDO),
    "ANULADO": (ROJO, ROJO_FONDO),
    "RECHAZADO": (ROJO, ROJO_FONDO),
    "AJUSTE": (MORADO, MORADO_FONDO),
    "ORIGINAL": (NEUTRO, NEUTRO_FONDO),
    "BORRADOR": (NEUTRO, NEUTRO_FONDO),
}


def color_estado(estado):
    """Color de texto y de fondo para la insignia de un estado."""
    return ESTADOS_INSIGNIA.get(str(estado or "").strip().upper(), (NEUTRO, NEUTRO_FONDO))


# ------------------------------------------------------------------ escalado
def zoom_guardado():
    """Zoom elegido en config.json (None = automático)."""
    try:
        valor = float(__import__("configuracion").leer().get("interfaz", {}).get("zoom", 0) or 0)
    except Exception:
        return None
    return valor if valor > 0 else None


def factor() -> float:
    """Cuánto se agranda o encoge la interfaz (1.0 = 100 %)."""
    z = zoom_guardado()
    return 1.0 if z is None else max(0.6, min(1.6, float(z)))


def px(valor, minimo=1) -> int:
    """Medida en píxeles ya escalada (para márgenes, altos y letras)."""
    return max(minimo, int(round(float(valor) * factor())))


def fuente(tamano=10, negrita=False):
    """Letra de la interfaz, ya escalada."""
    f = QFont(FUENTE, round(tamano * factor()))
    f.setBold(bool(negrita))
    return f


# --------------------------------------------------------------- hoja de estilo
def hoja_estilo() -> str:
    """Hoja de estilo (QSS) de todo el sistema: tarjetas, tablas, botones, campos."""
    a = {
        "AZUL": AZUL, "AZUL_CLARO": AZUL_CLARO, "AZUL_SUAVE": AZUL_SUAVE,
        "AMARILLO": AMARILLO, "AMARILLO_HOVER": AMARILLO_HOVER,
        "AMARILLO_SUAVE": AMARILLO_SUAVE,
        "FONDO": FONDO, "TARJETA": TARJETA, "TARJETA_SUAVE": TARJETA_SUAVE,
        "BORDE": BORDE, "BORDE_FUERTE": BORDE_FUERTE, "TEXTO": TEXTO,
        "TEXTO_SUAVE": TEXTO_SUAVE, "TEXTO_TENUE": TEXTO_TENUE,
        "MENU_ITEM": MENU_ITEM, "SELECCION_FONDO": SELECCION_FONDO,
        "SELECCION_BORDE": SELECCION_BORDE, "SELECCION_TEXTO": SELECCION_TEXTO,
        "ROJO": ROJO, "ROJO_FONDO": ROJO_FONDO, "VERDE": VERDE, "VERDE_FONDO": VERDE_FONDO,
        "RADIO": RADIO, "FUENTE": FUENTE,
        "F11": px(11, 9), "F12": px(12, 10), "F13": px(13, 11), "F15": px(15, 12),
        "F20": px(20, 15), "F24": px(24, 18),
        # Medidas compactas: con estos valores las pantallas entran completas sin
        # tener que bajar con la barra de desplazamiento.
        "ALTO": px(24, 20), "P7": px(5, 3), "P9": px(7, 4), "P14": px(11, 6),
    }
    return QSS_BASE % a + QSS_COMPONENTES % a

QSS_BASE = """
/* ------------------------------------------------------------ base */
QWidget {
    color: %(TEXTO)s;
    font-family: '%(FUENTE)s';
    font-size: %(F12)spx;
}
QMainWindow, QDialog, QWidget#pagina, QWidget#fondo, QScrollArea#lienzo,
QScrollArea#lienzo > QWidget > QWidget { background: %(FONDO)s; }
QToolTip {
    background: %(TEXTO)s; color: #FFFFFF; border: none;
    padding: %(P7)spx %(P9)spx; font-size: %(F12)spx;
}
QStatusBar { background: %(TARJETA)s; color: %(TEXTO_SUAVE)s; border-top: 1px solid %(BORDE)s; }

/* --------------------------------------------------------- tarjetas */
QFrame#tarjeta {
    background: %(TARJETA)s;
    border: 1px solid %(BORDE)s;
    border-radius: %(RADIO)spx;
}
QFrame#tarjetaBorde {
    background: %(TARJETA)s;
    border: 1px solid %(BORDE_FUERTE)s;
    border-radius: %(RADIO)spx;
}
QFrame#aviso {
    background: #F3F1FE;
    border: 1px solid %(SELECCION_BORDE)s;
    border-radius: %(RADIO)spx;
}
QFrame#barraLateral {
    background: %(TARJETA)s;
    border: none;
    border-right: 1px solid %(BORDE)s;
}
QFrame#cajaMenu { background: #F7F7FC; border: 1px solid %(BORDE)s; border-radius: %(RADIO)spx; }
QFrame#barraTitulo { background: %(TARJETA)s; border: none; border-bottom: 1px solid %(BORDE)s; }
QFrame#linea { background: %(BORDE)s; border: none; }

/* ---------------------------------------------------------- textos */
QLabel { background: transparent; }
QLabel#tituloPagina { font-size: %(F15)spx; font-weight: 700; color: %(TEXTO)s; }
QLabel#subtituloPagina { font-size: %(F12)spx; color: %(TEXTO_SUAVE)s; }
QLabel#tituloTarjeta { font-size: %(F13)spx; font-weight: 700; color: %(TEXTO)s; }
QLabel#subtituloTarjeta { font-size: %(F11)spx; color: %(TEXTO_SUAVE)s; }
QLabel#etiquetaKpi { font-size: %(F11)spx; color: %(TEXTO_SUAVE)s; }
QLabel#valorKpi { font-size: %(F20)spx; font-weight: 700; color: %(AZUL)s; }
QLabel#notaKpi { font-size: %(F11)spx; color: %(AZUL)s; }
QLabel#ayuda { font-size: %(F11)spx; color: %(TEXTO_TENUE)s; }
QLabel#contador { font-size: %(F11)spx; color: %(TEXTO_TENUE)s; }
QLabel#error { color: %(ROJO)s; font-weight: 700; }
QLabel#ok { color: %(VERDE)s; font-weight: 700; }
QLabel#clave { font-weight: 700; color: %(TEXTO_SUAVE)s; }
QLabel#logoTexto { color: %(AZUL)s; font-size: %(F15)spx; font-weight: 700; }

/* -------------------------------------------------------- botones */
QPushButton {
    background: %(AZUL)s; color: #FFFFFF; border: none;
    border-radius: %(RADIO)spx; padding: %(P7)spx %(P14)spx;
    font-weight: 700; font-size: %(F12)spx;
}
QPushButton:hover { background: %(AZUL_CLARO)s; }
QPushButton:disabled { background: #D9DDE3; color: #8A8F98; }
QPushButton#amarillo { background: %(AMARILLO)s; color: #1C1C1C; }
QPushButton#amarillo:hover { background: %(AMARILLO_HOVER)s; }
QPushButton#secundario {
    background: #F3F4F6; color: %(TEXTO)s; border: 1px solid %(BORDE_FUERTE)s;
}
QPushButton#secundario:hover { background: #E9EAF0; }
QPushButton#borde {
    background: %(TARJETA)s; color: %(AZUL)s;
    border: 1px solid %(AZUL)s; border-radius: %(ALTO)spx;
    padding: %(P9)spx %(P14)spx;
}
QPushButton#borde:hover { background: %(AZUL_SUAVE)s; }
QPushButton#peligro { background: %(ROJO)s; color: #FFFFFF; }
QPushButton#peligro:hover { background: #DC2626; }
QPushButton#plano {
    background: transparent; color: %(AZUL)s; border: none;
    padding: %(P7)spx; font-weight: 700;
}
QPushButton#plano:hover { color: %(AZUL_CLARO)s; }
QPushButton#menu {
    background: transparent; color: %(MENU_ITEM)s; border: 1px solid transparent;
    border-radius: %(RADIO)spx; padding: %(P9)spx %(P9)spx;
    text-align: left; font-weight: 600; font-size: %(F12)spx;
}
QPushButton#menu:hover { background: #F5F5FB; color: %(SELECCION_TEXTO)s; }
QPushButton#menu:checked {
    background: %(SELECCION_FONDO)s; border: 1px solid %(SELECCION_BORDE)s;
    color: %(SELECCION_TEXTO)s; font-weight: 700;
}
QPushButton#menuGrande {
    background: %(AZUL)s; color: #FFFFFF; border: none;
    border-radius: %(RADIO)spx; padding: %(P14)spx; text-align: left;
    font-weight: 700; font-size: %(F13)spx;
}
QPushButton#menuGrande:hover { background: %(AZUL_CLARO)s; }
QPushButton#menuGrandeGris {
    background: #F3F4F6; color: %(TEXTO)s; border: 1px solid %(BORDE_FUERTE)s;
    border-radius: %(RADIO)spx; padding: %(P14)spx; text-align: left;
    font-weight: 700; font-size: %(F13)spx;
}
QPushButton#menuGrandeGris:hover { background: #E9EAF0; }
QPushButton#barraHerramienta {
    background: %(TARJETA)s; color: %(TEXTO)s; border: 1px solid %(BORDE_FUERTE)s;
    border-radius: %(P7)spx; padding: %(P7)spx %(P9)spx;
    font-weight: 600; font-size: %(F12)spx;
}
QPushButton#barraHerramienta:hover { background: #F5F5FB; color: %(AZUL)s; }
QPushButton#pestana {
    background: %(TARJETA)s; color: %(TEXTO)s; border: 1px solid %(BORDE_FUERTE)s;
    border-radius: %(RADIO)spx; padding: %(P9)spx %(P14)spx;
    font-weight: 700; font-size: %(F12)spx;
}
QPushButton#pestana:checked { background: %(AZUL)s; color: #FFFFFF; border-color: %(AZUL)s; }
QPushButton#encabezado {
    background: transparent; color: %(TEXTO_SUAVE)s; border: none;
    border-bottom: 1px solid %(BORDE_FUERTE)s; border-radius: 0px;
    padding: %(P9)spx; text-align: left; font-weight: 700; font-size: %(F11)spx;
}
QPushButton#encabezado:hover { color: %(AZUL)s; }
"""

QSS_COMPONENTES = """
/* --------------------------------------------------------- campos */
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox,
QPlainTextEdit, QTextEdit {
    background: %(TARJETA)s; color: %(TEXTO)s;
    border: 1px solid %(BORDE_FUERTE)s; border-radius: %(P7)spx;
    padding: %(P7)spx %(P9)spx;
    selection-background-color: %(AZUL)s; selection-color: #FFFFFF;
}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox { min-height: %(ALTO)spx; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QPlainTextEdit:focus, QTextEdit:focus { border: 2px solid %(AZUL)s; }
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QPlainTextEdit:disabled,
QTextEdit:disabled, QSpinBox:disabled { background: #F3F4F6; color: %(TEXTO_TENUE)s; }
QLineEdit[error="true"] { border: 2px solid %(ROJO)s; background: %(ROJO_FONDO)s; }
QLineEdit#buscar { padding-left: %(P14)spx; min-height: %(ALTO)spx; }
QLineEdit#filtro {
    min-height: %(P14)spx; border-radius: 6px; font-size: %(F11)spx;
    padding: 1px 4px; color: %(TEXTO_SUAVE)s;
}
QComboBox::drop-down, QDateEdit::drop-down { border: none; width: %(F20)spx; }
QComboBox::down-arrow, QDateEdit::down-arrow {
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid %(AZUL)s; width: 0px; height: 0px; margin-right: %(P7)spx;
}
QComboBox QAbstractItemView {
    background: %(TARJETA)s; border: 1px solid %(BORDE_FUERTE)s; border-radius: %(P7)spx;
    selection-background-color: %(AZUL_SUAVE)s; selection-color: %(SELECCION_TEXTO)s;
    padding: 2px; outline: none;
}
QCheckBox, QRadioButton { spacing: %(P7)spx; padding: %(P7)spx 0px; font-size: %(F12)spx; }
QCheckBox::indicator, QRadioButton::indicator { width: %(F15)spx; height: %(F15)spx; }
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid %(BORDE_FUERTE)s; background: %(TARJETA)s;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: %(AZUL)s; border: 1px solid %(AZUL)s;
}
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: %(F11)spx; }
QGroupBox {
    background: %(TARJETA)s; border: 1px solid %(BORDE)s; border-radius: %(RADIO)spx;
    margin-top: %(F15)spx; padding: %(P9)spx;
    font-weight: 700; font-size: %(F12)spx;
}
QGroupBox::title {
    subcontrol-origin: margin; left: %(P14)spx; padding: 0px %(P7)spx;
    color: %(TEXTO_SUAVE)s; font-weight: 700;
}

/* ---------------------------------------------------------- tablas */
QTableWidget, QTableView {
    background: %(TARJETA)s; alternate-background-color: %(TARJETA_SUAVE)s;
    border: none; gridline-color: %(BORDE)s; outline: none;
    selection-background-color: %(AZUL_SUAVE)s; selection-color: %(TEXTO)s;
    font-size: %(F12)spx;
}
QTableWidget::item, QTableView::item { padding: %(P7)spx %(P9)spx; border-bottom: 1px solid %(BORDE)s; }
QTableWidget::item:selected, QTableView::item:selected { color: %(TEXTO)s; }
QHeaderView { background: transparent; border: none; }
QHeaderView::section {
    background: %(TARJETA)s; color: %(TEXTO_SUAVE)s; border: none;
    border-bottom: 1px solid %(BORDE_FUERTE)s;
    padding: %(P9)spx %(P9)spx; font-weight: 700; font-size: %(F11)spx;
}
QHeaderView::section:hover { color: %(AZUL)s; }
QTableCornerButton::section { background: %(TARJETA)s; border: none; }

/* --------------------------------------------------- listas y árboles */
QAbstractScrollArea { background: %(TARJETA)s; border: none; }
QListWidget, QListView, QTreeWidget, QTreeView, QColumnView {
    background: %(TARJETA)s; alternate-background-color: %(TARJETA_SUAVE)s;
    border: 1px solid %(BORDE)s; border-radius: %(P7)spx; outline: none;
    selection-background-color: %(SELECCION_FONDO)s; selection-color: %(SELECCION_TEXTO)s;
    font-size: %(F12)spx;
}
QListWidget::item, QListView::item, QTreeWidget::item, QTreeView::item {
    color: %(TEXTO)s; padding: %(P7)spx %(P9)spx; border: none;
}
QListWidget::item:hover, QListView::item:hover,
QTreeWidget::item:hover, QTreeView::item:hover { background: #F5F5FB; }
QListWidget::item:selected, QListView::item:selected,
QTreeWidget::item:selected, QTreeView::item:selected {
    background: %(SELECCION_FONDO)s; color: %(SELECCION_TEXTO)s;
}
QTabWidget > QWidget { background: transparent; }
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: %(AZUL_SUAVE)s; border-bottom: 1px solid %(BORDE)s;
}
QCalendarWidget QToolButton {
    background: transparent; color: %(TEXTO)s; border: none; border-radius: %(P7)spx;
    padding: %(P7)spx %(P9)spx; font-weight: 700; font-size: %(F12)spx;
}
QCalendarWidget QToolButton:hover { background: #D7D7F5; }
QCalendarWidget QToolButton::menu-indicator { image: none; }
QCalendarWidget QSpinBox {
    background: %(TARJETA)s; color: %(TEXTO)s; border: 1px solid %(BORDE_FUERTE)s;
    border-radius: 6px; padding: 2px %(P7)spx; min-height: %(ALTO)spx;
}
QCalendarWidget QAbstractItemView {
    background: %(TARJETA)s; color: %(TEXTO)s;
    selection-background-color: %(AZUL)s; selection-color: #FFFFFF; outline: none;
}
QCalendarWidget QAbstractItemView:disabled { color: %(TEXTO_TENUE)s; }
QCalendarWidget QMenu { background: %(TARJETA)s; color: %(TEXTO)s; }

/* -------------------------------------------------------- pestañas */
QTabWidget::pane {
    border: 1px solid %(BORDE)s; border-radius: %(RADIO)spx;
    background: %(TARJETA)s; top: -1px;
}
QTabBar::tab {
    background: transparent; color: %(TEXTO_SUAVE)s; border: none;
    padding: %(P9)spx %(P14)spx; margin-right: %(P7)spx;
    font-weight: 700; font-size: %(F12)spx;
}
QTabBar::tab:selected { color: %(AZUL)s; border-bottom: 2px solid %(AZUL)s; }
QTabBar::tab:hover { color: %(AZUL_CLARO)s; }

/* ---------------------------------------------------- desplazamiento */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: %(F13)spx; margin: 0px; }
QScrollBar::handle:vertical {
    background: #C9CBD6; border-radius: %(P7)spx; min-height: %(F24)spx; margin: 2px;
}
QScrollBar::handle:vertical:hover { background: #A9ACBE; }
QScrollBar:horizontal { background: transparent; height: %(F13)spx; margin: 0px; }
QScrollBar::handle:horizontal {
    background: #C9CBD6; border-radius: %(P7)spx; min-width: %(F24)spx; margin: 2px;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0px; width: 0px; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* -------------------------------------------------------- menú/barra */
QMenuBar { background: %(TARJETA)s; color: %(TEXTO)s; }
QMenuBar::item:selected { background: %(AZUL_SUAVE)s; color: %(SELECCION_TEXTO)s; }
QMenu { background: %(TARJETA)s; border: 1px solid %(BORDE_FUERTE)s; padding: %(P7)spx; }
QMenu::item { padding: %(P7)spx %(P14)spx; border-radius: 6px; }
QMenu::item:selected { background: %(AZUL_SUAVE)s; color: %(SELECCION_TEXTO)s; }
QProgressBar {
    background: #EDEDF5; border: none; border-radius: %(P7)spx; height: %(F12)spx;
    text-align: center; font-size: %(F11)spx; color: %(TEXTO_SUAVE)s;
}
QProgressBar::chunk { background: %(AZUL)s; border-radius: %(P7)spx; }
QMessageBox { background: %(TARJETA)s; }
QMessageBox QLabel { color: %(TEXTO)s; font-size: %(F13)spx; }

/* ------------------------------------------------ cajas destacadas */
/* El «efectivo sugerido» del viático: se ve distinto del resto para que no se
   confunda con un campo más del formulario. */
QFrame#tarjetaSugerido {
    background: %(AMARILLO_SUAVE)s;
    border: 2px solid %(AMARILLO)s;
    border-radius: %(RADIO)spx;
}
QLabel#valorSugerido { font-size: %(F24)spx; font-weight: 700; color: %(TEXTO)s; }

/* Los renglones de datos de la justificación: una franja clara y la siguiente blanca,
   para que cada dato se distinga del de arriba. */
QFrame#bandaDatos {
    background: #F4F7FC;
    border: 1px solid #E4E9F3;
    border-radius: %(P7)spx;
}
QFrame#bandaDatosPar { background: transparent; border: none; }
"""

# ------------------------------------------------------------ instalación
def paleta_clara():
    """Paleta CLARA explícita para toda la aplicación.

    Windows puede estar en modo oscuro: si no se fija la paleta, los controles que
    no llevan estilo propio (listas, árboles, calendario, menús, barras…) se dibujan
    oscuros y el texto oscuro del tema queda encima: no se lee nada. Con esta paleta
    el sistema se ve igual en cualquier equipo, en modo claro u oscuro.
    """
    from PySide6.QtGui import QPalette
    p = QPalette()
    p.setColor(QPalette.Window, QColor(FONDO))
    p.setColor(QPalette.WindowText, QColor(TEXTO))
    p.setColor(QPalette.Base, QColor(TARJETA))
    p.setColor(QPalette.AlternateBase, QColor(TARJETA_SUAVE))
    p.setColor(QPalette.Text, QColor(TEXTO))
    p.setColor(QPalette.Button, QColor(TARJETA))
    p.setColor(QPalette.ButtonText, QColor(TEXTO))
    p.setColor(QPalette.BrightText, QColor("#FFFFFF"))
    p.setColor(QPalette.Link, QColor(AZUL))
    p.setColor(QPalette.LinkVisited, QColor(AZUL))
    p.setColor(QPalette.Highlight, QColor(AZUL_SUAVE))
    p.setColor(QPalette.HighlightedText, QColor(SELECCION_TEXTO))
    p.setColor(QPalette.ToolTipBase, QColor(TEXTO))
    p.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))
    p.setColor(QPalette.PlaceholderText, QColor(TEXTO_TENUE))
    p.setColor(QPalette.Light, QColor("#FFFFFF"))
    p.setColor(QPalette.Midlight, QColor("#EFEFF7"))
    p.setColor(QPalette.Mid, QColor(BORDE_FUERTE))
    p.setColor(QPalette.Dark, QColor("#C9CBD6"))
    p.setColor(QPalette.Shadow, QColor("#B9BBC6"))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXTO_TENUE))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXTO_TENUE))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXTO_TENUE))
    p.setColor(QPalette.Disabled, QPalette.Base, QColor("#F3F4F6"))
    p.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#EDEDF5"))
    p.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(TEXTO_TENUE))
    return p


def aplicar_tema(app=None):
    """Instala el estilo, la paleta clara, la letra y el ícono del sistema."""
    from PySide6.QtWidgets import QApplication
    app = app or QApplication.instance()
    if app is None:
        return
    try:
        app.setStyle("Fusion")            # mismo dibujo en cualquier Windows
    except Exception:
        pass
    app.setPalette(paleta_clara())        # aunque Windows esté en modo oscuro
    app.setFont(fuente(10))
    app.setStyleSheet(hoja_estilo())
    icono = icono_app()
    if icono is not None:
        app.setWindowIcon(icono)


def icono_app():
    """Ícono del sistema (icono.ico o el logo), si se encuentra."""
    try:
        import database as db
        for nombre in ("icono.ico", "image.png"):
            ruta = db.recurso(nombre)
            if ruta is not None and ruta.exists():
                return QIcon(str(ruta))
    except Exception:
        pass
    return None


def logo_pixmap(alto=None):
    """Logo de Miempresa ya escalado (o None si no está el archivo)."""
    try:
        import database as db
        ruta = db.recurso("image.png")
        if ruta is None or not ruta.exists():
            return None
        pix = QPixmap(str(ruta))
        if pix.isNull():
            return None
        if alto:
            pix = pix.scaledToHeight(px(alto), Qt.SmoothTransformation)
        return pix
    except Exception:
        return None


def preparar_dpi():
    """Avisa a Windows que el programa ya se encarga del escalado de la pantalla.

    Igual que `tema.preparar_dpi()` (versión Tk), pero sin depender de tkinter:
    se llama una sola vez, antes de crear la primera ventana. Se desactiva con
    `interfaz.dpi_consciente: false` en config.json.
    """
    try:
        valor = __import__("configuracion").leer().get("interfaz", {}).get("dpi_consciente", True)
    except Exception:
        valor = True
    if valor in (False, 0, "0", "false", "False", "no", "NO"):
        return False
    if sys.platform != "win32":
        return False
    try:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        return False
    return True


def guardar_zoom(zoom):
    """Deja el zoom elegido en config.json (0 = automático). Devuelve True si pudo."""
    try:
        import configuracion as cfg
        cfg.guardar({"interfaz": {"zoom": 0 if zoom is None else round(float(zoom), 3)}})
        return True
    except Exception:
        return False


def texto_contraste(fondo):
    """Blanco o negro según el color de fondo (para insignias)."""
    c = QColor(fondo)
    return "#1C1C1C" if (c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114) > 160 else "#FFFFFF"


def estilo_insignia(fondo, color=None, radio=None):
    """Hoja de estilo de una insignia (etiqueta redondeada) ya calculada."""
    color = color or texto_contraste(fondo)
    r = px(9, 6) if radio is None else radio
    return ("QLabel { background: %s; color: %s; border: none; border-radius: %spx;"
            " padding: %spx %spx; font-size: %spx; font-weight: 700; }"
            % (fondo, color, r, px(2, 1), px(9, 5), px(11, 9)))


def formato_moneda(valor):
    """Valor en el formato que usa todo el sistema: $12.50 (o '-' si es cero)."""
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        v = 0.0
    return "-" if abs(v) < 0.005 else "$%.2f" % v


def formato_fecha(iso):
    """De 'AAAA-MM-DD' (o con hora) a 'DD/MM/AAAA'; deja el texto si no encaja."""
    if not iso:
        return ""
    try:
        y, m, d = str(iso)[:10].split("-")
        return "%s/%s/%s" % (d, m, y)
    except Exception:
        return str(iso)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
