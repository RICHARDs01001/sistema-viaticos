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
rem  Borra las tareas programadas del respaldo automatico.
rem  Se usa cuando hay que cambiar la hora o la clave, o cuando
rem  quiere dejar de respaldar solo. Correr EN EL SERVIDOR.
rem
rem  Uso:   QUITAR_RESPALDO_DIARIO.bat
rem
rem  (Los archivos ya respaldados en respaldos_base NO se tocan.)
rem ============================================================
net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo *** Se necesitan permisos de Administrador. Se pedira permiso...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo ============================================================
echo   Quitar las tareas de respaldo automatico
echo ============================================================
echo.
schtasks /Delete /TN "Viaticos - respaldo diario" /F
schtasks /Delete /TN "Viaticos - respaldo mediodia" /F
echo.
echo Tareas que quedan con el nombre "Viaticos - respaldo":
schtasks /Query /FO TABLE 2>nul | findstr /i "Viaticos - respaldo"
echo.
echo (Si no aparece ninguna linea arriba, ya no hay tareas de respaldo.)
echo.
pause
