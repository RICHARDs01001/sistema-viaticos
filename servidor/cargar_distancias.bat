@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
chcp 65001 > nul
cd /d "%~dp0"
rem ==========================================================
rem   Carga los km y las horas de viaje en la base central
rem   (PostgreSQL instalado DIRECTO en Windows)
rem
rem   Uso:   cargar_distancias.bat
rem          cargar_distancias.bat viaticos_distancias_ANTES.sql
rem
rem   Lo primero que hace es un RESPALDO (respaldar_base_nativo.bat) y
rem   después carga el archivo indicado. El .sql solo toca la tabla
rem   `distancias` (los km y las horas de las rutas desde Cuenca): los
rem   viáticos, los gastos y los usuarios NO se tocan. Todo va dentro de
rem   una transacción, así que si algo falla NO se guarda nada.
rem
rem   Los archivos .sql los arma:
rem     python herramientas\preparar_distancias_excel.py
rem   El servidor usa PostgreSQL 18, en C:\Program Files\PostgreSQL\18\bin
rem ==========================================================
set ARCHIVO=%1
if "%ARCHIVO%"=="" set ARCHIVO=viaticos_distancias_NUEVO.sql
set CLAVE=%2
if "%CLAVE%"=="" set CLAVE=miempresa
set PUERTO=%3
rem  El servidor de Miempresa tiene PostgreSQL en el puerto 2345
if "%PUERTO%"=="" set PUERTO=2345

echo ==========================================================
echo   Cargar km y horas de viaje en la base central
echo   Archivo: %ARCHIVO%
echo   Puerta %PUERTO%  -  usuario miempresa
echo ==========================================================
echo.
if not exist "%ARCHIVO%" (
  echo *** No se encontro el archivo "%ARCHIVO%" en esta carpeta.
  echo     Copielo aqui (lo genera herramientas\preparar_distancias_excel.py)
  echo     o escriba el nombre completo como primer dato.
  pause
  exit /b 1
)

rem --- buscar psql: primero el 18, que es el del servidor ---
set PGBIN=
if exist "C:\Program Files\PostgreSQL\18\bin\psql.exe" set PGBIN=C:\Program Files\PostgreSQL\18\bin
rem ...y si no estuviera el 18, la version que haya instalada (16, 17, 19...)
if "%PGBIN%"=="" for /d %%D in (C:\Program Files\PostgreSQL\*) do if exist "%%D\bin\psql.exe" set PGBIN=%%D\bin
if "%PGBIN%"=="" (
  echo.
  echo *** No se encontro psql.exe en C:\Program Files\PostgreSQL\
  echo     ^(se busca primero en la version 18^)
  echo     Instale PostgreSQL o copie el .sql al servidor y carguelo alla.
  pause
  exit /b 1
)

echo 1^) Respaldo de la base ^(por si acaso^)...
call respaldar_base_nativo.bat %CLAVE% %PUERTO% 127.0.0.1 0 auto
if errorlevel 1 (
  echo.
  echo *** No se pudo respaldar. NO se cargo nada. Revise el respaldo y vuelva a intentar.
  pause
  exit /b 1
)

echo.
echo 2^) Cargando "%ARCHIVO%" ...
set PGPASSWORD=%CLAVE%
rem OJO: en Windows el psql nativo lee por defecto en la codificacion del sistema
rem (Windows-1252) y las tildes y las enies se danarian. Se fuerza UTF-8, que es
rem como esta creada la base ("ENCODING 'UTF8'").
set PGCLIENTENCODING=UTF8
"%PGBIN%\psql.exe" -h 127.0.0.1 -p %PUERTO% -U miempresa -d viaticos -v ON_ERROR_STOP=1 -f "%ARCHIVO%"
if errorlevel 1 (
  set PGPASSWORD=
  echo.
  echo *** Hubo un error y NO se guardo nada ^(la transaccion se deshizo^).
  echo     Si quiere volver atras, cargue:  cargar_distancias.bat viaticos_distancias_ANTES.sql
  pause
  exit /b 1
)
set PGPASSWORD=
echo.
echo Listo: los km y las horas quedaron guardados en la base central.
echo Abra el sistema y revise PARAMETROS - Provincias y km ^(MACAS debe dar 242 km y 5.67 h^).
pause
