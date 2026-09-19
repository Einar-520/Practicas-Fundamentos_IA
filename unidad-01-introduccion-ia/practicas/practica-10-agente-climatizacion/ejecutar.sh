#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
interprete="$proyecto/.venv/bin/python"
if [[ ! -x "$interprete" ]]; then
  echo "Primero crea el entorno virtual desde la raíz del proyecto: python3 -m venv .venv"
  exit 1
fi
if ! "$interprete" -c 'import tkinter' >/dev/null 2>&1; then
  echo "Falta Tkinter. En Ubuntu/WSL ejecuta: sudo apt install python3-tk"
  echo "Utiliza el mismo intérprete del proyecto en VS Code."
  exit 1
fi
if ! "$interprete" -c 'import pymongo, dotenv' >/dev/null 2>&1; then
  echo "Instala las dependencias desde la raíz del proyecto:"
  echo ".venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/requirements.txt"
  exit 1
fi
"$interprete" "$directorio/preparar_env.py"
exec "$interprete" "$directorio/10_agente_climatizacion.py"
