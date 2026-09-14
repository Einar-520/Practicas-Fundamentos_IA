#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
interprete="$proyecto/.venv/bin/python"
if [[ ! -x "$interprete" ]]; then
  echo "Primero crea el entorno virtual desde la raíz del proyecto: python3 -m venv .venv"
  exit 1
fi
if ! "$interprete" -c 'import flask, pymongo' >/dev/null 2>&1; then
  echo "Faltan dependencias de esta práctica. Desde la raíz del proyecto ejecuta:"
  echo ".venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/requirements.txt"
  exit 1
fi
exec "$interprete" "$directorio/08_conexion_mongodb.py"
