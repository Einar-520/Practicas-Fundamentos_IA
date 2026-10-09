#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
interprete="$proyecto/.venv/bin/python"
if [[ ! -x "$interprete" ]]; then
  interprete="python3"
fi
programa="12_grafica_ventas.py"
if [[ "${1:-}" == "--paletas" ]]; then
  programa="12_paletas_colores.py"
  shift
fi
exec "$interprete" "$directorio/$programa" "$@"
