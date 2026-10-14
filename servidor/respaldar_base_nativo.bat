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
rem   Respaldo de la base central de viaticos (PostgreSQL
rem   instalado DIRECTO en Windows)
rem
rem   Uso:   respaldar_base_nativo.bat
rem          respaldar_base_nativo.bat <clave> <puerto>
rem          respaldar_base_nativo.bat <clave> <puerto> <servidor>
rem          respaldar_base_nativo.bat <clave> <puerto> <servidor> <dias>
rem          respaldar_base_nativo.bat <clave> <puerto> <servidor> <dias> auto
rem   ("auto" lo pone la tarea programada: no espera ninguna tecla al final)
rem
rem   <servidor> es la IP del servidor PostgreSQL. Si se omite se usa
rem   127.0.0.1 (el propio equipo, que es el caso normal cuando este
rem   script corre EN el servidor). Poniendo la IP se puede respaldar
rem   tambien DESDE otra PC de la red.
rem   <dias> es la antiguedad con la que se borrarian los respaldos
rem   automaticos viejos. POR DEFECTO ES 0: NO se borra ninguno, se
rem   guardan todos. (Poniendo 30 se borrarian los de mas de 30 dias.)
rem   <auto> es el 5o dato y SOLO lo pone la tarea programada: hace que el
rem   script NO se quede esperando una tecla al terminar. Si se quedara
rem   esperandola, la tarea apareceria "En ejecucion" para siempre y las
rem   noches siguientes YA NO se respaldarian. Si lo corre una persona
rem   (o sea, sin <auto>), si se le pide la tecla, como siempre.
rem   El servidor usa PostgreSQL 18, en C:\Program Files\PostgreSQL\18\bin
rem ==========================================================
set CLAVE=%1
if "%CLAVE%"=="" set CLAVE=miempresa
set PUERTO=%2
rem  El servidor de Miempresa tiene PostgreSQL en el puerto 2345
if "%PUERTO%"=="" set PUERTO=2345
set SERVIDOR=%3
if "%SERVIDOR%"=="" set SERVIDOR=127.0.0.1
set DIAS=%4
if "%DIAS%"=="" set DIAS=0
rem  %ESPERA% = la pausa del final. Con "auto" (lo lanza la tarea) NO espera
rem  ninguna tecla: asi la tarea termina bien y avisa "Ultimo resultado: 0".
rem  (Se usa "pause <nul >nul" para que tampoco muestre el mensaje de la tecla,
rem   que confunde cuando lo lanza la tarea o el programador.)
set ESPERA=pause
if /i "%~5"=="auto" set ESPERA=pause ^<nul ^>nul

rem --- buscar pg_dump: primero el 18, que es el del servidor ---
set PGBIN=
if exist "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" set PGBIN=C:\Program Files\PostgreSQL\18\bin
rem ...y si no estuviera el 18, la version que haya instalada (16, 17, 19...)
if "%PGBIN%"=="" for /d %%D in (C:\Program Files\PostgreSQL\*) do if exist "%%D\bin\pg_dump.exe" set PGBIN=%%D\bin
if "%PGBIN%"=="" (
  echo.
  echo *** No se encontro pg_dump.exe en C:\Program Files\PostgreSQL\
  echo     ^(se busca primero en la version 18^)
  echo     Instale PostgreSQL o ajuste la ruta en este archivo.
  %ESPERA%
  exit /b 1
)

echo ==========================================================
echo   Respaldo de la base central de viaticos (pg_dump)
echo   Servidor %SERVIDOR%, puerto %PUERTO%, usuario miempresa
echo   Usando: %PGBIN%
echo ==========================================================
echo.
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set FECHA=%%i
if not exist respaldos_base mkdir respaldos_base
set PGPASSWORD=%CLAVE%
rem OJO: en Windows el pg_dump nativo escribe por defecto en la codificacion del sistema
rem (Windows-1252) y los nombres con tilde o enie se danaban. Se fuerza UTF-8, que es
rem como esta creada la base ("ENCODING 'UTF8'").
set PGCLIENTENCODING=UTF8
echo Generando respaldos_base\viaticos_%FECHA%.sql ...
"%PGBIN%\pg_dump.exe" -h %SERVIDOR% -p %PUERTO% -U miempresa -d viaticos -F p > "respaldos_base\viaticos_%FECHA%.sql"
if errorlevel 1 (
  set PGPASSWORD=
  echo.
  echo *** No se pudo generar el respaldo. Revise:
  echo     1^) que el servicio este encendido:  Get-Service postgresql*
  echo     2^) la clave del usuario miempresa  ^(parametro 1^)
  echo     3^) el puerto                    ^(parametro 2^)
  echo     4^) que el servidor %SERVIDOR% sea alcanzable  ^(servidor\PROBAR_SERVIDOR.bat^)
  echo     ^(si el respaldo quedo a medias, borre el archivo respaldos_base\viaticos_%FECHA%.sql^)
  %ESPERA%
  exit /b 1
)
set PGPASSWORD=
echo.
echo Listo: respaldos_base\viaticos_%FECHA%.sql
echo Guarde ese archivo en un lugar seguro (servidor o nube).
if "%DIAS%"=="0" goto fin
echo.
echo Limpiando respaldos automaticos de mas de %DIAS% dias (si hubiera)...
rem (solo borra los automaticos: viaticos_20*.sql. Los manuales tipo
rem  viaticos_ANTES_DE_ALGO.sql NUNCA se borran solos)
forfiles /p respaldos_base /m viaticos_20*.sql /d -%DIAS% /c "cmd /c del /q @path" >nul 2>&1
:fin
if "%DIAS%"=="0" echo No se borra ningun respaldo: se guardan todos en respaldos_base\.
%ESPERA%
