<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
  Prohibida su copia, reproducción o distribución sin autorización escrita.
-->

# Manual de usuario — Sistema de Viáticos Miempresa

Este manual explica, pantalla por pantalla, cómo se usa el sistema **tal como está
instalado**: generar un viático, revisarlo, ajustarlo, justificarlo con sus facturas y
llevar el control de lo que hace cada usuario.

Los **números rojos** de las figuras señalan el botón, la casilla o el dato del que
habla cada paso. Las imágenes se sacaron del programa real con un viático de ejemplo
(**N° 164/2026**, del 04/10/2026 al 11/10/2026, con dos ajustes, tres gastos y tres
facturas), así que los importes que se ven en ellas son de muestra.

**Cómo está organizado**

| Capítulo | Para qué |
| --- | --- |
| 1 | Abrir el sistema y entrar a un área (usuario y clave) |
| 2 | El menú principal y qué hace cada módulo |
| 3 | Generar un viático nuevo: paso a paso, el total línea por línea y los errores |
| 4 | Revisar, corregir y anular un viático |
| 5 | Agregar un ajuste (más días o más efectivo), con su cuenta de ejemplo |
| 6 | Justificar: gastos, facturas, saldo, cierre y qué hacer si algo no cuadra |
| 7 | Bandeja de respaldos |
| 8 | Parámetros y catálogos: las 23 tarifas, cómo cambiarlas y qué efecto tienen |
| 9 | Usuarios y roles |
| 10 | Conexión: base local, base central y tamaño de pantalla |
| 11 | Bitácora: quién hizo qué |
| 12 | Preguntas frecuentes y problemas conocidos |
| 13 | Índice de figuras |

**Lo mínimo que hay que saber**

- Un **viático** es un número por año (N° 164/2026) con una o varias **personas** (una
  fila por persona) que viajan con sus **fechas, horas y gastos**.
- Un viático nace **PENDIENTE**; cuando se rinde con facturas y se firma, queda
  **JUSTIFICADO**; si se da de baja, **ANULADO** (no se borra: se conserva para la
  auditoría).
- Nada se pierde: mientras se llena el formulario el sistema guarda un **borrador** cada
  20 segundos y al cerrar la ventana.

---

## 1. Abrir el sistema y entrar a un área

El programa **abre directo en el menú principal**, sin pedir clave (capítulo 2). La clave
se pide al **entrar a cada módulo** (a cada «área»): ahí aparece esta ventana.

![Figura 1 — Clave del área](manual/img/01_ingreso.png)

1. **Usuario** — el nombre corto que le entregó el administrador (por ejemplo `PAOLA`).
   Se escribe sin apellidos.
2. **Clave** — la contraseña. Se ve como puntos: no se muestra nunca.
3. **No volver a pedir la clave en este equipo** — si lo marca, en esta computadora no
   se vuelve a pedir la clave para ese rol (útil en el equipo de cada persona). **No** lo
   marque en una computadora compartida.
4. **INGRESAR** — comprueba la clave y abre el módulo. También funciona con `Enter`.
5. **SALIR** — cierra la ventana sin entrar (el menú sigue abierto).

**El rol manda.** Si la clave es de un rol que no corresponde a esa área, el sistema no
deja entrar y avisa para quién es. Un `EMPLEADO(A)` trabaja en *Generar / revisar*,
*Justificar* y *Respaldos*; un usuario de `JUSTIFICACIÓN` en *Justificar* y *Respaldos*;
el **superusuario** además en *Parámetros*, *Informe de actividad*, *Usuarios* y
*Conexión*.

> **Si no puede entrar:** el mensaje dice si el usuario no existe o si la clave está mal.
> Después de varios intentos fallidos el sistema espera unos segundos antes de volver a
> probar. Si olvidó la clave, el **superusuario** se la cambia desde *Usuarios del
> sistema* (capítulo 9); la clave del superusuario solo la puede cambiar él mismo.

Abajo de la ventana dice a qué base está conectado (`BASE LOCAL (SQLite): …` o
`BASE CENTRAL (PostgreSQL): …`, capítulo 10). Cada ingreso queda anotado en la
**bitácora** («INICIÓ SESIÓN», capítulo 11) con el nombre, el rol y la hora.

---

## 2. El menú principal

![Figura 2 — Menú principal](manual/img/02_menu.png)

1. **Sesión en uso** — quién tiene abierta la sesión en esta computadora
   (`PAOLA NARANJO · SUPERUSUARIO`). Es solo informativo: para trabajar con otra persona
   se pulsa **🔑 Olvidar la clave** (abajo) y se entra con su clave al área que necesite.
2. **Generar / revisar / ajustar viáticos** — el corazón del sistema: crear un viático,
   ver el historial, corregirlo y agregarle ajustes (capítulos 3, 4 y 5).
3. **Justificar viáticos** — registrar gastos y facturas, cerrar el viático e imprimir
   la justificación (capítulo 6).
4. **Respaldos** — todos los archivos (facturas, comprobantes) que se han subido
   (capítulo 7).
5. **Parámetros, empleados, vehículos…** — solo el **superusuario**: tarifas, horas
   límite, empleados, clientes, vehículos y distancias (capítulo 8).
6. **Informe de actividad (auditoría)** — solo el **superusuario**: la bitácora de lo que
   se hizo y quién lo hizo (capítulo 11).
7. **Usuarios del sistema** — solo el **superusuario**: crear y corregir usuarios
   (capítulo 9).
8. **Conexión / base de datos** — solo el **superusuario**: base local o base central,
   servidor, zoom de la pantalla y numeración de viáticos (capítulo 10).

Abajo de la barra están **🔑 Olvidar la clave** (borra el usuario recordado en esta
computadora) y **🚪 Salir del sistema**. El panel de la derecha muestra el **Resumen de
viáticos** (total, pendientes, justificados y anulados) y los dos botones grandes del
trabajo diario.

Los botones que el rol del usuario no permite **no aparecen**: un empleado ve del 2 al 4
y nada más.

> **Un solo programa para varias computadoras.** Si están en **base central**, lo que
> registra una persona lo ven las demás: la lista de viáticos de *Justificar* se
> actualiza sola cada 15 segundos y los catálogos se releen al abrir cada ventana. Si
> están en **base local**, cada computadora tiene sus propios datos (capítulo 10).

---

## 3. Generar un viático nuevo

Menú → **Generar / revisar / ajustar viáticos** → pestaña **Nuevo / editar viático**.

### 3.1 La cabecera: quién, para quién y con qué vehículo

![Figura 3 — Formulario de un viático nuevo](manual/img/03_viatico_nuevo.png)

1. **N° del viático** — lo pone el sistema: es el **próximo número del año** (por
   ejemplo `N° 165/2026`). No se escribe a mano; si hay que empezar en otro número, se
   cambia en *Conexión → Numeración de viáticos* (capítulo 10).
2. **Creado por** — el responsable del viático (quien lo llena). Sale de la lista de
   empleados; si falta alguien, se agrega en *Parámetros y catálogos → Empleados*.
3. **Cliente y proyecto** — destino del gasto (por ejemplo `MUNICIPALIDAD DE CUENCA`).
4. **Recibo N° 1** — el número del recibo de caja con el que se entrega el efectivo
   (hay tres: 1, 2 y 3, para cuando el pago se parte).
5. **Placa vehículo** — el vehículo del viaje. Al elegirlo se ajustan las **horas** del
   estimado (un camión no anda a la velocidad de un auto).
6. **Observaciones** — cualquier nota del viático; sale impresa.
7. **💾 GUARDAR VIÁTICO** — calcula una fila por persona y **guarda**. En un ajuste el
   mismo botón dice **GUARDAR AJUSTE**.
8. **🧹 LIMPIAR Y CANCELAR** — deja el formulario como nuevo (y borra el borrador).
9. **↩ RECUPERAR LO ÚLTIMO** — vuelve a cargar lo que se estaba llenando (ver 3.5).

### 3.2 Fechas, horas y estimado del viaje

![Figura 4 — Tarjeta de fechas y horarios](manual/img/04_viatico_fechas.png)

1. **Salida de Miempresa — fecha** y 2. **hora**: cuándo sale el empleado de la
   empresa.
3. **Llegada al trabajo — fecha** y 4. **hora**: cuándo llega al sitio.
5. **Salida del trabajo — fecha** y 6. **hora**: cuándo termina y emprende el regreso.
7. **Llegada a Miempresa — fecha** y 8. **hora**: cuándo vuelve. Con la hora de
   regreso el sistema decide si corresponde **merienda** y **taxi de regreso** (según las
   horas límite de los parámetros).
9. **🕒 Estimar viaje** — calcula las **horas del camino** con los km del cantón y la
   velocidad del vehículo, y muestra a qué hora se llegaría.
10. **Efectivo sugerido** — el efectivo de combustible que corresponde a los km
    (km × valor por km), redondeado al múltiplo del cajero.
11. **USAR** — copia ese valor al campo **Efectivo Comb. $** de la cabecera.

> **Ojo con las fechas:** el día de salida y el de regreso cuentan distinto (el sistema
> paga las comidas del día extremo según la hora). Si se equivoca, corrija la fecha y
> vuelva a generar: el viático se guarda **con el mismo número**.

### 3.3 Personas, destino y gastos del viaje

![Figura 5 — Personas, destino y gastos](manual/img/05_viatico_datos.png)

1. **Empleado encargado** — el beneficiario del viático (a él se le entrega el dinero).
2. **Provincia** y 3. **Cantón** — el destino. Al elegir el cantón, el sistema **llena
   solo** los km y las horas registrados en *Provincias y km* (capítulo 8).
4. **Chofer** — quién maneja (es **obligatorio** para poder guardar; si maneja el
   encargado, se elige a él mismo). **A la fila del chofer** se le cargan el km, el
   parqueadero/peaje y el efectivo de combustible.
5. **Lugar / referencia** — el sitio exacto (se escribe en mayúsculas y sale impreso).
6. **Km** — los km del viaje (los sugeridos se pueden corregir).
7. **Parq./Peaje** — parqueadero y peajes pagados en efectivo.
8. **Transp./Otros** — otros gastos entregados en efectivo.
9. **Medio** (`AUTO` o `BUS`) y 10. **Extra $** — para los **acompañantes**: cada uno
   puede ir en otro medio y llevar un valor extra.
11. **Empleado** — el acompañante que se va a agregar.
12. **➕ Agregar** — lo suma a la lista. Cada persona lleva **sus propias fechas y
    horas**: si viaja en otro vehículo o sale otro día, se cambian antes de agregarla.
13. **Vista previa** — lo que se va a guardar, persona por persona y con el **total**.

### 3.4 Revisar antes de guardar

![Figura 6 — Vista previa del viático](manual/img/06_vista_previa.png)

La tabla de **Vista previa** muestra, por persona, los días, las comidas, el hospedaje,
el agua, los taxis, el combustible y el **total**; abajo está la fila **TOTAL**. Es el
mismo detalle que se imprime. Si algo no cuadra, corrija el dato (km, fechas, medio) y la
tabla se recalcula sola.

### 3.5 Borradores: si se cierra el programa, no se pierde lo escrito

Mientras el formulario está abierto, el sistema guarda una copia **cada 20 segundos** y
al cerrar la ventana. Si se va la luz o alguien cierra el programa por error:

- Al volver a entrar aparece un aviso con la fecha y hora del borrador y el botón
  **↩ RECUPERAR** (9 de la figura 3) lo devuelve al formulario.
- El borrador se borra al **guardar**, al **limpiar** y cuando pasa el día.
- Queda anotado en la bitácora («RECUPERÓ LO QUE ESTABA LLENANDO»).

### 3.6 Qué calcula el sistema (para poder revisarlo)

- **Comidas:** desayuno y almuerzo se pagan por día según las horas límite; la merienda
  solo si el regreso pasa de la hora límite de merienda.
- **Hospedaje:** un valor por noche (o por fechas del viaje, si así está configurado).
- **Agua:** un valor por día.
- **Taxis:** el de **salida** se paga si sale **a las 06:00 o antes**; el de **regreso**,
  si vuelve **a las 21:00 o después**. Son **un taxi de ida y uno de vuelta por viático**
  (no uno por día) y se pagan en la fila de cada persona, con las horas de *Parámetros*
  (capítulo 8).
  Un **ajuste** **no** paga taxi de salida —el empleado ya salió en el viático original— y
  el **taxi de regreso se paga una sola vez en todo el viático**: si el original ya lo
  pagó, los ajustes lo muestran en **$0**; y si el original no lo pagó (volvía antes de
  las 21:00) pero el último ajuste cambia la hora de regreso y ahora sí llega a las 21:00
  o después, el taxi se paga **en ese ajuste**.
  Si un taxi sale en **$0**, debajo de la vista previa el sistema dice **por qué** y con
  qué hora quedó registrado el viaje: «Taxi de regreso $0: se paga si vuelve a las 21:00
  o después (vuelve a las 19:30)» o «Taxi de regreso $0: ya se pagó en el viático original
  (se paga una sola vez, cuando vuelve de verdad)».

> **Los dos taxis, en una línea.** Sale a las **06:00 o antes** → taxi de salida. Vuelve a
> las **21:00 o después** → taxi de regreso. Si sale **después** de las 06:00 y vuelve
> **antes** de las 21:00, los dos quedan en **$0**: no es un error, no corresponden.
>
> **En un ajuste** el taxi de salida **siempre** es **$0** (ya se pagó en el original).
> **El de regreso también se paga una sola vez** en todo el viático: si el original ya lo
> pagó, los ajustes lo muestran en **$0** (el empleado vuelve a su casa una sola vez).
>
> **Vuelta de madrugada** (llegar entre las 00:00 y las 06:00): solo se paga si el
> superusuario activa **«Taxi regreso — pagarlo también al que vuelve de madrugada»** en
> *Parámetros* (8.1), porque el Excel de la empresa no lo contempla. Si la ida y la vuelta
> son en la **misma** madrugada (sale 04:00 y vuelve 05:30), se paga **un solo** taxi: el
> de salida.
- **Combustible:** km × valor por km, y el total se redondea al múltiplo del cajero.

Los valores y las horas límite son los de **Parámetros** (capítulo 8). Si cambian las
tarifas, los viáticos ya guardados **no** se recalculan solos: hay que corregirlos.

### 3.7 El orden correcto para llenarlo

El formulario se puede llenar en cualquier orden, pero hay uno que evita errores, porque
cada dato alimenta al siguiente:

1. **Cliente y proyecto** (3 de la figura 3) — define para qué se gasta.
2. **Creado por** y **Placa vehículo** (2 y 5) — el vehículo fija la velocidad del
   estimado.
3. **Las cuatro fechas y horas** (figura 4) — de ellas salen los días, las noches, las
   comidas y los taxis.
4. **Provincia y cantón** — al elegir el cantón se llenan solos los km y las horas de
   *Provincias y km*.
5. **Empleado encargado** y **Chofer** — antes de escribir el dinero: el km, el
   parqueadero/peaje y el efectivo de combustible se cargan **a la fila del chofer** (o
   a la del encargado si el chofer no viaja en este viático).
6. **Km**, **Parq./Peaje**, **Transp./Otros** y **Efectivo Comb.** (o **USAR**).
7. **Lugar / referencia** y **Observaciones**.
8. **Los acompañantes**, uno por uno, con su medio y su extra.
9. **Revisar la vista previa** y pulsar **💾 GUARDAR VIÁTICO**.

> **Cambiar algo al final mueve el dinero de fila.** Si primero escribe el peaje y
> después cambia el chofer, el peaje pasa a la fila del chofer nuevo. Y si cambia el
> cantón después de corregir los km a mano, los km vuelven a los del catálogo. Por eso
> conviene dejar el dinero (paso 6) para cuando las personas ya estén puestas.

### 3.8 Antes de guardar: la lista de control

| Qué revisar | Cómo debe verse | Si no está bien |
| --- | --- | --- |
| N° del viático | El que sigue del año (`N° 165/2026`) | Se corrige en *Conexión → Numeración* (10.2) |
| Creado por | El responsable del viático | Agregue o corrija el empleado (8.2) |
| Cliente y proyecto | El cliente al que se le carga el gasto | Agregue el cliente (8.2) |
| Fechas | Salida y regreso; el regreso nunca antes | Corrija la fecha y mire otra vez la vista previa |
| Horas | Las cuatro, incluida la de regreso | Con la hora de regreso se deciden merienda y taxi |
| Encargado y chofer | Quien recibe el dinero y quien maneja | El chofer es obligatorio: si maneja el encargado, elíjalo |
| Km y peaje | Los del viaje, en la fila del chofer | Corrija el km o el cantón |
| Efectivo Comb. | 0 para que se calcule por km, o el valor entregado | **USAR** copia el sugerido |
| Acompañantes | Cada uno con su medio (`AUTO` o `BUS`) y su extra | **➕ Agregar** de nuevo con el dato correcto |
| Vista previa | Una fila por persona y la fila **TOTAL** | Si falta alguien, no se agregó a la lista |

### 3.9 El total, línea por línea (ejemplo)

Ejemplo de práctica, con las tarifas de fábrica del manual: una persona sale el
**04/10/2026 a las 06:00**, llega al trabajo el mismo día a las 10:00, sale del trabajo
el **08/10 a las 18:00**, regresa a las **21:30**, con 400 km y $10 de peaje.

| Concepto | Cómo lo calcula el sistema | En el ejemplo |
| --- | --- | --- |
| Días de viaje | Del 04 al 08: los dos extremos cuentan | 5 |
| Desayuno | $3 × (días − 1) + el del día de salida si sale a las 06:00 o antes | 12 + 3 = **15** |
| Almuerzo | $3 × (días − 1) + el del día de regreso si vuelve a las 13:00 o después | 12 + 3 = **15** |
| Merienda | $3 × (días − 1) + la del día de regreso si vuelve a las 21:00 o después | 12 + 3 = **15** |
| Taxi de salida | $3 si sale a las 06:00 o antes | **3** |
| Taxi de regreso | $3 si vuelve a las 21:00 o después | **3** |
| Hospedaje | $15 × noches (regreso − salida) | 15 × 4 = **60** |
| Agua | $1 × días | **5** |
| Combustible | 400 km × $0.25 (o el efectivo escrito a mano) | **100** |
| Parqueadero/Peaje | El valor escrito en el formulario | **10** |
| **Total** | La suma de todo lo anterior | **226** |
| **Cajero** | El total redondeado **hacia arriba** al múltiplo de $5 | **230** |

Si en el mismo viático va un **acompañante en BUS** (sin km, sin peaje y sin
combustible), su fila paga 15 + 15 + 15 + 3 + 3 + 60 + 5 = **116**; el viático suma
**342** y el cajero redondea a **345**: un solo redondeo, sobre el total del grupo.

| Si cambia… | El total pasa de 226 a… | Por qué |
| --- | --- | --- |
| Sale a las **06:30** | **220** | Pierde el desayuno del día de salida y el taxi de salida |
| El efectivo se escribe a mano: **$120** | **246** | El efectivo manda sobre los km × tarifa |
| El almuerzo se sube a **$3.50** | **228.50** | Cinco almuerzos × $0.50 más |
| El cajero se sube a **$20** | **240** | 226 redondeado hacia arriba al múltiplo de 20 |

> **El total y el entregado no son lo mismo.** El **total** es lo que cuesta el viaje
> según las reglas; el **entregado** es el **cajero** (el total redondeado), porque el
> cajero no entrega fracciones del múltiplo. En la justificación se compara el
> **entregado** contra lo respaldado con facturas (6.3 y 6.7).

### 3.10 Avisos y errores al generar

| Lo que dice el sistema | Por qué sale | Qué hacer |
| --- | --- | --- |
| «Seleccione el empleado encargado.» | No hay encargado elegido | Elíjalo en la lista (8.2 si falta) |
| «Seleccione un chofer.» | Se intentó guardar sin chofer | Elija quién maneja; si maneja el encargado, elíjalo |
| «Elija provincia y cantón para tener el lugar de trabajo.» | Falta el destino | Elija provincia y cantón; el lugar se llena solo |
| «Complete las fechas de salida y regreso.» | Falta una fecha | Escriba las dos (figura 4) |
| «La fecha de regreso no puede ser anterior a la de salida.» | Las fechas están cruzadas | Corrija el regreso |
| «El chofer debe viajar en AUTO.» | El chofer se agregó como acompañante en BUS | Cámbiele el medio o elija otro chofer |
| «El chofer no está en la lista y el auto ya tiene 3 personas…» | El auto está lleno | Agregue al chofer como acompañante o use otro vehículo |
| «Datos inválidos» | Un número mal escrito (por ejemplo `10,5` o una letra) | Corrija el campo que marca el mensaje |
| «Combustible $0: escriba los km…» | No hay km ni efectivo | Escriba los km o el efectivo |
| «Taxi de regreso $0: se paga si vuelve a las 21:00 o después…» | La hora de regreso no llega a la límite | No es un error: verifique la hora |

Los avisos que salen **debajo de la vista previa** no impiden guardar: explican por qué
un valor quedó en $0 para que se pueda revisar antes de firmar.

---

## 4. Revisar, corregir y anular un viático

Menú → **Generar / revisar / ajustar viáticos** → pestaña **Historial**.

![Figura 7 — Historial de viáticos](manual/img/08_historial.png)

1. **Buscar** — filtra por número visible (164), por número interno, por empleado, por
   lugar o por responsable. Escriba y la lista se filtra sola.
2. **Estado** — `TODOS`, `PENDIENTE`, `JUSTIFICADO` o `ANULADO`.
3. **Provincia** — filtra por destino.
4. **🔄 Actualizar** — vuelve a leer la lista (útil en base central, para ver lo que
   registró otra computadora).
5. **Tabla de viáticos** — un renglón por viático, con salida, regreso, responsable,
   total y estado.
6. **Detalle** — las filas del viático elegido: cada persona con sus fechas, horas,
   km, gastos y total. Un viático con ajustes muestra el original y cada ajuste.
7. **Ajustar viático** — agrega días o efectivo al mismo número (capítulo 5).
8. **Editar original** — abre el viático en el formulario para corregirlo (mismo
   número). Solo se editan viáticos **PENDIENTES**.
9. **Anular** — da de baja el viático **con todos sus ajustes**. No se borra: queda
   como `ANULADO` y se puede reactivar.
10. **Ver justificado** — muestra la justificación cerrada de un viático que ya se
    rindió (solo lectura).

En la misma barra están **Editar ajuste** (corrige un ajuste guardado sin tocar el
original), **Nuevo viático**, **Unir PDFs**, **Imprimir / PDF**, los Excel (**Original**,
**Ajuste**, **General**) y el filtro **Ajuste:** para ver un ajuste concreto del detalle.

**Reglas de oro del historial**

- Un viático **JUSTIFICADO** no se edita ni se ajusta: primero se **reactiva** (capítulo
  6.5, botón **↩ A pendiente** en *Justificar*) y después se corrige.
- Al guardar una corrección se **reescriben** las filas de ese número, conservando el
  número, los recibos y el cierre de la justificación.
- Nada se borra en firme: anular es una baja lógica y queda en la bitácora
  («ANULÓ VIÁTICO»).

---

## 5. Agregar un ajuste (más días o más efectivo)

Un **ajuste** es «más viático para el mismo viaje»: el trabajo se alargó unos días o hay
que entregar más efectivo para combustible, peaje u otros gastos. **El original no se
toca** (ese dinero ya se entregó y ya se firmó): el ajuste agrega filas nuevas al mismo
número, numeradas `AJUSTE N° 1`, `AJUSTE N° 2`…

**Cómo se hace**

1. En el **Historial** (figura 7) elija el viático **PENDIENTE** y pulse
   **Ajustar viático** (7).
2. El formulario se abre con los datos del original y el encabezado dice
   `VIÁTICO N° 164 / AJUSTE N° 3` (el número de ajuste que toca). El botón cambia a
   **GUARDAR AJUSTE**.

![Figura 8 — Un ajuste nuevo](manual/img/07_ajuste_nuevo.png)

1. **N° del ajuste** — lo pone el sistema: el que sigue (`AJUSTE N° 1`, `N° 2`, `N° 3`…),
   nunca repite el número de otro ajuste.
2. **Salida de Miempresa** — **no se puede cambiar**: queda fija en el día siguiente al
   regreso del último ajuste (o al del original), porque hasta ahí ya se pagó. Así el
   ajuste cubre exactamente los días nuevos.
3. **Llegada a Miempresa (el regreso)** — la **única fecha que se cambia**: hasta qué
   día se extiende el viaje. Tiene que ser **al menos un día después** del último día ya
   pagado (el regreso del original o el del ajuste anterior); si no, el sistema avisa y no
   deja guardar.
4. **Vista previa** — el original y los ajustes ya guardados, y al final el bloque del
   ajuste que se está creando. Se calcula con **las mismas reglas del viático original**,
   pero solo sobre los días nuevos: desayuno, almuerzo y agua de cada día, la **merienda**
   y el **taxi de regreso** si el regreso pasa de las 21:00, y el **hospedaje por noche**
   (no un día por día): las noches del período **más la noche del último día entregado**,
   que el viático anterior no pagó. Así el original y todos sus ajustes pagan todas las
   noches que la persona durmió fuera. El **taxi de salida no se paga**: el empleado ya
   salió en el viático original.

**Además de los días nuevos, el ajuste acepta tres montos** (se escriben en la cabecera y
se cargan al **chofer**): efectivo para combustible (o el botón **USAR** para tomar el
sugerido del km del original), **Parq./Peaje** y **Transp./Otros**. Todos arrancan en
**cero**, porque lo del original ya se entregó.

> El ajuste se puede hacer **mientras el viático esté PENDIENTE**. Si ya se justificó,
> reactívelo primero (6.5).

### 5.1 Cuánto paga un ajuste (ejemplo)

Con el viático de 3.9 (04/10 06:00 → 08/10 21:30, con cuatro noches ya pagadas), el
trabajo se alarga hasta el **10/10 a las 21:30**:

| Concepto | Cómo se calcula en el ajuste | En el ejemplo |
| --- | --- | --- |
| Días nuevos | Del 09 al 10: el 08 ya se pagó | 2 |
| Desayuno | $3 × (días − 1) + el de la salida (00:00) | 3 + 3 = **6** |
| Almuerzo | $3 × (días − 1) + el del regreso (21:30) | 3 + 3 = **6** |
| Merienda | $3 × (días − 1) + la del regreso (21:30) | 3 + 3 = **6** |
| Taxi de salida | **No se paga**: ya se pagó en el original | **0** |
| Taxi de regreso | $3 si vuelve a las 21:00 o después | **3** |
| Hospedaje | $15 × noches, contando la noche del último día entregado (08→09) | 15 × 2 = **30** |
| Agua | $1 × días nuevos | **2** |
| **Total / cajero** | La suma, redondeada al múltiplo de $5 | **53 / 55** |

Entre el original y el ajuste el viaje queda en **7 días y 6 noches** (04/10 al 10/10),
con **279** de total y **285** entregados (230 del original + 55 del ajuste). Esa es la
cuenta que se compara contra las facturas al justificar (6.3).

---

## 6. Justificar: gastos, facturas y cierre

Justificar es **rendir cuentas**: registrar las facturas en qué se gastó el dinero
entregado, adjuntar los respaldos, anotar si el empleado devuelve o si le queda a favor,
firmar y cerrar el viático.

Menú → **Justificar viáticos**.

### 6.1 Buscar el viático y elegirlo

![Figura 9 — Justificación de viáticos](manual/img/09_justificar.png)

1. **Buscar** — por número (164), empleado, lugar o responsable.
2. **Estado** — `TODOS`, `PENDIENTE`, `JUSTIFICADO` o `ANULADO`.
3. **Viáticos registrados** — un renglón por viático con salida, regreso, total y estado.
   Al hacer clic en uno se cargan sus datos y sus gastos.
4. **N° comprobante** — el número de la factura, nota de venta o retención.
5. **Concepto** — en qué se gastó (ver la lista de 6.2). El valor cae en **esa**
   columna del detalle, igual que en el Excel.
6. **Valor de la factura $** — el importe del comprobante.
7. **💾 Guardar gasto** — agrega el gasto a la lista. Al elegir un gasto ya cargado, el
   mismo botón dice **Guardar cambios** y aparece **🗑 Eliminar**.

Arriba a la derecha están también **🔄 Actualizar**, y los botones de **Excel: Lista de
viáticos** y **Excel: Justificación** (exportan lo que se está viendo).

**Datos del viático seleccionado** resume el viático: beneficiario (encargado), proyecto,
a dónde viajó, vehículo, quién manejó, estado, quién lo creó, los ajustes que tiene y las
personas. Así se revisa **sin salir de la pantalla**.

### 6.2 Los gastos y las facturas

![Figura 10 — Detalle de gastos](manual/img/10_justificar_gastos.png)

Cada línea del detalle es **una factura o comprobante**. Los **7 conceptos** son:

| Concepto | Columna del detalle |
| --- | --- |
| `HOSPEDAJE` | Hospedaje |
| `COMBUSTIBLE` / orden de combustible | Combustible |
| `BUSES` | Buses |
| `TAXIS O CAMIONETAS` | Taxis o camionetas |
| `ALIMENTACIÓN` | Alimentación |
| `PEAJE` | Peaje |
| `OTROS` | Otros |

El valor se guarda en **una sola** de esas columnas (las demás quedan en cero) y la
última fila **TOTAL** suma cada columna. La columna **FACTURAS** dice cuántos archivos
tiene adjuntos cada gasto.

Para adjuntar la factura: elija el gasto en la tabla y pulse
**📎 Subir archivos…** en *Facturas / archivos del viático*. Se pueden subir varias a la
vez (`PDF`, `JPG`, `PNG`, `WEBP`, `BMP`, `TIF`): las **fotos se convierten a PDF** solas y
quedan atadas a ese gasto.

- **👁 Abrir** — abre el archivo para verlo.
- **🗑 Quitar** — lo saca del viático (el archivo no se borra del disco).
- Si se elimina un gasto, sus facturas **no** se borran: quedan sueltas en la lista del
  viático.

### 6.3 El resumen: entregado contra respaldado

![Figura 11 — Recibos, resumen y cierre](manual/img/11_justificar_cierre.png)

1. **Facturas / archivos del viático** — todo lo que está adjunto al viático.
2. **Entregado** — la suma de **todo** el dinero entregado (original + todos los ajustes).
3. **Saldo (entregado – respaldado)** — lo que falta por justificar.
4. **Recibo N° 1, 2 y 3** — los números de recibo de caja del viático (se pueden
   corregir aquí y se guardan con el botón **Guardar** de la misma tarjeta).
5. **Devuelve a Miempresa $** — lo que el empleado devuelve.
6. **A favor del empleado $** — lo que se le quedó debiendo.
7. **✅ JUSTIFICAR** — cierra el viático (6.4).

| Saldo | Qué significa | Qué hace el sistema |
| --- | --- | --- |
| Mayor que 0 | Sobró dinero | llena **Devuelve a Miempresa** con el saldo |
| Menor que 0 | Se gastó más de lo entregado | llena **A favor del empleado** con el sobrante negativo |
| Igual a 0 | Cuadra | deja las dos casillas en 0 |

La sugerencia solo se pone si las dos casillas están en cero: **nunca pisa** un monto que
ya se guardó. En **Motivo** escriba por qué devuelve (o por qué queda a favor) y en
**Nota de cierre** cualquier observación; las dos salen impresas.

### 6.4 Cerrar la justificación

**✅ JUSTIFICAR** hace todo esto de una vez:

1. Si no hay gastos, pregunta si de todas formas se quiere justificar.
2. Guarda los **recibos 1, 2 y 3**, la devolución, el pago al empleado, la nota y quién
   elabora (arranca con el usuario que inició sesión).
3. Marca el viático como **JUSTIFICADO** — **todas** sus filas, original y ajustes — con
   la fecha, la hora y el usuario.
4. Une las facturas en **un solo PDF** del viático (capítulo 7.2).
5. Lo anota en la bitácora («JUSTIFICÓ VIÁTICO»).

Si falla la unión del PDF, **la justificación ya quedó guardada**: solo se pierde el
archivo unificado y se puede volver a generar.

Después de justificar quedan disponibles **👁 Ver original** (el viático completo con el
detalle calculado del original y de cada ajuste), **🖨 Imprimir** y los dos Excel.

### 6.5 Volver a pendiente (para corregir algo ya justificado)

**↩ A pendiente** deshace el cierre: el viático vuelve a `PENDIENTE` para poder editarlo,
ajustarlo o anularlo. **No borra nada**: los gastos, las facturas y la devolución siguen
ahí; solo se limpian «justificado por» y la fecha de cierre. Queda anotado como
«REACTIVÓ VIÁTICO».

### 6.6 Paso a paso: justificar de principio a fin

1. **Menú → Justificar viáticos** y entre con su usuario (capítulo 1).
2. **Busque el viático** por número, empleado o lugar, y elíjalo en la lista. Se
   justifican los `PENDIENTE`; los `JUSTIFICADO` ya están cerrados y los `ANULADO` no se
   rinden.
3. **Lea «Datos del viático seleccionado»**: encargado, proyecto, lugar, vehículo,
   chofer, **los ajustes que tiene** y las personas. Si algo no cuadra, no se corrige
   aquí: se edita en el historial (capítulo 4) o se reactiva (6.5).
4. **Registre cada gasto**: **N° comprobante**, **Concepto** y **Valor** →
   **💾 Guardar gasto**. Una factura, un renglón; repita hasta cargar todas.
5. **Adjunte los archivos**: elija el gasto en la tabla y **📎 Subir archivos…** (varias
   a la vez; las fotos se convierten a PDF solas).
6. **Mire el detalle**: cada valor cayó en su columna y la fila **TOTAL** suma cada
   concepto. La columna **FACTURAS** dice cuántos archivos tiene cada gasto.
7. **Compare Entregado, Respaldado y Saldo** (6.3 y 6.7).
8. **Complete los recibos 1, 2 y 3** si faltan y pulse **Guardar** en esa tarjeta.
9. **Devolución o a favor**, el **Motivo**, la **Nota de cierre** y quién **elabora**.
10. **✅ JUSTIFICAR** y compruebe en la lista que el estado quedó en `JUSTIFICADO`.

> **El orden importa en una cosa:** primero los gastos y las facturas, y **al final** la
> devolución. La devolución se sugiere con el saldo que hay en ese momento; si se escribe
> antes de cargar una factura, queda con el saldo viejo (se puede corregir mientras el
> viático no se haya justificado).

### 6.7 Cómo cuadrar el saldo

La cuenta que hace el sistema es una sola:

> **Entregado** = la suma del cajero del viático original y de **todos** sus ajustes.
> **Respaldado** = la suma de los gastos registrados. **Saldo** = entregado − respaldado.

| Saldo | Qué significa | Qué se escribe |
| --- | --- | --- |
| **0** | Las facturas cuadran con lo entregado | Nada: las dos casillas quedan en 0 |
| **Mayor que 0** | Sobró dinero | **Devuelve a Miempresa** con ese valor y el motivo |
| **Menor que 0** | Se gastó más de lo entregado | **A favor del empleado** con el valor (sin signo) y el motivo |
| Distinto de 0 y sin devolución ni pago | Queda un saldo abierto | Explíquelo en la nota o cuadre las casillas |

La sugerencia se pone **solo** si las dos casillas están en cero, así que un monto ya
guardado nunca se pisa. Lo que se escriba en **Motivo** y en **Nota de cierre** es lo
que verá quien revise el expediente: ponga en pocas palabras por qué devuelve (por
ejemplo «devuelve sobrante de combustible») o por qué quedó a favor («faltó la factura de
hospedaje, se repone»).

> **El saldo no impide justificar.** El sistema deja cerrar con saldo distinto de cero
> porque a veces la factura llega después. Lo que sí conviene es que la devolución o el
> pago estén anotados: si no, el viático queda cerrado con un saldo que nadie explica.

### 6.8 Situaciones frecuentes al justificar

- **Falta una factura y hay que cerrar igual.** Cargue las que tiene, deje la devolución
  o el pago según el saldo y anótelo en la nota. Cuando llegue la factura: **↩ A
  pendiente**, se registra el gasto y se vuelve a justificar (no se pierde nada).
- **La factura se subió al gasto equivocado.** Elija el gasto correcto y súbala otra
  vez; después **🗑 Quitar** la que quedó mal. El archivo no se borra del disco.
- **Una factura trae dos conceptos** (por ejemplo hospedaje y alimentación). Registre
  **dos gastos** con el mismo **N° comprobante**, cada uno con su concepto y su valor; el
  archivo se adjunta al gasto principal.
- **El viático tiene ajustes.** No se justifica por partes: se rinde el número completo,
  con el original y todos los ajustes. El **Entregado** ya los suma y el PDF muestra
  cada bloque por separado.
- **Se justificó y apareció un error.** **↩ A pendiente** (6.5), corrija y
  **✅ JUSTIFICAR** otra vez: los gastos, las facturas y la devolución siguen ahí.
- **Se justificó sin gastos.** El sistema pregunta antes («¿Justificar de todos
  modos?»). Si fue un error, reactive el viático y cárguelos.
- **El archivo no se lee (foto borrosa).** **🗑 Quitar** y suba una foto mejor: el
  sistema la achica, pero no puede recuperar lo que no se ve.

### 6.9 Avisos y errores al justificar

| Lo que dice el sistema | Por qué sale | Qué hacer |
| --- | --- | --- |
| «Seleccione un viático primero.» | Se pulsó un Excel o Imprimir sin elegir | Elija un viático de la lista |
| «Este viático todavía no tiene gastos.» | Se pidió el Excel de la justificación sin gastos | Cargue al menos un gasto |
| «El valor de la factura debe ser numérico.» | El valor tiene letras, coma o está vacío | Escriba solo números (`12.50`) |
| «No se pudieron adjuntar N archivo(s).» | El archivo está abierto en otro programa o no es PDF ni imagen | Ciérrelo y vuelva a subirlo |
| «No hay gastos registrados. ¿Justificar de todos modos?» | Se pulsó **JUSTIFICAR** sin facturas | Cancele y cargue los gastos |
| «No se pudo leer la base de datos…» | Se perdió la conexión (base central) | **🔄 Actualizar**; si sigue, revise *Conexión* (10) |
| «Viático N° 164/2026 JUSTIFICADO. Elija otro viático de la lista.» | Todo salió bien | El viático ya está cerrado |

---

## 7. Bandeja de respaldos

### 7.1 Ver y abrir las facturas de todos los viáticos

![Figura 12 — Bandeja de respaldos](manual/img/12_respaldos.png)

1. **Buscar** — por número de viático, nombre del archivo, concepto o persona.
2. **Tabla** — todos los archivos subidos: N° de viático, nombre, concepto, quién lo
   subió y cuándo. La columna **CONCEPTO** puede decir `PDF CONSOLIDADO` (el paquete del
   viático) o `EN CARPETA` (un archivo que está en la carpeta de respaldos pero no
   registrado en la base; igual se puede abrir).
3. **👁 Abrir seleccionado** — abre el PDF con el visor de Windows (también con doble
   clic sobre la línea).
4. **🔄 Actualizar** — relee la lista.

### 7.2 El PDF consolidado del viático

Al **justificar**, el sistema une todas las facturas del viático en un solo archivo
`VIATICO_164-2026_COMPLETO.pdf` y borra los individuales: en la carpeta (o dentro de la
base) queda **una factura por viático** en vez de diez PDF sueltos. Si se vuelve a
justificar, el COMPLETO anterior se usa como primera parte, así **no se pierde ninguna
factura**. Si la unión fallara, no se borra nada: se conservan los archivos individuales.

**Dónde quedan los archivos** (se elige en *Conexión*, capítulo 10):

| Modo | Dónde | Cuándo conviene |
| --- | --- | --- |
| **En una carpeta** (por defecto) | `data\respaldos\viatico_<n>\` o una carpeta compartida del servidor | cuando las computadoras comparten una carpeta |
| **Dentro de la base** | en la propia base central | cuando no hay carpeta compartida: todas las máquinas ven las facturas |

Las fotos que se adjuntan se convierten a PDF y se achican (una foto de celular de 12 MP
queda en ~250 KB), así la base no crece de más y la factura se lee igual al imprimir.

---

## 8. Parámetros y catálogos

Menú → **Parámetros, empleados, vehículos…** (solo **superusuario**). Tiene cinco
pestañas:
**⚙️ Parámetros**, **👥 Empleados**, **🧑‍💼 Clientes**, **🚗 Vehículos** y
**🗺️ Provincias y km**. Cada cambio que se hace aquí queda anotado en la bitácora
(«CAMBIÓ PARÁMETROS», «AGREGÓ EMPLEADO», «CAMBIÓ DISTANCIA», «IMPORTÓ …»).

### 8.1 Tarifas, horas límite y opciones

![Figura 13 — Parámetros (parte de arriba)](manual/img/13_parametros.png)

1. **Pestañas** — con estas cinco se llega a todo lo que alimenta el formulario del
   viático.
2. **Valor del desayuno por día** — y su **hora límite de salida**, que decide si se paga
   el desayuno.
3. **Valor del hospedaje por noche**.
4. **Valor del combustible por km** — con esto se calcula el efectivo sugerido.

![Figura 14 — Parámetros (final y Guardar)](manual/img/13b_parametros_final.png)

5. **Hospedaje — contar las noches por las fechas del viaje** (`SÍ`/`NO`): en `SÍ` se
   cuentan las noches como en el Excel manual.
6. **Taxi regreso — pagarlo también al que vuelve de madrugada** (`SÍ`/`NO`): el Excel
   manual no lo paga; con `SÍ` el sistema sí lo reconoce.
7. **💾 Guardar parámetros** — graba los 23 valores de una vez.

Los demás valores de la pestaña son: horas límite y valores de **almuerzo**, **merienda**,
**taxi de salida** y **taxi de regreso**, **agua por día**, **parqueadero/peaje sugerido**,
**redondeo del cajero** y los del **estimado de viaje** (velocidad del automóvil, del
camión y del bus, y las horas extra por desayuno, almuerzo y merienda en el camino).
Están explicados uno por uno, con lo que cambia en las cuentas, en **8.4**; y la forma
segura de cambiarlos, en **8.5**.

> **Cambiar una tarifa no recalcula lo ya guardado.** Los viáticos existentes conservan
> sus valores; si hay que corregirlos, se editan uno por uno (8.5).

### 8.2 Empleados

![Figura 15 — Catálogo de empleados](manual/img/14_catalogo_empleados.png)

1. **Lista de empleados** — lo que se puede elegir como encargado, chofer o acompañante.
2. **Buscar en todo** — filtra la lista mientras escribe.
3. **➕ Agregar empleado** — agrega el nombre escrito. Se escribe **APELLIDOS NOMBRES**
   (así salen ordenados y así aparecen en el viático impreso).
4. **📥 Importar Excel** — carga una lista completa desde un Excel.

Al lado están **Clientes** (cliente/proyecto del viático) y **Vehículos** (placa, tipo y
chofer): se agregan y se eliminan de la misma forma.

### 8.3 Distancias: kilómetros y horas por cantón

![Figura 16 — Provincias y km](manual/img/15_catalogo_distancias.png)

1. **Provincia** y 2. **Cantón / ciudad** — al elegir el cantón, si ya tiene datos, se
   cargan solos los km y las horas.
2. **Km aprox.** — los kilómetros desde Cuenca.
3. **Horas de viaje (ida)** — se escribe como se lee (`5:40`) o en horas (`5.67`).
4. **Distancias registradas** — la lista de todo lo cargado; al hacer clic en una línea
   vuelve al formulario de arriba para corregirla.

**💾 Guardar km y horas** graba el cantón (si es nuevo, lo **agrega** a la provincia y
desde ese momento aparece en la lista del viático). **📥 Importar Excel** lee de una sola
vez el archivo **«TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx»** de la carpeta `excel\` del
programa.

> Los km y las horas quedan **en la base**: los ven todas las computadoras. En base
> central se importa **una sola vez**, no en cada PC.

### 8.4 Los 23 parámetros, uno por uno

Estos son todos los valores de la pestaña **⚙️ Parámetros**, **en el mismo orden en que
aparecen en pantalla** y con el mismo texto de cada casilla. Los de fábrica son $3 por
comida y por taxi, $15 por noche, $1 de agua, $0.25 por km, $10 de peaje sugerido,
redondeo de $5, 70/55/45 km/h y 1 hora extra por comida; **los de su instalación son los
que se ven en la pantalla**.

**Comidas** — se pagan por día; el día extremo depende de la hora

| Parámetro (como se ve en pantalla) | Formato | Qué cambia |
| --- | --- | --- |
| Desayuno — hora límite de salida (HH:MM) | HH:MM | Si sale a esa hora o antes, paga el desayuno del día de salida |
| Desayuno — valor por día (USD) | número | Lo que paga cada desayuno |
| Almuerzo — hora límite de regreso (HH:MM) | HH:MM | Si vuelve a esa hora o después, paga el almuerzo del día de regreso |
| Almuerzo — valor por día (USD) | número | Lo que paga cada almuerzo |
| Merienda — hora límite de regreso (HH:MM) | HH:MM | Si vuelve a esa hora o después, paga la merienda del día de regreso |
| Merienda — valor por día (USD) | número | Lo que paga cada merienda |

**Taxis** — uno de ida y uno de vuelta por viático

| Parámetro (como se ve en pantalla) | Formato | Qué cambia |
| --- | --- | --- |
| Taxi salida — hora límite (HH:MM) | HH:MM | Se paga si sale a esa hora o antes |
| Taxi salida — valor (USD) | número | Lo que se paga por el taxi de ida |
| Taxi regreso — hora límite (HH:MM) | HH:MM | Se paga si vuelve a esa hora o después |
| Taxi regreso — valor (USD) | número | Lo que se paga por el taxi de vuelta |

**Hospedaje, agua, combustible y gastos en efectivo**

| Parámetro (como se ve en pantalla) | Formato | Qué cambia |
| --- | --- | --- |
| Hospedaje — valor por noche (USD) | número | Lo que paga cada noche |
| Agua — valor por día (USD) | número | Lo que paga cada día de viaje |
| Combustible — valor por km (USD) | número | El sugerido (km × tarifa) y el combustible cuando no se escribe efectivo |
| Parqueadero/Peaje — valor sugerido por viaje (USD) | número | El valor que aparece escrito en **Parq./Peaje** al abrir un formulario nuevo |
| Redondeo cajero — múltiplo de (USD) | número | El múltiplo al que se redondea **hacia arriba** el total del viático (el entregado) |

**Estimado de viaje** — solo afecta al botón **🕒 Estimar viaje** y al sugerido

| Parámetro (como se ve en pantalla) | Formato | Qué cambia |
| --- | --- | --- |
| Estimado de viaje — velocidad del automóvil (km/h) | km/h | Las horas del camino para un auto |
| Estimado de viaje — velocidad del camión/camioneta (km/h) | km/h | Las horas del camino para un camión |
| Estimado de viaje — velocidad del bus (km/h) | km/h | Las horas del camino para un bus |
| Estimado de viaje — horas extra por el desayuno en el camino | horas | Lo que se suma al estimado por la parada del desayuno |
| Estimado de viaje — horas extra por el almuerzo en el camino | horas | Lo mismo, por el almuerzo |
| Estimado de viaje — horas extra por la merienda en el camino | horas | Lo mismo, por la merienda |

**Opciones de sí/no** — se eligen de una lista, no se escriben

| Parámetro (como se ve en pantalla) | Formato | Qué cambia |
| --- | --- | --- |
| Hospedaje — contar las noches por las fechas del viaje (como el Excel) | SÍ / NO | `SÍ`: noches = regreso − salida (como el Excel). `NO`: noches entre la llegada al trabajo y la salida del trabajo |
| Taxi regreso — pagarlo también al que vuelve de madrugada (el Excel no lo paga) | SÍ / NO | `SÍ`: también paga el taxi al que vuelve antes de las 06:00 (el Excel no lo paga) |

> **Ninguno de estos valores cambia un viático ya guardado.** Se usan al **calcular**
> (crear, editar o ajustar). Para que un viático viejo tome una tarifa nueva hay que
> editarlo (capítulo 4) o reactivarlo y volver a justificarlo (6.5).

### 8.5 Cómo cambiar los parámetros sin romper nada

1. **Anote cómo están** los valores que va a tocar: una foto de la pantalla sirve. La
   bitácora guarda que se cambió, pero no los valores anteriores.
2. **Entre con el superusuario** a *Parámetros, empleados, vehículos…* → pestaña
   **⚙️ Parámetros**.
3. **Cambie solo lo decidido.** Las horas se escriben `HH:MM` (`06:00`, `21:30`); los
   valores, con punto decimal (`0.25`, `3.50`). No deje campos vacíos.
4. **💾 Guardar parámetros** una sola vez. Si algo está mal escrito, el sistema avisa
   «Revise los valores. Use HH:MM y números válidos.» y **no guarda nada**.
5. **Pruébelo con un viático de prueba**: pestaña **Nuevo / editar viático**, con las
   mismas fechas y los mismos km de un viático conocido, y mire la **vista previa**. No
   hace falta guardarlo.
6. **Corrija los viáticos que haga falta**: los guardados **no** se recalculan solos.
   Mientras estén `PENDIENTE` se editan; si ya están `JUSTIFICADO`, primero **↩ A
   pendiente** (6.5).
7. **Revise la bitácora** (`CAMBIÓ PARÁMETROS`, capítulo 11): queda el usuario, la fecha,
   la hora y el detalle del cambio.

> **Cambiar las tarifas no es un tema de pantalla, es un tema de dinero.** Hágalo con la
> persona que autoriza los viáticos, déjelo en la bitácora y avise a quien justifica: el
> **entregado** de los viáticos nuevos va a cambiar con el nuevo cajero.

> **El cajero se aplica sobre el total del grupo.** Si cambia el múltiplo, los viáticos
> que se creen después se redondean al nuevo; los ya guardados conservan su cajero.

### 8.6 Ejemplos de cambios y su efecto

Con el viático de 3.9 (5 días, 4 noches, 400 km, total 226 y cajero 230):

| Si cambia… | Antes | Después | Por qué |
| --- | --- | --- | --- |
| Combustible de $0.25 a $0.30 por km | 100 | 120 | 400 km × la tarifa nueva |
| Almuerzo de $3 a $3.50 | 15 | 17.50 | 5 almuerzos × $0.50 |
| Cajero de $5 a $20 | 230 | 240 | 226 redondeado hacia arriba al múltiplo de 20 |
| Hora límite del taxi de salida de 06:00 a 05:00 | 3 | 0 | Sale a las 06:00 y ya no llega a la límite |
| Hora límite de la merienda de 21:00 a 22:00 | 15 | 12 | Vuelve a las 21:30 y ya no alcanza la merienda del regreso |
| «Hospedaje por fechas» de SÍ a NO | 4 noches | Las noches entre llegada y salida (aquí también 4) | Con SÍ manda el día de salida; con NO, el horario real del trabajo |
| «Taxi de regreso de madrugada» de NO a SÍ | 0 | 3 | Con SÍ paga al que vuelve antes de las 06:00 |

> Con **«Taxi de regreso de madrugada» en `SÍ`** hay una excepción: si sale y vuelve en
> la **misma** madrugada (sale 04:00 y vuelve 05:30), se paga **un solo** taxi (el de
> salida), porque es el mismo traslado.

### 8.7 Lo que no se cambia en esta pestaña

| Qué | Dónde está |
| --- | --- |
| Empleados, clientes y vehículos | Pestañas **👥 Empleados**, **🧑‍💼 Clientes** y **🚗 Vehículos** (8.2) |
| Kilómetros y horas por cantón | Pestaña **🗺️ Provincias y km** (8.3) |
| Usuarios, claves y roles | *Usuarios del sistema* (capítulo 9) |
| Base de datos, numeración y respaldos | *Conexión / base de datos* (capítulo 10) |
| Estado de un viático (anular, reactivar, justificar) | Capítulos 4 y 6 |

> **Orden recomendado la primera vez:** 1) empleados, clientes y vehículos; 2)
> provincias y km; 3) tarifas y horas límite; 4) usuarios; 5) recién entonces los
> viáticos. Todo eso queda en la base: se hace **una sola vez**, no en cada computadora.

---

## 9. Usuarios y roles

Menú → **Usuarios del sistema** (solo **superusuario**).

![Figura 17 — Usuarios y roles](manual/img/16_usuarios.png)

1. **Tabla de usuarios** — usuario, nombre, rol, la clave (siempre «cifrada») y la fecha
   de creación. Se elige un usuario haciendo clic en su línea.
2. **Usuario** — el nombre corto con el que se entra (sin espacios, por ejemplo
   `paola`).
3. **Nombre** — el nombre completo, que es el que sale en la bitácora.
4. **Clave** — la contraseña. Al corregir un usuario se puede dejar en blanco para **no**
   cambiarla.
5. **Rol** — `EMPLEADO(A)` (crea viáticos) o `JUSTIFICACIÓN` (justifica y maneja
   respaldos). El **superusuario** aparece en la lista como `MIEMPRESA` con rol
   `SUPERUSUARIO`: nadie le puede cambiar el rol y solo él mismo cambia su clave.
6. **Estado / avisos** — confirma lo que se hizo («Nuevo usuario», «Usuario guardado»…).

Los botones de la tarjeta son **➕ Crear usuario**, **💾 Guardar cambios**, **🗑 Eliminar**
y **🧹 Limpiar** (deja el formulario listo para uno nuevo).

Las claves se guardan **cifradas**, no en texto plano. Cada alta, cambio o baja queda en
la bitácora.

---

## 10. Conexión: dónde están los datos

Menú → **Conexión / base de datos** (solo **superusuario**).

### 10.1 Qué base se está usando

![Figura 18 — Conexión y base de datos](manual/img/17_conexion.png)

1. **En uso** — dice si los datos son **locales** (un archivo SQLite en esta
   computadora) o de la **base central** (PostgreSQL en el servidor), con la ruta o el
   servidor, más un resumen: cuántos viáticos, empleados, clientes y respaldos hay.
2. **Tipo de base** — `Base LOCAL (cada máquina con su archivo SQLite)` o
   `Base CENTRAL en el servidor (PostgreSQL)`. Al cambiar de base el sistema pide
   confirmación y reinicia la conexión.
3. **Servidor (IP o nombre)** — por ejemplo `192.168.22.171`.
4. **Puerto** — `5432` (el de PostgreSQL).
5. **Usuario** de PostgreSQL — `miempresa`.

La **clave** del servidor se escribe una vez y se guarda cifrada. El nombre de la base
(`viaticos`) no se cambia aquí.

### 10.2 Facturas, numeración, zoom y pruebas

![Figura 19 — Conexión: final de la pantalla](manual/img/17b_conexion_final.png)

6. **Tamaño de la pantalla en esta computadora** — elija la opción que se lea cómoda
   (`Automático` es lo recomendado). **Solo afecta a esta máquina**: se guarda en
   `config.json`, no en la base.
7. **🔌 Probar conexión** — avisa si el servidor responde con los datos escritos, antes
   de guardar.
8. **💾 Guardar** — aplica los cambios.

Otros bloques de esta pantalla:

- **Archivos de respaldo (facturas)** — dónde se guardan las facturas: **dentro de la
  base central** (recomendado: todas las máquinas los ven) o en una **carpeta
  compartida del servidor** (con **Elegir…**).
- **Numeración de viáticos (reinicia cada año)** — fija en qué número va el próximo
  viático del año (por ejemplo `165`). Úselo solo para empezar a mitad de año o para
  corregir un desfase.
- **⬆ Subir mis datos locales a la central** — copia empleados, vehículos, parámetros,
  clientes, viáticos, ajustes, justificaciones, respaldos y bitácora de esta computadora
  a la base central. Se usa **una sola vez**, en la máquina que tiene los datos buenos.

> **En base central** importe los Excel de catálogos **una sola vez**: los datos quedan
> en el servidor y los ven todas las computadoras.

---

## 11. Bitácora: quién hizo qué

Menú → **Informe de actividad (auditoría)** (solo **superusuario**).

![Figura 20 — Informe de actividad](manual/img/18_bitacora.png)

1. **usar fechas** — activa los campos **Desde** y **Hasta**.
2. **Desde** y 3. **Hasta** — el rango de fechas (día/mes/año).
4. **Usuario** — filtra por la persona que hizo la acción.
5. **Acción** — filtra por tipo de movimiento (`INICIÓ SESIÓN`, `GENERÓ VIÁTICO`,
   `GUARDÓ AJUSTE`, `REGISTRÓ GASTO`, `SUBIO FACTURA(S)`, `JUSTIFICÓ VIÁTICO`,
   `ANULÓ VIÁTICO`, `CAMBIÓ PARÁMETROS`, `AGREGÓ EMPLEADO`, `CAMBIÓ DISTANCIA`,
   `CREÓ USUARIO`…).
6. **Buscar texto** y **🔍 Buscar** — busca en el detalle (viático, empleado, lugar…).
   **⟲ Todo el historial** limpia los filtros.
7. **Movimientos registrados** — fecha y hora, usuario, rol, acción, módulo, referencia
   (por ejemplo `N° 164/2026`) y el detalle.

A la derecha, **Resumen del filtro** cuenta los movimientos por usuario y por acción.
Abajo, **📊 Exportar a Excel / CSV** y **🖨 Imprimir / PDF** sacan el informe tal como se
está viendo.

> La bitácora es la prueba de lo que pasó: no se puede editar ni borrar desde el
> programa. Si un viático se anuló, quién lo justificó o quién cambió una tarifa, aquí
> está.

---

## 12. Preguntas frecuentes

**No me aparece un botón del menú.** Su rol no lo permite: *Parámetros*, *Bitácora*,
*Usuarios* y *Conexión* son del superusuario.

**El viático dice JUSTIFICADO y no me deja editarlo.** Es lo correcto: primero
**↩ A pendiente** en *Justificar* (6.5) y después corríjalo.

**Cambié una tarifa y los viáticos viejos siguen igual.** Es a propósito: lo guardado no
se recalcula. El **sugerido** de los nuevos sí cambia. Corrija el viático que lo necesite
(8.5).

**Se cerró el programa y perdí lo que estaba llenando.** No se perdió: vuelva a abrir el
formulario y use **↩ RECUPERAR** (3.5).

**El cantón no aparece en la lista.** Agréguelo en *Provincias y km* (8.3): al guardar, el
sistema lo suma a la provincia y ya queda disponible.

**Subí una factura a un gasto equivocado.** Elija el gasto correcto y vuelva a subirla; o
**🗑 Quitar** y súbala otra vez. Las facturas no se borran del disco al quitarlas.

**La pantalla se ve muy grande o muy pequeña.** *Conexión → Tamaño de la pantalla*
(10.2); el cambio es solo de esta computadora.

**¿Dónde están los datos?** En la tarjeta **En uso** (figura 18) aparece la ruta del
archivo local o el servidor de la base central.

**Trabajo en dos computadoras: ¿veo lo mismo?** Solo si están en **base central**. En
base local cada máquina tiene sus propios datos.

**El total del viático dice 226 y me entregan 230.** Es el **cajero**: el total se
redondea hacia arriba al múltiplo configurado ($5 de fábrica). En la justificación se
compara el **entregado** (230), no el total (3.9 y 6.3).

**¿Los ajustes se justifican aparte?** No. El viático se rinde una sola vez: el
**entregado** suma el original y todos sus ajustes (5.1 y 6.8).

**Justifiqué con saldo distinto de cero: ¿está mal?** No está prohibido, pero hay que
dejar escrito qué pasó: **Devuelve a Miempresa**, **A favor del empleado**, el motivo y
la nota de cierre (6.7).

**¿Quién puede cambiar las tarifas?** Solo el **superusuario**, en *Parámetros* (8.1).
Cada cambio queda en la bitácora como `CAMBIÓ PARÁMETROS`.

**¿Cuántas facturas puede tener un gasto?** Las que haga falta: **📎 Subir archivos…**
acepta varias a la vez y la columna **FACTURAS** muestra cuántas tiene cada renglón.

---

## 13. Índice de figuras

| Figura | Archivo | Pantalla |
| --- | --- | --- |
| 1 | `img/01_ingreso.png` | Ingreso: usuario y clave |
| 2 | `img/02_menu.png` | Menú principal |
| 3 | `img/03_viatico_nuevo.png` | Viático nuevo: cabecera |
| 4 | `img/04_viatico_fechas.png` | Fechas, horas y estimado |
| 5 | `img/05_viatico_datos.png` | Personas, destino y gastos |
| 6 | `img/06_vista_previa.png` | Vista previa del viático |
| 7 | `img/08_historial.png` | Historial: buscar, editar, anular |
| 8 | `img/07_ajuste_nuevo.png` | Ajuste nuevo |
| 9 | `img/09_justificar.png` | Justificar: viáticos y gastos |
| 10 | `img/10_justificar_gastos.png` | Detalle de gastos |
| 11 | `img/11_justificar_cierre.png` | Recibos, resumen y cierre |
| 12 | `img/12_respaldos.png` | Bandeja de respaldos |
| 13 | `img/13_parametros.png` | Parámetros (arriba) |
| 14 | `img/13b_parametros_final.png` | Parámetros (final y Guardar) |
| 15 | `img/14_catalogo_empleados.png` | Catálogo de empleados |
| 16 | `img/15_catalogo_distancias.png` | Provincias y km |
| 17 | `img/16_usuarios.png` | Usuarios y roles |
| 18 | `img/17_conexion.png` | Conexión y base de datos |
| 19 | `img/17b_conexion_final.png` | Conexión (zoom y pruebas) |
| 20 | `img/18_bitacora.png` | Informe de actividad (bitácora) |

---

*Sistema de Viáticos Miempresa — Richard Esteban Salazar Guillén ·
richards0101789@gmail.com · +593 981239086. Documentación de uso; para el detalle
técnico vea `FUNCIONAMIENTO_VIATICOS.md`, y para la instalación en red,
`SERVIDOR.md` y `PRUEBA_PC_SERVIDOR_16_2345.md`.*
