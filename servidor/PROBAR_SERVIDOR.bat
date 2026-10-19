@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
chcp 65001 > nul
rem ============================================================
rem  Prueba de conexion al servidor de la base central
rem  Uso:   PROBAR_SERVIDOR.bat                        (192.168.22.123 : 5432)
rem         PROBAR_SERVIDOR.bat 192.168.22.123           (solo cambia la IP)
rem         PROBAR_SERVIDOR.bat 192.168.22.123 5433      (IP y puerto)
rem ============================================================
set SERVIDOR=%1
if "%SERVIDOR%"=="" set SERVIDOR=192.168.22.123
set PUERTO=%2
if "%PUERTO%"=="" set PUERTO=5432
echo.
echo Probando el servidor %SERVIDOR% en el puerto %PUERTO% ...
echo (debe decir TcpTestSucceeded : True)
echo.
powershell -NoProfile -Command "$r = Test-NetConnection -ComputerName '%SERVIDOR%' -Port %PUERTO% -WarningAction SilentlyContinue; Write-Host ('Equipo alcanzable ....: ' + $r.PingSucceeded); Write-Host ('Puerto %PUERTO% abierto ..: ' + $r.TcpTestSucceeded)"
echo.
echo Si el puerto aparece como False, revise EN EL SERVIDOR:
echo   1) que PostgreSQL este encendido
echo      ^(Get-Service postgresql*   ^)
echo   2) que escuche en toda la red   ^(listen_addresses = '*'^)
echo   3) que el firewall permita el puerto %PUERTO%
echo   4) que la linea de la red este en pg_hba.conf  ^(ver documentacion\SERVIDOR.md^)
echo.
pause

