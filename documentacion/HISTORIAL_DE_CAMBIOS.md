<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Guía de implementación — Sistema de Viáticos Miempresa

> **Nota:** este documento es el **historial** de cómo se fue construyendo el sistema
> (versión por versión, con el detalle de cada cambio). Es de consulta, no hace falta
> leerlo para usar el sistema. Las guías actuales son:
> `GUIA_DEL_SISTEMA.md` (todo lo que hace el sistema), `PRUEBA_EN_2_PCS.md` (la prueba
> en dos computadoras) y `SERVIDOR_POSTGRES.md` (montar el servidor).


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
6. El calendario visual es propio del sistema (no requiere librerías externas). Para importar listas de empleados o clientes desde Excel sí se necesita `openpyxl` (`pip install -r requirements.txt`).
7. Para probar en un equipo sin Python: doble clic en `EMPAQUETAR_EXE.bat` (necesita `pip install pyinstaller`) y copie `dist\Sistema_Viaticos.exe`. Los datos se crean en la carpeta `data` que aparece junto al ejecutable.

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

- Calendario visual propio: se abre con el botón 📅 y permite navegar mes a mes, año a año, volver a "Hoy" y elegir el día.
- La caja de texto acepta `dd/mm/aaaa` digitado a mano.
- No depende de librerías externas.

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
- Desayuno del día de salida: se paga si sale a la hora límite o antes.
- Almuerzo y merienda del día de regreso: se pagan si regresa a la hora límite o después.
- Hospedaje: por cada noche cuando el regreso es en fecha posterior.
- Agua: por cada día.
- Combustible normal: `km × tarifa por km`.
- Si se ingresa efectivo de combustible mayor que cero, ese valor reemplaza al cálculo por km.
- Valor de cajero: redondeo hacia arriba al múltiplo configurado.

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

---

## Novedades de la versión 2 (ajustes, chofer y justificación)

1. **Chofer independiente del encargado**: en la pantalla de viático hay un campo "Chofer real". Puede ser el encargado o cualquier acompañante. Solo esa persona recibe km, peaje y combustible. El encargado lleva sus viáticos normales y el campo "Transp./Otros".
2. **Tres cuadros de recibo**: "Recibo N° 1, 2 y 3" en la generación y visibles en la justificación; además un "Recibo ajuste" por cada ajuste.
3. **Ajustes de viático (mismo número, más transferencias)**: en Historial, con un viático seleccionado pulse **"➕ Ajustar viático"**. Se cargan los mismos datos/personas y usted cambia las fechas del periodo adicional. Se permite cualquier cantidad de ajustes (los usuarios pidieron hasta 4). En el detalle aparecen como `[AJUSTE n]` y en la lista de ajustes con su recibo.
4. **Impresión diferenciada**: botones 🖨 **Original**, 🖨 **Ajuste** (elige cuál; doble clic en la lista de ajustes también lo imprime) y 🖨 **General** (original + cada ajuste en secciones con su propio total y un total general al final, como pidieron).
5. **Justificación**: muestra las horas de llegada/salida al **trabajo** y las de llegada/salida a **Miempresa**, los 3 recibos, y abajo el espacio de **devolución de dinero** (monto + motivo) cuando los gastos no agotan lo entregado. El botón **"✅ JUSTIFICAR VIÁTICO"** guarda el estado JUSTIFICADO, que se ve en el historial; **"↩ Volver a pendiente"** lo reabre para correcciones.
6. **Impresión de justificación**: botón **"🖨 IMPRIMIR JUSTIFICACIÓN"** con el mismo formato del Excel (gastos, totales por columna, entregado/respaldado/saldo, devolución y firmas).

Nota: la justificación siempre toma el **viático general** (original + todos los ajustes) para cuadrar todo lo entregado contra todo lo gastado.

---

## Ajustes de la versión 2.1 (segunda ronda de observaciones)

1. **Recibos a un costado**: los 3 recibos quedaron apilados a la derecha de "Datos generales". Se eliminó el campo "Recibo ajuste": los números de recibo son un control único del viaje (original o ajuste) y se anotan en los 3 cuadros.
2. **Chofer**: ahora se llama solo "Chofer" y se puede elegir libremente de la lista completa de empleados. Si el chofer elegido no está entre los viajeros, el sistema lo agrega automáticamente como acompañante en AUTO (respeta el máximo de 3 en el auto).
3. **Ajuste de viático**: la fecha/hora de SALIDA se bloquea en modo ajuste (mensaje en rojo) porque ese viático ya se entregó; el sistema reconoce hasta qué día se dio viático (regreso original) y solo permite avanzar el REGRESO a la fecha real. Calcula automáticamente el extra por cada día adicional: desayuno + almuerzo (merienda si regresan después de las 21:00), hospedaje y agua. **No agrega taxis ni dinero de transporte** (el pasaje de bus no varía porque aún no lo usan para volver). Tampoco agrega combustible/km/peaje.
4. **Justificación reconstruida**: vuelve al estilo anterior (buscar, lista, datos precargados, detalle de gastos, digitar gasto, facturas, resumen y cierre) pero a **dos columnas** (ventana 1280x720) para que quepa en pantallas pequeñas: izquierda = viáticos + datos + cierre; derecha = gastos + digitar + facturas.
5. **Recibos editables en justificación**: la persona que justifica puede completar el N°2 o N°3 de recibo si en la generación solo se alcanzó a registrar uno ("💾 Guardar recibos"); al JUSTIFICAR se guardan automáticamente.
6. **Impresión de justificación**: formato exacto del Excel 2026 (mes/año, BENEFICIARIO, PROYECTO, VIAJA A, DÍAS, CAMIONETA, PERSONAS, fechas/horas de viaje, Maneja ir/volver, Recibo N°, tabla de 14 columnas, VALOR ENTREGADO/RESPALDADO/SALDO, observación JEP y firmas de Elaborado/Revisado por).
7. Fix: `actualizar_ajuste_viaje` convertía mal la fila de estado (error de guardado al re-editar un ajuste).

---

## Ajustes de la versión 2.2 (tercera ronda de observaciones)

1. **Datos de prueba eliminados**: se limpiaron de la base los viáticos y empleados de prueba; la numeración continúa desde el N° 142. Las pruebas futuras usan la variable de entorno `VIATICOS_DATA` apuntando a una carpeta temporal, sin tocar la base real.
2. **Separadores de ajuste**: en la vista previa del ajuste y en el detalle del historial aparece una línea sombreada "AJUSTE N° n — VALOR NUEVO A ENTREGAR" que separa el original de cada ajuste con su listado de empleados.
3. **Justificación**: al terminar de justificar, la pantalla vuelve limpia a la lista para elegir otro viático.
4. **Datos precargados visuales**: se reemplazó el bloque de texto por una cuadrícula de etiqueta/valor (beneficiario, proyecto, viaja a, vehículo, maneja, ajustes, salida/llegada/salida del trabajo/regreso, estado, personas).
5. **Digitar gasto por concepto**: se elige QUÉ se está justificando (Hospedaje, Combustible/Orden, Buses, Taxis/Camionetas, Alimentación, Peaje, Otros) y el valor de la factura va directo a esa columna. Varias facturas = varios gastos, uno por concepto.
6. **Facturas en imagen**: al adjuntar JPG/PNG/etc. el sistema los convierte automáticamente a PDF (con Pillow) y guarda el PDF en respaldos.
7. **Devolución en ambos sentidos**: en "Resumen y cierre" hay "Devuelve a Miempresa $" (sobró dinero) y "A favor del empleado $" (gastó más de lo entregado); el sistema sugiere el valor automáticamente según el saldo. Ambos valores salen en la impresión de la justificación.

---

## Ajustes de la versión 2.3 (cuarta ronda de observaciones)

1. **"Medio encargado" eliminado**: el encargado siempre viaja en el vehículo de la empresa (AUTO). Se quitó ese selector del formulario.
2. **Botón "🆕 Nuevo viático"** en la barra del Historial: limpia el formulario y va directo a la pestaña de generación.
3. **Agregar empleados dentro del ajuste**: la sección de empleados adicionales sigue activa en modo ajuste; un empleado nuevo agregado allí recibe el mismo valor nuevo a entregar por día adicional.
4. **Beneficiario vs Creado por**: en la justificación, "Beneficiario" es el ENCARGADO del viaje (quien viaja) y "Creado por" es la persona que generó el viático en el sistema. En la impresión, BENEFICIARIO muestra al encargado.
5. **Elaborado por**: nuevo campo en "Resumen y cierre" de la justificación, predeterminado a **el usuario que justifica** (editable, se guarda por viático y sale en la impresión).
6. **Observación libre**: la impresión ya no trae el texto fijo de la JEP; el responsable escribe la observación (a veces es a favor de la empresa, a veces del empleado).
7. **Botón "Actualizar" eliminado** del área de gastos: hacía lo mismo que "Guardar gasto". Ahora "Guardar gasto" sirve para crear y para modificar el gasto seleccionado.

---

## Ajustes de la versión 2.4 (quinta ronda de observaciones)

1. **Calendario en todo el sistema** (con la librería `tkcalendar` instalada): las fechas de generación, ajustes y justificación abren el mini-calendario. Si la librería no está instalada, el campo sigue funcionando como caja de texto para digitar la fecha.
2. **Menú principal simplificado**: se eliminó el botón redundante "Revisar y modificar viáticos" (llevaba al mismo lugar). Quedan: Generar/Revisar/Ajustar, Justificar, Parámetros... y Salir.
3. **Recálculo automático del ajuste**: al cambiar la fecha u hora de REGRESO en un ajuste, la vista previa se recalcula sola, sin necesidad de tocar la hora. El botón muestra "💾 GUARDAR AJUSTE" en modo ajuste.
4. **Mensajes eliminados**: se quitó el aviso en rojo de "salida bloqueada" y las alertas del cálculo del ajuste (solo avisan al guardar si algo falta). La salida sigue bloqueada en modo ajuste, pero sin texto rojo.
5. **Textos de separadores acortados**: las líneas sombreadas ahora dicen "═ ORIGINAL ═" y "═ AJUSTE N° n · NUEVO ═" para no cortarse en la tabla.
6. **Actualización incluida**: paquete re-empacado SIN la carpeta `data/` (para no sobrescribir la base de datos real al descomprimir).

---

## Ajustes de la versión 3.0 (sexta ronda de observaciones)

1. **Efectivo sugerido de combustible**: se eliminó el botón "Sugerir". En su lugar hay un cuadro fijo a la derecha del formulario con el título "EFECTIVO SUGERIDO COMBUSTIBLE", el valor calculado debajo (km × valor por km, parámetro `valor_combustible_km`) y el botón "USAR" al pie. El número se recalcula automáticamente al cambiar los km, el cantón o cualquier dato del viaje.

2. **Calendario funcional**: se reemplazó `tkcalendar` por un calendario propio (`dateentry.py`). Ahora las flechas ‹ › cambian de mes y « » cambian de año sin límites, se puede volver a "Hoy" y elegir cualquier día; también acepta la fecha escrita a mano. Antes el selector se quedaba pegado en el mes del viaje.

3. **PDF consolidado automático al justificar**: al pulsar ✔ JUSTIFICAR el sistema une todos los respaldos del viático en `VIATICO_###_COMPLETO.pdf` sin pedir nada más. (En la versión 3.1 se quitó el botón manual que existía para revisarlo antes; ver más abajo.)

4. **Respaldos ya no aparecen vacíos**: el PDF consolidado se registra en la base de datos (concepto "PDF CONSOLIDADO") y la ventana 📁 RESPALDOS ahora muestra además los archivos que estén en la carpeta `data/respaldos/viatico_###` aunque no estén registrados (concepto "EN CARPETA"). Al consolidar, la lista se refresca sola.

5. **Importación de empleados desde Excel** (pestaña 👥 Empleados de Parámetros): botón "📥 Importar Excel" que lee la primera columna del archivo `.xlsx`, ignora la fila de encabezado y agrega los nombres sin duplicar. Informa cuántas filas leyó y cuántos empleados nuevos creó.

6. **Catálogo de clientes** (nueva pestaña 🧑‍💼 Clientes de Parámetros): permite agregar, eliminar e importar la lista de clientes desde Excel, igual que los empleados.

7. **Cliente y proyecto con búsqueda**: en el formulario del viático el campo "Cliente y proyecto" dejó de ser una caja simple; ahora es un desplegable editable con búsqueda automática sobre el catálogo de clientes (igual que Empleados y Provincias). El nombre que se escriba queda guardado en el catálogo al grabar el viático.

8. **Dependencia nueva**: `openpyxl` (para leer los Excel). Se agregó a `requirements.txt`. `tkcalendar` ya no se usa.

---

## Ajustes de la versión 3.1 (séptima ronda de observaciones)

1. **Sin botón de consolidar en ninguna pantalla**: se quitó "📑 Consolidar PDF único" de la ventana de Justificar y "📑 Consolidar PDF" de la ventana de Respaldos. La unión de los respaldos en un solo PDF es **automática** al pulsar ✔ JUSTIFICAR.

2. **Respaldos como lista completa**: la ventana 📁 RESPALDOS ya no exige buscar un número. Al abrirse muestra **todos** los respaldos de todos los viáticos (N° de viático, archivo, concepto, quién lo subió y fecha), ordenados del viático más reciente al más antiguo. La búsqueda queda como opción: escribe el N° de viático, el nombre del archivo, el concepto o la persona, o pulsa "↺ Ver todos" para volver a la lista completa. Se agregó el botón "↺ Actualizar".

3. **Ver el justificado desde el Historial**: en la pestaña 📋 Historial (pantalla de generar viáticos) se agregó el botón "👁 Ver justificado". Abre la pantalla de Justificación con ese viático ya seleccionado, mostrando sus gastos, facturas, respaldos y cierre.

4. **Ver el viático original desde Justificar**: se agregó el botón "👁 Ver viático original", que abre una ventana de solo lectura con todos los datos del viático (encargado, chofer, cliente, vehículo, órdenes, km, recibos, fechas, estado, notas) y el detalle calculado completo, separando ORIGINAL de cada AJUSTE con sus totales.

---

## Ajustes de la versión 3.2 (empaquetado para pruebas)

1. **Ejecutable portátil**: se agregó `EMPAQUETAR_EXE.bat`, que con PyInstaller genera `dist\Sistema_Viaticos.exe` (≈ 26 MB) en un solo archivo. No necesita tener Python instalado para ejecutarse.
2. **Los datos quedan junto al ejecutable**: en modo empaquetado la base y los respaldos se guardan en la carpeta `data` que se crea al lado del `.exe`. Se agregaron `carpeta_app()`, `recurso()` y un `dir_datos()` que reconoce el modo empaquetado. Para probar con otros datos, coloque un archivo `data_path.txt` junto al `.exe` con la ruta de la carpeta `data` que quiera usar.
3. **Logo dentro del paquete**: `image.png` se incluye con `--add-data` y se ubica con `db.recurso()`, así funciona igual en código fuente y en `.exe`.
4. **Aviso de error al iniciar**: como el `.exe` no tiene consola, `main_gui.py` muestra el detalle de cualquier fallo en una ventana.
5. **Autodiagnóstico**: ejecutando el `.exe` con la variable de entorno `VIATICOS_SELFTEST=1` se escribe `autodiagnostico.txt` junto al ejecutable, con el estado de la base de datos, Tkinter, Pillow, PyPDF2 y openpyxl, además de una prueba real: imagen → PDF, unión de PDFs y creación/lectura de un Excel.
6. **Verificación realizada**: el `.exe` arranca correctamente, crea la base (13 tablas, 31 empleados, 24 provincias, 204 cantones) y todas las dependencias quedaron incluidas. La misma aplicación ejecutada desde el código fuente sigue funcionando sin cambios.

---

## Ajustes de la versión 4.0 (usuarios, superusuario, informe de actividad y ajustes de valores)

1. **Inicio de sesión obligatorio** (`ui_login.py`, nuevo): al abrir el sistema pide **usuario y clave**.
   Usuarios de creación de viáticos: **VENDEDOR1 a VENDEDOR4** (clave `1234`).
   Justificación: **JUSTIFICA1** (clave `1234`). El usuario se escribe sin importar
   mayúsculas y también se acepta una parte del nombre.
   Los usuarios `admin` / `justifica` de versiones anteriores se eliminan al migrar.

2. **Todos pueden hacer todo**: los usuarios normales (vendedoras y justificación)
   pueden ver y modificar parámetros, empleados, clientes, vehículos, rutas, viáticos,
   ajustes y justificación. No hay pantallas restringidas para ellos.

3. **Superusuario oculto**: existe un superusuario que **no aparece en ninguna lista ni
   pantalla**; solo entra escribiendo usuario y clave. Sus credenciales se entregan
   aparte (no se documentan aquí por seguridad). Al entrar ve dos opciones extra:
   **🕵 INFORME DE ACTIVIDAD (AUDITORÍA)** y **👥 USUARIOS DEL SISTEMA**.

4. **Informe de actividad** (`ui_bitacora.py`, nuevo): registra *todo* lo que hacen los
   usuarios con fecha/hora, usuario, rol, acción, módulo, referencia y detalle
   (creó/editó viático y ajuste, anuló, justificó, reactivó, recibos, gastos, facturas,
   parámetros, empleados, clientes, vehículos, rutas, usuarios y los ingresos/salidas).
   Tiene filtros por usuario, acción, rango de fechas y texto libre, resumen por usuario
   y por acción, **exportación a Excel y CSV** e impresión/PDF.
   Toda la información viene de la tabla nueva `bitacora`.

5. **Administración de usuarios** (`ui_usuarios.py`, nuevo): el superusuario puede crear
   usuarios nuevos de ventas o de justificación, cambiar clave/nombre/rol y dar de baja.
   El superusuario no se lista, no se edita y no se puede eliminar.

6. **Nombre del usuario en el sistema**: el menú y la barra amarilla de cada pantalla
   muestran quién inició sesión; en el viático el campo **«Creado por»** y en la
   justificación **«Elaborado por»** se llenan solos con ese nombre.

7. **Ajuste de viático con más conceptos**: además de los días adicionales, el ajuste
   ahora acepta **efectivo para combustible** (se puede digitar un valor mayor al
   sugerido o pulsar **USAR** para tomar el *efectivo sugerido de combustible*),
   **Parq./Peaje** y **Transp./Otros del encargado**. Se suman al total/cajero del
   ajuste y salen en su columna. Un ajuste nuevo arranca con esos tres campos en cero
   (lo del original ya se entregó) y al reeditarlo se recuperan sus propios valores.

8. **Explicación del valor de una factura**: en «Digitar gasto / factura» hay un cuadro
   nuevo **📝 Explicación** donde se escribe el motivo por el que una factura se respalda
   con un valor distinto al impreso (por ejemplo, factura de $30,00 respaldada por $25,00
   porque el empleado cubrió $5,00). La lista de gastos muestra la columna **EXPLICACIÓN**
   y la justificación impresa la agrega al final de la tabla, más el bloque
   **«EXPLICACIÓN DE VALORES DE LAS FACTURAS»**. No se pide ni se imprime el «valor real
   de la factura»: ese dato se compara directo contra la factura en los respaldos.

9. **Respaldos: un solo PDF por viático**: al pulsar ✔ JUSTIFICAR se unen todos los
   respaldos en `VIATICO_n_COMPLETO.pdf` y **se borran los archivos individuales** y sus
   registros. Si se subieron 10 imágenes, en la carpeta del viático queda únicamente el
   completo (que es el que sale en 📁 RESPALDOS). Mientras el viático no se justifique se
   conservan los archivos sueltos porque son la base de la unión; si se reactiva y se
   vuelve a justificar, el completo anterior se usa como base y se le agregan las
   facturas nuevas, sin perder nada. Si la unión falla, no se borra ningún archivo.

10. **Ajuste de viático con más conceptos**: el ajuste acepta **efectivo para combustible**
    (el sugerido se calcula con el km del **viático original**, porque el lugar y la ruta
    no cambian: se puede pulsar **USAR** o escribir arriba un valor mayor), **Parq./Peaje**
    y **Transp./Otros del encargado**; se suman al total y al cajero del ajuste. Un ajuste
    nuevo arranca con esos tres campos en cero (lo del original ya se entregó) y al
    reeditarlo se recuperan sus propios valores.

11. **Diseño más limpio**: se quitaron los textos de ayuda grises del cuadro de
    explicación y del cuadro de efectivo sugerido; el cuadro del sugerido queda centrado
    (encabezado, valor y botón USAR) y la pantalla de ingreso se simplificó.

12. **Migración automática**: al abrir por primera vez se crean la tabla `bitacora` y las
    columnas nuevas (`gastos.nota`, `usuarios.creado_el`), y se dan de alta los seis
    usuarios del sistema. No se pierde ningún viático, ajuste, gasto ni respaldo.

13. **Importación de las listas de personal y clientes**: los botones **📥 Importar Excel**
    de Parámetros (Empleados y Clientes) ahora **detectan solos la columna correcta**
    (buscan el encabezado «Nombre» o «Cliente»), aunque el archivo tenga títulos arriba y
    muchas columnas. Se cargaron:
    - el listado de personal de la empresa → **todos los empleados** del archivo;
    - la lista de clientes de la empresa → tomando **solo el nombre**
      (no se importan RUC, ciudad, contacto ni grupo).
    Reimportar el mismo archivo no duplica nada. La lista de empleados quedó igual al
    Excel; se conservó el nombre suelto que ya estaba usado en un viático existente.

14. **Nombres completos en el sistema**: para entrar se sigue escribiendo el **usuario
    corto** (VENDEDOR1, VENDEDOR2, VENDEDOR3, VENDEDOR4, JUSTIFICA1), pero los campos
    **«Creado por»** (viático) y **«Elaborado por»** (justificación) firman con el nombre
    completo del listado de personal. Si el superusuario cambia ese nombre a mano, ya no se
    pisa.

15. **Pantalla de ingreso más limpia**: el contenido (logo, títulos, campos y botones)
    quedó **centrado** y la ventana se abre centrada en la pantalla; el campo **Usuario se
    escribe siempre en MAYÚSCULAS**, incluso al pegar texto. La clave sigue distinguiendo
    mayúsculas de minúsculas.

---

## Versión 5.0 — Base de datos CENTRAL en el servidor (PostgreSQL en Docker)

16. **Una sola base para las 5 máquinas**: el sistema puede trabajar contra una base
    PostgreSQL que corre en Docker en el servidor; cada máquina usa su `.exe` y todos ven
    los mismos datos (empleados, vehículos, parámetros, clientes, viáticos, ajustes,
    justificaciones, gastos, respaldos, usuarios y bitácora).
    - **`configuracion.py`** (nuevo) lee/guarda `config.json` junto al programa o al `.exe`.
      Si no existe el archivo, todo sigue funcionando con la base local SQLite.
    - **`bd.py`** (nuevo) es la capa de conexión: traduce lo que cambia entre SQLite y
      PostgreSQL y entrega las filas igual que antes, así que **la lógica no cambió**.
    - **`database.py`** conserva todas las funciones; se corrigieron los puntos que
      dependían de SQLite y ahora el consecutivo de viáticos **nunca repite número**.
    - **`migracion.py`** (nuevo) copia la base local completa a la central.
    - **`ui_conexion.py`** (nuevo, superusuario) es la pantalla **🔌 CONEXIÓN / BASE DE
      DATOS**: elegir local o central, probar la conexión, guardarla y «⬆ Subir mis datos
      locales a la central».
17. **Facturas centralizadas**: los respaldos se pueden guardar **dentro de la base**
    (recomendado: todas las máquinas los ven, sin carpetas compartidas) o en una
    **carpeta compartida** del servidor. Se mantiene que al justificar queda un solo PDF
    por viático (`VIATICO_n_COMPLETO.pdf`).
18. **Carpeta `docker/`** (nueva): `docker-compose.yml` (PostgreSQL 16, zona horaria de
    Ecuador), `respaldar_base.bat` (respaldo diario con `pg_dump`) y **`LEEME_DOCKER.md`**
    con el paso a paso para probar en su equipo y luego montarlo en el servidor.

    Probado con PostgreSQL 16.15 en Docker: la regresión completa (viáticos, ajustes,
    gastos, respaldos en base y en carpeta, unión de facturas, bitácora, reportes y todas
    las ventanas) y la migración real de los datos (32 empleados, 755 clientes, 7 viáticos,
    3 respaldos con sus PDF, bitácora incluida).

19. **Numeración por año automática**: la numeración vuelve a empezar en 1 cada año
    (el año se toma de la fecha del viaje) y en los informes se muestra como
    **001/2026**. Internamente se guarda `año*1000+número` para que los viáticos de
    años distintos nunca se mezclen, y el consecutivo se toma con bloqueo de fila
    (nunca se repite, aunque dos máquinas guarden a la vez). Las bases con
    numeración antigua se renumeran solas al abrir, moviendo también gastos,
    respaldos y carpetas, y dejando registro del cambio.
20. **Arranque configurable por el superusuario**: en **🔌 CONEXIÓN / BASE DE DATOS**
    se ve el resumen de numeración por año y se puede **fijar el año y el número
    desde el que se empieza** (para pasar de las pruebas a los viáticos reales).
    Si se pide un número ya usado, el sistema toma el siguiente libre.
21. **Zoom de la interfaz para pantallas chicas** (monitores de 20", escalado de Windows al 125 %).
    Se midió lo que pide cada ventana con las pantallas reales: justificación **1481 px** de ancho y
    viáticos **889 px** de alto, más las tablas, que por tener 25 y 16 columnas de ancho fijo
    obligaban a la ventana a medir **1655** y **2094** px: por eso los botones de la derecha y de
    abajo quedaban fuera de la pantalla (y la barra horizontal de la tabla quedaba fuera también, o
    sea que no se podía llegar al resto de las columnas).
    - **`tema.py`**: nuevas funciones `preparar_zoom()`, `zoom_automático()`, `zoom_guardado()`,
      `guardar_zoom()`, `zoom_texto()`, `px()` y `preparar_dpi()`. El zoom se aplica con
      `tk scaling` **antes** de crear los controles de cada ventana (Tk crea las letras en ese
      momento y no las recalcula después), se guarda en `config.json` → `"interfaz"` → `"zoom"`
      (`0` = automático) y se cambia en **🔌 CONEXIÓN / BASE DE DATOS → «Tamaño de la pantalla en
      esta computadora»** (solo superusuario), así que **cada PC guarda el suyo** y no afecta a las
      demás (el sistema se reinicia solo para aplicarlo, ver punto 23). También se escalan los
      espacios del tema (alto de fila de las tablas, relleno de botones, cajas y pestañas) y el
      tamaño que pide cada ventana.
    - **Tablas que ya no ensanchan la ventana**: el marco de la tabla de vista previa
      (`ui_viaje.crear_tabla`) y el de «Detalle de gastos» (`ui_ajustes`) ahora piden 300×200 y
      420×140 con `propagate(False)` y ocupan el espacio disponible; además «Detalle de gastos» ganó
      **barra horizontal** y el ancho de las columnas acompaña al zoom (`tema.px`). El campo
      «Explicación» del gasto pasó de 95 a 60 caracteres y se estira con la ventana.
    - **`preparar_dpi()`** avisa a Windows que el programa se encarga del escalado (sin esto la
      imagen se estira y se ve borrosa con el 125 %/150 %); se desactiva con
      `"interfaz": {"dpi_consciente": false}`.
    - Comprobado con una pantalla simulada de **1366×768** y una base SQLite temporal: en la ventana
      de viáticos se ven todos los controles (observaciones, recibos, botón GUARDAR y el estado) y
      en la de justificación todo entra desde el **80 %**. Zoom automático resultante:
      1366×768 al 100 % → 82 %; 1600×900 al 125 % → 78 %; 1920×1080 → 100 %; 1024×768 → 66 %.
    - El autodiagnóstico informa `pantalla: 1920 x 1080 · zoom: Automático (100 %) · dpi consciente: True`.
22. **Informe del viático: totales alineados y COMBUST. sin números raros.** Dos arreglos en
    `reportes._tabla_viatico` que se vieron al revisar el informe general del viático 001/2026:
    - La fila **TOTALES** armaba **una celda vacía de más**, así que todos los totales salían
      **corridos una columna** hacia la derecha: los kilómetros aparecían bajo DESAY., el total bajo
      PARQ./PEAJE, y el último valor (CAJERO) se salía de la tabla. Ahora el KM va en la columna KM
      y cada total en la suya. Lo mismo en el bloque **TOTAL GENERAL**: su título usaba
      `colspan="22"` y la tabla tiene **25** columnas, así que TOTAL y CAJERO salían una columna
      corridos; ahora el `colspan` es **23**.
    - La columna **COMBUST.** mostraba el **número de orden pegado al valor** («01 50.00», «01 -»),
      que se leía como un número equivocado. Además el caso «EFECTIVO …» **nunca se activaba**
      porque consultaba `combustible_efectivo`, columna que no existe (la real es
      `efectivo_combustible`). Ahora la columna muestra **solo el valor** (`fmt(combustible)`),
      igual que la vista previa de la pantalla, y la orden sigue en el encabezado (**ORDEN COMB.**),
      junto con el efectivo (**EFECTIVO COMB.**).
    - Comprobado generando el informe del viático 001/2026 (original + 2 ajustes): las 12 filas de
      datos y las 3 filas de totales tienen **25 celdas** cada una y cada total cae en su columna.
23. **El tamaño de pantalla (zoom) pasó a la pantalla de superusuario.** La barra
    **🔍 Tamaño de la pantalla** de la primera fila del menú principal se veía recargada; se quitó de
    ahí y ahora es una sección de **🔌 CONEXIÓN / BASE DE DATOS**: «Tamaño de la pantalla en esta
    computadora», con las mismas opciones **Automático · 100 · 90 · 80 · 70 · 60 %**. El valor se
    guarda en el **`config.json` de esa computadora** (al lado del `.exe`), no en la base, así que
    **cada equipo recuerda su propio tamaño** y no cambia el de las demás ni lo que se imprime. Al
    guardar, el sistema avisa y, si se acepta, se cierra y se vuelve a abrir solo:
    `tema.reiniciar_sistema(ventana)` reemplaza al `_reiniciar` que tenía el menú (sube hasta la
    ventana raíz, así funciona desde cualquier pantalla).
24. **Pantallas de superusuario más limpias.** Se quitaron las notas que solo repetían lo que ya se
    veía en la pantalla: «Solo el superusuario ve este informe.» (informe de actividad),
    «El superusuario no aparece en esta lista y no se puede modificar ni eliminar.» (usuarios), el
    párrafo largo bajo la numeración y el cierre del bloque de ayuda de la pantalla de conexión
    («Los cambios se aplican al instante…»). El bloque de ayuda se mantiene, con el título «Para
    dejar el servidor en marcha», porque son los pasos de instalación del servidor (también están en
    `documentacion\SERVIDOR_POSTGRES.md`). En **Parámetros y catálogos** se quitó la nota «Nota:
    parqueadero/peaje es un valor sugerido…», porque el nombre del propio campo ya dice que es un
    valor sugerido por viaje.



## Versión 6.0 — Interfaz nueva (PySide6) y ajustes de pantalla

La interfaz se reescribió con **PySide6 (Qt)**: mismas funciones, mismas reglas de cálculo
(`calculos.py` no se tocó) y reportes idénticos (`reportes.py`); los colores de marca siguen
siendo los mismos (AZUL `#1F1CFF` y AMARILLO `#FACC00`). Se eliminaron los archivos de la
interfaz anterior (`ui_*.py`, `tema.py`, `dateentry.py`, `main_gui.py`).

1. **Una pantalla, un archivo**: `q_login.py` (ingreso), `q_menu.py` (menú principal),
   `q_conexion.py`, `q_viaje.py` (viáticos), `q_ajustes.py` (justificación), `q_admin.py`,
   `q_bitacora.py`, `q_respaldos.py`, `q_usuarios.py`. El aspecto vive en `qt_tema.py` (colores,
   hoja de estilo QSS y escalado) y las piezas repetidas en `qt_comunes.py` (tarjetas, tablas,
   campos de fecha y hora, insignias de estado, avisos y exportación a Excel). `colores.py` guarda
   los colores de marca que también usa la impresión.
2. **Todo entra en la pantalla**: las tarjetas, los campos y las letras son compactos y las
   ventanas grandes se abren maximizadas. **La justificación completa entra sin desplazarse.**
3. **Excel por documento** (`qt_comunes.exportar_excel_documento`): en **Viáticos → Historial**
   los botones *Original · Ajuste · General*; en la pestaña de captura, **📊 EXCEL**; en
   **Justificación**, **📊 Excel → Lista de viáticos / Justificación**.
4. **Autodiagnóstico**: `set VIATICOS_SELFTEST=1` y abrir el `.exe` escribe
   `dist\autodiagnostico.txt` (lo que depende del servidor sale como AVISO, no como falla).
5. **Séptima ronda de observaciones (pantallas, esta entrega)**:
   - «Encargado, chofer, destino y acompañantes» es **una sola tarjeta** (antes eran dos): los
     empleados adicionales quedan al lado del chofer, con su lista compacta, y el formulario ya no
     deja el medio de la pantalla vacío.
   - El **efectivo sugerido de combustible** se subió arriba a la derecha y se distingue con su
     propio color (`QFrame#tarjetaSugerido` en `qt_tema.py`); el botón **USAR** no cambió.
   - En la justificación, el panel «Digitar gasto / factura» pasó de **3 pares de campos por fila
     a 2** y se quitó la casilla **TOTAL** (repetía el valor de «Valor de la factura $»).
   - **Recibos** y **Resumen y cierre** se unieron en una sola tarjeta; «Motivo» y «Nota de cierre»
     comparten fila. Junto con lo anterior, es lo que hace que la justificación entre completa.
   - Las **tablas** dejaron de pedir 192 px de alto (`qt_comunes.Tabla.sizeHint`): piden el
     encabezado más unos pocos renglones y el espacio sobrante lo reparte la pantalla.
   - **Todas las etiquetas se ajustan solas** (`qt_comunes.etiqueta` activa `setWordWrap`): un
     texto largo se reparte en dos líneas en lugar de empujar los campos fuera de la ventana.
   - **Menú de Inicio**: los recuadros se reparten todo el ancho y se quitó el recuadro «Total»
     (la suma se ve en el detalle de cada viático).
   - **Ingreso**: la ventana mide lo que ocupa su contenido (antes 460×430 fijos, ahora ~430×274).
6. Comprobaciones: `python pruebas_qt.py` (18 comprobaciones), `python pruebas_ventanas.py`
   (las 7 ventanas se arman con datos falsos) y `EMPAQUETAR_EXE.bat` + `python EMPAQUETAR_ENTREGA.py`
   para el `.exe` y el ZIP de entrega.

7. **Octava ronda de observaciones (pantallas)**:
   - **Dos formularios en una tarjeta**: «👤 Encargado, chofer y destino | 👥 Empleados
     adicionales», separados por una **línea vertical** (`qt_comunes.linea(horizontal=False)`,
     que ahora ocupa el alto disponible). Los adicionales tienen su propio formulario a la
     derecha (empleado, medio, extra, *Agregar/Quitar* y la lista debajo).
   - El **efectivo sugerido de combustible** se movió al final de la tarjeta *Fechas, horarios y
     combustible sugerido* (es un solo valor y un botón **USAR**), alineado arriba.
   - **Observaciones** volvió a ser un campo **grande**, a todo el ancho de la tarjeta de datos
     generales (antes se había estirado y quedaba chico dentro de la rejilla).
   - **Historial**: se eliminó la tarjeta/tabla «Ajustes del viático» y su constante
     `COLS_AJUSTES`. El *Detalle — original y ajustes* —que ya lista el original, cada ajuste y
     los totales— pasó a ocupar todo el ancho y es más alto. Para imprimir, exportar o editar un
     ajuste puntual hay una lista **📋 Ajuste** en la barra superior, leída por `_ajuste_elegido()`
     (si no hay ninguno elegido, se pregunta el número, como antes).
   - **Calendario**: `qt_comunes.CampoFecha` fija un tamaño mínimo al calendario
     (300×220 escalado) para que entren las **seis semanas del mes** —antes la ventanita quedaba
     corta y solo se veían los primeros días— y, con un `eventFilter` sobre `QEvent.Show`, al
     abrirse con el campo vacío muestra **el mes actual** en lugar de enero de 1900 (fecha que el
     sistema usa como «vacío»).
   - **Justificación**: el formulario de gasto pasó a **dos columnas que llenan la tarjeta** con
     la opción `rejilla(..., espacio_medio=True)` (el sobrante se reparte entre la primera y la
     segunda pareja de campos, sin estirar los campos ni ensanchar la ventana) y la **Explicación**
     quedó en su propia fila a todo el ancho; el *Detalle de gastos* es más alto.
   - **Botones dentro de una fila**: `qt_comunes.fila(...)` acepta `None` para agregar un espacio
     elástico; sin él, los botones de la fila se estiraban a lo ancho.
   - Medido con datos de prueba: **viáticos 1920×1000 → sin barras de desplazamiento** y
     **justificación 1920×1000 → sin barras** (a 1536×800: 68 px de ancho y 10 px de alto).

8. **Novena ronda de observaciones (fallas al guardar y detalles de pantalla)**:
   - **Falla grave corregida — no se guardaba el viático**: al reescribir la pantalla en
     PySide6 quedaron fuera tres nombres del módulo `datetime` en `q_viaje.py`. Por eso
     `_hora()` lanzaba `NameError: name '_dtime' is not defined`, `_construir_filas()` no
     terminaba nunca y, en cadena, **la vista previa salía vacía, GUARDAR VIÁTICO no hacía
     nada, el Historial no mostraba el viático y no se podía probar ni el ajuste ni la
     justificación**. Se agregó el import que faltaba:
     `from datetime import date as _fecha, time as _dtime, timedelta`.
     Con eso quedó comprobado, sobre una **copia** de la base, el recorrido completo:
     abrir → elegir datos → **guardar** (VIÁTICO N° 1 con 1 empleado) → verlo en el
     **Historial** (lista + detalle) → **Ajustar** (Ajuste N° 1 del viático N° 1) → verlo en
     la **Justificación**. También se pasó `pyflakes` por todos los módulos: no queda ningún
     nombre sin definir (solo avisos de imports que no se usan).
   - **Fechas del viaje**: al abrir la pantalla las cuatro fechas (salida/regreso de
     Miempresa y llegada/salida del trabajo) arrancan **en el día de hoy** y de ahí se
     escoge la que se necesite (`q_viaje._poner_fechas_hoy()`, también al pulsar
     LIMPIAR). Antes salían en blanco.
   - **Efectivo sugerido junto a las fechas**: pasó a ser un renglón compacto
     `Efectivo sugerido  $0.00  [USAR]` pegado a la derecha del bloque de fechas (ya no
     queda al otro extremo de la tarjeta, que era lo que se veía mal) y la tarjeta de
     *Fechas, horarios y combustible sugerido* bajó de 187 a **146 px** de alto.
   - **Vista previa con más espacio**: al adelgazar la tarjeta de fechas y dejar la lista
     de adicionales en 60 px, la tarjeta *Vista previa — original o ajuste actual* pasó de
     175 a **234 px** con la tabla de 189 px, y sigue **sin barras de desplazamiento**
     (`viáticos 1920×1000 → h=0, v=0`; justificación 1920×1000 → h=0, v=0).
   - **Ingreso centrado**: se centra de verdad en la pantalla (`showEvent` + `move()` con el
     ancho/alto reales de la ventana), con el usuario/clave en campos de 250 px centrados y
     etiquetas alineadas, y los botones y el texto de conexión en el centro (430×280 px).
   - **Chofer**: se comprobó que el campo **no se llena solo** (queda vacío al abrir la
     pantalla, al poner el foco, al abrir la lista con Alt+↓, al pulsar Enter, al pulsar Tab
     y al escribir); solo se llena cuando se elige a alguien o cuando se edita/ajusta un
     viático que ya tenía chofer guardado.
   - Comprobaciones de esta ronda: `pruebas_qt.py` **18 de 18**, `pruebas_ventanas.py`
9. **Décima ronda de observaciones (Excel, justificación y pantalla limpia)**:
   - **Excel — falla corregida**: al exportar la justificación salía el aviso *«Invalid
     character / found in sheet title»*. El nombre de la hoja y el del archivo llevaban el
     «N° 001/2026» del viático y **Excel no admite la barra**. Ahora
     `qt_comunes._titulo_hoja()` y `qt_comunes.nombre_archivo()` limpian esos caracteres
     (`\ / : * ? [ ]` y `" < > |`): la hoja queda «Justificación 0012026» y el archivo
     `justificacion_001-2026.xlsx`. La limpieza se hace en `pedir_ruta_guardar()`, así vale
     para cualquier exportación (los Excel de viáticos, la lista de viáticos y el informe de
     actividad).
   - **Excel más lleno**: el encabezado ya no queda en dos columnas perdido a la izquierda.
     El título va **unido a todo el ancho** de la tabla (fondo azul, letra blanca), cada par
     rótulo/valor ocupa una fila (rótulo en gris a la izquierda y **el valor unido hasta la
     última columna**, con el texto ajustado y la fila más alta cuando el texto es largo, como
     la lista de personas), el encabezado de la tabla queda **congelado** (`freeze_panes`) para
     que al bajar sigan viéndose los títulos, y la columna de los rótulos se ensancha según el
     texto más largo. Comprobado con los tres Excel: viáticos, formulario y justificación.
   - **Justificación — datos diferenciados**: el bloque *Datos del viático seleccionado* dejó
     la cuadrícula amontonada y ahora son **franjas alternadas** (`QFrame#bandaDatos`: una
     clara con borde redondeado y la siguiente blanca), dos datos por renglón y los textos
     largos (personas) a todo el ancho: cada dato se distingue del de arriba.
   - **Vista previa con más espacio**: al quitar los textos de ayuda y poner el km en el mismo
     renglón del campo, la tarjeta *Vista previa* creció de 234 a **258 px** de alto (muestra
     las 4 personas, la fila de TOTALES y aire para más), la de fechas bajó a **133 px** y la
     de encargado/adicionales a **238 px**, todo sin barras de desplazamiento (medido a
     1920×1000: h=0, v=0).
   - **Columnas sin recortes**: en la vista previa las fechas llevan **96 px** (antes 82, que
     recortaba «23/09/2026» como «23/09/2…») y las horas 60-62 px; en el *Detalle de gastos*
     se ensancharon COMBUSTIBLE/ORDEN (122), TAXIS O CAMIONETAS (132), HOSPEDAJE (80) y
     ALIMENTACIÓN (96) para que los títulos entren completos, y EXPLICACIÓN bajó de 260 a 124.
   - **Pantalla limpia**: se quitaron los mensajes pequeños de uso («Cree el viático, ajuste
     días adicionales…», «El efectivo de combustible es el km recorrido…», «El encargado
     siempre viaja en el vehículo…», «Van 1 de 3 en el auto…», «Elija un viático…», «Elija uno
     para precargar sus datos», «Escriba el comprobante y su valor…», «Números de recibo…»,
     «Suba varios a la vez…», «Igual formato del Excel…», «Solo lectura…», y los subtítulos de
     Parámetros, Bitácora, Conexión, Respaldos y Usuarios). El **km que sugiere la tabla** va
     ahora al lado del campo *Km* («tabla: 50») y el aviso de **auto lleno** solo aparece
     cuando de verdad se llenó (los demás pasan a BUS). Se conservan los avisos que importan:
     errores, ajustes bloqueados e insignias de estado.
   - Comprobaciones de esta ronda: `pruebas_qt.py` **18 de 18**, `pruebas_ventanas.py`
     **8 de 8** y el recorrido viático → Excel → historial → justificación → los tres Excel
     leídos con openpyxl para revisar hoja, título, contenido y congelado de paneles.

     **8 de 8** y el recorrido de guardar/ajustar/justificar descrito arriba.

10. **Undécima ronda: comidas día por día, estimado de viaje y acabados**:
   - **Comidas y hospedaje con las horas reales (cambio de regla, `calculos.py`)**: antes se
     calculaba «todos los días intermedios completos» más la comida según la hora de salida y de
     regreso del viático, así que un viaje que sale el **23 a las 22:00** y llega al destino el
     **24 a las 06:00** pagaba comidas del 23 y **dos** noches de hotel. Ahora se revisa **día por
     día**: una comida cuenta si la persona está fuera de casa cuando llega esa hora límite (el día
     de salida se cuenta desde la hora de salida de Miempresa y el de regreso hasta la hora de
     llegada a Miempresa), y el **hospedaje sale de las fechas reales de llegada al trabajo y de
     salida del trabajo** (`noches_de_hospedaje`). Con el caso real (23 22:00 → 25 20:00, llegada al
     destino el 24 06:00, salida del trabajo el 25 14:00) da **2 desayunos, 2 almuerzos,
     2 meriendas, 1 hospedaje y 3 aguas** = $153,50 (cajero $155), que es lo que pidió la empresa;
     antes daba 2, 3, 3 y 2 noches. Los viajes de un día siguen dando exactamente lo mismo que
     antes (regla compatible).
   - **Merienda hasta las 20:00**: `hora_limite_merienda` pasa de 21:00 a **20:00**, así el que
     llega a las 20:00 tiene merienda (como en el caso real). Editable en Parámetros.
   - **Redondeo del cajero a múltiplo de 5**: `redondeo_cajero` pasa de 10 a **5** (21 → 25,
     26 → 30, 25 → 25). Sigue redondeando **hacia arriba** y el valor es editable.
   - **Botón ⏱ Estimar viaje**: con los km del cantón (tabla de distancias) y la velocidad promedio
     del medio —**tres parámetros nuevos**: automóvil 70, camión/camioneta 55, bus 45 km/h— calcula
     el tiempo de viaje y **escribe la llegada al trabajo y la salida del trabajo** (redondeado a 5
     minutos). Es una sugerencia y se puede corregir a mano. En el caso real: 8 h 35 min
     (470 km ÷ 55 km/h) → llegada 24/09 06:35 y salida 25/09 11:25.
   - **Horario propio por viajero (⏱ Horario…)**: en «Empleados adicionales» se elige un viajero de
     la lista y se le pone **su propio horario**, pensado para el que va en **BUS** (sale antes o
     llega más tarde) o en otro vehículo: sus comidas y su hospedaje se calculan con sus horas y su
     total sale distinto al del resto (en la lista queda marcado con **⏱**). El horario se guarda en
     la fila de esa persona y se vuelve a cargar al editar o ajustar el viático. Ejemplo probado: el
     encargado $153,50 y el del bus $42,00 (sin km ni peaje, que son del chofer, y con sus propias
     meriendas).
   - **Etiquetas de fechas**: «Regreso Miempresa» ahora se llama **«Llegada Miempresa»** (queda en
     pareja con «Salida Miempresa»); «Llegada al trabajo» y «Salida del trabajo» siguen igual.
     La impresión y el Excel oficial mantienen los nombres de sus columnas (F.REGRESO, etc.).
   - **Totales en color y bloques como el PDF**: en la vista previa la fila de TOTALES va resaltada
     y, al hacer un **ajuste**, se ve igual que en el informe impreso: **═ ORIGINAL ═** con sus
     totales, cada ajuste anterior con los suyos, **═ AJUSTE N° n · NUEVO ═** y al final el
     **TOTAL GENERAL** en un amarillo más fuerte (`FONDO_GENERAL`).
   - **Justificación ordenada**: los datos del viático elegido van en franjas alternadas y con
     **rótulo de ancho fijo alineado a la derecha**, así todos los valores quedan en la misma
     columna (medido: rótulos en x=9 y x=388, valores en x=195 y x=574 en todas las franjas).
   - **Excel con el encabezado en cuadrícula**: los datos se escriben en **3 parejas por fila**
     (como el informe impreso) repartidos a todo el ancho de la tabla, cada rótulo con su valor al
     lado, el título unido a todo el ancho, el encabezado de la tabla congelado y las columnas de
     los rótulos con el ancho que necesitan para no cortarse.
   - **Base de datos**: columnas nuevas `velocidad_automovil`, `velocidad_camion` y `velocidad_bus`
     en `parametros` (se agregan solas al iniciar, en SQLite y en la base central) y
     `cargar_parametros()` tolera una base sin migrar (los parámetros que falten toman su valor de
     fábrica).
   - Comprobaciones de esta ronda: `pruebas_qt.py` **18 de 18**, `pruebas_ventanas.py` **8 de 8** y
     un recorrido completo: viático del caso real → estimado de viaje → viajero en BUS con horario
     propio → guardar → ajuste (original + nuevo + general) → justificación → los tres Excel
     revisados con openpyxl.


## Versión 6.1 — Horas de Miempresa, cálculo del viaje y pantallas

1. **Salida y llegada de Miempresa.** Los rótulos del formulario (y los del diálogo de horario de
   cada viajero) pasaron a **«Salida de Miempresa»** y **«Llegada a Miempresa»**, y quedan en la
   **misma columna** del formulario, con las horas del trabajo (llegada y salida) en la otra: a la
   izquierda el viaje completo a Miempresa y a la derecha lo del trabajo. El informe impreso muestra
   las mismas etiquetas (antes decía «HORAS MIEMPRESA» y «HORAS TRABAJO»).
2. **El sistema calcula las dos llegadas.** Antes derivaba «Llegada al trabajo» y «Salida del
   trabajo» de las horas de Miempresa y había que pulsar el botón. Ahora se registran la **salida de
   Miempresa** y la **salida del trabajo**, y el sistema escribe la **llegada al trabajo** y la
   **llegada a Miempresa**:
   - se recalcula solo al cambiar la salida de Miempresa, la salida del trabajo, los km o el
     vehículo (`_recalcular_horas`, con un candado para no repetirse mientras se escribe);
   - el botón **⏱ Estimar viaje** sigue disponible y ahora muestra el detalle del cálculo;
   - **al abrir un viático guardado no se toca nada** (`_cargar_formulario` bloquea el cálculo
     mientras carga los campos), así un viático viejo conserva sus horas.
3. **Duración del viaje = recorrido + comidas** (`q_viaje.duracion_de_viaje`):
   - el recorrido es `km ÷ velocidad del medio` **redondeado hacia arriba a la hora entera** (de
     Cuenca a Guayaquil son 3 h 30 en Google, pero ellos registran 4);
   - se suma **una hora por cada comida que cae dentro del viaje**: un viaje de 11 h se registra
     como **13** (una por el desayuno y otra por el almuerzo), igual que lo hacían a mano;
   - esas horas son **dos parámetros nuevos**: `horas_desayuno_viaje` y `horas_almuerzo_viaje`
     (1 y 1 de fábrica), en **Parámetros → Estimado de viaje**, con columnas nuevas en `parametros`
     (se agregan solas al iniciar, en SQLite y en la base central).
   - Ejemplos: 200 km ÷ 70 km/h = 2,9 → **4 h**; si sale a las 02:00 (antes del desayuno) → **5 h**.
4. **Los que viajan en BUS no se calculan.** El sistema no toca sus horas (viajan en otro horario),
   pero se registran igual y su total sale de ellas; el **⏱ Horario…** de cada viajero sigue igual.
5. **Vista previa y detalle más legibles.** Las tablas anchas de 25 columnas ya **no estiran la
   última columna** (`qt_comunes.Tabla(..., estirar_ultima=False)`): antes CAJERO se llevaba todo el
   espacio sobrante y las columnas de valores salían recortadas con puntos suspensivos. Además las
   columnas de dinero quedaron más anchas (Combust./Transp./Peaje/TOTAL/CAJERO) para que entre
   completo. La vista previa ya mostraba **═ ORIGINAL ═ + cada ajuste + TOTAL GENERAL** en amarillo
   fuerte; eso no cambió.
6. **Facturas más cerca.** En «Digitar gasto / factura» se quitó el reparto del sobrante entre las
   dos columnas (`rejilla(..., espacio_medio=True)`): la segunda pareja de campos ya no queda pegada
   al borde derecho, así que «N° comprobante», «RUC», «Lugar» y «Valor de la factura» se leen junto a
   su rótulo.
7. **Horas de viaje por destino (la base del cálculo).** El estimado ya no sale solo de los km: cada
   cantón puede tener sus **horas de viaje (ida)**, que son las que ellos registran de verdad.
   - `q_viaje.HORAS_APROX` trae los destinos medidos en los viáticos reales de la empresa (Guayaquil
     3,5 h; Loja 5,5; Quito 9,5; Santo Domingo 9,5; Machala 6; Macas 6,5; Milagro 5,5; Puerto Quito
     10,5; Santa Isabel 2; Piñas 6,5) y **Parámetros → Rutas** permite escribir las horas de cualquier
     cantón junto a los km (columna nueva `horas` en la tabla `distancias`).
   - El recorrido se toma de esas horas y, si el cantón no tiene dato, de `km ÷ velocidad`; en los
     dos casos se **redondea hacia arriba a la hora entera**: **Cuenca–Guayaquil = 4 h** (antes 3),
     **Quito = 10 h**, Loja 6 h, Machala 6 h. Después se suman las horas de las comidas.
8. **Resumen con los totales a la vista.** La fila de **TOTALES** de cada bloque va en amarillo suave
   (`#FFF2B8`) y la de **TOTAL GENERAL** en el **mismo amarillo fuerte del informe impreso**
   (`#FACC00`). Comprobado con una captura de la tabla: el amarillo se dibuja de verdad.
9. **Falla corregida — el horario de los que viajan en BUS.** El diálogo **⏱ Horario…** se caía al
   abrirlo (`TypeError` en `Tarjeta.agregar_fila`): se le pasaba un armado de campos (`C.fila`) en
   lugar del widget. Ahora abre bien y recibe las **horas del destino** para su estimado.
10. **Pruebas nuevas contra los Excel reales del cliente** (en la carpeta del programa):
    **`pruebas_excel.py`** (lee los 80 viajes de `excel\VIATICO 2 2026.xlsx` y compara columna por
    columna) y **`pruebas_horas.py`** (las dos llegadas, el BUS y los colores del resumen). Los
    resultados quedan en `pruebas_excel_resultado.txt` y `pruebas_horas_resultado.txt`.
    - Comparación con los parámetros de la hoja «Parámetros» del Excel: DÍAS 4 de 80 · DESAY. 3 ·
      ALMUER. 22 · MERIEN. 14 · TAXI S. 4 · TAXI R. 2 · HOSP. 30 · AGUA 6 · COMBUST. 11 · TRANSP. 0 ·
      PARQ./PEAJE 0 · TOTAL 50 · CAJERO 80. Las diferencias son de **los datos del Excel**, no del
      cálculo: (a) comidas y hospedaje de los viajes que salen y regresan de madrugada —el Excel los
      paga «por día» y la empresa pidió la regla nueva (día por día y noches con las horas del
      trabajo)—; (b) COMBUST. de las hojas viejas, hechas con la tarifa 0,10 por km y no la 0,25 que
      dice su propia hoja «Parámetros»; (c) la columna CAJERO del Excel solo está llena en la fila del
      encargado; (d) filas con celdas en blanco o valores negativos (fórmulas rotas).


## Versión 6.2 — Ingreso por área, claves cifradas, índices y prueba con el Excel real

1. **El menú se abre sin pedir clave y cada área pide la suya** (`main_qt.py`, `q_menu.py`,
   `q_login.py`): al pulsar un módulo se pide usuario y clave y se comprueba el rol
   (`PERMISOS_MODULO`): viáticos y respaldos para todos; Justificar viáticos solo la persona de
   justificación y el superusuario; Parámetros, Auditoría, Usuarios y Conexión solo el superusuario.
   Si la clave es de otro rol, la ventana lo dice y no entra. Cada ingreso y cada cierre quedan en
   la auditoría.
   - Casilla «No volver a pedir la clave en este equipo» (se olvida al cerrar el sistema) y botón
     **🔒 Olvidar la clave** en el menú.
   - La pantalla de Conexión dejó de tener botón en la barra lateral: se abre con **Ctrl+Alt+B** (y
     sigue apareciendo sola cuando el servidor no responde).
2. **Las claves se guardan cifradas** (`database.py`): `sha256$<sal>$<resumen>` con sal al azar
   (`cifrar_clave`, `clave_correcta`, `es_clave_cifrada`). El login compara con el resumen
   (`hmac.compare_digest`), acepta las claves viejas en texto y las cifra sola la primera vez que
   ese usuario ingresa (y al abrir el sistema, en `_migrar_usuarios`). La pantalla de usuarios ya no
   muestra claves (muestra `•••• cifrada`) y la clave vacía significa «no cambiarla».
   - Además se cerró el agujero de `clave_super_ok()` (aceptaba la clave de PostgreSQL como clave
     maestra del sistema): esa función ya no existe.
3. **Índices que faltaban para producción**: `viajes.fecha_salida`, `viajes.estado`,
   `gastos.viatico_numero`, `ajustes.viatico_numero`, `respaldos.viatico_numero` y
   `usuarios.usuario` (se crean solos al iniciar, en SQLite y en la base central).
4. **Prueba con el Excel real de viáticos** (`herramientas\comparar_excel_viaticos.py`): lee las 129
   hojas de `VIATICOS 2026.xlsx`, crea los mismos 113 viáticos (con sus gastos) en una base local
   aparte y compara valores. Resultado: los gastos respaldados coinciden **al centavo** ($32.159,21
   en los dos) y el «valor entregado» difiere en $9.615,45 porque ese Excel pagaba las facturas
   reales y el programa paga por reglas. Informe: `documentacion\PRUEBA_EXCEL_VIATICOS.md`.
5. **Comparación regla contra regla del formato nuevo** (`herramientas\comparar_reglas_excel.py`):
   80 filas de `VIATICO 2 2026.xlsx`; 20 coinciden exacto y 60 tienen alguna diferencia. Las causas
   quedaron identificadas: la **merienda** (el Excel la paga hasta las 21:00 y el programa hasta las
   20:00), el **combustible** ($0,25 por km en el Excel y $0,10 en los parámetros del programa), el
   **hospedaje** (por fechas, contra llegada/salida del trabajo en el programa) y el
   **parqueadero/peaje** ($10 fijos por viaje en el Excel). Informe:
   `documentacion\COMPARACION_REGLAS_NUEVO_EXCEL.md`.
6. **Limpieza del proyecto**: se borraron temporales, `__pycache__`, el `dist` viejo y los
   resultados de prueba; los Excel de trabajo pasaron a `herramientas\excels_de_trabajo\` y la
   carpeta del programa quedó solo con lo que el sistema necesita (código, `INICIAR.bat`,
   `EMPAQUETAR_EXE_SERVIDOR.bat`, `data\`, `excel\` con las listas de personal y clientes, e
   `image.png` / `icono.ico`).
7. **Pruebas**: `pruebas_qt.py` pasa de 18 a **37 comprobaciones** (crea una base SQLite en una
   carpeta temporal y comprueba el cifrado de claves, el ingreso por área, los permisos por módulo y
   el menú sin sesión), todo en verde, y `compileall` sin errores.


## Versión 6.3 — Ventana de ingreso sin leyendas

1. **Se quitó la leyenda tenue de la ventana de ingreso** (`q_login.py`, `q_menu.py`): al abrir un
   área aparecía, debajo del título, el texto «Para abrir «Parámetros» escriba su clave. **Puede
   ingresar: SUPERUSUARIO**.» (letra pequeña y tenue, rol visual `QLabel#ayuda`). Ahora la ventana
   solo pide usuario y clave: nada anuncia quién puede entrar.
   - El área sigue identificada en el título de la ventana («Ingreso — Parámetros») y, si la clave es
     de otro rol, el aviso «Esa área es solo para: …» sale al intentar ingresar (eso no cambió).
   - Se quitó también el parámetro `motivo` de `LoginWindow` y de `pedir_sesion` (ya nadie lo usa) y
     el ayudante `MenuPrincipal._nombres_roles`, que era el que armaba la lista de roles que salía en
     la pantalla.
2. **Comprobaciones de esta ronda**: `python pruebas_qt.py` **37 de 37** (la comprobación del ingreso
   por área ahora revisa, además, que la ventana **no** nombre a los roles) y
   `python pruebas_ventanas.py` **8 de 8**, todo en verde.


## Versión 6.4 — El botón de Conexión vuelve a la barra lateral

1. **🔌 Conexión / base de datos vuelve a tener botón en el menú** (`q_menu.py`), como en el menú
   anterior. Había quedado solo con el atajo **Ctrl+Alt+B** y eso volvía incómodo lo que el
   superusuario hace a mano: ver la base en uso, cambiar entre la base local y la central, elegir
   dónde se guardan los respaldos, fijar la numeración y —sobre todo— **cambiar el zoom de esa
   computadora** (las pantallas chicas lo necesitan y es un ajuste por PC).
   - Sigue siendo **solo del superusuario**: al pulsar el botón el sistema pide la clave y comprueba
     el rol (`PERMISOS_MODULO["conexion"] == (db.ROL_SUPER,)`), igual que Parámetros, Auditoría y
     Usuarios. Si la clave es de otro rol, avisa («Esa área es solo para: …») y no deja entrar; el
     intento queda en la auditoría.
   - **Ctrl+Alt+B sigue funcionando** como atajo y la pantalla **sigue apareciendo sola** cuando el
     servidor no responde (eso no cambió).
   - El botón lleva su propia ayuda al pasar el ratón (`q_menu.AYUDA_CONEXION`): «Solo el superusuario
     (le pide su clave): tipo de base, datos del servidor, respaldos, numeración de viáticos y el
     tamaño de pantalla (zoom) de ESTA computadora».
2. **Documentación puesta al día**: `LEEME_PRIMERO.md` y `documentacion\GUIA_DEL_SISTEMA.md` vuelven
   a explicar que la pantalla de Conexión está en la barra lateral, y las notas del **zoom** dicen
   ahora que se llega a ella por ese botón **🔌**.
3. **Comprobaciones de esta ronda**: `python pruebas_qt.py` **38 de 38** (la prueba del menú ahora
   exige los 7 módulos con botón —el de la conexión incluido—, que el atajo siga y que el botón
   avise que es del superusuario) y `python pruebas_ventanas.py` **8 de 8**, todo en verde.


## Versión 6.5 — Las comidas del camino en la hora de llegada (y los tiempos de viaje completos)

1. **La llegada se registra con las comidas del camino, como lo hacen a mano** (`q_viaje.py`). La
   regla de la empresa es **una hora por cada comida que cae dentro del viaje**, y cada tramo se
   cuenta **desde su propia salida**:
   - sale de Miempresa a las 10:00 y llega a las 13:00 → se registra **14:00** (el almuerzo);
   - llega al lugar a las 08:00 → se registra **09:00** (el desayuno del camino);
   - vuelve de un viaje a las 22:00 → se registra **23:00** (la merienda de las 21:00 cayó dentro);
   - viaje largo: sale a las 02:00 y llega a las 14:00 → se registra **16:00** (desayuno y almuerzo).
   - Los tres primeros casos ya salían bien **menos dos**: la **merienda** no se contaba (no estaba en
     la lista de comidas del viaje) y la **vuelta** reutilizaba las horas calculadas para la ida, así
     que el que salía del trabajo a las 18:00 con 4 h de camino quedaba a las 22:00 y no a las 23:00.
     Ahora la ida se cuenta desde la salida de Miempresa y la vuelta desde la salida del trabajo,
     cada una con las comidas que le caen dentro (el viaje que cruza la medianoche sigue sumando una
     sola vez cada comida).
   - Es el mismo cálculo en el formulario (**⏱ Estimar viaje**, que además se recalcula solo al
     cambiar la salida, los km o el vehículo) y en el diálogo **⏱ Horario…** de cada viajero.
   - El aviso de **⏱ Estimar viaje** ahora muestra el detalle de los dos tramos: «Vuelta — salida del
     trabajo: 24/09 18:00 · 4 h de recorrido + 1 h por la merienda (21:00, en el camino) = 5 h ·
     llegada: 24/09 23:00», para que se vea de dónde sale cada hora.
2. **Parámetro nuevo `horas_merienda_viaje`** (1 h de fábrica), al lado de las del desayuno y el
   almuerzo en **Parámetros → Estimado de viaje**. La columna se agrega sola al iniciar en SQLite y
   en la base central (y también a la lista de columnas que se revisan antes de alterar PostgreSQL,
   donde faltaban justamente las dos horas de comida de la versión anterior). El texto de ayuda de
   **Parámetros → Provincias y km** recuerda que las horas se pueden dejar vacías: ahí el sistema
   estima el tiempo con los km y la velocidad, más las comidas del camino.
3. **El Excel de tiempos de viaje queda completo y explica la regla**
   (`herramientas\generar_excel_tiempos.py`):
   - de los **202 cantones**, solo **10** tenían horas de viaje medidas; los **187 restantes** se
     llenaron con el tiempo real de ruta medido con OpenStreetMap (`herramientas\tiempos_de_viaje.py`,
     que lo redondea hacia arriba a la hora entera). Los 10 destinos que la empresa midió a mano no se
     tocaron: la herramienta solo completa los vacíos. La tabla quedó **197 de 202 cantones con
     horas**, y los **5 que quedan en blanco** en el Excel son **Cuenca** y **Déleg** (a menos de una
     hora de camino: el mapa no da tiempo de viaje, así que el sistema lo estima con los km y la
     velocidad, igual que cualquier destino sin horas) y las **3 islas de Galápagos** (Isabela,
     San Cristóbal y Santa Cruz), a las que **no se llega en auto**. El cuadro de control de lo que
     se cargó queda en `herramientas\tiempos_de_viaje.txt`;
   - la herramienta se puede **volver a correr sin miedo**: **no vuelve a consultar** los cantones que
     ya tienen horas y, si se corta el internet, avisa «SIN CONSULTAR» y sigue con los demás (al
     correr otra vez el mismo comando arranca donde quedó). Con `--forzar` se revisan otra vez todos
     —útil para rehacer el cuadro de control completo— pero **las horas que midió la empresa nunca se
     pisan**: el cuadro las marca «empresa: X h (no se toca)». También aprendió a no caerse con los
     cantones **sin ruta en auto**: antes una isla tumbaba la corrida entera;
   - la hoja lleva tres columnas (cantón, km y horas de viaje) y el color dice de dónde sale el dato:
     **azul** = lo midió la empresa, **gris** = tiempo de ruta (revisable en Parámetros), **blanco** =
     todavía sin dato (el sistema lo estima con los km y la velocidad del vehículo);
   - la tabla guarda los km y las horas **por nombre de cantón** (así funciona el sistema desde el
     principio) y hay **dos nombres repetidos**: **BOLÍVAR** (Carchi y Manabí) y **OLMEDO** (Loja y
     Manabí). Por eso el Excel tiene **202 filas** para 204 cantones: esas dos filas sirven para los
     dos cantones de cada nombre y quedan con la hora del último que se calculó (BOLÍVAR quedó con 8 h
     y OLMEDO con 6 h). Si la empresa necesita distinguirlos, se ajusta esa fila a mano en
     **Parámetros → Provincias y km** (o se separan los nombres);
   - la hoja nueva **«Cómo se calcula»** deja escritos la regla, las horas de las comidas y los
     cuatro ejemplos, así nadie tiene que recordarlos.
   - Si la base central todavía no tiene esos tiempos, se cargan con el mismo Excel
     (**Parámetros → Provincias y km → 📥 Importar Excel**) o corriendo
     `python herramientas\tiempos_de_viaje.py --servidor 192.168.1.171`.
4. **Comprobaciones de esta ronda**: `python pruebas_qt.py` **43 de 43** (5 nuevas: el parámetro de la
   merienda, su fila en Parámetros y los tres ejemplos de la regla), `python pruebas_horas.py`
   **28 de 28** (los cuatro casos del cliente, el cruce de medianoche, la vuelta a las 23:00 en el
   formulario y el detalle del aviso) y `python pruebas_ventanas.py` **8 de 8**, todo en verde.


## Versión 6.6 — La barra lateral agrupada y las comparaciones con el Excel, al día

1. **La barra lateral del menú quedó agrupada** (`q_menu.py`): los ocho botones ya no van en una sola
   lista. Ahora son dos grupos, cada uno con su título en letra pequeña y una línea divisoria en medio:
   - **TRABAJO DEL DÍA**: generar / revisar / ajustar viáticos, justificar viáticos y respaldos (lo que
     se usa a diario);
   - **🔑 SUPERUSUARIO**: parámetros, auditoría, usuarios y conexión (esas ventanas le piden su clave al
     abrirse, como todas las suyas).
   - Los grupos están en una sola tabla al comienzo del archivo (`GRUPOS`) y cada título lleva su ayuda
     al pasar el ratón; un módulo nuevo que no esté en la tabla cae solo en **«OTROS MÓDULOS»**, así
     nada se pierde por olvido. El título de cada grupo se ajustó para que quepa **en una sola línea**
     (si se alarga, empuja los botones hacia abajo: la barra está pensada para el alto mínimo de la
     ventana).
   - Estilo nuevo `QLabel#grupoMenu` en `qt_tema.py` (letra pequeña, negrita y gris) y
     `qt_comunes.etiqueta()` acepta ahora cualquier nombre de estilo en `rubrica` (antes solo
     «contador»).
   - Nada más cambió en el menú: los mismos 7 módulos, los mismos permisos por rol, la misma sesión y
     el mismo atajo **Ctrl+Alt+B**.
2. **Las dos comparaciones con los Excel de la empresa, corridas de nuevo** (ya con los parámetros
   cuadrados al Excel nuevo: merienda 21:00, $0,25 por km, redondeo a múltiplo de 5, parqueadero/peaje
   $10 y hospedaje por fechas):
   - `herramientas\comparar_reglas_excel.py` (formato nuevo semanal, **80 filas**): **42 filas
     coinciden exacto** y 38 tienen alguna diferencia; el total del formato nuevo es **$4821,00**
     contra **$5221,25** del programa (diferencia **−$400,25**). La columna «valor a retirar en cajero»
     del Excel sigue **en blanco** en las 80 filas, así que ahí no hay nada que comparar (el programa
     calcula **$5390,00**). Las **reglas de los dos lados son las mismas** y las diferencias que quedan
     son **datos escritos a mano en el Excel**: el combustible a **$0,10 por km en 11 filas**
     (−$461,75; su propia hoja «Parámetros» dice $0,25), **comidas y agua −$84,00** (3 filas con «Días
     de Viaje» en blanco, cuyas fórmulas dan números negativos, y celdas sobrescritas a mano), **taxis
     −$6,00 en 6 filas** y el **«Transporte» $151,50 en 7 filas**, un concepto que el programa no paga
     (en el sistema entraría en «otros gastos»). **Parqueadero/peaje ($535,00) y hospedaje ($1335,00)
     coinciden en las 80 filas.**
   - `herramientas\comparar_excel_viaticos.py` (Excel histórico, **129 hojas**): **113 viáticos**
     comparados (109 con datos coherentes, 16 hojas anuladas o vacías). Los **gastos respaldados
     coinciden al centavo** ($32.159,21 en los dos lados). El «valor entregado» del Excel es
     **$20.375,45** contra **$11.170,00** del programa (diferencia **$9205,45**): ese Excel pagaba las
     **facturas reales** del viaje y el programa paga por reglas. Con **solo viáticos** (sin las
     facturas de la justificación) el programa daría **$5730,00** ($5516,00 antes del redondeo), o sea
     **$14.645,45** menos que lo entregado; las facturas de la justificación (combustible,
     parqueadero/peaje y otros) le suman **$5440,00** a los viáticos calculados solo por reglas.
   - Informes regenerados: `documentacion\PRUEBA_EXCEL_VIATICOS.md` y
     `documentacion\COMPARACION_REGLAS_NUEVO_EXCEL.md`.
3. **Comprobaciones de esta ronda**: `python pruebas_qt.py` **43 de 43** (incluye el menú con sus 7
   módulos y el botón Inicio), `python pruebas_horas.py` **fallos = 0** y `python pruebas_ventanas.py`
   **8 de 8**, todo en verde. El menú se revisó además con una **captura de la barra lateral** al alto
   normal y al alto mínimo de la ventana (los dos títulos caben en una línea y los ocho botones siguen
   a la vista).


## Versión 6.7 — Los parámetros y los catálogos quedan para todos (vendedoras incluidas)

1. **Las vendedoras pueden cambiar los parámetros** (`q_menu.py`). Antes la única puerta a
   **⚙️ Parámetros, empleados, vehículos y rutas** era la clave del superusuario
   (`PERMISOS_MODULO["admin"] == (db.ROL_SUPER,)`); ahora esa área es
   `(db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER)`: cada quien entra **con su propia clave** para
   cambiar las tarifas y las horas límite, el valor por km y las horas de viaje, los km/horas por
   cantón, los empleados, los clientes y los vehículos. **El cambio no es de una sola PC**: se guarda
   en la base en uso, así que lo ven todas las computadoras que trabajan contra la base central, y
   cada cambio queda en la auditoría con el nombre de quien lo hizo (`CAMBIÓ PARÁMETROS`,
   `CAMBIÓ DISTANCIA`, `AGREGÓ CLIENTE`, …).
   - **Auditoría, Usuarios y Conexión siguen siendo solo del superusuario**, y lo demás no se movió:
     viáticos y respaldos para todos, justificar viáticos para justificación y superusuario.
   - Para volver atrás, la tupla de `"admin"` en `PERMISOS_MODULO` vuelve a `(db.ROL_SUPER,)`.
2. **La barra lateral se reacomodó** (`q_menu.py`, tabla `GRUPOS`):
   - **TRABAJO DEL DÍA**: generar / revisar / ajustar viáticos, justificar viáticos, respaldos y
     **parámetros y catálogos** (eso es lo que ahora se usa a diario);
   - **🔑 SUPERUSUARIO** (con su título y una línea en medio): auditoría, usuarios y conexión.
   - La ayuda del grupo del superusuario ya no nombra los parámetros y el botón de Parámetros tiene su
     propia ayuda (`AYUDA_ADMIN`): dice qué se cambia ahí y que **el cambio lo ven las demás
     computadoras**. La tabla nueva `AYUDAS` guarda las ayudas por módulo (`conexion` y `admin`); los
     demás botones siguen mostrando su título.
3. **Documentación al día**: `LEEME_PRIMERO.md` y `documentacion\GUIA_DEL_SISTEMA.md` llevan la tabla
   de permisos corregida (Parámetros ✔ para vendedoras y justificación), la explicación de que los
   parámetros y los catálogos los abre cualquiera con su clave y que **el cambio queda para todas las
   computadoras**, que **los Excel (personal, clientes y km/horas) se cargan una sola vez** porque
   quedan en la base, y la barra lateral agrupada tal como quedó.
4. **Comprobaciones de esta ronda**: `python pruebas_qt.py` **46 de 46** (tres nuevas: los parámetros
   van con el trabajo del día en la barra, el botón de Parámetros avisa que el cambio alcanza a las
   demás PC, y una **vendedora abre Parámetros con su propia clave**; las dos de permisos se
   reacomodaron), `python pruebas_horas.py` **fallos = 0** y `python pruebas_ventanas.py` **8 de 8**,
   todo en verde. El menú se revisó además abriéndolo de verdad: los dos títulos ocupan **96 y 102 px
   de los 204 px útiles** de la barra (una sola línea cada uno) y la captura quedó actualizada en
   `sistema_viaticos_miempresa\documentacion\capturas\menu_barra_agrupada.png`.

## Versión 6.8 — El respaldo diario del servidor: IP y puerto correctos, nunca borra, y ya no se queda colgado

1. **Los datos del servidor quedaron fijos dentro de los scripts** (`servidor\respaldar_base_nativo.bat`,
   `servidor\PROGRAMAR_RESPALDO_DIARIO.bat`): el puerto por defecto pasa a **2345** (estaba en 5432) y el
   programador ya trae puestos **127.0.0.1** (o sea *el propio equipo*, sin pasar por la red ni por el
   firewall) **· puerto 2345 · usuario miempresa · PostgreSQL 18 · 21:00 todas las noches**, así que en el
   servidor se ejecuta **sin escribir nada**. Para sacar el respaldo **desde otra PC** de la red se le pasa
   la IP como 3.er dato: `PROGRAMAR_RESPALDO_DIARIO.bat 2345 miempresa 192.168.1.4`. Queda **una sola**
   tarea, **«Viaticos - respaldo diario»**, que corre **como SYSTEM** (aunque nadie tenga sesión abierta).
   Se eliminó la tarea/pregunta del mediodía que traía la versión anterior.
2. **No se borra nunca ningún respaldo**: el parámetro de días quedó en **0** por defecto (`DIAS=0`), o sea
   se conservan todos los `.sql`; los respaldos manuales `viaticos_ANTES_DE_....sql` nunca se tocan.
   Antes venía con **30 días** y el respaldo viejo se borraba solo.
3. **El respaldo se quedaba esperando una tecla cuando lo lanzaba la tarea** (esto era lo más grave y no se
   había visto): el script terminaba en `pause` y, al lanzarlo una tarea programada, esa pausa **nunca
   termina** — la tarea se queda *«En ejecución»* (`Último resultado: 267009`) para siempre y, como Windows
   no lanza una tarea que todavía está corriendo, **las noches siguientes ya no se respaldaba nada**. Se
   corrigió pasando un 5.º dato **`auto`** desde la tarea (`… miempresa 2345 127.0.0.1 0 auto`), que
   convierte la pausa en `pause <nul >nul` (`%ESPERA%`): con `auto` el script **no espera tecla** y
   termina, y **ni siquiera muestra el mensaje de la tecla** (para que nadie se confunda al verlo);
   si lo ejecuta una persona (sin `auto`) la pausa sigue igual. Probado en este equipo con una tarea real y
   un respaldo de prueba: `Estado: Listo` · `Último resultado: 0`, y la tarea terminó sola. Con `pause`
   normal la misma prueba dio `En ejecución` y un `cmd.exe` colgado esperando la tecla.
4. **Error de sintaxis corregido en el bloque de error del respaldo** (`servidor\respaldar_base_nativo.bat`):
   la lista numerada `1) 2) 3) 4)` dentro del `if ( … )` del mensaje de error hacía reventar el propio
   mensaje (*«No se esperaba que en este momento…»*); los paréntesis van escapados (`^)`).
5. **PostgreSQL 18 (o el que esté instalado)**: se busca primero `C:\Program Files\PostgreSQL\18\bin` y, si
   el servidor tuviera otra versión, se usa la que haya (**16, 17, 19…**). El respaldo se escribe en UTF-8
   (`PGCLIENTENCODING=UTF8`) para no dañar tildes ni eñes, y queda en
   `servidor\respaldos_base\viaticos_AAAAAMMDD_HHMMSS.sql` (la carpeta se crea sola).
6. **Documentación al día**: `documentacion\SERVIDOR.md` (encabezado, A5/A6 con el aviso del puerto 2345 y
   **A7** con el paso a paso, el `127.0.0.1` por defecto, el `schtasks` con `0 auto` y la advertencia de la
   pausa). Las copias para el repositorio en `PARA_GITHUB\servidor\` y `PARA_GITHUB\documentacion\` quedaron
   iguales a los originales (comparadas archivo por archivo, sin diferencias).
7. **Comprobaciones de esta ronda** (en este equipo, con un respaldo de prueba en lugar de `pg_dump`): el
   programador terminó solo (código 0), revisó que el `.sql` estuviera completo, creó la tarea con los cinco
   datos (*«Tarea que se ejecutará: … miempresa 2345 &lt;servidor&gt; 0 auto»*), la ejecutó y a los 20 s la
   tarea estaba en **`Estado: Listo`** con **`Último resultado: 0`**; las tareas y archivos de prueba se
   borraron (no quedó ninguna tarea `PRUEBA_*` en el equipo).
8. **Cómo se le pasan los datos y qué NO toca el respaldo** (esto importa porque el servidor tiene otros
   programas instalados): los 4 datos son **opcionales** y van en este orden —**puerto, clave, servidor y
   hora**— y lo que se omita queda con el valor por defecto; lo normal es ejecutarlo **sin escribir nada**
   (clic derecho → *Ejecutar como administrador*). El respaldo **solo** hace tres cosas: **lee** la base
   `viaticos` con `pg_dump`, escribe el `.sql` **dentro de su propia carpeta** `respaldos_base\` y crea
   **una** tarea de Windows llamada `Viaticos - respaldo diario` (que se quita con
   `QUITAR_RESPALDO_DIARIO.bat`). **No** reinicia servicios, **no** toca `postgresql.conf`, **no** usa el
   puerto 5432, **no** modifica ni borra nada de la base y no borra ningún respaldo (`DIAS=0`).

## Los viáticos ya pagados se volvieron a digitar (prueba contra el Excel)

> Los números de viático, los nombres del personal y los importes de esta prueba son **datos
> reales de la empresa**, así que **no se publican**: en el repositorio queda solo el método.

1. **Lo que se pidió**: volver a digitar **en el programa y en la base local** viáticos que la
   empresa **ya había pagado**, para comprobar que el programa liquida **lo mismo** que el Excel, y
   guardar los PDF para compararlos lado a lado.
2. **Herramienta de la prueba** (no se versiona, porque lleva los datos reales): hacía copia de
   seguridad de `data\viaticos.db`, agregaba los viajeros que faltaran a la lista de empleados,
   creaba los viáticos con las **mismas reglas de la pantalla** (`calculos.calcular` y el reparto del
   combustible: los km y el parqueadero/peaje solo en la fila del chofer), comparaba concepto por
   concepto contra lo pagado y dejaba el informe junto a los PDF. Se podía correr con
   `--sin-guardar` para solo comparar, sin escribir nada. **Nunca tocaba el servidor**: forzaba la
   base local (SQLite).
3. **Resultado: coinciden al centavo.** El total del programa, fila por fila y concepto por concepto
   (comidas, taxis, hospedaje por noche, agua por día, combustible por km y parqueadero/peaje), dio
   **igual que el Excel**. **No hizo falta cambiar ninguna regla.**
4. **PDF de la comparación**: el del programa (el mismo de 🖨 IMPRIMIR / PDF) y una copia del
   formato del Excel de la empresa armada con los mismos datos, para mirarlos lado a lado. Los PDF se
   generan con Edge en modo invisible: sin abrir ventanas y sin la cabecera que pone el navegador.
5. **Lo único que no era idéntico**: la columna **«VALOR A RETIRAR EN CAJERO»** del Excel estaba en
   blanco y el programa sí la calcula (redondeo hacia arriba al múltiplo del cajero). El **TOTAL
   VIÁTICOS** era el mismo en los dos lados. Si se quiere esa columna en blanco, se apaga el
   redondeo del cajero en Parámetros.
6. **Cambios en la base local** (`sistema_viaticos_miempresa\data\viaticos.db`, siempre **con copia
   de seguridad previa** `viaticos.db.bak_<fecha>`): los viáticos de la prueba, los viajeros que
   faltaban agregados a la lista, las líneas correspondientes en la bitácora y el **contador del
   año** puesto en el número correcto para que el próximo viático siga la numeración.
7. **Datos por confirmar con la empresa** (no cambian ningún valor): el texto de las observaciones,
   el nombre del cliente en la lista de clientes y el **tipo** de un vehículo, que en el catálogo
   estaba distinto que en el Excel (*CAMION GRUA* contra *CAMIONETA*).

## Versión 6.9 — El ENTER ya no cierra la ventana, el combustible a mano entra y MACAS con sus datos

1. **ENTER cerraba la ventana del módulo y se perdía lo escrito** (la falla más grave de esta ronda):
   en un `QDialog`, Qt nombra «botón por defecto» al primer botón que se crea, y en las ventanas de los
   módulos ese es el «← Volver al menú»; al pulsar ENTER dentro de cualquier campo —por ejemplo al
   terminar de escribir el combustible— el diálogo **se cerraba solo**. Se corrigió en
   `qt_comunes.Ventana`: al botón de volver se le quita la marca de «por defecto»
   (`setAutoDefault(False)` · `setDefault(False)`) y la ventana **ignora la tecla ENTER**
   (`keyPressEvent`), así ENTER solo sirve para terminar de escribir el campo. Comprobado abriendo la
   pantalla de viáticos de verdad (con PySide6, sin monitor): antes el ENTER disparaba «← Volver al
   menú» y dejaba la ventana cerrada; ahora la ventana sigue abierta y no hay ningún botón «por
   defecto». La pantalla de ingreso (`LoginWindow`) **no** se toca: su ENTER para entrar sigue igual.
2. **El efectivo de combustible escrito a mano no se reflejaba**: `txt_efectivo` era el único campo
   sin el aviso de cambios (los de km, parqueadero y otros sí lo tenían), así que al escribir otro
   valor la vista previa y el total seguían mostrando el sugerido. Ahora el campo refresca la vista
   previa al escribir (`cb=lambda _t: self._refrescar_prev()`), igual que los demás.
3. **Sin chofer, el combustible y el parqueadero/peaje se perdían en silencio**: esos dos valores van
   en la fila del chofer; si no había chofer elegido —o el chofer no viajaba en ese viático— no
   quedaban en ninguna fila y el total no los mostraba. Ahora, en ese caso, los lleva el
   **ENCARGADO** (que es quien recibe el dinero), tanto en el viático nuevo como en los ajustes.
4. **La ventana explica por qué un concepto sale en cero** (`_explicar_conceptos`): debajo de la vista
   previa aparece, por ejemplo, «Taxi de regreso $0: se paga si vuelve a las 21:00 o después (vuelve
   a las 19:30)» o «Combustible $0: escriba los km del viaje o el efectivo en «💵 Efectivo Comb. $»».
   El taxi de regreso **sí se suma** desde la hora límite (21:00 de fábrica); lo que faltaba era la
   explicación cuando la hora registrada es anterior. En un ajuste avisa que ahí solo se pagan días,
   comidas, hospedaje y agua.
5. **Tiempos y km de MACAS corregidos**: la tabla tenía **190 km y 6.5 h** (tiempo de ruta de
   OpenStreetMap); la empresa mide **230 km y 4.5 h**. Se corrigió la semilla (`database.KM_CUENCA` ·
   `database.HORAS_CUENCA`), la base local (`distancias`) y se volvió a armar
   `excel\TIEMPOS DE VIAJE MIEMPRESA.xlsx` para cargarlo con **PARÁMETROS → 🗺️ Provincias y km →
   📥 Importar Excel**. **Los tiempos y los km viven en la base de datos**: se corrigen una vez (en el
   servidor) y los ven todas las computadoras, sin tocar PC por PC. Ojo con el resto del catálogo:
   de los 197 cantones con horas, **solo 10 son tiempos medidos por la empresa** (Guayaquil, Loja,
   Quito, Santo Domingo, Machala, Macas, Milagro, Puerto Quito, Santa Isabel y Piñas); los otros 187
   son estimados de la ruta y conviene reemplazarlos con los tiempos reales.
6. **Comprobaciones de esta ronda**: `q_viaje.py`, `qt_comunes.py` y `database.py` compilan; los 15
   módulos del sistema cargan; y en la prueba en vivo (pantalla de viáticos abierta de verdad, sin
   monitor) se verificó que la ventana **no se cierra con ENTER**, que el combustible a mano entra
   con y sin chofer, que MACAS trae **230 km · 4.5 h**, que el taxi de regreso se paga desde las
   21:00 y que a las 19:30 la ventana dice el motivo.
7. **Para las computadoras**: esto es **código nuevo**, así que hay que volver a empaquetar
   (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe` a cada PC. Los tiempos y los
   km, en cambio, son **datos de la base**: no obligan a actualizar nada en las PC.

## Versión 7.0 — El valor a retirar en cajero es el del TOTAL (lo retira una sola persona)

1. **El error**: en la justificación salía un «entregado» que no era el entregado. El sistema
   redondeaba la cuenta de **cada viajero** al múltiplo del cajero ($5 de fábrica) y **después
   sumaba**, así que el total quedaba por encima del dinero que de verdad se retiró: el retiro del
   cajero lo hace **una sola persona** (el encargado) y lleva el dinero de todo el grupo, por lo que
   el redondeo tiene que hacerse **una sola vez**, sobre el total.
2. **La regla nueva** (`calculos.cajero_del_grupo`): el redondeo se hace **una sola vez**, sobre el
   **total del viático**, y el valor queda en la fila del **encargado** (las demás filas en cero,
   porque el retiro es uno solo). Como todo el sistema —la vista previa, el PDF, la justificación,
   el historial y los Excel— muestra la **suma** de la columna CAJERO, con eso muestran exactamente
   el dinero retirado sin tocar nada más. La usan el viático nuevo (`q_viaje._construir_filas`) y
   el ajuste (`q_viaje._filas_ajuste`, con el total del ajuste). `calculos.calcular` sigue
   devolviendo el redondeo **por fila** porque así lo hace el formato viejo del Excel: es lo que
   miden las herramientas de comparación (punto 6).
3. **Los viáticos que ya estaban guardados**: herramienta `herramientas\recalcular_cajero.py`.
   Muestra el cuadro (N°, total, cajero guardado, el que le toca y la diferencia) y **solo escribe
   con `--aplicar`**; antes de escribir hace copia de seguridad de la base local y deja el cambio en
   la bitácora. De fábrica **no toca los viáticos JUSTIFICADOS** (historia cerrada; se revisan con
   `--todas`). Con eso se pusieron al día los viáticos guardados con el valor viejo; los que se
   decida dejar como están, se quedan (el comando avisa la diferencia antes de tocar nada).
4. **Comprobado en vivo** (PySide6 sin monitor, base local real): al volver a digitar un viático ya
   guardado, el **CAJERO** queda **en la fila del encargado** (y en $0,00 la de los acompañantes) y
   la fila de **TOTALES** de la vista previa muestra la misma cifra en TOTAL y en CAJERO; la
   pantalla **JUSTIFICAR** dice el «Entregado» correcto y sugiere devolver ese mismo valor; y un
   ajuste de prueba redondea una sola vez. Sin errores de armado en las dos ventanas.
5. **Para las computadoras**: es **código nuevo**, así que hay que volver a empaquetar
   (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe` a cada PC. El cambio de los
   viáticos ya guardados es **dato de la base**: está hecho en la base **local** (que es la que se
   usa hoy, como lo dice el ingreso) y, si algún día se pasa a la base central, esos viáticos se
   corrigen ahí con el mismo criterio (el total redondeado, en la fila del encargado).
6. **Ojo con las herramientas de comparación**: `herramientas\comparar_reglas_excel.py` y
   `comparar_excel_viaticos.py` siguen midiendo el redondeo **fila por fila** (la fórmula del
   formato viejo del Excel): sirven para comparar fórmulas, no para saber lo que retira el sistema.
   Los PDF de la prueba son de antes de este cambio (solo cambia la columna CAJERO).


## Versión 8.0 — El BUS también se calcula solo (el mismo tiempo de viaje que los demás)

1. **El cambio**: cuando el vehículo del viático era un **BUS** el sistema no tocaba las horas
   («los del bus viajan en otro horario») y había que registrarlas a mano, aunque el bus hiciera el
   mismo viaje. Ahora el BUS **se calcula igual que los demás vehículos**:
   `q_viaje._recalcular_horas()` ya no se detiene cuando el medio es un bus y llama siempre a
   `_estimar_viaje()`, así que las dos llegadas se escriben solas con las **horas del cantón**
   (tabla de distancias) o, si el cantón no las tuviera, con los **km ÷ la velocidad del bus**, más
   las comidas del camino.
2. **El mismo tiempo de viaje**: el bus hace el mismo recorrido, así que tarda lo mismo. De los
   **202 cantones** de la base, **197 traen sus horas** en la tabla (el tiempo manda sobre la
   velocidad) y en los otros (Cuenca 10 km y Déleg 75 km) el redondeo hacia arriba deja el mismo
   resultado; la velocidad del bus (**45 km/h** en «Estimado de viaje») solo se usa donde no hay
   horas ni km reales (las filas de Galápagos, de 1000 km). Si algún día se quiere el bus a la
   velocidad del automóvil, se cambia ese parámetro en **Parámetros**.
3. **El BUS ahora se puede registrar**: el tipo `BUS` no estaba en la lista de tipos de vehículo,
   así que no se podía crear un bus desde **Parámetros → Vehículos**. Se agregó `BUS` a
   `database.TIPOS_VEHICULO` y a `q_admin.TIPOS_VEHICULO_UI` (entre `MOTO` y `OTRO`). Es lo que hace
   que el vehículo se reconozca como bus (`_va_en_bus()`, por el tipo que viene en «Placa vehículo»).
4. **Lo que NO cambió**: las horas siguen siendo una **sugerencia** (quedan escritas y se corrigen a
   mano), las comidas del camino siguen igual (`comidas_del_viaje`) y el horario propio por viajero
   sigue guardado en la base (el diálogo `DialogoHorario` ya no se abre desde la pantalla).
5. **Comprobaciones de esta ronda**: `pruebas_horas.py` (pantalla offscreen) da **0 fallos** con la
   sección nueva **C)**: con un vehículo **BUS-01 BUS** y Guayaquil (200 km · 3,5 h de tabla) la
   llegada al trabajo sale **24/09 07:00** (salida 02:00 + 4 h + 1 h del desayuno), la llegada a
   Miempresa **18:00** y la vuelta de las 18:00 **23:00**, exactamente lo mismo que con los demás
   vehículos; el respaldo de la velocidad del bus da 200 km ÷ 45 km/h → **5 h**. `q_viaje.py`,
   `q_admin.py` y `database.py` compilan en las tres copias y el informe queda en
   `pruebas_horas_resultado.txt`.
6. **Para las computadoras**: es **código nuevo**, así que hay que volver a empaquetar
   (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe` a cada PC. Si algún bus ya
   estaba registrado con otro tipo de vehículo, se corrige en **Parámetros → Vehículos** (dato de la
   base).


## Versión 8.1 — Los km y las horas salen del documento revisado (y las horas se ven como se leen)

1. **La fuente ahora es el documento de la empresa**: `herramientas\preparar_distancias_doc.py` lee
   `excel\DISTANCIAS DOC.docx` (una tabla por provincia, revisadas **cantón por cantón**: cabecera,
   ruta terrestre, distancia real, **tiempo en auto** y **tiempo en autobús**) y lo pasa al formato
   del sistema. Deja el Excel de detalle **«DISTANCIAS Y TIEMPOS DESDE CUENCA (DOC).xlsx»** (todo lo
   del documento + las horas que usará el sistema + el antes/después + una hoja con los cantones que
   el sistema no tiene), el Excel de tres columnas **«TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx»**
   para el botón 📥 Importar Excel, el reporte `herramientas\distancias_doc_resultado.txt` y los
   `.sql` de `servidor\` (el respaldo lo hace `respaldar_base_nativo.bat`). La base **solo se lee**.
2. **Una sola hora por cantón, sacada de los dos tiempos del documento**: el sistema usa **una**
   hora por destino (la que ya tenía), así que se calcula con la regla `--horas`:
   **promedio** (por defecto: el punto medio entre el auto y el autobús), `auto`, `auto1`
   (auto + 1 h, la regla del Excel anterior), `bus` y `bus1` (bus − 1 h). El resultado se redondea a
   **5 minutos** y se guarda en decimal (6.0 = 6:00). Con **promedio** MACAS queda en **6:00**
   (auto 5:15 + bus 6:45), o sea el **mismo recorrido de 6 h** que daban los 5:40 que ya se usaban
   —con las 4,5 h del Excel viejo el sistema redondeaba a 5 h—, así que la llegada del viático de
   Macas no se mueve respecto de la propuesta que la empresa aprobó.
3. **Las horas ya no se ven en decimal**: el sistema mostraba «5.67 h» en la lista de
   **Parámetros → 🗺️ Provincias y km** y «4.5 h de viaje» en el formulario de viáticos, que parece
   un error. Ahora se muestran **como se leen** —«5 h 40 min»— en los dos lugares y en la bitácora,
   con dos funciones nuevas de `calculos.py` (`horas_texto` y `horas_de_texto`). En el campo de
   horas se puede escribir **«5:40» o «5,67»** (se entienden las dos formas); el Excel de
   importación sigue llevando el decimal, que es como lo lee el sistema.
4. **Lo que entra y lo que no**: del documento salen **196 cantones** (los 202 de la base, menos los
   **5** que el documento no trae —CHUMBLÍN, HUAMBI, ISABELA, SAN CRISTÓBAL y SANTA CRUZ— y Cuenca,
   que es el origen). Los **20 cantones** del documento que el sistema todavía no ofrece
   (Camilo Ponce Enríquez, Nabón, San Fernando, Colta, Atahualpa, Las Lajas, Eloy Alfaro,
   Gral. Antonio Elizalde, Pindal, Valencia, Puerto López, Santa Ana, Huamboya, Pablo Sexto,
   San Juan Bosco, Sevilla Don Bosco, San Pedro de Pelileo, Santiago de Píllaro, Paquisha y
   Yantzaza) quedan **fuera** y anotados con sus km y tiempos en la segunda hoja del Excel, para
   agregarlos cuando se decida: si se escribieran en la base no saldrían nunca en el formulario.
   También quedan anotados los **repetidos** (BOLÍVAR de Carchi y de Manabí, OLMEDO de Loja y de
   Manabí): el sistema guarda uno solo de cada nombre.
5. **Comprobaciones**: `pruebas_horas.py` da **0 fallos** (sección nueva **F**: 5.67 h → «5 h 40 min»
   y se entienden «5:40», «5 h 40 min», «5,5», «6» y lo que no se entiende queda en blanco),
   `pruebas_qt.py` **46 de 46** y la herramienta del documento corre sin tocar la base
   (MACAS 242 km · 6 h 00 min · recorrido 6 h; AZOGUES 32 km · 0 h 40 min).
6. **Para las computadoras**: es **código nuevo** (`calculos.py`, `q_admin.py`, `q_viaje.py`), así
   que hay que volver a empaquetar (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar
   `dist\Sistema_Viaticos.exe`. Los km y las horas son **dato de la base**: se cargan con el botón
   📥 Importar Excel o con `servidor\cargar_distancias.bat` en la base central (que respalda
   primero y tiene su `ANTES` para volver atrás).

## Versión 8.2 — La pantalla ya no se queda pensando (la conexión se reutiliza)

1. **Qué pasaba**: el sistema abría y cerraba una conexión a la base **en cada consulta**
   (`conectar()` de `bd.py`). Contra la base central PostgreSQL eso significa repetir el saludo
   completo por la red —TCP + usuario + clave + arranque de la sesión en el servidor— **cada vez**, y
   el formulario de viáticos consulta muchísimas veces por interacción: los parámetros, los km y las
   horas del cantón, la lista de empleados, los clientes, los vehículos… De ahí la pausa al elegir
   **provincia** y **cantón**, y la demora al **guardar** hasta verlo en el historial. Una vuelta
   normal por la pantalla gastaba entre 25 y 30 conexiones nuevas.
2. **La conexión se reutiliza**: `bd.py` guarda la conexión y la va **prestando** (`_RESERVA`): el
   que la pide la devuelve al terminar y se vuelve a usar. Nada más cambia: `conn = conectar()` y
   `with conectar() as conn:` siguen comportándose igual (lo que no se confirma con `commit` se
   pierde al cerrar, como antes). Si el servidor o un cortafuegos corta una conexión que estuvo
   quieta, el sistema lo detecta con un `SELECT 1` y abre otra en lugar de fallar al guardar; a la
   conexión del servidor se le pusieron además `keepalives` para que no la corten por estar quieta.
   Se agregaron `bd.estadisticas()` (conexiones abiertas / reutilizadas / consultas) y
   `cerrar_reserva()`, que se usa al cambiar de servidor y al cerrar el sistema.
3. **Memoria corta de los catálogos**: `database.py` recuerda **30 segundos** los datos que se piden
   a cada rato y casi nunca cambian —parámetros, km y horas de las rutas (la tabla entera de una sola
   lectura), empleados, clientes, vehículos, provincias y cantones—. Todo lo que **graba** esos datos
   borra la copia en el momento (`olvidar_cache`), así que nunca se ve un dato viejo propio.
4. **Las listas desplegables no van a la base en cada clic**: `qt_comunes.ComboAuto` recuerda sus
   opciones **5 segundos** y solo las vuelve a dibujar si cambiaron. Abrir la lista de cantones
   (~200 nombres) ya no consulta ni repinta: era la causa de que la ventana se quedara pensando.
5. **Comprobado con números** (`pruebas_rendimiento.py`, con las ventanas de viáticos y de parámetros
   armadas de verdad y 25 ms simulados por cada conexión nueva, como en la red de la empresa):

   | Acción | antes | ahora |
   |---|---|---|
   | Elegir provincia | 30 ms | 0,4 ms |
   | Elegir cantón | 31 ms | 1,2 ms |
   | Abrir la lista de cantones | 1 ms | 1 ms (sin consultar) |
   | Refrescar el historial | 114 ms | 7 ms |
   | Ver el detalle de un viático | 58 ms | 4 ms |
   | Guardar y ver el historial | 172 ms | 11 ms |
   | **Las 14 acciones de la prueba** | **1.567 ms · 30 conexiones** | **766 ms · 0 conexiones** |

6. **La herramienta queda en el sistema**: `python pruebas_rendimiento.py` (base local de prueba, no
   toca los datos de trabajo), `--comparar` (antes/ahora en la misma corrida),
   `--simular-conexion=25` (como si fuera por la red) y `--servidor` (mide contra la base central,
   **solo leyendo**).
7. **Comprobaciones**: `pruebas_qt.py` **46 de 46**, `pruebas_horas.py` **0 fallos**,
   `pruebas_ventanas.py` **8 de 8**, `pruebas_conexion.py` **8 de 8** (que la conexión se reutilice,
   que lo confirmado con `commit` se guarde, que lo que no se confirma se pierda y que una consulta
   que falla no dañe la conexión) y las 14 acciones de `pruebas_rendimiento.py` sin errores. La base
   **no se tocó**: solo se leyó, y las herramientas trabajan sobre una base temporal que se borra al
   terminar.
8. **Para las computadoras**: es **código nuevo** (`bd.py`, `configuracion.py`, `database.py`,
   `qt_comunes.py`, `q_conexion.py`, `main_qt.py`), así que hay que volver a empaquetar
   (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe` a cada PC. No hay ningún
   cambio en la base de datos: los `.sql` de `servidor\` siguen igual.






## Versión 8.3 — El empaquetado ya no se cae si hay un Excel abierto

1. **Qué pasaba**: `Sistema_Viaticos.spec` metía la carpeta `excel\` completa
   (`datas=[('image.png','.'),('excel','excel')]`). Mientras alguien tenía un Excel **abierto** en
   esa carpeta, Office deja ahí un temporal (`~$algo.xlsx`) que Windows **no deja leer**, y el
   empaquetado terminaba en `PermissionError: ...~$distancias_cuenca_cantones_ecuador.xlsx`:
   había que cerrar el Excel para poder empaquetar.
2. **La carpeta se arma archivo por archivo** (`_catalogo_excel()` en el `.spec`): salta los
   temporales de Office (`~$…`), los ocultos (`.…`, `Thumbs.db`, `desktop.ini`) y los `*.tmp`, y a
   los demás les prueba abrirlos: si alguno está bloqueado (abierto, sincronizándose) lo **deja
   fuera con un AVISO bien visible** en vez de botar el empaquetado. Los catálogos siguen viajando
   dentro del `.exe` (de ahí los lee la carga inicial de un servidor nuevo).
3. **Comprobado con una prueba de verdad**: con un `~$…` y un catálogo **bloqueado sin compartir**
   (el bloqueo de Excel se reproduce con `CreateFileW`), PyInstaller terminó con **código 0**, el
   `.exe` salió de **65,5 MB**, los dos archivos de prueba se borraron y el aviso salió para los
   dos: el temporal se omitió y el bloqueado quedó fuera con su AVISO.
4. **Para las computadoras**: se vuelve a empaquetar (`EMPAQUETAR_EXE_SERVIDOR.bat`) y se copia
   `dist\Sistema_Viaticos.exe`. No cambia ningún dato.

## Versión 8.4 — YANTZAZA entra al catálogo (y un cantón ya no se escribe a mano)

1. **Qué pasaba**: el documento «DISTANCIAS DOC.docx» **sí** trae YANTZAZA (231 km · auto
   4 h 15 min · bus 5 h 30 min), pero el cantón **no estaba en el catálogo del formulario**
   (`PROV_CANT` de `database.py`, o sea las tablas `provincias`/`cantones`), así que
   `preparar_distancias_doc.py` lo mandaba a la segunda hoja del Excel («Cantones sin cargar») y
   **no entraba** ni al Excel de importación ni a los `.sql`. La empresa lo estaba usando a mano:
   en **Parámetros → 🗺️ Provincias y km** escribió «YANTZAZA» con **215 km y 5 h**, y eso quedó en
   `distancias` de la base central —el viático lo calculaba bien—, pero el cantón no aparecía en la
   lista desplegable del formulario y había que escribirlo cada vez.
2. **YANTZAZA queda en el catálogo**: se agregó a `PROV_CANT["ZAMORA CHINCHIPE"]`, a la semilla de
   km (`KM_CUENCA`: 215) y a la de horas (`HORAS_CUENCA`: 5). Como el catálogo se siembra **solo
   cuando la base está vacía**, se agregó una **reparación que corre una sola vez por base**
   (`_reparar_catalogo_cantones`, con su marca `catalogo_cantones_8_4` en `seq`): mete en
   `provincias`/`cantones` los cantones de fábrica que le falten a la base y **no pisa** ningún km
   ni hora ya cargado. Corre en la central y en la base de cada PC al abrir el sistema, y para el
   servidor quedó `servidor\viaticos_cantones_NUEVO.sql` (idempotente, con su «cómo se vuelve
   atrás»). **En la central ya quedó aplicado**: 205 cantones, YANTZAZA con 215 km · 5 h.
3. **Lo de la empresa manda sobre el documento**: la herramienta tiene ahora la lista `FIJOS` con
   YANTZAZA (**215 km y 5 h**), así que al regenerar los Excel y los `.sql` el Word **no** pisa lo
   que la empresa dejó a mano; el reporte lo marca con «← FIJADO A MANO» y tiene su sección propia.
   Si algún día se decide usar el dato del Word (231 km), se borra esa línea.
4. **Un cantón escrito a mano ya no se pierde**: al guardar km y horas en **Parámetros →
   🗺️ Provincias y km**, si el cantón no estaba en el catálogo se **agrega a la provincia elegida**
   (`database.asegurar_canton`, con `asegurar_provincia` si hace falta), queda en la lista del
   formulario y en la bitácora («AGREGÓ CANTÓN»). Es lo que evita volver a escribir YANTZAZA.
5. **Los archivos regenerados**: `excel\TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx` (197 cantones,
   con YANTZAZA), `excel\DISTANCIAS Y TIEMPOS DESDE CUENCA (DOC).xlsx` (YANTZAZA en la hoja de
   detalle; 19 en la de «sin cargar», antes 20), `herramientas\distancias_doc_resultado.txt` y los
   dos `.sql` de `servidor\`. Comparado cantón por cantón, **lo único que cambia** respecto de lo
   que ya tenía la central es la fila de YANTZAZA: los 196 cantones del documento quedan igual (la
   central ya tenía los valores del documento: MACAS 242 km · 6 h, CAÑAR 68 km, 24 DE MAYO 358 km,
   AZOGUES 32 km). Ojo: el `(NUEVO).xlsx` que había en disco era uno **viejo** —hecho por la
   herramienta anterior con `distancias_cuenca_cantones_ecuador.xlsx` y +1 h—; se reemplazó por el
   del documento.
6. **El arranque de un servidor nuevo ya no depende del orden alfabético**: `database.py` elige el
   Excel de los tiempos de viaje con `PREFERIDOS_RECURSOS` («TIEMPOS DE VIAJE MIEMPRESA (NUEVO)»),
   igual que el de los clientes. Antes ganaba el primero en orden alfabético y una copia suelta que
   hay en `excel\` («TIEMPOS DE VIAJE PU (2).xlsx», de un guardado en Excel) le ganaba al bueno.
7. **Comprobaciones**: `pruebas_qt.py` **51 de 51** (5 nuevas: YANTZAZA en el catálogo, YANTZAZA
   con 215 km · 5 h, un cantón escrito a mano entra al catálogo y no se duplica, la reparación lo
   vuelve a meter si falta y el Excel elegido es el de la herramienta), `pruebas_horas.py`
   **0 fallos**, `pruebas_ventanas.py` **8 de 8** y `pruebas_conexion.py` **8 de 8**. En una base
   **nueva** (carpeta temporal: los datos de trabajo no se tocaron) quedó YANTZAZA 215 km · 5 h y en
   su catálogo, con los 203 cantones del documento.
8. **Para las computadoras**: es **código nuevo** (`database.py`, `q_admin.py`), así que hay que
   volver a empaquetar (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe`. A las
   bases no hay que hacerles nada más: la reparación del catálogo las arregla sola al abrir.

## Versión 8.5 — Memoria temporal: no se pierde lo que se estaba capturando

1. **Lo que pidió la empresa**: si la vendedora cierra el sistema por error —o se apaga la
   computadora— a mitad de una cotización, poder **entrar otra vez con su usuario y ver lo que ya
   estaba llenando**.
2. **La pantalla guarda sola lo que se lleva escrito** (`q_viaje.py`): cada **20 segundos** (temporizador
   `self._memoria`) y **al cerrar la ventana** (`closeEvent`), y también en cuanto se **agrega o quita
   un acompañante**. No se guarda en un archivo de la PC sino en la tabla nueva **`borradores`** de la
   base en uso y **por usuario** (el de la clave, `database._clave_borrador`), con lo que se recupera
   igual en la misma computadora o en otra cuando se trabaja contra la central.
3. **Al volver a entrar se ofrece recuperarlo**: al abrir la ventana de viáticos sale un aviso (con la
   ventana ya dibujada, 700 ms después) que dice **cuándo** quedó («hoy a las 14:05», «ayer a las
   09:30», «el 28/09/2026 a las 09:30») y un **resumen** para reconocerlo (encargado, destino, km,
   cliente, cuántos acompañantes y, si era una edición, el número del viático). Si dice que sí, el
   formulario vuelve **tal como estaba**: datos generales, cliente, vehículo, órdenes y recibos,
   fechas y horas, provincia y cantón, km, peaje, transporte/otros, efectivo de combustible y la
   **lista de acompañantes** con su medio y su extra. Lo recuperado **no** se recalcula (las horas
   quedan como se escribieron, igual que al abrir un viático guardado).
4. **También se puede pedir a mano**: botón **🕘 RECUPERAR LO ÚLTIMO** en la barra de la captura (y si
   no hay nada guardado, lo dice). La recuperación queda en la bitácora como «RECUPERÓ LO QUE ESTABA
   LLENANDO», con la fecha y la hora del borrador.
5. **Nunca molesta ni ensucia**: solo se guarda si hay algo escrito **y** distinto de como estaba el
   formulario al abrirlo (`_hay_algo_que_recordar`), así que abrir la pantalla y cerrarla sin escribir
   nada no deja aviso para la próxima vez. El borrador se borra **al guardar el viático**, **al usar
   🧹 LIMPIAR / CANCELAR** y **a los 30 días** los que nadie reclamó (`borrar_borradores_viejos`, que
   corre al abrir el sistema con su propia conexión: `init_db`).
6. **Un caso que había que resolver**: si lo que quedó a medias era la **edición** de un viático que ya
   se guardó (o se anuló) en otra computadora, al recuperarlo el sistema lo avisa y lo deja como
   viático **NUEVO**, para no pisar lo que ya está guardado (`_viatico_pendiente`).
7. **Base de datos**: se agregó la tabla `borradores` al esquema de `database.py`
   (`usuario` · `pantalla` · `datos` (JSON) · `actualizado_el`). El sistema la crea **sola** en la base
   que use cada computadora al abrirse (`CREATE TABLE IF NOT EXISTS`, funciona igual en SQLite y en
   PostgreSQL), así que **no hace falta ningún `.sql`** ni tocar la central a mano: la primera PC con
   el `.exe` nuevo la deja creada.
8. **Comprobaciones**: `pruebas_qt.py` **58 de 58** (7 nuevas: guardar y volver a leer un borrador, que
   se borre al guardar el viático, que los viejos se descarten solos, que la ventana guarde sola lo
   escrito con su encargado/km/acompañantes, que **al volver a entrar con el mismo usuario se recupere
   igual**, que **otro usuario no vea nada** y que al limpiar el formulario se borre),
   `pruebas_ventanas.py` **8 de 8**, `pruebas_horas.py` **0 fallos** y `pruebas_conexion.py`
   **8 de 8**. Además, con el **`.exe` nuevo** y su autodiagnóstico (`VIATICOS_SELFTEST=1`) contra la
   **base central** (192.168.1.4:2345): **todo correcto**, los 13 módulos cargados y la tabla
   `borradores` **creada sola** en la central (`usuario` · `pantalla` · `datos` ·
   `actualizado_el`), con el ciclo guardar → leer → borrar comprobado en PostgreSQL (con un usuario de
   prueba que se borró después: no queda ningún borrador). En la base local de este equipo también se
   comprobó el ciclo completo.
9. **Para las computadoras**: es **código nuevo** (`database.py`, `q_viaje.py`), así que hay que volver
   a empaquetar (`EMPAQUETAR_EXE_SERVIDOR.bat`) y copiar `dist\Sistema_Viaticos.exe`. La tabla se crea
   sola al abrir el sistema; no hay que aplicar nada en la base central.

## Versión 8.6 — Los Excel, la semilla y la base local dicen lo mismo que el documento

1. **Lo que quedaba desalineado**: la **base central** ya tenía los km y las horas del documento
   revisado y el `.exe` llevaba el Excel corregido, pero quedaban cuatro rincones con los valores
   *viejos*. El más peligroso: `excel\TIEMPOS DE VIAJE MIEMPRESA.xlsx` (el del 29/09) seguía con
   MACAS **230 km · 4,5 h**, AZOGUES 30 · 2, 24 DE MAYO 380 · 6, CAÑAR 60 · 3 y GUAYAQUIL 200 · 3,5, y
   es **justo el nombre que mencionaba el texto en pantalla** de Parámetros → 🗺️ Provincias y km:
   quien abriera **📥 Importar Excel** y eligiera ese archivo volvía a los datos viejos y anulaba la
   corrección. Los otros tres: la **semilla de fábrica** (`database.KM_CUENCA` / `HORAS_CUENCA`) y la
   **base local de este equipo**, que hacían que una base **nueva** (o una PC que no alcanzara el Excel
   que viaja con el programa) naciera con los km y las horas de antes.
2. **La semilla de fábrica ahora es el documento** (`database.py`): `KM_CUENCA` (203 cantones) y
   `HORAS_CUENCA` (197) traen los valores del documento revisado, agrupados por provincia y con su
   comentario. **YANTZAZA** queda con lo que la empresa dejó a mano (215 km · 5 h, que es como viene
   fijado en el Excel) y los **6 cantones que el documento no trae** —CHUMBLÍN, HUAMBI, CUENCA e
   ISABELA / SAN CRISTÓBAL / SANTA CRUZ— conservan lo de siempre. Se generó de una sola pasada desde
   el Excel bueno (no se escribió número por número a mano).
3. **La base local de este equipo quedó igual al documento**: se cargó el Excel corregido con la misma
   función del botón **📥 Importar Excel** (197 cantones, **0 diferencias** contra el archivo) y, antes
   de tocarla, se dejó un respaldo de la base: `data\viaticos.db.bak_20260930`. La **central no se
   tocó**: se comprobó cantón por cantón contra el Excel y tiene **0 diferencias** en los 197.
4. **Los dos Excel de la carpeta dicen lo mismo**: se volvió a armar
   `excel\TIEMPOS DE VIAJE MIEMPRESA.xlsx` con `herramientas\generar_excel_tiempos.py` (203 cantones:
   los 197 del documento más los 6 que él no trae; 199 con horas —197 de la empresa y 2 de la ruta—).
   Comparado cantón por cantón con el **«(NUEVO).xlsx»**: **0 diferencias** en los 197 que ambos
   traen. Así, elija el archivo que elija quien importe, los datos que entran son los del documento.
5. **Los textos ya nombran el archivo correcto**: el aviso de la pantalla (`q_admin.py`) dice ahora
   «TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx» (en la carpeta `excel\` del programa), igual que el
   `docstring` de `importar_distancias_excel` y los comentarios de `q_viaje.py`, `database.py` y
   `herramientas\generar_excel_tiempos.py` (que además explica que el **azul** es «el tiempo de la
   empresa: el del documento revisado o el que ella dejó puesto»). `herramientas\tiempos_de_viaje.py`
   ya no pisa ninguno de los 197 cantones con un tiempo de ruta, que es lo correcto ahora.
6. **Pruebas nuevas para que no se vuelva a desalinear** (`pruebas_qt.py`, **60 de 60**): la semilla
   de fábrica tiene que traer los km y las horas del documento (los 197, comparados uno por uno) y los
   dos Excel de tiempos de viaje de la carpeta **no se pueden contradecir**. Además
   `pruebas_horas.py` **0 fallos** (se pusieron al día dos valores de ejemplo de Guayaquil: ahora
   196 km · 4 h, antes 200 km · 3,5 h), `pruebas_ventanas.py` **8 de 8** y `pruebas_conexion.py`
   **8 de 8**.
7. **El `.exe`**: rearmado con `EMPAQUETAR_EXE_SERVIDOR.bat` apuntando a la central
   (192.168.1.4:2345) y comprobado con su autodiagnóstico (`VIATICOS_SELFTEST=1`) contra esa base:
   **todo correcto**. Los Excel que lleva dentro ya son los cuadrados.
8. **Para las computadoras**: es **código nuevo** (`database.py`, `q_admin.py`, `pruebas_*`), así que
   hay que volver a copiar `dist\Sistema_Viaticos.exe`. **A la base central no hay que aplicarle
   nada** (ya tenía los valores del documento). Si alguna PC trabajara con **base propia** (sin
   central), sus km y horas se ponen al día con **Parámetros → 🗺️ Provincias y km → 📥 Importar
   Excel** y el Excel de la carpeta; y de ahí en adelante **toda base nueva nace con los valores del
   documento**, incluso si no encuentra el Excel.

## Versión 8.7 — Editar un viático ya no borra el km ni el parqueadero/peaje (ni el cierre)

1. **Lo que pasaba**: al abrir un viático guardado con **Editar**, el formulario mostraba el **km** y el
   **parqueadero/peaje** en **cero** cuando el **chofer era otra persona** distinta del encargado. Esos
   dos datos (y con ellos el **combustible** y el **total**) se guardan en la fila de **quien recibe el
   efectivo** —el chofer y, si no hay chofer en el viaje, el encargado—, pero el formulario los leía de
   la **primera fila** (la del encargado), que los tiene en cero. Al volver a guardar, la edición los
   dejaba en cero: **se perdía el peaje del viático**. En la base de este equipo **3 de los 5 viáticos**
   estaban así (N° 001, 002 y 003 de 2026, con el chofer distinto del encargado).
2. **El arreglo** (`q_viaje.py`): una función nueva `_fila_de_los_gastos()` devuelve la fila que de
   verdad lleva el km, el parqueadero/peaje y el combustible (la del **chofer** o, en viáticos viejos
   guardados sin esa marca, la que tenga los valores) y el formulario carga el km y el peaje **de ahí**.
   La fila del encargado también se busca por su marca (`es_encargado`) y no por la posición.
3. **El cierre ya no se pierde** (`database.py`): al editar, la pantalla borra las filas del viático y
   las vuelve a escribir con lo que hay en el formulario —que no toca la justificación—, así que después
   hay que **reponer** el cierre. Antes se reponían el estado, la justificación y la devolución, pero
   **no** el **«pago al empleado»** ni el **«elaborado por»**: un viático reactivado (↩ A pendiente) y
   editado quedaba **sin firma**. Ahora la lista del cierre es una constante (`VIAJE_COLS_CIERRE`, ocho
   columnas, las dos nuevas incluidas) y la repone `_restaurar_cierre()`, que usan las dos ediciones (la
   del original y la del ajuste). Si mañana se agrega otra columna de cierre, con sumarla a esa
   constante queda protegida.
4. **Comprobado sobre una COPIA de la base** (`data\viaticos.db` **no se tocó**): se editaron el original
   y el ajuste de los viáticos **guardando exactamente lo mismo** y se comparó **fila por fila y
   columna por columna**, incluido el cierre: **sin diferencias**. El antes/después quedó a
   la vista: con el código viejo el formulario cargaba `km=0 · peaje=0` y la edición dejaba
   `elaborado_por = None`; con el nuevo carga el **km y el peaje que tenía el viático** y
   conserva `elaborado_por`.
5. **Lo demás sigue igual**: `pruebas_qt.py` **60 de 60**, `pruebas_ventanas.py` **8 de 8**,
   `pruebas_conexion.py` **8 de 8** y `pruebas_horas.py` **0 fallos**.
6. **Para las computadoras**: es **código nuevo** (`q_viaje.py` y `database.py`), así que hay que volver
   a copiar `dist\Sistema_Viaticos.exe`. **A la base no hay que aplicarle nada**: los viáticos guardados
   están bien; lo que estaba mal era la pantalla al editarlos.


