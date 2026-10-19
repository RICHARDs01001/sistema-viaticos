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
rem  Empaqueta el .exe dejandolo apuntando al SERVIDOR NUEVO
rem
rem  Uso:   EMPAQUETAR_EXE_SERVIDOR.bat
rem         EMPAQUETAR_EXE_SERVIDOR.bat 192.168.22.185 5432
rem
rem  IMPORTANTE: la IP y el puerto quedan DENTRO del ejecutable
rem  (se escriben como valor de fabrica en configuracion.py, con
rem  respaldo configuracion.py.bak). Por eso a las otras PC se
rem  copia UNICAMENTE  dist\Sistema_Viaticos.exe : no hace falta
rem  llevar ningun archivo extra.
rem ============================================================
echo ============================================================
echo   Empaquetar "Sistema de Viaticos" para el SERVIDOR NUEVO
echo ============================================================
echo.
echo  La IP y el puerto quedan DENTRO del .exe: a las otras PC se
echo  copia solo  dist\Sistema_Viaticos.exe
echo.
echo  Requisitos:  pip install pyinstaller psycopg2-binary openpyxl pillow
echo  Todo el empaquetado esta en Sistema_Viaticos.spec
echo.

set IP=%~1
if "%IP%"=="" set /p IP=Escriba la IP del servidor (ej. 192.168.22.185):
if "%IP%"=="" (
  echo.
  echo *** Falta la IP del servidor. ***
  pause
  exit /b 1
)

set PUERTO=%~2
if "%PUERTO%"=="" set /p PUERTO=Puerto del servidor (Enter = 5432):
if "%PUERTO%"=="" set PUERTO=5432

set FORZAR=
if not "%IP:~-2%"==".1" goto preguntas
echo.
echo *** ATENCION: la IP %IP% termina en .1 y en casi todas las redes ESA es la IP DEL
echo     ROUTER (la puerta de enlace), NO una computadora. El servidor de viaticos no
echo     puede tener la IP del router: pida una IP libre ^(por ejemplo 192.168.22.185^).
echo     Compruebelo con "ipconfig" y con "ping %IP%" desde otra PC.
echo.
set /p SEGURO=Seguro que la PC servidor tiene la IP %IP% ? (s/N):
if /i not "%SEGURO%"=="s" (
  echo.
  echo  Cancelado: no se empaqueto nada.
  pause
  exit /b 1
)
set FORZAR=--forzar

:preguntas
rem La IP y el puerto se dejan SIEMPRE como valor de fabrica en configuracion.py
rem (--fabrica): asi el .exe ya sale apuntando al servidor por si solo y a las
rem otras computadoras se copia UNICAMENTE el ejecutable.
set OPT_FABRICA=--fabrica

if not exist "icono.ico" (
  echo Generando el icono a partir del logo...
  python -c "from pathlib import Path; from PIL import Image; p=Path('.'); i=Image.open('image.png').convert('RGBA'); n=max(i.size); c=Image.new('RGBA',(n,n),(31,28,255,255)); c.paste(i,((n-i.width)//2,(n-i.height)//2),i); c.save('icono.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
  if not exist "icono.ico" echo *** AVISO: no se pudo crear icono.ico (instale Pillow: pip install pillow^) ***
)

echo.
rem Se borra el codigo de error ANTERIOR (por ejemplo el de las preguntas "set /p"): si no,
rem un "if errorlevel" podria estar viendo ese error viejo y abortar sin motivo.
cmd /c exit 0
python empaquetar_servidor.py %IP% %PUERTO% %OPT_FABRICA% %FORZAR%
set RESULTADO=%ERRORLEVEL%
if not "%RESULTADO%"=="0" (
  echo.
  echo *** No se pudo empaquetar ^(codigo %RESULTADO%^). Revise los mensajes de arriba. ***
  pause
  exit /b %RESULTADO%
)

echo.
echo ============================================================
echo  Cuando termine:
echo   1) A cada PC se copia SOLO este archivo:
echo         dist\Sistema_Viaticos.exe
echo      ^(la IP %IP% y el puerto %PUERTO% ya van DENTRO del .exe^)
echo   2) Si en esa PC ya habia un config.json al lado del .exe
echo      ^(de una version anterior^), borrelo o abra
echo      CONEXION / BASE DE DATOS y confirme que diga %IP%.
echo      OJO: un config.json viejo MANDA sobre la IP de fabrica.
echo   3) En la barra del programa debe decir  BASE CENTRAL.
echo   4) Probar desde otra PC:  ..\servidor\PROBAR_SERVIDOR.bat %IP% %PUERTO%
echo ============================================================
pause
