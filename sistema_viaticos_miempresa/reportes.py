# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""reportes.py — Impresión HTML/PDF de viáticos (originales, ajustes, general) y justificaciones."""
import webbrowser
import tempfile
from pathlib import Path

import colores as tema
import database as db

HEADERS_VIATICO = [
    ("n", "N°", 30), ("empleado", "EMPLEADO", 155), ("lugar", "LUGAR", 100),
    ("f_sal", "F.SALIDA", 70), ("h_sal", "H.SAL", 42), ("f_reg", "F.REGRESO", 70),
    ("h_reg", "H.REG", 42), ("f_lt", "F.LLEG.TRAB", 70), ("h_lt", "H.LLEG", 42),
    ("f_st", "F.SAL.TRAB", 70), ("h_st", "H.SAL.TRAB", 42), ("dias", "DÍAS", 26),
    ("km", "KM", 34), ("des", "DESAY.", 45), ("alm", "ALMUER.", 45), ("mer", "MERIEN.", 45),
    ("txs", "TAXI S.", 40), ("txr", "TAXI R.", 40), ("hos", "HOSP.", 45), ("agua", "AGUA", 35),
    ("comb", "COMBUST.", 50), ("tra", "TRANSP./OTROS", 55), ("peaje", "PARQ./PEAJE", 45),
    ("total", "TOTAL", 62), ("cajero", "CAJERO", 62),
]

HEADERS_JUSTIFICACION = [
    ("fecha", "FECHA", 70), ("comprobante", "NRO COMPROBANTE", 105), ("tipo", "TIPO", 55),
    ("ruc", "RUC", 75), ("proveedor", "PROVEEDOR", 125), ("lugar", "LUGAR", 85),
    ("hospedaje", "HOSPEDAJE", 62), ("combustible", "COMBUSTIBLE/ORDEN", 80),
    ("buses", "BUSES", 55), ("taxis", "TAXIS O CAMIONETAS", 85), ("alimentacion", "ALIMENTACIÓN", 72),
    ("peaje", "PEAJE", 55), ("otros", "OTROS", 55), ("total", "TOTAL", 70),
    ("explicacion", "EXPLICACIÓN", 130),
]



def _num_txt(numero):
    """Número de viático como se muestra al usuario: «001/2026»."""
    try:
        return db.etiqueta_numero(numero)
    except Exception:
        return str(numero)


def fmt(v):
    v = float(v or 0)
    return "-" if abs(v) < 0.005 else f"{v:.2f}"


def fmt_f(iso):
    if not iso:
        return ""
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except Exception:
        return iso


def _base_css():
    azul, amarillo = tema.AZUL, tema.AMARILLO
    return f"""
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #1a1a2e; margin: 18px; }}
        h1 {{ font-size: 17px; color: {azul}; margin: 0 0 2px; letter-spacing: .5px; }}
        h2 {{ font-size: 13px; margin: 14px 0 6px; color: {azul}; border-left: 5px solid {amarillo};
              padding-left: 8px; }}
        .empresa {{ font-size: 11px; color: #555; margin-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 6px; page-break-inside: avoid; }}
        th {{ background: {azul}; color: #fff; border: 1px solid {azul}; padding: 4px 3px; font-size: 9px; }}
        td {{ border: 1px solid #b9c2d8; padding: 3px 4px; font-size: 10px; }}
        .r {{ text-align: right; }} .c {{ text-align: center; }}
        tr.tot td {{ background: {amarillo}; font-weight: bold; border-color: #c8a700; }}
        tr.ajuste-title td {{ background: #eef; font-weight: bold; color: {azul}; }}
        .meta {{ width: 100%; margin-top: 6px; }}
        .meta td {{ border: 1px solid #b9c2d8; }}
        .meta .lbl {{ background: #eef1f8; font-weight: bold; width: 13%; }}
        .firmas {{ margin-top: 26px; width: 100%; }}
        .firmas td {{ border: none; text-align: center; padding-top: 34px; font-size: 10px; }}
        .linea {{ border-top: 1px solid #333; width: 80%; margin: 0 auto 4px; }}
        .recibos {{ margin-top: 10px; font-size: 10px; }}
        .recibos span {{ display: inline-block; border: 1px solid #888; padding: 3px 10px; margin-right: 8px;
                          min-width: 90px; }}
        .recibos b {{ color: {azul}; }}
        @media print {{ body {{ margin: 8mm; }} h2 {{ page-break-after: avoid; }} }}
    """


def _head(titulo):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>{titulo}</title><style>{_base_css()}</style></head><body>"""


def _abrir(html, nombre="reporte"):
    tmp = Path(tempfile.gettempdir()) / f"{nombre}_{abs(hash(html))}.html"
    tmp.write_text(html, encoding="utf-8")
    webbrowser.open(f"file://{tmp}")
    return tmp


def _cabecera_viatico(num, cab, titulo_seccion, filas):
    r0 = filas[0] if filas else {}
    choferes = sorted({f["nombre_empleado"] for f in filas if f.get("es_chofer")})
    chofer = choferes[0] if choferes else (r0.get("nombre_empleado", "") if r0.get("es_encargado") else "")
    encargado = next((f["nombre_empleado"] for f in filas if f.get("es_encargado")), chofer)
    vehiculo = db.buscar_vehiculo_por_placa(cab.get("placa", "")) or {}
    tipo_veh = vehiculo.get("tipo", "") if vehiculo else ""
    chofer_veh = vehiculo.get("chofer", "") if vehiculo else ""
    salida_pub = ("%s %s" % (fmt_f(r0.get('fecha_salida')), r0.get('hora_salida', ''))).strip()
    llegada_pub = ("%s %s" % (fmt_f(r0.get('fecha_regreso')), r0.get('hora_regreso', ''))).strip()
    llegada_trab = ("%s %s" % (fmt_f(r0.get('fecha_llegada_trabajo')),
                               r0.get('hora_llegada_trabajo', ''))).strip()
    salida_trab = ("%s %s" % (fmt_f(r0.get('fecha_salida_trabajo')),
                              r0.get('hora_salida_trabajo', ''))).strip()
    recibos = "".join(
        f"<span><b>RECIBO {i}:</b> {cab.get(k) or '—'}</span>"
        for i, k in enumerate(("recibo_viatico", "recibo_viatico_2", "recibo_viatico_3"), 1)
    )
    if cab.get("recibo_ajuste"):
        recibos += f"<span><b>RECIBO AJUSTE:</b> {cab['recibo_ajuste']}</span>"
    return f"""
    <h1>{titulo_seccion}</h1>
    <div class="empresa">MIEMPRESA S.A. — Sistema de Viáticos · Cuenca, Ecuador</div>
    <table class="meta">
      <tr><td class="lbl">N° VIÁTICO</td><td><b>{_num_txt(num)}</b></td>
          <td class="lbl">RESPONSABLE</td><td>{cab.get('responsable','')}</td>
          <td class="lbl">CLIENTE / PROYECTO</td><td colspan="3">{cab.get('cliente_proyecto','')}</td></tr>
      <tr><td class="lbl">ENCARGADO</td><td>{encargado}</td>
          <td class="lbl">CHOFER</td><td>{chofer}</td>
          <td class="lbl">ORDEN COMB.</td><td>{cab.get('orden_combustible','') or '—'} {('/ ' + cab['orden_combustible_2']) if cab.get('orden_combustible_2') else ''}</td>
          <td class="lbl">EFECTIVO COMB.</td><td>{fmt(cab.get('efectivo_combustible', 0))}</td></tr>
      <tr><td class="lbl">VEHÍCULO</td><td>{cab.get('placa','')}</td>
          <td class="lbl">TIPO</td><td>{tipo_veh}</td>
          <td class="lbl">CHOFER</td><td>{chofer_veh}</td>
          <td class="lbl">LUGAR</td><td>{r0.get('lugar_trabajo','')}</td></tr>
      <tr><td class="lbl">SALIDA DE MIEMPRESA</td><td colspan="3">{salida_pub}</td>
          <td class="lbl">LLEGADA AL TRABAJO</td><td colspan="3">{llegada_trab}</td></tr>
      <tr><td class="lbl">LLEGADA A MIEMPRESA</td><td colspan="3">{llegada_pub}</td>
          <td class="lbl">SALIDA DEL TRABAJO</td><td colspan="3">{salida_trab}</td></tr>
      <tr><td class="lbl">OBSERVACIONES</td><td colspan="7">{cab.get('observaciones','')}</td></tr>
    </table>
    <div class="recibos">{recibos}</div>
    """


def _tabla_viatico(filas):
    ths = "".join(f"<th style='text-align:{'right' if k not in ('n','empleado','lugar','f_sal','h_sal','f_reg','h_reg','f_lt','h_lt','f_st','h_st','dias') else 'center' if k != 'empleado' and k != 'lugar' else 'left'}'>{t}</th>"
                  for k, t, _ in HEADERS_VIATICO)
    def row(i, f):
        km = float(f.get("km_recorridos") or 0)
        # La columna COMBUST. lleva SOLO el valor del combustible. Antes se le
        # pegaba delante el número de orden de combustible («01 50.00») y esos
        # números sueltos parecían un error de cálculo. La orden ya sale arriba,
        # en el encabezado del viático (ORDEN COMB.).
        comb = fmt(f.get("combustible"))
        vals = [
            (i, "c"), (f["nombre_empleado"], ""), (f.get("lugar_trabajo", ""), ""),
            (fmt_f(f.get("fecha_salida")), "c"), (f.get("hora_salida", ""), "c"),
            (fmt_f(f.get("fecha_regreso")), "c"), (f.get("hora_regreso", ""), "c"),
            (fmt_f(f.get("fecha_llegada_trabajo")), "c"), (f.get("hora_llegada_trabajo", ""), "c"),
            (fmt_f(f.get("fecha_salida_trabajo")), "c"), (f.get("hora_salida_trabajo", ""), "c"),
            (f.get("dias_viaje", ""), "c"), (int(km) if km else "", "c"),
            (fmt(f.get("desayuno")), "r"), (fmt(f.get("almuerzo")), "r"),
            (fmt(f.get("merienda")), "r"), (fmt(f.get("taxi_salida")), "r"),
            (fmt(f.get("taxi_regreso")), "r"), (fmt(f.get("hospedaje")), "r"),
            (fmt(f.get("agua")), "r"), (comb, "r"), (fmt(f.get("otros")), "r"),
            (fmt(f.get("parqueadero_peaje")), "r"), (fmt(f.get("total")), "r"),
            (fmt(f.get("valor_cajero")), "r"),
        ]
        tds = "".join(f"<td class='{c}'>{v}</td>" for v, c in vals)
        return f"<tr>{tds}</tr>"

    def tot(filas_t, clase="tot"):
        t = lambda k: sum(float(x.get(k) or 0) for x in filas_t)
        # La tabla tiene 25 columnas. Las 12 primeras (N°, EMPLEADO, LUGAR, las
        # cuatro fechas con sus horas y DÍAS) van vacías menos la palabra TOTALES
        # que va en EMPLEADO; de ahí en adelante KM y cada valor. Ojo: antes había
        # una celda vacía de más y toda la fila de totales salía corrida una
        # columna hacia la derecha (por eso los totales no cuadraban con el título).
        tds = (f"<td></td><td><b>TOTALES</b></td><td></td><td></td><td></td><td></td><td></td>"
               f"<td></td><td></td><td></td><td></td><td></td>"
               f"<td>{int(t('km_recorridos'))}</td>"
               f"<td class='r'>{fmt(t('desayuno'))}</td><td class='r'>{fmt(t('almuerzo'))}</td>"
               f"<td class='r'>{fmt(t('merienda'))}</td><td class='r'>{fmt(t('taxi_salida'))}</td>"
               f"<td class='r'>{fmt(t('taxi_regreso'))}</td><td class='r'>{fmt(t('hospedaje'))}</td>"
               f"<td class='r'>{fmt(t('agua'))}</td><td class='r'>{fmt(t('combustible'))}</td>"
               f"<td class='r'>{fmt(t('otros'))}</td><td class='r'>{fmt(t('parqueadero_peaje'))}</td>"
               f"<td class='r'>{fmt(t('total'))}</td><td class='r'>{fmt(t('valor_cajero'))}</td>")
        return f"<tr class='{clase}'>{tds}</tr>"

    body = "".join(row(i, f) for i, f in enumerate(filas, 1))
    return f"<table><tr>{ths}</tr>{body}{tot(filas)}</table>"


def imprimir_viatico(numero, cab, filas, general=False):
    """filas: lista plana. Si general=True, agrupa por ajuste_numero: original + cada ajuste + total general."""
    grupos = {}
    for f in filas:
        grupos.setdefault(int(f.get("ajuste_numero") or 0), []).append(f)
    html = _head(f"Viático {_num_txt(numero)}")
    if not general or len(grupos) <= 1:
        aj = int((filas[0].get("ajuste_numero") or 0)) if filas else 0
        titulo = f"VIÁTICO N° {_num_txt(numero)}" if aj == 0 else f"AJUSTE DE VIÁTICO N° {_num_txt(numero)}-{aj}"
        html += _cabecera_viatico(numero, cab, titulo, filas)
        html += _tabla_viatico(filas)
    else:
        html += _cabecera_viatico(numero, cab,
                                  f"VIÁTICO N° {_num_txt(numero)} — GENERAL (ORIGINAL + AJUSTES)",
                                  filas)
        total_t = 0
        total_c = 0
        for aj in sorted(grupos):
            gf = grupos[aj]
            titulo = "VIÁTICO ORIGINAL" if aj == 0 else f"AJUSTE DE VIÁTICO N° {_num_txt(numero)}-{aj}"
            if aj > 0:
                html += f"<h2>{titulo} — RECIBO: {cab.get('recibo_ajuste') or (gf[0].get('recibo_ajuste') or '—')}</h2>"
            else:
                html += f"<h2>{titulo}</h2>"
            html += _tabla_viatico(gf)
            total_t += sum(float(x.get("total") or 0) for x in gf)
            total_c += sum(float(x.get("valor_cajero") or 0) for x in gf)
        t = lambda k: sum(float(x.get(k) or 0) for x in filas)
        # TOTAL GENERAL: 23 columnas para el título + TOTAL (24) + CAJERO (25).
        # Antes decía 22 y los dos valores salían una columna corridos a la izquierda.
        html += f"""
        <table><tr class="tot">
          <td colspan="23"><b>TOTAL GENERAL DEL VIÁTICO N° {_num_txt(numero)}</b></td>
          <td class="r"><b>{fmt(t('total'))}</b></td><td class="r"><b>{fmt(t('valor_cajero'))}</b></td>
        </tr></table>"""
    html += _firmas_viatico(cab)
    html += "</body></html>"
    # El nombre del archivo (y lo que imprime el navegador como título) usa el
    # número visible del viático: viatico_001-2026. Antes usaba el número interno.
    _abrir(html, f"viatico_{db.db_etiqueta_archivo(numero)}")


def _firmas_viatico(cab):
    return f"""
    <table class="firmas"><tr>
      <td><div class="linea"></div>ELABORADO POR<br>{cab.get('responsable','')}</td>
      <td><div class="linea"></div>REVISADO POR<br>ADMINISTRACIÓN MIEMPRESA</td>
      <td><div class="linea"></div>APROBADO POR<br>GERENCIA</td>
      <td><div class="linea"></div>RECIBÍ CONFORME<br>ENCARGADO DEL VIÁTICO</td>
    </tr></table>"""


def imprimir_justificacion(numero, cab, filas, gastos, respaldos, devolucion=None):
    """Justificación en el formato exacto del Excel de Miempresa (hoja por viático)."""
    from datetime import date as fdate
    entregado = sum(float(f.get("valor_cajero") or 0) for f in filas)
    respaldo_total = sum(float(g.get("total") or 0) for g in gastos)
    devolucion = devolucion or {}
    dev_monto = float(devolucion.get("monto") or 0)
    pago_emp = float(devolucion.get("pago_empleado") or 0)
    saldo = entregado - respaldo_total
    r0 = filas[0] if filas else {}
    rf = filas[-1] if filas else {}
    fs = fdate.fromisoformat(r0["fecha_salida"]) if r0.get("fecha_salida") else fdate.today()
    fr = fdate.fromisoformat(rf["fecha_regreso"]) if rf.get("fecha_regreso") else fs
    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
             "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    mes_ano = f"{meses[fs.month - 1]}  -  {fs.year}"
    dias_total = (fr - fs).days + 1
    emps = sorted({f["nombre_empleado"] for f in filas})
    chofer = next((f["nombre_empleado"] for f in filas if f.get("es_chofer")), "")
    encargado = next((f["nombre_empleado"] for f in filas if f.get("es_encargado")),
                     cab.get("responsable", ""))
    elaborado = devolucion.get("elaborado_por") or "PAOLA NARANJO"
    recibos = " / ".join(x for x in (cab.get("recibo_viatico"), cab.get("recibo_viatico_2"),
                                     cab.get("recibo_viatico_3")) if x) or "—"
    # La observación la escribe el responsable (a veces es a favor de la empresa, a veces del empleado)
    obs = devolucion.get("observacion") or ""

    html = _head(f"Justificación {_num_txt(numero)}")
    html += f"""
    <h1>{mes_ano}</h1>
    <table class="meta">
      <tr><td class="lbl">BENEFICIARIO:</td><td>{encargado}</td>
          <td class="lbl">FECHA DE VIAJE DESDE CUENCA:</td><td>{fmt_f(r0.get('fecha_salida'))}</td>
          <td class="lbl">N° VIÁTICO:</td><td><b>{_num_txt(numero)}</b></td></tr>
      <tr><td class="lbl">PROYECTO O CLIENTE:</td><td>{cab.get('cliente_proyecto','')}</td>
          <td class="lbl">FECHA DE LLEGADA AL PROYECTO:</td><td>{fmt_f(r0.get('fecha_llegada_trabajo'))}</td>
          <td class="lbl">MANEJA (IR):</td><td>{chofer}</td></tr>
      <tr><td class="lbl">VIAJA A:</td><td>{r0.get('lugar_trabajo','')}</td>
          <td class="lbl">FECHA Y HORA DE SALIDA DEL PROYECTO:</td>
          <td>{fmt_f(r0.get('fecha_salida_trabajo'))} {r0.get('hora_salida_trabajo','')}</td>
          <td class="lbl">MANEJA (VOLVER):</td><td>{chofer}</td></tr>
      <tr><td class="lbl">DÍAS DE VIAJE:</td><td>{dias_total}</td>
          <td class="lbl">HORA DE LLEGADA A CUENCA:</td>
          <td>{fmt_f(rf.get('fecha_regreso'))} {rf.get('hora_regreso','')}</td>
          <td class="lbl">RECIBO DE VIÁTICO N°:</td><td>{recibos}</td></tr>
      <tr><td class="lbl">CAMIONETA:</td><td>{r0.get('placa','')}</td>
          <td class="lbl">PERSONAS:</td><td colspan="3">{', '.join(emps)}</td></tr>
    </table>
    """
    ths = "".join(f"<th>{t}</th>" for k, t, _ in HEADERS_JUSTIFICACION)
    por_gasto = {}
    for r in (respaldos or []):
        if r.get("gasto_id"):
            por_gasto.setdefault(r["gasto_id"], []).append(r.get("nombre_archivo", ""))
    rows = ""
    t = lambda k: sum(float(g.get(k) or 0) for g in gastos)
    for i, g in enumerate(gastos, 1):
        arch = ", ".join(por_gasto.get(g.get("id"), []))
        archivo = f"<br><span style='font-size:8px;color:#667'>{arch}</span>" if arch else ""
        explicacion = (g.get("nota") or "").replace("<", "&lt;").replace(">", "&gt;")
        rows += f"""<tr>
          <td class="c">{fmt_f(g.get('fecha'))}</td><td>{g.get('numero_comprobante','')}{archivo}</td>
          <td>{g.get('tipo','')}</td><td>{g.get('ruc','')}</td><td>{g.get('proveedor','')}</td>
          <td>{g.get('lugar','')}</td><td class="r">{fmt(g.get('hospedaje'))}</td>
          <td class="r">{fmt(g.get('combustible'))}</td><td class="r">{fmt(g.get('buses'))}</td>
          <td class="r">{fmt(g.get('taxis'))}</td><td class="r">{fmt(g.get('alimentacion'))}</td>
          <td class="r">{fmt(g.get('peaje'))}</td><td class="r">{fmt(g.get('otros'))}</td>
          <td class="r">{fmt(g.get('total'))}</td>
          <td style="font-size:9px">{explicacion}</td></tr>"""
    for _ in range(max(0, 8 - len(gastos))):
        rows += "<tr>" + "".join("<td>&nbsp;</td>" for _ in HEADERS_JUSTIFICACION) + "</tr>"
    rows += f"""<tr class="tot">
      <td colspan="6"><b>TOTAL GASTOS RESPALDADOS</b></td>
      <td class="r">{fmt(t('hospedaje'))}</td><td class="r">{fmt(t('combustible'))}</td>
      <td class="r">{fmt(t('buses'))}</td><td class="r">{fmt(t('taxis'))}</td>
      <td class="r">{fmt(t('alimentacion'))}</td><td class="r">{fmt(t('peaje'))}</td>
      <td class="r">{fmt(t('otros'))}</td><td class="r">{fmt(respaldo_total)}</td>
      <td></td></tr>"""
    html += f"<table><tr>{ths}</tr>{rows}</table>"

    notas = [g for g in gastos if (g.get("nota") or "").strip()]
    if notas:
        filas_notas = ""
        for g in notas:
            filas_notas += f"""<tr>
              <td>{g.get('numero_comprobante','') or '—'}</td>
              <td>{g.get('proveedor','') or '—'}</td>
              <td>{(g.get('nota') or '').replace('<', '&lt;').replace('>', '&gt;')}</td></tr>"""
        html += f"""<h2>EXPLICACIÓN DE VALORES DE LAS FACTURAS</h2>
        <table>
          <tr><th>NRO COMPROBANTE</th><th>PROVEEDOR</th><th>EXPLICACIÓN</th></tr>
          {filas_notas}
        </table>"""

    firmas = f"""
    <table class="meta" style="margin-top:12px">
      <tr><td class="lbl">VALOR ENTREGADO</td><td class="r"><b>{fmt(entregado)}</b></td>
          <td class="lbl">VALOR RESPALDADO</td><td class="r"><b>{fmt(respaldo_total)}</b></td></tr>
      <tr><td class="lbl">SALDO</td><td class="r"><b>{fmt(saldo)}</b></td>
          <td class="lbl">DEVOLUCIÓN A MIEMPRESA</td><td class="r"><b>{fmt(dev_monto)}</b></td></tr>
      <tr><td class="lbl"></td><td></td>
          <td class="lbl">PAGO AL EMPLEADO (GASTÓ MÁS)</td><td class="r"><b>{fmt(pago_emp)}</b></td></tr>
      <tr><td class="lbl">OBSERVACIÓN:</td><td colspan="3">{obs}</td></tr>
    </table>
    <table class="firmas"><tr>
      <td><div class="linea"></div>Elaborado por:<br>{elaborado}</td>
      <td><div class="linea"></div>Revisado por: _________________</td>
    </tr></table>
    """
    html += firmas
    html += "</body></html>"
    _abrir(html, f"justificacion_{db.db_etiqueta_archivo(numero)}")


def imprimir_bitacora(filas, filtros=""):
    """Informe de actividad (bitácora) listo para imprimir o guardar como PDF."""
    conteo_usuarios, conteo_acciones = {}, {}
    for r in filas:
        quien = r.get("usuario_nombre") or r.get("usuario") or "SIN USUARIO"
        conteo_usuarios[quien] = conteo_usuarios.get(quien, 0) + 1
        acc = r.get("accion") or "SIN ACCIÓN"
        conteo_acciones[acc] = conteo_acciones.get(acc, 0) + 1
    html = _head("Informe de actividad")
    html += f"""<h1>INFORME DE ACTIVIDAD DEL SISTEMA</h1>
    <div class="empresa">MIEMPRESA S.A. — Sistema de Viáticos · Cuenca, Ecuador</div>
    <div class="empresa">FILTRO: {filtros}</div>
    <div class="empresa">TOTAL DE MOVIMIENTOS: <b>{len(filas)}</b></div>"""
    ths = "".join(f"<th>{t}</th>" for t in ("FECHA Y HORA", "USUARIO", "ROL", "ACCIÓN",
                                            "MÓDULO", "REFERENCIA", "DETALLE"))
    rows = ""
    for r in filas:
        rows += f"""<tr>
          <td class="c">{r.get('fecha','')}</td><td>{r.get('usuario_nombre') or r.get('usuario') or ''}</td>
          <td class="c">{db.ETIQUETA_ROL.get(r.get('rol') or '', r.get('rol') or '')}</td>
          <td>{r.get('accion','')}</td><td class="c">{r.get('entidad','')}</td>
          <td class="c">{r.get('referencia','')}</td><td>{(r.get('detalle') or '')}</td></tr>"""
    html += f"<h2>MOVIMIENTOS</h2><table><tr>{ths}</tr>{rows}</table>"
    filas_res = "".join(f"<tr><td>{k}</td><td class='r'>{v}</td></tr>"
                        for k, v in sorted(conteo_usuarios.items()))
    html += f"""<h2>RESUMEN POR USUARIO</h2>
    <table><tr><th>USUARIO</th><th>MOVIMIENTOS</th></tr>{filas_res}</table>"""
    filas_acc = "".join(f"<tr><td>{k}</td><td class='r'>{v}</td></tr>"
                        for k, v in sorted(conteo_acciones.items()))
    html += f"""<h2>RESUMEN POR ACCIÓN</h2>
    <table><tr><th>ACCIÓN</th><th>MOVIMIENTOS</th></tr>{filas_acc}</table>"""
    html += """<table class="firmas"><tr>
      <td><div class="linea"></div>Elaborado por: _________________</td>
      <td><div class="linea"></div>Revisado por: _________________</td>
    </tr></table></body></html>"""
    _abrir(html, "informe_actividad")

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
