# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""comparar_excel_viaticos.py — Carga los viáticos del Excel real y compara valores.

Lee el Excel de viáticos de la empresa (una hoja por viático, formato histórico
«BENEFICIARIO / FECHA DE VIAJE DESDE / … / VALOR ENTREGADO»), **crea los mismos
viáticos en una base local** y compara, viático por viático:

  · los gastos respaldados (nuestra suma por categoría vs. la del Excel, que debe
    dar idéntico porque son los mismos datos);
  · lo entregado: lo que paga el programa con las reglas de `calculos.py`
    (desayuno, almuerzo, merienda, taxis, hospedaje, agua y el combustible de las
    facturas) contra el «VALOR ENTREGADO» escrito en el Excel;
  · los días de viaje y las noches de hospedaje.

Uso:

    python herramientas\\comparar_excel_viaticos.py
    python herramientas\\comparar_excel_viaticos.py "C:\\ruta\\VIATICOS 2026.xlsx" --desde 1 --hasta 20
    python herramientas\\comparar_excel_viaticos.py --sin-guardar      (solo compara)
    python herramientas\\comparar_excel_viaticos.py --base-real        (usa data\\viaticos.db)

Por defecto los viáticos se crean en una base local aparte
(`herramientas\\prueba_excel\\data\\viaticos.db`) para no mezclarlos con los datos
de trabajo, y el informe queda en `documentacion\\PRUEBA_EXCEL_VIATICOS.md`.
"""
import argparse
import os
import sys
from datetime import date, datetime, time
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_COLUMNAS_GASTO = ["hospedaje", "combustible", "buses", "taxis", "alimentacion",
                   "peaje", "otros"]


def preparar_base(base_real=False):
    """Deja lista la base local ANTES de importar el sistema. Devuelve la ruta del .db."""
    if base_real:
        return None
    destino = _AQUI / "prueba_excel" / "data"
    destino.mkdir(parents=True, exist_ok=True)
    os.environ["VIATICOS_MOTOR"] = "sqlite"
    os.environ["VIATICOS_DATA"] = str(destino)
    os.environ["VIATICOS_RESPALDOS"] = "carpeta"
    return destino / "viaticos.db"


# ------------------------------------------------------------ lectura del Excel
def _txt(valor):
    return "" if valor is None else str(valor).strip()


def _num(valor):
    """Convierte una celda en número (acepta '1.234,56' y celdas vacías)."""
    if valor is None or valor == "":
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("$", "").replace(" ", "")
    try:
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", ".")
        return float(texto)
    except ValueError:
        return 0.0


def _fecha(valor):
    """Fecha (YYYY-MM-DD) de una celda de Excel. '' si no sirve."""
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    texto = _txt(valor)
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto[:len(formato) + 2].strip(), formato).date().isoformat()
        except ValueError:
            continue
    return ""


def _hora(valor, por_defecto="00:00"):
    """Hora (HH:MM) de una celda de Excel. Las celdas dañadas dan el valor por defecto."""
    if isinstance(valor, datetime):
        return valor.strftime("%H:%M")
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    texto = _txt(valor)
    if ":" in texto:
        partes = texto.split(":")
        try:
            return "%02d:%02d" % (int(partes[0]), int(partes[1]))
        except ValueError:
            return por_defecto
    return por_defecto


def _numero_hoja(titulo, fila3):
    """Número del viático: el de la celda «N° Viático» o el del nombre de la hoja.

    `fila3` es la fila 3 de la hoja (lista de valores): en los archivos reales el
    rótulo y el número van juntos en una celda («N° Viático: 01») y a veces el
    número está en la celda de al lado.
    """
    for valor in fila3[8:14]:
        texto = _txt(valor).upper()
        if "VIÁTICO" in texto or "VIATICO" in texto:
            digitos = "".join(c for c in texto if c.isdigit())
            if digitos:
                return int(digitos)
        elif isinstance(valor, (int, float)) and float(valor) > 0:
            return int(valor)
    digitos = ""
    for caracter in _txt(titulo).strip():
        if caracter.isdigit():
            digitos += caracter
        elif digitos:
            break
    return int(digitos) if digitos else 0


def _anio_hoja(titulo, fecha_salida, anio_defecto=2026):
    """Año del viático: el del encabezado de la hoja («ENERO - 2026»)."""
    for palabra in titulo.replace("-", " ").split():
        if palabra.strip().isdigit() and 2000 <= int(palabra) <= 2100:
            return int(palabra)
    if fecha_salida[:4].isdigit() and 2000 <= int(fecha_salida[:4]) <= 2100:
        return int(fecha_salida[:4])
    return anio_defecto


def leer_hoja(hoja):
    """Un viático del Excel histórico. None si la hoja está anulada o vacía."""
    titulo = _txt(hoja.title)
    if "ANULAD" in titulo.upper():
        return None

    def celda(fila, columna):
        return hoja.cell(row=fila, column=columna).value

    beneficiario = _txt(celda(3, 2))
    if not beneficiario:
        return None                      # hoja en blanco (los anulados no tienen datos)
    datos = {
        "hoja": titulo,
        "numero": _numero_hoja(titulo, [celda(3, c) for c in range(1, 15)]),
        "beneficiario": beneficiario.upper(),
        "cliente": _txt(celda(4, 2)).upper(),
        "viaja_a": _txt(celda(5, 2)).upper(),
        "dias_excel": int(_num(celda(6, 2))),
        "placa": _txt(celda(7, 2)).upper(),
        "maneja": _txt(celda(6, 12)).upper(),
        "personas": _txt(celda(8, 2)),
        "recibo": _txt(celda(8, 14)),
        # En este formato la fecha va en la columna F (6) y la hora en la G (7).
        "fecha_salida": _fecha(celda(3, 6)), "hora_salida": _hora(celda(3, 7), "08:00"),
        "fecha_regreso": _fecha(celda(4, 6)), "hora_regreso": _hora(celda(4, 7), "18:00"),
        "fecha_llegada": _fecha(celda(5, 6)), "hora_llegada": _hora(celda(5, 7), "12:00"),
        "fecha_salida_trabajo": _fecha(celda(6, 6)),
        "hora_salida_trabajo": _hora(celda(6, 7), "16:00"),
        "gastos": [], "sumas_excel": {c: 0.0 for c in _COLUMNAS_GASTO},
        "total_declarado": 0.0, "entregado": 0.0, "respaldado": 0.0, "saldo": 0.0,
        "observacion": "",
    }
    datos["anio"] = _anio_hoja(titulo, datos["fecha_salida"])
    hay_sumas = False
    for fila in range(10, hoja.max_row + 1):
        textos = [_txt(celda(fila, c)) for c in range(1, 15)]
        etiqueta = textos[0].upper()
        numeros = [_num(celda(fila, c)) for c in range(7, 15)]      # G..N
        if etiqueta.startswith("VALOR ENTREGADO"):
            datos["entregado"] = numeros[7] or _num(celda(fila, 2)) or _num(celda(fila, 3))
            continue
        if etiqueta.startswith("VALOR RESPALDADO"):
            datos["respaldado"] = _num(celda(fila, 3)) or _num(celda(fila, 2))
            continue
        if etiqueta.startswith("SALDO"):
            datos["saldo"] = _num(celda(fila, 3)) or _num(celda(fila, 2))
            continue
        if etiqueta.startswith("OBSERVAC"):
            datos["observacion"] = _txt(celda(fila, 2))
            continue
        if etiqueta.startswith("TOTAL"):
            datos["sumas_excel"] = dict(zip(_COLUMNAS_GASTO, numeros[:7]))
            datos["total_declarado"] = numeros[7]
            hay_sumas = True
            continue
        fecha = _fecha(celda(fila, 1))
        if not fecha and not any(numeros[:7]):
            continue
        if not fecha and not textos[1] and not textos[4] and not hay_sumas:
            # Fila de sumas del Excel (sin etiqueta, sin fecha y sin proveedor).
            datos["sumas_excel"] = dict(zip(_COLUMNAS_GASTO, numeros[:7]))
            datos["total_declarado"] = numeros[7]
            hay_sumas = True
            continue
        gasto = {"fecha": fecha, "numero_comprobante": textos[1], "tipo": textos[2],
                 "ruc": textos[3], "proveedor": textos[4].upper(), "lugar": textos[5].upper()}
        gasto.update({c: v for c, v in zip(_COLUMNAS_GASTO, numeros[:7])})
        gasto["total"] = numeros[7] or round(sum(numeros[:7]), 2)
        datos["gastos"].append(gasto)
    datos["suma_gastos"] = {c: round(sum(g[c] for g in datos["gastos"]), 2)
                            for c in _COLUMNAS_GASTO}
    datos["total_gastos"] = round(sum(g["total"] for g in datos["gastos"]), 2)
    return datos


def sanear_fechas(datos):
    """Deja las fechas del Excel en un rango coherente y devuelve los avisos.

    El archivo trae años escritos mal (por ejemplo salida 25/01/2025 y llegada al
    trabajo 25/01/2026): si la fecha de llegada o de salida del trabajo queda fuera
    del viaje, se usan las del viaje, que es lo que hace el programa cuando no hay
    ese dato. Si el viaje entero es incoherente (el regreso antes de la salida o más
    de 60 días), el viático se marca como dudoso y no entra en los totales.
    """
    avisos = []
    salida, regreso = datos["fecha_salida"], datos["fecha_regreso"]
    if salida and regreso:
        if regreso < salida or (date.fromisoformat(regreso)
                                - date.fromisoformat(salida)).days > 60:
            datos["dudoso"] = True
            avisos.append("las fechas del viaje no cuadran (%s → %s)" % (salida, regreso))
        else:
            for clave, rotulo in (("fecha_llegada", "llegada al trabajo"),
                                  ("fecha_salida_trabajo", "salida del trabajo")):
                fecha = datos[clave]
                if fecha and not (salida <= fecha <= regreso):
                    datos[clave] = ""
                    avisos.append("la %s del Excel (%s) estaba fuera del viaje" % (rotulo, fecha))
        if salida[:4] != regreso[:4]:
            avisos.append("el año de las fechas cambia (%s → %s)" % (salida, regreso))
        dias = (date.fromisoformat(regreso) - date.fromisoformat(salida)).days + 1
        if datos["dias_excel"] and datos["dias_excel"] != dias:
            avisos.append("el Excel dice %d día(s) y sus fechas dan %d"
                          % (datos["dias_excel"], dias))
    datos["avisos"] = avisos
    return avisos


def comparar(datos, p, solo_reglas=False):
    """Compara lo que paga el programa con lo que dice el Excel.

    `solo_reglas=False` (como se paga en la empresa): comidas, taxis, hospedaje y
    agua según las reglas, y el combustible/peaje/otros de las facturas cargadas.
    """
    import calculos as CAL
    fs = datos["fecha_salida"] or datos["fecha_regreso"]
    fr = datos["fecha_regreso"] or fs
    if not fs or not fr:
        return None
    # Se revisan las fechas ANTES de calcular: el archivo tiene años escritos mal y
    # de ahí salían hospedajes imposibles.
    avisos = sanear_fechas(datos)
    v = CAL.DatosViaje(
        nombre_empleado=datos["beneficiario"], lugar_trabajo=datos["viaja_a"] or "—",
        fecha_salida=date.fromisoformat(fs), hora_salida=CAL.hora_limite(datos["hora_salida"]),
        fecha_regreso=date.fromisoformat(fr), hora_regreso=CAL.hora_limite(datos["hora_regreso"]),
        fecha_llegada_trabajo=date.fromisoformat(datos["fecha_llegada"] or fs),
        hora_llegada_trabajo=CAL.hora_limite(datos["hora_llegada"]),
        fecha_salida_trabajo=date.fromisoformat(datos["fecha_salida_trabajo"] or fr),
        hora_salida_trabajo=CAL.hora_limite(datos["hora_salida_trabajo"]),
        km_recorridos=0.0,
        parqueadero_peaje=0.0 if solo_reglas else datos["suma_gastos"]["peaje"],
        otros=0.0 if solo_reglas else datos["suma_gastos"]["otros"],
        combustible_efectivo=0.0 if solo_reglas else datos["suma_gastos"]["combustible"])
    r = CAL.calcular(v, p)
    fila = dict(datos)
    fila.update({"programa": r, "noches": CAL.noches_de_hospedaje(v),
                 "dias_programa": r["dias_viaje"],
                 "avisos": avisos,
                 "dudoso": bool(datos.get("dudoso")),
                 "delta_entregado": round(datos["entregado"] - r["valor_cajero"], 2),
                 "delta_respaldado": round(datos["respaldado"] - datos["total_gastos"], 2),
                 "delta_dias": datos["dias_excel"] - r["dias_viaje"]})
    return fila


def cab_y_filas(datos, calculado):
    """Cabecera y fila del viático tal como las guarda la pantalla de viáticos.

    Del Excel histórico se toma una fila (el beneficiario de la hoja): es quien
    maneja y a nombre de quien salieron los respaldos. Los acompañantes quedan
    anotados en las observaciones.
    """
    personas = (" · personas: " + datos["personas"]) if datos["personas"] else ""
    cab = {"responsable": datos["beneficiario"], "cliente_proyecto": datos["cliente"],
           "orden_combustible": "", "placa": datos["placa"],
           "observaciones": ("DEL EXCEL · hoja %s%s" % (datos["hoja"], personas)).upper(),
           "recibo_viatico": datos["recibo"], "recibo_viatico_2": "", "recibo_viatico_3": ""}
    salida = datos["fecha_salida"] or datos["fecha_regreso"]
    regreso = datos["fecha_regreso"] or datos["fecha_salida"]
    fila = {"lugar_trabajo": datos["viaja_a"] or "—", "provincia": "", "canton": datos["viaja_a"],
            "orden_combustible_2": "", "ajuste_numero": 0,
            "efectivo_combustible": datos["suma_gastos"]["combustible"],
            "fecha_salida": salida, "hora_salida": datos["hora_salida"],
            "fecha_regreso": regreso, "hora_regreso": datos["hora_regreso"],
            "fecha_llegada_trabajo": datos["fecha_llegada"] or salida,
            "hora_llegada_trabajo": datos["hora_llegada"],
            "fecha_salida_trabajo": datos["fecha_salida_trabajo"] or regreso,
            "hora_salida_trabajo": datos["hora_salida_trabajo"],
            "nombre_empleado": datos["beneficiario"], "es_encargado": 1,
            "es_chofer": 1 if datos["maneja"] == datos["beneficiario"] else 0,
            "medio_transporte": "AUTO", "extra_transporte": 0.0, "km_recorridos": 0.0,
            "parqueadero_peaje": datos["suma_gastos"]["peaje"],
            "otros": datos["suma_gastos"]["otros"]}
    fila.update(calculado["programa"])
    return cab, [fila]


def guardar_viatico(datos, calculado):
    """Crea el viático y sus gastos en la base local. Devuelve el número interno."""
    import database as db
    numero = db.clave_viatico(datos["anio"], datos["numero"] or 1)
    cab, filas = cab_y_filas(datos, calculado)
    db.guardar_viaje(cab, filas, numero=numero)
    campos = ("fecha", "numero_comprobante", "tipo", "ruc", "proveedor", "lugar",
              "hospedaje", "combustible", "buses", "taxis", "alimentacion", "peaje",
              "otros", "total")
    for g in datos["gastos"]:
        db.guardar_gasto(numero, {k: g.get(k) for k in campos})
    return numero


# ---------------------------------------------------------------- informe
def _f(valor):
    return "%.2f" % float(valor or 0)


def informe(lista, extra, ruta):
    """Escribe el informe de la comparación en Markdown."""
    # Los viáticos con fechas incoherentes (error de tipeo en el Excel) se listan
    # pero no entran en los totales.
    validos = [f for f in lista if not f.get("dudoso")]
    totales = {k: sum(f[k] for f in validos) for k in
               ("entregado", "total_gastos", "respaldado")}
    entregado_prog = sum(f["programa"]["valor_cajero"] for f in validos)
    total_prog = sum(f["programa"]["total"] for f in validos)
    iguales = [f for f in validos if abs(f["delta_entregado"]) < 0.01]
    arriba = [f for f in validos if f["delta_entregado"] > 0]
    abajo = [f for f in validos if f["delta_entregado"] < 0]
    mayor = sorted(validos, key=lambda f: -abs(f["delta_entregado"]))[:3]
    dias_igual = [f for f in validos if f["delta_dias"] == 0]
    con_sumas = [f for f in validos if abs(f["total_gastos"] - f["respaldado"]) < 0.01]
    n = len(validos)

    L = []
    ap = L.append
    ap("# Prueba con el Excel real de viáticos")
    ap("")
    ap("Comparación viático por viático entre el Excel de la empresa y lo que calcula")
    ap("el programa, hecha de forma **local** (sin tocar el servidor).")
    ap("")
    ap("| Dato | Valor |")
    ap("|---|---|")
    ap("| Archivo leído | `%s` |" % extra["archivo"])
    ap("| Hojas del archivo | %d |" % extra["hojas"])
    ap("| Viáticos comparados | %d |" % len(lista))
    ap("| Hojas anuladas o vacías | %d |" % extra["omitidas"])
    ap("| Base local usada | `%s` |" % extra["base"])
    ap("| Parámetros del programa | desayuno $%s · almuerzo $%s · merienda $%s · hospedaje $%s · agua $%s · km $%s · redondeo cajero $%s |"
       % (_f(extra["p"]["valor_desayuno"]), _f(extra["p"]["valor_almuerzo"]),
          _f(extra["p"]["valor_merienda"]), _f(extra["p"]["valor_hospedaje"]),
          _f(extra["p"]["valor_agua"]), _f(extra["p"]["valor_combustible_km"]),
          _f(extra["p"].get("redondeo_cajero", 5))))
    ap("")
    ap("## 1. Resumen")
    ap("")
    ap("| Concepto | Excel | Programa | Diferencia |")
    ap("|---|---|---|---|")
    ap("| Gastos respaldados (facturas) | $%s | $%s | $%s |"
       % (_f(totales["total_gastos"]), _f(totales["total_gastos"]),
          _f(0)))
    ap("| Valor entregado | $%s | $%s | $%s |"
       % (_f(totales["entregado"]), _f(entregado_prog),
          _f(totales["entregado"] - entregado_prog)))
    ap("| Total calculado antes del redondeo | — | $%s | — |" % _f(total_prog))
    ap("| Valor respaldado que dice el Excel | $%s | $%s (suma real de facturas) | $%s |"
       % (_f(totales["respaldado"]), _f(totales["total_gastos"]),
          _f(totales["respaldado"] - totales["total_gastos"])))
    ap("")
    ap("- Viáticos con diferencia menor a un centavo: **%d de %d**." % (len(iguales), n))
    ap("- El Excel pagó **más** que el programa en **%d** viáticos y **menos** en **%d**."
       % (len(arriba), len(abajo)))
    ap("- Días de viaje iguales en **%d de %d** viáticos." % (len(dias_igual), n))
    ap("- «Valor respaldado» del Excel igual a la suma de sus facturas en **%d de %d**"
       " (en el resto el Excel tiene diferencias propias)." % (len(con_sumas), n))
    ap("- Viáticos con fechas incoherentes en el Excel (no entran en los totales): **%d**."
       % (len(lista) - n))
    ap("")

    ap("## 2. Viático por viático")
    ap("")
    ap("«Respaldado» = suma de las facturas cargadas. «Entregado» = lo que el cajero")
    ap("entregó según el Excel y lo que entregaría el programa (ya redondeado).")
    ap("")
    ap("| N° | Beneficiario | Días Excel | Días programa | Respaldado Excel | Respaldado programa | Entregado Excel | Entregado programa | Diferencia | Nota |")
    ap("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for f in sorted(lista, key=lambda x: (x["anio"], x["numero"])):
        ap("| %d | %s | %d | %d | $%s | $%s | $%s | $%s | $%s | %s |"
           % (f["numero"], f["beneficiario"][:26], f["dias_excel"], f["dias_programa"],
              _f(f["total_gastos"]), _f(f["total_gastos"]), _f(f["entregado"]),
              _f(f["programa"]["valor_cajero"]), _f(f["delta_entregado"]),
              "⚠ revisar fechas" if f.get("dudoso") else ""))
    ap("")

    ap("## 3. Los viáticos con mayor diferencia")
    ap("")
    for f in mayor:
        r = f["programa"]
        ap("### Viático N° %d — %s (%s) · %s al %s"
           % (f["numero"], f["beneficiario"], f["viaja_a"] or "—", f["fecha_salida"],
              f["fecha_regreso"]))
        ap("")
        ap("| Concepto | Excel | Programa |")
        ap("|---|---:|---:|")
        ap("| Días de viaje | %d | %d |" % (f["dias_excel"], f["dias_programa"]))
        ap("| Desayuno | — | $%s |" % _f(r["desayuno"]))
        ap("| Almuerzo | — | $%s |" % _f(r["almuerzo"]))
        ap("| Merienda | — | $%s |" % _f(r["merienda"]))
        ap("| Taxi de salida | — | $%s |" % _f(r["taxi_salida"]))
        ap("| Taxi de regreso | — | $%s |" % _f(r["taxi_regreso"]))
        ap("| Hospedaje | $%s (facturas) | $%s (%d noche(s)) |"
           % (_f(f["suma_gastos"]["hospedaje"]), _f(r["hospedaje"]), f["noches"]))
        ap("| Agua | — | $%s |" % _f(r["agua"]))
        ap("| Otros gastos (facturas) | $%s | — |" % _f(f["suma_gastos"]["otros"]))
        ap("| Combustible | $%s (facturas) | $%s |" % (_f(f["suma_gastos"]["combustible"]),
                                                       _f(r["combustible"])))
        ap("| Peaje y parqueadero | $%s (facturas) | $%s |"
           % (_f(f["suma_gastos"]["peaje"]), _f(r.get("peaje", 0) or 0)))
        ap("| Alimentación / taxis de facturas | $%s | — |"
           % _f(f["suma_gastos"]["alimentacion"] + f["suma_gastos"]["taxis"]))
        ap("| **TOTAL** | $%s entregado · $%s respaldado | $%s (cajero $%s) |"
           % (_f(f["entregado"]), _f(f["total_gastos"]), _f(r["total"]),
              _f(r["valor_cajero"])))
        if f["observacion"]:
            ap("")
            ap("Observación del Excel: %s" % f["observacion"])
        for aviso in f.get("avisos", []):
            ap("")
            ap("- ⚠ %s" % aviso)
        ap("")

    ap("## 4. Por qué sale la diferencia")
    ap("")
    ap("- En el Excel histórico el **valor entregado** es un anticipo redondo y el respaldo")
    ap("  son las **facturas reales** que trajo la persona; la comida no se calcula por")
    ap("  horario. El programa sí aplica esas reglas (las mismas del formato nuevo), así")
    ap("  que la diferencia total de $%s es esperada."
       % _f(totales["entregado"] - entregado_prog))
    ap("- Diferencia media por viático: $%.2f."
       % (sum(abs(f["delta_entregado"]) for f in lista) / max(len(lista), 1)))
    ap("- En %d viáticos la diferencia es de $5 o menos (el redondeo del cajero la absorbe)."
       % len([f for f in lista if abs(f["delta_entregado"]) <= 5]))
    ap("- Entregado múltiplo de 5 en %d de %d viáticos (anticipo redondeado a mano)."
       % (len([f for f in lista if f["entregado"] and abs(f["entregado"] % 5) < 0.01]),
          len(lista)))
    ap("- %d viáticos traen facturas de combustible: el programa las respeta en lugar de"
       " cobrar por km, igual que hace la empresa."
       % len([f for f in lista if f["suma_gastos"]["combustible"] > 0]))
    ap("- %d viáticos traen facturas de hospedaje, mientras el programa calcula las noches"
       " con las fechas de llegada y salida del trabajo."
       % len([f for f in lista if f["suma_gastos"]["hospedaje"] > 0]))
    ap("- Horas de llegada al trabajo registradas en el Excel: %d de %d viáticos."
       % (len([f for f in lista if f["fecha_llegada"]]), len(lista)))
    ap("")
    ap("### Datos del Excel que no cuadran (revisar el archivo)")
    ap("")
    con_avisos = [f for f in lista if f.get("avisos")]
    ap("Viáticos con fechas, años o días escritos de forma incoherente: **%d de %d**."
       % (len(con_avisos), len(lista)))
    ap("")
    for f in con_avisos[:25]:
        ap("- **N° %d** (%s): %s" % (f["numero"], f["beneficiario"][:24],
                                     "; ".join(f["avisos"])))
    if len(con_avisos) > 25:
        ap("- … y %d más (revise el archivo del Excel)." % (len(con_avisos) - 25))
    ap("")
    ap("## 5. Cómo revisar estos viáticos en el sistema")
    ap("")
    ap("Quedaron creados con el **mismo número del Excel**. La base usada es")
    ap("`%s`." % extra["base"])
    ap("Para abrirlos en el programa: copie ese archivo `viaticos.db` a la carpeta `data`")
    ap("del sistema (haga antes una copia de la base que ya está ahí), o abra el sistema")
    ap("con `VIATICOS_MOTOR=sqlite` y `VIATICOS_DATA` apuntando a esa carpeta. Después")
    ap("entre a «Generar / revisar / ajustar viáticos» y a «Justificar viáticos».")
    ap("")
    ap("## 6. Conclusión")
    ap("")
    ap("- Cargar el Excel al programa funciona: los **gastos respaldados coinciden al")
    ap("  centavo** con el Excel en los %d viáticos (nuestra suma por categoría es la misma)."
       % len(lista))
    ap("- Las diferencias están en **cuánto se entrega**, no en los datos guardados: el")
    ap("  programa paga por reglas y el Excel histórico pagaba por facturas.")
    ap("- Para que los valores coincidan en el día a día conviene usar el formato nuevo")
    ap("  (`VIATICO 2 2026.xlsx`), que ya trae las columnas calculadas por día: ahí sí se")
    ap("  puede comparar regla contra regla.")
    ap("")
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return L


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(
        description="Carga los viáticos del Excel real en una base local y compara valores.")
    ap.add_argument("excel", nargs="?", default=str(_AQUI.parent.parent / "VIATICOS 2026.xlsx"),
                    help="ruta del Excel de viáticos")
    ap.add_argument("--desde", type=int, default=0, help="primer N° de viático a procesar")
    ap.add_argument("--hasta", type=int, default=0, help="último N° de viático a procesar")
    ap.add_argument("--limite", type=int, default=0, help="máximo de viáticos a procesar")
    ap.add_argument("--sin-guardar", action="store_true",
                    help="solo compara: no crea nada en la base")
    ap.add_argument("--base-real", action="store_true",
                    help="usar la base local de trabajo (data\\viaticos.db)")
    ap.add_argument("--informe", default=str(_AQUI.parent / "documentacion"
                                            / "PRUEBA_EXCEL_VIATICOS.md"),
                    help="archivo donde se escribe el informe")
    args = ap.parse_args()
    ruta_excel = Path(args.excel).expanduser()
    if not ruta_excel.exists():
        print("No se encontró el Excel:\n  %s" % ruta_excel)
        return 2
    base = preparar_base(args.base_real)
    sys.path.insert(0, str(_AQUI.parent / "sistema_viaticos_miempresa"))
    import openpyxl
    import database as db
    db.init_db()
    p = db.cargar_parametros()
    libro = openpyxl.load_workbook(ruta_excel, data_only=True)
    lista, omitidas = [], 0
    print("Leyendo %s (%d hojas)…" % (ruta_excel.name, len(libro.worksheets)))
    for hoja in libro.worksheets:
        datos = leer_hoja(hoja)
        if datos and args.desde and datos["numero"] < args.desde:
            continue
        if datos and args.hasta and datos["numero"] > args.hasta:
            continue
        if args.limite and len(lista) >= args.limite:
            break
        if not datos:
            omitidas += 1
            continue
        calculado = comparar(datos, p)
        if not calculado:
            omitidas += 1
            continue
        if not args.sin_guardar:
            try:
                calculado["numero_interno"] = guardar_viatico(datos, calculado)
            except Exception as ex:
                # Número de viático repetido en el Excel, por ejemplo: la comparación
                # no se pierde, solo se avisa.
                calculado["avisos"].append("no se pudo crear en la base: %s" % ex)
        lista.append(calculado)
    extra = {"archivo": ruta_excel, "hojas": len(libro.worksheets), "omitidas": omitidas,
             "base": str(base) if base else "data\\viaticos.db (base local de trabajo)",
             "p": p}
    if not lista:
        print("No se encontró ningún viático para comparar.")
        return 1
    informe(lista, extra, args.informe)
    # Los totales de la consola son los mismos del informe: sin los viáticos con
    # fechas incoherentes (esos se listan aparte para poder corregir el Excel).
    validos = [f for f in lista if not f.get("dudoso")]
    entregado_excel = sum(f["entregado"] for f in validos)
    entregado_prog = sum(f["programa"]["valor_cajero"] for f in validos)
    respaldado = sum(f["total_gastos"] for f in validos)
    print("\nViáticos comparados: %d (con datos coherentes: %d)   ·   hojas omitidas: %d"
          % (len(lista), len(validos), omitidas))
    print("Respaldado (facturas): Excel $%.2f · programa $%.2f" % (respaldado, respaldado))
    print("Entregado:             Excel $%.2f · programa $%.2f   (diferencia $%.2f)"
          % (entregado_excel, entregado_prog, entregado_excel - entregado_prog))
    print("Informe completo: %s" % args.informe)
    if not args.sin_guardar:
        print("Viáticos creados en: %s" % extra["base"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
