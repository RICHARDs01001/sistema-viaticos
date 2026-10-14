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
rem ============================================================
rem  Crea (una sola vez) la tarea programada que respalda la base
rem  central TODAS LAS NOCHES. HAY QUE CORRERLO EN EL SERVIDOR
rem  (el que tiene PostgreSQL). Se abre solo como Administrador.
rem
rem  Ya trae puestos los datos (no hay que escribir nada):
rem    Servidor ...........: 127.0.0.1  (el propio equipo: el respaldo
rem                         corre EN el servidor y no pasa por la red)
rem    Puerto .............: 2345
rem    Usuario ............: miempresa
rem    PostgreSQL .........: 18   (C:\Program Files\PostgreSQL\18\bin)
rem                         (si el servidor tuviera otra version, el
rem                          script la busca solo: 16, 17, 19...)
rem    Hora ...............: 21:00, todos los dias
rem    Respaldos viejos ...: NO se borra ninguno
rem
rem  Uso:   PROGRAMAR_RESPALDO_DIARIO.bat
rem         PROGRAMAR_RESPALDO_DIARIO.bat <puerto> <clave> <servidor> <hora>
rem  Los 4 datos son OPCIONALES y van en ese orden: puerto, clave, servidor
rem  y hora. Lo que no se escriba queda con el valor de la lista de arriba.
rem  Ejemplos:
rem    PROGRAMAR_RESPALDO_DIARIO.bat                                    <- lo normal
rem    PROGRAMAR_RESPALDO_DIARIO.bat 2345 miempresa 192.168.1.4       <- con la IP de la red
rem    PROGRAMAR_RESPALDO_DIARIO.bat 2345 miempresa 127.0.0.1 22:30    <- cambiando la hora
rem
rem  Apunta SIEMPRE a esta misma carpeta: la tarea llama al
rem  respaldar_base_nativo.bat que esta junto a este archivo
rem  (%~dp0), asi que si el servidor lo tiene en
rem  C:\MIEMPRESA_VIATICOS\servidor la tarea queda apuntando ahi
rem  y no hay que escribir ninguna ruta a mano.
rem
rem  Deja UNA tarea:  "Viaticos - respaldo diario" (todas las noches)
rem  Para borrarla:   QUITAR_RESPALDO_DIARIO.bat
rem ============================================================

rem --- parametros (todos opcionales: ya tienen los datos del servidor) ---
set PUERTO=%~1
if "%PUERTO%"=="" set PUERTO=2345
set CLAVE=%~2
if "%CLAVE%"=="" set CLAVE=miempresa
set SERVIDOR=%~3
rem  Por defecto el respaldo se conecta al PROPIO equipo (127.0.0.1): asi no
rem  depende de la red ni del firewall. Para sacarlo DESDE otra PC, la IP.
if "%SERVIDOR%"=="" set SERVIDOR=127.0.0.1
set HORA=%~4
if "%HORA%"=="" set HORA=21:00
rem  0 = NO borrar nunca respaldos viejos (se guardan todos)
set DIAS=0
set TAREA=Viaticos - respaldo diario

rem --- hace falta ser Administrador (la tarea corre como SYSTEM) ----
net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo *** Se necesitan permisos de Administrador.
  echo     Se va a abrir una ventana nueva y Windows pedira permiso.
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%PUERTO% %CLAVE% %SERVIDOR% %HORA%' -Verb RunAs"
  exit /b
)

echo ============================================================
echo   Respaldo automatico de la base de viaticos
echo   (todas las noches, sin borrar los respaldos viejos)
echo ============================================================
echo.
echo  Carpeta de este script ....: %~dp0
echo  Servidor PostgreSQL .......: %SERVIDOR%
echo  Puerto ....................: %PUERTO%
echo  Usuario ...................: miempresa
echo  Version de PostgreSQL .....: 18, o la que este instalada
echo  Hora del respaldo .........: %HORA%, todos los dias
echo  Borra respaldos viejos ....: NO
echo.
echo  El respaldo corre EN EL PROPIO SERVIDOR y se conecta a
echo  127.0.0.1 ^(el mismo equipo^): no pasa por la red ni por el firewall.
echo  Si prefiere que se conecte por la IP de la red, ejecutelo asi:
echo      PROGRAMAR_RESPALDO_DIARIO.bat 2345 miempresa 192.168.1.4
echo.

rem --- 1) comprobar que el respaldo FUNCIONA (antes de programar) ---
echo [1/3] Probando un respaldo AHORA (puede tardar unos segundos)...
call "%~dp0respaldar_base_nativo.bat" %CLAVE% %PUERTO% %SERVIDOR% 0 < nul
rem  No se confia en el codigo de salida del script: se revisa el ARCHIVO
rem  que acaba de dejar (el mas nuevo) y que este COMPLETO.
set ARCHIVO=
for /f "delims=" %%F in ('dir /b /o-d "respaldos_base\viaticos_20*.sql" 2^>nul') do if not defined ARCHIVO set ARCHIVO=%%F
if not defined ARCHIVO (
  echo.
  echo *** No se genero ningun archivo en respaldos_base\.
  echo     Revise el mensaje de arriba y vuelva a ejecutar este archivo.
  pause
  exit /b 1
)
set COMPLETO=
for /f "delims=" %%L in ('findstr /c:"PostgreSQL database dump complete" "respaldos_base\%ARCHIVO%"') do set COMPLETO=%%L
if not defined COMPLETO (
  echo.
  echo *** El respaldo %ARCHIVO% quedo INCOMPLETO, asi que NO se creo la tarea.
  echo     Borre ese archivo de respaldos_base\ y vuelva a ejecutar este archivo.
  pause
  exit /b 1
)
echo     OK: respaldos_base\%ARCHIVO% esta completo y sirve.

rem --- 2) crear la tarea de la noche ------------------------------
echo.
echo [2/3] Creando la tarea "%TAREA%" (todos los dias a las %HORA%)...
rem  El ultimo numero (%DIAS%) = 0 -> NO borrar nunca los respaldos viejos
rem  La palabra "auto" al final = el respaldo NO se queda esperando una tecla
rem  (si se quedara, la tarea se veria "En ejecucion" y las noches siguientes
rem  ya no respaldarian).
schtasks /Create /TN "%TAREA%" /TR "\"%~dp0respaldar_base_nativo.bat\" %CLAVE% %PUERTO% %SERVIDOR% %DIAS% auto" /SC DAILY /ST %HORA% /RU SYSTEM /RL HIGHEST /F
if errorlevel 1 (
  echo.
  echo *** No se pudo crear la tarea "%TAREA%". Vea el mensaje de arriba.
  pause
  exit /b 1
)

rem --- 3) revisar y probar ----------------------------------------
echo.
echo [3/3] Asi quedo la tarea:
echo.
schtasks /Query /TN "%TAREA%" /FO LIST /V | findstr /i /c:"Nombre de tarea" /c:"Estado:" /c:"resultado" /c:"Hora pr" /c:"Tarea que se ejecutar" /c:"Ejecutar como"
echo.
echo Ejecutando la tarea ahora mismo para comprobar que funciona...
schtasks /Run /TN "%TAREA%"
echo.
echo ============================================================
echo  LISTO.  Espere 1 minuto y compruebe:
echo    1) que arriba diga  Estado: Listo   y   Ultimo resultado: 0
echo    2) que haya un archivo NUEVO en:  %~dp0respaldos_base\
echo  El respaldo corre solo TODAS LAS NOCHES a las %HORA%.
echo ============================================================
echo.
echo LOS RESPALDOS NO SE BORRAN NUNCA: se guardan todos en
echo   %~dp0respaldos_base\
echo Copie esa carpeta a un USB o a la nube de vez en cuando: si el
echo servidor se daña, el respaldo tiene que estar FUERA de el.
echo.
pause
