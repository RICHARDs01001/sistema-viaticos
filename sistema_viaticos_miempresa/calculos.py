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
from datetime import date, datetime, time, timedelta
from typing import Optional

# Horas límite de fábrica (las mismas de `database.PARAMS_INICIALES`). Se usan cuando
# el parámetro viene vacío, mal escrito o la base es vieja. **No** se puede caer en
# `00:00`: con una hora límite en cero las dos reglas del taxi se invierten (el de
# regreso se paga siempre y el de salida no se paga nunca).
HORAS_DE_FABRICA = {
    "hora_limite_desayuno": time(6, 0),
    "hora_limite_almuerzo": time(13, 0),
    "hora_limite_merienda": time(21, 0),
    "hora_limite_taxi_salida": time(6, 0),
    "hora_limite_taxi_regreso": time(21, 0),
}

# Un regreso «de madrugada» es antes de esta hora del día (00:00–06:00). Es fija y no
# depende de la hora límite del taxi de salida: si esa se cambia (por ejemplo a las
# 09:00), el que vuelve a las 08:30 no se vuelve «madrugada».
HORA_FIN_MADRUGADA = time(6, 0)


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
    # Solo en los **ajustes**: el último día ya entregado (el regreso del original o del
    # ajuste anterior). La noche de ese día todavía **no** se pagó, así que el hospedaje
    # del ajuste se cuenta desde ahí y no desde el día siguiente. Con None se cuenta como
    # en el Excel (noches entre la salida y el regreso del propio período).
    noches_desde: Optional[date] = None


def redondear_cajero(total, multiplo):
    """Redondeo del cajero: **siempre hacia arriba** al siguiente múltiplo.

    Es el `CEILING` del Excel: con múltiplo 5, 51 → 55 y 56 → 60 (y 55 se queda en 55).
    El viático lo usa **una sola vez**, sobre el total de todo el viático: lo que hace el
    sistema está en `cajero_del_grupo`.
    """
    if not multiplo or multiplo <= 0:
        return round(total, 2)
    # El `round` final quita el ruido del punto flotante (55.00000000000001, 1234.6 + 1e-13):
    # el dinero se guarda y se muestra con dos decimales.
    return round(math.ceil(total / multiplo - 1e-9) * multiplo, 2)


def dias_de_viaje(v: "DatosViaje") -> int:
    """Días de calendario que abarca el viaje (el de salida y el de regreso cuentan).

    Es el `=MAX(FechaRegreso-FechaSalida+1;1)` de la columna «Días de Viaje» del Excel.
    """
    return max((v.fecha_regreso - v.fecha_salida).days + 1, 1)


def hora_limite(valor, por_defecto=time(0, 0)) -> time:
    """Hora límite escrita en los parámetros (HH:MM, como texto o como hora).

    Acepta lo que puede llegar de una base o de un archivo: una hora ya convertida
    (`time`), un `datetime`, `"06:00"`, `"6:00"`, `"06:00:00"` (así la devuelve
    PostgreSQL y así se escribe en Excel) y hasta un número (`21` o `21.5`). Si no se
    entiende devuelve `por_defecto`; por eso quien la llama **debe** pasar la hora de
    fábrica del parámetro (`HORAS_DE_FABRICA`) y nunca dejar el cero de `00:00`, que
    invertiría las reglas del taxi.
    """
    if isinstance(valor, time):
        return valor
    if isinstance(valor, datetime):
        return valor.time()
    try:
        partes = [x for x in str(valor).strip().replace(".", ":").split(":") if x.strip()]
        if not partes:
            return por_defecto
        h = int(partes[0])
        m = int(partes[1]) if len(partes) > 1 else 0
        return time(h, m)
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
    limite = hora_limite(p.get(clave_limite),
                         HORAS_DE_FABRICA.get(clave_limite, time(0, 0)))
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


def datos_ajuste(nombre_empleado: str, lugar_trabajo: str, ultimo_regreso: date,
                 fecha_regreso: date, hora_regreso: time,
                 fecha_llegada_trabajo: Optional[date] = None,
                 fecha_salida_trabajo: Optional[date] = None) -> DatosViaje:
    """`DatosViaje` del período que cubre un **ajuste** de viático.

    Un ajuste paga los días que todavía no se habían entregado. Empieza el día
    siguiente al **último regreso ya pagado** (`ultimo_regreso`: el del viático original
    o el del ajuste anterior) a las 00:00, y termina en la fecha y hora de regreso que
    se escriban. Con esas fechas el ajuste se calcula con las **mismas reglas del Excel
    que el original**: días de calendario, `días - 1` comidas más la del extremo,
    hospedaje por noches entre las dos fechas, agua por día y taxi de regreso según la
    hora de llegada.

    La salida a las 00:00 es solo la marca de dónde empieza el período: en un ajuste el
    viajero **ya está** en el lugar de trabajo, por eso `calcular(..., ajuste=True)` no
    paga el taxi de salida (se pagó en el viático original).

    El hospedaje se cuenta desde `ultimo_regreso` (`noches_desde`), no desde el día
    siguiente: la **noche** del último día entregado no la pagó el viático original
    (que pagó las noches hasta la anterior). Así el original más todos los ajustes pagan
    exactamente las noches que hubo entre la primera salida y el último regreso.
    """
    inicio = ultimo_regreso + timedelta(days=1)
    return DatosViaje(
        nombre_empleado=nombre_empleado, lugar_trabajo=lugar_trabajo,
        fecha_salida=inicio, hora_salida=time(0, 0),
        fecha_regreso=fecha_regreso, hora_regreso=hora_regreso,
        fecha_llegada_trabajo=fecha_llegada_trabajo or inicio,
        fecha_salida_trabajo=fecha_salida_trabajo or fecha_regreso,
        km_recorridos=0.0, parqueadero_peaje=0.0, otros=0.0,
        combustible_efectivo=0.0, noches_desde=ultimo_regreso)


def calcular(v: DatosViaje, p: dict, ajuste: bool = False) -> dict:
    """Valores del viático con las mismas reglas del Excel oficial de la empresa.

    Con `ajuste=True` (días adicionales de un viático que se alargó) **no** se paga el
    taxi de salida: el viajero ya salió en el viático original y el viaje del ajuste
    empieza a las 00:00 del día siguiente al último regreso entregado, sin traslado.

    Las horas límite que falten o no se entiendan toman su valor de fábrica
    (`HORAS_DE_FABRICA`), nunca `00:00`: con una hora límite en cero el taxi de regreso
    se pagaría en todos los viáticos y el de salida en ninguno.
    """
    dias = dias_de_viaje(v)
    desayuno = comida_dias(v, p, "valor_desayuno", "hora_limite_desayuno", "salida")
    almuerzo = comida_dias(v, p, "valor_almuerzo", "hora_limite_almuerzo", "regreso")
    merienda = comida_dias(v, p, "valor_merienda", "hora_limite_merienda", "regreso")
    # Taxi al SALIR: si el viaje empieza a la hora límite (06:00) o antes. `taxi_salida`
    # se paga una sola vez por período: en un ajuste el viajero ya salió en el original.
    limite_taxi_salida = hora_limite(
        p.get("hora_limite_taxi_salida"), HORAS_DE_FABRICA["hora_limite_taxi_salida"])
    limite_taxi_regreso = hora_limite(
        p.get("hora_limite_taxi_regreso"), HORAS_DE_FABRICA["hora_limite_taxi_regreso"])
    taxi_salida = (_numero(p.get("valor_taxi_salida"))
                   if v.hora_salida <= limite_taxi_salida else 0.0)
    if ajuste:
        taxi_salida = 0.0
    # Taxi al VOLVER: si se termina a la hora límite (21:00) o después, como el Excel.
    # Si el superusuario activa «Taxi de regreso de madrugada» también se paga al que
    # vuelve antes de las 06:00 (lo que el Excel no contempla). Una ida y vuelta en la
    # misma madrugada (sale 04:00 y vuelve 05:30) **no** es «volver de madrugada»: es el
    # mismo traslado, y el taxi de salida ya se pagó. En un ajuste la salida es a las
    # 00:00 (la marca de dónde empieza el período), así que ahí sí se paga.
    salio_de_madrugada = (v.fecha_regreso == v.fecha_salida
                          and time(0, 0) < v.hora_salida <= HORA_FIN_MADRUGADA)
    vuelve_de_madrugada = (v.hora_regreso <= HORA_FIN_MADRUGADA
                           and not salio_de_madrugada)
    taxi_regreso = 0.0
    if (v.hora_regreso >= limite_taxi_regreso
            or (_activado(p, "taxi_regreso_madrugada", 0) and vuelve_de_madrugada)):
        taxi_regreso = _numero(p.get("valor_taxi_regreso"))
    noches = (max((v.fecha_regreso - v.noches_desde).days, 0)
              if v.noches_desde is not None else noches_de_hospedaje(v, p))
    hospedaje = _numero(p.get("valor_hospedaje")) * noches
    agua = _numero(p.get("valor_agua")) * dias
    # Los gastos pueden venir como texto de una base o de un Excel viejo: se leen igual.
    if _numero(v.combustible_efectivo) > 0:
        combustible = round(_numero(v.combustible_efectivo), 2)
    else:
        combustible = round(_numero(v.km_recorridos) *
                            _numero(p.get("valor_combustible_km")), 2)
    total = round(desayuno + almuerzo + merienda + taxi_salida + taxi_regreso +
                  hospedaje + agua + combustible + _numero(v.parqueadero_peaje) +
                  _numero(v.otros), 2)
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
