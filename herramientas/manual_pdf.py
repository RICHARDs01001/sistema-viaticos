# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""manual_pdf.py — Arma el **MANUAL_DE_USUARIO.pdf** (con cuadros) desde el .md.

    python herramientas/manual_pdf.py
    python herramientas/manual_pdf.py <manual.md> <salida.pdf>

No hay nada escrito a mano: lee `documentacion/MANUAL_DE_USUARIO.md` (el mismo que
se entrega en Markdown), sus figuras de `documentacion/manual/img` y arma un PDF:

  - **Portada** editorial: lomo azul, título en serif y filete en bronce.
  - **Índice** con el número de página de cada capítulo y de cada apartado.
  - Cada capítulo empieza en **página nueva**, con su «CAPÍTULO N» en bronce y un
    filete que cruza la caja.
  - Los **recuadros** del manual (las líneas que empiezan con `>`) salen como
    cuadros con fondo muy claro y barra de color al costado: son las notas y los avisos.
  - Las **tablas** van con cabecera azul, filas alternadas y filetes horizontales.
  - Cada **figura** va enmarcada, con su número y su nombre debajo.
  - Encabezado y pie en todas las páginas: **«Página X de Y»**.
  - Índice del PDF (marcadores) para saltar de capítulo en capítulo.

El texto va en **Cambria** (serif de pantalla, muy legible) y las etiquetas, los pies
y las cabeceras de tabla en **Segoe UI Semibold**: la mezcla serif + sans es la de un
documento formal. Los iconos del manual (💾, 🖨, ✅…) se dibujan con **Segoe UI
Symbol**, así que se ven en blanco y negro, nítidos y sin cuadraditos de «falta el
carácter».
"""
import io
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image,
                                KeepTogether, PageBreak, PageTemplate, Paragraph, Table,
                                TableStyle)

AQUI = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.abspath(os.path.join(AQUI, "..", "documentacion"))
MD = os.path.join(DOC, "MANUAL_DE_USUARIO.md")
PDF = os.path.join(DOC, "MANUAL_DE_USUARIO.pdf")
IMGS = os.path.join(DOC, "manual", "img")
LOGO = os.path.join(IMGS, "logo-resg-tech.png")     # el logo de la portada (RESG Tech)

VERSION = "9.1"
FECHA = "octubre 2026"
TITULO = "Manual de usuario"
SUBTITULO = "Sistema de Viáticos Miempresa"
AUTOR = "Richard Esteban Salazar Guillén"
CONTACTO = "richards0101789@gmail.com  ·  +593 981239086"

# Lo que la portada resume del manual (lo cuenta `main` al leer el .md).
RESUMEN = {"capitulos": 0, "figuras": 0, "apartados": 0}

# Paleta formal: azul marino, bronce de filete y grises de imprenta.
AZUL = colors.HexColor("#17365D")
AZUL_MEDIO = colors.HexColor("#2E5E8C")
AZUL_CLARO = colors.HexColor("#F2F6FA")
GRIS = colors.HexColor("#5B6773")
GRIS_CLARO = colors.HexColor("#F8F9FB")
LINEA = colors.HexColor("#D7DEE6")
TINTA = colors.HexColor("#1D2733")
BRONCE = colors.HexColor("#8C6A3F")
AMBAR = colors.HexColor("#A9762A")
VERDE = colors.HexColor("#1E7A5A")

MARGEN_IZQ, MARGEN_DER, MARGEN_SUP, MARGEN_INF = 23 * mm, 21 * mm, 26 * mm, 22 * mm
ANCHO = A4[0] - MARGEN_IZQ - MARGEN_DER

# (nombre en el PDF, archivo de Windows, índice dentro del .ttc)
_FUENTES = (("Libro", "cambria.ttc", 0), ("Libro-B", "cambriab.ttf", 0),
            ("Libro-I", "cambriai.ttf", 0), ("Libro-BI", "cambriaz.ttf", 0),
            ("Segoe", "segoeui.ttf", 0), ("Segoe-B", "segoeuib.ttf", 0),
            ("Segoe-I", "segoeuii.ttf", 0), ("Segoe-BI", "segoeuiz.ttf", 0),
            ("Segoe-SB", "segoeuisl.ttf", 0), ("Segoe-L", "segoeuil.ttf", 0),
            ("Mono", "consola.ttf", 0), ("Mono-B", "consolab.ttf", 0),
            ("Sim", "seguisym.ttf", 0))
_CMAP = frozenset()


def registrar_fuentes():
    """Registra Cambria (texto), Segoe UI (etiquetas), Consolas e iconos."""
    global _CMAP, _CMAP_SIM
    from fontTools.ttLib import TTFont as _TTFont
    carpeta = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for nombre, archivo, indice in _FUENTES:
        ruta = os.path.join(carpeta, archivo)
        if not os.path.exists(ruta):
            raise SystemExit("No encuentro la fuente %s (hace falta para el PDF)." % ruta)
        pdfmetrics.registerFont(TTFont(nombre, ruta, subfontIndex=indice))
    pdfmetrics.registerFontFamily("Libro", normal="Libro", bold="Libro-B",
                                  italic="Libro-I", boldItalic="Libro-BI")
    pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="Segoe-B",
                                  italic="Segoe-I", boldItalic="Segoe-BI")
    pdfmetrics.registerFontFamily("Segoe-SB", normal="Segoe-SB", bold="Segoe-B",
                                  italic="Segoe-I", boldItalic="Segoe-BI")
    pdfmetrics.registerFontFamily("Segoe-L", normal="Segoe-L", bold="Segoe-SB",
                                  italic="Segoe-I", boldItalic="Segoe-BI")

    def _cmap(archivo):
        fuente = _TTFont(os.path.join(carpeta, archivo), fontNumber=0, lazy=True)
        mapa = set()
        for tabla in fuente["cmap"].tables:
            mapa.update(tabla.cmap)
        return frozenset(mapa)

    _CMAP = _cmap("cambria.ttc")            # lo que puede dibujar el texto del manual
    _CMAP_SIM = _cmap("seguisym.ttf")       # lo que pueden dibujar los iconos



def _estilos():
    """Todos los estilos de párrafo del manual, en un solo lugar."""
    return {
        "Cuerpo": ParagraphStyle("Cuerpo", fontName="Libro", fontSize=10.4, leading=15.6,
                                 alignment=TA_JUSTIFY, spaceAfter=5.4, textColor=TINTA),
        "Entradilla": ParagraphStyle("Entradilla", fontName="Libro-I", fontSize=10.6,
                                     leading=15.4, alignment=TA_LEFT, spaceAfter=4,
                                     textColor=GRIS),
        "Item": ParagraphStyle("Item", fontName="Libro", fontSize=10.2, leading=15,
                               alignment=TA_JUSTIFY, spaceAfter=3.4, textColor=TINTA,
                               leftIndent=19, firstLineIndent=-19, bulletIndent=0,
                               bulletFontName="Segoe-SB", bulletFontSize=8.6,
                               bulletColor=BRONCE),
        "Nota": ParagraphStyle("Nota", fontName="Libro", fontSize=9.9, leading=14.4,
                               alignment=TA_LEFT, spaceAfter=3.2,
                               textColor=colors.HexColor("#1B2B3A")),
        "NotaTitulo": ParagraphStyle("NotaTitulo", fontName="Segoe-SB", fontSize=9.7,
                                     leading=13.8, textColor=AZUL, spaceAfter=2.6),
        "H3": ParagraphStyle("H3", fontName="Libro-B", fontSize=12.6, leading=16,
                             textColor=AZUL, spaceBefore=14, spaceAfter=6,
                             keepWithNext=1),
        "H2": ParagraphStyle("H2", fontName="Libro-B", fontSize=20.5, leading=24.5,
                             textColor=AZUL),
        "Pie": ParagraphStyle("Pie", fontName="Libro-I", fontSize=8.7, leading=11.8,
                              textColor=GRIS, alignment=TA_CENTER),
        "Celda": ParagraphStyle("Celda", fontName="Libro", fontSize=9.3, leading=12.7,
                                textColor=TINTA),
        "CeldaCab": ParagraphStyle("CeldaCab", fontName="Segoe-SB", fontSize=8.9,
                                   leading=11.8, textColor=colors.white),
        "Indice1": ParagraphStyle("Indice1", fontName="Libro-B", fontSize=11.4, leading=19,
                                  textColor=AZUL, spaceBefore=2),
        "Indice2": ParagraphStyle("Indice2", fontName="Libro", fontSize=10.1, leading=14.8,
                                  textColor=TINTA, leftIndent=13),
        "IndicePag": ParagraphStyle("IndicePag", fontName="Segoe-SB", fontSize=9.4,
                                    leading=19, textColor=AZUL, alignment=TA_RIGHT),
        "IndicePag2": ParagraphStyle("IndicePag2", fontName="Libro", fontSize=9.8,
                                     leading=14.8, textColor=GRIS, alignment=TA_RIGHT),
        "TituloIndice": ParagraphStyle("TituloIndice", fontName="Libro-B", fontSize=25,
                                       leading=29, textColor=AZUL, spaceAfter=2),
        "Codigo": ParagraphStyle("Codigo", fontName="Mono", fontSize=8.3, leading=11.8,
                                 textColor=colors.HexColor("#243B53"),
                                 backColor=GRIS_CLARO, borderPadding=6,
                                 leftIndent=6, rightIndent=6, spaceBefore=3, spaceAfter=6),
    }


EST = _estilos()

_CODIGO = re.compile(r"`([^`]+)`")
_NEGRITA = re.compile(r"\*\*(.+?)\*\*")
_CURSIVA = re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])")
_ENLACE = re.compile(r"\[([^\]]+)\]\([^)\s]*\)")
_TAG = re.compile(r"(<[^>]+>)")
_NUMERO = re.compile(r"^(\d+)\.\s+(.*)$")
_VINETA = re.compile(r"^[-*]\s+(.*)$")
_SOLO_REGLA = re.compile(r"^\|[\s:|-]+\|$")


def _escapar(texto):
    """Texto listo para el marcado de reportlab (&, <, >)."""
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _simbolos(texto):
    """Los caracteres que Segoe UI no tiene se dibujan con Segoe UI Symbol.

    Así los iconos del manual (💾, 🖨, ✅…) salen nítidos y en blanco y negro. Un
    carácter que no esté en ninguna de las dos fuentes se descarta: antes salía como
    un cuadradito en el PDF.
    """
    trozos, actual, tipo = [], "", None
    for ch in texto:
        if ch in "\ufe0f\u200d":                  # marcas de emoji que no se dibujan
            continue
        if ord(ch) < 128 or ord(ch) in _CMAP:
            cual = "texto"
        elif ord(ch) in _CMAP_SIM:
            cual = "icono"
        else:
            continue
        if tipo is None:
            tipo, actual = cual, ch
        elif cual == tipo:
            actual += ch
        else:
            trozos.append((tipo, actual))
            tipo, actual = cual, ch
    if actual:
        trozos.append((tipo, actual))
    return "".join(t if tipo == "texto" else '<font name="Sim">%s</font>' % t
                   for tipo, t in trozos)


def _fuera_de_tags(texto):
    """Aplica `_simbolos` solo al texto, sin tocar las etiquetas del marcado."""
    return "".join(p if p.startswith("<") else _simbolos(p) for p in _TAG.split(texto))


def inline(texto):
    """Markdown de una línea → marcado de reportlab (`**negrita**`, `` `código` ``)."""
    guardados = []

    def guardar(m):
        guardados.append(m.group(1))
        return "\x00%d\x00" % (len(guardados) - 1)

    t = _CODIGO.sub(guardar, texto)
    t = _escapar(t)
    t = _ENLACE.sub(r"\1", t)
    t = _NEGRITA.sub(r"<b>\1</b>", t)
    t = _CURSIVA.sub(r"<i>\1</i>", t)
    t = _fuera_de_tags(t)
    for i, codigo in enumerate(guardados):
        t = t.replace("\x00%d\x00" % i,
                      '<font name="Mono" size="8.5" color="#7C2F4E">%s</font>'
                      % _escapar(codigo))
    return t


def plano(texto):
    """El texto sin marcado (para medir anchos de columna)."""
    return re.sub(r"[*`]", "", _ENLACE.sub(r"\1", texto))


class Capitulo(Flowable):
    """Cabecera de capítulo: «CAPÍTULO N» en bronce, título en serif y filete doble.

    Sustituye a la banda de color: mismo peso visual, pero de imprenta — el número
    va en versalitas espaciadas y el título en Cambria, con un filete fino de lado a
    lado y un tramo en bronce que marca el comienzo del capítulo.
    """

    def __init__(self, texto):
        Flowable.__init__(self)
        encontrado = re.match(r"^(\d+)\.\s+(.*)$", texto)
        self.numero, self.titulo = (encontrado.group(1), encontrado.group(2)) if encontrado \
            else ("", texto)
        self.width = ANCHO
        self.alto = 0
        self._lineas = []
        self._toc_nivel = 0
        self._toc_texto = ("%s. %s" % (self.numero, self.titulo)) if self.numero else self.titulo

    def wrap(self, ancho, alto):
        self.width = ancho
        tam = EST["H2"].fontSize
        self._lineas = _envolver(self.titulo, "Libro-B", tam, ancho - 2)
        self.alto = ((4.9 * mm if self.numero else 0) + len(self._lineas) * tam * 1.2
                     + 4.6 * mm)
        return (ancho, self.alto)

    def draw(self):
        lienzo = self.canv
        y = self.alto
        if self.numero:
            rotulo(lienzo, "CAPÍTULO %s" % self.numero, 0, y - 2.9 * mm, tam=8.3,
                   color=BRONCE, espacio=1.7, fuente="Segoe-SB")
            y -= 4.9 * mm
        lienzo.setFillColor(AZUL)
        lienzo.setFont("Libro-B", EST["H2"].fontSize)
        for linea in self._lineas:
            y -= EST["H2"].fontSize * 0.86
            lienzo.drawString(0, y, linea)
            y -= EST["H2"].fontSize * 0.34
        lienzo.setStrokeColor(LINEA)
        lienzo.setLineWidth(0.6)
        lienzo.line(0, 1.7 * mm, self.width, 1.7 * mm)
        lienzo.setStrokeColor(BRONCE)
        lienzo.setLineWidth(1.7)
        lienzo.line(0, 1.7 * mm, 24 * mm, 1.7 * mm)


class Hueco(Flowable):
    """Espacio en blanco **que nunca rompe el armado**.

    Un `Spacer` normal, si le quedan menos puntos de los que mide al pie de una
    página, hace que reportlab se detenga con «Flowable … too large». Este se
    encoge a lo que quede libre: el PDF sale igual y sin saltos de página raros.
    """

    def __init__(self, alto):
        Flowable.__init__(self)
        self.alto = alto
        self.width = 0

    def wrap(self, ancho, alto):
        self.width = ancho
        return (0, min(self.alto, max(alto - 1, 0)))

    def draw(self):
        pass


def _ancho_palabra(textos, estilo):
    """Lo que mide la palabra más larga de la columna, con su fuente y su tamaño."""
    try:
        fuente = pdfmetrics.getFont(EST[estilo].fontName)
    except KeyError:                                # fuentes todavía sin registrar
        return 0.0
    tam = EST[estilo].fontSize
    ancho = 0.0
    for texto in textos:
        for palabra in re.split(r"\s+", plano(texto)):
            if palabra:
                ancho = max(ancho, fuente.stringWidth(palabra, tam))
    return ancho + 12 + 1.5               # relleno izquierdo + derecho (6 + 6), y un pelo de aire


def _cabecera(celda, ancho_util):
    """Cabecera de tabla lista para el PDF, sin dejar una palabra sola en la última línea.

    Cuando la cabecera no cabe en una línea y la última palabra se iría sola
    («El total pasa de 226 / a…»), se une a la anterior con un **espacio duro**: la
    línea que baja lleva entonces dos palabras y el encabezado se lee entero.
    """
    marcado = inline(celda)
    palabras = [p for p in re.split(r"\s+", plano(celda)) if p]
    if len(palabras) < 2:
        return marcado
    try:
        fuente = pdfmetrics.getFont(EST["CeldaCab"].fontName)
    except KeyError:                                # fuentes todavía sin registrar
        return marcado
    tam = EST["CeldaCab"].fontSize
    if fuente.stringWidth(" ".join(palabras), tam) <= ancho_util:
        return marcado                              # cabe entera en una línea
    ultimas = palabras[-2] + " " + palabras[-1]
    if fuente.stringWidth(ultimas, tam) > ancho_util:
        return marcado                              # ni las dos últimas caben juntas
    corte, dentro = -1, False                       # el último espacio que no está dentro de una etiqueta
    for i, ch in enumerate(marcado):
        if ch == "<":
            dentro = True
        elif ch == ">":
            dentro = False
        elif ch == " " and not dentro:
            corte = i
    if corte < 0:
        return marcado
    return marcado[:corte] + "\u00a0" + marcado[corte + 1:]


def tabla(filas):
    """Tabla del manual con cabecera azul, filas alternadas y rejilla suave.

    El ancho de cada columna sale del texto que lleva, pero nunca baja de lo que
    mide su palabra más larga: así «Formato» no se parte en «Format / o» ni ningún
    encabezado queda cortado a la mitad. Y si aun así una cabecera tiene que bajar
    a una segunda línea, no se deja una palabra sola al pie (ver `_cabecera`).
    """
    if not filas:
        return [Hueco(1)]
    columnas = max(len(f) for f in filas)
    filas = [f + [""] * (columnas - len(f)) for f in filas]
    pesos, minimos = [], []
    for c in range(columnas):
        textos = [f[c] for f in filas]
        largo = max(len(plano(t)) for t in textos)
        pesos.append(min(max(largo, 5), 58))
        minimos.append(max(_ancho_palabra(textos, "Celda"),
                           _ancho_palabra(textos, "CeldaCab")))
    total = float(sum(pesos)) or 1.0
    anchos = [ANCHO * p / total for p in pesos]
    anchos = [max(a, 15 * mm, m) for a, m in zip(anchos, minimos)]
    sobra = sum(anchos) - ANCHO
    if sobra > 0:                                   # se recorta a las columnas con holgura
        holgura = [max(a - max(15 * mm, m), 0) for a, m in zip(anchos, minimos)]
        reparto = sum(holgura)
        if reparto > 0:
            anchos = [a - sobra * h / reparto for a, h in zip(anchos, holgura)]
        anchos = [a * ANCHO / sum(anchos) for a in anchos]
    datos = []
    for i, fila in enumerate(filas):
        if i == 0:                                  # cabecera: sin palabras sueltas al pie
            datos.append([Paragraph(_cabecera(celda, ancho - 12), EST["CeldaCab"])
                          for celda, ancho in zip(fila, anchos)])
        else:
            datos.append([Paragraph(inline(celda), EST["Celda"]) for celda in fila])
    t = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, AZUL),
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, AZUL),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINEA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.2),
        ("TOPPADDING", (0, 0), (-1, 0), 5.6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5.6),
    ]))
    return [Hueco(5), t, Hueco(9)]


def cuadro(parrafos):
    """Nota del manual (`> …`) como **cuadro** con fondo, barra de color y borde."""
    contenido = []
    for i, texto in enumerate(parrafos):
        titulo = i == 0 and re.match(r"^\*\*[^*]+\*\*$", texto.strip())
        contenido.append(Paragraph(inline(texto),
                                   EST["NotaTitulo" if titulo else "Nota"]))
    if not contenido:
        return []
    t = Table([[contenido]], colWidths=[ANCHO], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, AZUL),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINEA),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return [Hueco(6), t, Hueco(10)]


def figura(ruta, texto):
    """Captura de pantalla enmarcada, con su número y su nombre debajo."""
    if not os.path.exists(ruta):
        return [Paragraph(inline("(Falta la imagen %s)" % ruta), EST["Pie"])]
    img = Image(ruta)
    escala = min((ANCHO - 14) / img.imageWidth, (105 * mm) / img.imageHeight, 1.0)
    img.drawWidth = img.imageWidth * escala
    img.drawHeight = img.imageHeight * escala
    marco = Table([[img], [Paragraph(inline(texto), EST["Pie"])]],
                  colWidths=[ANCHO], hAlign="LEFT")
    marco.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, LINEA),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Hueco(5), KeepTogether(marco), Hueco(8)]


class Linea(Flowable):
    """Línea fina que también se encoge si queda poco espacio (nunca rompe el armado)."""

    def __init__(self, grosor=0.7, color=None, largo=None):
        Flowable.__init__(self)
        self.grosor = grosor
        self.color = color or LINEA
        self.largo = largo
        self.width = 0
        self._alto = grosor

    def wrap(self, ancho, alto):
        self.width = ancho
        self._alto = min(self.grosor + 2, max(alto - 0.5, 0))
        return (ancho, self._alto)

    def draw(self):
        fin = self.width if self.largo is None else min(self.largo, self.width)
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.grosor)
        self.canv.line(0, self._alto / 2.0, fin, self._alto / 2.0)


def regla():
    """Línea separadora (`---`)."""
    return [Hueco(7), Linea(), Hueco(9)]


def _envolver(texto, fuente, tam, ancho):
    """Parte un texto en renglones que caben en `ancho` (para la portada)."""
    renglones, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if pdfmetrics.stringWidth(prueba, fuente, tam) <= ancho or not actual:
            actual = prueba
        else:
            renglones.append(actual)
            actual = palabra
    if actual:
        renglones.append(actual)
    return renglones


def rotulo(lienzo, texto, x, y, tam=7.4, color=None, espacio=1.1, fuente="Segoe",
           derecha=False, centro=False):
    """Versalitas espaciadas (el «tracking» de las etiquetas de imprenta).

    reportlab no trae espaciado entre letras en el lienzo: se escribe con un objeto
    de texto, que sí lo admite. Devuelve el ancho ocupado por si hay que encadenar.
    """
    ancho = pdfmetrics.stringWidth(texto, fuente, tam) + espacio * len(texto)
    if derecha:
        x -= ancho
    elif centro:
        x -= ancho / 2.0
    lienzo.saveState()          # el Tc del objeto de texto se queda en el estado: se aísla
    objeto = lienzo.beginText(x, y)
    objeto.setFont(fuente, tam)
    objeto.setFillColor(color or GRIS)
    objeto.setCharSpace(espacio)
    objeto.textLine(texto)
    lienzo.drawText(objeto)
    lienzo.restoreState()
    return ancho


def portada(lienzo):
    """Portada editorial: lomo azul, título en serif y filete en bronce."""
    ancho, alto = A4
    lienzo.saveState()
    # lomo: una franja azul que da el mismo aire que la cabecera de los capítulos
    lienzo.setFillColor(AZUL)
    lienzo.rect(0, 0, 7 * mm, alto, stroke=0, fill=1)

    # membrete
    rotulo(lienzo, "MIEMPRESA", MARGEN_IZQ, alto - 27 * mm, tam=10, color=AZUL,
           espacio=2.6, fuente="Segoe-SB")
    # el logo de la empresa, arriba a la derecha (sustituye a la antigua etiqueta)
    if os.path.exists(LOGO):
        lienzo.drawImage(LOGO, ancho - MARGEN_DER - 56 * mm, alto - 40 * mm,
                         width=56 * mm, height=16 * mm, mask="auto",
                         preserveAspectRatio=True, anchor="ne")
    else:
        rotulo(lienzo, "DOCUMENTACIÓN DE USO", ancho - MARGEN_DER, alto - 27 * mm, tam=8.2,
               espacio=1.3, derecha=True)
    lienzo.setStrokeColor(BRONCE)
    lienzo.setLineWidth(1.1)
    lienzo.line(MARGEN_IZQ, alto - 31 * mm, MARGEN_IZQ + 34 * mm, alto - 31 * mm)

    # título y subtítulo
    lienzo.setFillColor(AZUL)
    lienzo.setFont("Libro-B", 36)
    lienzo.drawString(MARGEN_IZQ, alto - 64 * mm, TITULO)
    lienzo.setFillColor(AZUL_MEDIO)
    lienzo.setFont("Segoe-L", 17)
    lienzo.drawString(MARGEN_IZQ, alto - 77 * mm, SUBTITULO)

    # filete doble bajo el título: bronce corto sobre línea de imprenta
    lienzo.setStrokeColor(LINEA)
    lienzo.setLineWidth(0.6)
    lienzo.line(MARGEN_IZQ, alto - 86 * mm, ancho - MARGEN_DER, alto - 86 * mm)
    lienzo.setStrokeColor(BRONCE)
    lienzo.setLineWidth(2)
    lienzo.line(MARGEN_IZQ, alto - 86 * mm, MARGEN_IZQ + 22 * mm, alto - 86 * mm)

    # versión
    rotulo(lienzo, "VERSIÓN %s   ·   %s" % (VERSION, FECHA.upper()), MARGEN_IZQ,
           alto - 95 * mm, tam=8.6, espacio=1.1, fuente="Segoe-SB")

    # de qué trata
    y = alto - 118 * mm
    lienzo.setFillColor(TINTA)
    lienzo.setFont("Libro", 11.4)
    for linea in _envolver("Cómo generar, revisar, ajustar y justificar un viático, "
                           "pantalla por pantalla y con cada botón explicado.",
                           "Libro", 11.4, ANCHO - 8 * mm):
        lienzo.drawString(MARGEN_IZQ, y, linea)
        y -= 6.3 * mm
    y -= 5 * mm
    lienzo.setFillColor(GRIS)
    lienzo.setFont("Libro", 10.2)
    for linea in _envolver("Las capturas salen del programa real, así que los importes que "
                           "se ven son de muestra. Los recuadros azules son las notas "
                           "importantes: qué calcula el sistema, por qué un valor sale en "
                           "cero y qué revisar cuando algo no cuadra.",
                           "Libro", 10.2, ANCHO - 8 * mm):
        lienzo.drawString(MARGEN_IZQ, y, linea)
        y -= 5.5 * mm

    # resumen del contenido
    if RESUMEN["capitulos"]:
        rotulo(lienzo, "%d CAPÍTULOS   ·   %d FIGURAS   ·   %d APARTADOS"
               % (RESUMEN["capitulos"], RESUMEN["figuras"], RESUMEN["apartados"]),
               MARGEN_IZQ, alto - 168 * mm, tam=8.2, color=BRONCE, espacio=1.3,
               fuente="Segoe-SB")

    # pie de autor
    lienzo.setStrokeColor(LINEA)
    lienzo.setLineWidth(0.6)
    lienzo.line(MARGEN_IZQ, 42 * mm, ancho - MARGEN_DER, 42 * mm)
    lienzo.setFillColor(AZUL)
    lienzo.setFont("Libro-B", 11.5)
    lienzo.drawString(MARGEN_IZQ, 35 * mm, AUTOR)
    lienzo.setFillColor(GRIS)
    lienzo.setFont("Segoe", 9)
    lienzo.drawString(MARGEN_IZQ, 29.5 * mm, CONTACTO)

    # banda inferior
    lienzo.setFillColor(AZUL)
    lienzo.rect(0, 0, ancho, 13 * mm, stroke=0, fill=1)
    rotulo(lienzo, "SISTEMA DE VIÁTICOS MIEMPRESA", MARGEN_IZQ, 5 * mm, tam=7.8,
           color=colors.white, espacio=1.1)
    rotulo(lienzo, "MANUAL DE USUARIO", ancho - MARGEN_DER, 5 * mm, tam=7.8,
           color=colors.white, espacio=1.1, derecha=True)
    lienzo.restoreState()


def indice(entradas):
    """Índice del manual: cada capítulo y apartado con su número de página."""
    if not entradas:
        return [Hueco(1)]
    filas, niveles = [], []
    for nivel, texto, pagina in entradas:
        marcado = inline(texto)
        if nivel == 0:
            numero = re.match(r"^(\d+)\.\s+(.*)$", texto)
            if numero:                              # el número en bronce, como en el capítulo
                marcado = ('<font name="Segoe-SB" size="9.6" color="#8C6A3F">%s.</font>'
                           '&nbsp;&nbsp;%s' % (numero.group(1), inline(numero.group(2))))
        filas.append([Paragraph(marcado, EST["Indice1" if nivel == 0 else "Indice2"]),
                      Paragraph(str(pagina), EST["IndicePag" if nivel == 0
                                else "IndicePag2"])])
        niveles.append(nivel)
    tabla_indice = Table(filas, colWidths=[ANCHO - 20 * mm, 20 * mm], hAlign="LEFT")
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("TOPPADDING", (0, 1), (-1, -1), 3.4),
    ]
    for i, nivel in enumerate(niveles):        # filete solo sobre los capítulos
        estilo.append(("TOPPADDING", (0, i), (-1, i), 11 if nivel == 0 else 3.4))
        if i and nivel == 0:
            estilo.append(("LINEABOVE", (0, i), (-1, i), 0.5, LINEA))
    tabla_indice.setStyle(TableStyle(estilo))
    return [tabla_indice]


class Numerado(pdfcanvas.Canvas):
    """Canvas que escribe el pie «Página X de Y» en todas las páginas menos la portada.

    El total de páginas solo se sabe al terminar de armar el manual, así que el manual
    se arma más de una vez (ver `main`): antes de cada pasada se deja el total en
    `total` y el canvas lo escribe tal cual. Las páginas se escriben **en el momento**
    (no se guardan para el final), que es lo que mantiene atados los marcadores del PDF
    a su página de verdad.
    """

    total = 0                            # total que se escribe en el pie (lo fija main)
    ultimo_total = 0                     # páginas del último PDF armado

    def showPage(self):
        if self._pageNumber > 1:         # la portada va sin pie
            self._pie(Numerado.total or self._pageNumber)
        Numerado.ultimo_total = self._pageNumber
        pdfcanvas.Canvas.showPage(self)

    def _pie(self, total):
        ancho = A4[0]
        self.saveState()
        self.setStrokeColor(LINEA)
        self.setLineWidth(0.6)
        self.line(MARGEN_IZQ, 15 * mm, ancho - MARGEN_DER, 15 * mm)
        self.setFillColor(GRIS)
        rotulo(self, "MIEMPRESA", MARGEN_IZQ, 10.2 * mm, tam=7.4, espacio=1)
        rotulo(self, "DOCUMENTACIÓN DE USO", ancho - MARGEN_DER, 10.2 * mm, tam=7.4,
               espacio=1, derecha=True)
        self.setFillColor(GRIS)
        self.setFont("Libro", 8.8)
        self.drawCentredString(ancho / 2.0, 10.2 * mm,
                               "Página %d de %d" % (self._pageNumber, total))
        self.restoreState()


class Manual(BaseDocTemplate):
    """Documento del manual: portada, encabezado, índice y marcadores del PDF."""

    def __init__(self, archivo):
        BaseDocTemplate.__init__(
            self, archivo, pagesize=A4, leftMargin=MARGEN_IZQ, rightMargin=MARGEN_DER,
            topMargin=MARGEN_SUP, bottomMargin=MARGEN_INF,
            title="%s — %s" % (TITULO, SUBTITULO), author=AUTOR,
            subject="Manual de usuario del Sistema de Viáticos Miempresa",
            creator="herramientas/manual_pdf.py", keywords="viáticos, manual, Miempresa")
        self.entradas = []
        marco = Frame(MARGEN_IZQ, MARGEN_INF, ANCHO,
                      A4[1] - MARGEN_SUP - MARGEN_INF, id="cuerpo",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="normal", frames=[marco],
                                            onPage=self.decorar)])

    def decorar(self, lienzo, doc):
        """Portada en la página 1; en las demás, la línea del encabezado."""
        if doc.page == 1:
            portada(lienzo)
            return
        lienzo.saveState()
        lienzo.setStrokeColor(LINEA)
        lienzo.setLineWidth(0.6)
        lienzo.line(MARGEN_IZQ, A4[1] - MARGEN_SUP + 8.6 * mm,
                    A4[0] - MARGEN_DER, A4[1] - MARGEN_SUP + 8.6 * mm)
        rotulo(lienzo, "SISTEMA DE VIÁTICOS MIEMPRESA", MARGEN_IZQ,
               A4[1] - MARGEN_SUP + 10.9 * mm, tam=7.4, espacio=1.1)
        rotulo(lienzo, "MANUAL DE USUARIO · VERSIÓN %s" % VERSION,
               A4[0] - MARGEN_DER, A4[1] - MARGEN_SUP + 10.9 * mm, tam=7.4, espacio=1.1,
               derecha=True)
        lienzo.restoreState()

    def afterFlowable(self, flujo):
        """Anota los capítulos y apartados: marcadores del PDF y datos del índice."""
        nivel = getattr(flujo, "_toc_nivel", None)
        texto = getattr(flujo, "_toc_texto", None)
        if nivel is None or not texto:
            return
        clave = "sec%d" % len(self.entradas)
        self.entradas.append((nivel, texto, self.page))
        self.canv.bookmarkPage(clave)
        self.canv.addOutlineEntry(texto, clave, level=nivel, closed=False)


def leer_manual(ruta_md, carpeta_img):
    """El manual en Markdown → lista de flowables de reportlab."""
    texto = io.open(ruta_md, encoding="utf-8").read().replace("\r\n", "\n")
    lineas = texto.split("\n")
    flujos = []
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        if not linea.strip():
            i += 1
            continue
        # comentario de autoría del .md
        if linea.lstrip().startswith("<!--"):
            while i < len(lineas) and "-->" not in lineas[i]:
                i += 1
            i += 1
            continue
        # el título del documento va en la portada
        if re.match(r"^#\s", linea):
            i += 1
            continue
        # capítulo (## 3. …) → página nueva con su cabecera
        if re.match(r"^##\s", linea):
            flujos.append(PageBreak())
            flujos.append(Capitulo(linea[2:].strip()))
            flujos.append(Hueco(3))
            i += 1
            continue
        # apartado (### 3.1 …): el número en bronce, el título en serif
        if re.match(r"^###\s", linea):
            apartado = linea[3:].strip()
            numero = re.match(r"^(\d+(?:\.\d+)+)\s+(.*)$", apartado)
            if numero:
                marcado = ('<font name="Segoe-SB" size="9.9" color="#8C6A3F">%s</font>'
                           '&nbsp;&nbsp;%s' % (numero.group(1), inline(numero.group(2))))
            else:
                marcado = inline(apartado)
            parrafo = Paragraph(marcado, EST["H3"])
            parrafo._toc_nivel = 1
            parrafo._toc_texto = apartado
            flujos.append(parrafo)
            i += 1
            continue
        # figura
        imagen = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", linea)
        if imagen:
            archivo = os.path.basename(imagen.group(2))
            flujos.extend(figura(os.path.join(carpeta_img, archivo), imagen.group(1)))
            i += 1
            continue
        # tabla
        if linea.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                fila = lineas[i].strip()
                if not _SOLO_REGLA.match(fila):
                    filas.append([c.strip() for c in fila.strip("|").split("|")])
                i += 1
            nuevo = tabla(filas)
            # La tabla se mide de verdad (a lo ancho de la caja) para decidir el corte:
            # si cabe entera en una página, empieza en la siguiente cuando al pie no
            # entra (nada de dos filas sueltas); si es más alta que la página, se
            # permite partirla pero el título y su línea no se quedan solos abajo.
            alto_caja = A4[1] - MARGEN_SUP - MARGEN_INF
            alto_tabla = nuevo[1].wrap(ANCHO, alto_caja)[1] + 16 if len(nuevo) == 3 else 0
            desde = len(flujos)
            for atras in (1, 2):                    # el título / la línea que la presentan
                if len(flujos) < atras:
                    break
                anterior = flujos[-atras]
                if (isinstance(anterior, Paragraph)
                        and getattr(anterior.style, "name", "") in ("H3", "Cuerpo")
                        and len(plano(getattr(anterior, "text", ""))) <= 160):
                    desde = len(flujos) - atras
                else:
                    break
            if alto_tabla and alto_tabla < alto_caja - 24:
                flujos.insert(desde, CondPageBreak(alto_tabla))
            elif alto_tabla:
                flujos.insert(desde, CondPageBreak(120))
            flujos.extend(nuevo)
            continue
        # cuadro de aviso (líneas que empiezan con >)
        if linea.lstrip().startswith(">"):
            parrafos, actual = [], []
            while i < len(lineas) and lineas[i].lstrip().startswith(">"):
                limpio = lineas[i].lstrip()[1:].strip()
                if limpio:
                    actual.append(limpio)
                elif actual:
                    parrafos.append(" ".join(actual))
                    actual = []
                i += 1
            if actual:
                parrafos.append(" ".join(actual))
            flujos.extend(cuadro(parrafos))
            continue
        # listas (numeradas y de viñetas, con sus líneas de continuación)
        if _VINETA.match(linea) or _NUMERO.match(linea):
            while i < len(lineas):
                actual = lineas[i].rstrip()
                numerada = _NUMERO.match(actual)
                vineta = _VINETA.match(actual)
                if not numerada and not vineta:
                    break
                marca = numerada.group(1) + "." if numerada else "\u2022"
                item = numerada.group(2) if numerada else vineta.group(1)
                i += 1
                while (i < len(lineas) and lineas[i].strip()
                       and lineas[i].startswith(("  ", "\t"))):
                    item += " " + lineas[i].strip()
                    i += 1
                flujos.append(Paragraph(inline(item), EST["Item"], bulletText=marca))
            flujos.append(Hueco(4))
            continue
        # línea separadora
        if re.match(r"^---\s*$", linea):
            flujos.extend(regla())
            i += 1
            continue
        # párrafo: se juntan las líneas hasta el próximo bloque
        partes = [linea.strip()]
        i += 1
        while i < len(lineas):
            siguiente = lineas[i].rstrip()
            if (not siguiente.strip() or siguiente.startswith(("|", ">", "#", "!", "---"))
                    or _VINETA.match(siguiente) or _NUMERO.match(siguiente)
                    or siguiente.startswith("```")):
                break
            partes.append(siguiente.strip())
            i += 1
        flujos.append(Paragraph(inline(" ".join(partes)), EST["Cuerpo"]))
    return flujos


def _olvidar(flujo):
    """Borra la marca interna que reportlab deja al pasar por el pie de página.

    Cuando una pasada no alcanza a colocar un párrafo, reportlab le pone
    `_postponed`; si el **mismo** objeto se vuelve a usar en otra pasada (el índice
    se arma en dos pasadas), el párrafo se da por fallado y el armado se detiene con
    «Flowable … too large». Aquí se limpia antes de cada pasada.
    """
    if isinstance(flujo, (list, tuple)):
        for elemento in flujo:
            _olvidar(elemento)
        return
    if hasattr(flujo, "_postponed"):
        try:
            del flujo._postponed
        except AttributeError:
            pass
    for atributo in ("_content", "_cellvalues", "_flowables"):
        contenido = getattr(flujo, atributo, None)
        if isinstance(contenido, (list, tuple)):
            _olvidar(contenido)


def main():
    origen = sys.argv[1] if len(sys.argv) > 1 else MD
    destino = sys.argv[2] if len(sys.argv) > 2 else PDF
    if not os.path.exists(origen):
        raise SystemExit("No encuentro el manual: %s" % origen)
    registrar_fuentes()
    # la portada resume el manual con lo que de verdad trae el .md
    fuente_md = io.open(origen, encoding="utf-8").read()
    RESUMEN["capitulos"] = len(re.findall(r"(?m)^##\s", fuente_md))
    RESUMEN["apartados"] = len(re.findall(r"(?m)^###\s", fuente_md))
    RESUMEN["figuras"] = len(re.findall(r"(?m)^!\[", fuente_md))
    todos = leer_manual(origen, IMGS)
    # La presentación va antes del índice y el índice antes del primer capítulo.
    corte = next((k for k, f in enumerate(todos) if isinstance(f, PageBreak)), len(todos))
    presentacion = [Hueco(1), PageBreak()] + todos[:corte]
    capitulos = todos[corte:]
    portadilla = [PageBreak(), Paragraph("Índice", EST["TituloIndice"]), Hueco(1),
                  Linea(1.6, BRONCE, 30 * mm), Hueco(7),
                  Paragraph("A la derecha está la página donde empieza cada capítulo; los "
                            "apartados van sangrados. Cada capítulo abre en página nueva.",
                            EST["Entradilla"]), Hueco(10)]
    # 1) Una pasada **sin** el índice, solo para saber en qué página cae cada capítulo
    #    y cuántas páginas tiene el manual (para el «Página X de Y» del pie).
    borrador = Manual(os.path.join(os.path.dirname(destino) or ".", "_manual_indice.pdf"))
    _olvidar([presentacion, portadilla, capitulos])
    Numerado.total = 0                    # todavía no se sabe: el borrador no se entrega
    borrador.build(presentacion + portadilla + capitulos, canvasmaker=Numerado)
    entradas = list(borrador.entradas)
    total = Numerado.ultimo_total
    # 2) El PDF de verdad, con el índice y el total del pie (se repite si algo se corrió).
    documento = borrador
    for _ in range(4):
        documento = Manual(destino)
        _olvidar([presentacion, portadilla, capitulos])
        Numerado.total = total
        documento.build(presentacion + portadilla + indice(entradas) + capitulos,
                        canvasmaker=Numerado)
        nuevas = list(documento.entradas)
        if ([n[2] for n in nuevas] == [e[2] for e in entradas]
                and Numerado.ultimo_total == total):
            break
        entradas = nuevas
        total = Numerado.ultimo_total
    try:
        os.remove(borrador.filename)
    except OSError:
        pass
    print("PDF listo: %s" % destino)
    print("Páginas: %d · entradas en el índice: %d" % (Numerado.ultimo_total, len(entradas)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
