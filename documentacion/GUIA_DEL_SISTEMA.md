<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Guía de implementación — Sistema de Viáticos Miempresa

## 1. Decisión de reestructuración

No es necesario reescribir toda la aplicación. La estructura Tkinter actual es aprovechable, pero sí era necesario corregir tres niveles:

1. **Base de datos:** conservar una fila por empleado dentro del viático, pero agregar medio de transporte, rol de encargado, combustible en efectivo, recibo y gastos de justificación.
2. **Flujo de pantallas:** eliminar el login obligatorio y dejar un menú interno con cuatro opciones.
3. **Justificación:** separar la liquidación de gastos del cálculo original del viático, replicando las columnas del Excel manual.

La base de datos migra automáticamente al iniciar. No se pierden viáticos existentes; agrega las columnas nuevas cuando faltan.

## 2. Instalación y ejecución

1. Copie la carpeta `sistema_viaticos_miempresa` completa al equipo donde se usará.
2. Verifique que tenga Python 3 instalado.
3. Ejecute:
   - Windows: doble clic en `INICIAR.bat`, o `python main_gui.py`.
   - Linux: `python3 main_gui.py`.
4. La base se crea en `sistema_viaticos_miempresa/data/viaticos.db`.
5. Las facturas adjuntas se guardan en `data/respaldos/`.
6. `tkcalendar` es opcional. Si lo instala (`pip install -r requirements.txt`), aparece calendario visual; si no, las fechas se escriben como `dd/mm/aaaa`.

Haga copias de seguridad de la carpeta `data` antes de actualizar versiones.

## 3. Cambios archivo por archivo

### `main_gui.py`

- Se eliminó el ciclo de login.
- Ahora crea un usuario interno fijo y abre directamente el menú principal.
- Punto de entrada único: `python main_gui.py`.

### `ui_login.py`

- Se eliminó de esta versión porque el acceso será interno, sin claves.
- Si más adelante desea control de roles, conviene crear una pantalla nueva con claves cifradas y no guardar contraseñas en texto plano.

### `ui_menu.py`

Menú principal reducido a:

1. Generar viático.
2. Revisar y modificar viáticos.
3. Justificar viáticos.
4. Parámetros, empleados, vehículos y rutas.
5. Salir.

Se agregó el logo y se aplicaron los colores reales de la imagen:

- Azul principal: `#1F1CFF`.
- Amarillo principal: `#FACC00`.
- Blanco y grises neutros.

### `tema.py`

- Se actualizó la paleta corporativa completa.
- Se conservó `AutoCombo`, que es útil para buscar empleados, provincias, cantones y placas escribiendo parte del nombre.

### `dateentry.py` — archivo nuevo

- Selector visual de fecha si existe `tkcalendar`.
- Si no está instalado, funciona como una caja de texto `dd/mm/aaaa`.
- Evita que la aplicación falle por una dependencia externa obligatoria.

### `database.py`

Cambios principales:

- La base ahora se guarda dentro de la carpeta de la aplicación: `data/viaticos.db`.
- Migración automática de columnas nuevas en `viajes` y `respaldos`.
- Campos agregados al viático:
  - `recibo_viatico`;
  - `provincia`;
  - `canton`;
  - `es_encargado`;
  - `medio_transporte`;
  - `extra_transporte`;
  - `orden_combustible_2`;
  - `efectivo_combustible`.
- Nueva tabla `gastos` para justificación con las columnas del primer Excel:
  - fecha;
  - número de comprobante;
  - tipo;
  - RUC;
  - proveedor;
  - lugar;
  - hospedaje;
  - combustible;
  - buses;
  - taxis/camionetas;
  - alimentación;
  - peaje;
  - otros;
  - total.
- `respaldos` ahora puede relacionarse con un gasto específico.
- Funciones nuevas para guardar, editar, eliminar, listar y totalizar gastos.

### `calculos.py`

- Se conservó la lógica del segundo Excel.
- Se mantiene:
  - días de viaje;
  - desayuno, almuerzo y merienda;
  - taxis;
  - hospedaje por noche;
  - agua por día;
  - combustible por km;
  - combustible por valor fijo en efectivo;
  - total y redondeo de cajero.
- Las horas extras no se incluyeron, según lo solicitado.

### `ui_viaje.py`

Pantalla de generación y modificación:

- Encargado principal como primera fila del viático.
- Provincia y cantón/ciudad con kilómetros desde Cuenca.
- Lugar de trabajo automático como `cantón, provincia`.
- Km editable después de sugerirlo por cantón.
- Vehículo, orden de combustible, segunda orden, efectivo de combustible y recibo.
- Pasajeros adicionales con:
  - nombre;
  - medio `AUTO` o `BUS`;
  - extra en efectivo.
- Validación: máximo tres personas en auto, incluido el encargado.
- Solo el encargado recibe combustible por km o efectivo.
- Los acompañantes reciben alimentación, hospedaje, agua y taxis según fechas/horas, pero no combustible.
- Cada viajero puede tener **su propio horario** (botón **⏱ Horario…**): el que va en BUS sale antes o
  llega más tarde, y sus comidas y su hospedaje se calculan con sus horas.
- El extra de cada acompañante se suma como transporte/otros.
- El parqueadero/peaje sugerido sale del parámetro, pero se puede cambiar por viático.
- Historial con búsqueda, edición de pendientes, anulación e impresión.

### `ui_ajustes.py`

Reemplaza la justificación anterior. Ahora funciona así:

1. Busque o seleccione el número de viático.
2. La pantalla precarga automáticamente:
   - responsable;
   - proyecto/cliente;
   - destino;
   - fechas y horas;
   - vehículo;
   - empleados;
   - valor entregado.
3. Digite cada comprobante con las mismas columnas del Excel de justificación.
4. Seleccione un gasto y adjunte una o varias facturas.
5. El sistema calcula:
   - valor entregado;
   - valor respaldado;
   - saldo a favor del empleado o de la empresa.
6. Puede imprimir la liquidación y marcar el viático como justificado.

También permite reabrir un viático justificado para corrección.

### `ui_admin.py`

- Ya no administra usuarios ni claves.
- Pestañas actuales:
  - parámetros de viáticos;
  - empleados;
  - vehículos;
  - provincias/cantones y kilómetros desde Cuenca.
- El parámetro de parqueadero/peaje se usa como valor sugerido, no como valor obligatorio, porque en los Excel reales varía por viaje.

### `reportes.py`

- Reporte de viático con el formato del segundo Excel.
- Reporte de justificación con el formato del primer Excel:
  - encabezado del viático;
  - personas;
  - tabla de comprobantes;
  - totales por categoría;
  - valor entregado;
  - valor respaldado;
  - saldo;
  - observación automática;
  - lista de archivos adjuntos;
  - firmas.
- Se abre en el navegador listo para imprimir o guardar como PDF.
- Colores alineados al logo Miempresa.

## 4. Reglas de negocio implementadas

### Cálculo del viático

- Días: `(fecha regreso - fecha salida) + 1`, mínimo 1.
- **Comidas (desayuno, almuerzo y merienda): se revisan día por día.** Una comida cuenta si la
  persona está fuera de casa cuando llega esa hora límite (el día de salida se cuenta desde la hora
  de salida de Miempresa y el día de regreso hasta la hora en que llega a Miempresa).
  Ejemplo: se van el 23 a las 22:00, llegan al destino el 24 a las 06:00 y el 25 salen del trabajo a
  las 14:00 y llegan a las 20:00 → 2 desayunos, 2 almuerzos y 2 meriendas (el 23 no cuenta ninguna:
  a las horas límite todavía estaban en la ciudad). Los viajes de un día dan lo mismo que antes.
- **Hospedaje: noches que se duerme fuera**, según las fechas reales registradas de **llegada al
  trabajo** y **salida del trabajo** (`fecha salida del trabajo - fecha llegada al trabajo`). Si no
  se registraron, se usan las del viaje (comportamiento anterior).
- Agua: por cada día.
- Combustible normal: `km × tarifa por km`.
- Si se ingresa efectivo de combustible mayor que cero, ese valor reemplaza al cálculo por km.
- Valor de cajero: redondeo **hacia arriba** al múltiplo configurado (por defecto **5**: 21 → 25,
  26 → 30). Se hace **una sola vez, sobre el total del viático** y no por persona, porque el
  retiro del cajero lo hace **una sola persona** (el encargado) y lleva el dinero de todo el
  grupo: el valor queda en su fila y las demás en cero. Así un viático de 183 + 116 + 116
  (**$415**) retira **$415**, no los **$425** que salían de redondear cada cuenta por separado
  (185 + 120 + 120). Lo mismo vale para el ajuste, sobre el total del ajuste.
- Las horas límite (desayuno 06:00, almuerzo 13:00, merienda 21:00), los valores por día y el
  **estimado de viaje** (velocidad del automóvil, del camión/camioneta y del bus, más las **horas que
  se suman por cada comida —desayuno, almuerzo y merienda— que cae dentro del viaje**) se cambian en
  **Parámetros**.

### Varios empleados

- El encargado es quien maneja y quien puede recibir orden de combustible.
- En camioneta/auto: máximo tres personas en total.
- Acompañantes en auto reciben viático normal, pero no combustible.
- Acompañantes en bus pueden recibir un extra en efectivo.
- Cada empleado queda como una fila independiente para impresión y justificación.

### Justificación

- La justificación se guarda por número de viático.
- Cada gasto puede tener una o varias facturas adjuntas.
- No se exige que el respaldo sea exactamente igual al valor entregado: el saldo queda explícito para devolución o compensación.

## 5. Errores corregidos respecto a la versión subida

- `ui_ajustes.py` llamaba funciones de respaldos con parámetros que `database.py` no aceptaba.
- `database.py` no guardaba empleado/concepto/gasto en los archivos adjuntos.
- `ui_ajustes.py` usaba `tk.simpledialog` sin importarlo.
- Orden 2 y efectivo de combustible se agregaban fuera del flujo principal.
- El login bloqueaba el uso aunque no se requerían usuarios.
- La pantalla de justificación no replicaba realmente el primer Excel.
- El reporte de justificación no calculaba entregado, respaldado ni saldo.

## 6. Recomendaciones para producción

1. Haga una copia de prueba antes de abrir la base real.
2. Copie los viáticos Excel antiguos solo como respaldo; no los mezcle manualmente con la base SQLite.
3. Si desea exportar también a `.xlsx`, se puede agregar un tercer botón sin cambiar la lógica existente.
4. Si desea lectura automática de facturas, el siguiente paso sería OCR; pero primero conviene estabilizar esta versión manual.
5. Si vuelven a pedir usuarios, agregue permisos por pantalla: generar, modificar, justificar y administrar parámetros.

## 7. Usuarios, inicio de sesión y superusuario (versión actual)

Volvió el control de acceso, ahora sí con usuarios reales:

| Usuario | Clave | Rol | Para qué |
| --- | --- | --- | --- |
| TATIANA | 1234 | VENDEDOR(A) | crea viáticos, ajustes y todo lo demás |
| CRISTINA | 1234 | VENDEDOR(A) | igual |
| MIRIAM | 1234 | VENDEDOR(A) | igual |
| MARTINA | 1234 | VENDEDOR(A) | igual |
| PAOLA NARANJO | 1234 | JUSTIFICACIÓN | justifica viáticos (también puede todo lo demás) |
| **MIEMPRESA** | *reservada* | SUPERUSUARIO | informe de actividad y alta de usuarios |

Reglas:

- *(Antes)* Todos los usuarios normales podían **ver y modificar todo** (parámetros, empleados,
  clientes, vehículos, rutas, viáticos, ajustes y justificación). **Esto cambió**: vea abajo.
- El **superusuario no aparece en ninguna lista ni pantalla**: solo entra escribiendo
  usuario y clave. Sus credenciales se entregan aparte y no deben publicarse.
- Al iniciar sesión, el nombre del usuario aparece en el menú, en la barra amarilla de
  cada pantalla y queda escrito automáticamente en **«Creado por»** (viáticos) y
  **«Elaborado por»** (justificación).
- El usuario se escribe sin importar mayúsculas y también se acepta el primer nombre
  (por ejemplo `PAOLA` entra como `PAOLA NARANJO`).
- Los usuarios antiguos `admin` y `justifica` se eliminan solos al migrar la base.

### Ingreso por área y claves cifradas (entrega actual)

El sistema **abre en el menú principal sin pedir clave** y **cada área pide la clave al abrirse**,
comprobando el rol. Así una vendedora ya no puede entrar a Justificar viáticos (eso es de la persona
de justificación) y **Auditoría, Usuarios y Conexión quedan solo para el superusuario**; en cambio
**los parámetros y los catálogos los abre cualquier usuario con su propia clave** (ver la tabla).

| Área | Vendedoras | Justificación | Superusuario |
| --- | :---: | :---: | :---: |
| Generar / revisar / ajustar viáticos | ✔ | ✔ | ✔ |
| Respaldos (facturas y comprobantes) | ✔ | ✔ | ✔ |
| Justificar viáticos | — | ✔ | ✔ |
| Parámetros, empleados, clientes, vehículos y rutas | ✔ | ✔ | ✔ |
| Informe de actividad (auditoría) | — | — | ✔ |
| Usuarios del sistema | — | — | ✔ |
| Conexión / base de datos | — | — | ✔ |

- **Los parámetros y los catálogos son de todos**: cualquier usuario (vendedora o justificación)
  entra a **⚙️ Parámetros, empleados, vehículos y rutas** con **su propia clave** y cambia las
  tarifas y las horas límite, el valor por km y las horas de viaje, las distancias y horas por
  cantón, los empleados, los clientes y los vehículos. **El cambio queda guardado en la base en
  uso**, así que lo ven **todas las computadoras**, y queda en el **informe de actividad** con el
  nombre de quien lo hizo. Si una computadora todavía trabaja con **base local**, el cambio se queda
  en esa máquina hasta que se pase a la central y se suba con **⬆ Subir mis datos locales a la
  central**.
- **Los Excel se cargan una sola vez**: las listas de **personal** y de **clientes** (botón
  📥 Importar Excel de sus pestañas) y el Excel de **km y horas por cantón** (📥 Importar Excel de
  «⚙️ Parámetros → 🗺️ Provincias y km») quedan guardados **en la base**, así que con la **base
  central** los ven todas las computadoras y **no hay que repetir la carga en cada PC**.
- **Los km y las horas son los del documento de la empresa**: el archivo que va con el sistema es
  **`TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx`** (carpeta `excel\`, y también dentro del `.exe`):
  trae el km de cada cantón y **una hora** por destino —el punto medio entre el tiempo en auto y el
  tiempo en autobús que trae el documento revisado `DISTANCIAS DOC.docx`— con **YANTZAZA** en los
  215 km · 5 h que la empresa dejó puestos a mano. Al importar cualquier Excel de tiempos de viaje de
  esa carpeta se cargan **estos** valores (el otro archivo, `TIEMPOS DE VIAJE MIEMPRESA.xlsx`, dice
  lo mismo y además trae los cantones que el documento no tiene).
- **Las horas de viaje se leen como se leen**: se guardan en horas decimales (6.0 = 6:00, que es
  como las usa el cálculo y como las lleva el Excel de importación), pero en la pantalla se ven
  siempre como «6 h 00 min» —en la lista de «🗺️ Provincias y km» y en el aviso del formulario de
  viáticos— y en el campo de horas se pueden escribir como se lean («5:40») o en decimal («5.67»).
- Si alguien escribe la clave de un rol que **no** corresponde a esa área, la ventana lo avisa
  («Esa área es solo para: …») y no deja entrar. El intento queda en la auditoría.
- La ventana de ingreso **no muestra leyendas** sobre la clave ni sobre quién puede entrar: solo el
  usuario, la clave y la casilla de recordar. El área se ve en el título («Ingreso — Parámetros») y la
  tabla de permisos de arriba no se publica en pantalla; el aviso del rol sale únicamente al intentar
  ingresar (punto anterior).
- **«No volver a pedir la clave en este equipo»**: casilla de la ventana de ingreso, se olvida al
  cerrar el sistema. En el menú queda el botón **🔒 Olvidar la clave** para dejar el equipo sin
  sesión (y se registra el cierre en la auditoría).
- **Conexión / base de datos** tiene su **botón en la barra lateral** y es solo del superusuario (al
  pulsarlo el sistema pide su clave). Ahí se ve la base en uso, se elige local o central, se guardan
  los respaldos, se fija la numeración y se cambia el **zoom de esa computadora**. La misma pantalla
  aparece sola cuando el servidor no responde, y **Ctrl+Alt+B** la abre como atajo.
- **La barra lateral va agrupada** (tabla `GRUPOS` de `q_menu.py`): **TRABAJO DEL DÍA** —generar,
  revisar y ajustar viáticos, justificar viáticos, respaldos y **parámetros y catálogos**— y, aparte
  con su título y una línea en medio, **🔑 SUPERUSUARIO** —auditoría, usuarios y conexión—. El título
  de cada grupo lleva su ayuda al pasar el ratón y cualquier módulo nuevo que no esté en `GRUPOS` cae
  solo en «OTROS MÓDULOS», así nada se pierde por olvido.
- **Claves cifradas**: en la base se guarda `sha256$<sal>$<resumen>`, no la clave. La pantalla de
  usuarios muestra `•••• cifrada` y permite **cambiar** la clave (escribiendo una nueva) pero no
  leerla. Las bases anteriores (con claves en texto) se cifran solas la primera vez que se abre el
  sistema; a partir de ahí el login compara contra el resumen, no contra el texto.
- Los permisos por área están en una sola tabla al comienzo de `q_menu.py` (`PERMISOS_MODULO`). Hoy
  `"admin"` (parámetros y catálogos) es `(db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER)` —lo abre
  cualquier usuario con su clave— y `"bitacora"`, `"usuarios"` y `"conexion"` son `(db.ROL_SUPER,)`.
  Para volver a dejar los parámetros **solo** en el superusuario, quite los dos primeros roles de la
  tupla de `"admin"`; para dar un área a otro rol, agregue el rol a la tupla que corresponda y el
  sistema le pedirá la clave igual que al superusuario.

### `ui_login.py` — archivo nuevo

Pantalla de ingreso con el logo, validación contra la tabla `usuarios` y aviso de error
sin revelar si falló el usuario o la clave.

### `ui_bitacora.py` — archivo nuevo (solo superusuario)

Informe completo de actividad: **todo lo que hacen los usuarios**, con filtros por
usuario, acción, fechas y texto libre, además de resumen por usuario/acción, exportación
a Excel y CSV e impresión.

Acciones que se registran:

- `INICIÓ SESIÓN` / `CERRÓ SESIÓN`;
- `CREÓ VIÁTICO`, `EDITÓ VIÁTICO`, `CREÓ AJUSTE`, `EDITÓ AJUSTE`, `ANULÓ VIÁTICO`;
- `JUSTIFICÓ VIÁTICO`, `REACTIVÓ VIÁTICO`, `CAMBIÓ RECIBOS`, `REGISTRÓ GASTO`,
  `CAMBIÓ GASTO`, `ELIMINÓ GASTO`, `SUBIO FACTURA(S)`, `QUITÓ FACTURA`;
- `CAMBIÓ PARÁMETROS`, `AGREGÓ/ELIMINÓ/IMPORTÓ EMPLEADO(S)`, clientes, vehículos,
  `CAMBIÓ DISTANCIA`;
- `CREÓ/CAMBIÓ/ELIMINÓ USUARIO`.

Cada movimiento guarda fecha y hora, usuario, rol, acción, módulo, referencia (por
ejemplo `N° 138`) y un detalle legible: quién creó, encargado, lugar, número de
personas y total.

### `ui_usuarios.py` — archivo nuevo (solo superusuario)

Alta, cambio de clave/nombre/rol y baja de usuarios de ventas y de justificación.
El superusuario no se lista, no se modifica y no se puede eliminar.

### `main_gui.py`

Ahora pide iniciar sesión y registra el ingreso y la salida en la bitácora.

### `ui_menu.py`

Muestra `👤 nombre` y `USUARIO: … · ROL` del que inició sesión; las opciones
«Informe de actividad» y «Usuarios del sistema» aparecen únicamente para el
superusuario.

## 8. Ajuste de viático: combustible, parqueadero y otros

Antes el ajuste solo calculaba días adicionales (comidas, hospedaje y agua). Ahora:

- Se puede digitar **Efectivo Comb. $** en el ajuste, o presionar **USAR** para tomar
  el *efectivo sugerido de combustible* que aparece en el cuadro azul.
- El sugerido del ajuste se calcula con el **km del viático original** (el lugar y la
  ruta no cambian), así que se mantiene el mismo valor sugerido que ya se había
  calculado en el original: se puede pulsar **USAR** o escribir arriba un valor mayor.
- Se puede registrar **Parq./Peaje** y **Transp./Otros del encargado** en el ajuste.
- Esos valores se suman al total y al cajero del ajuste y van en la columna que
  corresponde (Combust., Parq./Peaje, Transp./Otros) para el encargado/chofer del
  ajuste. Si el ajuste lleva otra persona como chofer, esa persona es la que recibe el
  combustible y el peaje.
- Al **empezar un ajuste nuevo** esos tres campos arrancan en cero, porque lo del
  original ya se entregó; al **editar un ajuste guardado** se recuperan sus propios
  valores.
- Lo demás del ajuste se calcula con las **mismas reglas del viático original**, sobre
  los días nuevos: comidas, agua, hospedaje por noche y **taxi de regreso** si vuelve a
  la hora límite. El **taxi de salida** y el transporte extra de los acompañantes no se
  pagan (eso es propio del original).

## 9. Explicación del valor de una factura (justificación)

En «Digitar gasto / factura» hay un cuadro nuevo **📝 Explicación**: allí se escribe el
motivo por el que una factura se respalda con un valor distinto al impreso (por ejemplo:
la factura es de $30,00 y solo se respaldan $25,00 porque el empleado cubrió $5,00). El
valor que afecta el cálculo sigue siendo **Valor de la factura $**, que es donde va el
valor realmente justificado.

La lista de gastos muestra la columna **EXPLICACIÓN** y la justificación impresa la
agrega al final de la tabla, más el bloque **«EXPLICACIÓN DE VALORES DE LAS FACTURAS»**
con comprobante, proveedor y la explicación escrita. Ya no se pide ni se imprime el
«valor real de la factura»: en los respaldos se puede comparar contra la factura física.

## 10. Respaldos: solo el PDF unificado


Al pulsar **✔ JUSTIFICAR**, el sistema une *todos* los respaldos del viático en un único
archivo `VIATICO_n_COMPLETO.pdf` y **borra los archivos individuales** (y sus registros).
Si se subieron 10 imágenes, en `data/respaldos/viatico_n/` queda únicamente el PDF
completo, que es el que aparece en la ventana 📁 RESPALDOS.

- Mientras el viático no se justifique se conservan los archivos individuales, porque son
  la materia prima para armar el completo.
- Si el viático se justifica, se reactiva y se vuelve a justificar, el completo anterior
  se usa como base y se le agregan las facturas nuevas: **no se pierde nada**.
- Si la unión falla por cualquier motivo, no se borra ningún archivo.
- El borrado se hace en un archivo temporal y luego se reemplaza, para que una
  interrupción no dañe el PDF completo anterior.

## 11. Base de datos central (PostgreSQL en el servidor) — pruebas con 5 máquinas

El sistema ahora puede trabajar con **una sola base de datos en el servidor** para que las
5 máquinas (cada una con su `.exe`) vean y graben los mismos datos.

### Cómo quedó armado

- **`configuracion.py`** (nuevo): lee y guarda `config.json`, junto al programa o al
  `.exe`. Ahí se elige la base (`sqlite` o `postgres`), los datos del servidor y dónde se
  guardan las facturas. Si el archivo no existe, todo funciona como antes (base local).
- **`bd.py`** (nuevo): capa de conexión única. Las funciones de `database.py` no cambiaron
  de forma; esta capa traduce lo que difiere entre SQLite y PostgreSQL (parámetros,
  `INSERT OR IGNORE`, `GROUP_CONCAT`, `date()`, `datetime('now','localtime')`, tipo de
  fila) y devuelve los datos igual que antes (`fila["columna"]`). También cierra la
  conexión al terminar cada bloque, para no llenar el servidor de conexiones.
- **`database.py`**: se guardó **toda la lógica** (cálculos, ajustes, justificación,
  gastos, bitácora, reportes). Se corrigieron los puntos que dependían de SQLite:
  consecutivos atómicos (`UPDATE … RETURNING`), `RETURNING id` en vez de `lastrowid`,
  columnas que faltaban en el esquema (`pago_empleado_monto`, `elaborado_por`,
  `respaldos.contenido`) y la numeración de viáticos, que ahora **nunca repite un número**
  aunque el contador haya quedado atrás.
- **`migracion.py`** (nuevo): copia toda la base local (SQLite) a la central
  (empleados, vehículos, parámetros, provincias, cantones, distancias, clientes,
  usuarios, viáticos, ajustes, gastos, respaldos, bitácora y secuencias). Vacía la central
  con `TRUNCATE … CASCADE` y copia todo en orden de dependencias.
- **`ui_conexion.py`** (nuevo, solo superusuario): pantalla **🔌 CONEXIÓN / BASE DE DATOS**
  en el menú del superusuario, para elegir el tipo de base, probar la conexión, guardarla
  y **subir los datos locales a la central**.
- **Respaldos (facturas)** en dos modos:
  - *dentro de la base central* (`"respaldos": {"modo": "base"}`) — recomendado cuando las
    máquinas no comparten carpeta; los PDF se guardan como `BYTEA` y la unión al justificar
    se arma con ellos;
  - *carpeta compartida* (`"modo": "carpeta"`) — en la base queda solo la ruta
    (por ejemplo `\\SERVIDOR\viaticos_respaldos`).
  En los dos casos se mantiene la regla pedida: **al justificar queda un solo PDF por
  viático** (`VIATICO_n_COMPLETO.pdf`) y se borran los individuales.
- **`servidor/`** (nuevo): `postgresql.conf` con PostgreSQL 16 (zona horaria
  `America/Guayaquil`), `respaldar_base_nativo.bat` para respaldos con `pg_dump` y
  `PROBAR_SERVIDOR.bat` para comprobar el puerto desde otra PC. El paso a paso está

### Qué se probó (y funcionó)

1. **SQLite** (base local, como antes): regresión completa — usuarios, viáticos, ajustes,
   gastos, respaldos en carpeta y**en base**, bitácora, reportes y todas las ventanas.
2. **PostgreSQL 16.15 en el servidor**: la misma regresión completa, con respaldos dentro de la
   base y en carpeta, incluidas la unión de facturas (3 páginas → 4 al re-justificar) y la
   lectura de los PDF guardados en la base.
3. **Migración real**: se copiaron los datos de la base local a la central —32 empleados,
   6 vehículos, 24 provincias, 204 cantones, 202 distancias, 755 clientes, 6 usuarios,
   7 viáticos (47 filas), 10 gastos, 3 respaldos con sus PDF y 23 movimientos de bitácora—
   y luego se abrió el sistema contra la central verificando listados, ventanas y reportes.
4. **Numeración concurrente**: dos conexiones simultáneas obtienen números distintos, y un
   viático nuevo tomó el número siguiente al mayor existente (sin repetir).

### Para arrancar las pruebas

En el servidor o en su equipo: entre a la carpeta `servidor` y ejecute `Start-Service postgresql-x64-<V>`.
Después, en el sistema (superusuario) → **🔌 CONEXIÓN / BASE DE DATOS**: probar, guardar y

## 12. Numeración de viáticos por año (automática) y arranque configurable

Como en el manejo manual, **cada año la numeración vuelve a empezar en 1**:

- El número que ve el usuario es el **consecutivo del año** (1, 2, 3…) y en los
  informes se muestra como **«001/2026»**.
- El reinicio es **automático**: el año sale de la **fecha del viaje**, así que un
  viático de diciembre registrado en enero conserva la numeración de su año.
- Internamente el número guardado es `año * 1000 + consecutivo` (por ejemplo
  `2026005`), de modo que los viáticos de distintos años **nunca se mezclan**
  aunque tengan el mismo consecutivo; toda la lógica sigue funcionando igual.
- Los nombres de los PDF consolidados usan el número visible:
  `VIATICO_005-2026_COMPLETO.pdf`.
- **Nunca se repite un número**, aunque dos máquinas guarden al mismo tiempo (el
  consecutivo se toma con bloqueo de fila en la base central).

**Arranque configurable (superusuario):** en **🔌 CONEXIÓN / BASE DE DATOS** está
la sección **Numeración de viáticos**, con un resumen por año (cuántos viáticos hay
y cuál sería el próximo) y los campos para **fijar el año y el número desde el que
se empieza**. Es lo que se usa al pasar de las pruebas a los viáticos reales: por
ejemplo `2026` y `12` si ya llevan 11. Si se pide un número menor al ya usado, el
sistema toma el siguiente libre (protección contra repetidos).

**Migración de datos anteriores:** al abrir una base con numeración antigua
(1, 2, 3… globales), el sistema la convierte sola a la numeración por año: los
viáticos se renumeran por su fecha, los gastos y respaldos se mueven con ellos, las
carpetas de respaldos se renombran y queda registro del cambio (tabla
`renumeracion`) para reparar cualquier archivo que hubiera quedado con el número
anterior.

## 13. Listas de personal y clientes, nombres completos y login

### Importación desde Excel

Los botones **📥 Importar Excel** de «Parámetros → 👥 Empleados» y
«Parámetros → 🧑‍💼 Clientes» ahora **detectan solos la columna correcta**: buscan la fila
de encabezados y toman la columna **Nombre** (personal) o **Cliente** (clientes), sin
importar cuántas columnas tenga el archivo ni las filas de título que traiga arriba.
Si el Excel es una lista simple de una sola columna, sigue funcionando como antes.

- Personal se carga con `LISTADO PERSONAL MIEMPRESA ...xlsx` → **31 empleados**.
- Clientes se carga con `LISTA DE CLIENTES MIEMPRESA.xlsx` tomando **solo el nombre**
  (no se importan RUC, ciudad, contacto ni grupo) → **755 clientes**.
- Los dos importadores **no duplican**: si se vuelve a importar el mismo archivo, informa
  que no hay nuevos.

### Nombres completos de los usuarios

Para entrar se sigue escribiendo igual (**TATIANA, CRISTINA, MIRIAM, MARTINA,
PAOLA NARANJO**), pero el nombre que firma los documentos es el **nombre completo del
listado de personal**:

| Usuario (para entrar) | Nombre en «Creado por» / «Elaborado por» |
| --- | --- |
| TATIANA | PEÑA FERNANDEZ MAYRA TATIANA |
| CRISTINA | CASTILLO RIOFRIO IVETTE CRISTINA |
| MIRIAM | LOPEZ ROSALES MIRIAM ANGELA |
| MARTINA | JARAMILLO BORJA MARTINA MARIA |
| PAOLA NARANJO | NARANJO GONZALEZ MIRIAM PAOLA |

El cambio se aplica solo si el usuario todavía tiene el nombre corto, así no pisa un
nombre cambiado a mano desde «👥 Usuarios del sistema».

### Pantalla de ingreso

- El contenido está **centrado** (logo, títulos, campos y botones) y la ventana se abre
  centrada en la pantalla.
- El campo **Usuario se escribe siempre en MAYÚSCULAS** (también si se pega el texto).
- La clave sigue distinguiendo mayúsculas y minúsculas (la del superusuario es en
  minúsculas).

## 14. Correcciones para la puesta en marcha con la base central

### El menú del superusuario cortaba las dos últimas opciones

La ventana del menú medía siempre **640×620** y no se podía cambiar de tamaño,
pero el superusuario tiene **tres opciones más** que las vendedoras: el contenido
necesita **746 píxeles** de alto. Resultado: **«🔌 CONEXIÓN / BASE DE DATOS» y
«🚪 SALIR» quedaban fuera de la pantalla** (parecía que la opción de configurar la
conexión no existía).

- **`ui_menu.py`**: la ventana ahora **calcula su alto con `winfo_reqheight()`**
  después de dibujar los botones (`_ajustar_tamano()`), se centra en la pantalla y
  solo se puede estirar en vertical. Con el superusuario abre en **640×746**; con
  una vendedora, en **640×560**.

### Protección contra vaciar la base central

El botón **⬆ Subir mis datos locales a la central** reemplaza **todo** lo de la
central con lo que haya en el `data\viaticos.db` de esa máquina. El `.exe` de la
carpeta `dist` usa **su propia carpeta `dist\data`**, que está vacía, así que
abrirlo desde ahí y pulsar «subir» habría **borrado la base central**.

- **`ui_conexion.py` → `_migrar()`**: antes de preguntar, se lee
  `migracion.resumen_local()` y el aviso indica **cuántos viáticos, empleados,
  clientes, respaldos y movimientos de bitácora** se van a enviar. Si el resultado
  es **0 viáticos**, el mensaje cambia a una advertencia
  **«⚠ CUIDADO: esta máquina no tiene ningún viático»** que explica que se está
  usando el `.exe` de `dist` y que hay que abrir el sistema con `INICIAR.bat`.

### Corrección: el viático nuevo repetía el N° 001/2026 (contadores perdidos)

**Síntoma:** después de subir los datos a la base central, al guardar un viático el
sistema lo numeraba **001/2026** otra vez; como ese número ya existía, en la lista
"no aparecía" nada nuevo (el viático quedaba **mezclado** con el 001/2026 anterior).

**Causa:** al copiar la base, `migracion._reiniciar_secuencia` ejecutaba un `setval` sobre
la tabla `seq`, que **no tiene columna `id`**. PostgreSQL marcaba la transacción en error y
**se perdía todo lo copiado de esa tabla** (los contadores) **sin avisar**. Sin el contador
`viatico_2026`, el sistema empezaba a contar desde 1 y repetía el primer número.

**Correcciones:**

- `migracion._reiniciar_secuencia`: solo hace `setval` en tablas que **tienen** columna
  `id` (lo comprueba antes en `information_schema`).
- `migracion.migrar`: después de copiar cada tabla **cuenta los registros** y, si no
  coinciden, lanza un error claro en vez de dejar la base central a medias en silencio.
- `database._next`: si el contador del año no existe, **lo crea** y lo pone al día con el
  mayor viático guardado del año. Así es imposible entregar un número ya usado, aunque el
  contador se pierda o quede atrás.
- `database.listar_viaticos_unico`: `SELECT * … GROUP BY` no es válido en PostgreSQL; se
  reescribió con funciones de agregación (era una función sin uso, pero quedaba como
  bomba de tiempo).

**Probado:** migración sobre una base de prueba (el `seq` se conserva y el próximo viático
es el **008/2026**), guardado real contra la base central y contra la local (el viático sale
`008/2026` y aparece en la lista), y lectura completa de todas las pantallas contra
PostgreSQL.

### Una computadora nueva solo necesita el `.exe`

`configuracion.DEFECTO` ahora apunta **de fábrica** a la base central
(`192.168.22.179`, puerto `5432`, base `viaticos`, usuario `miempresa`, clave
`miempresa`, respaldos guardados **dentro de la base**). Por eso una computadora
que solo lleva `Sistema_Viaticos.exe` funciona **sin copiar ningún archivo extra**.

- Si existe un `config.json` junto al programa, **manda sobre esos valores**, así se
  puede cambiar de servidor sin volver a empaquetar.
- Si la base central no responde al abrir el sistema, aparece la pantalla
  **«NO SE PUDO ABRIR LA BASE DE DATOS»** (`ui_conexion.VentanaServidor`): se escribe
  otra IP y se pulsa **🔌 Probar y guardar** (queda guardada en `config.json`), o se
  elige **💻 Trabajar en esta PC (base local)**.
- `main_gui.main()` llama a `ui_conexion.asegurar_conexion()` **antes** del ingreso,
  porque el ingreso necesita la base para validar usuario y clave (así una PC que
  solo tiene el `.exe` nunca queda bloqueada sin poder revisar la dirección).

### Carpetas ordenadas

| Carpeta | Contenido |
| --- | --- |
| `servidor\` | `postgresql.conf`, `respaldar_base_nativo.bat`, `PROBAR_SERVIDOR.bat`, `respaldos_base\` |
| `sistema_viaticos_miempresa\` | El programa: código, `INICIAR.bat`, `EMPAQUETAR_EXE_SERVIDOR.bat`, `data\`, `excel\` y `dist\Sistema_Viaticos.exe` |
| `documentacion\` | Todas las guías `.md` |

### Mejoras pedidas después de las primeras pruebas en red

1. **La lista no se refrescaba sola.** Antes, si otra computadora creaba un viático había que
   cerrar y volver a abrir la ventana. Ahora:
   - El historial (Generar/Revisar) y la lista de viáticos (Justificar) se **actualizan solos cada
     15 segundos** y también **al volver a la ventana** (con `<FocusIn>`).
   - El refresco de fondo **solo redibuja si algo cambió** (compara una «firma» de la lista), así
     no parpadea ni pierde lo que estaba seleccionado.
   - `database.conteo_ajustes()` cuenta los ajustes de todos los viáticos **en una sola consulta**:
     antes se abría una conexión por viático (`db.ajustes_viaje(n)` dentro del bucle), y eso era lo
     que hacía lento el refresco contra la base central.

2. **Editar un gasto/factura ya registrado.** Basta con **hacer clic en la fila** del gasto en
   «Detalle de gastos»: sus datos se cargan en el formulario de arriba y el botón cambia a
   **💾 Guardar cambios** (al guardar se **modifica** ese gasto, no se duplica, y el botón vuelve a
   «💾 Guardar gasto»). No hace falta un botón aparte; la función `AjustesWindow._editar_gasto`
   queda disponible en el código por si más adelante se quiere ligar a una tecla.

3. **El formulario de gastos queda en blanco.** Después de guardar (nuevo o editado) el formulario
   se limpia y se quita la selección de la lista. Se conserva a propósito la **fecha** (para digitar
   varias facturas del mismo viaje).

4. **Ventanas adaptables a pantallas pequeñas.** Varias ventanas tenían un `minsize` grande
   (`ui_viaje` pedía 1220×880) que en monitores de 20" o con el escalado de Windows al 125 %
   **dejaba los botones de abajo fuera de la pantalla** y la ventana no se podía encoger.
   - Nuevo `tema.ajustar_ventana(ventana, ancho, alto, min_ancho, min_alto)`: recorta el tamaño y
     el mínimo a lo que de verdad cabe en la pantalla. Se aplicó en el menú, viáticos,
     justificación, original/ajustes, respaldos, parámetros, bitácora, usuarios y conexión.
   - El **menú principal** además aprieta los botones si la pantalla es baja y, si aun así no entra,
     muestra una **barra de desplazamiento** (con rueda del ratón): ningún botón queda fuera.

5. **Arreglos técnicos encontrados en las pruebas:**
   - `bd._a_postgres()`: los `%` escritos dentro del SQL (por ejemplo en un `LIKE '%algo%'`) ahora
     van dobles. Sin esto, psycopg2 fallaba con `IndexError: tuple index out of range`.
   - `servidor\respaldar_base_nativo.bat`: usaba `wmic`, que **ya no existe en Windows 11**, así que el
     respaldo salía con un nombre roto. Ahora la fecha se obtiene con PowerShell.

6. **Se quitó la opción que borraba los datos («Limpiar datos de prueba»).** Existía un botón en el
   menú del superusuario (y su versión por consola, `LIMPIAR_DATOS_DE_PRUEBA.py`) que dejaba la base
   solo con los catálogos. Se eliminó a pedido: los viáticos del periodo de pruebas **se quedan** en
   el historial (no estorban) y, como el sistema nunca entrega un número ya usado, para empezar la
   producción solo hay que fijar el número real en **🔌 CONEXIÓN / BASE DE DATOS → Numeración de
   viáticos → 💾 Fijar numeración** (por ejemplo, si el último de prueba fue el 007/2026, se fija el
   008). Nada del sistema borra la base: los respaldos siguen con `servidor\respaldar_base_nativo.bat`.

7. **Informe GENERAL y nombres de archivo con el número visible.** El título del informe general
   imprimía el número interno (`VIÁTICO N° 2026001`); ahora dice `VIÁTICO N° 001/2026`
   (`reportes.imprimir_viatico` usaba `{numero}` en vez de `_num_txt(numero)`). También se corrigieron
   los nombres de los archivos que genera el navegador, que son los que aparecen como título al
   imprimir: ahora son `viatico_001-2026.html` y `justificacion_001-2026.html`. Se comprobó generando
   los **cuatro** informes (original, ajuste, general y justificación) y buscando cualquier texto de
   la pantalla dentro del HTML: **ninguno aparece**, porque los informes se arman **solo con los datos
   de la base**, nunca con lo que se muestra en las ventanas.

8. **Tamaño de la interfaz (zoom) y pantallas chicas.** El sistema se diseñó pensando en pantallas
   grandes: la ventana de justificación pide **1481 px** de ancho y la de viáticos **889 px** de
   alto. En un monitor de 20" (1366×768) o con el escalado de Windows al 125 % eso dejaba los
   botones de la derecha y de abajo fuera de la pantalla.
   - **Zoom global** (`tema.preparar_zoom`): al abrir cada ventana se aplica un factor que encoge (o
     agranda) **toda** la letra y los controles del sistema. Se elige en **🔌 CONEXIÓN / BASE DE
     DATOS → «Tamaño de la pantalla en esta computadora»** (el botón **🔌 de la barra lateral** del
     menú, solo superusuario):
     **Automático · 100 · 90 · 80 · 70 · 60 %**. Se guarda en el `config.json` de **esa** PC
     (`"interfaz": {"zoom": 0.8}`, y `0` = automático), o sea que **cada computadora recuerda el
     suyo** y no cambia el de las demás. Como Tk crea las letras al abrir cada ventana, al guardar
     el sistema avisa y se **cierra y vuelve a abrir solo** para aplicarlo (`tema.reiniciar_sistema`).
     Ejemplos del automático: 1366×768 al 100 % → **82 %**; 1600×900 al 125 % → **78 %**;
     1920×1080 → **100 %**; 1024×768 → 66 %.
   - **Las tablas ya no ensanchan las ventanas.** Antes, la tabla de vista previa (25 columnas) y la
     de «Detalle de gastos» (16 columnas) obligaban a la ventana a medir 1655 y 2094 px: se veían
     cortadas por la derecha y **ni siquiera se podía usar la barra horizontal**, porque quedaba
     fuera de la pantalla. Ahora su marco pide 300×200 y 420×140 (solo «pide»; ocupa el espacio que
     le dé la ventana), se llega a las últimas columnas con la barra de abajo y la ventana mide lo
     que la pantalla permite. El campo «Explicación» del gasto también pedía 95 caracteres fijos y
     ahora pide 60 y se estira con la ventana.
   - **Los informes y la impresión no cambian**: el zoom solo cambia cómo se ve en el monitor, nunca
     lo que se imprime ni lo que se guarda en la base.
   - **Aviso de escalado a Windows**: al arrancar (antes de crear la primera ventana) el programa
     llama a `tema.preparar_dpi()`, que avisa a Windows de que el programa ya se encarga del
     escalado. Sin esto, Windows estira la imagen y en pantallas al 125 % todo se ve más grande y
     borroso. Se puede desactivar con `"interfaz": {"dpi_consciente": false}` en `config.json`.
   - El **autodiagnóstico** (`VIATICOS_SELFTEST=1`) ahora informa la pantalla y el zoom en uso, para
     poder revisar un equipo a distancia:
     `pantalla: 1920 x 1080 · zoom: Automático (100 %) · dpi consciente: True`.

9. **Informe del viático: filas alineadas y columna COMBUST. limpia** (`reportes._tabla_viatico`).
   - La fila **TOTALES** armaba una celda vacía de más, así que **todos los totales salían corridos
     una columna**: el KM aparecía bajo DESAY., el total bajo PARQ./PEAJE, y el último valor se
     salía de la tabla. Ahora el KM cae en la columna KM y cada total en la suya. En el bloque
     **TOTAL GENERAL** el título usaba `colspan="22"` cuando la tabla tiene **25** columnas: ahora
     es **23**, así TOTAL y CAJERO quedan bajo sus columnas.
   - La columna **COMBUST.** mostraba el **número de orden pegado al valor** («01 50.00», «01 -»),
     que se veía como un número equivocado, y el caso «EFECTIVO …» nunca se activaba porque leía
     `combustible_efectivo` (la columna real se llama `efectivo_combustible`). Ahora la columna
     lleva **solo el valor** del combustible, igual que la vista previa de la pantalla; la orden
     sigue saliendo arriba, en **ORDEN COMB.** del encabezado.
   - Comprobado con el viático **001/2026** (original + 2 ajustes): las filas de datos y las de
     totales de los tres bloques tienen **25 celdas** y cada total coincide con su columna.

10. **Pantallas de superusuario más limpias.** Se quitaron las notas que solo repetían lo que ya se
    veía: «Solo el superusuario ve este informe.» (informe de actividad), «El superusuario no
    aparece en esta lista y no se puede modificar ni eliminar.» (usuarios) y el párrafo largo bajo
    la numeración, además del último tramo del bloque de ayuda de la pantalla de conexión. Los pasos
    para dejar el servidor en marcha quedan en esa misma pantalla, y se quitó la nota del campo de
    parqueadero/peaje, que ya lo dice su propio nombre.

11. **Las horas del viático: dos se escriben y dos las calcula el sistema.** Los rótulos dicen
    **«Salida de Miempresa»**, **«Llegada a Miempresa»**, **«Llegada al trabajo»** y **«Salida del
    trabajo»**, con la salida y la llegada a Miempresa en la misma columna del formulario. Se
    registran las dos **salidas** y el sistema escribe las dos **llegadas** (se recalculan solas al
    cambiar la salida, los km o el vehículo, y con el botón **⏱ Estimar viaje**; al abrir un viático
    guardado no se toca nada). El tiempo de viaje es el del destino o `km ÷ velocidad` redondeado
    **hacia arriba a la hora entera**, más **una hora por cada comida que cae dentro del viaje**: el
    que sale a las 10:00 y llega a las 13:00 queda registrado a las **14:00** (el almuerzo), el que
    llega al lugar a las 08:00 a las **09:00** (el desayuno), el que vuelve a las 22:00 a las
    **23:00** (la merienda de las 21:00) y el viaje largo de 02:00 a 14:00 a las **16:00** (desayuno
    y almuerzo). Cada tramo se cuenta **desde su propia salida**: la ida desde la salida de
    Miempresa y la vuelta desde la salida del trabajo. El cálculo es el mismo para **todos los
    vehículos, incluido el BUS**: el bus hace el mismo viaje y tarda lo mismo (el tipo **BUS** se
    registra en **Parámetros → Vehículos** y, si el cantón no tuviera horas en la tabla, se usan
    los km ÷ la velocidad del bus). Las horas extra por comida son tres parámetros
    (`horas_desayuno_viaje`, `horas_almuerzo_viaje` y `horas_merienda_viaje`) y el aviso del botón
    **⏱ Estimar viaje** muestra el detalle del cálculo.
12. **La pantalla ya no se queda pensando (velocidad con la base central).** El sistema abría y
    cerraba una **conexión nueva en cada consulta**; contra el PostgreSQL del servidor eso es repetir
    el saludo por la red (TCP + usuario + clave) cada vez, y el formulario de viáticos consulta
    muchísimo por interacción (parámetros, km y horas del cantón, empleados, clientes, vehículos…).
    De ahí la pausa al elegir **provincia** y **cantón**, y la demora al **guardar** hasta verlo en el
    historial. Ahora:
    - **La conexión se reutiliza** (`bd.conectar`): se abre una sola vez y se va prestando. Nada más
      cambia: `conn = conectar()` y `with conectar() as conn:` siguen comportándose igual (lo que no
      se confirma con `commit` se pierde al cerrar, como antes). Si el servidor o un cortafuegos corta
      una conexión que estuvo quieta, se prueba con un `SELECT 1` y el sistema abre otra sola, en vez
      de fallar al guardar; la conexión del servidor lleva `keepalives` para que no la corten.
    - **Los catálogos y los parámetros se recuerdan 30 segundos** (`database.olvidar_cache` los borra
      en el momento en que se graba algo, así que nunca se ve un dato viejo propio) y las **listas
      desplegables 5 segundos** (`qt_comunes.ComboAuto`): abrir la lista de cantones (~200 nombres) ya
      no consulta ni vuelve a dibujar, y estimar el viaje o teclear los km no consultan nada.
    - Medido con `pruebas_rendimiento.py` (25 ms simulados por conexión, como en la red de la
      empresa): elegir **provincia** pasó de 30 a **0,4 ms**, elegir **cantón** de 31 a **1,2 ms**,
      refrescar el historial de 114 a **7 ms**, ver el detalle de un viático de 58 a **4 ms** y
      guardar + verlo en el historial de 172 a **11 ms**. Las 14 acciones de la prueba bajaron de
      **1.567 ms con 30 conexiones** a **766 ms con 0 conexiones**.
13. **Nadie pierde lo que estaba capturando (memoria temporal).** Las vendedoras llenan el viático y a
    veces alguien cierra el sistema —o se apaga la computadora— antes de guardarlo, y se perdía todo
    lo escrito. Ahora:
    - **La pantalla guarda sola** lo que se lleva escrito: cada **20 segundos** y **al cerrar la
      ventana**. Lo guarda en la base en uso, **por usuario** (el de la clave), así queda igual de
      bien en una computadora sola o contra la base central.
    - **Al volver a entrar** a «Generar / revisar / ajustar viáticos» con **ese mismo usuario**, el
      sistema avisa que quedó un viático a medio llenar («hoy a las 14:05»), muestra un resumen
      (encargado, destino, km, cliente y cuántos acompañantes) y pregunta si quiere recuperarlo tal
      como estaba. Si se estaba **editando** un viático, se recupera como edición de ese mismo
      número; si ese viático ya se guardó (o se anuló) en otra computadora, se recupera como viático
      **nuevo** para no pisar nada.
    - También hay un botón **🕘 RECUPERAR LO ÚLTIMO** en la barra de la captura, y la recuperación
      queda anotada en la bitácora («RECUPERÓ LO QUE ESTABA LLENANDO»).
    - **El borrador se borra solo**: al guardar el viático, al usar **🧹 LIMPIAR / CANCELAR** y a los
      **30 días** los que nadie reclamó (se revisan al abrir el sistema). Abrir la pantalla y cerrarla
      sin escribir nada **no** deja ningún aviso para la próxima vez.





