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
  echo "Falta Tkinter en este intérprete. En Ubuntu/WSL ejecuta: sudo apt install python3-tk"
  echo "Comprueba también el intérprete seleccionado en VS Code. Tkinter no se instala con pip."
  exit 1
fi
if ! "$interprete" -c 'import pymongo, dotenv' >/dev/null 2>&1; then
  echo "Instala las dependencias desde la raíz del proyecto:"
  echo ".venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/requirements.txt"
  exit 1
fi
exec "$interprete" "$directorio/interfaz_tkinter.py"
