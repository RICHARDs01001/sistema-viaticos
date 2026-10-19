<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Servidor de la base de datos (PostgreSQL directo en Windows)

> **La IP del servidor se escribe en cada computadora** (y queda dentro del `.exe`). En esta guía
> aparece `192.168.22.123` como ejemplo: cambie ese número por el de su servidor. Ojo: una IP
> terminada en **`.1`** es el **router** de la red, así que no sirve para el servidor.
>
> Las tablas las crea el propio programa la primera vez que se conecta.

> **Qué es esto:** la puesta en marcha, desde cero, de la **máquina que tendrá la base central**
> Al final: **qué hacer si el puerto 5432 ya está ocupado**, qué se cambia en cada PC y la hoja de
> control de la prueba.
>
> Todo se escribe en **PowerShell como Administrador** (Inicio → `powershell` → clic derecho →
> *Ejecutar como administrador*).

## Datos de esta instalación (los mismos en todas las PC)

| Dato | Valor | Dónde se escribe |
| --- | --- | --- |
| **IP del servidor** | `192.168.22.123` | pantalla **🔌 CONEXIÓN / BASE DE DATOS** de cada PC |
| **Puerto** | `5432` — o `5433` si el 5432 ya está ocupado | igual en todas |
| **Base** | `viaticos` | igual en todas |
| **Usuario** | `miempresa` | igual en todas |
| **Clave de `miempresa`** | `miempresa` (cámbiala si quieres) | igual en todas |
| **Clave de `postgres`** | `___________________` (la que se elige al instalar) | solo en el servidor |
| **Versión de PostgreSQL** | `16`, `17` o `18` → en los comandos es **`<V>`** | — |

> 🔴 En todos los comandos, **`<V>`** se reemplaza por el número de la versión instalada: si instalaste
> la 18 pones `18`, si la 16 pones `16`. Se ve en la carpeta `C:\Program Files\PostgreSQL\`.
>
> **Las tablas de la base NO se crean a mano:** las crea el propio programa la primera vez que se
> conecta (empleados, clientes, viáticos, parámetros…). Aquí solo se prepara la "casa" (usuario, base
> y permiso de red).

---

## PASO 0 — Antes de tocar nada (5 minutos, EN LA MÁQUINA NUEVA)

```powershell
# a) ¿Cuál es la IP de esta máquina de verdad?
ipconfig | Select-String "IPv4", "Puerta de enlace"
#    Debe salir:  IPv4 . . . . : 192.168.22.123
#    Si sale otra cosa, ESA es la IP real de esta PC: úsela en todo (o póngale la fija del A8).
```

> ⚠️ **Ojo con la IP `.1`.** En casi todas las redes la dirección `…1` es **el router**, no una PC. Si
> en el `ipconfig` de esta máquina **no** aparece la IP que se acordó (`192.168.22.123`), entonces hay
> que ponerla (con la IP fija del **A8**) o usar la que la máquina tenga hoy. Compruebe también que la
> **puerta de enlace** no sea la misma que se le puso a esta PC (eso sería un **conflicto de IP** y
> ninguna de las dos funcionaría).
> Un truco: `ping -a 192.168.22.1` y, desde otra PC, `ping 192.168.22.1` — si contesta el router, ese
> `…1` está ocupado. Usa la IP real que salga en `ipconfig` en **todos** los comandos y en las PC.

```powershell
# b) ¿Ya hay algo escuchando en el 5432?   (NO debe salir nada)
netstat -ano | Select-String ":5432"
#    Si sale LISTENING con un PID, anote ese número y siga con (c).

# c) ¿Qué programa es ese PID?
Get-Process -Id <PID> | Select-Object Id, ProcessName, Path
#    postgres.exe  -> ya hay un PostgreSQL instalado (ver «PUERTO OCUPADO», caso 1)
#    otra cosa     -> ver caso 3

# d) ¿Hay reglas de firewall viejas con ese puerto?
Get-NetFirewallRule -DisplayName "*5432*" | Format-Table DisplayName, Enabled, Action -AutoSize

# e) Nombre de la tarjeta de red y memoria (se usa más adelante)
Get-NetAdapter | Format-Table Name, Status, LinkSpeed -AutoSize
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
```

---

# Instalación del servidor, paso a paso (PostgreSQL directo en Windows)

Es el que el proyecto probó en la laptop-servidor y el que conviene aquí: **arranca como servicio de
Windows** (nadie tiene que abrir sesión) y **no necesita reiniciar** la máquina.

## A1 — Instalar PostgreSQL

1. Descarga **PostgreSQL para Windows** (instalador EDB): `https://www.postgresql.org/download/windows/`
   → *Download the installer*. Sirve la **16, 17 o 18**: el sistema usa SQL estándar y no depende de la
   versión. Si el servidor no tiene Internet, se descarga en otra PC y se pasa por USB.
2. Ejecuta el instalador y acepta lo que viene por defecto, **cambiando solo esto**:
   - **Password:** la clave del usuario `postgres` → *anótala* (la pedirá `psql` después).
   - **Port:** `5432` (si el instalador avisa que está ocupado, pon `5433` y sigue el apartado
     **PUERTO OCUPADO** al final de esta guía).
   - **Locale:** `Spanish, Ecuador` (o *Default locale*, da igual).
   - **Stack Builder** al final: **desmárcalo** (no hace falta).
3. Comprueba que quedó bien:

```powershell
Get-Service postgresql* | Format-Table Name, Status, StartType
#    Debe salir:  postgresql-x64-18   Running   Automatic
#    (si Status no dice Running:   Start-Service postgresql-x64-<V>)

# ¿Qué versión es exactamente?  (pide la clave de postgres)
& "C:\Program Files\PostgreSQL\<V>\bin\psql.exe" -U postgres -c "select version();"
#    Debe salir: PostgreSQL 18.x ...
```
> Si la ruta no existe, la carpeta se llama `16`, `17` o `18`: corrige el número y repite.
> Servicio en **Automatic** = cuando se reinicie el servidor, la base arranca sola. ✔

## A2 — Crear el usuario y la base que usa el programa

```powershell
$env:PGPASSWORD = "tu-clave-de-postgres"                    # la del instalador
$psql = "C:\Program Files\PostgreSQL\<V>\bin\psql.exe"

# ¿Qué hay ya creado? (aquí NO se borra nada)
& $psql -U postgres -c "\l"      # lista de BASES
& $psql -U postgres -c "\du"     # lista de USUARIOS

# Si NO aparecen, se crean (si ya existen, el comando dirá "ya existe": buena señal)
& $psql -U postgres -c "CREATE USER miempresa WITH PASSWORD 'miempresa';"
& $psql -U postgres -c "CREATE DATABASE viaticos OWNER miempresa ENCODING 'UTF8';"
& $psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE viaticos TO miempresa;"

# Comprobar
& $psql -U postgres -c "\l"  | Select-String "viaticos"
& $psql -U postgres -c "\du" | Select-String "miempresa"

# Probar con el usuario del programa (debe entrar y decir "viaticos")
$env:PGPASSWORD = "miempresa"
& $psql -U miempresa -h 127.0.0.1 -d viaticos -c "select current_database(), current_user;"
$env:PGPASSWORD = ""
```
> Si en vez de `miempresa` quieres otra clave, ponla aquí **y la misma** en cada PC.
> Con la versión 15 o superior la base queda a nombre de `miempresa` y ese usuario ya puede crear las
> tablas (el `GRANT` de arriba es por si acaso). **Las tablas las crea el propio programa.**

## A3 — Que escuche a toda la red (`postgresql.conf`)

```powershell
notepad "C:\Program Files\PostgreSQL\<V>\data\postgresql.conf"
```
Busca (**Ctrl+F**) y deja estas líneas así (si tienen `#` al inicio, **quítalo**):

```conf
listen_addresses = '*'                 # atender a las otras PC de la red, no solo a sí misma
port = 5432                            # (o 5433 si el 5432 ya está ocupado)
timezone = 'America/Guayaquil'         # las fechas de los viáticos, en hora de Ecuador
```
Guarda y cierra. *(Si no se deja guardar, ábrelo desde PowerShell en modo administrador, como está
arriba.)*

## A4 — Dar permiso a la red (`pg_hba.conf`)

```powershell
notepad "C:\Program Files\PostgreSQL\<V>\data\pg_hba.conf"
```
Al final del archivo, **agrega estas dos líneas** (la primera es para que el propio servidor entre
desde sí mismo con clave; la segunda, para toda la red):

```conf
host    all    all    127.0.0.1/32        scram-sha-256
host    all    all    192.168.22.0/24     scram-sha-256
```
> `192.168.22.0/24` = "cualquier PC que empiece con 192.168.22." (las 5 PC y los portátiles de la
> empresa). Si algún día se conecta desde otra red, se agrega otra línea con ese rango.
> Si tu archivo usa `md5` en vez de `scram-sha-256`, deja el mismo que ya tenga.

## A5 — Reiniciar y comprobar que quedó escuchando

> **En el servidor de Miempresa el puerto es 2345** (no el 5432 de una instalación normal, para no
> chocar con otra base que ya estuviera puesta). En los comandos de A5 y A6, cambie `5432` por `2345`.

```powershell
Restart-Service postgresql-x64-<V>

# Debe salir LISTENING en 0.0.0.0:5432   (0.0.0.0 = todas las tarjetas de red)
netstat -ano | Select-String ":5432"

# Confirmar los ajustes desde la propia base
$env:PGPASSWORD = "tu-clave-de-postgres"
& "C:\Program Files\PostgreSQL\<V>\bin\psql.exe" -U postgres -c "SHOW listen_addresses;"   # *
& "C:\Program Files\PostgreSQL\<V>\bin\psql.exe" -U postgres -c "SHOW timezone;"          # America/Guayaquil
& "C:\Program Files\PostgreSQL\<V>\bin\psql.exe" -U postgres -c "SHOW port;"              # 5432
$env:PGPASSWORD = ""

# Y que la puerta responde en el propio servidor
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432      # TcpTestSucceeded : True
```

## A6 — Abrir el puerto en el firewall (lo que deja entrar a las otras PC)

```powershell
New-NetFirewallRule -DisplayName "Viaticos PostgreSQL 5432" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow -Profile Any

# Comprobar
Get-NetFirewallRule -DisplayName "Viaticos PostgreSQL 5432" | Format-Table DisplayName, Enabled, Direction, Action, Profile -AutoSize
#    Enabled = True · Direction = Inbound · Action = Allow
Get-NetFirewallProfile | Format-Table Name, Enabled -AutoSize
```
> `-Profile Any` es importante: Windows suele marcar la red como **Pública** y así queda permitido
> igual. **Si el antivirus tiene su propio firewall** (Kaspersky, ESET, Avast…), hay que permitir ahí
> también el puerto 5432 o el programa `postgres.exe`.
> *(Con el ratón: `firewall.cpl` → Configuración avanzada → Reglas de entrada → Nueva regla → Puerto →
> TCP 5432 → Permitir.)*

## A7 — Respaldo diario (una vez) y respaldo a mano

Para la versión nativa el respaldo es `servidor\respaldar_base_nativo.bat`. En el servidor la base se llama
`viaticos`, el usuario es **miempresa**, el puerto **2345** y la IP **192.168.22.4** (los mismos de
`sistema_viaticos_miempresa\configuracion.py`). El script usa **PostgreSQL 18**
(`C:\Program Files\PostgreSQL\18\bin`) y, si el servidor tuviera otra versión, la busca solo.

```bat
servidor\respaldar_base_nativo.bat miempresa 2345                 (a mano, EN el servidor → usa 127.0.0.1)
servidor\respaldar_base_nativo.bat miempresa 2345 192.168.22.4     (a mano, DESDE otra PC de la red)
```
Deja el archivo en `servidor\respaldos_base\viaticos_AAAAAMMDD_HHMMSS.sql`. **No borra nada:** se
conservan todos los respaldos (y los manuales `viaticos_ANTES_DE_....sql` nunca se tocan). Para que
salga **solo, todas las noches**, se crea una tarea programada (una sola vez):

### A7.1 — Crear la tarea de la noche con un solo clic (recomendado)

En el servidor: **botón derecho sobre `servidor\PROGRAMAR_RESPALDO_DIARIO.bat` → Ejecutar como
administrador** (si no, él mismo se reabre pidiendo permiso). **No hay que escribir nada:** ya trae puestos
los datos (**se conecta a `127.0.0.1`**, o sea al propio equipo, sin pasar por la red; puerto 2345, clave
miempresa, PostgreSQL 18, 21:00 todas las noches y sin borrar respaldos) y hace esto:

1. un **respaldo de prueba** y revisa que el `.sql` quedó completo (si falla, avisa y **no** crea la tarea);
2. crea la tarea **"Viaticos - respaldo diario"** (todos los días a las 21:00);
3. muestra la tarea creada y la ejecuta una vez (`Estado: Listo`, `Último resultado: 0`).

Si se prefiere que el respaldo se conecte por la **IP de la red** en lugar de `127.0.0.1`, se le pasan los
datos (los 4 son opcionales y van en este orden: **puerto, clave, servidor y hora**; lo que se omita queda
por defecto):

```bat
PROGRAMAR_RESPALDO_DIARIO.bat 2345 miempresa 192.168.22.4
```

Para quitarla o rehacerla: `servidor\QUITAR_RESPALDO_DIARIO.bat` (también como administrador).

### A7.2 — Crearla a mano (`schtasks`)

```powershell
$bat = "C:\MIEMPRESA_VIATICOS\servidor\respaldar_base_nativo.bat"
schtasks /Create /TN "Viaticos - respaldo diario" /TR "`"$bat`" miempresa 2345 127.0.0.1 0 auto" /SC DAILY /ST 21:00 /RU SYSTEM /RL HIGHEST /F
schtasks /Query  /TN "Viaticos - respaldo diario" /V /FO LIST
schtasks /Run    /TN "Viaticos - respaldo diario"      # probarlo ahora mismo
```
> `/RU SYSTEM` = corre aunque nadie tenga sesión abierta. El último número (`0`) = **no borrar nunca**
> los respaldos viejos. La palabra final **`auto`** es importante: hace que el respaldo **no se quede
> esperando una tecla** al terminar (si se quedara, la tarea aparecería como *En ejecución* para
> siempre y **las noches siguientes ya no respaldarían**, porque Windows no lanza una tarea que aún
> está corriendo). El respaldo **incluye las facturas** guardadas dentro de la base. Guarde una
> copia de `respaldos_base\` fuera del servidor (nube o USB).

### A7.3 — Copia de seguridad FUERA del servidor

Los respaldos se quedan todos en `servidor\respaldos_base\`; cópielos a un USB o a la nube de vez en
cuando (una vez por semana basta). Si el servidor se daña, el respaldo tiene que estar fuera de él.

---

## A8 — Dejar el servidor "de verdad": IP fija y que no se duerma

```powershell
# a) IP fija (use el nombre de la tarjeta del PASO 0-e y la IP real que confirmó allí)
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.22.123 -PrefixLength 24 -DefaultGateway 192.168.22.254
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8, 8.8.4.4
#    (el DefaultGateway es el router: si el router NO es .254, ponga el que dé `ipconfig`)

# b) Que no se suspenda ni apague la pantalla (es un servidor)
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change disk-timeout-ac 0
```
> **Si es laptop**, además: Panel de control → Opciones de energía → *Elegir el comportamiento al
> cerrar la tapa* → **No hacer nada** (y que esté enchufada).

---

# PUERTO OCUPADO — «el 5432 ya está en uso», ¿qué hacemos?

Primero **saber quién lo tiene** (en el servidor, PowerShell):

```powershell
netstat -ano | Select-String ":5432"                 # apunte el PID de la línea LISTENING
Get-Process -Id <PID> | Select-Object Id, ProcessName, Path
Get-Service postgresql* | Format-Table Name, Status, StartType
```
Con eso, hay **tres casos**:

### Caso 1 — Es un PostgreSQL que **ya estaba instalado** en esa máquina (`postgres.exe`)

Dos salidas, **elige una**:
- **(1a) Aprovecharlo** (lo más simple): la base ya está hecha, solo falta la parte del programa →
  salta al **A2** (crear usuario y base) y sigue con A3/A4 usando los archivos de **ese** servidor
  (ojo: la carpeta `<V>` es la de la versión vieja) y A5 en adelante.
- **(1b) No usarlo y dejar el puerto libre** (si es una instalación que nadie usa):
```powershell
Stop-Service postgresql-x64-<V_vieja>                        # detener
Set-Service  postgresql-x64-<V_vieja> -StartupType Disabled   # que no vuelva a arrancar
netstat -ano | Select-String ":5432"                          # ya NO debe salir nada
# (si de verdad nadie la necesita, se desinstala desde "Aplicaciones instaladas")
```
Después instala la versión nueva en el 5432 normal (Método A).

### Caso 2 — Es **otro programa** cualquiera (SQL Server, una cámara, un POS…)

**No toques ese programa.** Lo correcto es **mover PostgreSQL al puerto 5433**:

```powershell
# 1) En el servidor: cambiar el puerto
notepad "C:\Program Files\PostgreSQL\<V>\data\postgresql.conf"      # port = 5433
Restart-Service postgresql-x64-<V>
netstat -ano | Select-String ":5433"          # LISTENING en 0.0.0.0:5433

# 2) Abrir ESE puerto en el firewall (convive con la regla del 5432, no hay que borrarla)
New-NetFirewallRule -DisplayName "Viaticos PostgreSQL 5433" -Direction Inbound -Protocol TCP -LocalPort 5433 -Action Allow -Profile Any

# 3) La línea de red en pg_hba.conf es la misma: el puerto NO cambia ese archivo

# 4) En CADA PC del programa: 🔌 CONEXIÓN / BASE DE DATOS → Puerto = 5433 → probar → 💾 Guardar

# 5) Comprobar desde otra PC
servidor\PROBAR_SERVIDOR.bat 192.168.22.123 5433     # Puerto 5433 abierto ..: True
```
Todo lo demás **sigue igual** (IP, base `viaticos`, usuario `miempresa`, clave y respaldos).

| Qué cambia con el 5433 | Dónde |
| --- | --- |
| `port = 5433` | `postgresql.conf` del servidor |
| Regla de firewall del **5433** (la del 5432 se deja) | servidor |
| **Puerto `5433`** | 🔌 CONEXIÓN / BASE DE DATOS de **cada** PC (y su `config.json`) |
| `"puerto": 5433` | `config.json` (texto) |
| `-p 5433` al respaldar | `respaldar_base_nativo.bat miempresa 5433` |

---

## En las PC que usan el programa (una sola vez por máquina)

> **Con el `.exe` empaquetado por `EMPAQUETAR_EXE_SERVIDOR.bat` no hay que configurar nada:** la IP y el
> puerto van dentro del ejecutable, así que solo se copia ese archivo. Los pasos de abajo son para
> comprobar/cambiar la dirección en una PC, o si el `.exe` quedó apuntando a otro servidor.

1. Abre el sistema con el **superusuario** → **🔌 CONEXIÓN / BASE DE DATOS**.
2. Marca **«Base CENTRAL en el servidor (PostgreSQL)»** y escribe:
   **Servidor `192.168.22.123`** · **Puerto `5432`** (o `5433`) · **Base `viaticos`** ·
   **Usuario `miempresa`** · **Clave** la elegida · Respaldos **«Guardar dentro de la base central»**.
3. Pulsa **🔌 Probar conexión** → debe decir «**Conexión correcta · PostgreSQL …**» → **💾 Guardar**.
   La barra superior de esa PC debe quedar en **BASE CENTRAL**.
4. **⬆ Subir mis datos locales a la central** — solo la **primera vez** y desde **una** PC (la de
   desarrollo), para llevar los catálogos: **32 empleados · 755 clientes** y el próximo viático en
   **N° 1**. Las demás PC **no** deben pulsar ese botón (reemplaza lo que haya en la base central).

Si prefieres hacerlo a mano, el `config.json` (va junto al `.exe`) es:

```json
{
  "motor": "postgres",
  "postgres": {
    "host": "192.168.22.123", "puerto": 5432, "base": "viaticos",
    "usuario": "miempresa", "clave": "miempresa"
  },
  "respaldos": { "modo": "base", "carpeta": "" }
}
```

---

# Prueba final (hoja de control)

- [ ] **0** — Confirmado que la máquina es de verdad la `192.168.22.123` (no es el router) y el puerto elegido
- [ ] **A1** — Servicio **Running** y en **Automático**
- [ ] **A2** — Base `viaticos` + usuario `miempresa` creados y `psql` entra con ese usuario
- [ ] **A3/A4** — `listen_addresses = '*'`, `timezone = 'America/Guayaquil'`, línea de la red en `pg_hba.conf`
- [ ] **A5** — `netstat` muestra **LISTENING** en el puerto elegido
- [ ] **A6** — Regla de firewall creada y `Test-NetConnection 127.0.0.1 -Port <puerto>` = True
- [ ] **A7** — Respaldo generado a mano y tarea programada diaria creada (y probada)
- [ ] **A8** — IP fija puesta; la máquina no se suspende ni hiberna
- [ ] **Otra PC** — `servidor\PROBAR_SERVIDOR.bat 192.168.22.123 5432` → `True`
- [ ] **Otra PC** — El programa marca **BASE CENTRAL** y abre con la clave
- [ ] **Prueba real** — Un viático creado en una PC se ve en la otra (botón 🔄 Actualizar) y la numeración sigue sin repetir
- [ ] **Prueba real** — La justificación sale con **un solo PDF** y en **🕵 INFORME DE ACTIVIDAD** se ven las dos PC

# Problemas frecuentes

| Qué ves | Qué pasa | Qué hacer |
| --- | --- | --- |
| `NO SE PUDO ABRIR LA BASE DE DATOS` | firewall, antivirus, IP equivocada o base apagada | PASO 0, A5 y A6, y la pantalla de conexión |
| `password authentication failed` | la clave no coincide | escribir la misma clave en la pantalla de conexión |
| `no pg_hba.conf entry for host …` | falta la línea de la red | A4 + `Restart-Service` |
| `could not connect to server` | servicio detenido, máquina dormida o puerto equivocado | `Get-Service postgresql*`, A5, PASO 0-b |
| `Address already in use` / el instalador no deja | **puerto ocupado** | apartado **PUERTO OCUPADO** |
| `netstat` no muestra el puerto | PostgreSQL no está corriendo | `Start-Service postgresql-x64-<V>` |
| Conectan, pero no ven los mismos viáticos | esa PC quedó en base **LOCAL** | en esa PC: 🔌 CONEXIÓN → **Base CENTRAL** → 💾 Guardar |
| Todo lento en la noche | el respaldo o el antivirus | mover la hora de la tarea / excluir la carpeta `data` del antivirus |

> **Cómo se empaqueta (solo se copia el `.exe` a las otras PC):** ejecute
> **`sistema_viaticos_miempresa\EMPAQUETAR_EXE_SERVIDOR.bat`** e indique la IP y el puerto. La IP queda
> **dentro del ejecutable** (valor de fábrica en `configuracion.py`, con respaldo `configuracion.py.bak`)
> y además se deja `dist\config.json.EJEMPLO`, que es **solo una referencia**: el programa lo ignora.
> A cada computadora se copia **únicamente** `dist\Sistema_Viaticos.exe`.
>
> ⚠️ **Nunca** reparta un `config.json`: ese archivo es de **cada** computadora y ahí va también su
> **zoom** (tamaño de pantalla). Si se copia de una PC a otra, la otra queda con el zoom ajeno. Si en
> alguna PC ya hay un `config.json` viejo al lado del `.exe`, ese archivo **manda** sobre la IP de
> fábrica: bórrelo o abra **🔌 CONEXIÓN / BASE DE DATOS** y confirme que apunte al servidor nuevo.
> El `.exe` debe quedar en una **carpeta local** de cada PC (nunca de red, USB o sincronizada: si dos
> PC comparten la carpeta, comparten `config.json` y el zoom de una salta a la otra).

> **Recordatorio:** no tenga **dos** PostgreSQL encendidos a la vez en el servidor: el segundo no
> arrancará porque el puerto estará ocupado. Use uno solo (el de esta guía).
