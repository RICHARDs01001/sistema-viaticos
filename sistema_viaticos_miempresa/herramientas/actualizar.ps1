# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
<#
    actualizar.ps1 — Busca una versión nueva del sistema en GitHub y la instala.

    Lo llama ACTUALIZAR_DESDE_GITHUB.bat (no hace falta ejecutarlo a mano).

    Qué hace, en orden:
      1. Encuentra la carpeta del programa, esté donde esté: la que se le indica,
         la que está guardada de la vez anterior, la de los accesos directos del
         escritorio / menú de inicio / barra de tareas, o la busca en los sitios
         habituales.
      2. Compara version.txt con el del repositorio.
      3. Si hay versión nueva: cierra el programa si está abierto, guarda una copia
         del código actual, baja el código y el Sistema_Viaticos.exe de la última
         versión publicada, los copia en su lugar y vuelve a dejar los accesos
         directos apuntando al ejecutable nuevo.

    Nunca toca los datos: la carpeta data\, config.json y los archivos *.db se
    quedan como están. Antes de copiar nada guarda la versión que había en
    respaldos_actualizacion\AAAA-MM-DD_HHMM\.

    Uso:
        powershell -ExecutionPolicy Bypass -File herramientas\actualizar.ps1
        ... -App "D:\Viaticos"        la carpeta del programa, si no se encuentra sola
        ... -Repo https://github.com/usuario/repositorio -Rama main
        ... -Simular                  solo dice qué haría (no copia nada)
        ... -Forzar                   actualiza aunque la versión sea la misma
        ... -Abrir                    abre el programa al terminar
        ... -SoloAccesos              (pruebas) solo rehace los accesos directos
#>
[CmdletBinding()]
param(
    [string]$Repo = "https://github.com/RICHARDs01001/sistema-viaticos",
    [string]$Rama = "main",
    [string]$App = "",
    [switch]$Simular,
    [switch]$SinPausa,
    [switch]$Forzar,
    [switch]$SoloAccesos,
    [switch]$Abrir,
    [string[]]$ZonasAccesos = @()
)

$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

$script:Log = $null
$NombreExe = "Sistema_Viaticos.exe"

function Decir($texto, $color = "Gray") {
    Write-Host $texto -ForegroundColor $color
    if ($script:Log) {
        try { Add-Content -Path $script:Log -Value ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $texto) -Encoding utf8 } catch { }
    }
}

function Fallar($texto) {
    Decir ""
    Decir "*** $texto ***" "Red"
    if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
    exit 1
}

function Descargar($url, $destino, [long]$minimo = 2048) {
    Decir "  bajando $url" "DarkGray"
    Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing -TimeoutSec 300
    if (-not (Test-Path -LiteralPath $destino)) { Fallar "No se pudo descargar el archivo." }
    $tam = (Get-Item -LiteralPath $destino).Length
    if ($tam -lt $minimo) {
        Fallar "El archivo bajado es demasiado pequeño ($tam bytes): revise que el repositorio sea público y que la rama se llame '$Rama'."
    }
    return $tam
}

function Test-Instalacion([string]$ruta) {
    if (-not $ruta) { return $false }
    if (-not (Test-Path -LiteralPath $ruta -PathType Container)) { return $false }
    return ((Test-Path -LiteralPath (Join-Path $ruta $NombreExe)) -or
            (Test-Path -LiteralPath (Join-Path $ruta "main_qt.py")))
}

# --- Dónde quedó instalado la última vez -------------------------------------
$CarpetaDatos = Join-Path $env:APPDATA "SistemaViaticos"
$ArchivoRuta = Join-Path $CarpetaDatos "instalacion.txt"

function Leer-RutaGuardada {
    if (-not (Test-Path -LiteralPath $ArchivoRuta)) { return "" }
    try {
        $r = (Get-Content -LiteralPath $ArchivoRuta -TotalCount 1).Trim().Trim('"')
        if (Test-Instalacion $r) { return $r }
    } catch { }
    return ""
}

function Guardar-Ruta([string]$ruta) {
    if (-not $ruta) { return }
    try {
        if (-not (Test-Path -LiteralPath $CarpetaDatos)) {
            New-Item -ItemType Directory -Path $CarpetaDatos -Force | Out-Null
        }
        Set-Content -LiteralPath $ArchivoRuta -Value $ruta -Encoding UTF8
    } catch { }
}

# --- Accesos directos ---------------------------------------------------------
function Get-Accesos {
    $zonas = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("CommonDesktopDirectory"),
        [Environment]::GetFolderPath("Programs"),
        [Environment]::GetFolderPath("CommonPrograms"),
        (Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    if ($ZonasAccesos -and $ZonasAccesos.Count -gt 0) { $zonas = $ZonasAccesos }

    $shell = New-Object -ComObject WScript.Shell
    $lista = @()
    foreach ($zona in $zonas) {
        $archivos = Get-ChildItem -LiteralPath $zona -Filter "*.lnk" -File -Recurse -ErrorAction SilentlyContinue
        foreach ($lnk in $archivos) {
            try {
                $a = $shell.CreateShortcut($lnk.FullName)
                if (-not $a.TargetPath) { continue }
                $lista += [pscustomobject]@{
                    Archivo     = $lnk.FullName
                    Nombre      = $lnk.BaseName
                    Destino     = $a.TargetPath
                    Argumentos  = $a.Arguments
                    Carpeta     = $a.WorkingDirectory
                    Icono       = $a.IconLocation
                    Estilo      = $a.WindowStyle
                    Descripcion = $a.Description
                }
            } catch { }
        }
    }
    return $lista
}

function Reparar-Accesos([string]$exe, [switch]$Simular) {
    $carpeta = Split-Path -Parent $exe
    $shell = New-Object -ComObject WScript.Shell
    $cambiados = 0
    $creados = 0

    foreach ($a in (Get-Accesos)) {
        $destino = $a.Destino
        $mismoNombre = ((Split-Path -Leaf $destino) -ieq $NombreExe)
        $apuntaAqui = ((Split-Path -Parent $destino) -ieq $carpeta)
        # Solo se tocan los accesos del sistema: el que apunta al ejecutable, el que
        # está en la carpeta del programa o el que se llama "Sistema de Viáticos".
        # Un acceso roto de otro programa (Office, VLC, etc.) NO se toca.
        $seLlamaViaticos = ($a.Nombre -match "(?i)vi[aá]tic")
        if (-not ($mismoNombre -or $apuntaAqui -or $seLlamaViaticos)) { continue }

        if ($Simular) {
            Decir ("  (-Simular) se habría re-apuntado: {0}" -f $a.Archivo) "Yellow"
            $cambiados++
            continue
        }
        try {
            $n = $shell.CreateShortcut($a.Archivo)
            $n.TargetPath = $exe
            $n.WorkingDirectory = $carpeta
            $n.IconLocation = "$exe,0"
            if ($a.Argumentos) { $n.Arguments = $a.Argumentos }
            if ($a.Estilo) { $n.WindowStyle = $a.Estilo }
            $n.Save()
            $cambiados++
            Decir ("  acceso directo al día: {0}" -f $a.Archivo) "DarkGray"
        } catch {
            Decir ("  no se pudo cambiar {0}: {1}" -f $a.Archivo, $_.Exception.Message) "Yellow"
        }
    }

    if ($cambiados -gt 0) { return [pscustomobject]@{ Cambiados = $cambiados; Creados = 0 } }

    # No había ninguno: se deja uno en el escritorio y otro en el menú de inicio.
    if ($ZonasAccesos -and $ZonasAccesos.Count -gt 0) {
        $destinos = @(
            (Join-Path $ZonasAccesos[0] "Sistema de Viáticos.lnk"),
            (Join-Path $ZonasAccesos[[Math]::Min(1, $ZonasAccesos.Count - 1)] "Sistema de Viáticos.lnk")
        ) | Select-Object -Unique
    } else {
        $destinos = @(
            (Join-Path ([Environment]::GetFolderPath("Desktop")) "Sistema de Viáticos.lnk"),
            (Join-Path ([Environment]::GetFolderPath("Programs")) "Sistema de Viáticos.lnk")
        )
    }
    foreach ($lnk in $destinos) {
        if (-not $lnk) { continue }
        if (Test-Path -LiteralPath $lnk) { continue }
        if ($Simular) {
            Decir ("  (-Simular) se habría creado: {0}" -f $lnk) "Yellow"
            $creados++
            continue
        }
        try {
            $padre = Split-Path -Parent $lnk
            if (-not (Test-Path -LiteralPath $padre)) { New-Item -ItemType Directory -Path $padre -Force | Out-Null }
            $n = $shell.CreateShortcut($lnk)
            $n.TargetPath = $exe
            $n.WorkingDirectory = $carpeta
            $n.IconLocation = "$exe,0"
            $n.Description = "Sistema de Viáticos"
            $n.Save()
            $creados++
            Decir ("  acceso directo creado: {0}" -f $lnk) "DarkGray"
        } catch {
            Decir ("  no se pudo crear {0}: {1}" -f $lnk, $_.Exception.Message) "Yellow"
        }
    }
    return [pscustomobject]@{ Cambiados = 0; Creados = $creados }
}

function Buscar-Instalacion {
    $guardada = Leer-RutaGuardada
    if ($guardada) { return $guardada }

    foreach ($a in (Get-Accesos)) {
        $d = Split-Path -Parent $a.Destino
        if ($d -and (Test-Instalacion $d)) { return $d }
    }

    $bases = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("MyDocuments"),
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:PUBLIC "Desktop"),
        "C:\",
        "D:\"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    foreach ($b in $bases) {
        $enc = Get-ChildItem -LiteralPath $b -Filter $NombreExe -File -Recurse -Depth 2 -ErrorAction SilentlyContinue |
               Select-Object -First 1
        if ($enc) { return (Split-Path -Parent $enc.FullName) }
    }
    return ""
}

# --- El .exe de la última versión publicada (adjunto de la "release") ---------
function Buscar-ExeRemoto {
    try {
        $release = Invoke-RestMethod -Uri "$Api/releases/latest" -UseBasicParsing -TimeoutSec 40 `
                                     -Headers @{ "User-Agent" = "viaticos-actualizador" }
        $asset = @($release.assets) | Where-Object { $_.name -match "(?i)Sistema[_-]?Vi[aá]ticos.*\.exe$" } |
                 Select-Object -First 1
        if ($asset) { return $asset.browser_download_url }
    } catch { }

    # Dirección fija del adjunto de la última versión publicada.
    foreach ($nombre in @("Sistema_Viaticos.exe", "Sistema-Viaticos.exe")) {
        $url = "https://github.com/$Dueno/$Nombre/releases/latest/download/$nombre"
        try {
            $r = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 30
            if ($r.StatusCode -eq 200) { return $url }
        } catch { }
    }
    return ""
}

# ============================================================ presentación
Decir ""
Decir "============================================================" "Cyan"
Decir "  Actualizar el Sistema de Viáticos desde GitHub" "Cyan"
Decir "============================================================" "Cyan"
Decir ""

# ------------------------------------------------------------- repositorio
if ($Repo -notmatch "github\.com[/:]([^/]+)/([^/.#]+)") {
    Fallar "La dirección del repositorio no parece de GitHub: $Repo"
}
$Dueno = $Matches[1]
$Nombre = $Matches[2] -replace "\.git$", ""
$Api = "https://api.github.com/repos/$Dueno/$Nombre"
$Crudo = "https://raw.githubusercontent.com/$Dueno/$Nombre/$Rama"
Decir "Repositorio: $Dueno/$Nombre   rama: $Rama"

# ------------------------------------------------------- carpeta del programa
$App = "$App".Trim().Trim('"').TrimEnd('\')
if (-not $App) { $App = Buscar-Instalacion }
if (-not $App -and -not $Simular -and -not $SinPausa) {
    Decir ""
    Decir "No encontré la carpeta del programa." "Yellow"
    Decir "Escriba la ruta donde está el programa (ENTER para cancelar):" "Yellow"
    $respuesta = Read-Host
    if ($respuesta) { $App = $respuesta.Trim().Trim('"').TrimEnd('\') }
}
if (-not $App) { Fallar "No se indicó la carpeta del programa. Use -App ""D:\Viaticos""." }
if (-not (Test-Instalacion $App)) {
    Fallar "En '$App' no está el Sistema de Viáticos (no hay $NombreExe ni main_qt.py)."
}
$App = (Resolve-Path -LiteralPath $App).Path

$script:Log = Join-Path $App "actualizacion.log"
$ExeLocal = Join-Path $App $NombreExe
$ArchivoLocal = Join-Path $App "version.txt"

Decir "Carpeta del programa: $App"
Decir ""

if ($SoloAccesos) {
    if (-not (Test-Path -LiteralPath $ExeLocal)) { Fallar "No hay $NombreExe en $App." }
    Decir "Revisando los accesos directos ..."
    $r = Reparar-Accesos $ExeLocal -Simular:$Simular
    Guardar-Ruta $App
    Decir ""
    Decir ("Listo: {0} re-apuntado(s), {1} creado(s)." -f $r.Cambiados, $r.Creados) "Green"
    if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
    exit 0
}

# ------------------------------------------------------------ versión de aquí
$VersionLocal = ""
if (Test-Path -LiteralPath $ArchivoLocal) {
    $VersionLocal = (Get-Content -LiteralPath $ArchivoLocal -TotalCount 1).Trim()
}
if (-not $VersionLocal) { $VersionLocal = "0" }
Decir "Versión instalada: $VersionLocal"

# --------------------------------------------------------- versión de GitHub
$VersionRemota = ""
try {
    $respuesta = Invoke-WebRequest -Uri "$Crudo/version.txt" -UseBasicParsing -TimeoutSec 40
    $VersionRemota = ($respuesta.Content -split "`n")[0].Trim()
} catch {
    Fallar "No pude leer version.txt del repositorio ($Crudo/version.txt). Revise la dirección, la rama y que el repositorio sea público."
}
if (-not $VersionRemota) { Fallar "El repositorio no dice qué versión tiene (version.txt vacío)." }
Decir "Versión en GitHub:  $VersionRemota"
Decir ""

$TieneCodigo = Test-Path -LiteralPath (Join-Path $App "main_qt.py")
$TieneExe = Test-Path -LiteralPath $ExeLocal
$AlDia = ($VersionRemota -eq $VersionLocal)

if ($AlDia -and -not $Forzar -and $TieneExe) {
    Decir "El sistema ya está al día (versión $VersionLocal). No hay nada que bajar." "Green"
    Decir ""
    Guardar-Ruta $App
    if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
    exit 0
}

$UrlExe = Buscar-ExeRemoto
if ($UrlExe) {
    Decir "Ejecutable publicado: sí" "DarkGray"
} else {
    Decir "Ejecutable publicado: no (la versión no trae un .exe adjunto)" "Yellow"
}
Decir ""

if ($Simular) {
    Decir "(-Simular) No se copiará nada. Esto es lo que haría:" "Yellow"
    Decir ("  versión {0}  ->  {1}" -f $VersionLocal, $VersionRemota)
    if ($TieneCodigo) { Decir "  código: se reemplaza (.py, .bat, .md y documentacion\)" }
    else { Decir "  código: no (esta PC solo tiene el ejecutable)" }
    if ($UrlExe) { Decir "  ejecutable: se baja de la última versión publicada" }
    elseif ($TieneExe) { Decir "  ejecutable: no hay uno publicado (se avisará y no se tocará)" "Yellow" }
    else { Decir "  ejecutable: esta PC no tiene .exe" }
    Decir "  respaldo: respaldos_actualizacion\AAAA-MM-DD_HHMM"
    $r = Reparar-Accesos $ExeLocal -Simular
    Decir ""
    if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
    exit 0
}

# ------------------------------------------------- el programa está abierto
$procesos = @(Get-Process -Name "Sistema_Viaticos" -ErrorAction SilentlyContinue)
if ($procesos.Count -gt 0) {
    Decir "El programa está abierto." "Yellow"
    $seguir = "S"
    if (-not $SinPausa) { $seguir = Read-Host "  ¿Lo cierro ahora para poder actualizar? (S/n)" }
    if ($seguir -match "(?i)^(n|no)$") { Fallar "Cierre el programa y vuelva a ejecutar la actualización." }
    $procesos | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    if (Get-Process -Name "Sistema_Viaticos" -ErrorAction SilentlyContinue) {
        Fallar "El programa no se cerró. Ciérrelo a mano (Administrador de tareas) y vuelva a intentar."
    }
}

# ------------------------------------------------------------------ descarga
$Tmp = Join-Path $env:TEMP ("viaticos_actualizacion_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $Tmp -Force | Out-Null
$Zip = Join-Path $Tmp "sistema.zip"
$UrlZip = "https://codeload.github.com/$Dueno/$Nombre/zip/refs/heads/$Rama"
$ExeNuevo = ""
$CarpetaNueva = ""

try {
    Decir ""
    $tam = Descargar $UrlZip $Zip
    Decir ("  bajaron {0:N0} KB de código" -f ($tam / 1KB)) "DarkGray"
    $Carpeta = Join-Path $Tmp "nuevo"
    Expand-Archive -Path $Zip -DestinationPath $Carpeta -Force
} catch {
    Fallar "No se pudo bajar o descomprimir la versión nueva: $($_.Exception.Message)"
}

$encontrado = Get-ChildItem -Path $Carpeta -Filter "main_qt.py" -Recurse -File -ErrorAction SilentlyContinue |
              Sort-Object { ($_.FullName -split "\\").Count } | Select-Object -First 1
if ($encontrado) { $CarpetaNueva = Split-Path -Parent $encontrado.FullName }

# El .exe puede venir dentro del .zip o como adjunto de la versión publicada.
$enZip = Get-ChildItem -Path $Carpeta -Filter $NombreExe -Recurse -File -ErrorAction SilentlyContinue |
         Sort-Object Length -Descending | Select-Object -First 1
if ($enZip) { $ExeNuevo = $enZip.FullName }

if ($UrlExe) {
    $descargado = Join-Path $Tmp $NombreExe
    try {
        $tamExe = Descargar $UrlExe $descargado 5MB
    } catch {
        Fallar "No se pudo bajar $NombreExe de la última versión publicada: $($_.Exception.Message)"
    }
    Decir ("  ejecutable: {0:N1} MB" -f ($tamExe / 1MB)) "DarkGray"
    $ExeNuevo = $descargado
}

if ($TieneCodigo) {
    if (-not $CarpetaNueva) {
        Fallar "El archivo bajado no parece el Sistema de Viáticos (no tiene main_qt.py). No se cambió nada."
    }
    foreach ($necesario in @("database.py", "calculos.py", "main_qt.py")) {
        if (-not (Test-Path -LiteralPath (Join-Path $CarpetaNueva $necesario))) {
            Fallar "La versión nueva no trae $necesario. No se cambió nada."
        }
    }
}

if ($TieneExe -and -not $ExeNuevo) {
    Fallar ("La versión {0} está publicada, pero no trae {1}.`n    El autor tiene que adjuntarlo a la 'release' de GitHub`n    (ver documentacion\ACTUALIZACION_por_github.md). No se cambió nada." -f $VersionRemota, $NombreExe)
}

# ------------------------------------------------------------------ respaldo
$Sello = Get-Date -Format "yyyy-MM-dd_HHmm"
$Respaldo = Join-Path $App ("respaldos_actualizacion\" + $Sello)
New-Item -ItemType Directory -Path $Respaldo -Force | Out-Null
Decir ""
Decir "Guardando la versión actual en respaldos_actualizacion\$Sello ..."
robocopy $App $Respaldo /E /XD data .git respaldos_actualizacion __pycache__ dist build /XF *.pyc *.db config.json actualizacion.log *.exe /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) {
    Fallar "No se pudo guardar la copia de la versión actual (código $LASTEXITCODE). No se cambió nada."
}

# ------------------------------------------------------------------- copiado
#  Se reemplaza el programa, pero NUNCA los datos:
#    data\  ·  config.json  ·  *.db  ·  los respaldos de actualización  ·  el log
if ($TieneCodigo -and $CarpetaNueva) {
    Decir "Copiando la versión $VersionRemota ..."
    robocopy $CarpetaNueva $App /E /XD data .git respaldos_actualizacion __pycache__ dist build /XF config.json *.db actualizacion.log *.pyc *.exe /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
    $codigo = $LASTEXITCODE
    if ($codigo -ge 8) {
        Decir ""
        Decir "*** Falló la copia (código $codigo). ***" "Red"
        Decir "La versión anterior quedó guardada en: $Respaldo" "Yellow"
        Decir "Para volver atrás, copie esa carpeta encima de $App (sin tocar data\)." "Yellow"
        if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
        exit 1
    }
}

# --------------------------------------------------------- el ejecutable
if ($ExeNuevo) {
    Decir "Reemplazando $NombreExe ..."
    try {
        Copy-Item -LiteralPath $ExeNuevo -Destination $ExeLocal -Force
    } catch {
        Fallar ("No se pudo reemplazar {0}: {1}`n    Cierre el programa y vuelva a intentar. La versión anterior está en {2}" -f $NombreExe, $_.Exception.Message, $Respaldo)
    }
    if (-not (Test-Path -LiteralPath $ExeLocal) -or (Get-Item -LiteralPath $ExeLocal).Length -lt 1MB) {
        Fallar "El $NombreExe copiado quedó incompleto. La versión anterior está en $Respaldo"
    }
}

# ------------------------------------------------------------- versión nueva
Set-Content -LiteralPath $ArchivoLocal -Value $VersionRemota -Encoding ASCII
Guardar-Ruta $App

# --------------------------------------------------------- accesos directos
$r = [pscustomobject]@{ Cambiados = 0; Creados = 0 }
if (Test-Path -LiteralPath $ExeLocal) {
    Decir ""
    Decir "Revisando los accesos directos ..."
    $r = Reparar-Accesos $ExeLocal
}

Decir ""
Decir "============================================================" "Green"
Decir "  Listo: el sistema quedó en la versión $VersionRemota" "Green"
Decir "============================================================" "Green"
Decir "  Sus datos NO se tocaron (data\, config.json, *.db)."
Decir ("  Accesos directos: {0} re-apuntado(s), {1} creado(s)." -f $r.Cambiados, $r.Creados)
Decir "  Copia de la versión anterior: respaldos_actualizacion\$Sello"
Decir ""
Decir "  Si algo no arranca, copie la carpeta del respaldo encima de:"
Decir "     $App"
Decir "  (el ejecutable anterior no se guarda en el respaldo: se puede volver a"
Decir "   bajar de la versión anterior en GitHub)."
Decir ""

if ($Abrir -and (Test-Path -LiteralPath $ExeLocal)) {
    Decir "  Abriendo el programa ..."
    Start-Process -FilePath $ExeLocal -WorkingDirectory $App
}

try { Remove-Item -Path $Tmp -Recurse -Force -ErrorAction SilentlyContinue } catch { }
if (-not $SinPausa) { Read-Host "ENTER para cerrar" | Out-Null }
exit 0

