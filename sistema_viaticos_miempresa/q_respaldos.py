# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_respaldos.py — Respaldos de viáticos: lista completa con búsqueda (PySide6).

Es la misma pantalla de `ui_respaldos.py`: se listan TODOS los archivos de respaldo
(facturas y comprobantes) y se pueden buscar por N° de viático, nombre de archivo,
concepto o persona. Doble clic (o el botón «Abrir seleccionado») abre el archivo.
"""
import os

import database as db
import qt_comunes as C

COLUMNAS = [
    ("numero", "N° VIÁTICO", 100),
    ("archivo", "ARCHIVO", 360),
    ("concepto", "CONCEPTO", 190),
    ("subido_por", "SUBIDO POR", 170),
    ("fecha", "FECHA", 150),
]


class RespaldosWindow(C.Ventana):
    """Ventana del módulo de respaldos."""

    def __init__(self, master=None, usuario=None):
        usuario = usuario or {"usuario": "SISTEMA", "nombre": "MIEMPRESA"}
        super().__init__(
            titulo="Respaldos — Sistema de Viáticos",
            usuario=usuario, padre=master, ancho=1120, alto=720,
            info=C.etiqueta_sesion(usuario))
        self._todos = []
        self._build()
        self._cargar()

    # ---------- construcción ----------
    def _build(self):
        self.tabla = C.TablaDatos(
            COLUMNAS, titulo="Archivos de respaldo",
            nombre="respaldos", alto=430, filtros=True)
        self.tabla.agregar_boton("👁  Abrir seleccionado", self._abrir)
        self.tabla.agregar_boton("↺  Actualizar", self._cargar)
        self.tabla.al_doble_clic(lambda _fila: self._abrir())
        self.agregar(self.tabla, 1)

    # ---------- datos ----------
    def _cargar(self):
        """Vuelve a leer la lista completa de respaldos."""
        try:
            self._todos = db.listar_todos_respaldos()
        except Exception as ex:
            C.error(self, "Respaldos", "No se pudo leer la lista de respaldos:\n\n%s" % ex)
            self._todos = []
        self.tabla.filtro_extra = self._coincide
        self.tabla.limpiar_filtros()
        self.tabla.set_datos(self._filas(self._todos))
        self.tabla.set_pie("%d archivo(s) · doble clic para abrir un archivo"
                           % len(self._todos))
        return self

    @staticmethod
    def _filas(filas):
        """Prepara las filas para la tabla (mismos datos + las columnas visibles)."""
        salida = []
        for r in filas:
            d = dict(r)
            try:
                d["numero"] = db.numero_visible(r.get("viatico_numero"))
            except Exception:
                d["numero"] = r.get("viatico_numero") or ""
            d["archivo"] = r.get("nombre_archivo") or ""
            d["concepto"] = r.get("concepto") or ""
            d["subido_por"] = r.get("empleado") or ""
            d["fecha"] = r.get("creado_el") or ""
            salida.append(d)
        return salida

    @staticmethod
    def _coincide(fila, texto):
        """La misma búsqueda de antes: número, archivo, concepto o persona."""
        texto = (texto or "").strip().upper()
        numero = str(fila.get("viatico_numero") or "")
        visible = str(fila.get("numero") or "")
        archivo = (fila.get("nombre_archivo") or "").upper()
        if texto.isdigit():
            return (numero == texto or visible == texto or texto in archivo)
        return (texto in archivo
                or texto in (fila.get("concepto") or "").upper()
                or texto in (fila.get("empleado") or "").upper()
                or texto in numero
                or texto in visible)

    # ---------- acciones ----------
    def _abrir(self):
        r = self.tabla.seleccion()
        if not r:
            C.aviso(self, "Respaldos", "Seleccione un archivo.")
            return
        ruta = db.ruta_para_abrir(r) if r.get("id") else r.get("ruta")
        if not ruta or not os.path.exists(ruta):
            C.aviso(self, "Respaldos", "El archivo ya no está disponible.")
            return
        if not C.abrir_archivo(ruta):
            C.error(self, "Respaldos", "No se pudo abrir el archivo:\n\n%s" % ruta)

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
