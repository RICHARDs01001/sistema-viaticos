# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""comparar_reglas_excel.py — Regla contra regla con el Excel nuevo de viáticos.

El formato nuevo de la empresa (`VIATICO 2 2026.xlsx`) ya trae las columnas
calculadas por día (Desayuno, Almuerzo, Merienda, Taxi salida, Taxi regreso,
Hospedaje, Agua, Combustible, TOTAL VIÁTICOS y VALOR A RETIRAR EN CAJERO), así que
con él sí se puede comparar **regla contra regla** con el programa:

  1. las tarifas y las horas límite de la hoja «Parámetros» contra los parámetros
     del sistema;
  2. viático por viático: lo que calcula el programa con las reglas nuevas
     (`calculos.py`) contra las columnas calculadas del Excel.

    python herramientas\\comparar_reglas_excel.py
    python herramientas\\comparar_reglas_excel.py "C:\\ruta\\VIATICO 2 2026.xlsx"

El informe queda en `documentacion\\COMPARACION_REGLAS_NUEVO_EXCEL.md`.
"""
import os
import sys
from datetime import date
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
MOTOR = os.environ.setdefault("VIATICOS_MOTOR", "sqlite")


def preparar_base():
    """Deja el sistema en modo LOCAL y con su propia base de prueba.

    **Nunca** se conecta a la base central: la comparación solo lee los parámetros del
    propio programa y calcula; así no se toca nada del servidor ni los datos de
    trabajo. Devuelve la ruta de la base que se usó.
    """
    destino = _AQUI / "prueba_excel" / "data_reglas"
    destino.mkdir(parents=True, exist_ok=True)
    os.environ["VIATICOS_MOTOR"] = "sqlite"
    os.environ["VIATICOS_DATA"] = str(destino)
    os.environ["VIATICOS_RESPALDOS"] = "carpeta"
    return destino / "viaticos.db"

# Nuestra columna de parámetros para cada concepto de la hoja «Parámetros».
EQUIVALENCIAS = {
    "desayuno": ("valor_desayuno", "hora_limite_desayuno", "06:00"),
    "almuerzo": ("valor_almuerzo", "hora_limite_almuerzo", "13:00"),
    "merienda": ("valor_merienda", "hora_limite_merienda", "20:00"),
    "taxi de salida": (None, "hora_limite_taxi_salida", "06:00"),
    "taxi de regreso": (None, "hora_limite_taxi_regreso", "21:00"),
    "hospedaje": ("valor_hospedaje", None, None),
    "agua": ("valor_agua", None, None),
    "combustible": ("valor_combustible_km", None, None),
    "parqueadero": ("valor_parqueadero_peaje", None, None),
    "redondeo": ("redondeo_cajero", None, None),
}
# Valor de cada taxi (en el Excel van en dos filas «Taxi salida - valor»).
VALOR_TAXI = {"taxi de salida": "valor_taxi_salida", "taxi de regreso": "valor_taxi_regreso"}


def _txt(valor):
    return "" if valor is None else str(valor).strip()


def _num(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("$", "").replace(" ", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _hora(valor):
    texto = _txt(valor)
    if isinstance(valor, (int, float)) or texto.endswith(":00"):
        pass
    partes = texto.split(":")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1][:2].isdigit():
        return "%02d:%02d" % (int(partes[0]), int(partes[1][:2]))
    return None


def leer_parametros_excel(ruta):
    """Tarifas y horas límite de la hoja «Parámetros» del Excel nuevo."""
    import openpyxl
    libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    hoja = None
    for candidata in libro.worksheets:
        if "PAR" in candidata.title.upper():
            hoja = candidata
            break
    if hoja is None:
        return {}
    filas = list(hoja.iter_rows(values_only=True))
    datos = {}
    for fila in filas[3:]:
        concepto = _txt(fila[0] if len(fila) > 0 else "")
        detalle = _txt(fila[1] if len(fila) > 1 else "")
        valor = fila[2] if len(fila) > 2 else None
        if not concepto:
            continue
        clave = concepto.lower()
        if "hora" in clave or "límite" in clave or "limite" in clave:
            datos.setdefault(clave, {})["hora"] = _hora(valor)
        elif "valor" in clave or "por día" in clave or "por noche" in clave or "km" in clave:
            datos.setdefault(clave, {})["valor"] = _num(valor)
        elif "redondeo" in clave:
            datos.setdefault(clave, {})["valor"] = _num(valor)
        elif "parqueadero" in clave:
            datos.setdefault(clave, {})["valor"] = _num(valor)
        datos.setdefault(clave, {})["detalle"] = detalle
    return datos


def buscar(datos, parte):
    """Junta las filas del Excel que hablan de ese concepto (el valor y la hora).

    En la hoja «Parámetros» cada concepto ocupa dos filas («hora límite» y «valor por
    día»), así que se unen en una sola ficha para poder comparar las dos cosas.
    """
    unido, encontrada = {}, None
    for clave, valores in datos.items():
        if parte in clave:
            encontrada = encontrada or clave
            for campo, valor in valores.items():
                if valor is not None and unido.get(campo) is None:
                    unido[campo] = valor
    return encontrada, unido


def leer_filas_excel(ruta, max_filas=400):
    """Filas de viático de las hojas semanales (una fila por persona).

    Devuelve [(hoja, número_fila, datos)] con los valores que ya calcula el Excel.
    """
    import openpyxl
    libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    filas = []
    for hoja in libro.worksheets:
        titulo = hoja.title.upper()
        if any(p in titulo for p in ("PAR", "LISTA", "NOTA", "HOJA")):
            continue
        for numero, fila in enumerate(hoja.iter_rows(values_only=True), start=1):
            if numero > max_filas or len(fila) < 25:
                continue
            nombre = _txt(fila[1])
            salida = fila[3]
            total = _num(fila[23])
            if not nombre or not isinstance(salida, date) or not total:
                continue
            if "NOMBRE" in nombre.upper() or "TOTALES" in _txt(fila[0]).upper():
                continue
            filas.append((hoja.title, numero, {
                "numero": _num(fila[0]) or 0, "empleado": nombre.upper(),
                "lugar": _txt(fila[2]).upper(),
                "fecha_salida": salida, "hora_salida": fila[4],
                "fecha_regreso": fila[5], "hora_regreso": fila[6],
                "fecha_llegada": fila[7], "hora_llegada": fila[8],
                "fecha_salida_trabajo": fila[9], "hora_salida_trabajo": fila[10],
                "dias": _num(fila[11]) or 0, "km": _num(fila[12]) or 0.0,
                "desayuno": _num(fila[13]) or 0.0, "almuerzo": _num(fila[14]) or 0.0,
                "merienda": _num(fila[15]) or 0.0, "taxi_salida": _num(fila[16]) or 0.0,
                "taxi_regreso": _num(fila[17]) or 0.0, "hospedaje": _num(fila[18]) or 0.0,
                "agua": _num(fila[19]) or 0.0, "combustible": _num(fila[20]) or 0.0,
                "transporte": _num(fila[21]) or 0.0,
                "peaje": _num(fila[22]) or 0.0, "total": total,
                "cajero": _num(fila[24]) or 0.0}))
    return filas


def comparar_fila(datos, p, CAL):
    """Calcula con el programa la misma fila del Excel. None si le faltan fechas."""
    salida, regreso = datos["fecha_salida"], datos["fecha_regreso"]
    if not isinstance(salida, date) or not isinstance(regreso, date):
        return None
    v = CAL.DatosViaje(
        nombre_empleado=datos["empleado"], lugar_trabajo=datos["lugar"] or "—",
        fecha_salida=salida, hora_salida=CAL.hora_limite(datos["hora_salida"]),
        fecha_regreso=regreso, hora_regreso=CAL.hora_limite(datos["hora_regreso"]),
        fecha_llegada_trabajo=(datos["fecha_llegada"]
                               if isinstance(datos["fecha_llegada"], date) else salida),
        hora_llegada_trabajo=CAL.hora_limite(datos["hora_llegada"]),
        fecha_salida_trabajo=(datos["fecha_salida_trabajo"]
                              if isinstance(datos["fecha_salida_trabajo"], date) else regreso),
        hora_salida_trabajo=CAL.hora_limite(datos["hora_salida_trabajo"]),
        km_recorridos=datos["km"], parqueadero_peaje=datos["peaje"], otros=0.0,
        combustible_efectivo=0.0)
    r = CAL.calcular(v, p)
    r["delta_total"] = round(datos["total"] - r["total"], 2)
    r["delta_cajero"] = round(datos["cajero"] - r["valor_cajero"], 2)
    r["noches"] = CAL.noches_de_hospedaje(v)
    return r


def _f(valor):
    return "%.2f" % float(valor or 0)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else str(
        _AQUI.parent.parent / "VIATICO 2 2026.xlsx")
    ruta_excel = Path(ruta).expanduser()
    if not ruta_excel.exists():
        print("No se encontró el Excel:\n  %s" % ruta_excel)
        return 2
    base = preparar_base()
    sys.path.insert(0, str(_AQUI.parent / "sistema_viaticos_miempresa"))
    import database as db
    import calculos as CAL
    db.init_db()
    p = db.cargar_parametros()
    en_excel = leer_parametros_excel(ruta_excel)
    filas = leer_filas_excel(ruta_excel)

    L = []
    ap = L.append
    ap("# Regla contra regla: Excel nuevo de viáticos vs. el programa")
    ap("")
    ap("| Dato | Valor |")
    ap("|---|---|")
    ap("| Archivo leído | `%s` |" % ruta_excel)
    ap("| Filas de viático leídas | %d |" % len(filas))
    ap("| Base de parámetros usada | `%s` (local, la comparación **no** toca el servidor) |"
       % base)
    ap("| Parámetros del programa | merienda hasta %s · km $%s · redondeo $%s |"
       % (p["hora_limite_merienda"].strftime("%H:%M") if hasattr(p["hora_limite_merienda"],
                                                               "strftime") else p["hora_limite_merienda"],
          _f(p["valor_combustible_km"]), _f(p.get("redondeo_cajero", 5))))
    ap("")
    ap("## 1. Tarifas y horas límite")
    ap("")
    ap("| Concepto | Excel nuevo | Programa | ¿Igual? |")
    ap("|---|---:|---:|---|")
    for parte, (col_valor, col_hora, _) in EQUIVALENCIAS.items():
        _, valores = buscar(en_excel, parte)
        valor_excel, hora_excel = valores.get("valor"), valores.get("hora")
        valor_prog = float(p[col_valor] if col_valor else p[VALOR_TAXI[parte]])
        hora_prog = ""
        if col_hora and hasattr(p.get(col_hora), "strftime"):
            hora_prog = p[col_hora].strftime("%H:%M")
        igual = ((valor_excel is None or abs(valor_excel - valor_prog) < 0.01)
                 and (hora_excel is None or hora_excel == hora_prog))
        ap("| %s | %s%s | $%s%s | %s |"
           % (parte.title(),
              ("$" + _f(valor_excel)) if valor_excel is not None else "(vacío)",
              (" · " + hora_excel) if hora_excel else "",
              _f(valor_prog), (" · " + hora_prog) if hora_prog else "",
              "sí" if igual else "**NO**"))
    ap("")
    ap("En el Excel nuevo la hoja «Notas» añade: parqueadero/peaje de $10 fijos por")
    ap("viaje y otros gastos de $10 fijos por viaje.")
    ap("")
    ap("## 2. Viático por viático (columnas calculadas del Excel vs. el programa)")
    ap("")
    ap("| Hoja | Empleado | Días E/P | Desayuno E/P | Almuerzo E/P | Merienda E/P | Taxi E/P | Hospedaje E/P | Agua E/P | Comb. E/P | TOTAL Excel | TOTAL programa | Diferencia |")
    ap("|---|---|---|---|---|---|---|---|---|---|---:|---:|---:|")
    comparables, con_dif = 0, 0
    for hoja, _numero, datos in filas:
        r = comparar_fila(datos, p, CAL)
        if not r:
            continue
        comparables += 1
        if abs(r["delta_total"]) > 0.01:
            con_dif += 1
        ap("| %s | %s | %d/%d | %s/%s | %s/%s | %s/%s | %s/%s | %s/%s | %s/%s | %s/%s | $%s | $%s | $%s |"
           % (hoja[:16], datos["empleado"][:24], datos["dias"], r["dias_viaje"],
              _f(datos["desayuno"]), _f(r["desayuno"]),
              _f(datos["almuerzo"]), _f(r["almuerzo"]),
              _f(datos["merienda"]), _f(r["merienda"]),
              _f(datos["taxi_salida"] + datos["taxi_regreso"]),
              _f(r["taxi_salida"] + r["taxi_regreso"]),
              _f(datos["hospedaje"]), _f(r["hospedaje"]),
              _f(datos["agua"]), _f(r["agua"]),
              _f(datos["combustible"]), _f(r["combustible"]),
              _f(datos["total"]), _f(r["total"]), _f(r["delta_total"])))
    ap("")
    ap("## 3. Conclusión")
    ap("")
    ap("- Filas comparadas regla contra regla: **%d**; coinciden exactamente **%d** y"
       % (comparables, comparables - con_dif))
    ap("  tienen alguna diferencia **%d**." % con_dif)
    ap("- La diferencia que más se repite es el **hospedaje**: el Excel paga $15 por noche")
    ap("  cuando la fecha de regreso es distinta de la de salida, mientras el programa")
    ap("  cuenta las noches entre la llegada al trabajo y la salida del trabajo (por eso no")
    ap("  cobra hotel en salidas de madrugada ni en viajes que vuelven el mismo día).")
    ap("- También aparecen días cobrados de más en el Excel (comidas del día de salida o de")
    ap("  llegada que su propia hoja «Notas» dice que no corresponden).")
    ap("- De dónde salen las diferencias (lo que hay que decidir con la empresa):")
    ap("  1. **Hora límite de la merienda**: el formato nuevo paga merienda hasta las 21:00")
    ap("     y el programa hasta las 20:00 (se cambia en Parámetros). Un regreso a las")
    ap("     20:30 cobra merienda en el Excel y no en el programa.")
    ap("  2. **Hospedaje**: el Excel lo paga por noche cuando el regreso es de otro día;")
    ap("     el programa cuenta las noches entre la llegada al trabajo y la salida del")
    ap("     trabajo (más fino: si llega de madrugada y sale el mismo día, no hay hotel).")
    ap("  3. **Parqueadero/peaje y otros**: el Excel paga $10 fijos por viaje; el programa")
    ap("     solo paga lo que se registre en el viático.")
    ap("  4. **Días de viaje**: el Excel los escribe a mano y el programa los cuenta con")
    ap("     las fechas de salida y regreso.")
    ap("  5. **Redondeo del cajero**: en la hoja de parámetros del Excel está vacío; el")
    ap("     programa redondea hacia arriba al múltiplo de $5 (editable).")
    ap("")
    ap("Para que las dos partes coincidan: ponga en el sistema la hora límite de la")
    ap("merienda y el redondeo que usa la empresa, y registre el parqueadero/peaje de")
    ap("cada viaje en el viático.")
    ap("")

    destino = _AQUI.parent / "documentacion" / "COMPARACION_REGLAS_NUEVO_EXCEL.md"
    destino.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:26]))
    print("\nFilas comparadas: %d · con diferencias: %d" % (comparables, con_dif))
    print("Informe completo: %s" % destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
