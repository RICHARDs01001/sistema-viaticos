<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Arquitectura y funcionamiento — Sistema de Viáticos MIEMPRESA


**Índice**

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Mapa del proyecto](#2-mapa-del-proyecto)
3. [Arquitectura por capas](#3-arquitectura-por-capas)
4. [Arranque y ciclo de vida](#4-arranque-y-ciclo-de-vida)
5. [Roles, ingreso por área y auditoría](#5-roles-ingreso-por-área-y-auditoría)
6. [Modelo de datos](#6-modelo-de-datos)
7. [Numeración por año](#7-numeración-por-año)
8. [Flujo: generar y revisar viáticos](#8-flujo-generar-y-revisar-viáticos)
9. [Estimado de viaje (horas, km y comidas del camino)](#9-estimado-de-viaje-horas-km-y-comidas-del-camino)
10. [Cálculo del viático (fórmulas del Excel)](#10-cálculo-del-viático-fórmulas-del-excel)
11. [Ajustes del viático](#11-ajustes-del-viático)
12. [Flujo: justificación](#12-flujo-justificación)
13. [Respaldos y PDF consolidado](#13-respaldos-y-pdf-consolidado)
14. [Reportes](#14-reportes)
15. [Parámetros y catálogos](#15-parámetros-y-catálogos)
16. [Fuentes de datos](#16-fuentes-de-datos)
17. [Configuración y conexión](#17-configuración-y-conexión)
18. [Migración a la base central](#18-migración-a-la-base-central)
19. [Borradores (memoria temporal)](#19-borradores-memoria-temporal)
20. [Rendimiento](#20-rendimiento)
21. [Pruebas y autodiagnóstico](#21-pruebas-y-autodiagnóstico)
22. [Convenciones y cómo extender](#22-convenciones-y-cómo-extender)
23. [Glosario](#23-glosario)
24. [Apéndice: función → responsabilidad](#24-apéndice-función--responsabilidad)

---

## 1. Resumen ejecutivo

Aplicación **de escritorio** (Python + **PySide6** + **SQLite/PostgreSQL**) que
reemplaza el manejo manual del viático en Excel. Cubre el ciclo completo:

```
  GENERAR            GUARDAR             AJUSTAR             JUSTIFICAR         AUDITAR
  viático   ──────►  en la base   ──►   días/combustible ─► gastos+facturas ─► bitácora
  (reglas Excel)     (nº por año)       extra y peajes      + cierre          + informes
```

| Hecho | Valor verificado en el código |
| --- | --- |
| Punto de entrada | `sistema_viaticos_miempresa\main_qt.py` |
| Lanzador de escritorio | `INICIAR.bat` (`python main_qt.py`) |
| Interfaz | PySide6 (`q_*.py`); tema, zoom y DPI en `qt_tema.py` |
| Acceso a datos | una sola capa: `bd.py` (SQLite local **o** PostgreSQL central) |
| Datos y reglas | `database.py` (~2.700 líneas, ~120 funciones) |
| Motor de cálculo | `calculos.py` (reglas idénticas al Excel oficial) |
| Informes | `reportes.py` (HTML/PDF) y Excel por documento en `qt_comunes.py` |
| Base local | `data\viaticos.db` (+ `viaticos.db.bak_AAAAMMDD`) |
| Facturas | `data\respaldos\viatico_<clave>\` o dentro de la base, según config |
| Excel de la empresa | carpeta `excel\` (7 archivos, ver §16) |
| Usuarios de fábrica | 4 vendedoras + 1 justificación + 1 superusuario oculto |

**Las tres ideas que sostienen el diseño**

1. **El Excel es la especificación.** Cada fórmula del viático está copiada de la
   hoja de la empresa y probada contra ella (`calculos.py`, y las herramientas
   `herramientas\comparar_reglas_excel.py` y `comparar_excel_viaticos.py`).
2. **Una fila por viajero, un número por viático.** El viático es un grupo de
   personas; cada persona es una fila de la tabla `viajes` con el mismo
   `viatico_numero` (§6).
3. **El cambio de base no cambia la lógica.** Local o central se elige en
   `config.json`; todo lo demás sigue igual (`bd.py`).

---

## 2. Mapa del proyecto

```
MIEMPRESA_VIATICOS\
├─ sistema_viaticos_miempresa\      ← EL PROGRAMA
│  ├─ main_qt.py                     punto de entrada
│  ├─ INICIAR.bat                    lanzador (python main_qt.py)
│  ├─ EMPAQUETAR_EXE_SERVIDOR.bat    empaquetado del .exe
│  ├─ empaquetar_servidor.py         script de empaquetado
│  ├─ bd.py                          conexión SQLite/PostgreSQL
│  ├─ database.py                    datos + reglas + migraciones
│  ├─ calculos.py                    motor de cálculo (Excel oficial)
│  ├─ configuracion.py               config.json, motores, carpetas
│  ├─ migracion.py                   copiar la local a la central
│  ├─ reportes.py                    PDF/HTML de viáticos y justificaciones
│  ├─ autor.py                       créditos y sellado
│  ├─ colores.py / qt_tema.py        paleta corporativa, zoom y DPI
│  ├─ qt_comunes.py                  widgets, tablas, Excel, diálogos
│  ├─ q_login.py q_menu.py           ingreso por área y menú principal
│  ├─ q_viaje.py                     generar / revisar / ajustar viáticos
│  ├─ q_ajustes.py                   justificar viáticos
│  ├─ q_respaldos.py                 respaldos (facturas y comprobantes)
│  ├─ q_admin.py                     parámetros, empleados, clientes, vehículos, rutas
│  ├─ q_bitacora.py                  informe de actividad (auditoría)
│  ├─ q_usuarios.py                  altas, cambios de clave y bajas
│  ├─ q_conexion.py                  servidor, migración, numeración y zoom
│  ├─ pruebas_*.py                   pruebas automáticas (§21)
│  ├─ config.json                    configuración de ESTA carpeta
│  ├─ data\        viaticos.db · viaticos.db.bak_* · respaldos\
│  ├─ excel\                         Excel de la empresa (fuentes de datos)
│  ├─ dist\Sistema_Viaticos.exe      empaquetado de un solo archivo
│  └─ documentacion\capturas\        imágenes de las guías
├─ documentacion\                    las guías .md (este documento vive aquí)
├─ servidor\                         PostgreSQL, respaldo nativo, PROBAR_SERVIDOR.bat
├─ herramientas\                     utilidades de mantenimiento
└─ PARA_GITHUB\  PARA_SERVIDOR\      copias de entrega
```

> **Regla de convivencia:** `sistema_viaticos_miempresa\` es el programa; lo que
> lo rodea (`documentacion\`, `servidor\`, `herramientas\`) son guías,
> infraestructura y utilidades de mantenimiento.

**`herramientas\`** (no forma parte del sistema en producción; son utilidades de
una sola vez):

| Archivo | Para qué |
| --- | --- |
| `tiempos_de_viaje.py` / `generar_excel_tiempos.py` | armar el Excel de km y horas por cantón |
| `preparar_distancias_doc.py` / `preparar_distancias_excel.py` | leer `DISTANCIAS DOC.docx` y pasarlo a Excel |
| `comparar_reglas_excel.py` / `comparar_excel_viaticos.py` | contrastar `calculos.py` contra los Excel reales |
| `recalcular_cajero.py` | recalcular el redondeo de cajero en viáticos viejos |
| `viaticos_148_149.py` | recuperar dos viáticos desde su Excel |
| `limpiar_y_firmar.py` | limpieza previa a la entrega |
| `ver_excel.py` | inspección rápida de hojas y columnas |

---

## 3. Arquitectura por capas

```
┌───────────────────────────────────────────────────────────────────────────┐
│  PRESENTACIÓN (PySide6)                                                   │
│  q_login · q_menu · q_viaje · q_ajustes · q_respaldos · q_admin ·         │
│  q_bitacora · q_usuarios · q_conexion                                     │
│  apoyo visual: qt_tema.py (zoom, DPI, paleta) · qt_comunes.py (widgets)   │
└───────────────┬───────────────────────────────────────────────────────────┘
                │  llama funciones; nunca arma su propia conexión
┌───────────────▼───────────────────────────────────────────────────────────┐
│  DOMINIO                                                                  │
│  database.py  →  catálogos, parámetros, viajes, gastos, respaldos,        │
│                  usuarios, bitácora, numeración, migraciones              │
│  calculos.py  →  reglas de cálculo del Excel (DatosViaje + params → dict) │
│  reportes.py  →  HTML/PDF del viático y de la justificación               │
└───────────────┬───────────────────────────────────────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────────────────────┐
│  PERSISTENCIA                                                             │
│  bd.py  →  Conexion/Cursor homogéneos (mismos `?`, mismas filas-dict)      │
│         ├─ SQLite      data\viaticos.db          (esta PC)                │
│         └─ PostgreSQL  servidor, base `viaticos` (todas las PC)           │
│  configuracion.py  →  qué motor, qué servidor, dónde van los respaldos     │
│  migracion.py      →  copiar local → central                              │
└───────────────────────────────────────────────────────────────────────────┘
```

**Por qué así**

- **Un solo camino a los datos.** Las pantallas nunca abren conexión: piden
  `database.py`, y `database.py` pide `bd.conectar()`. Pasar de SQLite a
  PostgreSQL no toca ni una línea de las ventanas.
- **`calculos.py` no sabe de base de datos.** Recibe un `DatosViaje` y un
  diccionario de parámetros y devuelve números; por eso las reglas se pueden
  comparar contra los Excel reales y probar sin abrir la aplicación.
- **`reportes.py` tampoco.** Recibe filas ya calculadas y arma el HTML que se ve
  igual que el formato de la empresa.
- **La interfaz se carga por partes.** `q_menu.ARCHIVOS_MODULO` guarda
  «clave → (módulo, clase)» y cada ventana se importa **al abrirse**
  (`importlib`), así el menú aparece rápido aunque un módulo sea grande.
- **Nada de rutas absolutas.** `database.carpeta_app()`, `recurso()` y
  `dir_datos()` resuelven el programa, los recursos del `.exe` y la carpeta de
  datos, con lo que la misma lógica sirve ejecutando `python main_qt.py` o el
  `.exe` de `dist\`.

---

## 4. Arranque y ciclo de vida


`main_qt.py` hace, en este orden exacto:

```
1) _asegurar_conexion()
      → q_login.crear_app()            (crea/reutiliza QApplication y aplica el tema)
      → q_conexion.asegurar_conexion() (¿responde la base? ¿central o local?)
   Si la base no responde, se abre la pantalla 🔌 Conexión para arreglarlo
   (cambiar la IP del servidor o seguir en local) sin editar config.json a mano.

2) MenuPrincipal SIN pedir clave
   El menú se ve desde el primer momento; nadie queda afuera por no recordar
   su usuario.

3) Al pulsar un módulo → q_login.pedir_sesion(rol=…)
   Se pide usuario y clave y se comprueba el rol contra PERMISOS_MODULO (§5).
   Cada ingreso y cada cierre de sesión quedan en la bitácora.
```

**Errores.** Como el `.exe` no tiene consola, cualquier excepción del arranque se
muestra en un diálogo (`_aviso_error`) con los últimos 1.500 caracteres del
detalle; en consola se imprime igual.

**Autodiagnóstico del empaquetado.** Con la variable de entorno puesta:

```
set VIATICOS_SELFTEST=1
dist\Sistema_Viaticos.exe
```

se recorre el entorno (rutas, recursos, base, versión, permisos) y el informe se
deja en **`autodiagnostico.txt`**, junto al ejecutable. Sirve para revisar un
`.exe` recién empaquetado con `EMPAQUETAR_EXE_SERVIDOR.bat`.

**Ciclo de vida de una sesión**

```
abrir programa ──► menú (sin clave) ──► «Generar viáticos» ──► clave de la vendedora
                                                │
                        ┌───────────────────────┴────────────────────────┐
                        ▼                                                ▼
                 guarda el viático                              cierra la ventana
                 (queda en la base)                          (vuelve al menú)
                                                                        │
   «Salir» ────────────────────────────────────────────────────────────┘
   → cierre de sesión en la bitácora
```

---

## 5. Roles, ingreso por área y auditoría

Fútbol aparte: **hay tres roles** (`database.py`).

| Constante | Valor | Etiqueta | Quién es |
| --- | --- | --- | --- |
| `ROL_VENDEDOR` | `vendedor` | EMPLEADO(A) | las 4 personas que crean viáticos |
| `ROL_JUSTIFICA` | `justifica` | JUSTIFICACIÓN | quien revisa gastos y cierra |
| `ROL_SUPER` | `super` | SUPERUSUARIO | administrador; **no aparece en ninguna lista ni pantalla** |

`ROLES_VALIDOS = (ROL_VENDEDOR, ROL_JUSTIFICA, ROL_SUPER)`.
`ETIQUETA_ROL` también traduce el valor heredado `admin` como «ADMINISTRADOR»
(por bases viejas).

**El superusuario es invisible:** no se lista en ningún combo. Solo entra
**escribiendo su clave** (y en el login, el campo de usuario puede quedar vacío:
la clave lo identifica).

**Quién abre cada área** — una sola tabla al inicio de `q_menu.py`:

| Módulo | Área | Roles que entran |
| --- | --- | --- |
| `viaje` | Generar / revisar / ajustar viáticos | vendedor, justifica, super |
| `respaldos` | Respaldos (facturas y comprobantes) | vendedor, justifica, super |
| `admin` | Parámetros, empleados, vehículos y rutas | vendedor, justifica, super |
| `ajustes` | Justificar viáticos | **justifica, super** |
| `bitacora` | Informe de actividad (auditoría) | **solo super** |
| `usuarios` | Usuarios del sistema | **solo super** |
| `conexion` | Conexión / base de datos | **solo super** |

`PERMISOS_MODULO` es el único lugar donde se decide esto: para volver a dejar los
parámetros solo en el superusuario basta con dejar `"admin": (db.ROL_SUPER,)`
(lo dice el propio comentario del archivo). `pruebas_qt.py` **verifica estas
reglas** en cada corrida.

**Orden visual del menú** (`GRUPOS`): «TRABAJO DEL DÍA» (viáticos, justificar,
respaldos, parámetros) y, aparte con su línea, «🔑 SUPERUSUARIO» (auditoría,
usuarios, conexión). Un módulo nuevo que no esté en `GRUPOS` aparece solo, en
«OTROS MÓDULOS»: no hay que tocar la tabla para que se vea.

**Claves.** Se guardan **cifradas** (resumen, no texto): el login compara contra
el resumen. Las bases antiguas que tenían las claves en texto se cifran solas la
primera vez que se abre el sistema. La casilla «no volver a pedir la clave»
guarda la sesión **en ese equipo** (por eso es una comodidad por PC, no global).

**Bitácora (`q_bitacora.py`).** Cada evento relevante se registra con usuario,
fecha y detalle: ingresos y cierres de sesión, intentos con clave de otro rol,
alta/edición/baja de empleados, clientes, vehículos, rutas y sedes, cambios de
parámetros, cambios de usuario y clave, y los movimientos de viáticos. La
pantalla de auditoría filtra por usuario, área y fechas, y **exporta el informe
a Excel/PDF**.

---

## 6. Modelo de datos

La base **se crea sola** la primera vez que el programa se conecta: `database.py`
ejecuta `SCHEMA` (todo con `CREATE TABLE IF NOT EXISTS`), válido igual en SQLite y
en PostgreSQL. Después corre las **siembras** (`empleados`, `vehículos`,
`usuarios`, `parámetros`, provincias/cantones) solo si la tabla está vacía, así que
nunca pisa datos ya existentes.

### 6.1 Tablas

| Tabla | Qué guarda | Columnas clave |
| --- | --- | --- |
| `viajes` | **una fila por viajero** | `viatico_numero`, `nombre_empleado`, `lugar_trabajo`, `provincia`, `canton`, `es_encargado`, `es_chofer`, `medio_transporte`, fechas y horas, `dias_viaje`, valores calculados, `estado` |
| `ajustes` | movimientos posteriores de un viático | `viatico_numero`, `nombre_empleado`, `fecha`, `hora`, `concepto`, `otros_gastos` |
| `gastos` | una factura/comprobante de la justificación | `viatico_numero`, `numero_comprobante`, `proveedor`, `ruc`, `lugar`, rubros, `total`, `valor_factura`, `nota` |
| `respaldos` | archivo/imagen de cada comprobante | `viatico_numero`, `nombre_archivo`, `ruta`, `empleado`, `concepto`, `gasto_id`, `contenido` (BLOB) |
| `parametros` | **una sola fila** (`CHECK (id = 1)`) con las tarifas y horas límite | las 23 columnas de `PARAM_COLS` |
| `empleados` | listado de personal | `nombre` (único) |
| `vehiculos` | flota | `placa`, `tipo`, `chofer` |
| `clientes` | clientes y proyectos | `nombre` (único) |
| `provincias` / `cantones` | catálogo geográfico | `provincia_id`, `nombre` |
| `distancias` | **km y horas desde Cuenca por cantón** | `canton` (PK), `km`, `horas` |
| `usuarios` | quién entra y con qué rol | `usuario`, `clave` (cifrada), `nombre`, `rol` |
| `bitacora` | auditoría | `fecha`, `usuario`, `rol`, `accion`, `entidad`, `referencia`, `detalle` |
| `seq` | contadores (uno por año de viáticos) | `nombre` (`viatico_2026`), `valor` |
| `renumeracion` | mapa viejo→nuevo de la renumeración | `viejo` (PK), `nuevo` |
| `borradores` | memoria temporal de la captura, **por usuario** | `usuario` (PK), `pantalla`, `datos` (JSON), `actualizado_el` |

Índices: `viajes(viatico_numero)`, `viajes(fecha_salida)`, `viajes(estado)`,
`gastos(viatico_numero)`, `ajustes(viatico_numero)`, `respaldos(viatico_numero)`,
`usuarios(usuario)`, `bitacora(fecha)`. Existen porque el uso normal es «buscar el
viático por su número» y «filtrar por fecha o estado».

### 6.2 La idea central: un número, varias filas

El «viático» **no es una fila**: es un **número** (`viatico_numero`) que agrupa
tantas filas de `viajes` como personas viajaron. Los datos comunes del grupo
(responsable, cliente/proyecto, orden de combustible, placa, observaciones y los
tres recibos) se repiten en cada fila, y así se puede imprimir la hoja completa sin
cruzar tablas.

```
viatico_numero = 2026007   (año 2026, consecutivo 7)
┌────┬───────────────┬───────────────┬─────────┬───────────┬────────┬─────────┐
│ id │ nombre_emp…   │ lugar_trabajo │ canton  │ es_chofer │ total  │ estado  │
├────┼───────────────┼───────────────┼─────────┼───────────┼────────┼─────────┤
│ 41 │ JARAMILLO …   │ OBRA SUR      │ CUENCA  │ 1         │ 48.00  │PENDIENTE│
│ 42 │ SINCHI …      │ OBRA SUR      │ CUENCA  │ 0         │ 31.00  │PENDIENTE│
└────┴───────────────┴───────────────┴─────────┴───────────┴────────┴─────────┘
```

El otro eje es **quién manda**: `es_encargado` marca al responsable del grupo (de
él sale el «responsable» del viático) y `es_chofer` marca a quien maneja (de él
salen la placa, la orden de combustible y el combustible pagado). Una misma persona
puede ser encargada y chofer.

### 6.3 Tipos de fila dentro de un viático

| `tipo_registro` | Qué es |
| --- | --- |
| `ORIGINAL` | el viático tal como se generó |
| otras | la fila nació de un **ajuste** posterior (`ajuste_numero` dice cuál) |

`ajuste_numero = 0` significa que la fila pertenece al viático original.

### 6.4 Los tres bloques de valores de `viajes`

1. **Lo que se captura**: fechas y horas (salida de Miempresa, llegada al trabajo,
   salida del trabajo, regreso a Miempresa), `km_recorridos`,
   `parqueadero_peaje`, `otros`, `medio_transporte`, `extra_transporte`.
2. **Lo que se calcula** (§10): `dias_viaje`, `desayuno`, `almuerzo`, `merienda`,
   `taxi_salida`, `taxi_regreso`, `hospedaje`, `agua`, `combustible`, `total`,
   `valor_cajero`.
3. **Lo que se cierra en la justificación** (§12): `estado`, `justificado_por`,
   `justificado_el`, `nota_justificacion`, `devolucion_monto`,
   `devolucion_observacion`, `pago_empleado_monto`, `elaborado_por`.

`VIAJE_COLS` (en `database.py`) es la lista ordenada de columnas que se escriben al
guardar un viático; si algún día se agrega una columna, **hay que agregarla también
al esquema y a `VIAJE_COLS`** para que se guarde.

`VIAJE_COLS_CIERRE` es la lista de las columnas que la pantalla **no** escribe (el
cierre de la justificación y la firma): al editar un viático hay que devolverles su
valor tal como estaba, y con agregar ahí una columna nueva queda protegida.

---

## 7. Numeración por año

Se numera **igual que en el manejo manual del Excel**: cada año la serie vuelve a
empezar en 1. Para que los viáticos de 2025 y de 2026 no choquen, el número que se
**guarda** y el que se **ve** son distintos:

```
FACTOR_ANIO = 1000

  se ve:        7      (consecutivo dentro del año)
  se guarda:   2026007 (año * 1000 + consecutivo)
```

Funciones de conversión (`database.py`):

| Función | Entra | Sale |
| --- | --- | --- |
| `clave_viatico(anio, numero)` | `2026, 7` | `2026007` |
| `anio_de(clave)` | `2026007` | `2026` (0 si es numeración antigua) |
| `numero_visible(clave)` | `2026007` | `7` |
| `etiqueta_numero(clave)` | `2026007` | `"007/2026"` |

La carpeta de facturas de ese viático se llama **`viatico_2026007`** (con la clave
completa), así nunca se mezclan dos años.

**El contador.** En la tabla `seq` hay una fila por año, `viatico_2026`, cuyo
`valor` es **el último número usado**. Dos cuidados hacen que el contador sea
confiable incluso con varias computadoras escribiendo a la vez:

1. `_next()` es **atómico**: entrega el consecutivo en una sola operación.
2. **Se pone al día solo**: antes de entregar, mira el mayor `viatico_numero` que
   ya existe en ese año y, si el contador quedó atrás (por ejemplo en una base
   recién copiada), lo sube. Nunca entrega un número ya usado.

`proximo_numero(anio)` (lo que muestra el formulario) devuelve
`max(contador + 1, mayor del año + 1)`, y `numeraciones()` da el resumen por año
(viáticos registrados, último número y cuál sería el siguiente) para la pantalla
🔌 Conexión.

**Fijar el inicio (superusuario).** `fijar_inicio(numero, anio)` pone el contador
para que el próximo viático de ese año sea `numero`; si ese año ya tiene viáticos,
**nunca baja** del siguiente número libre.

**Migración de la numeración antigua.** Las bases viejas numeraban 1, 2, 3… sin
año. La primera vez que se abre una base así, `_migrar_numeracion_por_anio()`:

1. Toma los viáticos con número `< 1000` y les asigna `anio_de_fecha(fecha_salida)`
   como año, continuando **después** del mayor número que ya exista en ese año.
2. Renumera `viajes`, `gastos`, `respaldos` y `ajustes` (pasa primero por
   negativos para que los números nuevos no choquen con los que faltan convertir).
3. Guarda el mapa viejo→nuevo en la tabla `renumeracion` (para poder reparar
   rutas de archivos).
4. Si los respaldos están en carpetas, **renombra** `viatico_<viejo>` a
   `viatico_<nuevo>` y corrige las rutas guardadas.
5. Deja la marca `seq.numeracion_por_anio = 1`: la migración corre **una sola vez**.

Si algo falla, se imprime «No se pudo migrar la numeración: …» y **no se marca
nada**, de modo que se reintenta en el siguiente arranque.

---

## 8. Flujo: generar y revisar viáticos

Pantalla: **`q_viaje.py`** (`ViajeWindow`). Es el corazón del sistema.

### 8.1 Generar un viático nuevo

```
1. El formulario arranca con el próximo número del año (proximo_numero()).
2. Se eligen el responsable (encargado) y el cliente/proyecto.
3. Se arma la lista de PERSONAS que viajan (empleados del catálogo).
4. Se eligen provincia y cantón → se llenan km y horas desde Cuenca
   (tabla `distancias`; si el cantón no está, KM_APROX / HORAS_CUENCA, §16).
5. Se capturan las fechas y horas: salida de Miempresa, llegada al trabajo,
   salida del trabajo y regreso a Miempresa.
6. Se marca quién es encargado y quién es chofer, el vehículo, el medio de
   transporte y las novedades (km, parqueadero/peaje, otros).
7. Se pulsa Generar → calculos.py calcula una fila por persona y se guardan
   todas con el MISMO viatico_numero.
```

Cada persona que viaja en un vehículo distinto **repite el bloque de fechas y
horas**: el formulario permite varias «personas» con sus propios horarios y su
propio cantón dentro del mismo viático.

### 8.2 Revisar / editar

La pantalla muestra la lista de viáticos por número (y por fecha/estado) y al abrir
uno se ven sus filas con **los mismos campos que el Excel**, más los botones de
ajuste, anulación, reimpresión y borrado. Al guardar una corrección se reescriben
las filas del grupo (`viajes`), conservando el número.

Dos cuidados de la edición (v8.7), porque lo que la pantalla no lee del lugar correcto
se pierde al volver a guardar:

- El **km, el parqueadero/peaje y el combustible** se escriben una sola vez en el
  formulario, pero se guardan en la fila de **quien recibe el efectivo** —el chofer y,
  si no hay chofer en el viaje, el encargado (`es_chofer`)—. Al abrir el viático se
  leen de **esa** fila (`_fila_de_los_gastos()`), no de la del encargado.
- El **cierre** de la justificación (`estado`, `justificado_por`, `justificado_el`,
  `nota_justificacion`, `devolucion_monto`, `devolucion_observacion`,
  `pago_empleado_monto`, `elaborado_por`) no lo toca la pantalla: hay que **reponerlo**
  después de reescribir las filas (`_restaurar_cierre()`), o el viático quedaría como
  recién creado.

### 8.3 Estados

| Estado | Significa |
| --- | --- |
| `PENDIENTE` | generado, todavía sin justificar (es el estado al crear) |
| `JUSTIFICADO` | justificación cerrada (`justificar()`), con quién y cuándo |
| `ANULADO` | dado de baja lógica (`anular_viaje()`); no se borra |

`reactivar_viaje()` devuelve un `JUSTIFICADO` a `PENDIENTE` (y limpia
`justificado_por` / `justificado_el`) para corregir la justificación.

### 8.4 Borradores: nada se pierde

Mientras se llena el formulario, `q_viaje.py` guarda el estado de la pantalla en la
tabla **`borradores`** (por usuario) **cada 20 segundos y al cerrar la ventana**. Si
el sistema se cierra por error, al volver aparece lo que se estaba escribiendo. El
borrador se borra al **guardar** el viático, al **limpiar** el formulario y cuando
pasa el día (`borrar_borradores_viejos`). Los datos se guardan como **JSON**, así
que agregar un campo al formulario no exige cambiar la base.

## 9. Estimado de viaje (horas, km y comidas del camino)

Cuando el vendedor escribe la **salida de Miempresa** y la **salida del trabajo**,
el botón **⏱ Estimar viaje** escribe las dos horas que faltan (**llegada al
trabajo** y **llegada a Miempresa**). El aviso que aparece muestra el detalle del
cálculo y las horas quedan escritas en el formulario, **corregibles a mano**
(«las horas quedan escritas y se pueden corregir a mano», `_recalcular_horas`).

El cálculo está en cuatro funciones de `q_viaje.py`:

| Función | Qué resuelve |
| --- | --- |
| `_horas_del_destino()` | horas de camino **hasta ese cantón** |
| `_km_para_estimar()` | los km con los que se estima |
| `_velocidad_estimada(p)` | la velocidad del vehículo elegido |
| `_detalle_tramo(p, salida)` → `detalle_viaje()` | recorrido + comidas = horas totales |

### 9.1 Horas del destino (el dato manda)

`_horas_desde_cuenca(canton, provincia)` busca en este orden:

1. las horas **registradas** en la base para ese cantón (`db.horas_para`, columna
   `distancias.horas`, editable en **Parámetros → 🗺️ Provincias y km**);
2. la tabla semilla `database.HORAS_CUENCA` (alias `HORAS_APROX`), tomada del
   documento que revisó la empresa cantón por cantón y de **sus viáticos reales**
   (Guayaquil 3,5 h · Loja 5,5 · Quito 9,5 · Santo Domingo 9,5 · Machala 6 · Macas
   6,5 · Milagro 5,5 · Santa Isabel 2 · Piñas 6,5 …);
3. si no hay dato, devuelve **0** y el estimado cae al respaldo de km ÷ velocidad.

### 9.2 Km y velocidad

```text
_km_para_estimar()   = km del formulario
                       → db.km_para(cantón)          (Parámetros → Rutas)
                       → km del viático original     (solo en un ajuste)

_velocidad_estimada(p) = BUS          → p["velocidad_bus"]      (45 de fábrica)
                         CAMION / GRUA → p["velocidad_camion"]  (55 de fábrica)
                         resto         → p["velocidad_automovil"] (70 de fábrica)
```

Los km de respaldo vienen de la tabla semilla `q_viaje.KM_APROX` (Cuenca 15,
Girón 60, Azogues 30, Guayaquil 200, Manta 400, Quito 470, Tena 380…), que es la
misma información sembrada en `distancias`.

> **Detalle fino:** en un **ajuste** el campo Km vale 0 a propósito (los km ya se
> pagaron en el viático original), así que el estimado toma el km del **cantón** y,
> si tampoco hubiera, el del viático original. Antes se quedaba sin km y salía el
> aviso «Faltan los km del cantón o la velocidad del vehículo».

### 9.3 Recorrido: primero el dato, después la aritmética

`recorrido_de_viaje(km, velocidad, horas)` devuelve **horas enteras, siempre hacia
arriba**, porque así lo registra la empresa: de Cuenca a Guayaquil son 3 h 30 y
ellos anotan **4**; a Quito son 9 h 30 y quedan **10**.

```text
si horas_del_destino > 0 → max(1, ceil(horas))
si no                    → max(1, ceil(km / velocidad))
si no hay nada           → 0            (el estimado avisa y no inventa horas)
```

### 9.4 Las comidas del camino

La empresa suma **una hora por cada comida** cuya hora límite cae **dentro** del
viaje. Se configura en **Parámetros → Estimado de viaje**:

| Comida | Hora límite (parámetro) | Horas extra (parámetro) |
| --- | --- | --- |
| el desayuno | `hora_limite_desayuno` (06:00) | `horas_desayuno_viaje` (1) |
| el almuerzo | `hora_limite_almuerzo` (13:00) | `horas_almuerzo_viaje` (1) |
| la merienda | `hora_limite_merienda` (21:00) | `horas_merienda_viaje` (1) |

`comidas_del_viaje(p, salida, fin)` revisa **día por día** (el viaje puede cruzar
la medianoche): para cada comida mira si
`salida <= fecha_del_día + hora_límite <= fin` y, si cae dentro, suma sus horas
**una sola vez** y pasa a la siguiente comida. Si la comida no cae en el tramo, no
suma nada. Ejemplos de la empresa: el que sale a las 10:00 y llega a las 13:00
registra **14:00** (una hora por el almuerzo); el que vuelve a las 22:00 registra
**23:00** (la merienda); el viaje de madrugada (02:00 → 14:00) suma **dos** horas
(desayuno y almuerzo) y registra **16:00**.

### 9.5 El tramo completo

```text
detalle_viaje(km, velocidad, p, salida, horas)
    recorrido = recorrido_de_viaje(...)
    fin       = salida + recorrido
    comidas   = comidas_del_viaje(p, salida, fin)
    return recorrido + suma(horas de las comidas), recorrido, comidas
```

La **ida** se cuenta desde la salida de Miempresa y la **vuelta** desde la salida
del trabajo: así el que vuelve a las 18:00 con 4 h de camino registra las **23:00**
por la merienda y no las 22:00. `duracion_de_viaje()` es lo mismo sin el detalle y
`texto_estimado()` es el texto que se le muestra al usuario:

```text
Ida — salida de Miempresa: 24/09 18:00
   4 h de recorrido + 1 h por la merienda (21:00, en el camino) = 5 h
   llegada: 24/09 23:00
```

### 9.6 Ejemplo completo

Salida de Miempresa 24/09 18:00 hacia **Guayaquil**, automóvil, 200 km:

| Paso | Resultado |
| --- | --- |
| horas del destino (Guayaquil) | 3,5 h |
| recorrido = `ceil(3,5)` | **4 h** |
| fin del tramo | 24/09 22:00 |
| merienda (límite 21:00) ¿cae dentro? | sí → **+1 h** |
| desayuno (06:00) y almuerzo (13:00) | no caen → 0 |
| **total ida** | **5 h** |
| llegada al trabajo | 24/09 **23:00** |

Con un vehículo **BUS** el resultado es el mismo: «el bus hace el mismo viaje y
tarda lo mismo». El vehículo solo informa el medio (`_va_en_bus`) y sirve de
respaldo cuando el cantón no tiene horas registradas (km ÷ 45 en vez de ÷ 70).

## 10. Cálculo del viático (fórmulas del Excel)

Todo el viático de una persona lo produce **una sola** función:
`calculos.calcular(DatosViaje, parametros) -> dict`. No hay cálculos repartidos por
la interfaz: la pantalla, el PDF, el informe y la justificación **leen las mismas
columnas ya calculadas** guardadas en `viajes`.

`DatosViaje` (dataclass de `calculos.py`) trae las fechas y horas de esa persona
(salida, regreso, llegada al trabajo y salida del trabajo —estas dos últimas
opcionales—), `km_recorridos`, `parqueadero_peaje`, `otros`,
`combustible_efectivo` y `noches_desde` (solo lo usan los **ajustes**: el último día
ya entregado, desde el cual se cuentan las noches — §11.2).

### 10.1 Columna por columna

| Columna del Excel | Fórmula exacta (código) | Parámetro |
| --- | --- | --- |
| **Días de Viaje** | `max(fecha_regreso − fecha_salida + 1, 1)` | — |
| **Desayuno** | `valor × (días−1)` + `valor` si `hora_salida <= 06:00` | `valor_desayuno`, `hora_limite_desayuno` |
| **Almuerzo** | `valor × (días−1)` + `valor` si `hora_regreso >= 13:00` | `valor_almuerzo`, `hora_limite_almuerzo` |
| **Merienda** | `valor × (días−1)` + `valor` si `hora_regreso >= 21:00` | `valor_merienda`, `hora_limite_merienda` |
| **Taxi Salida** | `valor` si `hora_salida <= 06:00` | `valor_taxi_salida`, `hora_limite_taxi_salida` |
| **Taxi Regreso** | `valor` si `hora_regreso >= 21:00` | `valor_taxi_regreso`, `hora_limite_taxi_regreso` |
| **Hospedaje** | `valor_hospedaje × noches` (`noches = fecha_regreso − fecha_salida`, o desde `noches_desde` en un ajuste) | `valor_hospedaje`, `hospedaje_por_fechas` |
| **Agua** | `valor_agua × días` | `valor_agua` |
| **Combustible** | `combustible_efectivo` si es > 0; si no `km × valor_combustible_km` | `valor_combustible_km` |
| **Parqueadero/Peaje** | el valor escrito en el formulario | `valor_parqueadero_peaje` (sugerido) |
| **Otros** | el valor escrito en el formulario | — |
| **TOTAL** | suma de todo lo anterior, redondeada a 2 decimales | — |

Las **comidas** son el caso especial: `comida_dias()` paga los días completos
(`días − 1` comidas) y solo el día **extremo** depende de la hora. El **desayuno**
lo decide la **hora de salida** de Miempresa (se paga si sale a las 06:00 o antes)
y el **almuerzo** y la **merienda** la **hora de regreso** (13:00 y 21:00 o
después). Por eso el que sale a las 14:00 igual lleva el almuerzo de ese día, y el
que vuelve a las 22:00 lleva la merienda.

Ejemplo del Excel (salida 30/07 23:59 → regreso 31/07 10:00, **2 días**, $3 cada
comida): desayuno = 1×3 + 0 = **3** · almuerzo = 1×3 + 0 = **3** · merienda =
1×3 + 0 = **3**.

### 10.2 Noches y taxi: las dos reglas que se pueden cambiar

```text
noches_de_hospedaje(v, p):
    hospedaje_por_fechas = 1 → fecha_regreso − fecha_salida        (como el Excel)
    hospedaje_por_fechas = 0 → fecha_salida_trabajo − fecha_llegada_trabajo

taxi_salida   → valor si hora_salida <= 06:00            (en un ajuste: 0)
taxi_regreso  → valor si hora_regreso >= 21:00
                ó (taxi_regreso_madrugada = 1 y vuelve de madrugada)
vuelve de madrugada = hora_regreso <= 06:00  y  no salió ese mismo día
                      entre las 00:00 y las 06:00
```

`hospedaje_por_fechas` (1 de fábrica) es lo que hace el Excel: un viaje de 5 días
paga **4 noches**. Apagado, se cuentan las noches **reales** entre la llegada al
trabajo y la salida del trabajo. `taxi_regreso_madrugada` (0 de fábrica, o sea
«como el Excel») permite pagarle también el taxi al que **vuelve de madrugada**,
que el Excel no contempla.

> **Una hora límite que no se entiende no puede invertir la regla.** `hora_limite()`
> acepta una hora ya convertida, `"06:00"`, `"6:00"`, `"06:00:00"` (PostgreSQL y Excel)
> y números; si el parámetro falta o no se entiende usa `HORAS_DE_FABRICA` (06:00
> salida/desayuno, 13:00 almuerzo, 21:00 merienda y taxi de regreso) y **nunca**
> `00:00`, porque con una hora límite en cero el taxi de regreso se pagaría en **todos**
> los viáticos y el de salida en **ninguno**. `HORA_FIN_MADRUGADA` es fija (06:00): la
> hora límite del taxi de salida **no** decide qué es madrugada (si se cambia a las
> 09:00, el que vuelve a las 08:30 no es «madrugada»), y una ida y vuelta en la
> **misma** madrugada (04:00 → 05:30) paga **un solo** taxi, el de salida.

### 10.3 El redondeo del cajero: uno solo por viático

`redondear_cajero(total, múltiplo)` es el `CEILING` del Excel: **siempre hacia
arriba** al siguiente múltiplo (múltiplo 5 → 51 pasa a 55, 56 pasa a 60 y 55 se
queda en 55).

Ese redondeo se aplica **una sola vez, sobre el total de todo el viático**, porque
el dinero lo retira **una sola persona** (el encargado) y lleva el de todo el
grupo:

```text
cajero_del_grupo(filas, p)
    total = round(sum(total de cada fila), 2)
    valor = redondear_cajero(total, p["redondeo_cajero"])
    filas[0]["valor_cajero"] = valor     # el encargado
    filas[1:]["valor_cajero"] = 0        # los demás, en cero
```

El valor queda en la fila del **encargado** (la primera de la lista) para que la
columna CAJERO —y todo lo que la suma: vista previa, PDF, justificación,
historial— muestre **exactamente el dinero retirado**.

> **Por qué no se redondea por persona.** Antes se redondeaba la cuenta de cada
> viajero y luego se sumaba: en un viático de tres personas
> (183 + 116 + 116 = **415**) el redondeo por persona daba 185 + 120 + 120 = **425**,
> o sea **$10 más** de lo que en realidad se retiró, y la justificación mostraba un
> «entregado» que no era el entregado. El campo `valor_cajero` que devuelve
> `calcular()` para una fila suelta conserva el redondeo por persona **solo** para
> comparar con el formato viejo del Excel; el viático nunca lo usa así.

### 10.4 Parámetros y valores de fábrica

`database.PARAMS_INICIALES` (23 columnas, `PARAM_COLS`) crea la única fila de
`parametros` la primera vez:

| Parámetro | Fábrica | Parámetro | Fábrica |
| --- | --- | --- | --- |
| `hora_limite_desayuno` | `06:00` | `valor_hospedaje` | `15.00` |
| `valor_desayuno` | `3.00` | `valor_agua` | `1.00` |
| `hora_limite_almuerzo` | `13:00` | `valor_combustible_km` | `0.25` |
| `valor_almuerzo` | `3.00` | `valor_parqueadero_peaje` | `10.00` |
| `hora_limite_merienda` | `21:00` | `redondeo_cajero` | `5.00` |
| `valor_merienda` | `3.00` | `velocidad_automovil` | `70` |
| `hora_limite_taxi_salida` | `06:00` | `velocidad_camion` | `55` |
| `valor_taxi_salida` | `3.00` | `velocidad_bus` | `45` |
| `hora_limite_taxi_regreso` | `21:00` | `horas_desayuno/almuerzo/merienda_viaje` | `1` |
| `valor_taxi_regreso` | `3.00` | `hospedaje_por_fechas` | `1` |
| | | `taxi_regreso_madrugada` | `0` |

Los cambios que hizo la empresa en su Excel se aplican **una sola vez** al
arrancar, con una marca en `seq` (`ajustes_parametros`, `ajustes_parametros_excel`):
merienda hasta las 21:00, redondeo al múltiplo de 5, combustible a $0,25/km y
hospedaje por fechas. Después de eso **el superusuario manda desde Parámetros** y
el sistema ya no revierte nada.

### 10.5 Tolerancias del motor

- `_numero()` acepta texto en bases viejas (un `""` o `None` vale el valor por
  defecto) y `_activado()` lee los «sí/no» como `1`/`0`.
- `hora_limite()` acepta `"HH:MM"`, `"H:MM"`, `"HH:MM:SS"` (así las devuelve
  PostgreSQL), una hora ya convertida y números; si el parámetro falta o no se entiende
  usa la hora **de fábrica de ese parámetro** (`HORAS_DE_FABRICA`), nunca `00:00`.
  `database._hora_parametro()` hace lo mismo al leer la fila de `parametros`.
- Las tres **velocidades** y las tres **horas extra de comida** se usan **solo**
  para estimar las horas del camino (§9): no entran en ningún valor del viático.

## 11. Ajustes del viático

Un **ajuste** es «más viático para el mismo viaje»: el trabajo se alargó unos días, o
hay que entregar más efectivo para combustible, parqueadero/peaje u otros gastos del
encargado. El ajuste **no modifica el viático original** (ese dinero ya se entregó y
ya se firmó): agrega **filas nuevas** al mismo número.

| Concepto | Dónde queda |
| --- | --- |
| Filas del ajuste | tabla `viajes`, **mismo** `viatico_numero` |
| Cuál ajuste es | `ajuste_numero` = 1, 2, 3… (el original es `0`) |
| Tipo de fila | `tipo_registro` = `'AJUSTE'` (el original dice `'ORIGINAL'`) |
| Rótulos | en pantalla «VIÁTICO N° 120 / AJUSTE N° 1»; en el PDF «AJUSTE DE VIÁTICO N° 120-1» |

### 11.1 Cuándo se puede ajustar

`q_viaje.py → ajustar_seleccionado()` (botón de acción del historial):

```text
ajustar_seleccionado()
    n = viático seleccionado en la lista
    si el estado del original != 'PENDIENTE'  → aviso «Solo se pueden agregar
                                                 ajustes a viáticos PENDIENTES»
    _cargar_formulario(filas_originales, n, db.proximo_ajuste(n))
```

- Solo se ajustan viáticos **PENDIENTES** (igual que editar). Un viático ya
  justificado se **reactiva** primero (§12) y después se ajusta.
- `db.proximo_ajuste(n)` = `MAX(COALESCE(ajuste_numero,0)) + 1` de ese número: un
  ajuste nunca reutiliza el número de otro.

Al cargar el formulario en modo ajuste (`_cargar_formulario_datos`) todo viene del
**original**, con dos cuidados:

1. **Solo cambia el regreso.** `fecha_salida` / `hora_salida` quedan fijas en
   `(último regreso ya pagado + 1 día) 00:00` —el del original o el del **ajuste
   anterior**— y el campo de salida se **deshabilita**
   (`_bloquear_salida`: «en modo ajuste la salida queda deshabilitada, ya se entregó
   el original»). Así el ajuste cubre exactamente los días **nuevos**.
2. **Lo del original ya se entregó.** El efectivo de combustible, el parqueadero/peaje
   y los otros gastos **arrancan en cero** (`nuevo_ajuste`); el km del viaje original
   se recuerda aparte (`_km_orig_ajuste`) solo para **sugerir** el combustible (el
   lugar y la ruta no cambian).

En pantalla el encabezado pasa a `VIÁTICO N° … / AJUSTE N° …` y el botón dice
**💾 GUARDAR AJUSTE**.

### 11.2 Fórmula del ajuste (`_filas_ajuste` → `datos_ajuste` → `calcular`)

```text
fr_o   = último regreso YA PAGADO      # el del original o el del AJUSTE anterior
         (`db.ultimo_regreso_entregado`)
inicio = fr_o + 1 día                  # la salida del ajuste se pone sola, a las 00:00
ndias  = (fecha_regreso del ajuste − fr_o).days
si ndias < 1  → error: «El regreso del ajuste debe ser al menos 1 día después del
                        último día entregado (dd/mm/aaaa)»

Se arma un `DatosViaje` del período (`calculos.datos_ajuste`) y se calcula con las
MISMAS reglas del Excel que el original (§10.2), con `calcular(..., ajuste=True)`:

desayuno  = valor × (ndias − 1) + valor si hora_salida ≤ hora_limite → valor × ndias
almuerzo  = valor × (ndias − 1) + valor si hora_regreso ≥ hora_limite_almuerzo
merienda  = valor × (ndias − 1) + valor si hora_regreso ≥ hora_limite_merienda
hospedaje = valor_hospedaje × noches
            # noches = fecha_regreso − fr_o (NO desde `inicio`): el viático anterior
            # pagó las noches hasta la anterior a su regreso, así que la **noche del
            # último día entregado** se paga aquí. Con eso, el original más todos los
            # ajustes suman exactamente las noches que hubo entre la primera salida y
            # el último regreso (antes se perdía una noche por cada ajuste).
agua      = valor_agua × ndias
taxi_salida  = 0                        # ya se pagó en el viático original
taxi_regreso = valor si hora_regreso ≥ hora_limite_taxi_regreso
               (o si `taxi_regreso_madrugada` = 1 y vuelve de madrugada)
               y SOLO si esa persona todavía no lo tiene pagado en el original o en
               un ajuste anterior (`q_viaje.taxi_regreso_pagado`)
total     = round(desayuno + almuerzo + merienda + taxi_salida + taxi_regreso +
                  hospedaje + agua + combustible + peaje + otros, 2)
```

**El taxi de regreso se paga UNA sola vez en todo el viático.** Es «responsivo»: el
viajero vuelve a su casa **al final**, no una vez por cada ampliación. Por eso el ajuste
mira lo que ya quedó guardado (el original y los ajustes anteriores, empleado por
empleado):

| Situación | Dónde se paga |
| --- | --- |
| El original ya lo pagó (volvía a las 21:00 o después) | queda en el **original**; los ajustes muestran **$0** |
| El original **no** lo pagó (volvía antes) y el último ajuste cambia la hora de regreso a las 21:00 o después | se paga **en ese ajuste**, una sola vez |
| El ajuste anterior ya lo pagó | los ajustes siguientes muestran **$0** |
| Un empleado nuevo que no estaba antes | se le paga en el ajuste (si la hora corresponde) |

Antes se sumaba en **cada** bloque: en un viático de dos personas con dos ajustes la
columna **Taxi R.** del TOTAL GENERAL terminaba en **$18,00** cuando solo correspondía
**$6,00**. Debajo de la vista previa el sistema explica el $0: «Taxi de regreso $0: ya se
pagó en el viático original (se paga una sola vez, cuando vuelve de verdad)».

**Lo que cambió y por qué.** Antes el ajuste se calculaba a mano, **siempre desde el
regreso del original** y sumando `valor × ndias` por concepto, **sin taxis**. De ahí
salían los tres errores: del **segundo ajuste** en adelante la salida quedaba vieja y se
**volvían a pagar días ya entregados**, el **hospedaje se cobraba por día** (una noche
de más) y el **taxi de vuelta no se pagaba nunca**. Ahora el período arranca el día
siguiente al **último regreso entregado** (`db.ultimo_regreso_entregado`) y todo se
calcula con la misma fórmula del original; el **taxi de salida** queda en cero porque el
viajero ya salió en el original.

Después se encontró el error contrario, más fino: al empezar a contar las noches desde
`inicio` (el día siguiente al regreso), **la noche de ese último día no la pagaba
nadie** — el original paga las noches hasta la víspera de su regreso y el ajuste
arrancaba una noche después. En el viático 164/2026 (04/10 → 20/10 con dos ajustes) se
pagaban **14 noches de las 16** que el viajero durmió fuera. Desde la versión 9 el
hospedaje del ajuste se cuenta desde el **último regreso ya pagado** (`DatosViaje.
noches_desde`), así que el original y sus ajustes suman **todas** las noches del viaje
(lo comprueba `pruebas_reglas.py`, parte D).

Además del bloque de días, el ajuste acepta **tres montos extra**:

| Monto | A quién se le asigna |
| --- | --- |
| Efectivo para combustible (digitado, o botón **USAR** para tomar el sugerido del km original) | al **chofer** |
| Parq./Peaje | al **chofer** |
| Transp./Otros del encargado | al **encargado** |

Igual que en el original, si no hay chofer (o el chofer elegido no viaja en este
ajuste) el efectivo y el peaje **los lleva el encargado** (`lleva_gastos`): antes se
perdían en silencio. El **taxi de salida** y el transporte extra de los acompañantes
no se pagan en el ajuste: eso es propio del viático original (el **taxi de regreso**
sí se paga, según la hora de llegada).

El **cajero** se calcula **una sola vez** sobre el total del ajuste con
`cajero_del_grupo(filas, p)` (§10.3): el retiro lo hace uno solo y lleva el dinero de
todos, así que el redondeo no puede repetirse por persona.

### 11.3 Guardar, re-editar, borrar

`q_viaje.guardar()` decide el camino según el estado del formulario:

| Situación | Función de `database.py` | Qué hace |
| --- | --- | --- |
| Ajuste nuevo | `guardar_ajuste_viaje(n, cab, filas)` | `proximo_ajuste(n)` + `guardar_viaje(..., ajuste_numero=a)`; **inserta** las filas `'AJUSTE'` |
| Re-editar un ajuste | `actualizar_ajuste_viaje(n, a, cab, filas)` | **borra** las filas de **ese** ajuste y las reinserta; conserva `estado`, justificación y devolución del viático |
| Editar el original | `actualizar_viaje(n, cab, filas)` | borra y reinserta **solo** `ajuste_numero = 0` |
| Borrar un ajuste | `eliminar_ajuste(n, a)` | `DELETE` de las filas de ese ajuste |
| Anular todo el viático | `anular_viaje(n)` | pone `estado = 'ANULADO'` en **todas** las filas del número (original **y** ajustes) |

Ninguna de estas operaciones toca los otros grupos: el historial, la justificación y
los PDF siguen viendo cada ajuste por separado. El movimiento queda en la **bitácora**
(`CREÓ VIÁTICO`, `EDITÓ VIÁTICO`, `EDITÓ AJUSTE`, `ANULÓ VIÁTICO`) con el usuario, la
fecha y el detalle (§5).

### 11.4 Qué se ve en el historial y en los PDF

- `db.conteo_ajustes()` cuenta los ajustes de **todos** los viáticos en **una sola
  consulta** (`GROUP BY viatico_numero`). Antes se abría una conexión por viático dentro
  del bucle y por eso la lista tardaba en refrescarse contra la base central.
- `db.ajustes_viaje(n)` devuelve **un renglón por ajuste**: rango de fechas
  (`MIN(fecha_salida)` / `MAX(fecha_regreso)`), `recibo_ajuste`, orden de combustible,
  efectivo, `SUM(total)` y `SUM(valor_cajero)`.
- El combo **Ajuste** del historial lista los `ajuste_numero` existentes
  (`_ajuste_elegido()` pregunta cuál cuando hay más de uno, y avisa «Este viático no
  tiene ajustes» cuando no hay ninguno). Con él funcionan **Editar ajuste**,
  **Imprimir ajuste** y el **general**.
- `reportes.imprimir_viatico(n, cab, filas, general=True)` agrupa por `ajuste_numero` y
  saca **original + cada ajuste + total general**: las cifras nunca se mezclan.
- En la vista previa el ajuste aparece **después** del original, con sus propios totales.

### 11.5 La tabla `ajustes` (heredada)

`database.py` conserva `guardar_ajuste()` y `listar_ajustes()` sobre la tabla
`ajustes` (`viatico_numero`, `nombre_empleado`, `fecha`, `hora`, `concepto`,
`otros_gastos`). Son de la **versión anterior** del sistema, cuando «ajuste» quería
decir *cualquier* movimiento suelto de dinero. Hoy el ajuste real son filas de `viajes`
con `ajuste_numero`, y la justificación de gastos usa la tabla `gastos` (§12). La tabla
se mantiene únicamente para no romper bases antiguas.

## 12. Flujo: justificación

Justificar un viático es **rendir cuentas**: registrar las facturas en qué se gastó el
dinero entregado, adjuntar los respaldos, anotar si el empleado devuelve o si le queda
a favor, firmar y cerrar el viático. La ventana es `q_ajustes.py → AjustesWindow`
(«Justificación de viáticos»), de **dos columnas** para que todo entre sin bajar con la
barra de desplazamiento.

```text
┌─ 🔍 Buscar …  Estado: TODOS|PENDIENTE|JUSTIFICADO|ANULADO   📊 Excel: Lista | Justificación ─┐
├───────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ Viáticos registrados (tabla)  │ Digitar gasto / factura   (proveedor, RUC, concepto, valor)   │
│ Datos del viático             │ Detalle de gastos (igual al Excel de justificación + TOTAL)   │
│ Recibos, resumen y cierre     │ Facturas / archivos del viático                               │
│ ✅ JUSTIFICAR ↩ A pendiente   │                                                              │
│ 👁 Ver original 🖨 Imprimir   │                                                              │
└───────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

- **Refresco de fondo cada 15 s** (`QTimer`): si en otra computadora se registró un
  viático, aparece solo. No parpadea porque compara una **firma** de la lista
  (`_lista_firma` = n° + estado + empleados + total) y, si no cambió, no la redibuja; así
  no se pierde el viático que la persona tenía elegido.
- El buscador filtra por **número visible** (1, 2, 3…), por **número interno**, por
  empleados, lugares o el responsable; el combo de estado filtra por `PENDIENTE`,
  `JUSTIFICADO`, `ANULADO` o `TODOS`.
- La lista sale de `db.resumen_viaticos()`: **una fila por viático**
  (`GROUP BY viatico_numero`), con `MIN(fecha_salida)`, `MAX(fecha_regreso)`,
  `SUM(total)` y `SUM(valor_cajero)`; el estado es el de las filas (`MAX(estado)`).

### 12.1 Panel «Datos del viático»: lo entregado contra lo respaldado

Al elegir un viático, `_refrescar()` arma el resumen con dos números y su diferencia:

```text
Entregado   = Σ valor_cajero de TODAS las filas del número (original + ajustes)  ← §10.3
Respaldado  = db.totales_gastos(n)["total"]  = Σ total de la tabla gastos
Saldo       = Entregado − Respaldado
```

| Saldo | Significado | Qué sugiere el sistema |
| --- | --- | --- |
| > 0 | Sobró dinero | llena **«Devuelve a Miempresa $»** con el saldo |
| < 0 | Se gastó más de lo entregado | llena **«A favor del empleado $»** con `−saldo` |
| = 0 | Cuadra | deja las dos casillas en `0` |

La sugerencia solo se aplica si las dos casillas están en cero (nunca pisa un monto ya
guardado). En la misma tarjeta se muestran también: **recibos N° 1, 2 y 3**
(`recibo_viatico`), el **estado** y, en las filas, el personal que viajó, el **chofer**
(`es_chofer`), el **encargado** (`es_encargado`, el beneficiario), el vehículo
(`placa`), y los **ajustes** existentes («N° 1, N° 2» o «ninguno»).

### 12.2 Gastos y facturas

Cada línea de gasto es **una factura o comprobante** (tabla `gastos`), con los mismos
campos del Excel de justificación:

| Se digita | Se guarda en |
| --- | --- |
| Fecha | `fecha` |
| N° comprobante | `numero_comprobante` |
| Tipo: `FACTURA`, `NOTA VENTA`, `COMP. RETENCIÓN`, `OTRO` | `tipo` |
| RUC / Proveedor / Lugar | `ruc`, `proveedor`, `lugar` |
| Concepto (7 opciones) + «Valor de la factura $» | en **esa** columna de monto y en `total` |
| Explicación | `nota` |

Los **7 conceptos** y la columna donde cae el valor (`q_ajustes.CAMPO_CONCEPTO`):

```text
HOSPEDAJE → hospedaje     COMBUSTIBLE/ORDEN → combustible   BUSES → buses
TAXIS O CAMIONETAS → taxis   ALIMENTACIÓN → alimentacion    PEAJE → peaje
OTROS → otros
```

El valor **siempre cae en una sola columna**: `_datos_gasto()` pone en cero las otras
siete antes de escribir el concepto elegido y guarda `total = round(valor, 2)` — por eso
la fila TOTAL y la suma de las columnas coinciden con el Excel.

En la tabla se muestra además la columna **FACTURAS**: los archivos adjuntos asociados a
ese gasto (`respaldos.gasto_id`), y la última fila **TOTAL**
(`db.totales_gastos` → `COALESCE(SUM(...))` de cada columna).

- **Nuevo / Guardar / Eliminar.** Al tocar una fila se cargan sus datos y el botón cambia
  a **«💾 Guardar cambios»** (para que quede claro que modifica, no que crea). Guardar
  hace `db.guardar_gasto()` (INSERT con `RETURNING id`) o `db.actualizar_gasto()`;
  eliminar hace `db.eliminar_gasto()`, que además pone `gasto_id = NULL` en sus respaldos
  (las facturas **no** se borran: quedan sueltas en el viático y se ven en **👁 Abrir**).
- **Subir archivos.** `📎 Subir archivos…` acepta **varios** a la vez
  (`*.pdf *.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff`). Cada archivo pasa por
  `db.agregar_respaldo()`, que **convierte las imágenes a PDF** y lo guarda según la
  configuración (carpeta `data\respaldos\viatico_<clave>\` o dentro de la base con
  `contenido`, §13). El respaldo se ata al gasto que esté seleccionado (`gasto_id`).
- **👁 Abrir** usa `db.ruta_para_abrir()`: si el archivo está dentro de la base, escribe
  una copia temporal en `%TEMP%\viaticos_respaldos\` y la abre con `os.startfile`
  (Windows) o `xdg-open` (Linux).

Toda acción deja rastro en la **bitácora**: `REGISTRÓ GASTO`, `CAMBIÓ GASTO`,
`ELIMINÓ GASTO`, `SUBIO FACTURA(S)`, `QUITÓ FACTURA`, con el detalle (concepto, valor y
comprobante) y la referencia `N° 001/2026`.

### 12.3 Cerrar: JUSTIFICAR y volver a pendiente

**✅ JUSTIFICAR** (`_justificar`) hace el cierre completo, en este orden:

```text
1. si no hay gastos → pregunta «No hay gastos registrados. ¿Justificar de todos modos?»
2. guarda los recibos N° 1, 2 y 3                (db.actualizar_recibos)
3. guarda el cierre:                             (_guardar_cierre)
       devolución  → db.guardar_devolucion(n, monto, motivo)
       a favor     → db.guardar_pago_empleado(n, monto)
       nota        → db.guardar_nota_cierre(n, texto)
       firma       → db.guardar_elaborado_por(n, nombre)
4. db.justificar(n, usuario, nota)
       UPDATE viajes SET estado='JUSTIFICADO', justificado_por=usuario,
                         justificado_el=ahora(), nota_justificacion=nota
       WHERE viatico_numero = n          ← TODAS las filas (original + ajustes)
5. db.consolidar_respaldos_pdf(n)        ← une las facturas en un solo PDF (§13)
6. bitácora «JUSTIFICÓ VIÁTICO» + recarga la lista y limpia el panel
```

- El estado `JUSTIFICADO` se pone en **todo el número**, no fila por fila: un viático se
  justifica entero, con sus ajustes.
- `consolidar_respaldos_pdf` va dentro de `try/except`: si falla la unión del PDF, **la
  justificación ya quedó guardada** (es lo importante) y solo se pierde el archivo
  unificado.
- **«Elaborado por»** arranca con el nombre del usuario que inició sesión
  (`_elaborado_por_defecto`), no con un texto fijo.

**↩ A pendiente** (`_reactivar`) deshace el cierre:

```text
UPDATE viajes SET estado='PENDIENTE', justificado_por=NULL, justificado_el=NULL
WHERE viatico_numero=? AND estado='JUSTIFICADO'
```

Sirve para corregir algo después de justificar. **No borra nada**: los gastos, las
facturas y la devolución siguen ahí; el viático vuelve a aparecer como PENDIENTE (y
desde ahí se puede editar, ajustar o eliminar). Queda registrado como `REACTIVÓ VIÁTICO`.

### 12.4 Ver el original, imprimir y exportar

- **👁 Ver original** abre `VentanaOriginal` en **solo lectura**: los datos del viático
  original (creado por, proyecto, lugar, provincia/cantón, vehículo, órdenes de
  combustible, efectivo, km, parqueadero/peaje, recibos, salida, llegada al trabajo,
  salida del trabajo, llegada a Miempresa, observaciones, quién justificó y la nota de
  cierre) **más la tabla «Detalle calculado — original y ajustes»** con un bloque
  `═ ORIGINAL ═` y un `═ AJUSTE N° k · NUEVO ═` por cada ajuste, reutilizando las mismas
  columnas del estimado (`q_viaje.COLS_DETALLE`). Es la trazabilidad completa del dinero.
- **🖨 Imprimir** llama a `reportes.imprimir_justificacion(n, cab, filas, gastos,
  respaldos, devolucion)` con los recibos que están en pantalla (tienen prioridad sobre
  los guardados), el monto de devolución, la observación, el pago al empleado y la firma.
- **📊 Excel → Lista de viáticos** exporta **lo que se está viendo** (respeta el buscador
  y el filtro de estado) con `C.exportar_excel`.
- **📊 Excel → Justificación** exporta **lo mismo que se imprime** con
  `C.exportar_excel_documento`: título `JUSTIFICACIÓN DEL VIÁTICO N° 001/2026`, la
  cabecera (n°, estado, creado por, cliente/proyecto, lugar, salida→regreso, recibos,
  entregado, respaldado, saldo, devuelve, a favor, motivo, nota, elaborado por), el
  detalle de gastos y la fila TOTAL. El archivo se llama
  `justificacion_001-2026.xlsx` (ver §14.4).

## 13. Respaldos y PDF consolidado

Un **respaldo** es la factura o el comprobante escaneado/fotografiado que prueba un
gasto, guardado en la tabla `respaldos` (`id, viatico_numero, nombre_archivo, ruta,
empleado, concepto, gasto_id, creado_el` + la columna `contenido` con el PDF en sí).
Siempre es un **PDF**: si se adjunta una foto, el sistema la convierte.

### 13.1 Dos modos de guardado (`config.json → "respaldos"."modo"`)

| Modo | Dónde queda el archivo | Qué guarda la base | Cuándo conviene |
| --- | --- | --- | --- |
| `carpeta` (por defecto) | `data\respaldos\viatico_<clave>\` (o la carpeta que diga `"respaldos"."carpeta"`, puede ser compartida) | solo `ruta` y `nombre_archivo` | cuando las máquinas comparten una carpeta del servidor |
| `base` | dentro de la base, en la columna `contenido` (`BYTEA` en PostgreSQL / `BLOB` en SQLite) | el `contenido` del PDF (`ruta` queda en `NULL`) | cuando no hay carpeta compartida: **todas** las máquinas ven las facturas por la base central |

La carpeta de un viático se llama `viatico_<clave>` (`db._carpeta_viatico`), donde
`<clave>` es el número interno (por año, ver §7). Las funciones de lectura
(`db.ruta_para_abrir`, `db.contenido_respaldo`) y el respaldo de la base se comportan
igual en los dos modos, así que cambiar de modo no obliga a rehacer nada: el modo
`carpeta` guarda también `contenido = NULL` y el modo `base` `ruta = NULL`.

### 13.2 Conversión y compresión de las facturas (`db._a_pdf`)

Al adjuntar, cada archivo pasa por `_a_pdf(ruta_origen, carpeta)`:

```text
ext ∈ {.jpg .jpeg .png .webp .bmp .gif .tif .tiff}
    → abrir con Pillow, pasar a RGB
    → thumbnail((1600, 1600))            ← LADO_MAX: solo encoge, nunca agranda
    → guardar como PDF, resolution=100, quality=72   ← CALIDAD_JPEG
cualquier otro (ya es .pdf)
    → copiar tal cual
nombre   → _nombre_libre(): si ya existe, agrega _1, _2… (nunca pisa una factura)
```

Por qué: una foto de celular de 12 MP (varios MB) queda en **~250 KB** y la factura se
lee perfectamente en pantalla y al imprimir. Así ni la base ni la carpeta de respaldos
crecen de más con los años. Si el archivo es chico, `thumbnail` **no** lo altera.

`db.agregar_respaldo(numero, ruta_origen, empleado, concepto, gasto_id)` es la puerta de
entrada: convierte, guarda (carpeta o base) e inserta el registro. El `gasto_id` es lo
que ata la factura a **un renglón de la tabla `gastos`** (por eso la columna FACTURAS del
detalle de justificación puede decir cuáles van con cada gasto). El `concepto` se toma
del proveedor escrito o de `VIÁTICO` si todavía no hay gasto.

`db.eliminar_respaldo(id)` borra el registro **y** el archivo en disco (si está en
carpeta); si el archivo está dentro de la base, solo borra la fila.

### 13.3 El PDF consolidado (`db.consolidar_respaldos_pdf`)

Al **justificar** (§12.3) el sistema une todas las facturas del viático en **un solo
archivo** y borra los individuales: así en la carpeta (o en la base) queda **una factura
por viático** y no 10 PDF sueltos.

```text
nombre = VIATICO_<visible-año>_COMPLETO.pdf     p.ej. VIATICO_005-2026_COMPLETO.pdf
registros = listar_respaldos_completo(n)        (registrados + los que estén en la carpeta)
completo  = el que ya se llama *_COMPLETO.pdf   sueltos = los demás
si no hay sueltos  → se devuelve el completo que ya existe (nada que unir)

1. si ya había un COMPLETO, se usa como PRIMERA parte de la nueva unión
   (así, si se justifica de nuevo, no se pierde ninguna factura previa)
2. se unen en orden con PyPDF2 (PdfMerger; retrocede a PdfFileMerger en versiones viejas)
3. se escribe primero en un archivo temporal y solo se reemplaza si el PDF
   quedó con contenido (> 0 bytes). Si la unión falla → NO se borra nada:
   se conservan los respaldos individuales
4. se guarda según el modo:
      base    → se actualiza/inserta la fila con concepto 'PDF CONSOLIDADO' y contenido
      carpeta → se escribe VIATICO_..._COMPLETO.pdf (vía .tmp.pdf + os.replace)
                y se borran los archivos individuales
5. se borran los registros sueltos de `respaldos`
```

Detalles que evitan perder información:

- Solo se unen archivos que **terminan en `.pdf`**; lo que no sea PDF se salta (las
  imágenes ya se convirtieron antes, así que en la práctica todo es PDF).
- El registro del COMPLETO queda con `concepto = "PDF CONSOLIDADO"` y `gasto_id = NULL`
  (deja de pertenecer a un gasto puntual, porque ahora es el paquete de todos).
- Si al unir no queda nada que unir, **no** se toca lo que ya había.

### 13.4 Reconciliación automática (`database._reparar_rutas_respaldos`)

Cada vez que se abre la base, `inicializar()` llama —después de
`_migrar_numeracion_por_anio()`— a `_reparar_rutas_respaldos(conn)`: revisa la coherencia
entre la tabla `respaldos` y lo que hay en disco y **arregla solo**. En modo `base` sale
de inmediato (los PDF viven dentro de la base, no hay rutas que reparar):

| Situación | Qué hace |
| --- | --- |
| La carpeta de respaldos se movió y la `ruta` ya no existe | busca el archivo en `data\respaldos\viatico_<n>\<nombre>` y corrige la `ruta` |
| Hay un `VIATICO_n_COMPLETO.pdf` en disco sin registro | lo registra con concepto `PDF CONSOLIDADO` |
| Un registro apunta a un archivo que ya no existe y está dentro del COMPLETO | borra el registro roto (para que la lista no muestre entradas vacías) |
| El mismo archivo quedó registrado dos veces (típico al renumerar) | conserva el registro del número **más alto** y borra el otro |
| Quedó una carpeta con numeración antigua (`viatico_5`) pero sus archivos ya son del número por año (`2026005`) | renombra la carpeta y corrige las rutas |

Gracias a esto la ventana 📁 RESPALDOS nunca muestra «fantasmas» ni pierde facturas
después de una migración o de mover la carpeta compartida.

### 13.5 La ventana 📁 RESPALDOS (`q_respaldos.py`)

`RespaldosWindow` lista **todos** los archivos (de todos los viáticos) con
`db.listar_todos_respaldos()`:

| Columna | Contenido |
| --- | --- |
| N° VIÁTICO | `numero_visible` (1, 2, 3… dentro del año) |
| ARCHIVO | `nombre_archivo` |
| CONCEPTO | el concepto del respaldo, o **`PDF CONSOLIDADO`**, o **`EN CARPETA`** |
| SUBIDO POR | `empleado` (quien lo adjuntó) |
| FECHA | `creado_el` |

- **`EN CARPETA`** marca los archivos que **están en la carpeta pero no registrados** en
  la base (por ejemplo copiados a mano). `listar_todos_respaldos()` recorre
  `respaldos\viatico_*\` y agrega los que falten, así que igual se pueden abrir desde
  aquí. En modo `base` no hay carpeta que recorrer y solo se ven los registrados.
- La búsqueda filtra por número (interno o visible), nombre de archivo, concepto o
  persona; si lo escrito es solo dígitos, compara contra el N° de viático y busca dentro
  del nombre del archivo.
- **👁 Abrir seleccionado** (o doble clic) resuelve la ruta con `db.ruta_para_abrir()`
  —que materializa una copia temporal cuando el PDF viene de la base— y la abre.
- El pie muestra `«N archivo(s) · doble clic para abrir un archivo»`.

## 14. Reportes

Todo lo que el sistema muestra se puede **sacar del programa** de tres maneras: a **Excel
`.xlsx`**, a **CSV** (`;` + BOM, para Excel en español) o a **HTML para imprimir / guardar
como PDF**. Ninguna exportación vuelve a consultar la base por su cuenta: exporta **lo que
ya está en pantalla**, así el Excel dice exactamente lo mismo que el informe.

| Dónde | Botón | Qué saca | Función |
| --- | --- | --- | --- |
| Cualquier tabla | 📊 Excel · 📄 CSV | la lista tal como se ve (buscador, filtros, columnas) | `VentanaTabla.exportar_excel_segun` / `exportar_csv_segun` |
| Viáticos → Captura | 📊 EXCEL | el viático **en edición** (original o ajuste) | `ViajeWindow.exportar_excel_formulario` |
| Viáticos → Historial | 📊 Excel: Original · Ajuste · General | el viático elegido, solo, con un ajuste, o completo | `exportar_excel_original` / `_ajuste` / `_general` |
| Justificación | 📊 Excel → Lista de viáticos | la lista de viáticos que se está viendo | `AjustesWindow.exportar_excel_lista` |
| Justificación | 📊 Excel → Justificación | el documento de justificación del viático elegido | `AjustesWindow.exportar_excel_justificacion` |
| Bitácora | 📊 Exportar a Excel / 📄 CSV / 🖨 Imprimir | el informe de actividad | `BitacoraWindow._exportar_excel` / `_exportar_csv` / `_imprimir` |
| Viáticos, Justificación | 🖨 Imprimir / PDF | informe HTML (Ctrl+P → PDF) | `reportes.imprimir_viatico` / `imprimir_justificacion` |

### 14.1 Las funciones base (`qt_comunes.py`)

**`exportar_excel(ruta, columnas, filas, hoja="Datos")`** — tabla plana. Recorre las
`columnas` con `datos_columna(col)` (acepta tuplas `(clave, título, ancho)` o diccionarios)
y escribe el encabezado y luego cada fila, tomando el valor de la clave con
`_valor_para_archivo()` (`None` → celda vacía, `True/False` → `SI`/`NO`). El ancho de cada
columna sale del ancho declarado (`ancho / 7.0`, entre 12 y 50). Necesita **openpyxl**; si
falta, lanza un `RuntimeError` que la ventana muestra como error («Instale con: pip install
openpyxl»).

**`exportar_csv(ruta, columnas, filas)`** — el mismo esquema pero a texto: se abre con
`encoding="utf-8-sig"` (BOM incluido, para que Excel reconozca los acentos) y delimitador
**punto y coma** `;`, que es el que Excel en español interpreta como separador de columnas.

**`exportar_excel_documento(ruta, bloques, hoja="Documento")`** — exporta un *documento* con
formato, no una tabla suelta. `bloques` es una lista de:

| Bloque | Contenido |
| --- | --- |
| `("titulo", "TEXTO")` | una línea de título, unida a todo el ancho, fondo azul y letra blanca; deja una fila en blanco debajo |
| `("datos", [(etiqueta, valor), ...])` | pares rótulo/valor en una **cuadrícula de 3 parejas por fila** |
| `("tabla", columnas, filas)` | tabla con encabezado azul/blanco y celdas con borde |
| `("totales", columnas, fila)` | una fila resaltada en amarillo y en negrita (el TOTAL) |
| `("salto",)` | una fila en blanco |

Detalles de formato que hacen que la hoja se vea **llena y ordenada**:

- El ancho del documento lo manda **la tabla más ancha** (`ancho = max(len(columnas))`): el
  título y los rótulos se estiran hasta esa última columna, así el encabezado no queda como
  un bloque de dos columnas perdido a la izquierda (era el defecto anterior: se veía al 8 %
  del ancho del detalle).
- En los `datos`, cada rótulo queda en gris y en negrita y su valor ocupa las columnas
  siguientes; el **alto de la fila crece según el largo del texto** (28 / 44 / 60 puntos para
  más de 60 / 120 / 200 caracteres), porque hay valores largos (lista de personas,
  observaciones).
- Al escribir la tabla se fija `ws.freeze_panes` **debajo del encabezado**: al bajar en la
  hoja, los títulos de columna quedan siempre a la vista.
- Al final se ensanchan las tres columnas de rótulos según el texto más largo de cada ranura.

**Nombre de la hoja y del archivo.** Excel **no acepta** `\ / : * ? [ ]` en el nombre de
una hoja, y el «N° 001/2026» traía la barra (openpyxl rechazaba el archivo). Por eso
`_titulo_hoja(nombre)` borra esos caracteres y recorta a 31 letras. Para el archivo,
`pedir_ruta_guardar()` limpia con `nombre_archivo()`, que cambia `\ / : * ? " < > |` por
`-`: por eso lo que se propone es `justificacion_001-2026.xlsx` y la hoja queda
«Justificación 0012026».

### 14.2 El botón Excel/CSV de todas las tablas

`VentanaTabla` (la base de las listas del sistema) arma su barra de herramientas con
**📊 Excel** (`exportar_excel_segun`) y **📄 CSV** (`exportar_csv_segun`), que se apoyan en:

- `datos_exportables()` → `(self.columnas, self.visibles())`. `visibles()` devuelve
  `self._visibles`, que son **las filas que pasaron el buscador y los filtros** (el contador
  de la barra muestra «N de M»). Es decir: **se exporta lo que se está viendo**, no toda la
  tabla.
- `pedir_ruta_guardar(self, "%s.xlsx" % self.nombre)` pregunta dónde guardar (nombre
  sugerido = el título de la ventana) y al terminar informa la ruta y el número de filas.
- `exportar_excel_en(ruta)` / `exportar_csv_en(ruta)` son las mismas funciones **sin
  preguntar**, para los informes que ya tienen su ruta decidida.

### 14.3 El Excel de un viático (`q_viaje.py`)

Las cuatro exportaciones de viático pasan por un mismo armador,
**`_guardar_excel_viatico(numero, cab, filas, titulo, nombre)`**:

1. Si no hay filas, avisa y no hace nada.
2. Pide la ruta con `C.pedir_ruta_guardar(self, nombre)`.
3. Arma los bloques:

```python
bloques = [("titulo", titulo),
           ("datos", self._cabecera_viatico(numero, cab, filas, filas[0])),
           ("salto",),
           ("tabla", COLS_DETALLE, [vals_fila(i, f) for i, f in enumerate(filas, 1)]),
           ("totales", COLS_DETALLE, [vals_totales(filas)])]
```

4. Llama a `C.exportar_excel_documento(ruta, bloques, "Viático <n>")` —el nombre de la hoja
   sale de `db.numero_visible()`— y termina informando la ruta, el N° y cuántas **personas**
   (filas) tiene el viático.

La **cabecera** (`_cabecera_viatico`) lleva los mismos datos que el informe impreso: Viático
N°, Estado, Creado por, Cliente y proyecto, **Encargado** y **Chofer** (los deduce de las
filas: quien tenga `es_encargado` / `es_chofer`), Lugar de trabajo, Provincia / cantón,
Vehículo (placa), Orden combustible 1 y 2, Efectivo combustible, Km recorridos, Parqueadero /
peaje, Recibos (`recibo_viatico`, `_2`, `_3` juntos), Salida y Regreso a Miempresa, Llegada
al trabajo, Salida del trabajo, Observaciones, Justificado por y Nota de cierre. El detalle usa
las **25 columnas** de `COLS_DETALLE` (`vals_fila` numera las personas) y la última fila es
`vals_totales(filas)`.

Los cuatro botones del Historial y de la Captura:

| Botón | Filas que usa | Título | Archivo propuesto |
| --- | --- | --- | --- |
| `exportar_excel_original` | `db.filas_originales(n)` | `VIÁTICO N° <n> — ORIGINAL` | `viatico_<n>_original.xlsx` |
| `exportar_excel_ajuste` | `db.filas_numero(n, ajuste)` (el ajuste marcado, con `_ajuste_elegido`) | `VIÁTICO N° <n> — AJUSTE N° <k>` | `viatico_<n>_ajuste_<k>.xlsx` |
| `exportar_excel_general` | `db.filas_numero(n)` (original + todos los ajustes) | `VIÁTICO N° <n> — ORIGINAL Y AJUSTES` | `viatico_<n>.xlsx` |
| `exportar_excel_formulario` (Captura) | `self._construir_filas(avisar=True)`: **lo que está en pantalla** | `— ORIGINAL` o `— AJUSTE N° <k>` si se está editando un ajuste | `viatico_<n>.xlsx` / `viatico_<n>_ajuste_<k>.xlsx` |

> El número que va en el **título y en el nombre del archivo** es `db.numero_visible(n)`
> (1, 2, 3… dentro del año), no la etiqueta con año `001/2026`. La etiqueta con año se usa en
> los **informes HTML/PDF** (`reportes.py`, que arma el nombre con `db_etiqueta_archivo` →
> `viatico_001-2026`) y en la justificación. En ambos casos el nombre es válido en Windows.

### 14.4 La Justificación: lista de viáticos y documento

En la ventana de **Justificación** (`q_ajustes.py`) la barra superior tiene siempre a la vista
**📊 Excel:** con dos botones.

**`exportar_excel_lista()`** — «Lista de viáticos»: toma `self.tabla_v.datos`, es decir **las
filas que se están viendo** (respeta el buscador y el filtro de estado), y las vuelca con
`C.exportar_excel(ruta, COLS_V, filas, "Viáticos")`. Sirve para **entregar los viáticos que se
van justificando**: se filtra en pantalla (por ejemplo por estado o por responsable) y se
exporta exactamente eso. Archivo propuesto: `viaticos.xlsx`.

**`exportar_excel_justificacion()`** — «Justificación»: exporta **lo mismo que se imprime**. No
exporta la lista sino el documento del viático elegido:

- Título: `JUSTIFICACIÓN DEL VIÁTICO N° 001/2026`.
- Cabecera (15 pares rótulo/valor): **Viático N°** (`db.etiqueta_numero`), Estado, Creado por,
  Cliente y proyecto, Lugar de trabajo, Salida / regreso (`fecha_salida → fecha_regreso`),
  Recibos (`recibo_viatico` 1–3, «/» separados), **Entregado** = suma de `valor_cajero` de
  todas las filas del viático, **Respaldado** = `db.totales_gastos(n)["total"]`, **Saldo**
  (entregado − respaldado), **Devuelve a Miempresa**, **A favor del empleado**, Motivo, Nota de
  cierre y Elaborado por.
- Tabla `COLS_G` (los gastos justificados) **sin** la última fila, y luego el bloque
  `("totales", COLS_G, filas[-1:])` con la fila TOTAL.

  ```python
  bloques = [("titulo", "JUSTIFICACIÓN DEL VIÁTICO N° %s" % db.etiqueta_numero(self.numero)),
             ("datos", cabecera),
             ("salto",),
             ("tabla", COLS_G, filas[:-1]),      # los gastos, sin el TOTAL
             ("totales", COLS_G, filas[-1:])]    # la fila TOTAL

  ```

- Nombre propuesto: `justificacion_001/2026.xlsx`, que `nombre_archivo()` convierte en
  **`justificacion_001-2026.xlsx`**; la hoja queda «Justificación 0012026»
  (`_titulo_hoja`). Al terminar informa la ruta y cuántos **gastos** se exportaron
  (`len(filas) - 1`, sin contar el TOTAL).

### 14.5 El informe de actividad o bitácora (`q_bitacora.py`)

Esta pantalla **no** usa `C.exportar_excel`: arma su propio Excel porque el informe tiene dos
hojas y un formato propio. La barra ofrece **📊 Exportar a Excel**, **📄 Exportar CSV** y
**🖨 Imprimir / PDF**, y las tres empiezan igual: si no hay movimientos, avisan y no hacen nada.

`_exportar_excel()` guarda `informe_actividad_miempresa.xlsx` con:

- Hoja **«Actividad»**: fila 1 = `INFORME DE ACTIVIDAD — <filtros>`, fila 2 en blanco, fila 3 =
  encabezados (Fecha y hora, Usuario, Rol, Acción, Módulo, Referencia, Detalle) pintados en
  **blanco sobre azul `1F1CFF`**, luego un renglón por movimiento, una fila en blanco y
  `TOTAL DE MOVIMIENTOS` con el conteo. Los anchos de columna van fijos (20, 22, 16, 24, 16,
  16, 70).
- Hoja **«Resumen»**: `USUARIO / MOVIMIENTOS` y `ACCIÓN / MOVIMIENTOS` con los conteos que
  arma `_conteos(...)`.

`_exportar_csv()` escribe el mismo contenido a `informe_actividad_miempresa.csv` (UTF-8 con
BOM y `;`). `_imprimir()` llama a `reportes.imprimir_bitacora(self.filas, self._texto_filtro())`
para el informe HTML. En los tres casos la bitácora exporta **lo que está filtrado en pantalla**.

### 14.6 Los informes HTML/PDF (`reportes.py`)

Es el módulo de **impresión**. No guarda PDF: arma el **HTML** con el mismo formato en todas
las salidas y le pide al navegador que lo abra; de ahí se imprime o se hace
*Guardar como PDF* con `Ctrl+P` (el navegador propone como nombre el título del documento).

- **`_head(titulo)` + `_base_css()`** — encabezado HTML y hoja de estilos común, con los
  colores del tema (`tema.AZUL` / `tema.AMARILLO`, del módulo `colores`): título azul, `h2` con
  barra amarilla a la izquierda, tabla de borde fino, `tr.tot` con fondo amarillo y
  `tr.ajuste-title` para los separadores de ajuste. Las tablas llevan
  `page-break-inside: avoid` para que no se partan a la mitad al imprimir.
- **`_abrir(html, nombre="reporte")`** — escribe el HTML en
  `%TEMP%\<nombre>_<hash del contenido>.html` y lo abre con `webbrowser.open(...)`. El nombre
  es el que el navegador muestra al imprimir: por eso `imprimir_viatico` usa
  `viatico_001-2026` y `imprimir_justificacion` usa `justificacion_001-2026` (vía
  `db.db_etiqueta_archivo`, §14.3).
- **`fmt(v)`** deja `-` cuando el valor es cero (menos de medio centavo) y **`fmt_f(iso)`**
  cambia `aaaa-mm-dd` a `dd/mm/aaaa`; **`_num_txt(clave)`** devuelve `001/2026`.
- **`imprimir_viatico(numero, cab, filas, general=False)`** — informe del viático con las **25
  columnas** de `HEADERS_VIATICO` (N°, Empleado, Lugar, F./hora de salida, regreso, llegada y
  salida del trabajo, Días, Km, desayuno, almuerzo, merienda, taxi de salida y regreso,
  hospedaje, agua, combustible, transporte/otros, parqueadero/peaje, Total y Cajero) y una fila
  de totales. Con `general=True` **agrupa por `ajuste_numero`**: imprime el original, cada
  ajuste con su rótulo y un total general, sin mezclar las cifras (§11). Lo llaman el botón
  🖨 de la Captura y los tres botones **Original · Ajuste · General** del Historial.
- **`imprimir_justificacion(numero, cab, filas, gastos, respaldos, devolucion=None)`** — la
  hoja de justificación con el formato del Excel de la empresa: título y cabecera, tabla de
  gastos con las columnas de `HEADERS_JUSTIFICACION` (Fecha, N° comprobante, Tipo, RUC,
  Proveedor, Lugar, Hospedaje, Combustible/orden, Buses, Taxis o camionetas, Alimentación,
  Peaje, Otros, Total, Explicación), tabla de **notas** (comprobante, proveedor, explicación),
  el cuadro de firmas con **VALOR ENTREGADO / VALOR RESPALDADO / SALDO / DEVOLUCIÓN A
  MIEMPRESA / PAGO AL EMPLEADO (gastó más)** y la **OBSERVACIÓN**, y las líneas *Elaborado
  por* / *Revisado por*. Lo llama 🖨 Imprimir de la ventana de Justificación (§12).
- **`imprimir_bitacora(filas, filtros="")`** — el informe de actividad: cabecera con el filtro
  y el total de movimientos, la tabla de movimientos (con el rol traducido por
  `db.ETIQUETA_ROL`), el **resumen por usuario** y el **resumen por acción**, y las líneas de
  firma. Se pide desde 🖨 Imprimir / PDF de la bitácora.

## 15. Parámetros y catálogos

Pantalla: **`q_admin.py` (`AdminWindow`)**, «Parámetros y catálogos». Solo la ve el
superusuario y tiene **cinco pestañas**:

| Pestaña | Qué guarda | Tabla |
| --- | --- | --- |
| ⚙️ Parámetros | tarifas, horas límite y opciones del estimado | `parametros` (una sola fila) |
| 👥 Empleados | el personal que se elige al armar un viático | `empleados` |
| 🧑‍💼 Clientes | clientes / proyectos | `clientes` |
| 🚗 Vehículos | placa, tipo y chofer | `vehiculos` |
| 🗺️ Provincias y km | km y horas de viaje desde Cuenca, por cantón | `distancias`, `provincias`, `cantones` |

**Cada cambio se anota en la bitácora** con `_bitacora(accion, entidad, referencia, detalle)` →
`db.registrar_bitacora(self.usuario, ...)`: `CAMBIÓ PARÁMETROS`, `AGREGÓ/ELIMINÓ EMPLEADO`,
`AGREGÓ/ELIMINÓ CLIENTE`, `AGREGÓ VEHÍCULO`, `CAMBIÓ DISTANCIA`, `AGREGÓ CANTÓN`,
`IMPORTÓ EMPLEADOS / CLIENTES / TIEMPOS DE VIAJE` (con el nombre del Excel y cuántas filas se
leyeron y cuántas entraron). Nada se cambia «por fuera» de esa ventana.

### 15.1 Pestaña ⚙️ Parámetros

La lista de campos no está escrita dos veces: vive en la constante **`PARAMS_UI`** de
`q_admin.py`, con una tupla `(columna, etiqueta, tipo)` por cada una de las **23 columnas**
de `PARAM_COLS` (`database.py`). El tipo decide el control: `time` → campo de texto `HH:MM`,
`float` → campo numérico, `si_no` → lista desplegable **SÍ/NO** («para que no se escriban
valores raros»). Los dos últimos son justamente de sí/no:

| Columna | Etiqueta en pantalla | Tipo |
| --- | --- | --- |
| `hora_limite_desayuno` | Desayuno — hora límite de salida (HH:MM) | time |
| `valor_desayuno` | Desayuno — valor por día (USD) | float |
| `hora_limite_almuerzo` | Almuerzo — hora límite de regreso (HH:MM) | time |
| `valor_almuerzo` | Almuerzo — valor por día (USD) | float |
| `hora_limite_merienda` | Merienda — hora límite de regreso (HH:MM) | time |
| `valor_merienda` | Merienda — valor por día (USD) | float |
| `hora_limite_taxi_salida` | Taxi salida — hora límite (HH:MM) | time |
| `valor_taxi_salida` | Taxi salida — valor (USD) | float |
| `hora_limite_taxi_regreso` | Taxi regreso — hora límite (HH:MM) | time |
| `valor_taxi_regreso` | Taxi regreso — valor (USD) | float |
| `valor_hospedaje` | Hospedaje — valor por noche (USD) | float |
| `valor_agua` | Agua — valor por día (USD) | float |
| `valor_combustible_km` | Combustible — valor por km (USD) | float |
| `valor_parqueadero_peaje` | Parqueadero/Peaje — valor sugerido por viaje (USD) | float |
| `redondeo_cajero` | Redondeo cajero — múltiplo de (USD) | float |
| `velocidad_automovil` | Estimado de viaje — velocidad del automóvil (km/h) | float |
| `velocidad_camion` | Estimado de viaje — velocidad del camión/camioneta (km/h) | float |
| `velocidad_bus` | Estimado de viaje — velocidad del bus (km/h) | float |
| `horas_desayuno_viaje` | Estimado de viaje — horas extra por el desayuno en el camino | float |
| `horas_almuerzo_viaje` | Estimado de viaje — horas extra por el almuerzo en el camino | float |
| `horas_merienda_viaje` | Estimado de viaje — horas extra por la merienda en el camino | float |
| `hospedaje_por_fechas` | Hospedaje — contar las noches por las fechas del viaje (como el Excel) | si_no |
| `taxi_regreso_madrugada` | Taxi regreso — pagarlo también al que vuelve de madrugada (el Excel no lo paga) | si_no |

Los valores de fábrica (`PARAMS_INICIALES`) y qué significan están en §10.4 y §9.

**Guardar** (`_guardar`): recorre las entradas y convierte según el tipo —`HH:MM` con
`int(h)`/`int(m)`, `SÍ…`→`1.0` y `NO…`→`0.0`, el resto `float(...)`—; si algo no cuadra aborta
con «Revise los valores. Use HH:MM y números válidos.» y **no guarda nada**; si todo está bien
llama a **`db.guardar_parametros(parametros)`** y confirma «Parámetros guardados
correctamente.»

Del lado de los datos (`database.py`), los parámetros son los únicos que **no** se leen a cada
rato: `cargar_parametros()` los recuerda **30 s** en memoria (`_SEGUNDOS_MEMORIA`) y devuelve
una copia; `_leer_parametros()` lee la fila `id=1`, **rellena con `PARAMS_INICIALES`** las
columnas que falten (así una base vieja —sin las velocidades del estimado— funciona igual) y
convierte toda columna que empiece por `hora_` a `datetime.time`. `guardar_parametros(d)` hace
un solo `UPDATE parametros SET … WHERE id=1` con las 23 columnas y luego `olvidar_cache(...)`,
de modo que el cambio se ve al instante y no dentro de 30 s.

### 15.2 Empleados y clientes (y cómo se importa un Excel)

Las dos pestañas usan el **mismo widget**, `_PanelLista`: una lista (`QListWidget` con filas
alternas), un campo de texto que **convierte a mayúsculas** y tres botones —**Agregar**
(primario), **Eliminar** (rojo) e **📥 Importar Excel** (amarillo, solo si la pestaña lo pide)—.
Escribir y pulsar **Enter** agrega igual que el botón (`returnPressed`).

- **👥 Empleados** — `_ref_emp()` lista `db.listar_empleados()`; `_add_emp()` pasa el nombre a
  mayúsculas, lo guarda con `db.agregar_empleado(nombre)` y anota `AGREGÓ EMPLEADO`;
  `_del_emp()` pide confirmación («¿Eliminar a NOMBRE?», botón *Sí, eliminar*) y llama a
  `db.eliminar_empleado(nombre)` → `ELIMINÓ EMPLEADO`. Los nombres se guardan **en
  mayúsculas** y **sin duplicados** (`INSERT OR IGNORE` sobre `nombre`, que es `UNIQUE`).
- **🧑‍💼 Clientes** — igual, con `db.listar_clientes()`, `db.agregar_cliente()` y
  `db.eliminar_cliente()`. Ojo: el formulario de viáticos **solo acepta clientes que estén en
  esta lista** (lo comprueba `db.existe_cliente()`, §8), así que un cliente nuevo se agrega
  aquí primero.

Tras cada alta o baja se llama a `olvidar_cache("empleados")` / `olvidar_cache("clientes")`: los
catálogos se recuerdan **30 s** en memoria (`listar_*` → `_memoria(clave, _SEGUNDOS_MEMORIA,
_leer_*)`, que devuelve una **copia** para que nadie los modifique sin querer), y el borrado de
la caché hace que el cambio se vea de inmediato en el resto de la aplicación.

**📥 Importar Excel** (`_importar_empleados` / `_importar_clientes`) abre el diálogo de archivo
(`Excel (*.xlsx *.xlsm)`) y llama a `db.importar_empleados_excel(ruta)` /
`db.importar_clientes_excel(ruta)`, que devuelven **`(filas leídas, nuevos)`**; la pantalla
refresca la lista, anota en la bitácora el **nombre del archivo** y esas dos cifras, y muestra
el mismo resumen. Si el Excel está dañado o le falta `openpyxl`, se avisa con el error real
(«No se pudo leer el Excel: …») y no se toca nada.

Los dos importadores son iguales salvo las **palabras clave de la columna** y el largo mínimo:
empleados busca `NOMBRE, NOMBRES, EMPLEADO, PERSONAL, APELLIDO` y descarta textos de menos de
**4** caracteres; clientes busca `CLIENTE, RAZON SOCIAL, RAZÓN SOCIAL, NOMBRE` y descarta menos
de **3** (para no meter iniciales o números de fila). En ambos casos **no duplican**: los
nombres que ya están se dejan como están.

Quien lee el Excel es **`db._leer_excel_columna(ruta, palabras_clave)`**:

1. Abre el libro con **openpyxl** (`data_only=True, read_only=True`), solo la **primera hoja**
   y hasta **30 000** filas (por seguridad en hojas con filas vacías de sobra).
2. Busca la fila de encabezado entre las **primeras 60 filas**: gana la que tenga **más títulos
   que coincidan exactamente** con las palabras clave, y de ahí lee **esa misma columna** hacia
   abajo. La coincidencia tiene que ser **exacta** para no confundir el título «Lista de
   Clientes» con la columna «Cliente».
3. Si no hay encabezado exacto, usa la primera celda cuyo texto **contenga** la palabra clave;
   y si tampoco, la **primera columna con datos** (el comportamiento de una lista simple de una
   sola columna).
4. Descarta las filas cuyo texto sea uno de los `ENCABEZADOS_EXCEL` (`N°`, `NO`, `NUM`, `#`,
   `TEXTO`, `NOMBRE`, `CLIENTE`, `LISTA DE EMPLEADOS`…) para que los títulos no entren como
   datos.

### 15.3 Pestaña 🚗 Vehículos

Una lista con **`PLACA | TIPO | CHOFER`** y, debajo, una barra con el campo **Placa**, la lista
de tipos (`TIPOS_VEHICULO_UI`: CAMIONETA, CAMION, CAMION GRUA, AUTOMOVIL, MOTO, BUS, OTRO) y el
campo **Chofer** (ambos en mayúsculas), más **Agregar / actualizar** y **Eliminar**. Se guarda
con `db.agregar_vehiculo(placa, tipo, chofer)`, que es un **upsert por placa**
(`insert_actualizar`): por eso el botón dice «Agregar **/ actualizar**» — si la placa ya existe,
le cambia el tipo y el chofer en vez de duplicarla. El formulario de viáticos usa
`db.buscar_vehiculo_por_placa(placa)` para traer tipo y chofer al elegir la placa.

### 15.4 Pestaña 🗺️ Provincias y km

Es la pestaña que alimenta el **estimado de viaje** (§9): aquí se guardan, cantón por cantón,
los **km desde Cuenca** y —si se conocen— las **horas de viaje de ida**. Tiene dos tarjetas:

**«Actualizar kilómetros desde Cuenca»** — Provincia (lista `db.listar_provincias`), Cantón /
ciudad (lista de esa provincia), **Km aprox.** y **Horas de viaje (ida)** (se escriben como se
leen: `5:40`), con **💾 Guardar km y horas** y **📥 Importar Excel**. Al elegir un cantón, si ya
tiene datos registrados, `_km_ruta_seleccionado()` los trae (`db.km_para`, `db.horas_para`) y el
campo de horas se muestra con `calculos.horas_texto(horas, sufijo=False)`.

**Guardar** (`_guardar_ruta`) valida, en este orden: cantón obligatorio («Seleccione o escriba
el cantón/ciudad»), km numérico **≥ 0** («Ingrese un valor válido de kilómetros») y, si se
escribieron horas, que sean **mayores que 0** leyéndolas con `calculos.horas_de_texto` («Las
horas de viaje tienen que ser mayores que 0… escriba el tiempo como se lee (5:40) o en horas
(5.67)»). Si todo está bien:

1. `db.set_distancia(canton, km, horas)` — **upsert** por cantón (`INSERT … ON CONFLICT(canton)
   DO UPDATE`), donde las horas usan `COALESCE(excluded.horas, distancias.horas)`: guardar solo
   km **no** borra las horas que ya había.
2. `db.asegurar_canton(provincia, canton)` — si el cantón se escribió a mano y no estaba en el
   catálogo, **se agrega a la provincia** elegida (`asegurar_provincia` primero, si hiciera
   falta). Esto es lo que hace que un cantón nuevo (el caso real fue **YANTZAZA**) aparezca
   después en la lista desplegable del formulario de viáticos; antes se guardaban los km pero
   el formulario no conocía el cantón y había que escribirlo cada vez.
3. Anota en la bitácora `CAMBIÓ DISTANCIA` (con km y horas) y, si se agregó, `AGREGÓ CANTÓN`.
4. Refresca las listas y confirma con el detalle, avisando cuando el cantón se agregó al
   catálogo.

**📥 Importar Excel** (`_importar_distancias`) lee de una sola vez el Excel de tiempos de viaje
que va con el sistema —**«TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx»**, en la carpeta
`excel\` del programa** (columnas cantón, km y horas)— con `db.importar_distancias_excel(ruta)`;
devuelve `(filas leídas, cantones actualizados)`, hace **upsert** por cantón (km siempre; horas
solo si vienen) y borra las cachés `distancias` y `cantones:*`. La pantalla informa esas cifras
y recuerda que **los tiempos quedan en la base de datos, así que los ven todas las
computadoras** (importante: en modo central se importa una sola vez, no en cada PC).

**«Distancias registradas»** lista `db.listar_distancias()` con el texto
`cantón` + km + «5 h 40 min» (`horas_texto`; nunca «5.67»). Al hacer clic en una línea,
`_ruta_a_formulario()` la lleva al formulario: el cantón son los **primeros 35 caracteres** de
la línea y los km y horas se vuelven a leer de la base (por eso la lista puede mostrar las horas
«como se leen» sin perder el valor guardado).

Los km y las horas nunca se leen de la pantalla sino de **`database.km_para(canton)`** y
**`horas_para(canton)`**, que consultan `_rutas()`: un mapa con el **cantón en mayúsculas** →
`(km, horas)` y la lista para mostrar. `_rutas()` tolera una base antigua **sin** la columna
`horas` (la lee igual y devuelve `None`, y entonces el estimado usa su tabla aproximada, §9).

La ventana tiene además `actualizar()`, que vuelve a leer **todos** los catálogos (empleados,
clientes, vehículos y rutas) cuando el menú la abre: así se ven los cambios hechos desde otra
computadora.

## 16. Fuentes de datos

El sistema **no inventa** ningún dato: todo sale de algún lugar concreto y verificable. Hay
**tres fuentes** y conviene no confundirlas:

1. **Los Excel que viajan con el programa** (carpeta `excel\`): la lista de clientes y los
   tiempos de viaje que la empresa preparó. Se cargan **una sola vez**, cuando la base está
   vacía, y de ahí en adelante viven **dentro de la base de datos**.
2. **Las tablas semilla** escritas en `database.py`: personal, vehículos, provincias/cantones,
   los km y las horas desde Cuenca y los valores iniciales de Parámetros. Son el punto de
   partida de una instalación nueva.
3. **Lo que se escribe en el sistema**: Parámetros y catálogos (§15), el formulario de viáticos
   (§8), los ajustes (§11) y la justificación (§12). A partir de la primera puesta en marcha,
   **esto manda** sobre las fuentes 1 y 2.

### 16.1 La carpeta `excel\`

Va **dentro** de la entrega (junto al `.exe` o al código) y contiene los archivos de origen:

| Archivo | Para qué sirve |
|---|---|
| `DISTANCIAS DOC.docx` | El documento que la empresa revisó **cantón por cantón** (ruta, distancia real y dos tiempos: auto y autobús). Es el origen de los km y las horas de la versión 8.6. |
| `DISTANCIAS Y TIEMPOS DESDE CUENCA (DOC).xlsx` | El resultado de pasar ese Word al formato del sistema (`preparar_distancias_doc.py`), para revisarlo en Excel. |
| `distancias_cuenca_cantones_ecuador.xlsx` | Km por carretera y tiempo `h:min` por cantón (el otro insumo de los tiempos). |
| `LISTA DE CLIENTES MIEMPRESA.xlsx` | Lista de clientes de la empresa → carga inicial de la tabla `clientes`. |
| `LISTADO PERSONAL MIEMPRESA 21092026.xlsx` | Personal de la empresa → origen de `EMPLEADOS_SEMILLA`. |
| `TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx` | **El que carga el sistema**: cantón, km y horas de viaje (ida). |
| `TIEMPOS DE VIAJE MIEMPRESA.xlsx`, `TIEMPOS DE VIAJE PU (2).xlsx` | Versiones anteriores que quedaron en la carpeta. |

**`_archivo_de_recursos(parte_nombre)`** es quien encuentra estos archivos, y tiene dos
cuidados que responden a problemas reales:

- Busca en **dos carpetas** —la de recursos que va dentro del `.exe` (`cfg.carpeta_recursos()`)
  y la de al lado del programa (`cfg.carpeta_app()`, §17)— y dentro de cada una primero en
  `excel\` y después en la raíz. Así funciona igual corriendo desde el código, empaquetado, o
  si el superusuario deja los Excel junto al `.exe`.
- Si en la carpeta hay **varios** archivos que encajan, gana el de nombre preferido
  (`PREFERIDOS_RECURSOS`: «TIEMPOS DE VIAJE MIEMPRESA (NUEVO)» y «LISTA DE CLIENTES
  MIEMPRESA»). Antes ganaba el primero en orden alfabético y una copia que hubiera quedado de
  un guardado en Excel (`TIEMPOS DE VIAJE PU (2).xlsx`) le ganaba al archivo bueno: un servidor
  nuevo se llenaba con esos datos.

### 16.2 Las tablas semilla

Están escritas a mano en `database.py` y se siembran **solo si la tabla está vacía** (así una
base ya en uso nunca se pisa):

| Constante | Qué siembra |
|---|---|
| `EMPLEADOS_SEMILLA` | Los **32** nombres del personal, en mayúsculas y en el mismo orden del Excel de personal. |
| `VEHICULOS_SEMILLA` | Los **6** vehículos de partida como `(placa, tipo, chofer)` — por ejemplo `ABL-3969 / CAMION GRUA / EDISSON PÉREZ`. |
| `PROV_CANT` | Las provincias y sus cantones, que son las listas del formulario (provincia → cantón). |
| `KM_CUENCA` | Los km **desde Cuenca** por cantón (los del documento revisado, v8.6). Los seis cantones que el documento no trae (CHUMBLÍN, HUAMBI, CUENCA e ISABELA / SAN CRISTÓBAL / SANTA CRUZ) conservan los km de siempre. |
| `HORAS_CUENCA` | Las horas de viaje **solo ida** desde Cuenca (las del mismo documento). `HORAS_APROX` es el nombre anterior de esta tabla y sigue apuntando a ella. |
| `DISTANCIAS_NUEVAS` | `{"YANTZAZA": 215}`: el km de partida de los cantones que entraron al catálogo después, para que las bases ya creadas lo reciban solos. |
| `PARAMS_INICIALES` | Los **23** valores iniciales de Parámetros (§10.4, §15.1). |
| `TIPOS_VEHICULO` | Los tipos que ofrece la pantalla de vehículos: CAMIONETA, CAMION, CAMION GRUA, AUTOMOVIL, MOTO, BUS, OTRO. |

**Regla de oro:** una hora por cantón. El documento trae **dos** tiempos (auto y autobús) y el
sistema guarda **uno solo**; los km son siempre **desde Cuenca**, de ida, y el regreso se calcula
multiplicando (§10).

### 16.3 Carga inicial de los catálogos (una sola vez)

`_cargar_catalogos_iniciales(conn)` corre al final de `init_db()` y hace **dos** cargas
independientes. Cada una deja su **marca en la tabla `seq`**, y esa marca es la que evita que el
trabajo se repita en cada arranque o que se pise lo que después se editó a mano:

| Marca en `seq` | Se ejecuta si… | Qué hace |
|---|---|---|
| `catalogo_clientes` | no hay marca **y** la tabla `clientes` está vacía | Busca el Excel de clientes y carga los nombres con `_insertar_clientes(conn, _leer_excel_columna(...))` (los que ya están no se tocan). |
| `catalogo_tiempos` | no hay marca **y** ningún cantón tiene horas (`horas > 0`) | Busca el Excel de tiempos y carga km y horas con `_insertar_distancias(conn, _leer_excel_distancias(ruta))`. |

Todo va dentro de `try / except Exception: pass`: si el Excel no está, está dañado o falta
`openpyxl`, **el sistema arranca igual** (sin esos datos, no roto). Es la misma idea que en el
resto del arranque: la carga inicial es una **ayuda**, no un requisito.

Quien lee el Excel de tiempos es **`_leer_excel_distancias(ruta)`**, y también es tolerante a
propósito:

- Abre la **primera hoja** (openpyxl, `data_only`, `read_only`) hasta **30 000** filas.
- Busca la fila de encabezados en las **primeras 30**, y la da por buena **solo si en esa misma
  fila aparecen el cantón y los km**: cantón = una celda con `CANT…`, `CIUDAD` o `DESTINO`;
  km = una que empiece por `KM` o diga `DISTANCIA`; horas = una con `HORA` o `TIEMPO` (opcional).
  Así un título como «TIEMPOS DE VIAJE» antes de los encabezados no confunde nada.
- Si no encuentra encabezados, usa **las tres primeras columnas** (una lista simple).
- Descarta filas sin cantón, las que repiten títulos (`CANTÓN`, `CIUDAD`, `DESTINO`, `TOTAL`),
  y las que no traen **km > 0**. Las horas que vengan en `0` o mal quedan en **`None`**: el
  cantón se guarda con sus km y el sistema estima el tiempo con la velocidad del vehículo (§9).
- Los números se leen con `_a_numero()`, que acepta tanto números como texto escrito a la
  manera de la oficina (`"$1.250,50"`, `"3,5"`).

### 16.4 Ajustes de parámetros que se aplican una sola vez

Los valores iniciales de Parámetros se insertan con `PARAMS_INICIALES` **solo si la tabla está
vacía**. Aparte de eso hay **dos revisiones** que corrigen valores que quedaron de una versión
anterior, y cada una tiene su propia marca en `seq` para que **no** se repita:

| Marca | Qué deja igual al Excel de la empresa |
|---|---|
| `ajustes_parametros` | `redondeo_cajero` → **5** (antes 10), `hora_limite_merienda` → **21:00**, y las velocidades con las que se estima la llegada al trabajo: automóvil **70**, camión **55**, bus **45** km/h. |
| `ajustes_parametros_excel` | La merienda hasta las **21:00** (antes 20:00, y las meriendas de la vuelta de las 21:00 no se pagaban), el redondeo del cajero al múltiplo de **5**, el combustible a **$0,25** por km, el parqueadero/peaje de partida en **$10**, **hospedaje por las fechas del viaje** (`hospedaje_por_fechas = 1`, como el Excel) y **sin** taxi de regreso madrugada. |

Cada corrección se aplica con la pareja **«valor viejo → valor nuevo»** (`UPDATE … WHERE
columna = 10`) o, cuando el valor estaba en blanco, solo a los `NULL`. Gracias a las marcas,
**el superusuario manda**: si después cambia cualquiera de esos valores en Parámetros, el
siguiente arranque **no** lo revierte.

En la misma pasada se siembran el resto de datos de partida, siempre «si está vacío»: empleados
(`EMPLEADOS_SEMILLA`), vehículos (`VEHICULOS_SEMILLA`), provincias y cantones (`PROV_CANT`),
km de los cantones (`KM_CUENCA`), el contador de viáticos (`seq.viatico = 137`, §7) y los
usuarios del sistema (§5).

### 16.5 Las herramientas que arman los Excel (`herramientas\`)

Fuera del programa —se ejecutan a mano, con `python herramientas\<archivo>.py`, y **no** forman
parte del `.exe`— hay una carpeta de utilidades con las que se preparan y comprueban esos datos:

| Herramienta | Qué hace |
|---|---|
| `preparar_distancias_doc.py` | Pasa el Word `DISTANCIAS DOC.docx` al formato del sistema: lee sus tablas (una por provincia) y saca por fila el cantón, la cabecera, la ruta, los km y **dos** tiempos (auto y autobús), y deja **una sola hora** por cantón según `--horas` (por defecto el punto medio entre los dos). No toca el `.docx` ni la base. |
| `preparar_distancias_excel.py` | Pasa `distancias_cuenca_cantones_ecuador.xlsx` al formato del sistema, emparejando nombres de cantones (`CALVAS (CARIAMANGA)` → `CALVAS`, `SÍGSIG` → `SIGSIG`) y sumando el **margen** de `--margen` (1 h por defecto), porque los camiones y camionetas van con carga y no andan al ritmo de un auto. |
| `generar_excel_tiempos.py` | Arma el Excel que **viaja con el sistema** (`TIEMPOS DE VIAJE MIEMPRESA.xlsx`) a partir de la tabla `distancias` de la base local, para que la empresa lo revise y para que el sistema lo cargue de una sola vez. |
| `tiempos_de_viaje.py` | Llena las **horas** que falten usando OpenStreetMap **sin claves ni tarjeta**: Nominatim ubica el cantón (nombre + provincia) y OSRM da la duración en auto; redondea **hacia arriba a la hora entera** (regla de la empresa), **no toca los km** y deja un cuadro de control con los km de OSRM al lado de los registrados, para descubrir un cantón mal ubicado. |
| `ver_excel.py` | Muestra la estructura de un libro (hojas, columnas y filas), útil para revisar los archivos reales antes de cargarlos. |
| `comparar_excel_viaticos.py` | Carga los viáticos del Excel histórico de la empresa en una base local y compara, viático por viático, los gastos respaldados, los días y noches, y lo que paga el programa. |
| `comparar_reglas_excel.py` | Regla contra regla con el Excel nuevo (`VIATICO 2 2026.xlsx`): las tarifas y horas límite de la hoja «Parámetros» y luego el cálculo de cada viático contra las columnas calculadas del Excel. |
| `recalcular_cajero.py` | Actualiza el «valor a retirar en cajero» de viáticos viejos al criterio nuevo (desde la v7.0 se redondea **una sola vez** el total del viático y el valor queda en la fila del encargado; antes se redondeaba por viajero). |
| `viaticos_148_149.py` | Carga los viáticos reales 148 y 149 en la base local con las mismas reglas de la pantalla y comprueba que el programa pague igual que el Excel. |
| `limpiar_y_firmar.py` | Deja el proyecto firmado (cabecera y firma en cada archivo, `CREDITOS.md`, `version_info.txt` del `.exe`) y limpia `__pycache__`, `build` y temporales. |

Completan la carpeta `exceles_de_trabajo\` y `prueba_excel\` (copias de trabajo para las pruebas)
y los informes `distancias_doc_resultado.txt` / `tiempos_de_viaje.txt`, que son la salida de las
herramientas y quedan para revisar qué se cambió.

### 16.6 Migraciones y reparaciones automáticas

Cada arranque, `init_db()` ajusta una base que viene de una versión anterior. Nada se borra: se
**agrega** o se **corrige**.

| Función | Se ejecuta | Qué hace |
|---|---|---|
| `_migrar_usuarios(conn)` | **Todos** los arranques | Crea los usuarios que falten (`USUARIOS_SEMILLA`) **sin tocar** los que ya existen (así nadie pierde una clave cambiada a mano), retira los usuarios obsoletos y pone el **nombre completo** del personal donde todavía esté el corto. Además cifra, una sola vez, las claves que hubieran quedado **en texto** en bases anteriores. |
| `_migrar_numeracion_por_anio(conn)` | Una vez (queda registro en `renumeracion`) | Convierte la numeración antigua (1, 2, 3…) a la numeración por año (§7). Primero pasa los números a **negativos** para que no choquen con los nuevos, y guarda el cambio **viejo → nuevo** en la tabla `renumeracion` para poder reparar después los respaldos. |
| `_reparar_rutas_respaldos(conn)` | Todos los arranques (solo si los respaldos se guardan en carpeta) | Si un respaldo apunta a una ruta que ya no existe pero el archivo está en la carpeta actual de datos, **actualiza la ruta**; y a los respaldos que quedaron con un número viejo les pone el nuevo usando `renumeracion` (solo si ese número ya no existe en `viajes`). |
| `_reparar_catalogo_cantones(conn)` | Una vez (marca `catalogo_cantones_8_4`) | Mete en las bases **ya creadas** los cantones que se agregaron al catálogo después: los de `PROV_CANT` y los km de `DISTANCIAS_NUEVAS` (YANTZAZA: 215 km y 5 h). **No pisa** lo que la base ya tenga: si el cantón existe con sus km y sus horas puestos a mano, se respetan. |
| `nuevas_columnas` / `information_schema` | Todos los arranques | Agrega por `ALTER TABLE` las columnas que no existían en bases antiguas (SQLite: intento y listo; PostgreSQL: se consulta primero para no abortar la transacción, §18). |

Todo esto es la razón por la que **actualizar el sistema no exige migrar a mano**: se copia la
carpeta nueva, se abre el programa y la base queda al día sola.

## 17. Configuración y conexión

De todo el sistema, **lo único que se configura a mano** es la conexión: dónde vive la base y
dónde se guardan los archivos de respaldo. Todo lo demás (tarifas, parámetros, catálogos) vive
en la base o viaja dentro del programa (§16).

La decisión de fondo está escrita en `configuracion.py`: el sistema trabaja con **una sola base
central** (PostgreSQL en el servidor) a la que se conectan todas las computadoras, y la
configuración por defecto **ya apunta al servidor**; por eso en las demás máquinas *basta con
copiar el `.exe`*, sin ningún archivo extra.

### 17.1 `config.json`: qué manda y en qué orden

`configuracion.leer()` arma la configuración de varias fuentes y **la que va después pisa a la
anterior**:

```
DEFECTO (lo que trae el programa)  →  config.json  →  variables de entorno
```

| Fuente | Dónde está | Para qué |
| --- | --- | --- |
| Defecto | `DEFECTO`, dentro del código | El sistema recién copiado ya funciona contra el servidor sin tocar nada |
| Archivo | `ruta_config()` = `carpeta_app()\config.json` (se puede forzar con `VIATICOS_CONFIG`) | Lo que el usuario cambia desde la pantalla de conexión |
| Perfil de Windows | `%APPDATA%\Miempresa\config.json` (`ruta_config_usuario()`) | Se usa **solo** si la carpeta del programa no se puede escribir (Program Files, carpeta de red de solo lectura) |
| Variables de entorno | las de la tabla de abajo | Pruebas y arranques de una sola vez |

Valores de fábrica (`DEFECTO`): motor `postgres`, `host` `192.168.22.4` (`SERVIDOR`), `puerto`
`2345`, base `viaticos`, usuario `miempresa`, clave `miempresa` (`CLAVE_SERVIDOR`),
`respaldos.modo` `base` y `interfaz.zoom` `0`.

El archivo que va **junto al programa** puede cambiar todo eso: el `config.json` de esta carpeta
de trabajo, por ejemplo, está puesto en `"motor": "sqlite"` para poder probar sin servidor
encendido.

Opciones que entiende el archivo:

| Clave | Valores | Qué hace |
| --- | --- | --- |
| `motor` | `sqlite` / `postgres` | `motor()` acepta además `postgresql`, `pg` y `central` como sinónimos de PostgreSQL |
| `postgres.host` · `puerto` · `base` · `usuario` · `clave` | — | Datos de la base central |
| `respaldos.modo` | `base` / `carpeta` | `base` = los archivos van **dentro** de la base (todas las PC los ven); `carpeta` = en la base solo queda la ruta. `modo_respaldos()` acepta `bd`/`db` como sinónimos de `base` |
| `respaldos.carpeta` | ruta local o de red, como `\\SERVIDOR\viaticos_respaldos` | `carpeta_respaldos()` la crea si no existe; si está vacía usa `data\respaldos` |
| `sede` | texto | Sede con la que arranca esta computadora |
| `interfaz.zoom` | `0` (automático) · `1.0` · `0.9` · `0.8` · `0.7` · `0.6` | Tamaño de la letra y los controles (§17.4) |
| `interfaz.dpi_consciente` | `true` / `false` | En `false` desactiva el aviso de escalado a Windows (§22) |

**`leer()` lee el disco una sola vez** y deja la configuración en memoria (`_CACHE`), devolviendo
copias (`deepcopy`) para que nadie pueda modificar la copia guardada; `olvidar_cache()` la
descarta (y también olvida la carpeta de datos, §17.2). Está así porque `leer()` se llama **en
cada consulta** a la base y en cada tecleo del formulario: leer el archivo cada vez se sentía
(§20).

**`guardar(datos)` no borra lo que ya había**: mezcla `DEFECTO` + el archivo actual + lo nuevo
(`_mezclar`, que ignora los valores `None` y entra en los diccionarios anidados) y escribe con
`indent=2` y acentos legibles (`ensure_ascii=False`). Si la carpeta del programa no se puede
escribir, cae sola al perfil de Windows, así que la configuración **no se pierde**; al final
llama a `olvidar_cache()` para que lo guardado se use de inmediato.

**Variables de entorno** (útiles para pruebas y para el empaquetado):

| Variable | Efecto |
| --- | --- |
| `VIATICOS_MOTOR` | `sqlite` / `postgres` |
| `VIATICOS_PG_HOST` · `VIATICOS_PG_PUERTO` · `VIATICOS_PG_BASE` · `VIATICOS_PG_USUARIO` · `VIATICOS_PG_CLAVE` | Datos del servidor sin editar el archivo |
| `VIATICOS_RESPALDOS` · `VIATICOS_RESPALDOS_DIR` | Modo y carpeta de respaldos |
| `VIATICOS_CONFIG` | Ruta del `config.json` que se va a usar |
| `VIATICOS_DATA` | Carpeta de datos locales (§17.2) |
| `VIATICOS_SIN_RESERVA` | Desactiva la conexión reutilizada; sirve **solo** para medir (§17.3, §20) |
| `VIATICOS_SELFTEST` | Autodiagnóstico del `.exe` (§4, §21) |

`describir()` resume todo lo anterior en una línea, que es la que se ve en la pantalla de
conexión y queda en la bitácora:

```
Base CENTRAL PostgreSQL: miempresa@192.168.22.4:2345/viaticos · respaldos dentro de la base
Base LOCAL (SQLite): …\sistema_viaticos_miempresa\data\viaticos.db
```

### 17.2 Las carpetas: programa, recursos y datos

`configuracion.py` es el único lugar que decide **dónde está cada cosa**, y lo hace distinguiendo
si el sistema corre **desde el código** (`python main_qt.py`) o **empaquetado**
(`dist\Sistema_Viaticos.exe`, donde `sys.frozen` es verdadero):

| Función | Desde el código | Como `.exe` | Para qué se usa |
| --- | --- | --- | --- |
| `carpeta_app()` | la carpeta de `configuracion.py` (`sistema_viaticos_miempresa\`) | la carpeta del ejecutable (`dist\`) | `config.json`, trabajar con rutas relativas |
| `carpeta_recursos()` | igual que `carpeta_app()` | `sys._MEIPASS` (la carpeta temporal donde PyInstaller descomprime el `.exe` de un solo archivo) | leer `excel\` con las semillas de los catálogos (§16.3) |
| `dir_datos()` | 1) `VIATICOS_DATA` · 2) el texto de `data_path.txt`, que se busca **en la carpeta de arriba** (`carpeta_app().parent`) · 3) `carpeta_app()\data` | lo mismo, partiendo de `dist\` | `viaticos.db` y, si `respaldos.modo = carpeta`, la carpeta `data\respaldos\` |

`dir_datos()` crea la carpeta si hace falta y —igual que `leer()`— **se resuelve una sola vez y
queda en memoria** (`_CARPETA_DATOS`): antes se buscaba `data_path.txt` y se creaba la carpeta en
*cada* consulta a la base, que es algo que ocurre muchas veces por segundo (§20). Los dos se
olvidan con `olvidar_cache()`.

De ahí sale la trampa conocida de la carpeta `dist\` (la avisa la pantalla de migración, §18): el
`.exe` suelto trabaja con **su propia** base en `dist\data\`, que está vacía, y no con la base
buena de `sistema_viaticos_miempresa\data\`.

### 17.3 `bd.py`: dos motores, un solo lenguaje

`database.py` (y con él toda la aplicación) **no sabe** si está hablando con SQLite o con
PostgreSQL: siempre llama a las mismas funciones. Quien traduce es `bd.py`, y por eso el código
antiguo no tuvo que cambiar cuando apareció el servidor.

**La conexión se presta, no se recrea.** `conectar()` guarda la conexión abierta en una reserva
(`_RESERVA`, con clave `(base, hilo)`) y la **presta** a cada consulta; al terminar, la consulta
la devuelve. Antes, cada consulta abría y cerraba la suya, y contra el servidor eso significa
negociar de nuevo red + usuario + clave **en cada consulta** —con la pantalla consultando por
tecleo (parámetros, km del cantón, listas de empleados y clientes)—, que es la causa de la pausa
«se queda pensando».

| Pieza | Qué hace |
| --- | --- |
| `conectar()` | Toma una conexión libre de la reserva o abre una nueva. Da igual escribir `conn = conectar()` que `with conectar() as conn:` |
| `conectar(directa=True)` | Abre una conexión **aparte**, que no se guarda: sirve para **probar otra dirección** sin tocar la que está en uso |
| `_clave_base()` | Identifica la base (motor + host/puerto/base/usuario, o la ruta del `.db`): si cambia la conexión, se abre otra |
| `_QUIETA_SEGUNDOS = 20` | Si la conexión llevaba ese tiempo sin usarse, se prueba con un `SELECT 1` **antes** de prestarla: los cortafuegos y el propio servidor cortan las conexiones quietas, y es mejor enterarse ahí que fallar al guardar |
| `_CANDADO` (`RLock`) | Evita que dos hilos tomen la misma conexión a la vez |
| `cerrar_reserva()` ← `db.cerrar_conexiones()` | Cierra todo lo guardado: al **cambiar de servidor** y al **salir** del sistema (§4) |
| `estadisticas()` / `reiniciar_estadisticas()` | Cuenta aperturas, reusos, consultas y segundos de espera (§20) |
| `VIATICOS_SIN_RESERVA=1` | Apaga la reutilización para **medir** cómo era antes (§20) |

**Traducción del dialecto.** `_a_postgres(sql)` reescribe al vuelo el SQL que se escribió para
SQLite, y eso es lo que permite tener un solo `database.py`:

| Escrito para SQLite | Se convierte en PostgreSQL |
| --- | --- |
| `?` (marcas de parámetro) | `%s` |
| `%` dentro del SQL (por ejemplo en `LIKE '%algo%'`) | `%%` — se hace **antes** de cambiar los `?`, para no estropear los `%s` recién creados |
| `INSERT OR IGNORE INTO` / `INSERT OR REPLACE INTO` | `INSERT INTO … ON CONFLICT DO NOTHING` |
| `datetime('now','localtime')` | `to_char(now(), 'YYYY-MM-DD HH24:MI:SS')` |
| `GROUP_CONCAT(x)` / `GROUP_CONCAT(DISTINCT x)` | `STRING_AGG(x, ',')` / `STRING_AGG(DISTINCT x, ',')` |
| `date(x)` | `substr(x, 1, 10)` |

Para no depender de esa traducción al escribir código nuevo hay dos ayudantes,
`bd.insert_ignorar(tabla, columnas, conflicto)` y `bd.insert_actualizar(tabla, columnas, clave)`,
que arman el `ON CONFLICT` correcto en los dos motores, y tres atajos para lo que más se escribe:
`bd.ahora()`, `bd.agrupar()` y `bd.fecha_dia()`.

**Lo que devuelven las consultas se comporta igual:** las filas son diccionarios
(`fila["columna"]`) tanto con `sqlite3.Row` como con `RealDictCursor`, y `Cursor` es un resultado
**ya materializado** con `fetchone()`, `fetchall()`, `rowcount` y `lastrowid` (en PostgreSQL el
`lastrowid` se detecta cuando la consulta termina en `RETURNING id`).

**Cómo se abre cada motor:**

- **SQLite (local):** `sqlite3.connect(data\viaticos.db, timeout=30)` con `row_factory =
  sqlite3.Row` y `PRAGMA foreign_keys = ON`. No hay usuario, ni clave, ni red: el archivo es la base.
- **PostgreSQL (central):** `psycopg2.connect(...)` con `RealDictCursor` y, a propósito,
  `connect_timeout=6` (si el servidor está apagado o dormido se avisa **en 6 segundos** en vez de
  quedarse colgado; la pantalla de conexión aparece enseguida), `keepalives` (30 s de reposo,
  sondeo cada 10 s, 5 intentos) porque la conexión queda abierta mientras se usa el sistema,
  `application_name = "Sistema Viaticos Miempresa"` (así se ve quién está conectado en el
  servidor) y `options = "-c statement_timeout=60000 -c lock_timeout=30000"` (una consulta o un
  bloqueo no se quedan esperando para siempre). Si falta el conector, el mensaje lo dice tal cual:
  *«Falta el conector de PostgreSQL (psycopg2)…»*.
- **Probar una conexión** (`probar_conexion(datos)`): guarda los datos indicados, abre una conexión
  **directa** (la de trabajo no se toca), pregunta la versión (`SELECT version()` o
  `sqlite_version()`) y **restaura** la configuración anterior; devuelve `(ok, mensaje)` con la
  versión al frente, que es lo que muestran los botones «Probar conexión» de la pantalla.

### 17.4 La pantalla de conexión (`q_conexion.py`, solo superusuario)

`ConexionWindow` («Conexión y base de datos — Superusuario», 1020×800) es el equivalente a editar
`config.json` a mano, pero con comprobaciones. Al abrirse **rechaza a quien no sea superusuario**
(«Solo el superusuario puede cambiar la conexión.»), coherente con `PERMISOS_MODULO` (§5).

Está hecha por tarjetas, de arriba abajo:

| Tarjeta | Qué muestra / permite |
| --- | --- |
| **Conexión en uso** | `cfg.describir()` (la línea de §17.1), los datos de la base **local** (`migracion.resumen_local()`) y los de la **central** (`viáticos · empleados · clientes · movimientos de bitácora`). Es el tablero para saber dónde están los datos |
| **Tipo de base** | `Base LOCAL (cada máquina con su archivo SQLite)` o `Base CENTRAL en el servidor (PostgreSQL)` |
| **Datos del servidor (PostgreSQL)** | Host/IP, puerto, base, usuario y clave (el campo de la clave va oculto) |
| **Archivos de respaldo (facturas)** | `base` (dentro de la base central: todas las máquinas ven los archivos —lo recomendado—) o `carpeta` (local o de red), con «Elegir…» (`QFileDialog`, que además marca el modo «carpeta») |
| **Numeración de viáticos (reinicia cada año)** | El resumen por año (`2026: 137 viático(s), el próximo es el N° 138`) y «💾 Fijar numeración» (§7) |
| **Tamaño de la pantalla en esta computadora** | «Automático» / 100 % / 90 % / 80 % / 70 % / 60 %, con la que está en uso |
| **Para dejar el servidor en marcha** | `AYUDA_SERVIDOR`: los 4 pasos, remitiendo a `documentacion\SERVIDOR_POSTGRES.md` |

Los botones de la barra son **💾 Guardar**, **🔌 Probar conexión** (`db.probar_conexion`, que
devuelve la versión del motor), **⬆ Subir mis datos locales a la central** (§18) y
**🔄 Actualizar información** (vuelve a leer todo y repinta la pantalla).

**Al guardar** (`_guardar`) pasa, en este orden: se arma el diccionario nuevo (`motor`, `postgres`,
`respaldos` e `interfaz.zoom`; el puerto tiene que ser número), `cfg.guardar(...)` (si la carpeta
no se puede escribir avisa del `OSError`), `db.cerrar_conexiones()` —porque **la conexión en uso
era de la dirección anterior**—, se anota en la bitácora **«CAMBIÓ CONEXIÓN»** con
`cfg.describir()`, y se repinta. Si el zoom quedó distinto al que estaba en uso, ofrece reiniciar.

**El tamaño de pantalla es de cada computadora.** Se guarda en el `config.json` de esa PC (no viaja
a la base) y `_cargar_zoom()` marca el botón más cercano al valor guardado, aunque se haya escrito
a mano (por ejemplo `0.75`). Como el tema ya está aplicado, el cambio se ve al reabrir:
`reiniciar_sistema()` lanza de nuevo el programa —`sys.executable` (más la ruta del `.py` cuando no
está empaquetado) con `cwd = carpeta_app()`— y cierra la aplicación actual; si no se puede, el
aviso pide cerrar el sistema a mano.

**Fijar la numeración** (`_fijar_numeracion`) valida año (2000–2100) y número (≥ 1), confirma,
llama a `db.fijar_inicio(numero, anio)` (§7), lo deja en la bitácora («FIJÓ NUMERACIÓN DE
VIÁTICOS») y avisa si el número pedido queda **ocupado** —es decir, si en ese año ya existen
viáticos con números posteriores, el sistema usa el siguiente libre (`db.numero_visible`).

### 17.5 Abrir el sistema cuando el servidor no responde

Esto es lo que hace que nadie tenga que saber de redes para entrar (paso 1 del arranque, §4).
`asegurar_conexion(app)` está escrito como un **ciclo**:

```
mientras no se pueda entrar:
    db.init_db()  →  si funciona, se entra al sistema
    si falla      →  VentanaServidor(mensaje)   ¿qué hacer?
                     ├─ escribir otra dirección → la prueba, la guarda y vuelve a intentar
                     ├─ «💻 Trabajar en esta PC (base local)» → guarda motor sqlite y sigue
                     └─ «✖ Salir» → no se abre el sistema
```

`VentanaServidor` («No se pudo abrir la base de datos», 900×640) muestra el **error real** del
motor —hasta 900 caracteres—, no un «contacte al administrador». Trae los campos del servidor
precargados con lo que dice `config.json`, y sus botones son:

| Botón | Qué hace | `self.accion` |
| --- | --- | --- |
| **🔌 Probar y guardar** | `db.probar_conexion`; si responde, guarda la configuración y anota en la bitácora «CAMBIÓ CONEXIÓN (ARRANQUE)» | `None` → se **vuelve a intentar** el arranque |
| **💻 Trabajar en esta PC (base local)** | `cfg.guardar({"motor": "sqlite"})`: se sigue con la base de esta máquina | `"local"` → se vuelve a intentar |
| **✖ Salir** | No se abre el sistema | `"salir"` → `asegurar_conexion` devuelve `False` |

En esta pantalla el botón «volver al menú» se oculta a propósito: todavía no hay menú. Y trabajar
en local **no copia nada**: se usa la base SQLite de esa computadora (si está vacía, se verá
vacía), y para pasar esos datos a la central está la migración (§18).

Por último, al cerrar el sistema `main_qt.py` llama a `db.cerrar_conexiones()`, para que el
servidor no siga viendo «abiertas» unas conexiones que ya nadie usa.

## 18. Migración a la base central

`migracion.py` es el puente de **una sola vez** entre la base local («los datos buenos están en
esta computadora») y la base central del servidor. Después de la migración, todas las máquinas
trabajan contra PostgreSQL y el archivo `viaticos.db` de cada PC deja de ser la fuente de verdad
(queda como respaldo). Se ejecuta desde la pantalla «Conexión / Base de datos» (§17.4), con el
botón **⬆ Subir mis datos locales a la central**, o desde la consola.

Dos reglas que están escritas en el propio archivo:

- **No borra nada del equipo:** solo *lee* la base local y *escribe* en la central.
- **La central queda como copia exacta:** antes de copiar **vacía** sus tablas, para que no queden
  mezclados datos viejos y nuevos. Por eso la pantalla pide confirmación (§18.4).

### 18.1 Qué se copia y en qué orden

El orden es el de `TABLAS`, que va **de padres a hijos** (primero los catálogos, al final lo que
depende de ellos), porque la base respeta las claves foráneas:

| Grupo | Tablas | Qué son |
| --- | --- | --- |
| Catálogos | `empleados` · `vehiculos` · `parametros` · `provincias` · `cantones` · `distancias` · `clientes` | §6.2 y §15: personas, flota, tarifas y geografía |
| Accesos | `usuarios` | §5: usuarios y claves |
| Movimiento | `viajes` · `ajustes` · `gastos` · `respaldos` · `bitacora` | §8, §11, §12, §13: los viáticos y todo lo que cuelga de ellos |
| Contadores | `seq` | §7: la numeración por año (viático, etc.) |

Los respaldos viajan **dentro** de la base: si localmente estaban en modo `carpeta`, al migrar se
**leen los archivos del disco** y se guardan en la columna `contenido` (`_contenido_respaldo`), que
es lo que permite que cualquier PC los vea sin depender de una carpeta compartida (§13).

### 18.2 El procedimiento, paso a paso

`migrar(destino_postgres=True, incluir_respaldos=True, progreso=None)` hace, en este orden:

```
1) Comprueba que la configuración apunte a la central
   Si no → «La configuración actual no apunta a la base central (config.json → "motor": "postgres")»
2) db.init_db() en el DESTINO
   Crea las tablas que falten y siembra los catálogos con la base ya creada (§6, §16) — se
   importa `database` aquí dentro para no crear un ciclo de importaciones.
3) Abre las dos bases
   origen = SQLite de esta PC (cfg.dir_datos()\viaticos.db · si no existe, error claro)
   destino = bd.conectar()  (la central configurada)
   existentes = las tablas de TABLAS que existen en el destino
4) Vacía la central
   PostgreSQL:  TRUNCATE <tablas> RESTART IDENTITY CASCADE   (una sola orden)
   SQLite:      DELETE en orden inverso (por si el destino fuera local)
5) Copia tabla por tabla, fila por fila
   Se leen las columnas REALES del origen (PRAGMA table_info) y se insertan explícitamente, así
   una base vieja (con menos columnas) se puede subir sin inventar nada. Al terminar cada tabla,
   avisa cuántos registros copió (`progreso`, que en la pantalla es el texto del aviso).
6) Cuadra los contadores (`_reiniciar_secuencia`)
   Como los `id` se copian **con su valor**, PostgreSQL tiene que saber por dónde va:
   setval(pg_get_serial_sequence(tabla,'id'), MAX(id)). Solo en las tablas que tienen `id`.
7) Comprueba cada tabla
   El COUNT(*) de la central tiene que ser igual a lo que se copió; si no, lanza un error claro
   («La tabla «x» quedó con N registro(s) … la copia no se completó») en vez de dejar la central
   a medias en silencio.
8) Devuelve el resumen  {tabla: registros}  y cierra las dos conexiones
```

### 18.3 Los detalles que evitan perder datos

Casi todo lo delicado de este módulo nació de un problema real que está comentado en el código:
**los contadores (`seq`) se perdieron en la primera migración y un viático nuevo repitió el
N° 001/2026.** De ahí las precauciones:

| Detalle | Por qué |
| --- | --- |
| `_reiniciar_secuencia()` comprueba **primero** que la tabla tenga columna `id` (preguntando a `information_schema.columns`) | Porque `setval` lanza error en tablas sin `id` (`seq`, `distancias`), y en PostgreSQL **un error deja la transacción en estado fallido**: se perdería todo lo copiado de esa tabla. Si no puede cuadrar el contador, lo avisa por consola y sigue |
| Al copiar un `id` **se copia su valor** y luego se cuadra la secuencia con `MAX(id)` | Si se dejara al servidor repartir ids nuevos, se romperían las relaciones (`viajes` ↔ `ajustes` ↔ `gastos`) |
| `TRUNCATE … RESTART IDENTITY CASCADE` en **una sola** sentencia | `CASCADE` resuelve solo las dependencias (provincias/cantones, viajes/ajustes) y `RESTART IDENTITY` deja los contadores limpios, sin borrar tabla por tabla |
| Cada tabla se copia dentro de su transacción (`with conn:`), fila por fila | Si algo falla, esa tabla no queda a medias |
| Al final de cada tabla se compara el `COUNT(*)` del destino con lo copiado | Un fallo silencioso (como el de los contadores) se convierte en un error con el nombre de la tabla y los dos números |
| `incluir_respaldos=False` | Permite migrar **sin** las facturas y fotos: útil cuando lo que se quiere es mover los datos rápido y los archivos pesan demasiado |

También `_existe_tabla()` pregunta distinto en cada motor (`information_schema.tables` en
PostgreSQL, `sqlite_master` en SQLite), para que la migración sirva igual si algún día el destino
vuelve a ser una base local.

### 18.4 Desde la pantalla o desde la consola

**Desde la pantalla** (botón «⬆ Subir mis datos locales a la central», `_migrar` de
`q_conexion.py`), en este orden:

1. Exige que el motor elegido sea `postgres`; si no, pide primero «Base CENTRAL en el servidor» y
   guardar.
2. Lee **esta** máquina (`migracion.resumen_local()`) y enseña la lista exacta de lo que se va a
   enviar, con la advertencia de que **se reemplaza** todo lo que haya en la central y de que hay
   que hacerlo desde la máquina que tiene los datos buenos.
3. Si esta máquina **no tiene ningún viático**, el aviso sube de tono:

   > ⚠ CUIDADO: esta máquina no tiene ningún viático. Si continúa, la base central quedará VACÍA.
   >
   > Esto pasa cuando se abre el sistema desde el `.exe` de la carpeta «dist»: ese ejecutable usa su
   > propia carpeta «dist\data», que está vacía. Para subir los datos reales abra el sistema con
   > `INICIAR.bat` (o desde el código, no desde el `.exe`).

   Es exactamente la trampa de carpetas descrita en §17.2, avisada **antes** de destruir datos.
4. Pide la confirmación de peligro y, ya con el «si», guarda la configuración, va mostrando el
   avance de cada tabla (`progreso`, con `QApplication.processEvents()` para que se vea en
   pantalla mientras trabaja), llama a `migracion.migrar(...)`, descarta la caché
   (`db.olvidar_cache()`, porque la base cambió por completo), anota en la bitácora **«MIGRÓ A BASE
   CENTRAL»** con el host y el resumen, y termina con «Ahora el sistema trabaja contra el
   servidor».

**Desde la consola** —útil para revisar antes de tocar nada—:

```bat
python migracion.py           rem  muestra la conexión de destino y el resumen local; NO migra
python migracion.py --si      rem  ejecuta la migración (progreso por consola)
```

Después de migrar, en las demás computadoras solo hay que abrir el sistema: ya traen la dirección
del servidor por defecto (`AYUDA_SERVIDOR`, §17.4) y verán los mismos datos, sin llevar `config.json`
ni `viaticos.db`.

## 19. Borradores (memoria temporal)

La persona está llenando el viático, se va a buscar un dato, alguien cierra el sistema o
se apaga la computadora. Al volver a entrar **con su usuario**, el sistema le ofrece lo
que estaba escribiendo: eso es la «memoria temporal». No es un dato del viático ni un
archivo de la PC: es una fila de la tabla **`borradores`** (§6.2) que se guarda **sola**.

Que viva en la base (y no en un archivo local) es lo que permite recuperarla **en esta
computadora o en cualquier otra** cuando el sistema trabaja contra la central (§17, §18):
un archivo en `carpeta_app` no viajaría con la persona.

### 19.1 Qué se guarda y con qué nombre

`q_viaje.py` arma el estado completo de la pestaña de captura (`_clave_formulario()`) y
`database.guardar_borrador()` lo guarda como texto **JSON**. Lo que entra:

| Grupo | Claves del JSON |
| --- | --- |
| Lo que se está editando | `edit_numero`, `edit_ajuste_numero` |
| Datos generales | `responsable`, `cliente`, `vehiculo`, `ord1`, `ord2`, `efectivo`, `obs` |
| Recibos | `recibo`, `recibo2`, `recibo3` |
| Ruta y personal | `encargado`, `chofer`, `provincia`, `canton`, `lugar` |
| Montos | `km`, `peaje`, `otros`, `extra` |
| Fechas y horas | `salida`, `regreso`, `llego`, `sali_trabajo` (cada una `[fecha, hora]`) |
| Acompañantes | `pasajeros`: lista de `{nombre, medio, extra}` |

Dos decisiones que se ven en el código:

- **JSON y no columnas**: agregar un campo al formulario **no obliga a cambiar la base**
  (§8.4). El borrador no es un dato contable —es una ayuda—, así que no lleva las
  validaciones ni las claves foráneas del viático.
- **La clave es el `usuario`** (el de la clave), no el nombre completo que la persona
  escribe al entrar: `_clave_borrador()` toma `usuario["usuario"]` (o `usuario["nombre"]`)
  y lo pasa a mayúsculas, para que el borrador lo recupere **su dueño** y no cualquiera.
  En la tabla eso es **una fila por usuario** (`usuario` es la clave primaria), con
  `pantalla` (por defecto `'viatico'`: deja lugar a otras pantallas) y `actualizado_el`
  (`datetime('now','localtime')`, la fecha en la que se guardó). Guardar es **reemplazar**
  (`DELETE` + `INSERT`), así nunca quedan dos borradores del mismo usuario.

### 19.2 Cuándo se guarda (y cuándo no)

| Momento | Quién lo dispara |
| --- | --- |
| Cada **20 segundos** con la ventana abierta | temporizador `self._memoria` (`QTimer`, 20 000 ms) → `_guardar_borrador()` |
| Al **cerrar la ventana** de viáticos | `closeEvent` → `_guardar_borrador()` |
| Al **agregar o quitar** un acompañante | `agregar_pasajero()` / `quitar_pasajero()` → `_guardar_borrador()` (los acompañantes viven en memoria, no en el formulario) |
| Al **recuperar** lo guardado | `_aplicar_estado()` deja el formulario con lo recuperado y el guardado automático sigue |

No se guarda siempre: `_hay_algo_que_recordar()` exige que **haya algo escrito**
(`_hay_contenido()`: encargado, cliente, lugar, observaciones, órdenes, recibos, vehículo,
acompañantes, o `km`/`efectivo`/`otros` distintos de cero según `_es_cero()`) **y** que sea
distinto de cómo estaba el formulario al abrirlo (`_borrador_base`, fijado por
`_recordar_base()` al abrir la ventana, al limpiar y al cargar un viático). Así, abrir la
pantalla y cerrarla **sin tocar nada** no deja un aviso para la próxima vez; y si el
formulario volvió a quedar vacío (por ejemplo, se recuperó y se limpió), el borrador que
había se borra.

Si la base no responde, el borrador **no interrumpe nada**: `guardar_borrador()` atrapa el
error, lo escribe en la consola («No se pudo guardar el borrador: …») y devuelve `False`;
la persona sigue trabajando igual.

### 19.3 Cómo se recupera

1. **Aviso automático al abrir la ventana.** `QTimer.singleShot(700, …)` llama a
   `_avisar_borrador_pendiente()` cuando la ventana ya está dibujada; si la ventana no
   está visible no hace nada, y con `silencioso=True` no dice nada cuando no hay borrador.
2. **A pedido del usuario.** El botón **🕘 RECUPERAR LO ÚLTIMO** de la barra de la captura
   llama a `_boton_recuperar()` → `_recuperar_borrador(silencioso=False)`; si no hay nada,
   lo explica: «No hay nada guardado a medias para su usuario… (se guarda cada 20
   segundos)».
3. **Antes de pisar lo que hay, pregunta.** El aviso muestra **cuándo** se guardó
   (`_cuando_guardado()`: «hoy a las 14:05», «ayer a las 09:30» o «el 28/09/2026 a las
   09:30») y un **resumen reconocible** (`_resumen_estado()`: encargado, destino, km,
   cliente, número de acompañantes y, si corresponde, «(se estaba editando el viático N°
   X)»). Si el formulario ya tiene algo escrito, avisa que **se reemplaza**.
4. **Vuelve al formulario.** `_aplicar_estado()` repone cajas de texto, listas
   desplegables, fechas/horas y acompañantes; refresca los catálogos que dependen de otros
   campos (`cb_canton`, `cb_chofer`), recalcula el «medio» del vehículo
   (`_actualizar_medio()`) y vuelve a numerar (`_actualizar_numero()`). Lo recuperado **no
   se recalcula**: las horas quedan como se escribieron, igual que al abrir un viático
   guardado (§8.2), y no como cuando se usa el botón **⏱ Estimar viaje** (§9).
5. **Nunca pisa datos ya guardados.** Si el viático que se estaba editando **ya no está
   pendiente** (`_viatico_pendiente()`: otra computadora lo guardó o lo anuló), lo
   recuperado pasa a ser **viático NUEVO** y el aviso lo dice con todas las letras.
6. **Queda anotado.** `db.registrar_bitacora(usuario, "RECUPERÓ LO QUE ESTABA LLENANDO", …)`
   con la fecha y hora del borrador (§5), la barra de estado muestra «Recuperado lo que
   estaba llenando (…)» y el borrador **sigue guardándose solo** (`_borrador_guardado =
   True`), por si vuelve a pasar lo mismo.

### 19.4 Cuándo se borra (y limpieza automática)

| Se borra cuando… | Cómo |
| --- | --- |
| Se **guarda** el viático | `guardar()` termina llamando a `limpiar()` → `_borrar_borrador()` |
| Se usa **🧹 LIMPIAR / CANCELAR** | `limpiar()` → `_borrar_borrador()` |
| El formulario vuelve a quedar sin contenido | `_guardar_borrador()` ve que no hay nada que recordar y borra lo que había |
| Pasan **30 días** | `DIAS_BORRADOR = 30`; `borrar_borradores_viejos()` al abrir el sistema |

`_borrar_borrador()` no hace nada si en esta sesión nunca se guardó nada
(`_borrador_guardado`) y cualquier error se ignora: el borrador es una ayuda, no un dato
del viático.

La limpieza por edad corre en `init_db()` (arranque, §4) con la conexión ya abierta
(`borrar_borradores_viejos(conn=conn)`), comparando el **texto** de la fecha
(`actualizado_el < ahora − 30 días`), que funciona igual en SQLite y en PostgreSQL. Es a
propósito: en la central la memoria temporal la ven todas las PC y no tiene sentido
guardar capturas a medias para siempre; los borradores del día se conservan.

Para ver quién tiene algo a medio llenar (usuario, pantalla y cuándo) está
`db.usuarios_con_borrador()`. Hoy lo usan las pruebas (§21), que comprueban el ciclo
completo: la ventana guarda sola (encargado, km y acompañantes) → se cierra sin guardar el
viático → al abrirla de nuevo con el mismo usuario lo recupera → al guardar el viático el
borrador desaparece → los de más de 30 días se descartan solos.

## 20. Rendimiento

Dos quejas concretas movieron todo lo que se cuenta en esta sección: **«la pantalla se
queda pensando»** al elegir la provincia o el cantón, y **la lista de viáticos tarda** en
refrescarse cuando varias computadoras trabajan contra la base central. El diagnóstico
fue simple: **el problema no estaba en el cálculo ni en el archivo local, estaba en el
viaje a la base de datos**. Cuatro decisiones lo resuelven, y ninguna cambia la forma de
trabajar de la gente:

| Palanca | Dónde vive | Qué se gana |
| --- | --- | --- |
| La conexión se **reutiliza** | `bd.py` (`_RESERVA`) | No se paga el saludo al servidor en cada consulta |
| **Memoria corta** (30 s) de catálogos y parámetros | `database.py` (`_MEMORIA`) | Teclear en el formulario no consulta la base |
| **Una consulta por pantalla**, no una por fila | `resumen_viaticos()`, `conteo_ajustes()` | El historial completo del año se llena con 2 consultas |
| **No redibujar lo que no cambió** | `q_viaje`, `q_ajustes`, `ComboAuto` | Nada parpadea y no se pierde lo elegido |

### 20.1 El costo real: el saludo a la base

Abrir una conexión **contra el servidor central** no es gratis: hay que negociar el TCP,
autenticarse con usuario y clave y arrancar la sesión en PostgreSQL. En la red de la
empresa eso son **entre 15 y 40 ms** que la persona percibe como pausa. Antes, `bd.py`
abría y cerraba **una conexión por consulta**, y el formulario de viáticos consulta
muchísimas veces por interacción (parámetros, km y horas del cantón, empleados, clientes,
vehículos, provincias). Una vuelta normal por la pantalla gastaba **entre 25 y 30
conexiones nuevas** (§20.7).

Ahora la conexión se abre **una sola vez por base y por hilo** y se va prestando:

| Pieza | Para qué |
| --- | --- |
| `_RESERVA` | Guarda la conexión por clave `(_clave_base(), threading.get_ident())` |
| `_CANDADO` (`RLock`) | Evita que dos hilos tomen la misma conexión a la vez |
| `_clave_base()` | Identifica **a qué base** apunta (motor, host, puerto, base, usuario) |
| `conectar()` | Presta una libre (`prestada=True`), o abre una nueva con `_abrir_guardada()` |
| `close()` | Devuelve la conexión a la reserva (no la cierra) |
| `directa=True` | Abre una conexión aparte que **no** se guarda: sirve para **probar otra dirección** sin tocar la que está en uso (§17) |

Lo que se pidió con `conn = conectar()` y con `with conectar() as conn:` sigue
comportándose igual que antes, y **lo que no se confirma con `commit` se pierde** al
cerrar: reciclar la conexión no cambió la forma de guardar, solo el costo (§21 lo
comprueba).

**Cuando la conexión se queda quieta.** Los cortafuegos y el propio servidor suelen cortar
las conexiones inactivas; si eso pasara al guardar, el usuario vería un error. Por eso:
si la conexión lleva más de `_QUIETA_SEGUNDOS = 20` segundos sin usarse,
`_probar_si_estuvo_quieta()` le lanza un `SELECT 1`; si falla, `_olvidar_de_reserva()` la
da de baja y se abre otra en su lugar. A la conexión del servidor se le pusieron además
`keepalives` (idle 30 s, intervalo 10 s, 5 intentos) para que no la corten por estar
quieta, y `connect_timeout=6` para avisar **en 6 segundos** si el servidor está dormido en
vez de dejar la ventana colgada (§17.1).

**Si una consulta falla.** En PostgreSQL un error deja la transacción en mal estado y,
como ahora la conexión se comparte, sin arreglarlo fallarían **todas** las consultas
siguientes. De ahí `_dejar_sana()`, que hace `rollback()` cuando algo revienta. Y al
devolver la conexión, `_devolver()` mira `conn.info.transaction_status`: si quedó algo a
medias lo deshace antes de prestarla otra vez.

**Cuando la base cambia.** Cambiar de servidor en la pantalla de conexión (§17.4) cambia
`_clave_base()`, así que la próxima consulta abre una conexión nueva; `_abrir_guardada()`
cierra la que quedó sin devolver. Al **salir** del sistema, `db.cerrar_conexiones()` →
`bd.cerrar_reserva()` cierra todo lo guardado (§4).

**Cómo se mide esto sin adivinar.** `bd.estadisticas()` lleva los contadores
(`aperturas`, `reusos`, `consultas`, `espera_seg`) y `bd.reiniciar_estadisticas()` los
pone en cero; con eso `pruebas_conexion.py` y `pruebas_rendimiento.py` comprueban que la
conexión se reutilice de verdad. Para comparar, la variable de entorno
`VIATICOS_SIN_RESERVA=1` apaga la reserva y deja el sistema **como era antes** (§20.7).

### 20.2 Memoria corta: lo que se pide a cada rato

Hay datos que la pantalla necesita **en cada tecleo** y que casi nunca cambian: los
parámetros (tarifas, horas límite), la tabla de rutas (km y horas por cantón), los
empleados, los clientes, los vehículos, las provincias, los cantones de la provincia
elegida. Pedirlos a la base cada vez era la otra mitad del problema.

`database.py` los guarda unos segundos en memoria:

| Pieza | Qué hace |
| --- | --- |
| `_SEGUNDOS_MEMORIA = 30` | Cuánto se recuerda cada dato |
| `_MEMORIA` | Diccionario `clave → (momento, valor)` |
| `_memoria(clave, segundos, fábrica)` | Devuelve lo guardado si todavía sirve; si no, lo vuelve a leer |
| `olvidar_cache(*claves)` | Borra todo, una clave, o **todo un grupo** pasando el prefijo terminado en `:` |
| `_copiar(valor)` | Devuelve una **copia**, para que nadie modifique lo guardado sin querer |

Claves que se recuerdan: `empleados`, `vehiculos`, `provincias`, `clientes`,
`cantones:<PROVINCIA>`, `distancias` (la tabla de rutas completa, de **una sola lectura**,
porque el formulario la necesita entera para calcular horas) y `parametros`.

La regla que evita datos viejos: **todo lo que graba esas tablas borra la copia en el
momento**. Por eso `olvidar_cache()` aparece en las funciones que agregan o cambian
empleados, clientes, vehículos, provincias, cantones, rutas y parámetros, y también al
**migrar** (la base cambió por completo, §18). Nunca se ve un dato viejo **propio**; el
de otra computadora entra, a lo más, 30 segundos después —el mismo margen que el refresco
de fondo del historial (§20.4)—.

`configuracion.py` hace lo mismo con lo que **no** es base de datos: lee `config.json`
**una sola vez** (`_CACHE`) y resuelve la carpeta de datos **una sola vez**
(`_CARPETA_DATOS`), porque se consultan muchas veces por segundo; `olvidar_cache()` las
vuelve a leer del disco, y eso es lo que se llama al guardar desde la pantalla de
conexión (§17.4).

> **Ojo con el nombre «memoria».** Aparecen tres memorias distintas y ninguna es la otra:
> `database._MEMORIA` (catálogos y parámetros, 30 s), `configuracion._CACHE` (el
> `config.json`) y `q_viaje.self._memoria` (el `QTimer` de 20 s que guarda el **borrador**,
> §19).

### 20.3 Una consulta por pantalla, no una por fila

Cuando se abría el historial, lo caro no era la consulta: era **repetirla por cada
viático**. Hoy el historial completo del año se llena con **dos** consultas y el filtrado
se hace **en memoria**:

| Función | Qué resuelve |
| --- | --- |
| `resumen_viaticos()` | **Una** consulta con `GROUP BY viatico_numero` que trae, por viático, `MIN(fecha_salida)`, `MAX(fecha_regreso)`, `MAX(responsable)`, `MAX(estado)`, `SUM(total)`, `SUM(valor_cajero)` y los textos agrupados de `empleados` y `lugares` (`bd.agrupar()` → `GROUP_CONCAT` en SQLite, `STRING_AGG` en PostgreSQL) |
| `conteo_ajustes()` | **Una** consulta (`COUNT(DISTINCT ajuste_numero)` con `GROUP BY viatico_numero`) que devuelve el número de ajustes de **todos** los viáticos a la vez |
| `ajustes_viaje(numero)` | Los ajustes de **un solo** viático, y solo cuando hace falta |
| `numero_visible(clave)` | El número que ve la gente («001/2026») es **aritmética** (`clave % FACTOR_ANIO`), no una consulta: se puede llamar por fila sin costo (§7) |

Con esas filas ya en memoria, el buscador del historial filtra por número, empleados,
lugares, responsable o cliente en Python (`q_viaje.refrescar_historial()`), igual que el
filtro por provincia y por estado. **Escribir en el buscador no consulta la base ni una
vez**: solo recorre lo que ya se leyó.

Otras tres decisiones del mismo tipo:

- **`LIMIT 1` cuando solo hace falta saber «si hay»**: el arranque pregunta
  `SELECT 1 FROM parametros LIMIT 1` (y lo mismo con empleados, vehículos, provincias,
  distancias y clientes) antes de sembrar las tablas semilla (§16); `proximo_valor()`
  obtiene el consecutivo con `UPDATE … RETURNING` en vez de leer y escribir por separado;
  `estado_justificacion()` pide una sola fila del viático.
- **`executemany()` para lo masivo**: sembrar catálogos y la copia tabla por tabla de la
  migración (§18) van en bloque, no fila por fila.
- **Indexar lo que se filtra**: cuando el historial se filtra en memoria, la base solo
  necesita responder rápido al `GROUP BY` y a los filtros de la bitácora (§20.5).

### 20.4 No redibujar lo que no cambió

El refresco de fondo es lo que hace que un viático guardado en otra computadora aparezca
solo. Para que eso no cueste (ni parpadee, ni pierda lo que la persona tenía elegido), la
regla es: **volver a leer sí, redibujar solo si cambió**.

| Ventana | Temporizador | Qué compara antes de dibujar |
| --- | --- | --- |
| Viáticos (historial) | `QTimer` de **15 s** → `refrescar_historial(automatico=True)` | `_hist_firma`: tupla de (número interno, estado, empleados, total) de todas las filas |
| Justificación (lista de viáticos) | `QTimer` de **15 s** → `_cargar_lista(automatico=True)` | `_lista_firma`: lo mismo (número, estado, empleados, total) |
| Listas desplegables | A pedido: `ComboAuto.opciones()` | `_pintadas`: la lista de opciones que está dibujada |

Los dos detalles que se ven en el código:

- **La firma incluye el total y el estado**, no solo el número: así el refresco también
  detecta que otra computadora **justificó** o **anuló** un viático, no solo que agregó
  uno nuevo. Si la firma es idéntica, la función **termina sin tocar la tabla**, y por eso
  el viático que la persona tenía seleccionado sigue seleccionado.
- **`ComboAuto` recuerda sus opciones 5 segundos** (`SEGUNDOS_MEMORIA = 5`, menos que los
  30 s de los catálogos, porque una lista puede cambiar por el trabajo de otra máquina).
  `showPopup()` llama a `refrescar_opciones(forzar=False)`, o sea: **abrir la lista de
  cantones (~200 nombres) no consulta la base ni repinta**; y cuando sí repinta, guarda el
  texto que se estaba escribiendo, bloquea las señales (`blockSignals`) para no disparar
  recálculos y lo repone (`setEditText`). Ese parpadeo era, literalmente, la causa de que
  la ventana «se quedara pensando».

**No hay «avisos» entre computadoras** (nada de sockets ni notificaciones): cada ventana
**pregunta sola** cada 15 segundos. Cuesta dos consultas por ventana abierta y por
intervalo, y a cambio hay una sola forma de estar al día, que funciona igual con la base
local y con la central (§17, §18). El mismo criterio se usa en el borrador (§19): guardar
cada 20 segundos **solo si hay algo que recordar**.

### 20.5 Índices: que la base no recorra todo

El esquema (§6.1) crea sus índices con `CREATE INDEX IF NOT EXISTS`, de modo que la misma
sentencia corre en cada arranque sin fallar si ya existen (§4). Están puestos sobre lo que
de verdad se filtra o se agrupa:

| Índice | Sobre | Para qué |
| --- | --- | --- |
| `idx_viajes_numero` | `viajes(viatico_numero)` | El `GROUP BY` de `resumen_viaticos()` y `conteo_ajustes()`, y cargar un viático con sus filas |
| `idx_viajes_fecha` | `viajes(fecha_salida)` | Informes y filtros por fecha |
| `idx_viajes_estado` | `viajes(estado)` | Historial por estado (pendiente / justificado / anulado) |
| `idx_gastos_numero` | `gastos(viatico_numero)` | Justificación: los gastos de un viático |
| `idx_ajustes_numero` | `ajustes(viatico_numero)` | Los ajustes de un viático |
| `idx_respaldos_numero` | `respaldos(viatico_numero)` | Las facturas de un viático (§13) |
| `idx_bitacora_fecha` | `bitacora(fecha)` | El informe de actividad por rango de fechas (§14, §5) |
| `idx_usuarios_usuario` | `usuarios(usuario)` | El ingreso por usuario (§5) |

Los índices van **al final** del esquema a propósito: primero se crean las tablas y
después los índices, así el mismo texto sirve para una base nueva y para una que ya existía
(todas las sentencias son `IF NOT EXISTS`).

Dos decisiones que se eligieron **no** tomar:

- **No se activó WAL ni se cambiaron los `PRAGMA` de SQLite** más allá de
  `PRAGMA foreign_keys = ON` (§17.1). La pausa no venía del archivo local —que se abre
  con `timeout=30` y vive en el mismo equipo— sino del saludo al servidor; cada opción
  extra sería una cosa más que explicar, respaldar y justificar (§13, §16). Si algún día
  la base local creciera de verdad, este es el primer lugar donde mirar.
- **No hay paginación ni carga por demanda en el historial**: se lee el año completo y se
  filtra en memoria, porque con una consulta agregada (§20.3) eso es barato y permite que
  el buscador responda al instante. Si el volumen creciera mucho, el paso siguiente sería
  paginar `resumen_viaticos()` y filtrar en la base, no en Python.

### 20.6 Lo que no entra a la base, y por qué eso también es velocidad

Lo más pesado del sistema no son los viáticos: son **las fotos de las facturas y los
PDF** (§13). La base guarda solo lo necesario para encontrarlos y, según el modo elegido
en la configuración, **o la ruta** (`carpeta`) **o los bytes** (`base`). Para que eso no se
descontrole:

| Medida | Dónde | Efecto |
| --- | --- | --- |
| Compresión al adjuntar: `LADO_MAX = 1600 px`, `CALIDAD_JPEG = 72`, `thumbnail()` con `LANCZOS` y guardado en PDF | Respaldos (§13) | Una foto de celular de varios MB entra en unos cientos de KB: menos red, menos respaldo, más rápido de abrir |
| `consolidar_respaldos_pdf()`: al justificar, todos los respaldos del viático se unen en **un** `VIATICO_n_COMPLETO.pdf` y los sueltos se borran | Justificación (§13) | Un solo documento por viático para ver, imprimir y respaldar; menos archivos que recorrer |
| `ruta_para_abrir()`: si el respaldo vive **dentro** de la base, se escribe una copia temporal en `%TEMP%\viaticos_respaldos` y se devuelve esa ruta | Respaldos (§13) | Abrir/ver funciona igual en los dos modos |
| Informes **HTML** en la carpeta temporal, abiertos con el navegador (`webbrowser.open`), y Excel con `openpyxl` | Informes (§14) | No se empaqueta ninguna librería pesada de PDF: el motor de impresión del navegador y el Excel instalados hacen el trabajo |
| Los PDF se abren con el sistema (`os.startfile`) | Respaldos (§13) | No se incluye un visor propio |

En resumen: la base (y su respaldo) se queda con lo pequeño y estructurado, y **lo grande se
comprime y se abre solo cuando hace falta**.

### 20.7 Cómo se mide (y las cifras)

`pruebas_rendimiento.py` no «simula» la pantalla: **levanta las ventanas de verdad** con la
plataforma `offscreen` (sin mostrar nada en pantalla) y cronometra lo que se hace todo el
día. Su forma de trabajar:

| Pieza | Qué hace |
| --- | --- |
| `bd.reiniciar_estadisticas()` antes de cada acción | Para que los contadores sean **de esa acción**, no acumulados |
| `_mediciones` | Guarda por acción: milisegundos, consultas, conexiones **abiertas** y el ahorro estimado (`(consultas − aperturas) × costo de conexión`) |
| `_simular_latencia(ms)` | Sustituye `bd._abrir_cruda` por una versión que **duerme** ese tiempo, para sentir en la misma máquina lo que pasa por la red |
| `_tabla()` | Imprime la tabla de acciones y los totales, y al final «Consultas: N · conexiones abiertas: M» y el veredicto OK / FALLA |
| Alertas apagadas | `informar` / `aviso` / `error` / `confirmar` se reemplazan por funciones vacías, para que ninguna ventana se quede esperando un clic |

Opciones: sin argumentos usa una **base local de prueba** en una carpeta temporal
(`VIATICOS_DATA` + `VIATICOS_MOTOR=sqlite`, borrada al terminar) y carga datos de ejemplo,
de modo que **nunca toca los datos de trabajo**; `--servidor` mide contra la base central de
`config.json` y **omite el paso de guardar** (solo lee); `--comparar` mide dos veces, «antes»
(una conexión por consulta) y «ahora» (conexión reutilizada); `--simular-conexion=25` suma
25 ms a cada conexión nueva; `--ms-conexion=30` fija el costo usado para el «ahorro».

Las cifras salen de la **Versión 8.2** de `HISTORIAL_DE_CAMBIOS.md`, con las ventanas de
viáticos y de parámetros armadas de verdad y **25 ms simulados por cada conexión nueva**
(como en la red de la empresa):

| Acción | Antes | Ahora |
| --- | --- | --- |
| Elegir provincia | 30 ms | 0,4 ms |
| Elegir cantón | 31 ms | 1,2 ms |
| Abrir la lista de cantones | 1 ms | 1 ms (sin consultar ni repintar) |
| Refrescar el historial | 114 ms | 7 ms |
| Ver el detalle de un viático | 58 ms | 4 ms |
| Guardar y ver el historial | 172 ms | 11 ms |
| **Las 14 acciones de la prueba** | **1.567 ms · 30 conexiones nuevas** | **766 ms · 0 conexiones nuevas** |

Cómo se lee la tabla: las consultas se siguen haciendo (la base hace el mismo trabajo), lo
que **desaparece son las conexiones nuevas**, y con ellas la espera. Lo que queda en pie es
el trabajo que no depende de la red: armar las ventanas y dibujar la tabla.

Una corrida posterior, en la máquina de desarrollo y con el mismo
`--comparar --simular-conexion=25`, confirmó el resultado: **antes 2.291 ms con 30 conexiones
nuevas; ahora 1.524 ms con 0** (33 % menos de tiempo), **las mismas 27 consultas** y las dos
comprobaciones del final en **OK** («todas las acciones se completaron sin errores» y «la
conexión se reutiliza: 0 conexiones para 27 consultas»). En esa corrida la **primera**
apertura de la lista de cantones tardó ~128 ms, pero con **0 consultas**: ese tiempo es armar
el desplegable en pantalla, no la base.

`pruebas_conexion.py` comprueba los invariantes de ese comportamiento (§21): tres lecturas
seguidas abren **una sola** conexión y la reutilizan, los catálogos no suman consultas de
más, un `commit` sí graba, un cierre sin `commit` no graba, y una consulta que falla **no
daña** la conexión para las siguientes.

Y lo que la persona nota, al final, es exactamente eso: elegir provincia y cantón responde
al instante, la lista de cantones se abre sin pausa, y el historial del año aparece sin
esperar —también cuando lo llenó otra computadora— (§19, §21).

## 21. Pruebas y autodiagnóstico

Todo lo que se explicó antes tiene una comprobación que se puede correr en cualquier
máquina, **sin servidor y sin tocar los datos de trabajo**. Son programas sueltos
(`pruebas_*.py`, en la carpeta del sistema) que se ejecutan a mano con `python`:

```bat
cd sistema_viaticos_miempresa
python pruebas_conexion.py
```

### 21.1 Qué comprueba cada prueba

| Prueba | Qué comprueba | Resultado de la última corrida |
| --- | --- | --- |
| `pruebas_conexion.py` | La conexión reutilizable (§20.1): que **no** se abra una por consulta, que cerrar y volver a pedir siga funcionando, que lo confirmado con `commit` se guarde y lo no confirmado no, que una consulta que falla **no** deje la conexión inservible, que `config.json` se lea una sola vez y que un viático se guarde y se vuelva a leer | **8 comprobaciones → «TODO OK»** |
| `pruebas_ventanas.py` | Que **cada ventana Qt se arme** y cargue datos (con datos falsos): detecta de inmediato un error de construcción o un cambio de nombre en `database.py` | **8 de 8 ventanas correctas** |
| `pruebas_qt.py` | La interfaz sin abrir nada: tema, componentes (tablas, tarjetas, campos de fecha/hora, listas con autocompletado), ventanas de ingreso y del menú, **claves cifradas** e **ingreso por área** (§5); al final lista los módulos pendientes de migrar | **60 de 60 comprobaciones correctas** · «Módulos pendientes de migrar: ninguno» |
| `pruebas_horas.py` | El cálculo automático de llegadas, las comidas del camino y los colores del resumen (§9); deja el detalle en `pruebas_horas_resultado.txt` | OK / FALLA por cada línea |
| `pruebas_excel.py` | **La especificación**: compara cada viaje del Excel de trabajo con lo que calcula `calculos.py` (§10, §16); deja `pruebas_excel_resultado.txt`; si no encuentra el Excel, lo avisa **sin fallar** | OK / FALLA por cada viaje |
| `pruebas_ajustes.py` | Los **ajustes** de viático (§11.2): que el ajuste empiece el día siguiente al **último día entregado**, que el hospedaje se cobre **por noche** (incluida la del último día entregado) y que pague el **taxi de regreso** (y no el de salida); base temporal, sin ventanas | **22 comprobaciones · 0 fallos** |
| `pruebas_taxis.py` | **Cuándo se paga el taxi y cuándo no** (§10.2): viático nuevo, ajuste, vuelta de madrugada, horas límite como las guarda la base (`"06:00:00"`, `"6:00"`, una base vieja sin esas columnas) y una hora límite que no se entiende | **26 comprobaciones · 0 fallos** |
| `pruebas_reglas.py` | **El repaso total del motor** (§10 y §11.2): lee `VIATICO 2 2026.xlsx` y compara **celda por celda** las fórmulas del Excel con `calculos.py` (días, comidas, taxis, hospedaje, agua, combustible y total) con las tarifas y horas de su hoja «Parámetros»; aparte cuenta las celdas escritas a mano; casos de oro hechos a mano y el ejemplo de cuatro personas a Quito del Excel ($94 / $181.50 / $54 / $94 y $450 de cajero); barrido de las **96 cuartos de hora del día** en cinco escenarios; ajustes encadenados (días y noches completos); parámetros vacíos, en texto, con segundos o imposibles; cajero del grupo; lectura de horas; y los bordes de días, noches y comidas. Deja el detalle en `pruebas_reglas_resultado.txt` | **734 comprobaciones · 0 fallos** |
| `pruebas_rendimiento.py` | Cuántas consultas y cuántas conexiones cuesta cada una de las 14 acciones de una jornada, y cuánto tarda (§20.7) | Tabla completa + veredicto; **siempre devuelve 0** (es una herramienta de medición, no un portero) |

### 21.2 Cómo están escritas (el patrón es el mismo en todas)

| Detalle | Por qué |
| --- | --- |
| `QT_QPA_PLATFORM = "offscreen"` | Se arman las ventanas **sin abrir ventanas**: corre igual en un servidor o por escritorio remoto |
| Carpeta temporal + `VIATICOS_MOTOR=sqlite`, `VIATICOS_DATA`, `VIATICOS_RESPALDOS=carpeta` | Cada prueba trabaja en **su propia base desechable**; al terminar la borra y lo dice en pantalla |
| Función `revisar(nombre, condición, detalle="")` | Acumula cada comprobación y la imprime como `OK` / `FALLA` con su detalle |
| Recuento y **código de salida** `0` / `1` | «N de M correctas» y `sys.exit(0|1)`: se puede encadenar en un `.bat` o en una verificación automática |
| Nada se escribe en los datos reales | Es la regla de todas: la prueba de rendimiento con `--servidor` **solo lee** (§20.7) |

### 21.3 El autodiagnóstico del `.exe`

Cuando el programa no arranca en una computadora, casi siempre es porque al `.exe` le falta
algo (una librería, la carpeta de datos, los permisos). Para eso está el **autodiagnóstico**
(§4): se ejecuta el `.exe` con la variable puesta y **no abre ninguna ventana**, solo revisa
y escribe el informe.

```bat
set VIATICOS_SELFTEST=1
dist\Sistema_Viaticos.exe
```

`main_qt.autodiagnostico()` corre **antes** de crear cualquier ventana y deja el informe en
**`autodiagnostico.txt`, junto al ejecutable** (el `.exe` no tiene consola: el archivo es la
única forma de leerlo; además lo imprime en pantalla cuando se corre desde el código
fuente). El informe trae:

| Bloque | Qué informa |
| --- | --- |
| Encabezado | Fecha y hora, versión de Python, ruta del programa y **carpeta de datos** en uso |
| Autoría | `autor.creditos()` y si la **firma del autor** está completa (§5) |
| Interfaz | La versión de **PySide6** que se cargó |
| Base de datos | Que `init_db()` deje la base lista, `configuracion.describir()` (qué conexión está en uso, §17.4) y **cuántos** empleados, clientes, viáticos y parámetros se leen de verdad |
| Librerías | Versiones de `openpyxl` (Excel), `Pillow` (fotos/PDF) y `psycopg2` (servidor) |
| Módulos | Que los **13 módulos** del sistema se puedan importar: `qt_tema`, `qt_comunes`, `q_login`, `q_menu`, `q_viaje`, `q_ajustes`, `q_admin`, `q_bitacora`, `q_respaldos`, `q_usuarios`, `q_conexion`, `reportes` y `migracion` |
| Cierre | `RESULTADO: todo correcto` o **cuántos** problemas se encontraron |

Dos detalles que hacen útil el informe:

- **Lo que depende del servidor se marca `AVISO`, no `FALLA`**: si la base central está
  apagada, eso no es un problema del programa, y el resumen no debe teñirse de rojo por eso.
- El empaquetador (`empaquetar_servidor.py`) **termina recordando** cómo correr esta
  comprobación, y `autor.sellar_bitacora()` puede dejar constancia **fechada en la bitácora**
  de que el programa en uso es el original del autor (§5).

### 21.4 Las pruebas contra el Excel (la especificación)

La regla de oro del sistema es «**el Excel es la especificación**» (§1), así que las pruebas
más importantes son las que comparan **contra el Excel de la empresa**, no contra lo que el
programa cree. La que vive dentro del sistema es `pruebas_excel.py`; las demás son
herramientas de trabajo que viven **fuera** del programa (carpeta `herramientas\`, no se
empaquetan ni se copian a las computadoras, §2):

| Herramienta | Qué hace |
| --- | --- |
| `pruebas_excel.py` | Compara **cada viaje** del Excel de viáticos con lo que calcula `calculos.calcular` (§10) |
| `comparar_reglas_excel.py` | **Regla contra regla** con el formato nuevo (`VIATICO 2 2026.xlsx`), que ya trae las columnas calculadas por día (desayuno, almuerzo, merienda, taxis, hospedaje, agua, combustible, total y valor a retirar en cajero) |
| `comparar_excel_viaticos.py` | Lee el Excel real (una hoja por viático), **crea los mismos viáticos en una base local** y compara valor por valor (§16) |
| `viaticos_148_149.py` | Carga los **dos viáticos reales ya pagados** (N° 148 y 149, semana del 28/09 al 03/10 de 2026, personal en MACAS) en la base **local**, comprueba que el programa pague exactamente lo mismo que el Excel y guarda los PDF (carpeta `PDF_VIATICOS_148_149\`) |
| `generar_excel_tiempos.py` | Genera `TIEMPOS DE VIAJE MIEMPRESA.xlsx`, el que **va con el sistema** en `excel\`: todos los cantones con sus km desde Cuenca y las horas de viaje |
| `tiempos_de_viaje.py` | Llena esas horas de viaje con servicios libres de OpenStreetMap (**sin claves ni tarjeta**): ubica el cantón y calcula la ruta |
| `preparar_distancias_excel.py` · `preparar_distancias_doc.py` | Pasan el Excel de distancias y el Word «DISTANCIAS DOC.docx» que la empresa revisó cantón por cantón al formato del sistema; dejan su resultado en `*_resultado.txt` |
| `recalcular_cajero.py` | Pone al día el «valor a retirar en cajero» de los viáticos **ya guardados** con el criterio nuevo: un solo redondeo sobre el total del viático (§10, §11) |
| `ver_excel.py` | Muestra las hojas, columnas y filas de un libro de Excel, para revisarlo **antes** de cargarlo al sistema (§16) |
| `manual_pdf.py` (+ `MANUAL_A_PDF.bat`) | Arma `documentacion\MANUAL_DE_USUARIO.pdf` desde `MANUAL_DE_USUARIO.md`: portada, índice con páginas, cada capítulo en página nueva, capturas enmarcadas y las notas en **cuadros azules**. Se vuelve a correr cuando cambie el manual |
| `limpiar_y_firmar.py` | Deja el proyecto **firmado y limpio**: cabecera y firma en todos los `.py`/`.bat`, cabecera en los `.md`, `CREDITOS.md`, `DOCUMENTACION.md`, `version_info.txt` enganchado al `.spec`, y borra `__pycache__`, `build` y temporales. Es idempotente (correrlo dos veces no duplica nada) |

### 21.5 La rutina antes de entregar a las computadoras

1. **Correr las pruebas** en la máquina donde se hizo el cambio:
   `python pruebas_conexion.py`, `python pruebas_qt.py`, `python pruebas_ventanas.py`.
   Si se tocaron horas, llegadas o comidas del camino, además `python pruebas_horas.py`; si
   se tocó la conexión, `python pruebas_rendimiento.py --comparar --simular-conexion=25`.
   Ninguna necesita servidor ni toca los datos de trabajo.
2. **Empaquetar** con `EMPAQUETAR_EXE_SERVIDOR.bat` (§17: el empaquetado de servidor ya trae
   la IP y el puerto de fábrica apuntando al servidor de la empresa).
3. **Comprobar el `.exe`** con `set VIATICOS_SELFTEST=1` y leer el `autodiagnostico.txt` (§21.3).
4. **Copiar** `dist\Sistema_Viaticos.exe` a cada computadora (§17.5).
5. Si el cambio tocó la **base de datos**, aplicar los `.sql` de `servidor\` y verificar la
   migración desde la pantalla de conexión (§18, §17.4).

---

## 22. Convenciones y cómo extender

Esta sección es la **casa ordenada**: cómo se llaman las cosas, cómo se escribe el código y
las recetas para los cuatro cambios que se repiten (un campo, una ventana, un parámetro,
una regla del Excel). Sirve para que un cambio hecho dentro de un año se vea igual que todo
lo demás y funcione **con los dos motores** (SQLite y PostgreSQL, §17.3).

### 22.1 Convenciones de nombres

| Qué | Convención | Ejemplos |
| --- | --- | --- |
| Ventanas (una por módulo del menú) | `q_*.py`, y su clase `AlgoWindow` | `q_viaje.py` → `ViajeWindow`, `q_ajustes.py` → `AjustesWindow`, `q_admin.py` → `AdminWindow`, `q_bitacora.py` → `BitacoraWindow`, `q_usuarios.py` → `UsuariosWindow`, `q_conexion.py` → `ConexionWindow`, `q_login.py` → `LoginWindow` |
| Interfaz compartida | `qt_tema.py` (colores, fuentes, estilos) y `qt_comunes.py` (componentes) | `qt_comunes.py` → `TablaDatos`, `Tabla`, `Tarjeta`, `Kpi`, `Aviso`, `Insignia`, `CampoFecha`, `CampoHora`, `ComboAuto`, `FilaFiltros`, `Pagina`, `Ventana`, `Item` |
| Pruebas | `pruebas_*.py` | `pruebas_conexion.py`, `pruebas_ventanas.py`, `pruebas_qt.py`, `pruebas_horas.py`, `pruebas_excel.py`, `pruebas_rendimiento.py` |
| Funciones de `database.py` | verbo en español + a qué objeto; **132 funciones** en total | `listar_*` (15), `guardar_*` (10), `eliminar_*` (7), `actualizar_*` (5), `agregar_*` (5), `importar_*` (3), y los casos puntuales `existe_*`, `proximo_*`, `resumen_*`, `conteo_*`, `asegurar_*`, `cargar_*`, `obtener_*`, `anular_*`, `reactivar_*`, `justificar`, `login` |
| Ayudantes internos | empiezan con `_` (nada de afuera los usa) | 30 de esas 132 (`_esquema`, `_memoria`, `_filas_ajuste`, `_clave_borrador`, `_carpeta_viatico`) |
| `bd.py` (lo mínimo que habla con los motores) | nombres cortos y sin adornos | `conectar`, `motor`, `es_postgres`, `ahora`, `agrupar`, `fecha_dia`, `insert_ignorar`, `insert_actualizar`, `probar_conexion`, `estadisticas`, `cerrar_reserva` |
| Tablas y columnas | minúsculas, español, sin tildes; la columna dice **para qué** es | `viajes`, `respaldos`, `parametros`, `distancias`, `seq`; columnas `es_chofer`, `es_encargado`, `tipo_registro`, `ajuste_numero`, `pago_empleado_monto` |
| Constantes y listas fijas | MAYÚSCULAS | `MODULOS`, `GRUPOS`, `PERMISOS_MODULO`, `ARCHIVOS_MODULO`, `PARAM_COLS`, `PARAMS_INICIALES`, `KM_CUENCA`, `TIPOS_VEHICULO`, `ROL_VENDEDOR`, `ROL_JUSTIFICA`, `ROL_SUPER` |
| Herramientas y empaquetado | fuera del programa | `empaquetar_servidor.py`, `EMPAQUETAR_EXE_SERVIDOR.bat`, `herramientas\*.py` |

### 22.2 Convenciones de estilo y de código

- **Todo en español**: nombres, comentarios, docstrings y mensajes al usuario. Un mensaje
  que ve la gente dice «qué pasó» y «qué hacer», no «error 0x…».
- **Los comentarios explican el porqué, no el qué.** El sistema está lleno de párrafos que
  cuentan *por qué* una decisión se tomó así (el saludo a la base, el redondeo del cajero,
  los km que la empresa corrigió a mano). Al tocar algo, ese párrafo se actualiza: es la
  memoria del proyecto.
- **Cabecera de autoría en cada archivo y firma al final**, en `.py`, `.bat` y `.md`; las
  pone y las mantiene `herramientas\limpiar_y_firmar.py` (es idempotente: correrlo dos
  veces no duplica nada).
- **Los archivos se ordenan por bloques**, separados con una línea de `# ------------`
  (`database.py` tiene 15 bloques, `qt_comunes.py` 11, `qt_tema.py` 9).
- **Docstring de presentación** en la primera línea con el formato `archivo.py — qué hace`,
  y debajo el detalle (parámetros, ejemplos de uso).
- **Nadie abre la conexión por su cuenta**: siempre `bd.conectar()`; y para construir SQL
  que sirva a los dos motores, `bd.agrupar()`, `bd.fecha_dia()`, `bd.ahora()`,
  `bd.insert_ignorar()` e `bd.insert_actualizar()`.
- **Los datos siempre con `?`**, uno por valor, en el orden de la consulta: nunca se pega
  texto dentro del SQL (además de ser lo correcto, es lo que hace que la misma consulta
  funcione igual en SQLite y en PostgreSQL).
- **Lo que se graba, se olvida**: las funciones de `database.py` que escriben llaman a
  `olvidar_cache(...)` para las claves que tocaron (`olvidar_cache("parametros")` borra lo
  guardado de los parámetros, y una clave que termina en `:` —como `"cantones:"`— borra
  todo lo que empiece así), de modo que el dato nuevo se vea al instante y no al vencer los
  `_SEGUNDOS_MEMORIA` de 30 s (§20.2).

### 22.3 Cómo agregar un campo a una tabla (o una tabla nueva)

El sistema **se pone al día solo**: al arrancar, `init_db()` crea lo que falte y agrega las
columnas nuevas. Por eso el cambio se hace en este orden:

1. **Declarar el campo en el esquema** (`SCHEMA`, dentro de `database.py`), para que toda
   base nueva —y la base central cuando se crea por primera vez— ya nazca con él.
2. **Agregar la línea `ALTER TABLE ... ADD COLUMN ...`** a la lista `nuevas_columnas` de
   `init_db()`, que es la que arregla las bases **que ya existen**. Esa lista se aplica a
   ciegas: si la columna ya está, el error se ignora (`except: pass`) y no pasa nada.
3. **Ponerle el valor de fábrica en el propio `ALTER`** (`REAL DEFAULT 0`, `TEXT` sin
   `DEFAULT` = vacío): es lo que hace que un viático guardado **antes** del cambio siga
   abriendo sin que le falte nada.
4. **Leerlo y grabarlo** en las funciones de `database.py` que correspondan
   (`guardar_viaje`, `actualizar_viaje`, `obtener_viaje`, `filas_numero`, o las del catálogo
   que sea), con `?` y en el orden de las columnas. Si el campo es un **parámetro**, además
   va en `PARAM_COLS` y en `PARAMS_INICIALES` —el orden de esas dos listas manda— y se lee
   por `cargar_parametros()` (§10.4).
5. **Ponerlo en la ventana** que lo usa (`q_viaje.py`, `q_admin.py`, …), con los componentes
   de `qt_comunes.py` (§14.1) y los estilos de `qt_tema.py`; y si la ventana graba, que
   olvide la memoria (§22.2).
6. **Probar**: `python pruebas_ventanas.py` (que la ventana siga armando) y, si el campo
   entra en alguna cuenta, la comparación contra el Excel (§22.6).

> **Ojo con la base central.** `init_db()` solo revisa **doce columnas** contra
> `information_schema.columns` (las que hizo falta agregar cuando las bases venían del
> sistema anterior; se consulta antes para no abortar la transacción). Si el campo también
> tiene que existir en el **servidor**, hay que agregarlo allí: o se le suma la tupla a esa
> lista corta, o se corre el `ALTER TABLE` a mano / con los `.sql` de `servidor\` (§18).
> La regla práctica: **una columna nueva = esquema + `ALTER` de SQLite + `ALTER` del servidor.**

### 22.4 Cómo agregar una ventana (un módulo nuevo del menú)

1. **Crear el archivo** `q_algo.py` con la clase `AlgoWindow`. La ventana recibe
   `(menu, usuario)`; `q_menu.abrir_modulo()` la llama así y, si la firma no coincide,
   reintenta con `AlgoWindow(usuario)`.
2. **Registrarla en las tres listas de `q_menu.py`**:

   | Lista | Qué se agrega |
   | --- | --- |
   | `MODULOS` | `(clave, icono, título, descripción, ¿se ve en la barra lateral?)` |
   | `PERMISOS_MODULO` | La tupla de roles que pueden abrirla (al abrirla se pide la clave del área, §5) |
   | `ARCHIVOS_MODULO` | `clave → (archivo, clase)` |

   No hace falta tocar `GRUPOS`: cualquier módulo que no esté agrupado aparece solo en
   **«OTROS MÓDULOS»**, y así agregar un módulo no obliga a reordenar la barra lateral.
3. **Agregar el módulo a `hiddenimports` del `.spec`.** Los módulos se cargan al abrirlos
   (`importlib.import_module` con el nombre en una variable), así que PyInstaller no los ve
   solo: sin esta línea el `.exe` abre el menú y al entrar a la ventana dice «Módulo no
   disponible».
4. **Escribir el interior con lo que ya existe**: `Ventana`, `TablaDatos`, `Tabla`,
   `Tarjeta`, `Kpi`, `Aviso`, `Insignia`, `ComboAuto`, `CampoFecha`, `CampoHora`,
   `FilaFiltros` y `Pagina` de `qt_comunes.py`; colores, fuentes y estilos de `qt_tema.py`;
   y los datos **solo** por `database.py`.
5. **Probar**: `python pruebas_ventanas.py` (que se arme y cargue datos), `python
   pruebas_qt.py` (que el módulo no quede en la lista de «pendientes de migrar», que la saca
   recorriendo `ARCHIVOS_MODULO`) y `python pruebas_conexion.py` si el módulo hace consultas
   nuevas.
6. Si la ventana muestra una tabla, **el botón de Excel/CSV ya viene** con `TablaDatos`
   (§14.2); si necesita un informe aparte, va en `reportes.py` (§14.6).

### 22.5 Cómo agregar un parámetro de cálculo o un catálogo

**Un parámetro** (§10.4) son tres pasos y una prueba:

1. Agregarlo en `PARAM_COLS` (**el orden manda**: es el orden en que se leen y se graban) y
   su valor de fábrica en `PARAMS_INICIALES`.
2. Ponerle su campo y su ayuda en la pestaña **Parámetros** (`q_admin.py`, §15.1).
3. Agregar la columna con su `DEFAULT` en el `ALTER TABLE parametros ...` (§22.3).
4. Probar que la regla sigue dando lo del Excel (§22.6). Si el parámetro **cambia de
   criterio** respecto a versiones anteriores, el cambio de fábrica se aplica **una sola
   vez** y queda marcado en la tabla `seq` (`ajustes_parametros`), para no revertir lo que
   el superusuario cambie después a mano (§16.4).

**Un catálogo** (empleados, clientes, vehículos, provincias, cantones y sus km):

1. La lista de base vive en `database.py` (tabla semilla, §16.2; los km de Cuenca, en
   `KM_CUENCA`); el catálogo se completa con `asegurar_provincia` / `asegurar_canton`.
2. Las funciones `listar_*`, `agregar_*` y `eliminar_*` se escriben como las demás
   (§22.1) y **olvidan la memoria** de esa clave al grabar.
3. La pestaña va en `q_admin.py` (§15.2–§15.4), y si el catálogo también existe en Excel,
   se importa con `importar_empleados_excel`, `importar_clientes_excel` o
   `importar_distancias_excel` (§16.1, §16.3).
4. Las listas que son de fábrica y no se editan (`TIPOS_VEHICULO`) se cambian en el código,
   no en la base.

### 22.6 Cómo cambiar una regla de cálculo (y no romper el Excel)

Es la parte delicada del sistema, porque **el Excel es la especificación** (§1):

1. **La cuenta se cambia en `calculos.py`**, no en la ventana: la ventana solo dibuja lo que
   el motor devuelve (§3).
2. **Respetar las tolerancias** del motor (§10.5) y el criterio único del redondeo del
   cajero (§10.3): un redondeo por viático, no por viajero.
3. **Volver a comparar**: `python pruebas_excel.py` y, si el cambio fue de fondo,
   `herramientas\comparar_reglas_excel.py` (regla contra regla con `VIATICO 2 2026.xlsx`) y
   `herramientas\comparar_excel_viaticos.py` (§21.4).
4. **Recordar que lo guardado no se recalcula solo**: un viático ya guardado conserva los
   valores que tenía; para ponerlo al día están los ajustes (§11) y herramientas como
   `recalcular_cajero.py` (§21.4).
5. **Si cambia un criterio de fábrica**, anotarlo donde corresponda: el «por qué» en el
   código, el cambio en `HISTORIAL_DE_CAMBIOS.md` y, si es por el Excel nuevo de la
   empresa, en `documentacion\COMPARACION_REGLAS_NUEVO_EXCEL.md`.

### 22.7 Las reglas que no se rompen

Son las que sostienen todo lo demás; si un cambio obliga a saltarse una, el cambio está mal
planteado:

1. **Una sola puerta a la base**: `bd.conectar()`. Nadie abre `sqlite3` ni `psycopg2` por su
   cuenta, y los datos van siempre con `?`.
2. **La interfaz no sabe nada de la base ni de la aritmética**: pide los datos a
   `database.py` y las cuentas a `calculos.py`.
3. **Toda cuenta del viático vive en `calculos.py`** y se compara contra el Excel (§22.6).
4. **Una consulta no cambia datos.** La prueba de rendimiento contra el servidor **solo
   lee** (§20.7): se puede correr en plena jornada sin miedo.
5. **Lo que se graba, olvida la memoria** (`olvidar_cache`) y **lo que se pide a cada rato,
   se recuerda** unos segundos (§20.2).
6. **Un módulo nuevo son las tres listas de `q_menu.py` más `hiddenimports` del `.spec`**
   (§22.4). Si falta la última, el `.exe` falla solo al entrar a esa ventana.
7. **Los datos de trabajo no se tocan al probar**: toda prueba corre en su carpeta
   temporal y con su base desechable (§21.2).
8. **Todo se escribe en español, y el «por qué» queda escrito** donde se tomó la decisión.
9. **Antes de entregar, la rutina del §21.5** (pruebas → paquete → autodiagnóstico → copiar).
10. **El que cambia algo actualiza la documentación en el mismo cambio**: el «por qué» y los
    números que se citan en este documento salen del código, y si el código cambia, el
    documento queda mintiendo.

> **Nota sobre las librerías.** `requirements.txt` pide lo que hace falta para correr desde
> el código fuente: **PySide6** (obligatoria: sin ella no abre), **openpyxl** (Excel de
> empleados y clientes) y **psycopg2-binary** (solo para la base central). El manejo de
> facturas en PDF e imágenes usa **Pillow**, que el `.exe` sí lleva dentro
> (`hiddenimports`: `PIL.Image`, `PIL.PdfImagePlugin`) pero que al instalar desde el código
> fuente hay que agregar a mano (`pip install Pillow`), porque de eso dependen la conversión
> y el PDF consolidado (§13.2, §13.3).

---

## 23. Glosario

Las palabras que se usan en este documento y en el programa, con el sentido exacto que
tienen **aquí** (varias significan algo distinto en otras oficinas).

### 23.1 Palabras del negocio

| Palabra | Qué significa en este sistema | Dónde |
| --- | --- | --- |
| **Viático** | El documento que se entrega por un viaje: número, beneficiarios, fechas, valores y su cierre. En la base es **un número con varias filas** (una por viajero) | §6, §8 |
| **Viajero / fila** | Cada persona de un viático, con su sueldo, su rol en el viaje y sus valores | §6.2 |
| **Encargado** | El viajero que responde por el viático (marca `es_encargado`) | §6.4 |
| **Chofer** | El viajero que conduce (marca `es_chofer`); se usa para el combustible y el taxi | §6.4, §10 |
| **Provincia / cantón** | El destino. El **cantón** es lo que manda: de ahí salen los km y las horas de viaje | §9, §15.4 |
| **Comidas del camino** | El desayuno, el almuerzo y la merienda que se pagan por salir temprano, estar en ruta a mediodía o volver tarde | §9.4 |
| **Hospedaje** | La noche pagada, contada por fechas (`hospedaje_por_fechas`) | §10 |
| **Taxi madrugada / taxi regreso** | El taxi de la salida muy temprano y el del regreso de madrugada | §10.2 |
| **Valor a retirar en cajero** | Lo que el cajero entrega: el total del viático **redondeado una sola vez** al múltiplo del cajero | §10.3 |
| **Ajuste** | Un viático **nuevo** (con su propio número de ajuste) que corrige a otro: más días, combustible extra, peajes | §11 |
| **Anular** | Dejar un viático sin efecto sin borrarlo de la historia | §8.3, §11 |
| **Justificación** | El paso donde se rinde el viático: se cargan **los gastos y las facturas** y se cierra | §12 |
| **Comprobante / respaldo** | La factura o el recibo que se guarda como prueba de un gasto; viaja en **PDF** | §13 |
| **Consolidado** | El **PDF único** que arma el sistema con todas las facturas de un viático, en orden | §13.3 |
| **Devolución** | Lo que el viajero devuelve cuando gastó menos de lo entregado | §12.3 |
| **Pago al empleado** | Lo que la empresa le paga aparte al viajero (por ejemplo, el combustible que puso de su bolsillo) | §12.3 |
| **Cierre / nota de cierre** | La observación final con que se justifica un viático | §12.3 |
| **Bitácora** | El registro de **quién hizo qué y cuándo**, con su detalle; es la auditoría del sistema | §5, §14.5 |
| **Borrador** | Lo que se está escribiendo en una pantalla y todavía no se guarda como viático; se recupera al volver a entrar | §19 |
| **Parámetro** | Un valor de fábrica que el superusuario puede cambiar (tarifas, horas límite, velocidades, redondeo) | §10.4, §15.1 |
| **Catálogo** | Una lista que se mantiene: empleados, clientes, vehículos, provincias, cantones y sus km | §15.2–§15.4 |
| **Semilla** | La lista que el sistema trae escrita en el código y usa para **sembrar** la base la primera vez | §16.2 |
| **Numeración por año** | Los viáticos se numeran 1, 2, 3… **dentro de cada año**, y el número visible se muestra como `001-2026` | §7 |
| **Superusuario** | El rol con permiso para auditoría, usuarios y conexión (y para todo lo demás) | §5 |

### 23.2 Palabras técnicas

| Palabra | Qué significa en este sistema | Dónde |
| --- | --- | --- |
| **Capa** | Cada uno de los tres pisos del sistema: **motor de cálculo** (`calculos.py`), **datos** (`bd.py` + `database.py`) e **interfaz** (`main_qt.py`, `q_*.py`, `qt_*.py`) | §3 |
| **Motor de base de datos** | El programa que guarda los datos: **SQLite** (un archivo, local) o **PostgreSQL** (central, en el servidor). Lo decide `config.json`; `bd.motor()` lo dice | §17.3 |
| **Base local / base central** | La de cada computadora (archivo) y la del servidor (todos escriben en ella) | §17, §18 |
| **`config.json`** | El archivo de configuración que va junto al programa: motor, datos del servidor, carpeta de respaldos, zoom | §17.1 |
| **Carpeta de datos** | Dónde vive la base local y lo que se guarda (se puede mover con `VIATICOS_DATA`) | §17.2 |
| **Saludo a la base** | Lo que cuesta **abrir o reconectar** una conexión (sobre todo contra el servidor). Es el costo que §20 ataca | §20.1 |
| **Reserva de conexión** | La conexión que se deja **abierta y marcada** mientras el usuario trabaja, para no saludar a la base en cada consulta; se cierra sola si nadie la toca en `_QUIETA_SEGUNDOS` (20 s) | §20.1 |
| **Memoria corta / caché** | Lo que el sistema recuerda unos segundos en vez de volver a preguntar: catálogos y parámetros (`database._MEMORIA`, 30 s), configuración (`configuracion._CACHE`) y las listas desplegables (`ComboAuto`, 5 s) | §20.2 |
| **Índice** | La lista ordenada que tiene la base para encontrar filas sin recorrer toda la tabla | §20.5 |
| **Tolerancia** | La diferencia de centavos que el motor acepta al comparar con el Excel | §10.5 |
| **Migración** | Pasar los datos de una base a otra (por ejemplo, de la local a la central) sin perder nada | §18 |
| **`seq`** | La tabla de **secuencias y marcas**: el último número de viático de cada año y las marcas de lo que ya se aplicó una sola vez | §16.4 |
| **`parametros`** | La tabla donde vive **una sola fila** (id = 1) con todos los valores de fábrica ajustables | §10.4, §15.1 |
| **`.exe` / empaquetado** | El programa convertido en un solo archivo con PyInstaller (`empaquetar_servidor.py`, `.spec`), para copiarlo a las computadoras sin instalar Python | §17 |
| **`hiddenimports`** | La lista del `.spec` con los módulos que PyInstaller **no ve solo**, porque se cargan al abrirlos | §22.4 |
| **Autodiagnóstico** | La revisión que hace el `.exe` **sin abrir ventanas** y escribe en `autodiagnostico.txt` | §21.3 |
| **Prueba (`revisar`)** | Cada comprobación suelta de las `pruebas_*.py`: imprime `OK`/`FALLA` y cuenta el resultado | §21.1, §21.2 |
| **Offscreen** | Correr Qt **sin pantalla** (las pruebas arman las ventanas sin que se vean): así se pueden correr en el servidor o por escritorio remoto | §21.2 |
| **Herramienta** | Programa **fuera** del sistema (`herramientas\`): compara contra el Excel, arma los catálogos, firma el proyecto. No se empaqueta ni se copia a las PC | §21.4, §22.1 |
| **Rol** | El perfil de un usuario: vendedor, justificación o superusuario | §5 |
| **Área** | Un módulo del menú. Al abrirlo se pide **la clave de quien entra**, y solo pasa el rol que corresponde | §5 |
| **Respaldo** | Cuidado, dos sentidos: (1) el **comprobante/factura** de un gasto (tabla `respaldos`, §13) y (2) la **copia de seguridad** de la base (pantalla de conexión, §17.4) | §13, §17.4 |
| **Excel nuevo / Excel histórico** | El formato que la empresa usa hoy (`VIATICO 2 2026.xlsx`, con las columnas calculadas por día) y el formato viejo (una hoja por viático, con `VALOR ENTREGADO`) | §16, §21.4 |
| **Zoom** | El tamaño de pantalla que cada computadora fija para sí misma desde la pantalla de conexión | §17.4 |

---

## 24. Apéndice: función → responsabilidad

Para responder rápido «¿quién hace esto?»: primero el **archivo**, después la **función**
(los nombres van como están en el código, en el orden en que aparecen dentro del archivo).
Las que empiezan con `_` son **internas** (§22.1), y varias funciones van agrupadas en una
fila cuando comparten la misma responsabilidad.

### 24.1 `database.py` — el negocio y los datos

| Funciones | Responsabilidad |
| --- | --- |
| `_memoria`, `olvidar_cache`, `_copiar` | La **memoria corta**: recordar catálogos y parámetros 30 s, borrarlos al grabar y devolver copias para que nadie los modifique sin querer (§20.2) |
| `carpeta_app`, `recurso`, `dir_datos` | Las tres carpetas: dónde está el programa, dónde sus recursos (logo, `excel\`) y dónde viven los datos (§17.2) |
| `conectar`, `cerrar_conexiones` | La única puerta a la base (delegan en `bd.py` y usan la reserva de conexión, §20.1) |
| `motor`, `es_postgres`, `descripcion_conexion`, `probar_conexion` | Qué motor se está usando, si es el servidor, el texto que se muestra en la pantalla de conexión y la prueba de que responde (§17.3, §17.4) |
| `_esquema`, `init_db` | El esquema en el dialecto del motor y el **arranque de la base**: crear lo que falte, agregar columnas nuevas, migraciones y valores de fábrica (§22.3) |
| `_archivo_de_recursos`, `_cargar_catalogos_iniciales`, `_reparar_catalogo_cantones` | La **carga inicial** de los catálogos desde `excel\` (una sola vez) y la reparación de provincias y cantones (§16.3) |
| `_migrar_numeracion_por_anio`, `_migrar_usuarios`, `_reparar_rutas_respaldos` | Migraciones y reparaciones automáticas: numeración por año (§7), usuarios con clave cifrada (§5) y rutas de los respaldos (§13.4) |
| `_next`, `hora_local`, `anio_actual`, `anio_de_fecha` | Ayudantes de fecha y de secuencias: la hora local del sistema, el año en curso y el año de una fecha cualquiera |
| `clave_viatico`, `anio_de`, `numero_visible`, `etiqueta_numero`, `db_etiqueta_archivo` | La **clave interna** de un viático (`año · 1000 + número`) contra el **número visible** (`001-2026`) y el nombre del archivo de la base (§7) |
| `valor_de` | Leer una columna de una fila sin que el programa se caiga si la columna no está |
| `proximo_numero`, `numeraciones`, `fijar_inicio` | La **numeración por año**: qué número sigue, el listado de cada año y el número inicial que el superusuario puede fijar (§7) |
| `listar_empleados`, `_leer_empleados`, `agregar_empleado`, `eliminar_empleado` | El catálogo de **empleados** (§15.2) |
| `listar_vehiculos`, `_leer_vehiculos`, `buscar_vehiculo_por_placa`, `agregar_vehiculo`, `eliminar_vehiculo` | El catálogo de **vehículos** (placa, tipo y chofer), con la búsqueda por placa que usa la pantalla de viáticos (§15.3) |
| `listar_provincias`, `_leer_provincias`, `asegurar_provincia`, `asegurar_canton` | **Provincias y cantones**: listarlas y crearlas cuando aparecen en un Excel o en un viático (§15.4) |
| `listar_clientes`, `_leer_clientes`, `agregar_cliente`, `eliminar_cliente`, `existe_cliente` | El catálogo de **clientes** (§15.2) |
| `listar_cantones`, `_leer_cantones` | Los cantones de una provincia (§15.4) |
| `_leer_excel_columna`, `_a_numero`, `importar_empleados_excel`, `importar_clientes_excel`, `_insertar_clientes`, `_leer_excel_distancias`, `_insertar_distancias`, `importar_distancias_excel` | La **importación desde Excel**: leer la columna que corresponde (buscándola por palabras clave) y cargar empleados, clientes y distancias con sus km y horas (§15.2, §16.1) |
| `_rutas`, `_leer_rutas`, `km_para`, `horas_para`, `set_distancia`, `listar_distancias` | Las **distancias**: km y horas de viaje por cantón, incluidas las rutas propias cargadas a mano (§9, §15.4) |
| `listar_usuarios`, `existe_usuario`, `agregar_usuario`, `actualizar_usuario`, `eliminar_usuario` | El catálogo de **usuarios**: altas, cambios de clave y de rol, y bajas (§5) |
| `_resumen_clave`, `cifrar_clave`, `es_clave_cifrada`, `clave_correcta` | Las **claves cifradas**: cómo se guardan, cómo se reconocen las viejas y cómo se comprueban (§5) |
| `login` | El ingreso: comprobar usuario, clave y rol, y registrar el inicio de sesión |
| `registrar_bitacora`, `listar_bitacora`, `usuarios_bitacora`, `acciones_bitacora` | La **bitácora**: anotar cada acción y consultarla con sus filtros (§14.5) |
| `cargar_parametros`, `_leer_parametros`, `guardar_parametros` | Los **parámetros** de cálculo: leerlos (con la memoria corta) y grabarlos (§10.4, §15.1) |
| `guardar_viaje`, `_insertar_filas`, `actualizar_viaje`, `_estado_viaje`, `_restaurar_cierre` | **Grabar** un viático nuevo (cabecera y una fila por viajero, en una sola transacción) y volver a grabarlo al editarlo, reponiendo el cierre de la justificación que la pantalla no toca (§8) |
| `guardar_ajuste_viaje`, `actualizar_ajuste_viaje`, `proximo_ajuste`, `eliminar_ajuste`, `filas_originales`, `conteo_ajustes`, `ajustes_viaje` | Los **ajustes**: grabarlos, reeditarlos, borrarlos, saber qué número de ajuste toca y comparar contra las filas originales (§11) |
| `actualizar_recibos`, `guardar_pago_empleado`, `guardar_devolucion` | Los cierres de plata: los números de recibo del viático, el pago al empleado y la devolución (§12.3) |
| `listar_viajes`, `listar_viaticos_unico`, `filas_numero`, `obtener_viaje` | **Consultar**: la lista de viáticos por estado, los que no tienen ajuste, las filas de un viático y uno solo con su cabecera (§8.2) |
| `guardar_elaborado_por`, `guardar_nota_cierre`, `justificar`, `anular_viaje`, `reactivar_viaje` | El **estado** del viático: quién lo elaboró, la nota de cierre, JUSTIFICAR, anular y volver a ponerlo pendiente (§8.3, §12.3) |
| `guardar_ajuste`, `listar_ajustes` | La tabla `ajustes` **heredada**, que se conserva por compatibilidad (§11.5) |
| `resumen_viaticos` | El **resumen por estado** que se ve en la Justificación (§12.4) |
| `guardar_gasto`, `actualizar_gasto`, `eliminar_gasto`, `listar_gastos`, `totales_gastos` | Los **gastos y facturas** de la justificación, y sus totales (§12.2) |
| `_carpeta_viatico`, `_nombre_libre`, `_a_pdf`, `agregar_respaldo` | Guardar un **comprobante**: la carpeta del viático, un nombre que no choque, la conversión a PDF y su fila en la base (§13.1, §13.2) |
| `contenido_respaldo`, `ruta_para_abrir`, `listar_respaldos`, `eliminar_respaldo`, `listar_respaldos_completo`, `listar_todos_respaldos` | **Ver y ordenar** los comprobantes: sacarlos de la base (modo «en la base»), abrir los de la carpeta (modo «carpeta»), listarlos, borrarlos y traer todos los del viático (§13.1, §13.5) |
| `consolidar_respaldos_pdf` | El **PDF consolidado**: un solo documento con todos los comprobantes de un viático, en orden (§13.3) |
| `_clave_borrador`, `guardar_borrador`, `leer_borrador`, `borrar_borrador`, `usuarios_con_borrador`, `borrar_borradores_viejos` | Los **borradores**: guardar lo que se está escribiendo por usuario y pantalla, recuperarlo, borrarlo al limpiar el formulario y hacer la limpieza automática de los viejos (§19) |

### 24.2 Los módulos de apoyo (datos, cálculo, estilo, informes)

**`bd.py` — lo mínimo que habla con los dos motores** (nada de reglas de negocio aquí):

| Funciones | Responsabilidad |
| --- | --- |
| `class Conexion` | El objeto que envuelve la conexión real y **traduce**: el mismo `execute`/`executescript` sirve para SQLite y para PostgreSQL (§17.3) |
| `conectar`, `_abrir_guardada`, `_abrir_cruda` | Abrir la conexión: primero la **reserva** que ya está abierta; si no, una nueva |
| `_cruda_sqlite`, `_conectar_sqlite`, `_cruda_postgres`, `_conectar_postgres` | Los dos caminos de conexión, con el tiempo de espera corto (`connect_timeout=6`) para que un servidor apagado no cuelgue el programa (§20.1) |
| `_reserva_activa`, `_clave_base`, `_probar_si_estuvo_quieta`, `_olvidar_de_reserva`, `cerrar_reserva` | La **reserva de conexión**: dejarla abierta mientras se trabaja, cerrarla si nadie la toca en `_QUIETA_SEGUNDOS` (20 s) y soltarla cuando el usuario termina (§20.1) |
| `motor`, `es_postgres`, `ahora`, `agrupar`, `fecha_dia`, `_a_postgres` | Saber qué motor está en uso y escribir SQL que sirva a los dos: la hora, la agrupación de textos, el día de una fecha y los arreglos de sintaxis hacia PostgreSQL |
| `insert_ignorar`, `insert_actualizar` | El `INSERT` que **no falla si ya existe** y el que **actualiza si ya existe**, cada uno en la forma de su motor (§17.3) |
| `probar_conexion` | Probar unos datos de conexión **sin guardarlos**: es la prueba de la pantalla de conexión (§17.4) |
| `estadisticas`, `reiniciar_estadisticas` | El **contador** de consultas, conexiones y tiempos que lee el autodiagnóstico y usa la prueba de rendimiento (§20.7) |

**`configuracion.py` — `config.json` y las carpetas:**

| Funciones | Responsabilidad |
| --- | --- |
| `carpeta_app`, `ruta_config`, `ruta_config_usuario`, `carpeta_recursos`, `dir_datos` | Dónde está el programa, dónde su `config.json` (junto al `.exe` o en el perfil del usuario), dónde sus recursos y dónde los datos (§17.1, §17.2) |
| `_leer_del_disco`, `_mezclar`, `leer`, `olvidar_cache` | Leer la configuración **una sola vez** y tenerla en memoria (`_CACHE`), mezclando lo que trae por defecto con lo que el archivo dice; `olvidar_cache` la relee (§20.2) |
| `guardar` | Grabar los cambios de configuración (lo hace la pantalla de conexión) |
| `motor`, `es_postgres`, `modo_respaldos`, `carpeta_respaldos` | Las cuatro respuestas que más se piden: qué motor, si es el servidor, si los comprobantes van a la base o a una carpeta, y en qué carpeta (§13.1) |
| `describir` | El texto de una línea con la conexión en uso, que aparece en la pantalla de conexión y en el autodiagnóstico (§17.4) |

**`autor.py`, `colores.py`, `migracion.py`:**

| Funciones | Responsabilidad |
| --- | --- |
| `autor.creditos`, `autor.firmado`, `autor.sellar_bitacora` | La autoría: el texto de créditos, si la firma del programa está completa y la constancia fechada en la bitácora (§5) |
| `colores.py` (solo constantes) | La **paleta** en un solo lugar (azul y amarillo de la marca, grises, rojo, verde, naranja): la usan el tema en pantalla y también `reportes.py`, para que lo impreso salga con los mismos colores |
| `migracion._conectar_sqlite_local`, `_columnas`, `_existe_tabla`, `_reiniciar_secuencia`, `_contenido_respaldo` | Los ayudantes de la migración: abrir la base local, saber qué columnas tiene una tabla, si existe, dejar bien las secuencias de PostgreSQL y sacar el contenido de un comprobante (§18.2) |
| `migracion.migrar`, `migracion.resumen_local` | La **migración a la base central** (con progreso) y el resumen de lo que hay en la base local antes de migrar (§18.1, §18.4) |

**`calculos.py` — el motor: las fórmulas del Excel** (§9, §10). No depende de la base ni de
la interfaz: recibe datos y devuelve valores.

| Funciones | Responsabilidad |
| --- | --- |
| `class DatosViaje` | El **paquete** con los datos de un viático que recibe el motor (fechas, horas, km, cantón, parámetros del viaje) |
| `calcular(v, p)` | **La cuenta completa**: devuelve todas las columnas del Excel para cada viajero (comidas, taxis, hospedaje, combustible, total, valor a entregar) (§10.1) |
| `redondear_cajero(total, multiplo)` | El **redondeo del cajero**: al múltiplo configurado y **una sola vez por viático** (§10.3) |
| `cajero_del_grupo(filas, p)` | Quién **retira en caja** y cuánto le corresponde por el grupo (§10.1) |
| `dias_de_viaje(v)` | Cuántos **días** dura el viaje, contados desde/hasta la fecha |
| `comida_dias(v, p, clave_valor, clave_limite, ...)` | Los **días en que corresponde cada comida** (desayuno, almuerzo, merienda) según las horas del viaje y la hora límite del parámetro (§9.4) |
| `noches_de_hospedaje(v, p)` | Cuántas **noches** se pagan: por fechas o por la regla que diga el parámetro (§10.2) |
| `hora_limite(valor, por_defecto)` | Convertir el texto de un parámetro de hora (`"21:00"`) a una hora real, con su valor por defecto si viene vacío |
| `horas_texto(horas, sufijo)`, `horas_de_texto(texto)` | **Mostrar y leer** horas en formato `h:mm` (lo que se ve en pantalla y lo que se escribe en un campo) |
| `_numero(valor, por_defecto)`, `_activado(p, clave, por_defecto)` | Ayudantes: leer un valor numérico sin caerse y saber si un parámetro está activado |

**`qt_tema.py` — colores, tamaños y estilos** (todo lo visual en un solo lugar):

| Funciones | Responsabilidad |
| --- | --- |
| `aplicar_tema(app)`, `hoja_estilo`, `paleta_clara` | La **hoja de estilos** del programa, que se aplica una sola vez al abrir y viste todas las ventanas (§14.1) |
| `color_estado(estado)`, `texto_contraste(fondo)`, `estilo_insignia(fondo, color, radio)` | Los **colores por estado** del viático (pendiente, justificado, anulado) y el texto que se lee bien encima de cada color (§8.3) |
| `fuente(tamano, negrita)`, `px(valor, minimo)`, `factor()` | Las **fuentes** y la conversión de medidas según el **zoom** de esa computadora (§17.4) |
| `zoom_guardado()`, `guardar_zoom(zoom)` | Leer y guardar el **zoom** de esa PC (queda en `config.json`) |
| `preparar_dpi()`, `icono_app()`, `logo_pixmap(alto)` | La preparación de pantallas de alta resolución, el icono de las ventanas y el **logo** |
| `formato_moneda(valor)`, `formato_fecha(iso)` | Cómo se escriben los **valores** ($ 1.234,56) y las **fechas** (dd/mm/aaaa) en todo el programa (§14.1) |

**`main_qt.py` — el arranque** (§4):

| Funciones | Responsabilidad |
| --- | --- |
| `main()` | Crea la aplicación, aplica el tema, revisa la base (`_asegurar_conexion`), hace la limpieza de borradores viejos y abre el menú |
| `autodiagnostico()` | La revisión completa del §21.3, que se escribe en `autodiagnostico.txt` cuando el `.exe` se ejecuta con `VIATICOS_SELFTEST=1` |
| `_asegurar_conexion()`, `_aviso_error(detalle)` | Preparar la base al arrancar y mostrar el aviso con el detalle técnico cuando algo falla (§17.5) |

**`qt_comunes.py` — las piezas que se repiten en todas las ventanas** (§14):

| Funciones | Responsabilidad |
| --- | --- |
| `margenes(layout, ...)`, `fila(*widgets)`, `columna(*widgets)`, `linea()` | El **acomodo**: márgenes estándar, filas y columnas de controles y la línea separadora, para que todas las pantallas se vean igual |
| `etiqueta(...)`, `rejilla(filas, ...)` | La **etiqueta** estándar (título, rúbrica y ayuda azul) y la **rejilla** de filas «etiqueta + campo» que usan los formularios |
| `normalizar_columnas`, `datos_columna` | Los ayudantes de las tablas: aceptar columnas escritas de varias formas y sacar el dato de una fila (ya venga como tupla o como diccionario) |
| `boton`, `boton_primario`, `boton_amarillo`, `boton_secundario`, `boton_borde`, `boton_peligro`, `boton_plano`, `boton_herramienta`, `boton_menu` | Los **botones** en sus estilos: el amarillo para la acción principal, el plano para lo secundario, el rojo para lo peligroso y el de menú para la barra lateral (§14.1) |
| `campo`, `campo_clave`, `campo_entero`, `campo_decimal`, `campo_area`, `combo`, `poner_combo`, `combo_auto`, `check`, `radios` | Los **campos**: de texto, de clave, de números enteros y decimales, de varias líneas, las listas desplegables (con búsqueda o con lista de la base), la casilla y los botones de opción (§14.2, §14.3) |
| `nombre_archivo`, `pedir_ruta_guardar`, `_valor_para_archivo`, `_titulo_hoja`, `exportar_excel`, `exportar_csv`, `exportar_excel_documento`, `abrir_archivo` | **Exportar y abrir**: limpiar el nombre del archivo, la ventana «Guardar como», el Excel o CSV de una tabla, el Excel de un documento armado y abrir lo exportado con el programa del sistema (§16.4, §19) |
| `_caja`, `informar`, `aviso`, `error`, `confirmar`, `confirmar_peligro`, `preguntar`, `preguntar_largo`, `preguntar_valor` | Los **avisos y preguntas** con el aspecto del sistema: informar, advertir, avisar de un error, confirmar una acción, confirmar algo peligroso y pedir un texto, un texto largo o un valor (§14.4) |
| `etiqueta_sesion(usuario, extra)` | El texto de la **barra inferior**: quién entró, con qué rol y a qué base está conectado (§14.5) |

**`reportes.py` — los informes que se imprimen o se guardan en PDF** (§12.5). Arma un
documento HTML con los colores de la marca y lo abre para imprimir:

| Funciones | Responsabilidad |
| --- | --- |
| `_num_txt(numero)`, `fmt(valor)`, `fmt_f(iso)` | Escribir el número del viático, los valores (con dos decimales) y las fechas en el informe como se ven en pantalla |
| `_base_css()`, `_head(titulo)`, `_abrir(html, nombre)` | El estilo del documento, su encabezado y el paso final de abrirlo |
| `_cabecera_viatico`, `_tabla_viatico`, `_firmas_viatico` | Las tres piezas de un informe de viático: los datos generales, la **tabla** de viajeros con sus valores y el espacio de **firmas** |
| `imprimir_viatico(numero, cab, filas, general=False)` | El **informe del viático** (el `general` cambia el título cuando se imprime para revisión) |
| `imprimir_justificacion(numero, cab, filas, gastos, respaldos, devolucion)` | El **informe de la justificación**: gastos, comprobantes y devolución (§12.5) |
| `imprimir_bitacora(filas, filtros)` | El **informe de la bitácora**, con los filtros usados anotados arriba (§14.5) |

**`empaquetar_servidor.py` — la herramienta del administrador** (§18.3):

| Funciones | Responsabilidad |
| --- | --- |
| `ip_valida(texto)`, `buscar(patron, texto)`, `escribir_ejemplo(carpeta, datos, simular)`, `cambiar_fabrica(ip, puerto, clave, simular)` | Encontrar y **cambiar la «dirección de fábrica»** del servidor dentro de los ejecutables, y dejar escrito el archivo de ejemplo con los datos de la base central |
| `empaquetar(simular)`, `main()` | Armar el **paquete del servidor** (base + programa + instrucciones) y el punto de entrada de la herramienta; el `simular=True` permite ver qué haría sin tocar nada |

### 24.3 Las ventanas (`q_*.py`)

Todas las ventanas de módulo se construyen sobre el **marco común** `C.Ventana` (de
`qt_comunes.py`): título, subtítulo, botón «← Volver», tarjetas y zoom. Lo único que cambia
es lo que va adentro. Quién puede abrir cada una está en `PERMISOS_MODULO` (§6).

| Archivo | Ventana o clase | Responsabilidad |
| --- | --- | --- |
| `q_menu.py` | `MenuPrincipal`, `grupos_de_modulos()` | El **menú principal**: barra lateral agrupada («Trabajo del día» y «Superusuario»), pide la clave del área al abrirla y carga cada módulo al abrirlo. Las listas `MODULOS`, `GRUPOS`, `PERMISOS_MODULO`, `ARCHIVOS_MODULO` y `AYUDAS` son el catálogo de módulos: qué hay, quién lo abre y con qué archivo y clase (§6, §22.4) |
| `q_login.py` | `LoginWindow` | El **ingreso** al sistema: usuario y clave, elección de base local o central y el cambio de clave cuando toca (§5) |
| `q_viaje.py` | `ViajeWindow` | **Generar / revisar / ajustar viáticos**: la pantalla principal, con la cabecera, los viajeros, el cálculo en vivo, el historial, anular y reactivar, y el paso a justificar (§8) |
| `q_viaje.py` | `DialogoHorario` | El **horario propio de un viajero**: el bus no sale ni llega a la misma hora que los demás, así que aquí se ponen sus horas y su total de comidas y hospedaje sale distinto (§9.3) |
| `q_ajustes.py` | `AjustesWindow` | **Justificar viáticos**: el original, sus ajustes, los gastos y facturas, los comprobantes, el cierre y las devoluciones (§12) |
| `q_ajustes.py` | `VentanaOriginal` | Ver **en solo lectura** el viático original junto con sus ajustes, para comparar sin poder cambiar nada (§11.4) |
| `q_respaldos.py` | `RespaldosWindow` | Los **comprobantes guardados**: buscarlos por viático, verlos, abrirlos, exportarlos y armar el PDF consolidado (§13) |
| `q_admin.py` | `AdminWindow`, `_PanelLista` | **Parámetros, sedes, empleados, clientes, vehículos y rutas**; `_PanelLista` es la pestaña que se repite (lista, campo de escritura y los botones Agregar, Eliminar e Importar Excel) (§15) |
| `q_bitacora.py` | `BitacoraWindow` | El **informe de actividad (auditoría)**: los filtros por usuario, acción y fechas, y el informe imprimible (§14.5) |
| `q_usuarios.py` | `UsuariosWindow` | Los **usuarios del sistema**: altas, cambio de clave y de rol, y bajas (§5) |
| `q_conexion.py` | `ConexionWindow` | La pantalla del **superusuario**: qué base está en uso, los datos del servidor, dónde se guardan los respaldos, la numeración de viáticos y el zoom de esa computadora (§17.4) |
| `q_conexion.py` | `VentanaServidor` | La que **aparece sola** cuando la base central no responde: escribir otra dirección del servidor o seguir trabajando con la base local (§17.5) |
| `bd.py` | `Conexion` | El objeto que envuelve la conexión real y **traduce** el SQL, para que las consultas de `database.py` sirvan igual en SQLite y en PostgreSQL (§17.3) |

### 24.4 Las pruebas y las herramientas

**Las pruebas** (`pruebas_*.py`, §21.1). Se ejecutan con el Python del sistema desde la
carpeta del programa; el resultado esperado y las cifras reales están en el §21.2.

| Archivo | Qué comprueba |
| --- | --- |
| `pruebas_horas.py` | Las **horas y las comidas**: los casos de horarios, horas límite y noches de hospedaje del §9.4, que es donde más fácil se equivoca un cálculo |
| `pruebas_excel.py` | El **Excel**: exportar una tabla y volver a leerla, con libros de verdad |
| `pruebas_conexion.py` | La **base**: la reserva de conexión, los dos motores y la traducción del SQL |
| `pruebas_qt.py` | Que las **pantallas se puedan construir**: recorre las ventanas y comprueba que se dibujen (60 pantallas, §21.2) |
| `pruebas_ventanas.py` | El **recorrido completo**: abrir cada ventana, usarla un poco y cerrarla sin errores |
| `pruebas_rendimiento.py` | Los **tiempos** de las consultas más usadas con la base ya llena (§20.7). No comprueba nada: mide |

**Las herramientas** (`herramientas\`, §21.4). Son para el desarrollador o para una
reparación puntual: no forman parte del programa que usa la empresa.

| Herramienta | Para qué sirve |
| --- | --- |
| `ver_excel.py` | Abrir un Excel cualquiera y ver sus columnas y sus filas, para revisarlo antes de importarlo |
| `comparar_reglas_excel.py` | Comparar las **reglas de cálculo** del sistema contra las del Excel original |
| `comparar_excel_viaticos.py` | Comparar, uno por uno, los viáticos calculados por el sistema contra los del Excel |
| `generar_excel_tiempos.py`, `tiempos_de_viaje.py` | Armar el Excel de **tiempos de viaje** por cantón que después se importa como horas |
| `preparar_distancias_excel.py`, `preparar_distancias_doc.py` | Preparar el listado de **distancias** (km y horas) en Excel y en documento, para revisarlo con quien conoce las rutas |
| `recalcular_cajero.py` | Volver a aplicar el **redondeo del cajero** (§10.3) sobre lo que ya está grabado |
| `viaticos_148_149.py` | Revisar y corregir dos viáticos concretos (el 148 y el 149), que se usaron como caso de prueba |
| `limpiar_y_firmar.py` | Dejar el programa **listo para entregar**: limpiar los datos de prueba, revisar la firma del programa y sellar la bitácora (§21.4) |

---

*Fin del documento.*






