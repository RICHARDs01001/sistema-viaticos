@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
rem  SUBIR_EXE_A_GITHUB.bat
rem
rem  Sube la versión nueva y deja el .exe adjunto a la versión de GitHub,
rem  que es de donde lo bajan las PCs de la empresa.
rem
rem  Hace todo esto, sin entrar a la página de GitHub:
rem    1. sube el número de version.txt (8 -> 9);
rem    2. git add -A, commit y push;
rem    3. crea la versión vN en GitHub y le adjunta Sistema_Viaticos.exe.
rem
rem  Uso:   doble clic .......................... sube version.txt + 1
rem         SUBIR_EXE_A_GITHUB.bat 12 .......... publica la versión 12
rem         SUBIR_EXE_A_GITHUB.bat 12 "D:\Sistema_Viaticos.exe"
rem
rem  Necesita el GitHub CLI (gh) con la sesión ya iniciada:
rem         gh auth status        (tiene que decir "Logged in")
rem  Este .bat va en la RAÍZ del repositorio (carpeta PARA_GITHUB_LIMPIO).
rem =====================================================================
chcp 65001 >nul
setlocal EnableExtensions
pushd "%~dp0" 2>nul

echo ============================================================
echo   Publicar una version nueva (con el .exe adjunto)
echo ============================================================
echo.

rem --- 1. gh instalado y con sesion ---------------------------------------
where gh >nul 2>&1
if errorlevel 1 (
    echo *** No encuentro el GitHub CLI ^(gh^). ***
    echo     Instalelo con:  winget install --id GitHub.cli
    echo     Despues:        gh auth login
    goto :fin_error
)
gh auth status >nul 2>&1
if errorlevel 1 (
    echo *** El GitHub CLI no tiene la sesion iniciada. ***
    echo     Ejecute una vez:  gh auth login
    goto :fin_error
)

rem --- 2. el .exe ---------------------------------------------------------
set "EXE=%~2"
if "%EXE%"=="" set "EXE=..\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
if not exist "%EXE%" set "EXE=..\PARA_GITHUB\sistema_viaticos_miempresa\dist\Sistema_Viaticos.exe"
if not exist "%EXE%" (
    echo *** No encuentro Sistema_Viaticos.exe. ***
    echo     Primero empaquete el ejecutable ^(EMPAQUETAR_EXE.bat^).
    echo     O indiquelo:  SUBIR_EXE_A_GITHUB.bat 12 "D:\ruta\Sistema_Viaticos.exe"
    goto :fin_error
)
for %%F in ("%EXE%") do set "EXE=%%~fF"
echo Ejecutable: %EXE%

rem --- 3. numero de version ----------------------------------------------
set "NUEVA=%~1"
if "%NUEVA%"=="" (
    set "ACTUAL=0"
    if exist "version.txt" set /p ACTUAL=<version.txt
    set /a NUEVA=ACTUAL+1
)
echo Version nueva: %NUEVA%
echo.

rem --- 4. version.txt en la raiz y en la carpeta del programa --------------
> "version.txt" echo %NUEVA%
for /d %%D in (sistema_viaticos_*) do > "%%D\version.txt" echo %NUEVA%

rem --- 5. commit y push ---------------------------------------------------
echo == Subiendo el codigo a GitHub ...
git add -A
if errorlevel 1 goto :fin_error
git commit -m "Version %NUEVA% - publicada con SUBIR_EXE_A_GITHUB.bat"
git push origin main
if errorlevel 1 (
    echo.
    echo *** No pude hacer push. Revise la conexion o el estado de git. ***
    goto :fin_error
)
echo.

rem --- 6. la version en GitHub con el .exe adjunto ------------------------
echo == Creando la version v%NUEVA% y adjuntando el .exe ...
echo     ^(son 73 MB: la subida tarda un rato, no cierre esta ventana^)
gh release view v%NUEVA% >nul 2>&1
if errorlevel 1 (
    gh release create v%NUEVA% "%EXE%" --title "Sistema de Viaticos v%NUEVA%" --notes "Version %NUEVA%: actualizacion desde GitHub. El ejecutable va adjunto a esta version." --latest
) else (
    gh release upload v%NUEVA% "%EXE%" --clobber
)
if errorlevel 1 (
    echo.
    echo *** No pude publicar la version. ***
    echo     Si el codigo ya subio, la version queda a medias: repita este .bat
    echo     con el mismo numero ^(no lo incremente otra vez^).
    goto :fin_error
)

echo.
echo ============================================================
echo   Listo: version v%NUEVA% publicada con el .exe adjunto
echo ============================================================
echo   Version publicada : %NUEVA%
echo   Descarga directa : https://github.com/RICHARDs01001/sistema-viaticos/releases/latest/download/Sistema_Viaticos.exe
echo   En cada PC       : doble clic en ACTUALIZAR_DESDE_GITHUB.bat
echo.
pause
popd
exit /b 0

:fin_error
echo.
pause
popd
exit /b 1
