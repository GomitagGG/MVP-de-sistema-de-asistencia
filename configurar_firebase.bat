@echo off
REM =====================================================
REM  Configuracion de Firebase (credential) en este PC
REM =====================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo =====================================================
echo  CONFIGURACION DE FIREBASE
echo =====================================================
echo.

if not exist "config" mkdir config

if exist "config\firebase-key.json" (
    echo Ya existe config\firebase-key.json. Todo listo.
    echo (input>nul
    goto fin
)

echo Buscando el archivo de credencial en el equipo...
set "ENCONTRADA="
for /r "%USERPROFILE%\Downloads" %%f in (*firebase*.json) do (
    set "ENCONTRADA=%%f"
    goto hallada
)
for /r "%USERPROFILE%\Desktop" %%f in (*firebase*.json) do (
    set "ENCONTRADA=%%f"
    goto hallada
)

:hallada
if defined ENCONTRADA (
    echo Encontrada: !ENCONTRADA!
    copy /y "!ENCONTRADA!" "config\firebase-key.json" >nul
    echo Copiada a config\firebase-key.json
    goto fin
)

echo.
echo NO se encontro el archivo de credencial en Downloads/Escritorio.
echo.
echo Pidelo a tu equipo y guardalo como:
echo     config\firebase-key.json
echo (dentro de la carpeta del proyecto, con ese nombre exacto).
echo.

:fin
if exist "config\firebase-key.json" (
    echo.
    echo OK: config\firebase-key.json presente.
) else (
    echo AUN FALTA: la credencial no esta en config\.
)
echo.
pause