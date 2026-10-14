# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""qt_comunes.py — Componentes visuales reutilizables (PySide6) del sistema de viáticos.

Aquí vive todo lo que se repite en las pantallas: tarjetas, tablas con buscador y
exportación a Excel/CSV, botones, cajas de texto, campos de fecha y hora, insignias
de estado y los avisos (reemplazan a `messagebox` y `simpledialog` de Tkinter).

Ninguna función de este archivo habla con la base de datos: es solo presentación.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QDate, QEvent, QRegularExpression, QSize, Qt, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCalendarWidget, QCheckBox, QComboBox, QCompleter,
    QDateEdit, QDialog, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import qt_tema as T

HORAS = ["%02d:%02d" % (h, m) for h in range(24) for m in (0, 15, 30, 45)]


# ------------------------------------------------------------- utilidades
def margenes(layout, izq=0, arriba=0, der=0, abajo=0, esp=0):
    """Márgenes y separación de un layout ya escalados (px)."""
    layout.setContentsMargins(T.px(izq), T.px(arriba), T.px(der), T.px(abajo))
    layout.setSpacing(T.px(esp))
    return layout


def fila(*widgets, esp=8, estirar=None, margen=(0, 0, 0, 0)):
    """Contenedor horizontal con los widgets indicados (None = espacio elástico)."""
    caja = QWidget()
    lay = margenes(QHBoxLayout(caja), margen[0], margen[1], margen[2], margen[3], esp)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        elif isinstance(w, str):
            lay.addWidget(QLabel(w))
        else:
            lay.addWidget(w)
    if estirar is not None:
        lay.setStretch(estirar, 1)
    return caja


def columna(*widgets, esp=8, margen=(0, 0, 0, 0)):
    """Contenedor vertical con los widgets indicados (None = espacio elástico)."""
    caja = QWidget()
    lay = margenes(QVBoxLayout(caja), margen[0], margen[1], margen[2], margen[3], esp)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        elif isinstance(w, str):
            lay.addWidget(QLabel(w))
        else:
            lay.addWidget(w)
    return caja


def linea(horizontal=True):
    """Línea divisoria gris (ocupa todo el largo o el alto disponible)."""
    l = QFrame()
    l.setObjectName("linea")
    if horizontal:
        l.setFixedHeight(1)
        l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    else:
        l.setFixedWidth(1)
        l.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    return l


def etiqueta(texto="", clave=False, ayuda=False, titulo=None, rubrica=None):
    """Etiqueta de texto con el rol visual que se pida.

    `titulo`: "pagina" | "subtitulo" | "tarjeta" | "subtituloTarjeta"
    `clave`: negrita (etiqueta de un dato).  `ayuda`: letra pequeña tenue.
    `rubrica`: texto pequeño de apoyo (nombre de columna, contador…).
    """
    l = QLabel(texto or "")
    if titulo in ("pagina", "subtitulo", "tarjeta", "subtituloTarjeta"):
        l.setObjectName({"pagina": "tituloPagina", "subtitulo": "subtituloPagina",
                         "tarjeta": "tituloTarjeta",
                         "subtituloTarjeta": "subtituloTarjeta"}[titulo])
    elif rubrica:
        # «contador» y cualquier otro estilo de la hoja que se pida por su nombre
        # (por ejemplo «grupoMenu», el título de un grupo de la barra del menú).
        l.setObjectName(rubrica)
    elif clave:
        l.setObjectName("clave")
    elif ayuda:
        l.setObjectName("ayuda")
    # Todas las etiquetas se ajustan solas: así ninguna obliga a ensanchar la pantalla
    # (el texto largo se reparte en dos líneas en lugar de empujar el resto fuera).
    l.setWordWrap(True)
    return l


# --------------------------------------------------------------- botones
def boton(texto, cb=None, estilo="primario", ancho=None, icono=None, herramienta=None):
    """Botón con uno de los estilos del tema.

    estilos: primario · amarillo · secundario · borde · peligro · plano ·
             barraHerramienta · menu · menuGrande · menuGrandeGris · pestana
    """
    b = QPushButton("%s  %s" % (icono, texto) if icono else texto)
    if estilo != "primario":
        b.setObjectName(estilo)
    b.setCursor(Qt.PointingHandCursor)
    if ancho:
        b.setMinimumWidth(T.px(ancho))
    if herramienta:
        b.setToolTip(herramienta)
    if cb:
        b.clicked.connect(cb)
    return b


def boton_primario(texto, cb=None, **kw):
    return boton(texto, cb, "primario", **kw)


def boton_amarillo(texto, cb=None, **kw):
    return boton(texto, cb, "amarillo", **kw)


def boton_secundario(texto, cb=None, **kw):
    return boton(texto, cb, "secundario", **kw)


def boton_borde(texto, cb=None, **kw):
    return boton(texto, cb, "borde", **kw)


def boton_peligro(texto, cb=None, **kw):
    return boton(texto, cb, "peligro", **kw)


def boton_plano(texto, cb=None, **kw):
    return boton(texto, cb, "plano", **kw)


def boton_herramienta(texto, cb=None, **kw):
    return boton(texto, cb, "barraHerramienta", **kw)


def boton_menu(texto, cb=None, marcable=True, alto=30):
    """Botón de la barra lateral del menú principal."""
    b = boton(texto, cb, "menu")
    b.setCheckable(marcable)
    b.setMinimumHeight(T.px(alto, 22))
    b.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    return b


# ---------------------------------------------------------------- campos
def campo(texto="", ancho=None, placeholder="", solo_lectura=False, maximo=None,
          mayusculas=False, cb=None):
    """Caja de texto de una línea."""
    e = QLineEdit("" if texto is None else str(texto))
    if ancho:
        e.setFixedWidth(T.px(ancho))
    if placeholder:
        e.setPlaceholderText(placeholder)
    if maximo:
        e.setMaxLength(int(maximo))
    if solo_lectura:
        e.setReadOnly(True)
    if mayusculas:
        def _mayus(t):
            if t != t.upper():
                e.setText(t.upper())
        e.textChanged.connect(_mayus)
    if cb:
        e.textChanged.connect(lambda t: cb(t))
    return e


def campo_clave(ancho=None, placeholder=""):
    """Caja de texto para claves (oculta lo que se escribe)."""
    e = campo("", ancho, placeholder)
    e.setEchoMode(QLineEdit.Password)
    return e


def campo_entero(valor=0, minimo=-999999999, maximo=999999999, ancho=None, cb=None):
    s = QSpinBox()
    s.setRange(int(minimo), int(maximo))
    s.setValue(int(valor or 0))
    if ancho:
        s.setFixedWidth(T.px(ancho))
    if cb:
        s.valueChanged.connect(cb)
    return s


def campo_decimal(valor=0.0, minimo=-999999999.0, maximo=999999999.0, decimales=2,
                  ancho=None, cb=None, sufijo=""):
    s = QDoubleSpinBox()
    s.setDecimals(int(decimales))
    s.setRange(float(minimo), float(maximo))
    s.setValue(float(valor or 0))
    if sufijo:
        s.setSuffix(" " + sufijo)
    if ancho:
        s.setFixedWidth(T.px(ancho))
    if cb:
        s.valueChanged.connect(cb)
    return s


def campo_area(texto="", alto=90, solo_lectura=False, ancho=None, cb=None):
    a = QPlainTextEdit("" if texto is None else str(texto))
    a.setFixedHeight(T.px(alto))
    if ancho:
        a.setFixedWidth(T.px(ancho))
    a.setReadOnly(solo_lectura)
    if cb:
        a.textChanged.connect(lambda: cb(a.toPlainText()))
    return a


# -------------------------------------------------------------- listas
def combo(valores, actual=None, ancho=None, cb=None, editable=False):
    """Lista desplegable. `actual` marca la opción que queda elegida."""
    c = QComboBox()
    c.addItems([str(v) for v in (valores or [])])
    c.setEditable(bool(editable))
    if actual is not None:
        poner_combo(c, actual)
    if ancho:
        c.setFixedWidth(T.px(ancho))
    if cb:
        c.currentTextChanged.connect(cb)
    return c


def poner_combo(c, valor):
    """Deja elegido `valor` en la lista (agrega la opción si todavía no está)."""
    texto = "" if valor is None else str(valor)
    i = c.findText(texto, Qt.MatchFixedString)
    if i < 0 and texto:
        c.addItem(texto)
        i = c.findText(texto, Qt.MatchFixedString)
    c.setCurrentIndex(max(i, 0))
    return c


class ComboAuto(QComboBox):
    """Lista editable que filtra mientras se escribe (reemplaza a `tema.AutoCombo`).

    `proveedor` puede ser una lista de opciones o una función que devuelve la lista
    (así se ve siempre lo último, incluso con la base central del servidor).

    La función se consulta **una vez cada pocos segundos** y no en cada clic: antes,
    abrir la lista (por ejemplo la de cantones, con ~200 nombres) iba a la base y volvía
    a dibujar todo, y por eso la ventana parecía quedarse pensando. Con esto se siente
    al instante y los nombres nuevos aparecen igual unos segundos después.
    """

    SEGUNDOS_MEMORIA = 5        # cuánto se recuerda la lista antes de volver a pedirla

    def __init__(self, proveedor, ancho=None, cb=None, padre=None):
        super().__init__(padre)
        self._proveedor = proveedor
        self._memoria = None            # (momento, opciones)
        self._pintadas = None           # lo que está dibujado ahora
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        if ancho:
            self.setFixedWidth(T.px(ancho))
        comp = QCompleter(self.model(), self)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(comp)
        self.refrescar_opciones()
        if cb:
            self.currentTextChanged.connect(cb)

    def opciones(self, forzar=False):
        """Opciones de la lista (se vuelven a pedir solo si pasó el tiempo o se fuerza)."""
        ahora = time.monotonic()
        if (not forzar and self._memoria is not None
                and ahora - self._memoria[0] < self.SEGUNDOS_MEMORIA):
            return list(self._memoria[1])
        try:
            valores = self._proveedor() if callable(self._proveedor) else self._proveedor
        except Exception:
            valores = []
        lista = [str(v) for v in (valores or [])]
        self._memoria = (ahora, lista)
        return list(lista)

    def refrescar_opciones(self, forzar=True):
        """Vuelve a leer la lista (sin perder lo que la persona escribió).

        Si la lista no cambió no se vuelve a dibujar: así no parpadea ni se pierde lo
        que estaba elegido. `forzar=False` (lo que se usa al abrir la lista) aprovecha lo
        que se leyó hace un momento y no va de nuevo a la base.
        """
        texto = self.currentText()
        lista = self.opciones(forzar=forzar)
        if lista != self._pintadas:
            self.blockSignals(True)
            self.clear()
            self.addItems(lista)
            self._pintadas = list(lista)
            self.setCurrentIndex(-1)
            self.setEditText(texto)
            self.blockSignals(False)
        return self

    def valor(self):
        return (self.currentText() or "").strip()

    def set_valor(self, valor):
        self.setEditText("" if valor is None else str(valor))
        return self

    def showPopup(self):
        self.refrescar_opciones(forzar=False)     # sin ir a la base en cada clic
        super().showPopup()


def combo_auto(proveedor, ancho=None, cb=None):
    """Atajo para crear un `ComboAuto`."""
    return ComboAuto(proveedor, ancho, cb)


def check(texto, valor=False, cb=None):
    c = QCheckBox(texto)
    c.setChecked(bool(valor))
    if cb:
        c.toggled.connect(cb)
    return c


def radios(opciones, actual=None, horizontal=False, cb=None):
    """Opciones excluyentes: `opciones` = [(texto, valor), ...].

    Devuelve (contenedor, {valor: boton}).
    """
    caja = QWidget()
    lay = QHBoxLayout(caja) if horizontal else QVBoxLayout(caja)
    margenes(lay, esp=6)
    grupo = QButtonGroup(caja)
    botones = {}
    for i, (texto, valor) in enumerate(opciones):
        b = QRadioButton(str(texto))
        grupo.addButton(b, i)
        b.setProperty("valor", valor)
        b.setChecked(valor == actual)
        if cb:
            b.toggled.connect(lambda activo, v=valor: cb(v) if activo else None)
        lay.addWidget(b)
        botones[valor] = b
    return caja, botones


class CampoFecha(QDateEdit):
    """Campo de fecha con calendario (reemplaza a `dateentry.DateEntry`).

    Si está vacío, `valor()` devuelve "" — igual que antes, cuando se podía dejar
    una fecha en blanco (por ejemplo «fecha de regreso» todavía desconocida).
    """

    VACIO = QDate(1900, 1, 1)

    def __init__(self, iso=None, ancho=120, cb=None, padre=None):
        super().__init__(padre)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setMinimumDate(self.VACIO)
        self.setMaximumDate(QDate(2100, 12, 31))
        self.setSpecialValueText(" ")            # fecha vacía: se ve en blanco
        self.setDate(self.VACIO)
        self.setFixedWidth(T.px(ancho))
        # Calendario ordenado y COMPLETO: semana que empieza el lunes, sin números de
        # semana y con tamaño mínimo suficiente para que entren las seis semanas del
        # mes (antes la ventanita quedaba corta y solo se veían los primeros días).
        cal = self.calendarWidget()
        if cal is not None:
            cal.setFirstDayOfWeek(Qt.Monday)
            cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
            cal.setGridVisible(True)
            cal.setMinimumSize(T.px(300, 250), T.px(220, 180))
            cal.installEventFilter(self)
        if iso:
            self.set_valor(iso)
        if cb:
            self.dateChanged.connect(lambda _f: cb(self.valor()))

    def eventFilter(self, objeto, evento):
        """Al abrirse el calendario de un campo vacío, muestra el mes de HOY.

        El sistema usa el 01/01/1900 para decir «fecha vacía»; sin esto, al abrir el
        calendario aparecía «enero 1900» en lugar del mes en el que se está trabajando.
        """
        if evento.type() == QEvent.Show and not self.valor():
            cal = self.calendarWidget()
            if cal is not None:
                hoy = QDate.currentDate()
                cal.setCurrentPage(hoy.year(), hoy.month())
        return super().eventFilter(objeto, evento)

    def focusInEvent(self, evento):
        """Al entrar al campo, si está vacío el calendario abre en el mes de hoy."""
        super().focusInEvent(evento)
        if not self.valor():
            hoy = QDate.currentDate()
            cal = self.calendarWidget()
            if cal is not None:
                cal.setCurrentPage(hoy.year(), hoy.month())

    def valor(self):
        """'AAAA-MM-DD' o "" si el campo está vacío."""
        f = self.date()
        return "" if f == self.VACIO else f.toString("yyyy-MM-dd")

    def set_valor(self, iso):
        texto = str(iso or "").strip()
        if not texto:
            self.setDate(self.VACIO)
            return self
        f = QDate.fromString(texto[:10], "yyyy-MM-dd")
        self.setDate(f if f.isValid() else self.VACIO)
        return self

    def hoy(self):
        self.setDate(QDate.currentDate())
        return self

    def limpiar(self):
        self.setDate(self.VACIO)
        return self


class CampoHora(QComboBox):
    """Hora en formato 24 h por cuartos (00:00 … 23:45), como en los viáticos."""

    def __init__(self, valor=None, ancho=90, cb=None, padre=None):
        super().__init__(padre)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.addItems(HORAS)
        self.setCurrentIndex(-1)
        self.setFixedWidth(T.px(ancho))
        self.lineEdit().setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^([01]\d|2[0-3]):?([0-5]\d)?$"), self))
        self.set_valor(valor)
        if cb:
            self.currentTextChanged.connect(lambda t: cb(self.valor()))

    def valor(self):
        """'HH:MM' (o "" si está vacío), tolerando «9», «930», «9:30»."""
        texto = (self.currentText() or "").strip()
        if not texto:
            return ""
        if ":" in texto:
            h, _, m = texto.partition(":")
        else:
            cifras = texto.zfill(4)[-4:] if len(texto) <= 4 else texto
            h, m = cifras[:-2], cifras[-2:]
        try:
            return "%02d:%02d" % (int(h or 0) % 24, int(m or 0) % 60)
        except ValueError:
            return ""

    def set_valor(self, valor):
        self.setEditText((valor or "").strip())
        return self


def rejilla(filas, esp=8, etiqueta_ancho=None, espacio_medio=False):
    """Formulario en rejilla: `filas` = [[(etiqueta, widget), ...], ...].

    Las columnas se quedan pegadas a la izquierda (el espacio sobrante va al final),
    así los campos no se riegan por toda la tarjeta y el formulario se ve ordenado.
    Con `espacio_medio` el sobrante se reparte entre la primera y la segunda pareja de
    cada fila: queda un formulario de dos columnas que llena la tarjeta, sin que los
    campos se estiren ni la pantalla tenga que ser más ancha.
    """
    caja = QWidget()
    g = QGridLayout(caja)
    margenes(g, esp=6)
    g.setHorizontalSpacing(T.px(esp))
    g.setVerticalSpacing(T.px(6))
    columnas = 0
    for i, datos in enumerate(filas):
        col = 0
        for etq, widget in datos:
            if etq:
                lbl = etiqueta(str(etq), clave=True)
                if etiqueta_ancho:
                    lbl.setFixedWidth(T.px(etiqueta_ancho))
                g.addWidget(lbl, i, col, Qt.AlignVCenter | Qt.AlignRight)
                col += 1
            g.addWidget(widget, i, col, Qt.AlignVCenter | Qt.AlignLeft)
            col += 1
        columnas = max(columnas, col)
    # el sobrante: al final (pegado a la izquierda) o entre las dos parejas
    g.setColumnStretch(2 if espacio_medio else columnas, 1)
    return caja


# ------------------------------------------------------- piezas visuales
class Tarjeta(QFrame):
    """Tarjeta blanca con esquinas redondeadas: la pieza base de las pantallas.

    Uso:  t = Tarjeta("Briefs", "5 trabajos de diseño")
          t.agregar(tabla)            # al cuerpo
          t.agregar_accion(boton)     # a la derecha del título
    """

    def __init__(self, titulo="", subtitulo="", padre=None, destacada=False,
                 esp=6, margen=9):
        super().__init__(padre)
        self.setObjectName("tarjetaBorde" if destacada else "tarjeta")
        self.raiz = margenes(QVBoxLayout(self), margen, margen, margen, margen, esp)
        self.encabezado = QHBoxLayout()
        margenes(self.encabezado, esp=8)
        self.textos = QVBoxLayout()
        margenes(self.textos, esp=2)
        self.lbl_titulo = None
        self.lbl_subtitulo = None
        if titulo:
            self.lbl_titulo = etiqueta(titulo, titulo="tarjeta")
            self.textos.addWidget(self.lbl_titulo)
        if subtitulo:
            self.lbl_subtitulo = etiqueta(subtitulo, titulo="subtituloTarjeta")
            self.textos.addWidget(self.lbl_subtitulo)
        self.acciones = QHBoxLayout()
        margenes(self.acciones, esp=6)
        self.encabezado.addLayout(self.textos, 1)
        self.encabezado.addStretch(0)
        self.encabezado.addLayout(self.acciones)
        self.raiz.addLayout(self.encabezado)
        self.cuerpo = QVBoxLayout()
        margenes(self.cuerpo, esp=8)
        self.raiz.addLayout(self.cuerpo)

    # ---------- contenido ----------
    def agregar(self, widget, estirar=0):
        self.cuerpo.addWidget(widget, estirar)
        return widget

    def agregar_fila(self, layout):
        self.cuerpo.addLayout(layout)
        return layout

    def agregar_estirar(self):
        self.cuerpo.addStretch(1)

    def agregar_accion(self, widget):
        self.acciones.addWidget(widget)
        return widget

    def agregar_separador(self):
        self.cuerpo.addWidget(linea())
        return self

    def poner(self, titulo=None, subtitulo=None):
        """Cambia el título y/o el subtítulo de la tarjeta ya creada."""
        if titulo is not None:
            if self.lbl_titulo is None:
                self.lbl_titulo = etiqueta(titulo, titulo="tarjeta")
                self.textos.insertWidget(0, self.lbl_titulo)
            else:
                self.lbl_titulo.setText(titulo)
        if subtitulo is not None:
            if self.lbl_subtitulo is None:
                self.lbl_subtitulo = etiqueta(subtitulo, titulo="subtituloTarjeta")
                self.textos.addWidget(self.lbl_subtitulo)
            else:
                self.lbl_subtitulo.setText(subtitulo)
        return self


class Insignia(QLabel):
    """Etiqueta redondeada de estado (PENDIENTE, JUSTIFICADO, ANULADO…)."""

    def __init__(self, texto="", fondo=None, color=None, padre=None):
        super().__init__(str(texto), padre)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.set_color(fondo or T.NEUTRO_FONDO, color)

    def set_color(self, fondo, color=None):
        self.setStyleSheet(T.estilo_insignia(fondo, color))
        return self

    def set_estado(self, estado, texto=None):
        color_texto, color_fondo = T.color_estado(estado)
        self.set_color(color_fondo, color_texto)
        self.setText(str(estado if texto is None else texto))
        return self

    def set_texto(self, texto):
        self.setText(str(texto))
        return self


class Kpi(QFrame):
    """Recuadro de indicador: rótulo pequeño, número grande y una nota al pie."""

    def __init__(self, rotulo="", valor="", nota="", color=None, padre=None,
                 estirar=False):
        super().__init__(padre)
        self.setObjectName("tarjeta")
        lay = margenes(QVBoxLayout(self), 14, 12, 14, 12, 3)
        self.lbl_rotulo = etiqueta(rotulo)
        self.lbl_rotulo.setObjectName("etiquetaKpi")
        self.lbl_valor = etiqueta(str(valor))
        self.lbl_valor.setObjectName("valorKpi")
        self.lbl_nota = etiqueta(nota)
        self.lbl_nota.setObjectName("notaKpi")
        lay.addWidget(self.lbl_rotulo)
        lay.addWidget(self.lbl_valor)
        lay.addWidget(self.lbl_nota)
        if color:
            self.set_valor(valor, color)
        # `estirar=True` deja que el recuadro se reparta el ancho disponible (así la
        # fila de indicadores llena la pantalla y no queda un hueco a la derecha).
        self.setSizePolicy(QSizePolicy.Expanding if estirar else QSizePolicy.Preferred,
                           QSizePolicy.Fixed)

    def set_valor(self, valor, color=None):
        self.lbl_valor.setText(str(valor))
        if color:
            self.lbl_valor.setStyleSheet("color: %s;" % color)
        return self

    def set_rotulo(self, texto):
        self.lbl_rotulo.setText(str(texto))
        return self

    def set_nota(self, texto):
        self.lbl_nota.setText(str(texto))
        return self


class Aviso(QFrame):
    """Franja informativa (la «ayuda en contexto» que va arriba de las pantallas)."""

    def __init__(self, titulo="", texto="", icono="ⓘ", padre=None):
        super().__init__(padre)
        self.setObjectName("aviso")
        lay = margenes(QHBoxLayout(self), 14, 12, 14, 12, 12)
        self.lbl_icono = QLabel(icono)
        self.lbl_icono.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.textos = margenes(QVBoxLayout(), esp=3)
        self.lbl_titulo = QLabel(str(titulo))
        self.lbl_titulo.setObjectName("tituloTarjeta")
        self.lbl_titulo.setWordWrap(True)
        self.lbl_texto = QLabel(str(texto))
        self.lbl_texto.setWordWrap(True)
        self.textos.addWidget(self.lbl_titulo)
        self.textos.addWidget(self.lbl_texto)
        lay.addWidget(self.lbl_icono)
        lay.addLayout(self.textos, 1)
        self.acciones = QHBoxLayout()
        margenes(self.acciones, esp=6)
        lay.addLayout(self.acciones)

    def poner(self, titulo=None, texto=None):
        if titulo is not None:
            self.lbl_titulo.setText(str(titulo))
        if texto is not None:
            self.lbl_texto.setText(str(texto))
        return self

    def agregar_accion(self, widget):
        self.acciones.addWidget(widget)
        return widget


# ------------------------------------------------------------- pantallas
class Pagina(QWidget):
    """Pantalla completa: encabezado (título, subtítulo y acciones) + cuerpo.

    El cuerpo se puede desplazar (monitores chicos o escalado de Windows) y todo se
    acomoda con layouts: nada de posiciones fijas.
    """

    def __init__(self, titulo="", subtitulo="", padre=None, desplazar=True, esp=8,
                 margen=(12, 10, 12, 10)):
        super().__init__(padre)
        self.setObjectName("pagina")
        raiz = margenes(QVBoxLayout(self), margen[0], margen[1], margen[2], margen[3], esp)
        self.cabecera = margenes(QHBoxLayout(), esp=10)
        self.textos = margenes(QVBoxLayout(), esp=2)
        self.lbl_titulo = etiqueta(titulo, titulo="pagina")
        self.lbl_subtitulo = etiqueta(subtitulo, titulo="subtitulo")
        self.textos.addWidget(self.lbl_titulo)
        self.textos.addWidget(self.lbl_subtitulo)
        self.acciones = margenes(QHBoxLayout(), esp=6)
        self.cabecera.addLayout(self.textos, 1)
        self.cabecera.addLayout(self.acciones)
        raiz.addLayout(self.cabecera)
        self.lienzo = None
        self.contenedor = None
        if desplazar:
            self.lienzo = QScrollArea()
            self.lienzo.setObjectName("lienzo")
            self.lienzo.setWidgetResizable(True)
            self.contenedor = QWidget()
            self.cuerpo = QVBoxLayout(self.contenedor)
            margenes(self.cuerpo, 0, 0, 6, 0, esp)
            self.lienzo.setWidget(self.contenedor)
            raiz.addWidget(self.lienzo, 1)
        else:
            self.cuerpo = QVBoxLayout()
            margenes(self.cuerpo, esp=esp)
            raiz.addLayout(self.cuerpo, 1)

    def agregar(self, widget, estirar=0):
        self.cuerpo.addWidget(widget, estirar)
        return widget

    def agregar_fila(self, layout, estirar=0):
        self.cuerpo.addLayout(layout, estirar)
        return layout

    def agregar_estirar(self):
        self.cuerpo.addStretch(1)

    def agregar_accion(self, widget):
        self.acciones.addWidget(widget)
        return widget

    def poner_titulo(self, titulo=None, subtitulo=None):
        if titulo is not None:
            self.lbl_titulo.setText(str(titulo))
        if subtitulo is not None:
            self.lbl_subtitulo.setText(str(subtitulo))
        return self


class Ventana(QDialog):
    """Ventana de un módulo, con el mismo encabezado y el botón de regreso al menú."""

    def __init__(self, titulo="", usuario=None, padre=None, ancho=1240, alto=780,
                 subtitulo="", info="", empezar_maximizada=None):
        super().__init__(padre)
        self.usuario = usuario or {}
        self.setWindowTitle(titulo or "Sistema de Viáticos")
        self.setModal(True)
        self.setMinimumSize(T.px(700, 520), T.px(440, 340))
        self.resize(T.px(ancho), T.px(alto))
        raiz = margenes(QVBoxLayout(self), 0, 0, 0, 0, 0)
        self.pagina = Pagina(titulo, subtitulo)
        self.boton_volver = boton_borde("← Volver al menú", self.volver)
        # En un QDialog, Qt nombra «botón por defecto» al primer botón que se crea —y este
        # es el primero—, así que al pulsar ENTER dentro de cualquier campo se activaba el
        # «Volver al menú»: la ventana se cerraba sola y se perdía todo lo escrito. Se le
        # quita esa marca (y la ventana además ignora la tecla, ver `keyPressEvent`).
        self.boton_volver.setAutoDefault(False)
        self.boton_volver.setDefault(False)
        self.pagina.agregar_accion(self.boton_volver)
        self.lbl_info = etiqueta(info, ayuda=True)
        if info:
            self.pagina.agregar_accion(self.lbl_info)
        raiz.addWidget(self.pagina)
        if empezar_maximizada is None:
            # Si la ventana no cabe en la pantalla se abre grande: así se ve todo sin
            # andar bajando con la barra de desplazamiento (como antes, al maximizar).
            empezar_maximizada = not self._cabe(T.px(ancho), T.px(alto))
        if empezar_maximizada:
            self.mostrar_maximizada()
        else:
            self.centrar()

    def _cabe(self, ancho, alto):
        """¿Entra una ventana de ese tamaño en la pantalla de esta computadora?"""
        pantalla = self.screen().availableGeometry() if self.screen() else None
        if pantalla is None:
            return True
        return ancho <= pantalla.width() and alto <= pantalla.height()

    # ---------- ayuda ----------
    @property
    def cuerpo(self):
        return self.pagina.cuerpo

    def keyPressEvent(self, evento):
        """La tecla ENTER **no** activa ningún botón de la ventana.

        Sin esto, ENTER activaba el «botón por defecto» del diálogo (el «← Volver al
        menú») y la ventana del módulo se cerraba en medio del trabajo, perdiendo lo que
        se había escrito. Con ENTER solo se termina de escribir el campo que tiene el
        cursor (los campos ya avisan con `editingFinished`/`textChanged`).
        Escape sigue cerrando la ventana, como en el resto del sistema.
        """
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter):
            evento.accept()
            return
        super().keyPressEvent(evento)

    def agregar(self, widget, estirar=0):
        return self.pagina.agregar(widget, estirar)

    def agregar_fila(self, layout, estirar=0):
        return self.pagina.agregar_fila(layout, estirar)

    def poner_titulo(self, titulo=None, subtitulo=None, info=None):
        self.pagina.poner_titulo(titulo, subtitulo)
        if info is not None:
            self.lbl_info.setText(str(info))
        return self

    def mostrar_maximizada(self):
        """Abre la ventana grande, sin salirse de la pantalla (como `state("zoomed")`)."""
        pantalla = self.screen().availableGeometry() if self.screen() else None
        if pantalla:
            self.resize(min(self.width(), pantalla.width()),
                        min(self.height(), pantalla.height()))
        self.showMaximized()
        return self

    def centrar(self):
        pantalla = self.screen().availableGeometry() if self.screen() else None
        if pantalla:
            geo = self.frameGeometry()
            geo.moveCenter(pantalla.center())
            self.move(geo.topLeft())
        return self

    def volver(self):
        """Cierra esta ventana y vuelve al menú principal."""
        self.done(QDialog.Accepted)

    def cerrar(self):
        self.done(QDialog.Accepted)

    def closeEvent(self, evento):
        evento.accept()


# ---------------------------------------------------------------- tablas
def normalizar_columnas(columnas):
    """Convierte [(clave, título, ancho[, alineación])] o [{...}] en diccionarios.

    Así las tablas y las exportaciones hablan siempre el mismo idioma, sin
    importar cómo se hayan declarado las columnas.
    """
    salida = []
    for c in columnas or []:
        if isinstance(c, dict):
            salida.append({"clave": c.get("clave", ""), "titulo": c.get("titulo", ""),
                           "ancho": T.px(c.get("ancho", 120)),
                           "alineacion": c.get("alineacion", Qt.AlignLeft)})
        else:
            salida.append({"clave": c[0], "titulo": c[1], "ancho": T.px(c[2]),
                           "alineacion": c[3] if len(c) > 3 else Qt.AlignLeft})
    return salida


def datos_columna(columna):
    """(título, clave, ancho) de una columna, venga como diccionario o como tupla."""
    if isinstance(columna, dict):
        return columna.get("titulo", ""), columna.get("clave", ""), columna.get("ancho", 120)
    return columna[1], columna[0], columna[2]


class Item(QTableWidgetItem):
    """Celda de tabla: guarda el dato completo y ordena bien números y fechas."""

    def __init__(self, texto="", valor=None, alineacion=Qt.AlignLeft):
        super().__init__("" if texto is None else str(texto))
        self.dato = valor
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.setTextAlignment(alineacion | Qt.AlignVCenter)

    def clave_orden(self):
        """Clave para el orden: los números van primero, por valor."""
        v = self.dato
        if isinstance(v, bool):
            return (0, float(v), "")
        if isinstance(v, (int, float)):
            return (0, float(v), "")
        return (1, 0.0, str(self.text()).upper())

    def __lt__(self, otro):
        try:
            return self.clave_orden() < otro.clave_orden()
        except AttributeError:
            return super().__lt__(otro)


class Tabla(QTableWidget):
    """Tabla de datos con el aspecto del sistema: filas alternadas y encabezados.

    `columnas` = [(clave, título, ancho), ...] o [(clave, título, ancho, alineación)]
    """

    def __init__(self, columnas=None, padre=None, alto_filas=24, ordenar=True,
                 seleccion_multiple=False, estirar_ultima=True):
        super().__init__(padre)
        self.columnas = []
        self.datos = []
        self._estirar_ultima = bool(estirar_ultima)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection if seleccion_multiple
                              else QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(T.px(alto_filas, 20))
        self._alto_fila = alto_filas
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(False)
        self.setSortingEnabled(bool(ordenar))
        if columnas:
            self.set_columnas(columnas)

    def sizeHint(self):
        """Tamaño que pide la tabla: el encabezado más unos pocos renglones.

        Así una tabla vacía (o con dos filas) no empuja la pantalla hacia abajo: el
        espacio de sobra, si lo hay, se lo reparte el layout.
        """
        filas = min(max(self.rowCount(), 3), 9)
        alto = T.px(30 + filas * self._alto_fila, 44)
        return QSize(super().sizeHint().width(), max(self.minimumHeight(), alto))

    # ---------- columnas ----------
    def set_columnas(self, columnas):
        """Define las columnas: [(clave, título, ancho[, alineación]), ...]"""
        self.columnas = normalizar_columnas(columnas)
        self.setColumnCount(len(self.columnas))
        self.setHorizontalHeaderLabels([c["titulo"] for c in self.columnas])
        for i, c in enumerate(self.columnas):
            self.setColumnWidth(i, c["ancho"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # `estirar_ultima=True` (lo de siempre): la última columna se lleva el espacio
        # que sobra. En las tablas anchas (el detalle de 25 columnas del viático) va en
        # False: si no, la última columna —CAJERO— se veía enorme y las de valores
        # salían recortadas con puntos suspensivos.
        self.horizontalHeader().setStretchLastSection(self._estirar_ultima)
        return self

    def clave_columna(self, indice):
        """Clave de la columna que está en esa posición ('' si no existe)."""
        if 0 <= indice < len(self.columnas):
            return self.columnas[indice]["clave"]
        return ""

    def indice_columna(self, clave):
        for i, c in enumerate(self.columnas):
            if c["clave"] == clave:
                return i
        return -1

    def ocultar(self, clave, ocultar=True):
        i = self.indice_columna(clave)
        if i >= 0:
            self.setColumnHidden(i, bool(ocultar))
        return self

    # ---------- datos ----------
    @staticmethod
    def texto_celda(valor):
        """Cómo se escribe un valor en la tabla (los números con 2 decimales)."""
        if valor is None:
            return ""
        if isinstance(valor, bool):
            return "Sí" if valor else "No"
        if isinstance(valor, float):
            return "%.2f" % valor
        return str(valor)


    def poner(self, filas):
        """Llena la tabla con una lista de diccionarios."""
        self.datos = list(filas or [])
        ordenando = self.isSortingEnabled()
        self.setSortingEnabled(False)
        self.setRowCount(len(self.datos))
        for f, registro in enumerate(self.datos):
            for c, col in enumerate(self.columnas):
                valor = (registro or {}).get(col["clave"])
                it = Item(self.texto_celda(valor), valor, col["alineacion"])
                it.setData(Qt.UserRole, f)          # posición en self.datos
                self.setItem(f, c, it)
        self.setSortingEnabled(ordenando)
        return self

    def limpiar(self):
        self.setRowCount(0)
        self.datos = []
        return self

    def fila(self, indice):
        """Diccionario completo de la fila que está en esa posición visual."""
        it = self.item(indice, 0)
        if it is None:
            return None
        f = it.data(Qt.UserRole)
        if f is None or not isinstance(f, int) or not 0 <= f < len(self.datos):
            return None
        return self.datos[f]

    def seleccion(self):
        """Diccionario de la fila elegida (o None si no hay ninguna)."""
        filas = self.selecciones()
        return filas[0] if filas else None

    def selecciones(self):
        """Diccionarios de todas las filas elegidas (sin repetir)."""
        vistas, salida = set(), []
        for it in self.selectedItems():
            f = it.data(Qt.UserRole)
            if f is None or f in vistas:
                continue
            vistas.add(f)
            if isinstance(f, int) and 0 <= f < len(self.datos):
                salida.append(self.datos[f])
        return salida

    def seleccionar_donde(self, clave, valor):
        """Marca la fila cuyo campo `clave` vale `valor` (la deja a la vista)."""
        for f, registro in enumerate(self.datos):
            if str((registro or {}).get(clave)) == str(valor):
                return self.seleccionar_posicion(f)
        return -1

    def seleccionar_posicion(self, posicion):
        """Marca la fila que ocupa esa posición de la lista original."""
        for i in range(self.rowCount()):
            it = self.item(i, 0)
            if it is not None and it.data(Qt.UserRole) == posicion:
                self.selectRow(i)
                self.scrollToItem(it)
                return i
        return -1

    def agregar_manejadores(self, al_seleccionar=None, al_doble_clic=None):
        """Conecta los eventos de la tabla con funciones que reciben la fila elegida."""
        if al_seleccionar:
            self.itemSelectionChanged.connect(lambda: al_seleccionar(self.seleccion()))
        if al_doble_clic:
            self.itemDoubleClicked.connect(lambda *a: al_doble_clic(self.seleccion()))
        return self


# ------------------------------------------------------- filtros y archivos
class FilaFiltros(QWidget):
    """Fila de cajitas de filtro alineadas con las columnas de una tabla.

    Va colocada por el layout justo debajo del encabezado; las cajitas se acomodan
    sobre cada columna siguiendo el ancho real del encabezado (así el filtro de
    «LUGAR» siempre queda bajo la columna LUGAR, aunque se cambie el ancho).
    """

    cambio = Signal(int, str)

    def __init__(self, tabla, padre=None):
        super().__init__(padre)
        self.tabla = tabla
        self.cajas = []
        self.setFixedHeight(T.px(24, 18))
        for i in range(tabla.columnCount()):
            c = QLineEdit(self)
            c.setObjectName("filtro")
            c.setPlaceholderText(">")
            c.setToolTip("Escriba aquí para filtrar esta columna")
            c.textChanged.connect(lambda t, col=i: self.cambio.emit(col, t))
            self.cajas.append(c)
        cab = tabla.horizontalHeader()
        cab.sectionResized.connect(lambda *a: self.acomodar())
        cab.sectionMoved.connect(lambda *a: self.acomodar())
        cab.geometriesChanged.connect(self.acomodar)
        tabla.horizontalScrollBar().valueChanged.connect(lambda *a: self.acomodar())
        self.acomodar()

    def acomodar(self):
        """Pone cada cajita encima de su columna."""
        cab = self.tabla.horizontalHeader()
        alto = max(self.height() - 2, T.px(16, 12))
        for i, caja in enumerate(self.cajas):
            if i >= self.tabla.columnCount() or self.tabla.isColumnHidden(i):
                caja.setVisible(False)
                continue
            caja.setVisible(True)
            x = cab.sectionViewportPosition(i) - cab.offset()
            ancho = cab.sectionSize(i)
            caja.setGeometry(x + 1, 0, max(T.px(26, 18), ancho - 2), alto)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.acomodar()

    def limpiar(self):
        for c in self.cajas:
            c.blockSignals(True)
            c.clear()
            c.blockSignals(False)

    def textos(self):
        return [c.text() for c in self.cajas]


def nombre_archivo(texto, por_defecto="documento"):
    """Nombre de archivo válido en Windows.

    Windows no deja usar  \\  /  :  *  ?  "  <  >  |  en un nombre de archivo: el
    «N° 001/2026» de un viático traía la barra y el archivo no se podía crear.
    """
    limpio = "".join(("-" if c in '\\/:*?"<>|' else c) for c in str(texto or ""))
    limpio = " ".join(limpio.split()).strip(" .")
    return limpio or por_defecto


def pedir_ruta_guardar(padre, nombre, filtro="Excel (*.xlsx)"):
    """Pregunta dónde guardar un archivo. Devuelve la ruta o None si se cancela."""
    nombre = nombre.replace("\\", "/").rsplit("/", 1)[-1]      # solo el nombre, sin carpetas
    nombre = nombre_archivo(nombre, "documento.xlsx")
    ruta, _ = QFileDialog.getSaveFileName(padre, "Guardar como", nombre, filtro)
    return ruta or None


def _valor_para_archivo(valor):
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "SI" if valor else "NO"
    return valor


def _titulo_hoja(nombre):
    """Nombre de hoja válido para Excel.

    Excel no deja usar  \\  /  :  *  ?  [  ]  en el nombre de la hoja (el
    «N° 001/2026» de un viático traía la barra y openpyxl rechazaba el archivo) y
    el nombre no puede pasar de 31 letras.
    """
    limpio = "".join(c for c in str(nombre or "Documento") if c not in "\\/:*?[]")
    limpio = " ".join(limpio.split())
    return (limpio or "Documento")[:31]


def exportar_excel(ruta, columnas, filas, hoja="Datos"):
    """Guarda una tabla en Excel (.xlsx). `columnas` = [(clave, título, ancho), ...]."""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except Exception:
        raise RuntimeError("Falta la librería 'openpyxl'.\nInstale con:  pip install openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = _titulo_hoja(hoja)
    ws.append([datos_columna(c)[0] for c in columnas])
    for f in filas:
        ws.append([_valor_para_archivo((f or {}).get(datos_columna(c)[1])) for c in columnas])
    for i, c in enumerate(columnas, start=1):
        ancho = datos_columna(c)[2] or 12
        ws.column_dimensions[get_column_letter(i)].width = max(12, min(50, ancho / 7.0))
    wb.save(ruta)
    return ruta


def exportar_csv(ruta, columnas, filas):
    """Guarda una tabla en CSV (UTF-8 con BOM: se abre bien en Excel)."""
    import csv
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
        escritor = csv.writer(fh, delimiter=";")
        escritor.writerow([datos_columna(c)[0] for c in columnas])
        for f in filas:
            escritor.writerow([_valor_para_archivo((f or {}).get(datos_columna(c)[1]))
                               for c in columnas])
    return ruta


def exportar_excel_documento(ruta, bloques, hoja="Documento"):
    """Exporta un «documento» a Excel: encabezado con datos + tablas, con formato.

    `bloques` es una lista de:
      ("titulo", "TEXTO")                      → una línea de título
      ("datos", [(etiqueta, valor), ...])      → pares etiqueta/valor (dos columnas)
      ("tabla", columnas, filas)               → tabla con encabezado azul
      ("totales", columnas, fila)              → última fila resaltada en amarillo
      ("salto",)                               → fila en blanco

    Sirve para que lo que se exporta se vea igual que lo que se imprime.
    """
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except Exception:
        raise RuntimeError("Falta la librería 'openpyxl'.\nInstale con:  pip install openpyxl")
    azul = PatternFill("solid", fgColor=T.AZUL.lstrip("#"))
    amarillo = PatternFill("solid", fgColor=T.AMARILLO_SUAVE.lstrip("#"))
    gris = PatternFill("solid", fgColor="F1F1F7")
    borde = Border(*[Side(style="thin", color="C9CBD6")] * 4)
    blanco = Font(color="FFFFFF", bold=True)
    negrita = Font(bold=True)
    izq = Alignment(horizontal="left", vertical="center", wrap_text=True)
    centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = _titulo_hoja(hoja)

    # Manda la tabla más ancha: el título y los datos se estiran hasta esa última
    # columna, así la hoja queda llena y no un bloque de dos columnas perdido a la
    # izquierda (antes el encabezado se veía al 8 % del ancho del detalle).
    ancho = 2
    for bloque in bloques:
        if bloque[0] in ("tabla", "totales"):
            ancho = max(ancho, len(bloque[1]))

    def escribir(fila, desde, hasta, texto, fuente=None, relleno=None, alineacion=izq):
        """Escribe un valor en un rango (lo une si son varias columnas) con borde."""
        for col in range(desde, hasta + 1):
            celda = ws.cell(fila, col)
            celda.border = borde
            if relleno is not None:
                celda.fill = relleno
        celda = ws.cell(fila, desde, texto)
        if fuente is not None:
            celda.font = fuente
        celda.alignment = alineacion
        if hasta > desde:
            ws.merge_cells(start_row=fila, start_column=desde, end_row=fila, end_column=hasta)
        return celda

    fila = 1
    for bloque in bloques:
        tipo = bloque[0]
        if tipo == "titulo":
            escribir(fila, 1, ancho, bloque[1], blanco, azul, centro)
            ws.row_dimensions[fila].height = 24
            fila += 2
        elif tipo == "datos":
            # Los datos van en una cuadrícula de 3 parejas por fila, como el informe
            # impreso: cada rótulo con su valor al lado, y el bloque se estira hasta la
            # última columna de la tabla más ancha (así la hoja queda llena y ordenada).
            por_fila = 3
            parte = max(2, ancho // por_fila)
            parejas = list(bloque[1])
            for i, (etiqueta_texto, valor) in enumerate(parejas):
                columna = (i % por_fila) * parte + 1
                fila_datos = fila + i // por_fila
                texto = "" if valor is None else str(valor)
                escribir(fila_datos, columna, columna, str(etiqueta_texto), negrita, gris, izq)
                escribir(fila_datos, columna + 1, columna + parte - 1, texto, None, None, izq)
                # Un valor largo (lista de personas, observaciones) pide más alto.
                alto = 16
                if len(texto) > 60:
                    alto = 28
                if len(texto) > 120:
                    alto = 44
                if len(texto) > 200:
                    alto = 60
                ws.row_dimensions[fila_datos].height = max(
                    ws.row_dimensions[fila_datos].height or 0, alto)
            fila += (len(parejas) + por_fila - 1) // por_fila
        elif tipo in ("tabla", "totales"):
            columnas, datos = bloque[1], bloque[2]
            if tipo == "tabla":
                for i, col in enumerate(columnas, start=1):
                    celda = ws.cell(fila, i, datos_columna(col)[0])
                    celda.font = blanco
                    celda.fill = azul
                    celda.border = borde
                    celda.alignment = centro
                ws.freeze_panes = ws.cell(fila + 1, 1)   # encabezado siempre a la vista
                fila += 1
            for registro in datos:
                for i, col in enumerate(columnas, start=1):
                    texto = _valor_para_archivo((registro or {}).get(datos_columna(col)[1]))
                    celda = ws.cell(fila, i, texto)
                    celda.border = borde
                    if tipo == "totales":
                        celda.fill = amarillo
                        celda.font = negrita
                fila += 1
            if tipo == "tabla":
                for i, col in enumerate(columnas, start=1):
                    ancho_col = datos_columna(col)[2] or 12
                    ws.column_dimensions[get_column_letter(i)].width = max(
                        10, min(42, ancho_col / 7.0))
        elif tipo == "salto":
            fila += 1
    # Cada columna de rótulos tiene que dejar leer su texto más largo: el valor va en
    # las columnas siguientes, así que el rótulo no se puede desbordar hacia al lado.
    con_datos = [b[1] for b in bloques if b[0] == "datos"]
    if con_datos:
        por_fila = 3
        parte = max(2, ancho // por_fila)
        for ranura in range(por_fila):
            letras = [len(str(pareja[0])) for parejas in con_datos
                      for i, pareja in enumerate(parejas) if i % por_fila == ranura]
            if not letras:
                continue
            letra = get_column_letter(ranura * parte + 1)
            ws.column_dimensions[letra].width = max(
                ws.column_dimensions[letra].width or 10, min(40, max(letras) + 2))
    wb.save(ruta)
    return ruta


def abrir_archivo(ruta):
    """Abre un archivo con el programa que le corresponde en Windows."""
    import os
    import subprocess
    import sys
    if not ruta or not os.path.exists(ruta):
        return False
    try:
        if sys.platform == "win32":
            os.startfile(ruta)                      # noqa: S606 (Windows)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
        return True
    except Exception:
        return False


class TablaDatos(QFrame):
    """Tarjeta con tabla: buscador, Excel/CSV, contador «n de n» y filtros por columna.

    Reproduce el comportamiento de las tablas del sistema: búsqueda en todas las
    columnas, orden por clic en el encabezado, exportación y contador visible.
    """

    cambio_seleccion = Signal(object)
    doble_clic = Signal(object)

    def __init__(self, columnas, titulo="", subtitulo="", padre=None, alto=280,
                 buscador=True, filtros=False, exportar=True, pie="", nombre="datos",
                 seleccion_multiple=False, alto_filas=24):
        super().__init__(padre)
        self.setObjectName("tarjeta")
        self.columnas = normalizar_columnas(columnas)
        self.nombre = nombre or "datos"
        self.datos = []
        self.filtro_extra = None          # (opcional) filtro propio de la pantalla
        self._filtros = [""] * len(self.columnas)
        raiz = margenes(QVBoxLayout(self), 14, 12, 14, 12, 8)

        # --- encabezado: título, subtítulo y botones propios de la pantalla ---
        cab = margenes(QHBoxLayout(), esp=8)
        self.textos = margenes(QVBoxLayout(), esp=2)
        self.lbl_titulo = etiqueta(titulo, titulo="tarjeta")
        self.lbl_subtitulo = etiqueta(subtitulo, titulo="subtituloTarjeta")
        self.textos.addWidget(self.lbl_titulo)
        self.textos.addWidget(self.lbl_subtitulo)
        cab.addLayout(self.textos, 1)
        self.acciones_herramienta = margenes(QHBoxLayout(), esp=6)
        cab.addLayout(self.acciones_herramienta)
        raiz.addLayout(cab)

        # --- barra: buscador, exportación y contador ---
        self.barra = margenes(QHBoxLayout(), esp=6)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setObjectName("buscar")
        self.txt_buscar.setPlaceholderText("Buscar en todo…")
        self.txt_buscar.setFixedWidth(T.px(240))
        self.txt_buscar.textChanged.connect(lambda _t: self.aplicar())
        if buscador:
            self.barra.addWidget(self.txt_buscar)
        self.barra.addStretch(1)
        self.btn_excel = boton_herramienta("📊  Excel", self.exportar_excel_segun)
        self.btn_csv = boton_herramienta("📄  CSV", self.exportar_csv_segun)
        if exportar:
            self.barra.addWidget(self.btn_excel)
            self.barra.addWidget(self.btn_csv)
        self.lbl_contador = etiqueta("0 de 0", rubrica="contador")
        self.barra.addWidget(self.lbl_contador)
        raiz.addLayout(self.barra)

        # --- tabla (y, si se pide, la barra de filtros por columna encima) ---
        self.tabla = Tabla(self.columnas, self, alto_filas=alto_filas,
                           seleccion_multiple=seleccion_multiple)
        self.tabla.setMinimumHeight(T.px(alto, 120))
        self.fila_filtros = None
        if filtros:
            self.fila_filtros = FilaFiltros(self.tabla, self)
            self.fila_filtros.cambio.connect(self._cambio_filtro)
            raiz.addWidget(self.fila_filtros)
        raiz.addWidget(self.tabla, 1)
        self.lbl_pie = etiqueta(pie, ayuda=True)
        raiz.addWidget(self.lbl_pie)

        self.tabla.itemSelectionChanged.connect(
            lambda: self.cambio_seleccion.emit(self.seleccion()))
        self.tabla.itemDoubleClicked.connect(
            lambda *a: self.doble_clic.emit(self.seleccion()))

    # ---------- contenido ----------
    def set_datos(self, filas):
        """Carga las filas (diccionarios) y vuelve a aplicar los filtros."""
        self.datos = list(filas or [])
        self.aplicar()
        return self

    def visibles(self):
        """Filas que se están mostrando ahora mismo."""
        return list(self._visibles)

    def _texto_fila(self, fila):
        return " ".join(self._texto(fila.get(c["clave"])) for c in self.columnas).upper()

    @staticmethod
    def _texto(valor):
        if valor is None:
            return ""
        if isinstance(valor, float):
            return "%.2f" % valor
        return str(valor)

    def aplicar(self):
        """Filtra (buscador + filtros por columna) y pinta el resultado."""
        buscado = (self.txt_buscar.text() or "").strip().upper()
        filas = []
        for f in self.datos:
            if buscado and not self._coincide_busqueda(f, buscado):
                continue
            if not self._coincide_filtros(f):
                continue
            filas.append(f)
        self._visibles = filas
        self.tabla.poner(filas)
        self.lbl_contador.setText("%d de %d" % (len(filas), len(self.datos)))
        return self

    def _coincide_busqueda(self, fila, texto):
        """Búsqueda del buscador: la de la pantalla, si definió una propia."""
        if self.filtro_extra is not None:
            try:
                return bool(self.filtro_extra(fila, texto))
            except Exception:
                pass
        return texto in self._texto_fila(fila)

    def _coincide_filtros(self, fila):
        for i, texto in enumerate(self._filtros):
            texto = (texto or "").strip().upper()
            if not texto:
                continue
            valor = self._texto(fila.get(self.columnas[i][0])).upper()
            if texto not in valor:
                return False
        return True

    def _cambio_filtro(self, columna, texto):
        if 0 <= columna < len(self._filtros):
            self._filtros[columna] = texto
        self.aplicar()

    def limpiar_filtros(self):
        """Borra el buscador y los filtros por columna."""
        self.txt_buscar.blockSignals(True)
        self.txt_buscar.clear()
        self.txt_buscar.blockSignals(False)
        self._filtros = [""] * len(self.columnas)
        if self.fila_filtros is not None:
            self.fila_filtros.limpiar()
        self.aplicar()
        return self

    def limpiar(self):
        """Deja la tabla vacía."""
        self.datos = []
        self._visibles = []
        self.tabla.limpiar()
        self.lbl_contador.setText("0 de 0")
        return self

    def buscar(self, texto):
        """Escribe en el buscador (como si se hubiera tecleado)."""
        self.txt_buscar.setText(texto or "")
        return self


    # ---------- selección ----------
    def seleccion(self):
        """Diccionario de la fila elegida (o None)."""
        return self.tabla.seleccion()

    def selecciones(self):
        """Diccionarios de todas las filas elegidas."""
        return self.tabla.selecciones()

    def seleccionar_donde(self, clave, valor):
        return self.tabla.seleccionar_donde(clave, valor)

    def marcar_primera(self):
        """Deja marcada la primera fila (útil después de cargar)."""
        if self.tabla.rowCount():
            self.tabla.selectRow(0)
        return self

    def al_seleccionar(self, funcion):
        self.cambio_seleccion.connect(funcion)
        return self

    def al_doble_clic(self, funcion):
        self.doble_clic.connect(funcion)
        return self

    # ---------- cabecera y pie ----------
    def poner_titulo(self, titulo=None, subtitulo=None):
        if titulo is not None:
            self.lbl_titulo.setText(str(titulo))
        if subtitulo is not None:
            self.lbl_subtitulo.setText(str(subtitulo))
        return self

    def set_pie(self, texto):
        self.lbl_pie.setText(str(texto))
        return self

    def agregar_accion(self, widget):
        """Agrega un botón propio de la pantalla (arriba a la derecha)."""
        self.acciones_herramienta.addWidget(widget)
        return widget

    def agregar_boton(self, texto, cb=None, estilo="barraHerramienta", icono=None):
        """Crea y agrega un botón de herramienta en la cabecera."""
        return self.agregar_accion(boton(texto, cb, estilo, icono=icono))

    # ---------- exportación ----------
    def datos_exportables(self):
        """Columnas y filas que se exportan: solo lo que se ve en pantalla."""
        return self.columnas, self.visibles()

    def exportar_excel_segun(self):
        columnas, filas = self.datos_exportables()
        if not filas:
            aviso(self, "Exportar", "No hay filas para exportar.")
            return None
        ruta = pedir_ruta_guardar(self, "%s.xlsx" % self.nombre)
        if not ruta:
            return None
        try:
            exportar_excel(ruta, columnas, filas, self.nombre)
        except Exception as ex:
            error(self, "Exportar a Excel", str(ex))
            return None
        informar(self, "Exportar a Excel", "Se guardó el archivo:\n%s\n\nFilas: %d"
                 % (ruta, len(filas)))
        return ruta

    def exportar_csv_segun(self):
        columnas, filas = self.datos_exportables()
        if not filas:
            aviso(self, "Exportar", "No hay filas para exportar.")
            return None
        ruta = pedir_ruta_guardar(self, "%s.csv" % self.nombre, "CSV (*.csv)")
        if not ruta:
            return None
        try:
            exportar_csv(ruta, columnas, filas)
        except Exception as ex:
            error(self, "Exportar a CSV", str(ex))
            return None
        informar(self, "Exportar a CSV", "Se guardó el archivo:\n%s\n\nFilas: %d"
                 % (ruta, len(filas)))
        return ruta

    def exportar_excel_en(self, ruta):
        """Exporta sin preguntar (para informes que ya tienen su ruta)."""
        columnas, filas = self.datos_exportables()
        exportar_excel(ruta, columnas, filas, self.nombre)
        return ruta

    def exportar_csv_en(self, ruta):
        columnas, filas = self.datos_exportables()
        exportar_csv(ruta, columnas, filas)
        return ruta


# ---------------------------------------------------------------- avisos
def _caja(padre, titulo, texto, icono, botones, defecto=None):
    caja = QMessageBox(padre)
    caja.setWindowTitle(str(titulo))
    caja.setIcon(icono)
    caja.setText(str(texto))
    caja.setStandardButtons(botones)
    caja.setDefaultButton(defecto if defecto is not None else QMessageBox.Ok)
    return caja


def informar(padre, titulo, texto):
    """Aviso informativo (reemplaza a `messagebox.showinfo`)."""
    caja = _caja(padre, titulo, texto, QMessageBox.Information, QMessageBox.Ok)
    caja.exec()
    return True


def aviso(padre, titulo, texto):
    """Advertencia (reemplaza a `messagebox.showwarning`)."""
    caja = _caja(padre, titulo, texto, QMessageBox.Warning, QMessageBox.Ok)
    caja.exec()
    return True


def error(padre, titulo, texto):
    """Error (reemplaza a `messagebox.showerror`)."""
    caja = _caja(padre, titulo, texto, QMessageBox.Critical, QMessageBox.Ok)
    caja.exec()
    return True


def confirmar(padre, titulo, texto, si="Sí, continuar", no="Cancelar"):
    """Pregunta de sí/no (reemplaza a `messagebox.askyesno`)."""
    caja = _caja(padre, titulo, texto, QMessageBox.Question,
                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    caja.button(QMessageBox.Yes).setText(si)
    caja.button(QMessageBox.No).setText(no)
    return caja.exec() == QMessageBox.Yes


def confirmar_peligro(padre, titulo, texto, si="Sí, continuar", no="Cancelar"):
    """Pregunta de sí/no con aviso rojo, para acciones que no se pueden deshacer."""
    caja = _caja(padre, titulo, texto, QMessageBox.Warning,
                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    caja.button(QMessageBox.Yes).setText(si)
    caja.button(QMessageBox.No).setText(no)
    return caja.exec() == QMessageBox.Yes


class _EntradaTexto(QDialog):
    """Ventanita para pedir un dato escrito (reemplaza a `simpledialog`)."""

    def __init__(self, padre, titulo, etiqueta_texto, valor="", clave=False,
                 ancho=300, multilinea=False, alto=90):
        super().__init__(padre)
        self.setWindowTitle(str(titulo))
        self.setModal(True)
        lay = margenes(QVBoxLayout(self), 16, 16, 16, 16, 10)
        lay.addWidget(QLabel(str(etiqueta_texto)))
        if multilinea:
            self.entrada = QPlainTextEdit("" if valor is None else str(valor))
            self.entrada.setFixedHeight(T.px(alto))
        else:
            self.entrada = QLineEdit("" if valor is None else str(valor))
            self.entrada.setFixedWidth(T.px(ancho))
            self.entrada.setEchoMode(QLineEdit.Password if clave else QLineEdit.Normal)
        lay.addWidget(self.entrada)
        barra = margenes(QHBoxLayout(), esp=8)
        barra.addStretch(1)
        barra.addWidget(boton_secundario("Cancelar", self.reject))
        barra.addWidget(boton_primario("Aceptar", self.accept))
        lay.addLayout(barra)
        (self.entrada.setFocus if multilinea else self.entrada.selectAll)()

    def texto(self):
        if isinstance(self.entrada, QPlainTextEdit):
            return self.entrada.toPlainText().strip()
        return self.entrada.text().strip()


def preguntar(padre, titulo, etiqueta_texto, valor="", clave=False, ancho=300):
    """Pide un texto. Devuelve el texto o None si se cancela."""
    dlg = _EntradaTexto(padre, titulo, etiqueta_texto, valor, clave, ancho)
    if dlg.exec() == QDialog.Accepted:
        return dlg.texto()
    return None


def preguntar_largo(padre, titulo, etiqueta_texto, valor="", alto=120):
    """Pide un texto largo (varias líneas). Devuelve el texto o None."""
    dlg = _EntradaTexto(padre, titulo, etiqueta_texto, valor, multilinea=True, alto=alto)
    if dlg.exec() == QDialog.Accepted:
        return dlg.texto()
    return None


def preguntar_valor(padre, titulo, etiqueta_texto, valor=0.0, ancho=200, decimales=2):
    """Pide un número (monto, km…). Devuelve el valor o None si se cancela."""
    dlg = QDialog(padre)
    dlg.setWindowTitle(str(titulo))
    dlg.setModal(True)
    lay = margenes(QVBoxLayout(dlg), 16, 16, 16, 16, 10)
    lay.addWidget(QLabel(str(etiqueta_texto)))
    caja = campo_decimal(valor, decimales=decimales, ancho=ancho)
    caja.selectAll()
    lay.addWidget(caja)
    barra = margenes(QHBoxLayout(), esp=8)
    barra.addStretch(1)
    barra.addWidget(boton_secundario("Cancelar", dlg.reject))
    barra.addWidget(boton_primario("Aceptar", dlg.accept))
    lay.addLayout(barra)
    caja.setFocus()
    if dlg.exec() == QDialog.Accepted:
        return float(caja.value())
    return None


def etiqueta_sesion(usuario, extra=""):
    """Texto de la barra de sesión: nombre, rol y base en uso."""
    usuario = usuario or {}
    nombre = usuario.get("nombre") or usuario.get("usuario") or "SISTEMA"
    rol = usuario.get("rol") or ""
    try:
        import database as db
        rol = db.ETIQUETA_ROL.get(rol, rol)
    except Exception:
        pass
    partes = [str(nombre)]
    if rol:
        partes.append(str(rol))
    if extra:
        partes.append(str(extra))
    return " · ".join(partes)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
