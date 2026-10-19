@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
rem  ACTUALIZAR_DESDE_GITHUB.bat
rem
rem  Busca la version nueva del sistema en GitHub y la instala en esta PC,
rem  este donde este la carpeta del programa. No toca los datos: la carpeta
rem  data\, config.json y los *.db se quedan igual.
rem
rem  Uso:   doble clic
rem         ACTUALIZAR_DESDE_GITHUB.bat "D:\Viaticos"
rem         ACTUALIZAR_DESDE_GITHUB.bat https://github.com/usuario/repositorio
rem
rem  Puede estar dentro de la carpeta del programa o en cualquier otra parte
rem  (escritorio, USB, carpeta compartida): siempre baja la ultima version de
rem  herramientas\actualizar.ps1 de GitHub; si no hay Internet usa la que ya
rem  esta en esta PC.
rem =====================================================================
chcp 65001 > nul
setlocal EnableExtensions
rem --- pushd tambien funciona desde una carpeta de red o un USB -----------
pushd "%~dp0" 2>nul

set "AQUI=%~dp0"
set "REPO="
set "CARPETA="
set "ARG=%~1"

rem --- Si el argumento es una direccion de GitHub, es el repositorio -----
if not "%ARG%"=="" for /f "delims=" %%R in ('echo %ARG% ^| findstr /i "github.com"') do set "REPO=%%R"
if defined REPO set "ARG="

rem --- Si el argumento es una carpeta, es la carpeta del programa --------
if not "%ARG%"=="" if exist "%ARG%" set "CARPETA=%ARG%"

rem --- Si este .bat esta dentro de la carpeta del programa, manda esa ----
if exist "%AQUI%main_qt.py" set "CARPETA=%AQUI%"
if exist "%AQUI%Sistema_Viaticos.exe" set "CARPETA=%AQUI%"
if defined CARPETA for %%A in ("%CARPETA%") do set "CARPETA=%%~fA"

echo ============================================================
echo   Actualizar el Sistema de Viaticos desde GitHub
echo ============================================================
echo.

set "PS1=%AQUI%herramientas\actualizar.ps1"
rem --- Se baja SIEMPRE la ultima version del actualizador: asi una PC con ---
rem --- un actualizador viejo no repite fallos que ya se corrigieron.     ---
rem --- El ?v=... evita que GitHub entregue una copia guardada en cache.  ---
echo  Bajando el actualizador de GitHub ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/RICHARDs01001/sistema-viaticos/main/sistema_viaticos_miempresa/herramientas/actualizar.ps1?v=%RANDOM%%RANDOM%' -OutFile '%TEMP%\actualizar_viaticos.ps1' } catch { exit 1 }"
if errorlevel 1 (
  if exist "%PS1%" (
    echo  Sin conexion: uso el actualizador que ya esta en esta PC.
  ) else (
    echo.
    echo *** No pude bajar el actualizador. Revise la conexion a Internet. ***
    pause
    exit /b 1
  )
) else (
  set "PS1=%TEMP%\actualizar_viaticos.ps1"
)

set "ARGS=-NoProfile -ExecutionPolicy Bypass -File "%PS1%""
if defined REPO set "ARGS=%ARGS% -Repo "%REPO%""
if defined CARPETA set "ARGS=%ARGS% -App "%CARPETA%""

powershell %ARGS%
set RESULTADO=%ERRORLEVEL%

if not "%RESULTADO%"=="0" (
  echo.
  echo *** La actualizacion no se completo ^(codigo %RESULTADO%^). ***
  echo     Revise los mensajes de arriba y el archivo actualizacion.log
  pause
  exit /b %RESULTADO%
)
exit /b 0
