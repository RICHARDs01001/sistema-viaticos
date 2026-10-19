# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
# -*- coding: utf-8 -*-
"""tiempos_de_viaje.py — Llena las HORAS de viaje de los cantones (Cuenca → cantón).

Usa dos servicios libres de OpenStreetMap (**sin claves ni tarjeta de crédito**):
  * **Nominatim** para ubicar cada cantón (nombre + provincia = certero).
  * **OSRM** para la duración real de la ruta **en auto**.

Regla de la empresa: la duración se **redondea hacia arriba a la hora entera**
(Cuenca–Girón 49 min → 1 h; Cuenca–Guayaquil 3 h 30 → 4 h).

**No toca los km**: guarda solo las horas, con el km que ya tiene cada cantón
(así no se altera el cálculo del combustible). Y deja un **cuadro de control** con
los km de OSRM al lado de los km registrados, para detectar un cantón mal ubicado.

Uso:
    python herramientas\\tiempos_de_viaje.py --simular              no guarda: solo el cuadro
    python herramientas\\tiempos_de_viaje.py --simular --limite 8   prueba con 8 cantones
    python herramientas\\tiempos_de_viaje.py --servidor 192.168.22.123
    python herramientas\\tiempos_de_viaje.py --solo GIRON           un solo cantón

Los cantones que ya tienen horas NO se vuelven a consultar. Así, si la corrida se corta (se
cayó el internet, una isla sin carretera), basta con volver a correr el mismo comando: sigue
solo con los que faltan. Con --forzar se revisan otra vez todos (sirve para rehacer el cuadro
de control completo), pero **las horas que midió la empresa nunca se pisan**.

Cuadro de control:  herramientas\\tiempos_de_viaje.txt

Sistema de Viáticos Miempresa
Autor: Richard Esteban Salazar Guillén · richards0101789@gmail.com · +593 981239086
"""
import argparse
import io
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(RAIZ, "sistema_viaticos_miempresa")
sys.path.insert(0, APP)
os.chdir(APP)

CUENCA = (-79.0045, -2.9006)                 # coordenadas del centro de Cuenca
CORREO = "richards0101789@gmail.com"         # contacto obligatorio para Nominatim
AGENTE = "SistemaViaticos-Miempresa/1.0 (%s)" % CORREO
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org/route/v1/driving/%f,%f;%f,%f?overview=false"

SALIDA = os.path.join(RAIZ, "herramientas", "tiempos_de_viaje.txt")

# Nombres que en la tabla están escritos distinto a como los conoce el mapa:
# se busca con el nombre correcto, pero la hora se guarda en el nombre que ya
# existe en la base (así no hay que renombrar nada ni tocar los viáticos).
ALIAS = {"CHORDALEG": "CHORDELEG"}


class SinRuta(Exception):
    """El servicio no puede calcular la ruta (ej. Galápagos: no hay carretera)."""


class SinRespuesta(Exception):
    """El servicio no respondió (se cayó el internet o el servidor está ocupado)."""


def pedir(url, pausa=0.0, intentos=3):
    """Pide una URL y devuelve el JSON. Reintenta solo si el servicio está ocupado.

    Con el agente y la pausa que piden los servicios de OpenStreetMap. Si el
    servidor responde «consulta no válida» (400) levanta SinRuta; si no responde
    después de varios intentos levanta SinRespuesta (problema de internet).
    """
    espera = 2.0
    for intento in range(1, intentos + 1):
        if pausa:
            time.sleep(pausa)
        pet = urllib.request.Request(url, headers={"User-Agent": AGENTE,
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(pet, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as ex:
            if ex.code == 400:              # OSRM: «NoRoute» (imposible llegar en auto)
                raise SinRuta("consulta rechazada (400)")
            if ex.code not in (429, 500, 502, 503, 504) or intento == intentos:
                raise SinRespuesta("el servidor respondió %s" % ex.code)
        except (urllib.error.URLError, TimeoutError, ValueError) as ex:
            if intento == intentos:
                raise SinRespuesta("no hubo respuesta: %s" % str(ex)[:60])
        print(" (reintento %d)" % intento, end="", flush=True)
        time.sleep(espera)
        espera = min(espera * 2, 30.0)
    return {}


def geocodificar(canton, provincia):
    """(lat, lon) del cantón o None. Se busca «cantón, provincia, Ecuador».

    Devuelve (None, motivo) si no se lo encontró y levanta SinRespuesta si el
    servicio no responde (internet).
    """
    consulta = ", ".join([x for x in (ALIAS.get(canton.upper(), canton).title(),
                                      provincia.title(), "Ecuador") if x])
    url = (NOMINATIM + "?" + urllib.parse.urlencode(
        {"q": consulta, "format": "json", "limit": 1, "countrycodes": "ec"}))
    try:
        datos = pedir(url, pausa=1.1)          # 1 consulta por segundo: norma del servicio
    except SinRuta:
        return None, "el servicio rechazó la consulta"
    if not datos:
        return None, "no se encontró"
    return (float(datos[0]["lat"]), float(datos[0]["lon"])), datos[0].get("display_name", "")[:60]


def ruta_auto(destino):
    """(segundos, metros, motivo) de la ruta Cuenca → destino en auto.

    Devuelve (None, None, motivo) cuando no existe ruta en auto (por ejemplo una
    isla); si el servicio no responde levanta SinRespuesta.
    """
    url = OSRM % (CUENCA[0], CUENCA[1], destino[1], destino[0])
    try:
        datos = pedir(url, pausa=0.2)
    except SinRuta:
        return None, None, "no hay ruta en auto (zona insular o sin carretera)"
    if datos.get("code") != "Ok" or not datos.get("routes"):
        return None, None, "el servidor no encontró una ruta"
    return datos["routes"][0]["duration"], datos["routes"][0]["distance"], ""


def main():
    ap = argparse.ArgumentParser(description="Horas de viaje Cuenca → cantón (OSRM, sin claves).")
    ap.add_argument("--simular", action="store_true", help="no guarda nada: solo el cuadro")
    ap.add_argument("--limite", type=int, default=0, help="probar solo con N cantones")
    ap.add_argument("--solo", default="", help="un cantón (ej. GIRON)")
    ap.add_argument("--servidor", default="", help="IP del servidor central (ej. 192.168.22.123)")
    ap.add_argument("--forzar", action="store_true",
                    help="volver a consultar también los que ya tienen horas "
                         "(las medidas por la empresa nunca se pisan)")
    op = ap.parse_args()

    if op.servidor:                      # escribir/leer en la base CENTRAL, no en la local
        os.environ["VIATICOS_MOTOR"] = "postgres"
        os.environ["VIATICOS_PG_HOST"] = op.servidor
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    import configuracion as cfg
    import database as db

    print("=" * 78)
    print("  Tiempos de viaje Cuenca → cantón · " + cfg.describir()[:60])
    print("  Modo: %s" % ("SIMULACIÓN (no guarda)" if op.simular else "GUARDAR en la base"))
    print("=" * 78)

    actuales = {str(d["canton"]).strip().upper(): d for d in db.listar_distancias()}
    # Los destinos que ya tienen el tiempo de la empresa —los del documento revisado y lo
    # que ella dejó puesto a mano: van en azul en el Excel— no se pisan: ni con --forzar
    # se les cambia la hora.
    medidos = {str(c).strip().upper() for c in db.HORAS_CUENCA}
    cantones = lista_cantones()
    if op.solo:
        cantones = [c for c in cantones if op.solo.upper() in c[0].upper()]
    if op.limite:
        cantones = cantones[:op.limite]
    print("  Cantones a revisar: %d\n" % len(cantones))

    salida = io.open(SALIDA, "w", encoding="utf-8")
    salida.write("TIEMPOS DE VIAJE (Cuenca → cantón) — OSRM/Nominatim de OpenStreetMap\n")
    salida.write("Regla: el recorrido se redondea HACIA ARRIBA a la hora entera.\n")
    salida.write("La columna «km OSRM» sirve de control: si se aleja mucho del km\n")
    salida.write("registrado, ese cantón puede haber quedado mal ubicado.\n\n")
    salida.write("%-26s %-14s %9s %9s %7s %6s %6s %s\n"
                 % ("CANTÓN", "PROVINCIA", "km reg.", "km OSRM", "dif.", "OSRM h",
                    "km/70 h", "GUARDADO"))
    salida.write("-" * 100 + "\n")

    guardados = sin_ubicar = con_horas = km_raro = sin_red = omitidos = reservados = 0
    sin_consultar = []
    for i, (canton, provincia, km) in enumerate(cantones, 1):
        fila = actuales.get(canton.upper())
        if fila and fila.get("horas") and not op.forzar:
            # Ya tiene horas (medidas por la empresa o cargadas en una corrida anterior):
            # no se vuelve a consultar el mapa.
            omitidos += 1
            salida.write("%-26s %-14s %9.1f %9s %7s %6.1f %6s ya tenía horas\n"
                         % (canton[:26], provincia[:14], km, "-", "-",
                            float(fila["horas"]), "-"))
            continue
        print("  [%3d/%3d] %-24s %-14s ..." % (i, len(cantones), canton[:24], provincia[:14]),
              end="", flush=True)
        try:
            punto, nota = geocodificar(canton, provincia)
            segundos, metros, motivo = ruta_auto(punto) if punto else (None, None, "")
        except SinRespuesta as ex:          # se cayó el internet: se avisa y se continúa
            sin_red += 1
            sin_consultar.append(canton)
            salida.write("%-26s %-14s %9.1f %9s %7s %6s %6s SIN CONSULTAR (%s)\n"
                         % (canton[:26], provincia[:14], km, "-", "-", "-", "-",
                            str(ex)[:40]))
            print(" sin consultar (%s)" % str(ex)[:40])
            continue
        if not punto:
            sin_ubicar += 1
            salida.write("%-26s %-14s %9.1f %9s %7s %6s %6s SIN UBICAR (%s)\n"
                         % (canton[:26], provincia[:14], km, "-", "-", "-", "-", nota))
            print(" sin ubicar (%s)" % nota)
            continue
        if segundos is None:
            sin_ubicar += 1
            salida.write("%-26s %-14s %9.1f %9s %7s %6s %6s SIN RUTA (%s)\n"
                         % (canton[:26], provincia[:14], km, "-", "-", "-", "-", motivo))
            print(" sin ruta (%s)" % motivo)
            continue
        # Menos de media hora es «moverse dentro de la ciudad»: no hay tiempo de viaje
        # (si no, Cuenca como destino daría 1 h).
        horas_osrm = (0 if segundos < 1800
                      else max(1, int(math.ceil(segundos / 3600.0 - 1e-9))))
        horas_km = (max(1, int(math.ceil(km / 70.0 - 1e-9))) if km > 0 else 0)
        km_osrm = round(metros / 1000.0, 1)
        dif = (abs(km_osrm - km) / km * 100.0) if km > 0 else 0.0
        aviso = ""
        if km > 0 and dif > 40:
            km_raro += 1
            aviso = "  <-- revisar (km muy distinto)"
        if fila is None:
            hecho = "no (no está en la tabla)"          # ese cantón no está en la tabla
        elif canton.upper() in medidos and fila.get("horas"):
            hecho = "empresa: %.1f h (no se toca)" % float(fila["horas"])
            reservados += 1
        elif not op.simular:
            db.set_distancia(canton, fila["km"] or km_osrm, horas_osrm)
            hecho = "sí"
            guardados += 1
        else:
            hecho = "sí (simulado)"
        con_horas += 1
        salida.write("%-26s %-14s %9.1f %9.1f %6.0f%% %6d %6d %s%s\n"
                     % (canton[:26], provincia[:14], km, km_osrm, dif, horas_osrm,
                        horas_km, hecho, aviso))
        print(" %s → %d h%s" % (canton[:20], horas_osrm,
                                "" if hecho in ("sí", "sí (simulado)") else "  [%s]" % hecho))
        salida.flush()          # el cuadro se va guardando línea por línea

    salida.write("-" * 100 + "\n")
    salida.write("Cantones con horas calculadas: %d · guardados: %d · sin ubicar/sin ruta: %d\n"
                 % (con_horas, guardados, sin_ubicar))
    salida.write("Cantones que ya tenían horas y no se volvieron a consultar: %d\n" % omitidos)
    salida.write("Horas que midió la empresa (no se tocan): %d\n" % reservados)
    if sin_red:
        salida.write("SIN CONSULTAR por problemas de red: %d (%s)\n"
                     % (sin_red, ", ".join(sin_consultar[:14])))
        salida.write("  Vuelva a correr el mismo comando: sigue solo con los que faltan.\n")
    salida.write("Cantones con km de OSRM muy distinto al registrado (>40%%): %d\n" % km_raro)
    salida.write("\nSistema de Viáticos Miempresa\n")
    salida.write("Autor: Richard Esteban Salazar Guillén · richards0101789@gmail.com"
                 " · +593 981239086\n")
    salida.close()

    print("\n" + "=" * 78)
    print("  Cuadro de control: %s" % SALIDA)
    print("  Con horas calculadas: %d · guardados: %d · sin ubicar/sin ruta: %d"
          % (con_horas, guardados, sin_ubicar))
    print("  Ya tenían horas (no se consultaron): %d" % omitidos)
    print("  Horas que midió la empresa (no se tocan): %d" % reservados)
    if sin_red:
        print("  SIN CONSULTAR por problemas de red: %d  <-- vuelva a correr el mismo comando"
              % sin_red)
    print("  Km de OSRM muy distinto al registrado (>40%%): %d" % km_raro)
    print("=" * 78)
    return 0


def lista_cantones():
    """[(cantón, provincia, km)] desde la base configurada."""
    import bd
    with bd.conectar() as c:
        filas = c.execute("SELECT c.nombre AS canton, p.nombre AS provincia, d.km AS km "
                          "FROM cantones c JOIN provincias p ON p.id = c.provincia_id "
                          "LEFT JOIN distancias d ON d.canton = c.nombre "
                          "ORDER BY p.nombre, c.nombre").fetchall()
    return [(str(f["canton"]).strip(), str(f["provincia"] or "").strip(),
             float(f["km"] or 0)) for f in filas]


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
