@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
rem  PUBLICAR_VERSION.bat   (lo usa el AUTOR, no las computadoras de trabajo)
rem
rem  Sube el numero de version, hace el commit, lo manda a GitHub y abre la
rem  pagina para adjuntar el ejecutable (.exe) de la version nueva.
rem
rem  Uso:   doble clic                     sube la version en 1
rem         PUBLICAR_VERSION.bat 12        deja la version 12
rem
rem  Antes de publicar: pruebe el sistema (correr_pruebas.bat), empaquete el
rem  .exe (EMPAQUETAR_EXE_SERVIDOR.bat) y tenga el repositorio con
rem  git remote -v  apuntando a GitHub.
rem =====================================================================
chcp 65001 > nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   Publicar una version nueva en GitHub
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo *** No encuentro git. Instalelo ^(https://git-scm.com/download/win^) y vuelva a probar. ***
  pause
  exit /b 1
)
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo *** Esta carpeta no es un repositorio git. ***
  echo.
  echo   Una sola vez, desde esta carpeta:
  echo       git init
  echo       git remote add origin https://github.com/USUARIO/REPOSITORIO.git
  echo       git add -A
  echo       git commit -m "Primera version"
  echo       git branch -M main
  echo       git push -u origin main
  echo.
  pause
  exit /b 1
)
git remote >nul 2>nul
for /f "delims=" %%R in ('git remote') do set HAY_REMOTO=1
if not defined HAY_REMOTO (
  echo *** El repositorio no tiene remoto ^(a donde subir^). ***
  echo       git remote add origin https://github.com/USUARIO/REPOSITORIO.git
  pause
  exit /b 1
)

if not exist "version.txt" echo 0 > version.txt
set NUEVA=%~1
if "%NUEVA%"=="" (
  set NUEVA=
  set /p NUEVA=<version.txt
  set /a NUEVA=NUEVA+1
)
> version.txt echo %NUEVA%
echo  Version nueva:
type version.txt
echo.

git add -A
git commit -m "Version %NUEVA% - %DATE% %TIME%"
if errorlevel 1 (
  echo.
  echo  ^(No habia cambios que confirmar o el commit no se pudo hacer.^)
)
git push
if errorlevel 1 (
  echo.
  echo *** No se pudo subir a GitHub. Revise su usuario/clave o su conexion. ***
  pause
  exit /b 1
)

rem ------------------------------------------------------------- el ejecutable
set "EXE="
for %%D in (
  "%~dp0dist\Sistema_Viaticos.exe"
  "%~dp0..\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
  "%~dp0..\..\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
  "%~dp0..\PARA_GITHUB\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
  "%~dp0..\..\PARA_GITHUB\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
) do if not defined EXE if exist %%D set "EXE=%%~fD"

echo.
echo ============================================================
echo  Version %NUEVA% subida al repositorio.
echo ============================================================
echo.
echo  FALTA UN PASO: adjuntar el ejecutable a la version de GitHub.
echo.

if not defined EXE (
  echo  *** No encontre dist\Sistema_Viaticos.exe ***
  echo      Empaquete primero con EMPAQUETAR_EXE_SERVIDOR.bat.
  echo      Si la version ya esta publicada, adjunte el .exe con
  echo      "Edit release" en GitHub ^(NO vuelva a ejecutar este .bat:
  echo      subiria el numero de version otra vez^).
  echo.
  goto :abrir_pagina
)

for %%F in ("%EXE%") do (
  echo   Ejecutable: %%~fF
  echo   Tamano    : %%~zF bytes
  echo   Fecha     : %%~tF
)
echo.
echo   SHA256 (para comprobar que llego igual a las PC):
for /f "delims=" %%H in ('powershell -NoProfile -Command "(Get-FileHash -LiteralPath '%EXE%' -Algorithm SHA256).Hash"') do echo      %%H
echo.
echo   En la pagina de GitHub que se abre:
echo      1. Arrastre Sistema_Viaticos.exe a "Attach binaries ..."
echo      2. Publish release
echo.

:abrir_pagina
if defined EXE start "" explorer /select,"%EXE%"
start "" "https://github.com/RICHARDs01001/sistema-viaticos/releases/new?tag=v%NUEVA%&title=Version%%20%NUEVA%"

echo  Cuando la version este publicada, en cada PC se ejecuta:
echo      ACTUALIZAR_DESDE_GITHUB.bat
echo.
echo ============================================================
echo.
pause
