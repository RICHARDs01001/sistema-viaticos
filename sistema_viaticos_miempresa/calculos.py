# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""calculos.py — Reglas de cálculo idénticas al Excel oficial."""
import math
from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass
class DatosViaje:
    nombre_empleado: str
    lugar_trabajo: str
    fecha_salida: date
    hora_salida: time
    fecha_regreso: date
    hora_regreso: time
    fecha_llegada_trabajo: Optional[date] = None
    hora_llegada_trabajo: Optional[time] = None
    fecha_salida_trabajo: Optional[date] = None
    hora_salida_trabajo: Optional[time] = None
    km_recorridos: float = 0.0
    parqueadero_peaje: float = 0.0
    otros: float = 0.0
    combustible_efectivo: float = 0.0   # si >0, se usa en lugar de km*tarifa


def redondear_cajero(total, multiplo):
    """Redondeo del cajero: **siempre hacia arriba** al siguiente múltiplo.

    Es el `CEILING` del Excel: con múltiplo 5, 51 → 55 y 56 → 60 (y 55 se queda en 55).
    El viático lo usa **una sola vez**, sobre el total de todo el viático: lo que hace el
    sistema está en `cajero_del_grupo`.
    """
    if not multiplo or multiplo <= 0:
        return round(total, 2)
    return math.ceil(total / multiplo - 1e-9) * multiplo


def dias_de_viaje(v: "DatosViaje") -> int:
    """Días de calendario que abarca el viaje (el de salida y el de regreso cuentan).

    Es el `=MAX(FechaRegreso-FechaSalida+1;1)` de la columna «Días de Viaje» del Excel.
    """
    return max((v.fecha_regreso - v.fecha_salida).days + 1, 1)


def hora_limite(valor, por_defecto=time(0, 0)) -> time:
    """Hora límite escrita en los parámetros (HH:MM, como texto o como hora)."""
    if isinstance(valor, time):
        return valor
    try:
        h, m = str(valor).split(":")
        return time(int(h), int(m))
    except Exception:
        return por_defecto


def horas_texto(horas, sufijo=True):
    """Horas de viaje como se leen: «5 h 40 min» (y «5:40» si `sufijo=False`).

    Las horas de viaje se **guardan en decimal** (5.67 = 4 h 40 + 1 h de margen), pero en
    la pantalla eso se ve raro (parece un error), así que lo que se muestra al usuario es
    el tiempo de verdad: 5.67 → «5 h 40 min». Devuelve "" si no hay dato.
    """
    if horas in (None, ""):
        return ""
    try:
        total = int(round(float(horas) * 60))
    except (TypeError, ValueError):
        return ""
    if total <= 0:
        return ""
    h, m = divmod(total, 60)
    return "%d:%02d" % (h, m) if not sufijo else "%d h %02d min" % (h, m)


def horas_de_texto(texto):
    """Horas decimales de lo que se escriba: «5:40», «5h40», «5,5» o «5.5».

    Es la vuelta de `horas_texto`: en Parámetros → Rutas se pueden escribir las horas
    como se lean (el sistema las confirma en pantalla) y aquí quedan en decimal, que es
    como las usa el cálculo. None si está vacío o no se entiende.
    """
    if texto is None:
        return None
    limpio = str(texto).strip().lower().replace(",", ".")
    if not limpio:
        return None
    if ":" in limpio or "h" in limpio:
        partes = [p for p in limpio.replace("min", "").replace("h", ":")
                  .replace(" ", "").split(":") if p]
        if not partes:
            return None
        try:
            minutos = int(partes[1]) if len(partes) > 1 else 0
            return int(partes[0]) + minutos / 60.0
        except ValueError:
            return None
    try:
        return float(limpio)
    except ValueError:
        return None


def _numero(valor, por_defecto=0.0) -> float:
    """Número de un parámetro (en bases viejas puede venir como texto)."""
    if valor in (None, ""):
        return float(por_defecto or 0)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return float(por_defecto or 0)


def _activado(p: dict, clave: str, por_defecto=0.0) -> bool:
    """Parámetro de sí/no (1 = activado, 0 = apagado) de la tabla de parámetros."""
    valor = p.get(clave)
    if valor in (None, ""):
        valor = por_defecto
    return _numero(valor) > 0


def cajero_del_grupo(filas, p):
    """Valor a retirar en cajero del viático: **un solo redondeo sobre el total**.

    El retiro del cajero lo hace **una sola persona** (el encargado) y lleva el dinero de
    todo el grupo, así que lo que se retira es el **total del viático** redondeado hacia
    arriba al múltiplo del parámetro (5 de fábrica). Antes se redondeaba la cuenta de
    **cada viajero por separado** y la suma salía más alta que el total: en un viático de
    tres personas (183 + 116 + 116 = **415**) el redondeo por persona daba 185 + 120 + 120
    = **425**, o sea $10 más de lo que en realidad se retiró (y la justificación mostraba
    un «entregado» que no era el entregado).

    El valor queda en la fila del **encargado** (la primera de la lista, que es como las
    arma la pantalla de viáticos) y las demás en cero, para que la columna CAJERO —y todo
    lo que la suma: la vista previa, el PDF, la justificación y el historial— muestre
    exactamente el dinero retirado. Devuelve ese valor.
    """
    if not filas:
        return 0.0
    total = round(sum(float(f.get("total") or 0) for f in filas), 2)
    valor = redondear_cajero(total, _numero(p.get("redondeo_cajero"), 5))
    for i, fila in enumerate(filas):
        fila["valor_cajero"] = valor if i == 0 else 0.0
    return valor


def comida_dias(v: "DatosViaje", p: dict, clave_valor: str, clave_limite: str,
                extremo: str) -> float:
    """Comida (desayuno, almuerzo o merienda) **igual que la fórmula del Excel**.

    El Excel paga `días - 1` comidas sin mirar ninguna hora y la comida que falta la
    decide con la hora de un extremo del viaje:

      - **desayuno** → la hora de **salida** de Miempresa (se paga si sale a la hora
        límite, 06:00, o antes);
      - **almuerzo** y **merienda** → la hora de **regreso** a Miempresa (se pagan si
        llega a su hora límite —13:00 y 21:00— o después).

    Así queda igual que la empresa: los días del viaje se pagan completos y solo el
    extremo (el día que sale o el día que vuelve) depende de la hora. Por eso el que
    sale a las 14:00 igual lleva el almuerzo de ese día, y el que vuelve a las 22:00
    lleva la merienda (el Excel paga merienda hasta las 21:00, no hasta las 20:00).

    Ejemplo (fórmula del Excel, Salida 30/07 23:59 → Regreso 31/07 10:00, 2 días):
    desayuno = 1×3 + 0 = 3 · almuerzo = 1×3 + 0 = 3 · merienda = 1×3 + 0 = 3.
    """
    valor = _numero(p.get(clave_valor))
    if not valor:
        return 0.0
    total = valor * (dias_de_viaje(v) - 1)
    limite = hora_limite(p.get(clave_limite))
    if extremo == "salida":
        if v.hora_salida <= limite:
            total += valor
    elif v.hora_regreso >= limite:
        total += valor
    return round(total, 2)


def noches_de_hospedaje(v: "DatosViaje", p: Optional[dict] = None) -> int:
    """Noches de hospedaje, como el Excel: `=FechaRegreso-FechaSalida`.

    Se pagan solo si el regreso es de otro día, así que un viaje de 5 días paga 4
    noches. Con el parámetro «Hospedaje por fechas» apagado se cuentan las noches
    reales (entre la llegada al trabajo y la salida del trabajo), que es lo que hacía
    antes el sistema.
    """
    if p is not None and not _activado(p, "hospedaje_por_fechas", 1):
        llegada = v.fecha_llegada_trabajo or v.fecha_salida
        salida = v.fecha_salida_trabajo or v.fecha_regreso
        return max((salida - llegada).days, 0)
    return max((v.fecha_regreso - v.fecha_salida).days, 0)


def calcular(v: DatosViaje, p: dict) -> dict:
    """Valores del viático con las mismas reglas del Excel oficial de la empresa."""
    dias = dias_de_viaje(v)
    desayuno = comida_dias(v, p, "valor_desayuno", "hora_limite_desayuno", "salida")
    almuerzo = comida_dias(v, p, "valor_almuerzo", "hora_limite_almuerzo", "regreso")
    merienda = comida_dias(v, p, "valor_merienda", "hora_limite_merienda", "regreso")
    # Taxi al SALIR: si el viaje empieza a la hora límite (06:00) o antes.
    taxi_salida = (_numero(p.get("valor_taxi_salida"))
                   if v.hora_salida <= hora_limite(p.get("hora_limite_taxi_salida")) else 0.0)
    # Taxi al VOLVER: si se termina a la hora límite (21:00) o después, como el Excel.
    # Si el superusuario activa «Taxi de regreso de madrugada» también se paga al que
    # vuelve antes de la hora límite de la mañana (regresos a las 03:00), que el Excel
    # no contempla.
    taxi_regreso = 0.0
    if (v.hora_regreso >= hora_limite(p.get("hora_limite_taxi_regreso"))
            or (_activado(p, "taxi_regreso_madrugada", 0)
                and v.hora_regreso <= hora_limite(p.get("hora_limite_taxi_salida")))):
        taxi_regreso = _numero(p.get("valor_taxi_regreso"))
    noches = noches_de_hospedaje(v, p)
    hospedaje = _numero(p.get("valor_hospedaje")) * noches
    agua = _numero(p.get("valor_agua")) * dias
    if v.combustible_efectivo > 0:
        combustible = round(v.combustible_efectivo, 2)
    else:
        combustible = round(v.km_recorridos * _numero(p.get("valor_combustible_km")), 2)
    total = round(desayuno + almuerzo + merienda + taxi_salida + taxi_regreso +
                  hospedaje + agua + combustible + v.parqueadero_peaje + v.otros, 2)
    return {
        "dias_viaje": dias, "desayuno": desayuno, "almuerzo": almuerzo,
        "merienda": merienda, "taxi_salida": taxi_salida, "taxi_regreso": taxi_regreso,
        "hospedaje": hospedaje, "agua": agua, "combustible": combustible,
        "total": total,
        # Valor a retirar en cajero de ESTA fila, tal como lo hace el formato viejo del
        # Excel (redondea la cuenta de cada viajero). El viático **no** se retira así: el
        # cajero es uno solo por viático y se redondea sobre el total, porque el retiro lo
        # hace una sola persona y lleva el dinero de todo el grupo (`cajero_del_grupo`).
        "valor_cajero": redondear_cajero(total, _numero(p.get("redondeo_cajero"), 5)),
    }

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
