<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# MIEMPRESA — Sistema de Viáticos · **Empiece por aquí**

## ¿Qué hay en cada carpeta?

| Carpeta / archivo | Qué es | Cuándo se usa |
| --- | --- | --- |
| **`servidor\`** | Todo lo del servidor de la base de datos (PostgreSQL): `respaldar_base_nativo.bat` (respaldo diario de la base), `PROBAR_SERVIDOR.bat` (probar el puerto desde otra PC) y `respaldos_base\` (los respaldos `.sql`). | En **un solo** equipo: el que hará de servidor. |
| **`sistema_viaticos_miempresa\`** | **El programa**: código, `INICIAR.bat`, **`EMPAQUETAR_EXE_SERVIDOR.bat`** (el único empaquetador), la carpeta `data` (base local de este equipo), `excel\` (listas de personal y clientes para importar) y `documentacion\capturas\` (imágenes de las pantallas). | En el equipo donde se programa y en el que se generan los `.exe`. |
| **`herramientas\`** | Utilidades que **no** son parte del programa: `limpiar_y_firmar.py` (firma del autor y limpieza), `tiempos_de_viaje.py` (horas de viaje de los cantones, medidas con la ruta real de OpenStreetMap), `generar_excel_tiempos.py` (arma el Excel **TIEMPOS DE VIAJE MIEMPRESA.xlsx** con las horas y los km), `preparar_distancias_doc.py` (pasa el Word **DISTANCIAS DOC.docx** —los km revisados cantón por cantón, con el tiempo en auto y en autobús— al formato del sistema, con **una hora por cantón** y los Excel y `.sql` listos para cargar), `preparar_distancias_excel.py` (lo mismo cuando la fuente es un Excel de la empresa), `ver_excel.py` (mirar un Excel), `comparar_excel_viaticos.py` y `comparar_reglas_excel.py` (cargar el Excel real de viáticos y comparar valores). | Cuando haga falta. |
| `herramientas\excels_de_trabajo\` | Los Excel de trabajo (viáticos y órdenes de producción). Están fuera del programa a propósito. | Para consultar o volver a correr las comparaciones. |
| `herramientas\prueba_excel\data\viaticos.db` | Base **de prueba**: los viáticos del Excel cargados por `comparar_excel_viaticos.py`. | Para revisar esa comparación dentro del sistema. **No** es la base de trabajo. |
| `dist\Sistema_Viaticos.exe` | **El programa terminado.** Se crea al ejecutar `EMPAQUETAR_EXE_SERVIDOR.bat`; es lo único que se copia a las demás computadoras. | Cada computadora de trabajo. |
| **`documentacion\`** | Todas las guías en un solo lugar (ver abajo). | Cuando se tenga una duda. |
| `sistema_viaticos_miempresa\data\` | La base de datos local (SQLite) y los PDF de respaldos de **este** equipo. | Solo en este equipo. **No borrar.** |

## 🚀 La primera vez que se abre en una computadora

**No hay que configurar nada a mano.** Copie el `.exe` en una carpeta **local** (por ejemplo
`C:\Viaticos\`) y ábralo:

- Si el `.exe` ya trae la dirección del servidor (lo normal: se elige al empaquetar), abre directo y en
  la barra amarilla dice **BASE CENTRAL**.
- Si **todavía no hay servidor** o no responde, el programa abre **solo** la pantalla de conexión:
  escriba ahí la **IP**, el **puerto** (`5432`), la base `viaticos`, el usuario `miempresa` y la clave;
  pulse **🔌 Probar conexión** y después **💾 Guardar**. Queda guardado en **esa** computadora
  (`config.json`) y no lo vuelve a pedir.

> El **zoom** (tamaño de pantalla) también se elige en esa pantalla y es de **cada PC**: no se copia a
> las demás. Y nunca reparta un `config.json` junto con el `.exe`.

### Ingreso al sistema: menú primero y clave por área (entrega actual)

- El sistema **abre directo en el menú principal, sin pedir clave**. Así nadie queda afuera por no
  recordar su usuario y el menú se ve desde el primer segundo.
- Al pulsar **cualquier** módulo, el sistema **pide la clave de esa área** y revisa el rol: si la
  clave es de un rol que no corresponde a esa área, no deja entrar y avisa para quién es.
- Qué puede cada rol:

| Área | Vendedoras | Justificación | Superusuario |
| --- | :---: | :---: | :---: |
| Generar / revisar / ajustar viáticos | ✔ | ✔ | ✔ |
| Respaldos (facturas y comprobantes) | ✔ | ✔ | ✔ |
| Justificar viáticos | — | ✔ | ✔ |
| Parámetros, empleados, clientes, vehículos y rutas | ✔ | ✔ | ✔ |
| Informe de actividad (auditoría) | — | — | ✔ |
| Usuarios del sistema | — | — | ✔ |
| Conexión / base de datos | — | — | ✔ |

- **Los parámetros y los catálogos los toca cualquiera**: **⚙️ Parámetros, empleados, vehículos y
  rutas** pide la clave de quien lo abre (vendedora o justificación) y ahí se cambian las tarifas y
  las horas límite, el valor por km y las horas de viaje, los km/horas por cantón, los empleados, los
  clientes y los vehículos. **El cambio queda guardado en la base**, así que lo ven **todas las
  computadoras** (no hay que repetirlo en cada PC) y queda anotado en el informe de actividad con el
  nombre de quien lo hizo.
- **Los Excel se cargan una sola vez**: la lista de **personal**, la de **clientes** y el Excel de
  **km y horas por cantón** (botón 📥 Importar Excel de cada pestaña de Parámetros) quedan guardados
  en la base; con la **base central** los ven todas las computadoras.
- La ventana de ingreso **no lleva leyendas**: antes mostraba, en letra tenue, para qué se pedía la
  clave y **quién podía entrar**. Ahora solo pide usuario y clave; el área se ve en el título de la
  ventana («Ingreso — Parámetros»).
- La casilla **«No volver a pedir la clave en este equipo»** (en la ventana de ingreso) sirve para
  no estar escribiendo la clave a cada rato: se olvida al cerrar el sistema, y en el menú queda el
  botón **🔒 Olvidar la clave** para dejar el equipo sin sesión.
- La pantalla **🔌 Conexión / base de datos** (solo superusuario) **tiene su botón en la barra
  lateral**: ahí se ve la base en uso, se cambia entre la local y la central, se elige dónde se
  guardan los respaldos, se fija la numeración y se cambia el **tamaño de pantalla (zoom) de esa
  computadora**. Si el servidor no responde, esa misma pantalla aparece sola al abrir el programa, y
  **Ctrl+Alt+B** la abre como atajo desde cualquier parte del menú.
- **Las claves se guardan cifradas** (sha256 con sal): en la base no queda la clave legible y tampoco
  se ve en los respaldos. En «👥 Usuarios del sistema» la lista muestra `•••• cifrada`; para
  cambiarla se escribe una nueva (si se deja vacía, no se cambia). Las claves que ya existían se
  cifran solas la primera vez que se abre el sistema con esta versión.
- Cada ingreso y cada cierre de sesión quedan en el **informe de actividad (auditoría)**.

### Interfaz nueva (PySide6) — entrega actual

Todas las pantallas se reescribieron con la **misma apariencia** (azul y amarillo de la marca) y
las **mismas funciones**; lo que se imprime no cambió. Novedades de esta entrega:

- **Todo se ve sin andar bajando con la barra**: las ventanas grandes (Viáticos, Justificación,
  Parámetros, Bitácora…) se abren maximizadas. La **Justificación entra completa en una sola
  pantalla** (en un monitor de 1080p no hay que desplazarse ni de lado ni hacia abajo) y los
  textos largos se reparten en dos líneas en lugar de empujar los campos fuera de la ventana.
- **Imprimir y exportar van en pares**: cada viático y cada justificación se pueden imprimir **y**
  sacar a Excel con el mismo formato de la impresión.
  - **Viáticos → 📋 Historial**: elija el viático y pulse **📊 Excel → Original / Ajuste / General**
    (el archivo lleva la cabecera del viático, el detalle con las 25 columnas del Excel oficial y
    la fila de **totales**). En la pestaña de captura, **📊 EXCEL** saca lo que está en pantalla.
  - **Justificación → 📊 Excel (en la barra de arriba, siempre a la vista)**: **Lista de viáticos**
    saca a Excel la lista que se está viendo (con el buscador y el estado que tenga puestos, sirve
    para entregar los viáticos que se van justificando) y **Justificación** saca el viático elegido
    (cabecera con entregado/respaldado/saldo, devolución y firma, las 16 columnas del Excel de
    justificación y la fila **TOTAL**).
- **Dos formularios en una tarjeta**: «👤 Encargado, chofer y destino | 👥 Empleados adicionales»
  quedó dividida por una línea vertical: a la izquierda el viaje (encargado, chofer, provincia,
  cantón, lugar, km, parqueadero/peaje y otros) y a la derecha los empleados adicionales
  (empleado, medio, extra, los botones *Agregar/Quitar* y su lista compacta). Antes eran dos
  tarjetas y quedaba un hueco en el medio.
- **Fechas del día y combustible al lado**: las cuatro fechas del viaje vienen con el **día de hoy**
  puesto (de ahí se escoge la que se necesite) y el cuadro amarillo **Efectivo sugerido** con su
  botón **USAR** quedó en el mismo renglón, pegado a las fechas (antes quedaba al otro extremo de la
  tarjeta y se veía lejos). Se sigue calculando con los km y la tarifa del sistema.
- **Observaciones otra vez grande**: el campo ocupa **toda la fila**, a lo ancho de la tarjeta de
  datos generales, como estaba antes.
- **Historial más simple**: se quitó el cajón «Ajustes del viático». La lista *Detalle — original y
  ajustes* ya muestra el **original, cada ajuste y los totales** de cada bloque, y ocupa todo el
  ancho. Para imprimir, exportar o editar **un** ajuste hay una lista **📋 Ajuste** en la barra de
  arriba (si no elige ninguno, el sistema pregunta cuál).
- **Calendario completo**: la ventanita del calendario tiene el tamaño mínimo para que se vean
  **todas las fechas del mes** (antes quedaba corta y solo se veían los primeros días) y, cuando el
  campo está vacío, abre en el **mes actual** en lugar de «enero 1900» (el sistema usa el
  01/01/1900 para decir «sin fecha»).
- **Justificación mejor repartida**: el formulario de gasto quedó como **dos columnas que llenan la
  tarjeta** (Fecha/N° comprobante, Tipo/RUC, Proveedor/Lugar, Concepto/Valor), con la
  **Explicación** a todo el ancho, y la tabla de *Detalle de gastos* es más alta.
- **Menú principal**: el tablero de Inicio se reparte todo el ancho (los recuadros llenan la
  pantalla) y se quitó el recuadro «Total» (la suma ya se ve en el detalle de cada viático).
  En la barra de la izquierda los botones van **agrupados**: **TRABAJO DEL DÍA** (viáticos,
  justificar y respaldos) y, aparte con su línea, **🔑 SUPERUSUARIO** (parámetros, auditoría,
  usuarios y conexión).
- **Ingreso más compacto y centrado**: la ventana mide justo lo que ocupan sus campos (430×280) y
  sale **en el centro de la pantalla**, con los campos y los botones equilibrados; Esc sigue
  saliendo del sistema.
- **Empleados adicionales**: el medio sale en **AUTO**; al completar 3 personas en el auto (con el
  encargado) el sistema pasa la lista a **BUS** y la deja bloqueada hasta que se quite a alguien.
- El programa **ya no usa la interfaz anterior (Tkinter)**: se eliminaron esos archivos. El `.exe`
  ahora incluye solo PySide6, así que **pesa menos y arranca más rápido**.
- **Corrección importante (guardar)**: la interfaz nueva **no estaba guardando el viático** (faltaba
  una importación en el código, así que la vista previa salía vacía y el guardado, el historial, el
  ajuste y la justificación se quedaban sin hacer nada). Ya está corregido y comprobado el recorrido
  completo: crear → **guardar** → verlo en el **historial** → **ajustar** → **justificar**.
- **Vista previa**: vuelve a llenarse sola mientras se digitan los datos y **es más alta** (muestra
  las personas, la fila de TOTALES y aire para más). Las columnas de fechas se ensancharon para que
  «23/09/2026» se lea completo (antes salía «23/09/2…»).
- **Excel**: la justificación **ya se puede guardar** (fallaba porque el nombre de la hoja y del
  archivo llevaban el «N°/2026» y Excel no acepta la barra; ahora la hoja queda «Justificación
  0012026» y el archivo `justificacion_001-2026.xlsx`). Además la hoja se ve **llena y ordenada**: el
  título va unido a todo el ancho con fondo azul, cada rótulo con su valor hasta el final (el texto
  largo se ajusta y la fila crece), el encabezado de la tabla queda **congelado** al bajar y la
  columna de los rótulos tiene el ancho que necesita.
- **Justificación sin amontonar**: los datos del viático elegido ahora van en **franjas alternadas**
  (una clara y la siguiente blanca), dos datos por renglón, y las listas largas (personas) a todo el
  ancho: cada dato se distingue del de arriba.
- **Pantalla limpia**: se quitaron los mensajes chiquitos de uso que había bajo los títulos (y los
  subtítulos explicativos de las demás ventanas). El km que sugiere la tabla aparece **junto al campo
  Km** («tabla: 50») y el aviso de **auto lleno** solo sale cuando de verdad se llenó. Los avisos que
  importan (errores, ajustes bloqueados, estados) siguen igual.
- **Comidas y hospedaje según las horas reales** (era lo que estaba mal): ahora se revisa **día por
  día**. Ejemplo real: se van el 23 a las 22:00, llegan al destino el 24 a las 06:00 y el 25 salen
  del trabajo a las 14:00 y llegan a las 20:00 → **2 desayunos, 2 almuerzos, 2 meriendas y 1 noche
  de hospedaje** (antes cargaba comidas del 23 y dos noches). Sale de las horas que se registran en
  «Llegada al trabajo» y «Salida del trabajo». La merienda cuenta hasta las **21:00** (la hora del
  Excel de la empresa) y los viajes de un día dan igual que antes.
- **Las horas: dos se escriben y dos las calcula el sistema.** Ellos registran la **salida de
  Miempresa** y la **salida del trabajo**; el sistema escribe la **llegada al trabajo** y la
  **llegada a Miempresa** (en el formulario cada pareja queda en su propia columna). Se calculan
  solas al cambiar la salida, los km o el vehículo, y también con el botón **⏱ Estimar viaje**:
  quedan escritas y se pueden corregir a mano. Al **abrir un viático guardado no se recalcula
  nada**: se ven las horas que se registraron.
- **Cuánto dura el viaje**: primero las **horas de viaje del destino** (las que la empresa registra
  de verdad: Guayaquil 3,5 h, Quito 9,5 h, Loja 5,5 h… y los demás cantones, cada uno con su tiempo)
  y, si el cantón no tiene ese dato, los km del cantón ÷ la velocidad del medio. El resultado se
  **redondea hacia arriba a la hora entera** (Cuenca–Guayaquil: 3 h 30 → **4 h**) y después se suma
  **una hora por cada comida que cae dentro del viaje**: el que sale a las 10:00 y llega a las 13:00
  queda registrado a las **14:00** (el almuerzo), el que llega al lugar a las 08:00 a las **09:00**
  (el desayuno), el que vuelve a las 22:00 a las **23:00** (la merienda de las 21:00) y el viaje
  largo de 02:00 a 14:00 a las **16:00** (el desayuno y el almuerzo). Cada tramo se cuenta **desde su
  propia salida**: la ida desde la salida de Miempresa y la vuelta desde la salida del trabajo.
  Ejemplo: Guayaquil con salida 02:00 → **llegada al trabajo 07:00**. Las horas de cada cantón se
  ajustan en **Parámetros → Rutas** (junto a los km) y se ven al elegir el cantón («tabla: 200 km ·
  3,5 h de viaje»).
- **En BUS se calcula igual que en los demás vehículos**: el bus hace el mismo viaje y tarda lo
  mismo, así que sus horas (las dos llegadas) también se escriben solas: primero las **horas del
  cantón** y, si el cantón no las tuviera, los **km ÷ la velocidad del bus**, más las comidas que
  caen en el camino. Para que el sistema lo tome como bus, el vehículo se registra con el tipo
  **BUS** en **Parámetros → Vehículos** (después de MOTO) y se elige en «Placa vehículo».
- **Un solo horario para todo el viático**: las cuatro horas valen para todos los viajeros (el
  horario propio por viajero se quitó de la pantalla: ya no hay botón **⏱ Horario…**). Si alguien
  sale o llega a otra hora, se corrige en el viático o en el ajuste.
- **Totales a la vista**: la fila de **TOTALES** va resaltada y, al hacer un **ajuste**, la vista
  previa muestra lo mismo que el informe: **ORIGINAL** con sus totales, cada ajuste con los suyos y
  al final el **TOTAL GENERAL**.
- **Redondeo del cajero**: ahora es al **múltiplo de 5** y siempre hacia arriba (**21 → 25,
  26 → 30**). Se cambia en Parámetros si algún día hace falta otro.
- **Fechas con nombre más claro**: «Regreso Miempresa» ahora se llama **«Llegada Miempresa»**
  (hace pareja con «Salida Miempresa»); «Llegada al trabajo» y «Salida del trabajo» siguen igual.
- Se revisa con `python pruebas_qt.py` (46 comprobaciones: interfaz, ingreso por área y claves
  cifradas, con una base de prueba en una carpeta temporal), `python pruebas_ventanas.py`
  (arma las 7 ventanas con datos de mentira; con `--capturar` guarda imágenes en
  `documentacion\capturas\`) y `python pruebas_conexion.py` (8 comprobaciones de la conexión
  reutilizable, también con una base temporal que se borra al terminar).
- **Si la pantalla se siente lenta** (por ejemplo al elegir provincia o cantón, o al guardar y ver el
  viático en el historial), se mide con `python pruebas_rendimiento.py --comparar --simular-conexion=25`:
  informa cuántas consultas y cuántas conexiones hace cada acción y cuántos milisegundos tarda, con
  una base de prueba temporal (los datos de trabajo no se tocan). Con `--servidor` mide contra la base
  central, **solo leyendo**.


| Archivo | Para qué sirve |
| --- | --- |
| `documentacion\GUIA_DEL_SISTEMA.md` | Todo lo que hace el sistema: pantallas, viáticos, ajustes, justificación, respaldos, usuarios, numeración, reportes y base central. |
| `documentacion\HISTORIAL_DE_CAMBIOS.md` | **Historial** de cómo se fue construyendo el sistema (versión por versión). Es de consulta, no hace falta leerlo para usarlo. |
| `documentacion\INFORME_TECNICO_Y_COSTOS.md` | Informe técnico y estimación de costos/horas del desarrollo. |
| `pruebas_rendimiento.py` (en `sistema_viaticos_miempresa\`) | Mide la velocidad de la pantalla: consultas, conexiones y milisegundos por acción. |

---

## Las 3 reglas que hay que recordar

1. **A las demás computadoras solo se lleva el `.exe`.** El archivo ya trae la dirección del
   servidor, así que no hace falta copiar `config.json` ni ninguna otra cosa. Si algún día
   cambia el servidor, el propio `.exe` muestra una pantalla para escribir la IP nueva.

2. **La base de datos vive en el servidor** (el equipo con el servidor). Todas las computadoras
   trabajan contra esa única base: ven los mismos viáticos, las mismas facturas y la misma
   numeración. La barra amarilla de cada ventana dice **BASE CENTRAL** cuando está así.

3. **Los datos iniciales se suben UNA sola vez y desde la computadora correcta**, abriendo el
   sistema con `sistema_viaticos_miempresa\INICIAR.bat` (**no** con el `.exe`), en
   **🔌 CONEXIÓN / BASE DE DATOS** → **⬆ Subir mis datos locales a la central**.

---

## Arranque rápido (prueba de 2 computadoras)

**En la computadora que tendrá la base de datos (el servidor):**

```
cd C:\MIEMPRESA_VIATICOS\servidor
Start-Service postgresql-x64-<V>            (enciende la base; comprobar con: Get-Service postgresql*)
ipconfig                        (copiar la "Dirección IPv4" del adaptador en uso)
```

Firewall, **una sola vez**, en PowerShell **como administrador**:
```
New-NetFirewallRule -DisplayName "Viaticos PostgreSQL 5432" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow -Profile Any
```

Luego abra `sistema_viaticos_miempresa\INICIAR.bat` → usuario **`MIEMPRESA`** →
**🔌 CONEXIÓN / BASE DE DATOS** → comprobar/guardar → **⬆ Subir mis datos locales a la central**.

**En la computadora de prueba:** copie **solo** `sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe`
y ábralo. Si todo está bien, la pantalla de ingreso dirá **· BASE CENTRAL**.

> El paso a paso completo, con lo que hay que probar y los problemas frecuentes, está en

---

## Usuarios del sistema

| Usuario | Clave | Qué puede hacer |
| --- | --- | --- |
| VENDEDOR1 · VENDEDOR2 · VENDEDOR3 · VENDEDOR4 | `1234` | Crear, revisar, ajustar y justificar viáticos (vendedoras) |
| JUSTIFICA1 | `1234` | Justificar viáticos |
| **MIEMPRESA** | `miempresa` | **Superusuario**: informe de actividad (auditoría), usuarios, conexión a la base y numeración de viáticos. **No aparece en ninguna lista** |

Las claves se pueden cambiar desde **👥 USUARIOS DEL SISTEMA** (solo el superusuario) y quedan
**cifradas**: nadie puede leerlas, ni siquiera mirando la base de datos o un respaldo.

---

## Comparación con el Excel real de viáticos (prueba local)

Dos utilidades de `herramientas\` cargan el Excel de la empresa **en una base local aparte**
(`herramientas\prueba_excel\data\viaticos.db`) y dejan un informe con las diferencias:

```bat
python herramientas\comparar_excel_viaticos.py    &REM Excel histórico (una hoja por viático)
python herramientas\comparar_reglas_excel.py      &REM formato nuevo semanal (reglas contra reglas)
```

Resultados que se pueden esperar de una corrida (el informe concreto queda **fuera del
repositorio**, porque lleva los datos reales de la empresa):

- **Los gastos respaldados coinciden al centavo** entre el Excel de la empresa y el
  programa: los dos lados aplican **las mismas tarifas y las mismas horas límite**.
- Las diferencias que aparecen son de **captura en el Excel** (filas escritas a mano), no
  de reglas: combustible por km con otro valor, filas de «Días de Viaje» en blanco,
  comidas y agua, taxis y el «Transporte» que el programa no paga (va en **otros
  gastos**). Parqueadero/peaje y hospedaje coinciden.

> Antes de cambiar nada en producción: confirme con la empresa la **tarifa por km**, que
> las comidas, el agua y los días se **calculen con las fechas** (no a mano) y que el
> **transporte** y el parqueadero/peaje de cada viaje se registren en el sistema (el
> transporte va en «otros gastos»). La hora de la merienda y el redondeo del cajero se
> cambian en **Parámetros** sin tocar el programa.

---

## Respaldos

- **De la base central** (todos los días, en el servidor):
  `servidor\respaldar_base_nativo.bat` → genera `servidor\respaldos_base\viaticos_FECHA.sql`.
  Ese archivo cópielo a un disco externo o a la nube.
- **De los archivos** (facturas): se guardan **dentro de la base central**, así todas las
  computadoras los ven. Al justificar un viático queda **un solo PDF completo**.

---

## Pasar de las pruebas a la producción (la numeración)

Los viáticos que se hicieron **de prueba se quedan** en el historial: no estorban y la numeración
manda sobre ellos (el sistema nunca entrega un número ya usado). Antes del primer viático **real**:

1. Respalde la base: `servidor\respaldar_base_nativo.bat` (en el servidor).
2. Fije el número por donde debe empezar la numeración real:
   **🔌 CONEXIÓN / BASE DE DATOS → Numeración de viáticos → 💾 Fijar numeración**.
   Por ejemplo: si el último viático de prueba fue el **007/2026** y el próximo real debe ser el
   **008/2026**, escriba **008** y guarde. Desde ahí el sistema sigue solo: 008, 009, 010…
3. El **1 de enero** la numeración vuelve a empezar en **001** por sí sola (001/2027, etc.).

> El sistema **ya no trae ninguna opción que borre la base** (ni en el menú ni por consola). Si algún
> día se quisiera dejar la base solo con los catálogos, se hace **con un respaldo previo** y a mano
> sobre la base central (`DELETE FROM viajes; …` desde pgAdmin) o pidiéndole el script al autor.

> **Nota sobre las pantallas:** todas las ventanas se adaptan al tamaño del monitor. Si el equipo
> tiene una pantalla baja (por ejemplo un monitor de 20" o el escalado al 125 %), el menú principal
> aprieta los botones y, si hace falta, aparece una barra para bajar con la rueda del ratón.
>
> Si aun así algún botón queda fuera de la vista, el **superusuario** puede agrandar o encoger todo
> el sistema desde el botón **🔌 CONEXIÓN / BASE DE DATOS** de la barra lateral → «Tamaño de la
> pantalla en esta computadora»:
> **Automático · 100 % · 90 % · 80 % · 70 % · 60 %** (es el *zoom* de todo el sistema, letra y
> controles, igual que el zoom de un navegador). **Automático** calcula el tamaño según la pantalla
> de ese equipo y es lo recomendado; si todavía queda algo fuera de la vista, elija un porcentaje más
> bajo (por ejemplo **80 %**). Al guardar, el sistema se cierra y se vuelve a abrir solo para
> aplicarlo (después hay que ingresar el usuario otra vez). El tamaño se guarda en el `config.json`
> **de esa computadora**, así que cada PC puede tener el suyo y no afecta a las demás ni a lo que se
> imprime.
