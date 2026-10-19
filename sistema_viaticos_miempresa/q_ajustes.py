# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_ajustes.py — Justificación de viáticos (gastos + facturas + cierre), PySide6.

Mismas funciones que `ui_ajustes.py`, con el diseño a dos columnas (todo en una sola
pantalla, sin bajar con la barra de desplazamiento):
  izquierda: lista de viáticos, datos del viático elegido y recibos/resumen/cierre.
  derecha:   digitación del gasto, detalle de gastos (como el Excel de justificación)
             y las facturas del viático.

Permite: registrar/editar/eliminar gastos, subir y quitar facturas, firmar los recibos,
anotar devolución o compensación, justificar, devolver a pendiente, ver el viático
original con sus ajustes, imprimir la justificación y exportar a Excel (la lista de
viáticos que se ve y la justificación del viático elegido).
"""
import os
import subprocess

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                               QListWidget, QSplitter, QVBoxLayout, QWidget)

import database as db
import qt_comunes as C
import qt_tema as T
import reportes

# --------------------------------------------------------------- conceptos
CONCEPTOS = ["HOSPEDAJE", "COMBUSTIBLE/ORDEN", "BUSES", "TAXIS O CAMIONETAS",
             "ALIMENTACIÓN", "PEAJE", "OTROS"]
CAMPO_CONCEPTO = {"HOSPEDAJE": "hospedaje", "COMBUSTIBLE/ORDEN": "combustible",
                  "BUSES": "buses", "TAXIS O CAMIONETAS": "taxis",
                  "ALIMENTACIÓN": "alimentacion", "PEAJE": "peaje", "OTROS": "otros"}
CAMPO_A_CONCEPTO = {v: k for k, v in CAMPO_CONCEPTO.items()}

_IZQ = ("comprobante", "proveedor", "lugar", "nota", "archivos")


def _col(clave, titulo, ancho, numerica=False):
    """Columna de tabla: a la izquierda los textos, a la derecha los valores."""
    return (clave, titulo, ancho, Qt.AlignRight if numerica else Qt.AlignLeft)


# Detalle de gastos: mismo formato del Excel de justificación.
# Detalle de gastos: mismo formato del Excel de justificación. Los anchos se ajustaron
# para que los títulos largos (COMBUSTIBLE/ORDEN, TAXIS O CAMIONETAS, ALIMENTACIÓN)
# entren completos y no salgan recortados.
COLS_G = [_col("fecha", "FECHA", 76), _col("comprobante", "NRO. COMPROBANTE", 100),
          _col("tipo", "TIPO", 72), _col("ruc", "RUC", 80),
          _col("proveedor", "PROVEEDOR", 110), _col("lugar", "LUGAR", 82),
          _col("hospedaje", "HOSPEDAJE", 80, True),
          _col("combustible", "COMBUSTIBLE/ORDEN", 122, True),
          _col("buses", "BUSES", 58, True), _col("taxis", "TAXIS O CAMIONETAS", 132, True),
          _col("alimentacion", "ALIMENTACIÓN", 96, True), _col("peaje", "PEAJE", 62, True),
          _col("otros", "OTROS", 62, True), _col("total", "TOTAL", 74, True),
          _col("nota", "EXPLICACIÓN", 124), _col("archivos", "FACTURAS", 95)]

# Lista de viáticos registrados.
COLS_V = [_col("numero", "N°", 45, True), _col("salida", "Salida", 80),
          _col("regreso", "Regreso", 80), _col("responsable", "Responsable", 130),
          _col("empleados", "Empleados", 150), _col("total", "Total", 70, True),
          _col("estado", "Estado", 90)]


def fmt(v):
    """Igual que en la justificación: los ceros se ven como «-»."""
    v = float(v or 0)
    return "-" if abs(v) < 0.005 else "$%.2f" % v


def fmt_f(iso):
    """Fecha AAAA-MM-DD → DD/MM/AAAA."""
    if not iso:
        return ""
    try:
        y, m, d = str(iso).split("-")
        return "%s/%s/%s" % (d, m, y)
    except Exception:
        return str(iso)


class AjustesWindow(C.Ventana):
    """Ventana de justificación de viáticos (dos columnas)."""

    def __init__(self, master=None, usuario=None, numero=None):
        usuario = usuario or {}
        super().__init__(
            titulo="Justificación de viáticos — Sistema de Viáticos",
            usuario=usuario, padre=master, ancho=1500, alto=860,
            empezar_maximizada=True,
            info=C.etiqueta_sesion(usuario))
        self.numero = None                # viático que se está justificando
        self.gasto_sel = None             # gasto que se está editando (None = nuevo)
        self.dato = {}                    # rótulos del panel «Datos del viático»
        self.ent = {}                     # campos del formulario de gasto
        self._lista_firma = None
        self._build()
        self._cargar_lista()
        self._limpiar_panel()
        # Refresco de fondo cada 15 s: si otra computadora registró un viático, aparece
        # solo (no parpadea: si la lista quedó igual no se redibuja).
        self._refresco = QTimer(self)
        self._refresco.timeout.connect(lambda: self._cargar_lista(automatico=True))
        self._refresco.start(15000)
        if numero:
            self.seleccionar(numero)

    # ---------- construcción ----------
    def _build(self):
        filtros = C.Tarjeta()
        fila = C.margenes(QHBoxLayout(), esp=8)
        fila.addWidget(C.etiqueta("🔍 Buscar:", clave=True))
        self.txt_buscar = C.campo("", ancho=200,
                                  placeholder="N° de viático, empleado, lugar…")
        self.txt_buscar.textChanged.connect(lambda _t: self._cargar_lista())
        fila.addWidget(self.txt_buscar)
        fila.addWidget(C.etiqueta("Estado:", clave=True))
        self.cb_estado = C.combo(["TODOS", "PENDIENTE", "JUSTIFICADO", "ANULADO"],
                                 "TODOS", ancho=130)
        self.cb_estado.currentTextChanged.connect(lambda _t: self._cargar_lista())
        fila.addWidget(self.cb_estado)
        fila.addWidget(C.boton_secundario("🔄  Actualizar", self._cargar_lista))
        # Excel a la vista: la lista que se está viendo y la justificación del viático
        # elegido (lo mismo que se imprime, en un solo lugar).
        fila.addWidget(C.etiqueta("📊  Excel:", clave=True))
        fila.addWidget(C.boton_primario("Lista de viáticos", self.exportar_excel_lista))
        fila.addWidget(C.boton_primario("Justificación", self.exportar_excel_justificacion))
        fila.addStretch(1)
        filtros.agregar_fila(fila)
        self.agregar(filtros)

        self.division = QSplitter(Qt.Horizontal)
        self.division.addWidget(self._columna_izquierda())
        self.division.addWidget(self._columna_derecha())
        self.division.setStretchFactor(0, 1)
        self.division.setStretchFactor(1, 2)
        self.division.setChildrenCollapsible(False)
        self.agregar(self.division, 1)

    def _columna_izquierda(self):
        izq = QWidget()
        lay = C.margenes(QVBoxLayout(izq), esp=8)

        # --- viáticos registrados ---
        self.tabla_v = C.Tabla(COLS_V, ordenar=False, alto_filas=22)
        self.tabla_v.setMinimumHeight(T.px(96, 72))
        self.tabla_v.agregar_manejadores(al_seleccionar=lambda _f: self._cargar_viatico())
        lv = C.Tarjeta("Viáticos registrados")
        lv.agregar(self.tabla_v, 1)
        lay.addWidget(lv, 1)

        # --- datos del viático seleccionado ---
        # Cada renglón va en su propia «banda» (franja clara alternada, dos pares por
        # renglón y los textos largos a todo el ancho): así los datos se distinguen
        # entre sí y no se ven amontonados como en una sola cuadrícula.
        dp = C.Tarjeta("Datos del viático seleccionado")
        parejas = [
            [("Beneficiario (encargado):", "Beneficiario (encargado):"),
             ("Salida Miempresa:", "salida_lbl")],
            [("Proyecto / cliente:", "Proyecto / cliente:"),
             ("Llegada Miempresa:", "regreso_lbl")],
            [("Viaja a:", "Viaja a:"), ("Llegada al trabajo:", "llegada_lbl")],
            [("Vehículo:", "Vehículo:"), ("Salida del trabajo:", "saltr_lbl")],
            [("Maneja (chofer):", "Maneja (chofer):"), ("Estado:", "estado_lbl")],
            [("Creado por:", "Creado por:"), ("Ajustes:", "ajustes_lbl")],
            [("Personas:", "personas_lbl")],
        ]
        for indice, renglon in enumerate(parejas):
            banda = QFrame()
            banda.setObjectName("bandaDatos" if indice % 2 == 0 else "bandaDatosPar")
            bl = C.margenes(QHBoxLayout(banda), 8, 5, 8, 5, 8)
            for posicion, (etq, clave) in enumerate(renglon):
                if posicion:
                    bl.addSpacing(18)
                # Rótulo de ancho fijo y alineado a la derecha: así todos los valores
                # quedan en la misma columna (antes cada renglón se corría distinto).
                rotulo = C.etiqueta(etq, clave=True)
                rotulo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                rotulo.setFixedWidth(T.px(178, 150))
                bl.addWidget(rotulo)
                lbl = C.etiqueta("—")
                lbl.setWordWrap(True)
                self.dato[clave] = lbl
                bl.addWidget(lbl, 1)
            dp.agregar(banda)
        lay.addWidget(dp)

        # --- recibos, resumen y cierre (todo junto: antes eran dos tarjetas) ---
        rc = C.Tarjeta("Recibos, resumen y cierre")
        fr = C.margenes(QHBoxLayout(), esp=6)
        self.txt_r1 = C.campo("", ancho=80)
        self.txt_r2 = C.campo("", ancho=80)
        self.txt_r3 = C.campo("", ancho=80)
        for etq, caja in (("Recibo N°1:", self.txt_r1), ("N°2:", self.txt_r2),
                          ("N°3:", self.txt_r3)):
            fr.addWidget(C.etiqueta(etq, clave=True))
            fr.addWidget(caja)
        fr.addWidget(C.boton_secundario("💾  Guardar", self._guardar_recibos))
        fr.addStretch(1)
        rc.agregar_fila(fr)

        self.lbl_ent = C.etiqueta("Entregado: —", clave=True)
        self.lbl_resp = C.etiqueta("Respaldado: —", clave=True)
        self.lbl_saldo = C.etiqueta("Saldo: —", clave=True)
        self.lbl_est = C.etiqueta("", clave=True)
        fs = C.margenes(QHBoxLayout(), esp=16)
        for lbl in (self.lbl_ent, self.lbl_resp, self.lbl_saldo, self.lbl_est):
            fs.addWidget(lbl)
        fs.addStretch(1)
        rc.agregar_fila(fs)

        self.txt_dev = C.campo("0", ancho=90)
        self.txt_pago = C.campo("0", ancho=90)
        self.txt_dev_obs = C.campo("", placeholder="Por qué devuelve o a favor del empleado")
        self.txt_nota = C.campo("", placeholder="Nota de cierre de la justificación")
        self.txt_elab = C.campo(self._elaborado_por_defecto(), ancho=220)
        rc.agregar(C.rejilla([
            [("Devuelve a Miempresa $:", self.txt_dev),
             ("A favor del empleado $:", self.txt_pago)],
            [("Motivo:", self.txt_dev_obs), ("Nota de cierre:", self.txt_nota)],
            [("Elaborado por:", self.txt_elab)],
        ], esp=6, etiqueta_ancho=150))
        fb = C.margenes(QHBoxLayout(), esp=6)
        fb.addWidget(C.boton_amarillo("✅  JUSTIFICAR", self._justificar))
        fb.addWidget(C.boton_secundario("↩  A pendiente", self._reactivar))
        fb.addWidget(C.boton_borde("👁  Ver original", self._ver_original))
        fb.addWidget(C.boton_borde("🖨  Imprimir", self._imprimir))
        fb.addStretch(1)
        rc.agregar_fila(fb)
        lay.addWidget(rc)
        return izq

    def _columna_derecha(self):
        der = QWidget()
        lay = C.margenes(QVBoxLayout(der), esp=8)

        # --- digitar gasto / factura ---
        gf = C.Tarjeta("Digitar gasto / factura")
        self.ent = {}
        self.ent["fecha"] = C.CampoFecha(ancho=130)
        self.ent["numero_comprobante"] = C.campo("", ancho=130, mayusculas=True)
        self.ent["tipo"] = C.combo(["FACTURA", "NOTA VENTA", "COMP. RETENCIÓN", "OTRO"],
                                   "FACTURA", ancho=140)
        self.ent["ruc"] = C.campo("", ancho=120)
        self.ent["proveedor"] = C.campo("", ancho=180, mayusculas=True)
        self.ent["lugar"] = C.campo("", ancho=150, mayusculas=True)
        self.cb_concepto = C.combo(CONCEPTOS, "ALIMENTACIÓN", ancho=190,
                                   cb=lambda _t: self._total_gasto())
        self.txt_valor = C.campo("0", ancho=110, cb=lambda _t: self._total_gasto())
        # El valor ya se ve en «Valor de la factura $»: no se repite en otra casilla.
        self.lbl_total_g = C.etiqueta("$0.00")
        self.txt_explica = C.campo("", placeholder="Explique brevemente en qué se gastó")
        gf.agregar(C.rejilla([
            [("Fecha:", self.ent["fecha"]),
             ("N° comprobante:", self.ent["numero_comprobante"])],
            [("Tipo:", self.ent["tipo"]), ("RUC:", self.ent["ruc"])],
            [("Proveedor:", self.ent["proveedor"]), ("Lugar:", self.ent["lugar"])],
            [("Concepto:", self.cb_concepto), ("Valor de la factura $:", self.txt_valor)],
        ], esp=6))
        # La explicación va en su propia fila y ocupa todo el ancho: así el formulario
        # llena la tarjeta (antes quedaba medio vacío a la derecha).
        fila_exp = C.margenes(QHBoxLayout(), esp=8)
        fila_exp.addWidget(C.etiqueta("Explicación:", clave=True))
        fila_exp.addWidget(self.txt_explica, 1)
        gf.agregar_fila(fila_exp)
        fg = C.margenes(QHBoxLayout(), esp=6)
        fg.addWidget(C.boton_secundario("🆕  Nuevo", self._limpiar_gasto))
        self.btn_gasto = C.boton_amarillo("💾  Guardar gasto", self._guardar_gasto)
        fg.addWidget(self.btn_gasto)
        fg.addWidget(C.boton_secundario("🗑  Eliminar", self._eliminar_gasto))
        fg.addStretch(1)
        gf.agregar_fila(fg)
        lay.addWidget(gf)

        # --- detalle de gastos ---
        self.tabla_g = C.Tabla(COLS_G, ordenar=False, alto_filas=22)
        self.tabla_g.setMinimumHeight(T.px(108, 84))
        self.tabla_g.agregar_manejadores(al_seleccionar=self._sel_gasto)
        dg = C.Tarjeta("Detalle de gastos")
        dg.agregar(self.tabla_g, 1)
        lay.addWidget(dg, 1)

        # --- facturas ---
        fa = C.Tarjeta("Facturas / archivos del viático")
        fb = C.margenes(QHBoxLayout(), esp=6)
        fb.addWidget(C.boton_secundario("📎  Subir archivos…", self._adjuntar))
        fb.addWidget(C.boton_secundario("🗑  Quitar", self._quitar_adjunto))
        fb.addWidget(C.boton_secundario("👁  Abrir", self._abrir_adjunto))
        fb.addStretch(1)
        fa.agregar_fila(fb)
        self.lst_fac = QListWidget()
        self.lst_fac.setMinimumHeight(T.px(58, 44))
        self.lst_fac.setMaximumHeight(T.px(92, 70))
        fa.agregar(self.lst_fac)
        lay.addWidget(fa)
        return der

    # ---------- datos generales ----------
    def seleccionar(self, numero):
        """Selecciona y precarga un viático por su número."""
        if self.tabla_v.seleccionar_donde("crudo", str(numero)) >= 0:
            self._cargar_viatico()

    def _elaborado_por_defecto(self):
        """Firma por defecto el usuario que inició sesión (justificación)."""
        return ((self.usuario or {}).get("nombre")
                or (self.usuario or {}).get("usuario") or "PAOLA NARANJO")

    def _bitacora(self, accion, detalle="", referencia=None):
        """Registra la acción en el informe de actividad del superusuario."""
        db.registrar_bitacora(self.usuario, accion, "justificación",
                              referencia if referencia is not None
                              else "N° %s" % db.etiqueta_numero(self.numero),
                              detalle)

    # ---------- lista de viáticos ----------
    def _cargar_lista(self, automatico=False):
        """Llena la lista de viáticos.

        `automatico=True` es para el refresco de fondo: si la lista quedó igual, no
        la redibuja (no parpadea ni se pierde lo que la persona tenía elegido).
        """
        texto = (self.txt_buscar.text() or "").strip().upper()
        estado = self.cb_estado.currentText()
        try:
            resumen = db.resumen_viaticos()
        except Exception as ex:
            if not automatico:
                C.error(self, "Actualizar lista",
                        "No se pudo leer la base de datos:\n\n%s" % ex)
            return
        filas = []
        for r in resumen:
            if estado != "TODOS" and r["estado"] != estado:
                continue
            if texto and not (texto in str(r["viatico_numero"])
                              or texto in str(db.numero_visible(r["viatico_numero"]))
                              or texto in (r["empleados"] or "").upper()
                              or texto in (r["lugares"] or "").upper()
                              or texto in (r["responsable"] or "").upper()):
                continue
            filas.append({"crudo": str(r["viatico_numero"]),
                          "numero": db.numero_visible(r["viatico_numero"]),
                          "salida": fmt_f(r["fecha_salida"]),
                          "regreso": fmt_f(r["fecha_regreso"]),
                          "responsable": (r["responsable"] or "")[:20],
                          "empleados": (r["empleados"] or "")[:30],
                          "total": fmt(r["total"]),
                          "estado": r["estado"]})
        firma = tuple((f["crudo"], f["estado"], f["empleados"], f["total"]) for f in filas)
        if automatico and firma == self._lista_firma:
            return
        self._lista_firma = firma
        self.tabla_v.poner(filas)
        if self.numero:
            self.tabla_v.seleccionar_donde("crudo", str(self.numero))

    def _limpiar_panel(self):
        """Vuelve al estado inicial: lista lista para elegir otro viático."""
        self.numero = None
        self.gasto_sel = None
        self.tabla_v.clearSelection()
        for lbl in self.dato.values():
            lbl.setText("—")
        for caja in (self.txt_r1, self.txt_r2, self.txt_r3, self.txt_dev_obs,
                     self.txt_nota):
            caja.clear()
        self.txt_elab.setText(self._elaborado_por_defecto())
        self.txt_dev.setText("0")
        self.txt_pago.setText("0")
        self.lbl_ent.setText("Entregado: —")
        self.lbl_resp.setText("Respaldado: —")
        self.lbl_saldo.setText("Saldo: —")
        self.lbl_est.setText("")
        self.tabla_g.limpiar()
        self.lst_fac.clear()
        self._limpiar_gasto()

    def _cargar_viatico(self):
        fila = self.tabla_v.seleccion()
        if not fila:
            return
        try:
            numero = int(str(fila.get("crudo")))
        except (TypeError, ValueError):
            return
        if numero == self.numero:
            return
        self.numero = numero
        self._refrescar()

    # ---------- datos del viático elegido ----------
    def _refrescar(self):
        filas = db.filas_numero(self.numero)
        if not filas:
            return
        r0 = filas[0]
        rf = filas[-1]
        entregado = sum(float(f.get("valor_cajero") or 0) for f in filas)
        gastos = db.listar_gastos(self.numero)
        resp = db.totales_gastos(self.numero)
        total_g = resp["total"]
        dev_monto = float(r0.get("devolucion_monto") or 0)
        pago_emp = float(r0.get("pago_empleado_monto") or 0)
        saldo = entregado - total_g
        emps = sorted({f["nombre_empleado"] for f in filas})
        chofer = next((f["nombre_empleado"] for f in filas if f.get("es_chofer")), "—")
        encargado = next((f["nombre_empleado"] for f in filas if f.get("es_encargado")), "—")
        ajus = sorted({int(f.get("ajuste_numero") or 0) for f in filas
                       if int(f.get("ajuste_numero") or 0) > 0})

        self.dato["Beneficiario (encargado):"].setText(encargado)
        self.dato["Creado por:"].setText(str(r0["responsable"]))
        self.dato["Proyecto / cliente:"].setText(str(r0["cliente_proyecto"]))
        self.dato["Viaja a:"].setText(str(r0["lugar_trabajo"]))
        self.dato["Vehículo:"].setText(str(r0["placa"] or "—"))
        self.dato["Maneja (chofer):"].setText(chofer)
        self.dato["ajustes_lbl"].setText(
            ", ".join("N° %s" % a for a in ajus) if ajus else "ninguno")
        self.dato["salida_lbl"].setText(
            "%s %s" % (fmt_f(r0["fecha_salida"]), r0["hora_salida"]))
        self.dato["llegada_lbl"].setText(
            "%s %s" % (fmt_f(r0["fecha_llegada_trabajo"]), r0["hora_llegada_trabajo"]))
        self.dato["saltr_lbl"].setText(
            "%s %s" % (fmt_f(r0["fecha_salida_trabajo"]), r0["hora_salida_trabajo"]))
        self.dato["regreso_lbl"].setText(
            "%s %s" % (fmt_f(rf["fecha_regreso"]), rf["hora_regreso"]))
        self.dato["estado_lbl"].setText(str(r0["estado"]))
        self.dato["personas_lbl"].setText(", ".join(emps))

        self.txt_r1.setText(str(r0.get("recibo_viatico") or ""))
        self.txt_r2.setText(str(r0.get("recibo_viatico_2") or ""))
        self.txt_r3.setText(str(r0.get("recibo_viatico_3") or ""))
        self.lbl_ent.setText("Entregado: %s" % fmt(entregado))
        self.lbl_resp.setText("Respaldado: %s" % fmt(total_g))
        self.lbl_saldo.setText("Saldo (entregado − respaldado): %s" % fmt(saldo))
        self.txt_dev.setText("%.2f" % dev_monto)
        self.txt_pago.setText("%.2f" % pago_emp)
        if dev_monto == 0 and pago_emp == 0:
            # sugerencia automática según el saldo
            if saldo > 0:
                self.txt_dev.setText("%.2f" % saldo)
            elif saldo < 0:
                self.txt_pago.setText("%.2f" % -saldo)
        self.txt_dev_obs.setText(str(r0.get("devolucion_observacion") or ""))
        self.txt_nota.setText(str(r0.get("nota_justificacion") or ""))
        self.txt_elab.setText(str(r0.get("elaborado_por") or self._elaborado_por_defecto()))
        self.lbl_est.setText("N° %s · %s" % (db.etiqueta_numero(self.numero), r0["estado"]))

        por_gasto = {}
        for r in db.listar_respaldos(self.numero):
            if r.get("gasto_id"):
                por_gasto.setdefault(r["gasto_id"], []).append(r["nombre_archivo"])
        self.tabla_g.poner(self._filas_gastos(gastos, resp, total_g, por_gasto))
        self._limpiar_gasto()
        self._cargar_adjuntos()

    def _filas_gastos(self, gastos, resp, total_g, por_gasto):
        """Filas de la tabla de gastos (+ la fila TOTAL, como en el Excel)."""
        filas = [{"id": g["id"], "fecha": fmt_f(g["fecha"]),
                  "comprobante": g["numero_comprobante"], "tipo": g["tipo"],
                  "ruc": g["ruc"], "proveedor": g["proveedor"], "lugar": g["lugar"],
                  "hospedaje": fmt(g["hospedaje"]), "combustible": fmt(g["combustible"]),
                  "buses": fmt(g["buses"]), "taxis": fmt(g["taxis"]),
                  "alimentacion": fmt(g["alimentacion"]), "peaje": fmt(g["peaje"]),
                  "otros": fmt(g["otros"]), "total": fmt(g["total"]),
                  "nota": g.get("nota") or "",
                  "archivos": ", ".join(por_gasto.get(g["id"], []))} for g in gastos]
        filas.append({"id": "", "fecha": "TOTAL", "comprobante": "", "tipo": "", "ruc": "",
                      "proveedor": "", "lugar": "",
                      "hospedaje": fmt(resp["hospedaje"]),
                      "combustible": fmt(resp["combustible"]),
                      "buses": fmt(resp["buses"]), "taxis": fmt(resp["taxis"]),
                      "alimentacion": fmt(resp["alimentacion"]),
                      "peaje": fmt(resp["peaje"]), "otros": fmt(resp["otros"]),
                      "total": fmt(total_g), "nota": "", "archivos": ""})
        return filas

    # ---------- gastos ----------
    def _sel_gasto(self, fila):
        """Carga en el formulario el gasto marcado en la lista para modificarlo."""
        if not fila or not str(fila.get("id") or "").isdigit():
            return
        gasto_id = int(fila["id"])
        gasto = next((x for x in db.listar_gastos(self.numero) if x["id"] == gasto_id), None)
        if not gasto:
            return
        self.gasto_sel = gasto_id
        self.ent["fecha"].set_valor(gasto["fecha"])
        for clave in ("numero_comprobante", "tipo", "ruc", "proveedor", "lugar"):
            if clave == "tipo":
                C.poner_combo(self.ent["tipo"], gasto[clave] or "FACTURA")
            else:
                self.ent[clave].setText(str(gasto[clave] or ""))
        concepto = next((CAMPO_A_CONCEPTO[k] for k in CAMPO_CONCEPTO.values()
                         if float(gasto.get(k) or 0) > 0), "ALIMENTACIÓN")
        C.poner_combo(self.cb_concepto, concepto)
        campo = CAMPO_CONCEPTO[concepto]
        self.txt_valor.setText("%.2f" % float(gasto.get(campo) or 0))
        self.txt_explica.setText(str(gasto.get("nota") or ""))
        self._total_gasto()
        self._marcar_editando()
        self._cargar_adjuntos()

    def _marcar_editando(self):
        """Avisa (en el botón) que se está modificando un gasto ya guardado.

        Basta con tocar la fila del gasto en la lista: se cargan sus datos y el botón
        pasa a «💾 Guardar cambios», para que quede claro que se modifica y no se crea
        otro. Al guardar vuelve a «💾 Guardar gasto».
        """
        self.btn_gasto.setText("💾  Guardar cambios")

    def _total_gasto(self):
        try:
            total = float((self.txt_valor.text() or "0").strip())
        except ValueError:
            total = 0.0
        self.lbl_total_g.setText("$%.2f" % total)

    def _datos_gasto(self):
        """Lo que se guarda del gasto (con el valor en el concepto elegido)."""
        d = {"fecha": self.ent["fecha"].valor(),
             "numero_comprobante": (self.ent["numero_comprobante"].text() or "").strip(),
             "tipo": self.ent["tipo"].currentText().strip(),
             "ruc": (self.ent["ruc"].text() or "").strip(),
             "proveedor": (self.ent["proveedor"].text() or "").strip().upper(),
             "lugar": (self.ent["lugar"].text() or "").strip().upper()}
        try:
            valor = float((self.txt_valor.text() or "0").strip())
        except ValueError:
            C.error(self, "Gasto", "El valor de la factura debe ser numérico.")
            return None
        for k in CAMPO_CONCEPTO.values():
            d[k] = 0.0
        d[CAMPO_CONCEPTO[self.cb_concepto.currentText()]] = valor
        d["total"] = round(valor, 2)
        d["nota"] = (self.txt_explica.text() or "").strip()
        return d

    def _guardar_gasto(self):
        if not self.numero:
            C.aviso(self, "Gasto", "Seleccione un viático primero.")
            return
        d = self._datos_gasto()
        if d is None:
            return
        concepto = self.cb_concepto.currentText()
        detalle = "%s $%.2f · comprobante %s" % (concepto, d["total"],
                                                d["numero_comprobante"] or "-")
        if d.get("nota"):
            detalle += " · " + d["nota"]
        if self.gasto_sel:
            db.actualizar_gasto(self.gasto_sel, d)
            self._bitacora("CAMBIÓ GASTO", detalle)
        else:
            self.gasto_sel = db.guardar_gasto(self.numero, d)
            self._bitacora("REGISTRÓ GASTO", detalle)
        self._refrescar()                 # recarga la lista de gastos del viático
        self._limpiar_gasto()             # deja el formulario listo para el siguiente

    def _eliminar_gasto(self):
        if self.gasto_sel and C.confirmar(
                self, "Eliminar", "¿Eliminar el gasto seleccionado y sus adjuntos?"):
            db.eliminar_gasto(self.gasto_sel)
            self._bitacora("ELIMINÓ GASTO", "Gasto %s y sus adjuntos" % self.gasto_sel)
            self._refrescar()

    def _limpiar_gasto(self):
        """Deja el formulario en blanco (gasto nuevo)."""
        self.gasto_sel = None
        self.ent["fecha"].hoy()
        for clave, caja in self.ent.items():
            if clave in ("fecha", "tipo"):
                continue
            caja.clear()
        C.poner_combo(self.ent["tipo"], "FACTURA")
        C.poner_combo(self.cb_concepto, "ALIMENTACIÓN")
        self.txt_valor.setText("0")
        self.txt_explica.clear()
        self.btn_gasto.setText("💾  Guardar gasto")
        self._total_gasto()

    # ---------- facturas del viático ----------
    def _adjuntos_viatico(self):
        return db.listar_respaldos(self.numero) if self.numero else []

    def _cargar_adjuntos(self):
        """Muestra en la lista las facturas del viático (y de qué gasto son)."""
        self.lst_fac.clear()
        for r in self._adjuntos_viatico():
            nombre = r.get("nombre_archivo") or "archivo"
            gasto = r.get("gasto_id") or ""
            self.lst_fac.addItem("%s   [gasto %s]" % (nombre, gasto) if gasto else nombre)

    def _adjuntar(self):
        if not self.numero:
            C.aviso(self, "Adjuntar", "Seleccione un viático primero.")
            return
        rutas, _filtro = QFileDialog.getOpenFileNames(
            self, "Seleccione una o varias facturas (PDF o imágenes)", "",
            "Facturas (*.pdf *.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff);;Todos (*.*)")
        if not rutas:
            return
        concepto = (self.ent["proveedor"].text() or "").strip().upper() or (
            "GASTO %s" % self.gasto_sel if self.gasto_sel else "VIÁTICO")
        errores = 0
        for ruta in rutas:
            try:
                db.agregar_respaldo(self.numero, ruta,
                                    empleado=(self.usuario or {}).get("nombre") or "SISTEMA",
                                    concepto=concepto, gasto_id=self.gasto_sel)
            except Exception as ex:
                errores += 1
                print("Error adjuntando %s: %s" % (ruta, ex))
        if errores:
            C.error(self, "Adjuntar", "No se pudieron adjuntar %d archivo(s)." % errores)
        self._bitacora("SUBIO FACTURA(S)",
                       "%d archivo(s) · concepto %s" % (len(rutas) - errores, concepto))
        self._refrescar()

    def _quitar_adjunto(self):
        adj = self._adjuntos_viatico()
        i = self.lst_fac.currentRow()
        if 0 <= i < len(adj):
            db.eliminar_respaldo(adj[i]["id"])
            self._bitacora("QUITÓ FACTURA",
                           "Archivo %s" % (adj[i].get("nombre_archivo") or ""))
            self._refrescar()

    def _abrir_adjunto(self):
        adj = self._adjuntos_viatico()
        i = self.lst_fac.currentRow()
        if not 0 <= i < len(adj):
            return
        ruta = db.ruta_para_abrir(adj[i])
        if not ruta:
            C.aviso(self, "Facturas", "No se pudo obtener el archivo del respaldo.")
            return
        if os.name == "nt":
            os.startfile(ruta)
        else:
            subprocess.Popen(["xdg-open", ruta])

    # ---------- cierre ----------
    def _guardar_recibos(self):
        if not self.numero:
            return
        r1 = (self.txt_r1.text() or "").strip()
        r2 = (self.txt_r2.text() or "").strip()
        r3 = (self.txt_r3.text() or "").strip()
        db.actualizar_recibos(self.numero, r1, r2, r3)
        self._bitacora("CAMBIÓ RECIBOS", "Recibos: %s / %s / %s"
                       % (r1 or "-", r2 or "-", r3 or "-"))
        C.informar(self, "Recibos", "Números de recibo guardados.")

    def _guardar_cierre(self):
        """Guarda devolución, compensación, nota de cierre y firma."""
        try:
            monto = float((self.txt_dev.text() or "0").strip())
        except ValueError:
            monto = 0.0
        try:
            pago = float((self.txt_pago.text() or "0").strip())
        except ValueError:
            pago = 0.0
        db.guardar_devolucion(self.numero, monto, (self.txt_dev_obs.text() or "").strip())
        db.guardar_pago_empleado(self.numero, pago)
        db.guardar_nota_cierre(self.numero, (self.txt_nota.text() or "").strip())
        db.guardar_elaborado_por(
            self.numero, (self.txt_elab.text() or "").strip() or self._elaborado_por_defecto())

    # ---------- exportar a Excel la lista de viáticos que se está viendo ----------
    def exportar_excel_lista(self):
        """Excel de la lista de viáticos que se ve (respeta el buscador y el estado)."""
        filas = self.tabla_v.datos
        if not filas:
            C.aviso(self, "Exportar", "La lista está vacía: no hay viáticos que exportar.")
            return None
        ruta = C.pedir_ruta_guardar(self, "viaticos.xlsx")
        if not ruta:
            return None
        try:
            C.exportar_excel(ruta, COLS_V, filas, "Viáticos")
        except Exception as ex:
            C.error(self, "Exportar a Excel", str(ex))
            return None
        C.informar(self, "Exportar a Excel",
                   "Se guardó el archivo:\n%s\n\n%d viático(s)." % (ruta, len(filas)))
        return ruta

    # ---------- exportar a Excel la justificación (igual que se imprime) ----------
    @staticmethod
    def _monto(caja):
        """Valor escrito en una caja de dinero (0 si no es un número)."""
        try:
            return float((caja.text() or "0").strip())
        except ValueError:
            return 0.0

    def exportar_excel_justificacion(self):
        """Excel de la justificación: cabecera, detalle de gastos y TOTAL."""
        if not self.numero:
            C.aviso(self, "Exportar", "Seleccione un viático primero.")
            return None
        filas = self.tabla_g.datos
        if not filas:
            C.aviso(self, "Exportar", "Este viático todavía no tiene gastos.")
            return None
        datos_viaje = db.filas_numero(self.numero)
        r0 = datos_viaje[0] if datos_viaje else {}
        entregado = sum(float(f.get("valor_cajero") or 0) for f in datos_viaje)
        respaldado = db.totales_gastos(self.numero)["total"]
        recibos = " / ".join([x for x in (self.txt_r1.text(), self.txt_r2.text(),
                                          self.txt_r3.text()) if (x or "").strip()]) or "—"
        cabecera = [
            ("Viático N°", db.etiqueta_numero(self.numero)),
            ("Estado", r0.get("estado") or "—"),
            ("Creado por", r0.get("responsable") or "—"),
            ("Cliente y proyecto", r0.get("cliente_proyecto") or "—"),
            ("Lugar de trabajo", r0.get("lugar_trabajo") or "—"),
            ("Salida / regreso", "%s → %s" % (fmt_f(r0.get("fecha_salida")),
                                              fmt_f(r0.get("fecha_regreso")))),
            ("Recibos", recibos),
            ("Entregado", fmt(entregado)),
            ("Respaldado", fmt(respaldado)),
            ("Saldo (entregado − respaldado)", fmt(entregado - respaldado)),
            ("Devuelve a Miempresa", fmt(self._monto(self.txt_dev))),
            ("A favor del empleado", fmt(self._monto(self.txt_pago))),
            ("Motivo", (self.txt_dev_obs.text() or "").strip() or "—"),
            ("Nota de cierre", (self.txt_nota.text() or "").strip() or "—"),
            ("Elaborado por", (self.txt_elab.text() or "").strip()
             or self._elaborado_por_defecto()),
        ]
        bloques = [("titulo", "JUSTIFICACIÓN DEL VIÁTICO N° %s"
                    % db.etiqueta_numero(self.numero)),
                   ("datos", cabecera),
                   ("salto",),
                   ("tabla", COLS_G, filas[:-1]),          # los gastos, sin el TOTAL
                   ("totales", COLS_G, filas[-1:])]        # la fila TOTAL
        nombre = "justificacion_%s.xlsx" % db.etiqueta_numero(self.numero)
        ruta = C.pedir_ruta_guardar(self, nombre)
        if not ruta:
            return None
        try:
            C.exportar_excel_documento(ruta, bloques,
                                       "Justificación %s" % db.etiqueta_numero(self.numero))
        except Exception as ex:
            C.error(self, "Exportar a Excel", str(ex))
            return None
        C.informar(self, "Exportar a Excel",
                   "Se guardó el archivo:\n%s\n\nViático N° %s · %d gasto(s)."
                   % (ruta, db.etiqueta_numero(self.numero), len(filas) - 1))
        return ruta

    # ---------- justificar / devolver / imprimir ----------
    def _justificar(self):
        if not self.numero:
            return
        if not db.listar_gastos(self.numero):
            if not C.confirmar(self, "Justificar",
                               "No hay gastos registrados. ¿Justificar de todos modos?"):
                return
        n = self.numero
        db.actualizar_recibos(n, (self.txt_r1.text() or "").strip(),
                              (self.txt_r2.text() or "").strip(),
                              (self.txt_r3.text() or "").strip())
        self._guardar_cierre()
        db.justificar(n, (self.usuario or {}).get("nombre") or "SISTEMA",
                      (self.txt_nota.text() or "").strip())
        respaldado = sum(float(g.get("total") or 0) for g in db.listar_gastos(n))
        self._bitacora("JUSTIFICÓ VIÁTICO",
                       "Justificado por %s · respaldado $%.2f"
                       % ((self.usuario or {}).get("nombre") or "SISTEMA", respaldado),
                       referencia="N° %s" % db.etiqueta_numero(n))
        try:
            db.consolidar_respaldos_pdf(n)
        except Exception:
            pass
        self._cargar_lista()
        self._limpiar_panel()
        C.informar(self, "Justificado",
                   "Viático N° %s JUSTIFICADO. Elija otro viático de la lista."
                   % db.etiqueta_numero(n))

    def _reactivar(self):
        if not self.numero:
            return
        db.reactivar_viaje(self.numero)
        self._bitacora("REACTIVÓ VIÁTICO", "Devuelto a PENDIENTE para corregir")
        self._cargar_lista()
        self._refrescar()

    def _imprimir(self):
        if not self.numero:
            C.aviso(self, "Imprimir", "Seleccione un viático.")
            return
        filas = db.filas_numero(self.numero)
        r0 = filas[0]
        cab = {"responsable": r0["responsable"], "cliente_proyecto": r0["cliente_proyecto"],
               "recibo_viatico": (self.txt_r1.text() or "").strip()
                                 or r0.get("recibo_viatico") or "",
               "recibo_viatico_2": (self.txt_r2.text() or "").strip()
                                   or r0.get("recibo_viatico_2") or "",
               "recibo_viatico_3": (self.txt_r3.text() or "").strip()
                                   or r0.get("recibo_viatico_3") or ""}
        devolucion = {"monto": float(r0.get("devolucion_monto") or 0),
                      "observacion": r0.get("devolucion_observacion") or "",
                      "pago_empleado": float(r0.get("pago_empleado_monto") or 0),
                      "elaborado_por": (self.txt_elab.text() or "").strip()
                                       or r0.get("elaborado_por") or "PAOLA NARANJO"}
        reportes.imprimir_justificacion(self.numero, cab, filas,
                                        db.listar_gastos(self.numero),
                                        db.listar_respaldos(self.numero), devolucion)

    def _ver_original(self):
        """Abre una ventana de solo lectura con el viático original y sus ajustes."""
        if not self.numero:
            C.aviso(self, "Viático original", "Seleccione un viático de la lista.")
            return
        try:
            VentanaOriginal(self, self.numero).exec()
        except Exception as ex:
            C.error(self, "Viático original",
                    "No se pudo mostrar el viático:\n\n%s" % ex)


class VentanaOriginal(C.Ventana):
    """Vista de solo lectura del viático original con sus ajustes."""

    def __init__(self, padre, numero):
        super().__init__(
            titulo="Viático N° %s — ORIGINAL y ajustes" % db.etiqueta_numero(numero),
            padre=padre, ancho=1420, alto=800, empezar_maximizada=True)
        self.agregar(self._card_datos(numero))
        self.agregar(self._card_detalle(numero), 1)
        self.boton_volver.setText("←  Cerrar")

    def _card_datos(self, numero):
        """Datos completos del viático original (solo lectura)."""
        filas = db.filas_numero(numero)
        r0 = filas[0] if filas else {}
        recibos = " / ".join([x for x in (r0.get("recibo_viatico"), r0.get("recibo_viatico_2"),
                                          r0.get("recibo_viatico_3")) if x]) or "—"
        datos = [
            ("N° viático:", str(numero)),
            ("Estado:", r0.get("estado") or "—"),
            ("Creado por:", r0.get("responsable") or "—"),
            ("Encargado:", next((f["nombre_empleado"] for f in filas if f.get("es_encargado")), "—")),
            ("Chofer:", next((f["nombre_empleado"] for f in filas if f.get("es_chofer")), "—")),
            ("Cliente / proyecto:", r0.get("cliente_proyecto") or "—"),
            ("Lugar de trabajo:", r0.get("lugar_trabajo") or "—"),
            ("Provincia / cantón:", "%s / %s" % (r0.get("provincia") or "—",
                                                r0.get("canton") or "—")),
            ("Vehículo:", r0.get("placa") or "—"),
            ("Orden combustible 1:", r0.get("orden_combustible") or "—"),
            ("Orden combustible 2:", r0.get("orden_combustible_2") or "—"),
            ("Efectivo combustible:", fmt(r0.get("efectivo_combustible"))),
            ("Km recorridos:", r0.get("km_recorridos") or 0),
            ("Parqueadero / peaje:", fmt(r0.get("parqueadero_peaje"))),
            ("Recibos:", recibos),
            ("Salida Miempresa:", "%s %s" % (fmt_f(r0.get("fecha_salida")),
                                              r0.get("hora_salida") or "")),
            ("Llegada Miempresa:", "%s %s" % (fmt_f(r0.get("fecha_regreso")),
                                               r0.get("hora_regreso") or "")),
            ("Llegada al trabajo:", "%s %s" % (fmt_f(r0.get("fecha_llegada_trabajo")),
                                               r0.get("hora_llegada_trabajo") or "")),
            ("Salida del trabajo:", "%s %s" % (fmt_f(r0.get("fecha_salida_trabajo")),
                                               r0.get("hora_salida_trabajo") or "")),
            ("Observaciones:", r0.get("observaciones") or "—"),
            ("Justificado por:", r0.get("justificado_por") or "—"),
            ("Nota de cierre:", r0.get("nota_justificacion") or "—"),
        ]
        card = C.Tarjeta("Datos del viático original")
        g = QGridLayout()
        C.margenes(g, esp=4)
        for i, (etq, valor) in enumerate(datos):
            g.addWidget(C.etiqueta(etq, clave=True), i // 3, (i % 3) * 2)
            lbl = C.etiqueta(str(valor))
            lbl.setWordWrap(True)
            g.addWidget(lbl, i // 3, (i % 3) * 2 + 1)
        card.agregar_fila(g)
        return card

    def _card_detalle(self, numero):
        """Detalle calculado: un bloque por el original y por cada ajuste."""
        card = C.Tarjeta("Detalle calculado — original y ajustes",
                         "Primero el original; después cada ajuste con sus totales")
        try:
            from q_viaje import COLS_DETALLE, sep_vals, vals_fila, vals_totales
        except Exception as ex:
            card.agregar(C.etiqueta("No se pudo cargar el detalle del viático (%s)." % ex,
                                    ayuda=True))
            return card
        tabla = C.Tabla(COLS_DETALLE, ordenar=False, estirar_ultima=False)
        tabla.setMinimumHeight(T.px(320, 200))
        grupos = {}
        for fila in db.filas_numero(numero):
            grupos.setdefault(int(fila.get("ajuste_numero") or 0), []).append(fila)
        salida = []
        for ajuste in sorted(grupos):
            salida.append(sep_vals("═ ORIGINAL ═" if ajuste == 0
                                   else "═ AJUSTE N° %s · NUEVO ═" % ajuste))
            for i, fila in enumerate(grupos[ajuste], start=1):
                salida.append(vals_fila(i, fila))
            salida.append(vals_totales(grupos[ajuste]))
        tabla.poner(salida)
        card.agregar(tabla, 1)
        return card

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
