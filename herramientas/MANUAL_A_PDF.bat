@echo off
rem =====================================================================
rem  Sistema de Viáticos Miempresa
rem  Autor:    Richard Esteban Salazar Guillén
rem  Contacto: richards0101789@gmail.com  ·  +593 981239086
rem  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
rem  Prohibida su copia, reproducción o distribución sin autorización escrita.
rem =====================================================================
rem Arma el MANUAL_DE_USUARIO.pdf desde el manual en Markdown.
rem Necesita Python con reportlab y fontTools (ya vienen con el proyecto:
rem   pip install reportlab fonttools
rem ). Se puede correr las veces que haga falta: siempre sale igual.
chcp 65001 > nul
cd /d "%~dp0"
python manual_pdf.py
if errorlevel 1 (
    echo.
    echo No se pudo armar el PDF. Lea el mensaje de arriba.
    pause
    exit /b 1
)
echo.
echo Listo: ..\documentacion\MANUAL_DE_USUARIO.pdf
pause
