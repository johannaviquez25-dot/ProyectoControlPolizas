@echo off
REM =====================================================================
REM  iniciar_app.bat - enciende la app de control de polizas (Windows)
REM  Uso: doble clic sobre este archivo.
REM =====================================================================

REM Nos ubicamos en la carpeta donde vive este .bat, aunque la ruta
REM tenga espacios. %~dp0 es la carpeta del propio archivo.
cd /d "%~dp0"

REM --- Comprobamos que uv este instalado y disponible ---
REM where uv busca el programa en el PATH. Si no lo encuentra, avisa.
where uv >nul 2>nul
if errorlevel 1 (
  echo.
  echo No se encontro uv en este equipo.
  echo Instalalo con este comando en PowerShell:
  echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
  echo Despues cierra esta ventana y vuelve a intentarlo.
  echo.
  pause
  exit /b 1
)

REM --- Mensajes para que sepas que esta pasando ---
echo Encendiendo la app de control de polizas...
echo Direccion: http://127.0.0.1:5001
echo Para apagarla: cierra esta ventana o presiona Ctrl + C.
echo.

REM --- Abrimos el navegador 3 segundos despues ---
REM Asi Flask ya tuvo tiempo de arrancar y la pagina carga de una vez.
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5001"

REM --- Encendemos la app ---
REM Esta linea se queda activa mientras la app este corriendo.
uv run app.py

REM --- Si la app se detiene, dejamos la ventana abierta ---
echo.
echo La app se detuvo.
pause
