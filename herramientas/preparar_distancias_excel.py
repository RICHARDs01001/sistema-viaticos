# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
# -*- coding: utf-8 -*-
"""preparar_distancias_excel.py — Pasa el Excel nuevo de distancias al del sistema.

Entrada: `sistema_viaticos_miempresa\\excel\\distancias_cuenca_cantones_ecuador.xlsx`
(el archivo que trae, por cantón: provincia, km por carretera y el tiempo en h:min).

Qué hace (no toca ni el archivo de entrada ni la base de datos):

  1. Lee los **km** y el **tiempo** de cada cantón del archivo nuevo.
  2. A los tiempos les suma el **margen** (`--margen`, por defecto **1 hora**): los
     camiones y camionetas van con carga y no andan al ritmo de un auto, así que el
     viaje se registra con ese colchón. Ejemplo: Macas 4:40 + 1 h = **5:40** → el
     sistema lo redondea hacia arriba (6 h) y le suma las comidas del camino.
  3. Iguala los **nombres de los cantones** a los que usa el sistema (los del combo
     PARÁMETROS → 🗺️ Provincias y km): «CALVAS (CARIAMANGA)» → CALVAS, «SÍGSIG» →
     SIGSIG, «CHORDELEG» → CHORDALEG, «MORONA (MACAS)» → MACAS, «LOMA…». Los cantones
     que el sistema **no** tiene se informan en el reporte y **no** se escriben: si se
     escribieran no saldrían nunca en el formulario.
  4. Escribe un Excel con el **mismo formato** del que va con el sistema
     (CANTÓN · KM DESDE CUENCA · HORAS DE VIAJE (IDA)) para cargarlo con
     PARÁMETROS → 🗺️ Provincias y km → 📥 Importar Excel.
  5. Deja un reporte con el antes/después de cada cantón y con lo que quedó fuera.
  6. Deja en `servidor\\` dos archivos `.sql` —`viaticos_distancias_NUEVO.sql` y
     `viaticos_distancias_ANTES.sql`— para cargar los mismos km y horas (o volver
     atrás) **directo en la base central del servidor** con `psql`, sin abrir el
     sistema. La cabecera de esos archivos trae el paso a paso.

La base local (`data\\viaticos.db`) solo se **lee**, para el reporte y para los modos
`--km actuales` / `--horas actuales`. El sistema en marcha **no** se toca.

Uso:
    python herramientas\\preparar_distancias_excel.py
    python herramientas\\preparar_distancias_excel.py --margen 1 --km nuevos
    python herramientas\\preparar_distancias_excel.py --km actuales --horas nuevas
    python herramientas\\preparar_distancias_excel.py --salida "C:\\ruta\\MI.xlsx"
"""
import argparse
import os
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
APP = AQUI.parent / "sistema_viaticos_miempresa"
ENTRADA = APP / "excel" / "distancias_cuenca_cantones_ecuador.xlsx"
SALIDA = APP / "excel" / "TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx"
REPORTE = AQUI / "distancias_nuevas_resultado.txt"
MARGEN = 1.0        # horas de colchón que se le suman a cada tiempo del archivo nuevo

sys.path.insert(0, str(APP))
os.environ.setdefault("VIATICOS_MOTOR", "sqlite")        # nunca el servidor

# Nombres del archivo nuevo que en el sistema se llaman de otra forma (provincia, nombre).
ALIAS = {
    ("AZUAY", "CHORDELEG"): "CHORDALEG",
    ("AZUAY", "SÍGSIG"): "SIGSIG",
    ("GUAYAS", "CORONEL MARCELINO MARIDUEÑA"): "MARCELINO MARIDUEÑA",
    ("GUAYAS", "SAN JACINTO DE YAGUACHI"): "YAGUACHI",
    ("MANABÍ", "VEINTICUATRO DE MAYO (SUCRE)"): "24 DE MAYO",
    ("MORONA SANTIAGO", "MORONA (MACAS)"): "MACAS",
    ("NAPO", "NAPO (TENA)"): "TENA",
    ("ORELLANA", "ORELLANA (EL COCA)"): "FRANCISCO DE ORELLANA",
    ("PASTAZA", "PASTAZA (PUYO)"): "PUYO",
    ("SUCUMBÍOS", "LAGO AGRIO (NUEVA LOJA)"): "NUEVA LOJA",
    ("TUNGURAHUA", "BAÑOS DE AGUA SANTA"): "BAÑOS",
}


def _texto(celda):
    """Texto limpio de una celda ('' si está vacía)."""
    return "" if celda is None else str(celda).strip()


def _sin_tildes(texto):
    """Mayúsculas sin tildes, para comparar nombres («SÍGSIG» = «SIGSIG»)."""
    t = unicodedata.normalize("NFKD", (texto or "").strip().upper())
    return "".join(c for c in t if not unicodedata.combining(c))


def _numero(celda):
    """Número de una celda (acepta 250, «250» y «250,5»)."""
    if celda is None:
        return None
    if isinstance(celda, (int, float)):
        return float(celda)
    try:
        return float(str(celda).strip().replace("$", "").replace(",", "."))
    except ValueError:
        return None


def _horas_de(celda):
    """Horas decimales de una celda «4:40», «4h40», «4.5» o un tiempo de Excel."""
    if celda is None:
        return None
    if hasattr(celda, "hour"):                        # datetime.time de Excel
        return celda.hour + getattr(celda, "minute", 0) / 60.0
    if isinstance(celda, (int, float)):
        return float(celda)
    texto = str(celda).strip().replace(",", ".")
    if not texto:
        return None
    if ":" in texto or "h" in texto.lower():
        partes = texto.lower().replace("h", ":").split(":")
        try:
            horas = int(partes[0] or 0)
            minutos = int(partes[1]) if len(partes) > 1 and partes[1] else 0
        except ValueError:
            return None
        return horas + minutos / 60.0
    try:
        return float(texto)
    except ValueError:
        return None


def leer_nuevo(ruta):
    """[(provincia, cantón, km, horas)] del Excel nuevo (columna «Tiempo (h:min)»).

    El cantón, los km y los tiempos se detectan por el encabezado (fila 5 del archivo
    de la empresa); las horas son el **tiempo de viaje sin el margen**.
    """
    import openpyxl
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    hoja = wb[wb.sheetnames[0]]
    filas = [list(f) for f in hoja.iter_rows(values_only=True)]
    wb.close()

    col_prov = col_canton = col_km = col_horas = None
    inicio = 0
    for i, fila in enumerate(filas[:30]):
        cand = {"prov": None, "canton": None, "km": None, "horas": None}
        for j, celda in enumerate(fila):
            texto = _texto(celda).upper()
            if not texto:
                continue
            if cand["prov"] is None and "PROVINCIA" in texto:
                cand["prov"] = j
            elif cand["canton"] is None and ("CANT" in texto or "CIUDAD" in texto
                                             or texto == "DESTINO"):
                cand["canton"] = j
            elif cand["km"] is None and (texto.startswith("KM") or "DISTANCIA" in texto):
                cand["km"] = j
            elif cand["horas"] is None and ("HORA" in texto or "TIEMPO" in texto):
                cand["horas"] = j
        if cand["canton"] is not None and cand["km"] is not None:
            col_prov, col_canton = cand["prov"], cand["canton"]
            col_km, col_horas = cand["km"], cand["horas"]
            inicio = i + 1
            break
    if col_canton is None:                            # sin encabezados: primeras columnas
        col_prov, col_canton, col_km, col_horas, inicio = 0, 1, 2, 3, 0

    salida = []
    for fila in filas[inicio:]:
        def celda(j, _fila=fila):
            return _fila[j] if j is not None and j < len(_fila) else None
        canton = _texto(celda(col_canton)).upper()
        if not canton or canton in ("CANTÓN", "CANTON", "CIUDAD", "DESTINO", "TOTAL"):
            continue
        km = _numero(celda(col_km))
        if km is None or km <= 0:
            continue
        horas = _horas_de(celda(col_horas)) or 0.0
        salida.append((_texto(celda(col_prov)).upper(), canton, float(km), horas))
    return salida


def cantones_sistema():
    """{(PROVINCIA, CANTÓN)} que ofrece el sistema (los del combo del formulario).

    Se leen de la base local; si este equipo no la tiene (por ejemplo el servidor recién
    instalado), se usan los de fábrica (`database.PROV_CANT`).
    """
    import sqlite3
    ruta = APP / "data" / "viaticos.db"
    if ruta.exists():
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % ruta.as_posix(), uri=True)
            pares = set((str(p).strip().upper(), str(c).strip().upper())
                        for p, c in conn.execute(
                            "SELECT p.nombre, c.nombre FROM cantones c "
                            "JOIN provincias p ON p.id=c.provincia_id"))
            conn.close()
            if pares:
                return pares
        except Exception as ex:
            print("   (no se pudo leer los cantones de la base local: %s)" % ex)
    import database as db                                  # no abre la base al importar
    return set((prov.upper(), canton.upper())
               for prov, cantones in db.PROV_CANT.items() for canton in cantones)


def valores_actuales():
    """{CANTÓN: (km, horas)} de la tabla de rutas de la base local (solo lectura)."""
    import sqlite3
    ruta = APP / "data" / "viaticos.db"
    datos = {}
    if not ruta.exists():
        return datos
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % ruta.as_posix(), uri=True)
        for canton, km, horas in conn.execute("SELECT canton, km, horas FROM distancias"):
            datos[str(canton).strip().upper()] = (
                float(km) if km is not None else None,
                float(horas) if horas is not None else None)
        conn.close()
    except Exception as ex:
        print("   (no se pudo leer la tabla de rutas: %s)" % ex)
    return datos


def igualar(prov, canton, sistema):
    """Nombre que el sistema usa para ese cantón, o None si no lo tiene.

    Se prueba en orden: el nombre tal cual, la tabla de equivalencias (`ALIAS`) y el
    nombre sin el paréntesis de la cabecera («CALVAS (CARIAMANGA)» → CALVAS), todo
    dentro de la misma provincia. Al final, sin tildes («SÍGSIG» = «SIGSIG»).
    """
    if (prov, canton) in sistema:
        return canton
    if (prov, canton) in ALIAS:
        return ALIAS[(prov, canton)]
    simple = canton.split("(")[0].strip()
    if simple and (prov, simple) in sistema:
        return simple
    for p, c in sistema:                       # último intento: sin tildes ni puntos
        if p == prov and _sin_tildes(c) == _sin_tildes(simple or canton):
            return c
    return None


def escribir(filas, destino, nota):
    """Excel con el mismo formato del que va con el sistema (cantón, km y horas).

    Los encabezados van en la fila 7 —igual que `TIEMPOS DE VIAJE MIEMPRESA.xlsx`—
    para que el botón **Importar Excel** de Parámetros → Provincias y km lo lea igual.
    """
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = openpyxl.Workbook()
    hoja = wb.active
    hoja.title = "Tiempos de viaje"
    amarillo = PatternFill("solid", fgColor="FFEB9C")
    lado = Side(style="thin", color="B7B7B7")
    borde = Border(left=lado, right=lado, top=lado, bottom=lado)

    hoja["A1"] = "TIEMPOS DE VIAJE DESDE CUENCA — MIEMPRESA (PROPUESTA)"
    hoja["A1"].font = Font(bold=True, size=13)
    hoja["A2"] = nota
    hoja["A3"] = ("Para cargarlo al sistema: PARÁMETROS → 🗺️ Provincias y km → "
                  "📥 Importar Excel.")
    hoja["A4"] = ("Revíselo antes de importar: al importar, estos cantones quedan con los km "
                  "y las horas de este archivo (los de hoy se reemplazan).")
    hoja["A5"] = ("A las horas de viaje el sistema les suma una hora por cada comida que cae "
                  "dentro del viaje (desayuno 06:00, almuerzo 13:00 y merienda 21:00) y "
                  "redondea el recorrido hacia arriba a la hora entera.")
    for fila in (2, 3, 4, 5):
        hoja.cell(row=fila, column=1).font = Font(size=9, italic=True)

    for j, titulo in enumerate(("CANTÓN", "KM DESDE CUENCA", "HORAS DE VIAJE (IDA)"), start=1):
        c = hoja.cell(row=7, column=j, value=titulo)
        c.font = Font(bold=True)
        c.fill = amarillo
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = borde
    for i, (canton, km, horas) in enumerate(filas, start=8):
        for j, valor in enumerate((canton, km, horas), start=1):
            c = hoja.cell(row=i, column=j, value=valor)
            c.border = borde
            if j > 1:
                c.alignment = Alignment(horizontal="center")
        hoja.cell(row=i, column=2).number_format = "0"
        if horas is not None:
            hoja.cell(row=i, column=3).number_format = "0.00"
    hoja.column_dimensions["A"].width = 34
    hoja.column_dimensions["B"].width = 18
    hoja.column_dimensions["C"].width = 22
    hoja.freeze_panes = "A8"
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return destino


def _hhmm(horas):
    """«5:40» de 5.67 horas (para leerlo cómodo en el reporte)."""
    total = int(round((horas or 0) * 60))
    return "%d:%02d" % (total // 60, total % 60)


def _ahora():
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M")


CABECERA_SQL = """\
-- =====================================================================
--  Sistema de Viáticos Miempresa — km y horas de viaje (rutas desde Cuenca)
--  %(titulo)s
--  Generado:       %(fecha)s
--  Archivo fuente: %(fuente)s
--  Cantones: %(cuantos)d   ·   km: %(km)s   ·   horas: %(horas)s   ·   margen %(margen)+g h
--
--  CÓMO SE USA (en el servidor, con PostgreSQL encendido):
--    1) RESPALDE PRIMERO:
--         cd C:\\MIEMPRESA_VIATICOS\\servidor
--         respaldar_base_nativo.bat miempresa 2345
--       (queda en respaldos_base\\viaticos_AAAAMMDD_HHMMSS.sql)
--    2) Cargue este archivo (los tres «set» son para no dañar tildes ni eñes):
--         chcp 65001
--         set PGPASSWORD=miempresa
--         set PGCLIENTENCODING=UTF8
--         "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" -U miempresa -h 127.0.0.1 ^
--            -p 2345 -d viaticos -v ON_ERROR_STOP=1 -f %(archivo)s
--       (ajuste la versión de PostgreSQL y el puerto a los de su servidor)
--    Más fácil todavía: en la carpeta `servidor\\` está `cargar_distancias.bat`, que
--    hace el respaldo y la carga de una sola vez (y `cargar_distancias.bat
--    viaticos_distancias_ANTES.sql` para volver atrás).
--
--  Solo toca la tabla `distancias`: los km y las horas de las rutas desde Cuenca.
--  No toca viáticos, ajustes, gastos, usuarios ni ningún otro dato.
-- =====================================================================
"""


def _sql_texto(texto):
    """Texto listo para un literal SQL (comillas simples dobladas)."""
    return "'" + str(texto).replace("'", "''") + "'"


def _sql_numero(valor):
    """Número listo para SQL (NULL si no hay dato)."""
    return "NULL" if valor is None else "%g" % float(valor)


def escribir_sql(filas, carpeta, entrada, margen, km_modo, horas_modo):
    """Escribe en `servidor\\` los dos .sql: los valores nuevos y los de antes.

    Devuelve (ruta_nuevo, ruta_antes). El de «antes» sirve para volver atrás tal como
    estaban las rutas en esta copia de la base; las filas que se agregan (que antes no
    existían) quedan anotadas en el mismo archivo para borrarlas a mano si hiciera falta.
    """
    datos = {"fecha": _ahora(), "fuente": entrada.name, "margen": margen,
             "cuantos": len(filas), "km": km_modo, "horas": horas_modo}
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    salidas = []
    for nombre, titulo, usar_antes in (
            ("viaticos_distancias_NUEVO.sql",
             "VALORES NUEVOS (km y horas del archivo de la empresa)", False),
            ("viaticos_distancias_ANTES.sql",
             "VALORES DE ANTES (para volver atrás si algo no gusta)", True)):
        datos["titulo"], datos["archivo"] = titulo, nombre
        lineas = [CABECERA_SQL % datos, "", "BEGIN;"]
        nuevos = []
        for canton, km, horas, _donde, km_hoy, horas_hoy in filas:
            if usar_antes:
                if km_hoy is None:
                    nuevos.append(canton)
                    continue
                km_fila, horas_fila = km_hoy, horas_hoy
            else:
                km_fila, horas_fila = km, horas
            lineas.append("INSERT INTO distancias (canton, km, horas) VALUES (%s, %s, %s)"
                          % (_sql_texto(canton), _sql_numero(km_fila),
                             _sql_numero(horas_fila)))
            lineas.append("  ON CONFLICT (canton) DO UPDATE SET km = EXCLUDED.km, "
                          "horas = EXCLUDED.horas;")
        if nuevos:
            lineas.append("")
            lineas.append("-- Estas rutas NO existían antes: si hay que volver atrás, bórrelas")
            lineas.append("-- descomentando la línea de abajo:")
            lineas.append("-- DELETE FROM distancias WHERE canton IN (%s);"
                          % ", ".join(_sql_texto(c) for c in nuevos))
        lineas.append("COMMIT;")
        lineas.append("")
        lineas.append("-- Comprobación: MACAS debe dar 242 y 5.67 (AZOGUES 41 y 1.75).")
        lineas.append("SELECT canton, km, horas FROM distancias "
                      "WHERE canton IN ('MACAS', 'AZOGUES') ORDER BY canton;")
        (carpeta / nombre).write_text("\n".join(lineas) + "\n", encoding="utf-8")
        salidas.append(carpeta / nombre)
    return salidas[0], salidas[1]


def main():
    p = argparse.ArgumentParser(
        description="Pasa el Excel nuevo de distancias al formato del sistema "
                    "(km del archivo y horas con margen).")
    p.add_argument("--entrada", default=str(ENTRADA), help="Excel nuevo de distancias")
    p.add_argument("--salida", default=str(SALIDA), help="Excel que se genera")
    p.add_argument("--margen", type=float, default=MARGEN,
                   help="horas que se le suman a cada tiempo del archivo (por defecto 1)")
    p.add_argument("--km", choices=("nuevos", "actuales", "faltantes"), default="nuevos",
                   help="los km del archivo nuevo, los que hoy tiene el sistema o los del "
                        "archivo solo donde hoy no hay km")
    p.add_argument("--horas", choices=("nuevas", "actuales", "faltantes"), default="nuevas",
                   help="lo mismo para las horas de viaje")
    p.add_argument("--sql-dir", default=str(AQUI.parent / "servidor"),
                   help="carpeta donde se dejan los .sql para cargar en el servidor")
    a = p.parse_args()

    entrada = Path(a.entrada).expanduser()
    if not entrada.exists():
        print("No se encontró el archivo: %s" % entrada)
        return 2

    print("Leyendo %s…" % entrada.name)
    sistema = cantones_sistema()
    actuales = valores_actuales()
    leidas = leer_nuevo(entrada)
    print("  cantones en el archivo: %d  ·  cantones que ofrece el sistema: %d"
          % (len(leidas), len(sistema)))

    filas, fuera, choques = [], [], []
    usados = {}
    for prov, canton, km_nuevo, horas_nuevo in leidas:
        destino = igualar(prov, canton, sistema)
        if destino is None:
            fuera.append((prov, canton, km_nuevo, horas_nuevo))
            continue
        km_hoy, horas_hoy = actuales.get(destino, (None, None))
        km = (km_hoy or km_nuevo) if a.km in ("actuales", "faltantes") else km_nuevo
        nuevas = round(horas_nuevo + a.margen, 2) if horas_nuevo else None
        horas = ((horas_hoy or nuevas) if a.horas in ("actuales", "faltantes") else nuevas)
        titulo = "%s · %s" % (prov.title(), canton.title())
        if destino in usados:                      # dos cantones con el mismo nombre
            choques.append((destino, usados[destino], titulo))
            continue
        usados[destino] = titulo
        filas.append((destino, km, horas, titulo, km_hoy, horas_hoy))

    filas.sort()
    nota = ("Armado con «%s»: los km son los del archivo y las horas son su tiempo (h:min) "
            "más %g h de margen, porque los camiones y camionetas van con carga y no andan "
            "al ritmo de un auto." % (entrada.name, a.margen))
    destino_excel = escribir([(f[0], f[1], f[2]) for f in filas],
                             Path(a.salida).expanduser(), nota)
    ruta_nuevo, ruta_antes = escribir_sql(filas, Path(a.sql_dir).expanduser(), entrada,
                                          a.margen, a.km, a.horas)

    provincias_raras = sorted(set(pr for pr, _c, _k, _h in leidas)
                              - set(pr for pr, _c in sistema))
    lineas = [
        "REPORTE — distancias del archivo nuevo",
        "=" * 100,
        "Archivo leído:   %s" % entrada,
        "Reporte hecho:   %s" % _ahora(),
        "Margen de tiempo: %+g h   ·   km: %s   ·   horas: %s" % (a.margen, a.km, a.horas),
        "Cantones leídos: %d   ·   escritos: %d   ·   que el sistema no tiene: %d   ·   "
        "repetidos: %d" % (len(leidas), len(filas), len(fuera), len(choques)),
        "",
        "-" * 100,
        "%-32s %14s %22s   %s" % ("CANTÓN (como lo tiene el sistema)",
                                  "KM (hoy → nuevo)", "HORAS (hoy → nuevas)", "de dónde sale"),
        "-" * 100,
    ]
    for nombre, km, horas, titulo, km_hoy, horas_hoy in filas:
        antes_km = "%g" % km_hoy if km_hoy else "—"
        antes_h = "%g" % horas_hoy if horas_hoy else "—"
        nuevo_h = "%g (%s)" % (horas, _hhmm(horas)) if horas else "—"
        lineas.append("%-32s %6s → %-6g %8s → %-12s   %s"
                      % (nombre, antes_km, km, antes_h, nuevo_h, titulo))

    if provincias_raras:
        lineas.append("")
        lineas.append("PROVINCIAS DEL ARCHIVO QUE NO ESTÁN EN EL SISTEMA: %s"
                      % ", ".join(provincias_raras))
    if choques:
        lineas.append("")
        lineas.append("CANTONES CON EL MISMO NOMBRE (el sistema guarda uno solo de los dos;")
        lineas.append("el segundo hay que ponerlo a mano en Provincias y km):")
        for destino, primero, segundo in choques:
            lineas.append("   %-26s se guardó %s  ·  quedó fuera %s"
                          % (destino, primero, segundo))
    if fuera:
        lineas.append("")
        lineas.append("-" * 100)
        lineas.append("CANTONES QUE EL SISTEMA NO TIENE (no se pudieron escribir): %d"
                      % len(fuera))
        lineas.append("Son cantones reales que no están en la lista del formulario: primero")
        lineas.append("hay que agregarlos al sistema y después volver a correr esta herramienta.")
        lineas.append("-" * 100)
        for prov, canton, km, horas in sorted(fuera):
            lineas.append("   %-44s %7g km   %s"
                          % ("%s · %s" % (prov.title(), canton.title()), km, _hhmm(horas)))
    lineas.append("")
    lineas.append("(este reporte no cambia nada: el Excel de entrada y la base quedan intactos)")

    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Excel generado: %s" % destino_excel)
    print("Para el servidor: %s   ·   %s" % (ruta_nuevo, ruta_antes))
    print("Reporte: %s" % REPORTE)
    print("Resumen: %d cantones escritos · %d fuera (el sistema no los tiene) · "
          "%d repetidos" % (len(filas), len(fuera), len(choques)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
