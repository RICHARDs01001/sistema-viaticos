# PC DE PRUEBA COMO SERVIDOR — PostgreSQL 16 · puerto 2345 · IP 192.168.22.171

> **Estás en la PC de prueba.** Sigue los pasos en orden, de arriba abajo. Todo se hace en
> **PowerShell como Administrador** (Inicio → escribe `powershell` → clic derecho →
> *Ejecutar como administrador*). Cada paso dice **qué escribes** y **qué debe salir**.
>
> Prueba: PostgreSQL **16** recién instalado · puerto **2345** (no el 5432, para que no choque con
> ninguna otra base) · IP de esta PC **192.168.22.171**.
>
> ⚠️ Si instalas otra versión (17 o 18), en **todos** los comandos cambia `16` por ese número
> (`postgresql-x64-17`, `C:\Program Files\PostgreSQL\17\…`).

## Datos de esta prueba (los mismos en todas las PC)

| Dato | Valor |
| --- | --- |
| **IP del servidor de prueba** | `192.168.22.171` |
| **Puerto** | `2345` |
| Base de datos | `viaticos` |
| Usuario | `miempresa` |
| Clave de `miempresa` | `miempresa` (se puede cambiar, y entonces se cambia igual en cada PC) |
| Clave del superusuario `postgres` | `_______________________` (la que elijas al instalar) |
| Versión | PostgreSQL **16** |
| Carpeta | `C:\Program Files\PostgreSQL\16` |
| Servicio | `postgresql-x64-16` |

> **Las tablas NO se crean a mano:** las crea el propio programa la primera vez que se conecta
> (empleados, clientes, viáticos, parámetros…). Aquí solo se prepara la "casa": usuario, base,
> puerto y permiso de red.

---

## PASO 0 — Mirar el terreno (3 minutos)

```powershell
# a) ¿Cuál es la IP de esta PC?   Debe salir 192.168.22.171
ipconfig | Select-String "IPv4", "Puerta de enlace"
#    Si sale OTRA cosa, o la pones fija en el PASO 5, o usa la IP real en todos los comandos.

# b) ¿Qué Windows es, cuánta RAM y cuánto espacio libre? (compatibilidad de PostgreSQL 16)
(Get-CimInstance Win32_OperatingSystem).Caption
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
Get-PSDrive C | Select-Object @{n='LibreGB'; e={[math]::Round($_.Free/1GB,1)}}

# c) ¿El puerto 2345 está libre?  NO debe salir NADA
netstat -ano | Select-String ":2345"

# d) ¿Windows no tiene reservado el 2345?  (que no aparezca dentro de un rango)
netsh int ipv4 show excludedportrange protocol=tcp

# e) ¿Hay alguna otra PostgreSQL instalada aquí?
Get-Service postgresql* -ErrorAction SilentlyContinue | Format-Table Name, Status, StartType -AutoSize
Get-ChildItem "C:\Program Files\PostgreSQL" -ErrorAction SilentlyContinue | Select-Object Name
```

**Debe quedar claro:** IP `192.168.22.171`, puerto `2345` **libre**, y (si ya hubiera otra
PostgreSQL) **su** puerto no debe ser el 2345.

---

## PASO 1 — Instalar PostgreSQL 16

1. Descarga el instalador: `https://www.postgresql.org/download/windows/` → **Download the
   installer** (EDB) → elige **PostgreSQL 16.x · Windows x86-64**.
   *(Si esta PC no tiene Internet, descárgalo en otra PC y pásalo por USB.)*
2. Ejecútalo (clic derecho → **Ejecutar como administrador**) y en cada pantalla:
   - **Installation Directory:** deja `C:\Program Files\PostgreSQL\16`.
   - **Select Components:** marca **PostgreSQL Server** y **Command Line Tools**.
     (pgAdmin y Stack Builder se pueden desmarcar.)
   - **Data Directory:** deja `C:\Program Files\PostgreSQL\16\data`.
   - **Password:** la clave del superusuario `postgres` → **anótala** (la pedirá `psql`).
   - 🔴 **Port: `2345`** ← *el cambio más importante de todo este documento.*
   - **Locale:** `Spanish, Ecuador` (o *Default locale*; da igual). Que el **Encoding** sea `UTF-8`.
   - Al terminar: **desmarca** *Launch Stack Builder* → **Finish**.
   - **Esta instalación NO reinicia la PC.** El servicio queda en *Automático* (arranca solo).

**Comprueba que quedó bien:**

```powershell
Get-Service postgresql* | Format-Table Name, Status, StartType -AutoSize
#    Debe salir:  postgresql-x64-16    Running    Automatic
#    (si no dice Running:  Start-Service postgresql-x64-16)

& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -p 2345 -c "select version();"
#    Pide la clave de postgres -> debe salir: PostgreSQL 16.x ...
```

---

## PASO 2 — Crear el usuario y la base que usa el programa

```powershell
$env:PGPASSWORD = "tu-clave-de-postgres"          # la del PASO 1
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

# ¿Qué hay ya creado?  (aquí NO se borra nada)
& $psql -U postgres -p 2345 -c "\l"               # lista de BASES
& $psql -U postgres -p 2345 -c "\du"              # lista de USUARIOS

# Si NO aparecen, se crean  (si ya existen, dirá "ya existe": buena señal)
& $psql -U postgres -p 2345 -c "CREATE USER miempresa WITH PASSWORD 'miempresa';"
& $psql -U postgres -p 2345 -c "CREATE DATABASE viaticos OWNER miempresa ENCODING 'UTF8';"
& $psql -U postgres -p 2345 -c "GRANT ALL PRIVILEGES ON DATABASE viaticos TO miempresa;"

# Comprobar que quedaron
& $psql -U postgres -p 2345 -c "\l"  | Select-String "viaticos"
& $psql -U postgres -p 2345 -c "\du" | Select-String "miempresa"

# Probar con el usuario del programa (debe entrar y responder "viaticos")
$env:PGPASSWORD = "miempresa"
& $psql -U miempresa -h 127.0.0.1 -p 2345 -d viaticos -c "select current_database(), current_user;"
$env:PGPASSWORD = ""
```
> Si quieres otra clave en vez de `miempresa`, ponla en el `CREATE USER` **y la misma** en cada PC
> (para esta prueba, mejor dejarla como está).

## PASO 3 — Que la base escuche en el **2345** y atienda a las otras PC

Son **dos archivos**. Ábrelos con Notepad (si no deja guardar, es porque Notepad no está abierto como
administrador; ábrelo desde la PowerShell de administrador como está aquí):

```powershell
notepad "C:\Program Files\PostgreSQL\16\data\postgresql.conf"
```
Busca con **Ctrl+F** y deja estas tres líneas así (si empiezan con `#`, **quítalo**):

```conf
listen_addresses = '*'                 # atender a las otras PC de la red, no solo a sí misma
port = 2345                            # el puerto de esta prueba
timezone = 'America/Guayaquil'         # las fechas de los viáticos, en hora de Ecuador
```

```powershell
notepad "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
```
Agrega **al final** estas dos líneas (deja el archivo como esté arriba; si tu archivo usa `md5` en vez
de `scram-sha-256`, escribe el mismo que ya tenga):

```conf
host    all    all    127.0.0.1/32        scram-sha-256
host    all    all    192.168.22.0/24     scram-sha-256
```

**Aplicar y comprobar (esto NO reinicia la PC):**

```powershell
Restart-Service postgresql-x64-16

# Debe salir LISTENING en 0.0.0.0:2345
netstat -ano | Select-String ":2345"

# Confirmar los tres ajustes desde la propia base
$env:PGPASSWORD = "tu-clave-de-postgres"
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
& $psql -U postgres -p 2345 -c "SHOW port;"               # 2345
& $psql -U postgres -p 2345 -c "SHOW listen_addresses;"   # *
& $psql -U postgres -p 2345 -c "SHOW timezone;"           # America/Guayaquil
$env:PGPASSWORD = ""

# Y que el puerto responde en esta misma PC
Test-NetConnection -ComputerName 127.0.0.1 -Port 2345      # TcpTestSucceeded : True
```

---

## PASO 4 — Abrir el puerto 2345 en el firewall

```powershell
New-NetFirewallRule -DisplayName "Viaticos PostgreSQL 2345" -Direction Inbound -Protocol TCP -LocalPort 2345 -Action Allow -Profile Any

Get-NetFirewallRule -DisplayName "Viaticos PostgreSQL 2345" |
  Format-Table DisplayName, Enabled, Direction, Action, Profile -AutoSize
#    Debe salir: Enabled True · Inbound · Allow

Get-NetFirewallProfile | Format-Table Name, Enabled -AutoSize
```

> `-Profile Any` es a propósito: Windows suele marcar la red como **Pública** y con `-Profile Private`
> la regla no aplicaría.
> **Si hay antivirus con firewall propio** (ESET, Kaspersky, Avast, Bitdefender…), permite ahí también
> el **puerto 2345** o el programa `postgres.exe`.

---

## PASO 5 — Dejar la IP fija `192.168.22.171`

**Primero mira los datos reales de tu red** (no los inventes):

```powershell
Get-NetIPConfiguration
Get-NetAdapter | Where-Object Status -eq "Up" | Format-Table Name, InterfaceDescription, LinkSpeed -AutoSize
#    Apunta: el nombre de la tarjeta (Ethernet en cable o Wi-Fi), la IP, el prefijo
#    (24 = máscara 255.255.255.0), la PUERTA DE ENLACE (el router, ej. 192.168.22.1 o ...254) y el DNS.
```

**Ahora ponla fija** (usa **el nombre real** de tu tarjeta y **la puerta de enlace que viste**):

```powershell
Set-NetIPInterface -InterfaceAlias "Ethernet" -Dhcp Disabled
Remove-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4 -Confirm:$false
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.22.171 -PrefixLength 24 -DefaultGateway 192.168.22.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8, 1.1.1.1

# Comprobar
ipconfig | Select-String "IPv4", "Puerta de enlace"
Test-NetConnection -ComputerName 8.8.8.8 -Port 443        # ¿hay Internet?
Resolve-DnsName google.com                                # ¿resuelven los nombres (DNS)?
```

> ⚠️ **Hazlo sentado en esa PC** (al cambiarla se corta la red unos segundos) y con la **puerta de
> enlace correcta**: sin ella **no habría Internet**.
> Si esa IP está dentro del rango del router podría chocar con otro equipo; lo ideal es pedir en el
> router una **reserva por MAC** (así no hay que tocar Windows).
>
> **Si algo sale mal y te quedas sin red, se vuelve a automático así:**
> ```powershell
> Remove-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4 -Confirm:$false
> Set-NetIPInterface -InterfaceAlias "Ethernet" -Dhcp Enabled
> Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ResetServerAddresses
> ipconfig /renew
> ```

---

## PASO 6 — Que la PC no se duerma ni se apague

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0
powercfg /change monitor-timeout-ac 15
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0   # cerrar la tapa: "No hacer nada"
powercfg /setactive SCHEME_CURRENT
```

- Déjala **enchufada** durante toda la prueba (con batería, Windows pasa a modo ahorro).
- Si va por WiFi: Administrador de dispositivos → adaptador WiFi → *Administración de energía* →
  **desmarca** «Permitir que el equipo apague este dispositivo para ahorrar energía».

## PASO 7 — Respaldo de esta base (diario)

*(Ajusta la ruta a donde tengas el proyecto. El script acepta clave y puerto.)*

```powershell
$bat = "C:\MIEMPRESA_VIATICOS\servidor\respaldar_base_nativo.bat"
& $bat miempresa 2345
Get-ChildItem "C:\MIEMPRESA_VIATICOS\servidor\respaldos_base" |
  Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name, Length, LastWriteTime
#    Debe aparecer:  viaticos_AAAAMMDD_HHMMSS.sql  con la fecha de hoy
```

Programarlo todos los días a las 21:00 (una sola vez):

```powershell
schtasks /Create /TN "Viaticos - respaldo diario" /TR "\"C:\MIEMPRESA_VIATICOS\servidor\respaldar_base_nativo.bat\" miempresa 2345" /SC DAILY /ST 21:00 /RU SYSTEM /RL HIGHEST /F
schtasks /Query /TN "Viaticos - respaldo diario" /V /FO LIST
schtasks /Run   /TN "Viaticos - respaldo diario"     # probarlo ahora
```
> El respaldo incluye las facturas (van dentro de la base). Copia el `.sql` más nuevo a un USB o a la nube.

---

## PASO 8 — Comprobar desde OTRA PC

En otra computadora de la red (PowerShell):

```powershell
Test-NetConnection -ComputerName 192.168.22.171 -Port 2345      # TcpTestSucceeded : True
```

O:

```
servidor\PROBAR_SERVIDOR.bat 192.168.22.171 2345
```

Si sale **False**: PASO 4 (firewall/antivirus), PASO 5 (¿es la IP `.171` de verdad?) y PASO 6
(¿la PC está despierta?).

---

## PASO 9 — Empaquetar el `.exe` apuntando a esta PC

Esto se hace en la **PC de desarrollo** (donde está el programa), no aquí:

```
cd C:\Users\richi\Desktop\MIEMPRESA_VIATICOS\sistema_viaticos_miempresa
EMPAQUETAR_EXE_SERVIDOR.bat 192.168.22.171 2345
```

Y se comprueba que quedó bien (autodiagnóstico del propio `.exe`):

```
set VIATICOS_SELFTEST=1
dist\Sistema_Viaticos.exe
type dist\autodiagnostico.txt
#    Debe decir:
#      conexion configurada: Base CENTRAL PostgreSQL: miempresa@192.168.22.171:2345/viaticos
#      OK  conexion -> Conexión correcta · PostgreSQL 16…
```

> ⚠️ En cada PC donde copies el `.exe`, **borra cualquier `config.json` que esté al lado**: si existe,
> *manda* sobre la IP y el puerto de fábrica y el programa intentaría conectarse a otro sitio.

---

## PASO 10 — La prueba de verdad (5 minutos)

1. Copia **solo** `dist\Sistema_Viaticos.exe` a otra PC, en una **carpeta local** (nunca en USB,
   carpeta de red o sincronizada).
2. Ábrelo: debe entrar directo y la barra decir **BASE CENTRAL**.
3. Entra con una vendedora: `TATIANA` / `1234` → crea un viático y **guárdalo** (debe quedar **001/2026**).
4. En la **PC de prueba** (o en otra) abre el sistema y pulsa **🔄 Actualizar**: el viático debe aparecer.
5. Justifica el viático desde una PC → en la otra debe verse **JUSTIFICADO** y en **📁 RESPALDOS**
   **un solo PDF** completo.
6. Crea **otro** viático: la numeración debe seguir (**002/2026**, sin repetir).
7. Con el superusuario (`MIEMPRESA` / `miempresa`) → **🕵 INFORME DE ACTIVIDAD**: deben verse los
   movimientos de las dos PC.

*(Opcional)* Subir los datos reales desde la **PC de desarrollo**: `INICIAR.bat` → `MIEMPRESA` →
**🔌 CONEXIÓN** → Servidor `192.168.22.171` · Puerto `2345` · Base `viaticos` · Usuario `miempresa` ·
Clave `miempresa` → **🔌 Probar conexión** → **💾 Guardar** → **⬆ Subir mis datos locales a la
central** → debe quedar **0 viáticos · 32 empleados · 755 clientes**.

---

## PASO 11 — Al terminar la prueba

**No hay que borrar nada:** los viáticos de prueba **se quedan** en la base central (no estorban) y el
sistema nunca entrega un número ya usado. Para arrancar la producción, vaya a
**🔌 CONEXIÓN / BASE DE DATOS → Numeración de viáticos → 💾 Fijar numeración** y ponga el número por
el que debe empezar el primer viático real (si el último de prueba fue el 007, ponga **008**).

Si ya no se usará la base de esta PC: `Stop-Service postgresql-x64-16` (y `Start-Service …` para
volver a encenderla; no borra nada).

---

## Problemas frecuentes

| Qué ves | Qué pasa | Qué hacer |
| --- | --- | --- |
| `Address already in use` / el servicio no arranca | el 2345 ya está ocupado | `netstat -ano \| Select-String ":2345"` → usa otro puerto (y cámbialo en TODO) |
| `no pg_hba.conf entry for host …` | falta la línea de la red | PASO 3 + `Restart-Service postgresql-x64-16` |
| `password authentication failed` | la clave no coincide | escribe la misma clave en 🔌 CONEXIÓN y guarda |
| La otra PC dice `NO SE PUDO ABRIR LA BASE` | firewall, antivirus, IP equivocada o PC dormida | PASOS 4, 5, 6 y 8 |
| El `.exe` no conecta (pero la base está bien) | hay un `config.json` viejo junto al `.exe` | bórralo (o corrige la dirección en 🔌 CONEXIÓN) |
| `server version mismatch` al respaldar | usó el `pg_dump` de otra versión | usa el de `…\PostgreSQL\16\bin` |
| Conectan, pero no ven los mismos viáticos | una PC quedó en base **LOCAL** | en esa PC: 🔌 CONEXIÓN → **Base CENTRAL** → 💾 Guardar |

---

## Hoja de control

- [ ] **0** — IP `192.168.22.171` vista · puerto `2345` libre
- [ ] **1** — PostgreSQL 16 instalado en **2345** · servicio `postgresql-x64-16` **Running/Automatic**
- [ ] **2** — Usuario `miempresa` + base `viaticos` creados (y `psql` entra con ese usuario)
- [ ] **3** — `port = 2345`, `listen_addresses = '*'`, `timezone` y `pg_hba.conf` + `Restart-Service`
- [ ] **4** — Regla de firewall del **2345** · `Test-NetConnection 127.0.0.1 -Port 2345` = True
- [ ] **5** — IP fija `192.168.22.171` puesta (y sigue habiendo Internet)
- [ ] **6** — La PC no se suspende y al cerrar la tapa no hace nada
- [ ] **7** — Respaldo probado + tarea diaria (`respaldar_base_nativo.bat miempresa 2345`)
- [ ] **8** — Desde otra PC: `PROBAR_SERVIDOR.bat 192.168.22.171 2345` → True
- [ ] **9** — `.exe` empaquetado con `192.168.22.171 2345` + autodiagnóstico = «PostgreSQL 16»
- [ ] **10** — Viático creado en una PC se ve en la otra · numeración · un solo PDF · auditoría
- [ ] **11** — Viáticos de prueba borrados (si era solo prueba)

