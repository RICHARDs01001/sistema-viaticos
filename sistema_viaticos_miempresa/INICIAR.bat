@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
rem Sistema de Viáticos — interfaz nueva (PySide6).
rem Si el sistema no arranca, la ventana se queda abierta para poder leer el error.
chcp 65001 > nul
cd /d "%~dp0"
python main_qt.py
if errorlevel 1 pause
