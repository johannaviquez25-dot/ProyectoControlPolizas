#!/bin/bash
# =====================================================================
#  iniciar_app.command - enciende la app de control de polizas (macOS)
#  Uso: doble clic sobre este archivo.
#  (Es el equivalente de iniciar_app.bat en Windows)
# =====================================================================

# --- Nos ubicamos en la carpeta del proyecto ---
# dirname "$0" es la carpeta donde vive este archivo.
# Las comillas son importantes: la ruta tiene espacios y termina en uno.
cd "$(dirname "$0")" || exit 1

# --- Buscamos uv ---
# Primero en el PATH; si no aparece, en su ruta habitual de instalacion.
if command -v uv >/dev/null 2>&1; then
  UV="uv"
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
else
  echo ""
  echo "No se encontro uv en este equipo."
  echo "Instalalo con este comando:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "Despues volve a hacer doble clic en este archivo."
  echo ""
  read -n 1 -s -r -p "Presiona una tecla para cerrar..."
  echo ""
  exit 1
fi

# --- Mensajes para que sepas que esta pasando ---
echo "Encendiendo la app de control de polizas..."
echo "Direccion: http://127.0.0.1:5001"
echo "Para apagarla: cerra esta ventana o presiona Ctrl + C."
echo ""

# --- Abrimos el navegador 3 segundos despues ---
# Los parentesis y el "&" lo mandan a segundo plano, asi no frena la app.
# El "sleep 3" le da tiempo a Flask para arrancar.
( sleep 3; open "http://127.0.0.1:5001" ) &

# --- Encendemos la app ---
# Esta linea se queda activa mientras la app este corriendo.
"$UV" run app.py

# --- Si la app se detiene, dejamos la ventana abierta ---
echo ""
echo "La app se detuvo."
read -n 1 -s -r -p "Presiona una tecla para cerrar..."
echo ""
