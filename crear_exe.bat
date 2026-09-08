@echo off
REM =====================================================
REM  Creador del ejecutable SistemaAsistencia (Windows)
REM =====================================================
cd /d "%~dp0"

echo.
echo [1/3] Activando entorno virtual...
if not exist "venv\Scripts\python.exe" (
    echo Error: no se encontro venv. Cree el entorno con:
    echo    py -m venv venv
    echo    venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/3] Verificando credencial de Firebase...
if not exist "config" mkdir config
if not exist "config\firebase-key.json" (
    if exist "config\registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json" (
        copy /y "config\registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json" "config\firebase-key.json" >nul
    )
)
if not exist "config\firebase-key.json" (
    if not exist "config\registro-asistencia-bfe64-firebase-adminsdk-fbsvc-1d738c49d5.json" (
        echo.
        echo ATENCION: No se encontro la credencial de Firebase.
        echo Coloque el archivo .json en la carpeta config\ como
        echo "firebase-key.json" o "registro-asistencia-bfe64-firebase-...json"
        echo para que el ejecutable pueda conectarse.
    ) else (
        echo Usando la credencial registro-asistencia-...json (se empaquetara en el exe).
    )
)

echo.
echo [3/3] Compilando ejecutable con PyInstaller...
call venv\Scripts\python.exe -m PyInstaller SistemaAsistencia.spec --noconfirm
if errorlevel 1 (
    echo.
    echo Fallo la compilacion. Revise el mensaje de error.
    pause
    exit /b 1
)

echo.
echo Creando acceso directo en el Escritorio...
set "DESTINO=%USERPROFILE%\OneDrive\Escritorio"
if not exist "%DESTINO%" set "DESTINO=%USERPROFILE%\Desktop"
powershell -NoProfile -Command ^
  "$W = New-Object -ComObject WScript.Shell;" ^
  "$S = $W.CreateShortcut('%DESTINO%\SistemaAsistencia.lnk');" ^
  "$S.TargetPath = '%~dp0dist\SistemaAsistencia.exe';" ^
  "$S.WorkingDirectory = '%~dp0dist';" ^
  "$S.Save()"
if errorlevel 1 (
    echo No se pudo crear el acceso directo. El ejecutable queda en dist\SistemaAsistencia.exe
) else (
    echo ACCESO DIRECTO CREADO: %DESTINO%\SistemaAsistencia.lnk
)

echo.
echo =====================================================
echo  EJECUTABLE GENERADO: dist\SistemaAsistencia.exe
echo =====================================================
pause
