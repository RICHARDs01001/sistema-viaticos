# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""recalcular_cajero.py — Pone al día el «valor a retirar en cajero» de los viáticos ya
guardados con el criterio nuevo: **un solo redondeo sobre el total del viático**.

Por qué existe: hasta la versión 6.9 el programa redondeaba la cuenta de **cada viajero** al
múltiplo del cajero (5 de fábrica) y después sumaba. En un viático de tres personas
(183 + 116 + 116 = **415**) eso daba 185 + 120 + 120 = **425**: la justificación mostraba
«Entregado $425» cuando en el cajero se retiraron **$415**, porque el retiro lo hace **una
sola persona** (el encargado) y lleva el dinero de todo el grupo. Desde la versión 7.0 el
sistema redondea **una sola vez** el total del viático y deja el valor en la fila del
encargado; este programa corrige los viáticos que quedaron guardados con el valor viejo.

Qué hace, paso por paso:

1. Copia de seguridad de la base **local** (`data\\viaticos.db`, una por día).
2. Compara, viático por viático y ajuste por ajuste, el cajero guardado con el que le toca
   ahora (`calculos.cajero_del_grupo`) y muestra el cuadro con la diferencia.
3. Solo con `--aplicar` escribe el valor nuevo (sin esa opción **no toca nada**). El valor
   queda en la fila del encargado y las demás filas en cero, igual que al digitar el viático
   ahora: así todo lo que suma la columna CAJERO (pantalla, PDF, justificación e historial)
   muestra exactamente el dinero retirado.
4. Deja el cambio anotado en la bitácora.

Uso:

    python herramientas\\recalcular_cajero.py                    (solo muestra el cuadro)
    python herramientas\\recalcular_cajero.py --aplicar          (corrige los PENDIENTES)
    python herramientas\\recalcular_cajero.py --numero 148 --aplicar
    python herramientas\\recalcular_cajero.py --todas --aplicar  (incluye los justificados)

De fábrica **no toca los viáticos JUSTIFICADOS**: son historia ya cerrada y auditada, y el
dinero pudo haberse retirado con el valor viejo (redondeado). Se revisan solo con `--todas`.
**Nunca toca el servidor**: fuerza la base local (SQLite).
"""
import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
_SISTEMA = _RAIZ / "sistema_viaticos_miempresa"

# La base de este trabajo es la LOCAL (SQLite). Se fuerza por variable de entorno para que,
# aunque `config.json` apunte al servidor, este programa NUNCA escriba en la base central.
os.environ["VIATICOS_MOTOR"] = "sqlite"
sys.path.insert(0, str(_SISTEMA))

import calculos as CAL                     # noqa: E402  (después de la ruta)
import database as db                      # noqa: E402


# --------------------------------------------------------------------- utilidades
def fmt(v):
    """Valor con dos decimales, como se ve en el sistema («415.00»)."""
    return "%.2f" % float(v or 0)


def respaldar_base():
    """Copia la base local antes de escribir en ella (una por día)."""
    import configuracion as cfg
    destino = cfg.dir_datos() / "viaticos.db"
    if not destino.exists():
        return None
    copia = destino.with_name("viaticos.db.bak_%s" % date.today().strftime("%Y%m%d"))
    if copia.exists():
        return copia
    shutil.copy2(destino, copia)
    return copia


def grupos(numero=None):
    """Grupos (viático + ajuste) con lo que tienen guardado y lo que les toca ahora.

    Devuelve una lista de diccionarios con: `numero` (clave interna), `etiqueta` (N° visible),
    `ajuste`, `personas`, `total`, `cajero` (lo guardado), `cajero_nuevo` (la regla nueva),
    `diferencia` y `justificado`.
    """
    p = db.cargar_parametros()
    consulta = ("SELECT viatico_numero, COALESCE(ajuste_numero,0) ajuste, COUNT(*) personas, "
                "SUM(COALESCE(total,0)) total, SUM(COALESCE(valor_cajero,0)) cajero, "
                "MAX(estado) estado FROM viajes ")
    with db.conectar() as c:
        if numero:
            filas = c.execute(consulta + "WHERE viatico_numero=? "
                              "GROUP BY viatico_numero, ajuste ORDER BY ajuste",
                              (numero,)).fetchall()
        else:
            filas = c.execute(consulta + "GROUP BY viatico_numero, ajuste "
                              "ORDER BY viatico_numero, ajuste").fetchall()
    datos = []
    for f in filas:
        d = dict(f)
        d["etiqueta"] = db.etiqueta_numero(d["viatico_numero"])
        d["cajero_nuevo"] = CAL.redondear_cajero(round(float(d["total"] or 0), 2),
                                                 p.get("redondeo_cajero", 5))
        d["diferencia"] = round(d["cajero_nuevo"] - float(d["cajero"] or 0), 2)
        d["justificado"] = str(d.get("estado") or "").upper() == "JUSTIFICADO"
        datos.append(d)
    return datos, p


def escribir(d):
    """Deja el cajero nuevo en la fila del encargado (y las demás filas del grupo en cero).

    Es lo mismo que hace la pantalla de viáticos al guardar: el retiro lo hace una sola
    persona, así que el valor del viático vive en una sola fila y todas las sumas de la
    columna CAJERO dan el dinero retirado.
    """
    with db.conectar() as c:
        c.execute("UPDATE viajes SET valor_cajero=0 WHERE viatico_numero=? "
                  "AND COALESCE(ajuste_numero,0)=?", (d["viatico_numero"], d["ajuste"]))
        c.execute("UPDATE viajes SET valor_cajero=? WHERE id=("
                  "SELECT id FROM viajes WHERE viatico_numero=? "
                  "AND COALESCE(ajuste_numero,0)=? "
                  "ORDER BY es_encargado DESC, id LIMIT 1)",
                  (d["cajero_nuevo"], d["viatico_numero"], d["ajuste"]))


def anotar_bitacora(d, usuario="ADMINISTRACIÓN"):
    """Deja el cambio anotado en la bitácora (nunca interrumpe el programa)."""
    try:
        db.registrar_bitacora(
            usuario, "CORRIGIÓ CAJERO", "viáticos", "N° %s" % d["etiqueta"],
            "Cajero del total: %s → %s (total de %d persona(s) $%s)"
            % (fmt(d["cajero"]), fmt(d["cajero_nuevo"]), d["personas"], fmt(d["total"])))
    except Exception as ex:                     # la bitácora nunca interrumpe
        print("   (aviso: no se pudo escribir en la bitácora: %s)" % ex)


# --------------------------------------------------------------------- programa
def main():
    try:                          # tildes y símbolos correctos en la consola de Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    import configuracion as cfg

    ap = argparse.ArgumentParser(
        description="Revisa y corrige el «valor a retirar en cajero» de los viáticos ya "
                    "guardados: el redondeo es UNO solo, sobre el total del viático.")
    ap.add_argument("--aplicar", action="store_true",
                    help="escribe el valor nuevo (sin esta opción solo muestra el cuadro)")
    ap.add_argument("--numero", type=int, default=0,
                    help="revisa solo ese viático (el N° que se ve, por ejemplo 148)")
    ap.add_argument("--anio", type=int, default=date.today().year,
                    help="año del N° visible (de fábrica el año en curso)")
    ap.add_argument("--todas", action="store_true",
                    help="incluye también los viáticos JUSTIFICADOS (no se tocan de fábrica)")
    args = ap.parse_args()

    print("Base LOCAL:        %s" % (cfg.dir_datos() / "viaticos.db"))
    clave = db.clave_viatico(args.anio, args.numero) if args.numero else None
    todos, p = grupos(numero=clave)
    if not todos:
        print("No hay viáticos que revisar%s."
              % (" con el N° %s" % args.numero if args.numero else ""))
        return 0

    revisar = todos if args.todas else [d for d in todos if not d["justificado"]]
    aparte = [] if args.todas else [d for d in todos if d["justificado"]]
    malos = [d for d in revisar if abs(d["diferencia"]) > 0.004]

    print("=" * 100)
    print("VALOR A RETIRAR EN CAJERO — revisión de los viáticos ya guardados")
    print("Regla: el redondeo se hace UNA sola vez, sobre el TOTAL del viático (múltiplo de")
    print("$%s). Retira una sola persona (el encargado) y lleva el dinero de todos."
          % ("%g" % float(p.get("redondeo_cajero", 5))))
    print("=" * 100)
    print("%-12s %-10s %9s %12s %12s %12s %11s   %s"
          % ("N°", "Ajuste", "Personas", "Total", "Guardado", "Le toca", "Diferencia", "Estado"))
    print("-" * 100)
    for d in malos:
        print("%-12s %-10s %9d %12s %12s %12s %11s   %s"
              % (d["etiqueta"], "—" if not d["ajuste"] else "N° %d" % d["ajuste"],
                 d["personas"], fmt(d["total"]), fmt(d["cajero"]), fmt(d["cajero_nuevo"]),
                 "%+.2f" % d["diferencia"], d["estado"]))
    if not malos:
        print("   (ninguno: los %d viático(s)/ajuste(s) revisados ya tienen el valor correcto)"
              % len(revisar))
    print("-" * 100)
    print("Revisados: %d   ·   con el valor viejo: %d   ·   diferencia total: %s"
          % (len(revisar), len(malos), fmt(sum(d["diferencia"] for d in malos))))
    if aparte:
        print("No revisados (JUSTIFICADOS: historia cerrada, se revisan con --todas): %d — %s"
              % (len(aparte), ", ".join("N° %s" % d["etiqueta"] for d in aparte)))
    if not malos:
        return 0
    if not args.aplicar:
        print()
        print("Para corregirlos, vuelva a correr el mismo comando con  --aplicar")
        return 0

    copia = respaldar_base()
    print()
    print("Copia de seguridad: %s" % (copia if copia else "(no había base local que copiar)"))
    for d in malos:
        escribir(d)
        anotar_bitacora(d)
        print("   N° %-10s corregido: %s → %s"
              % (d["etiqueta"], fmt(d["cajero"]), fmt(d["cajero_nuevo"])))
    print()
    print("Listo: %d viático(s)/ajuste(s) al día." % len(malos))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
