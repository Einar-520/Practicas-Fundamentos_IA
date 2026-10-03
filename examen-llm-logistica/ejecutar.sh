#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/.." && pwd)"
interprete="$proyecto/.venv/bin/python"
if [[ ! -x "$interprete" ]]; then
  interprete="python3"
fi
ejercicio="${1:-}"
if [[ "$ejercicio" != "1" && "$ejercicio" != "2" ]]; then
  echo 'Uso: bash examen-llm-logistica/ejecutar.sh 1|2 [opciones]'
  exit 1
fi
shift
if [[ "$ejercicio" == "1" ]]; then
  exec "$interprete" "$directorio/p02primertutor_llm.py" "$@"
fi
exec "$interprete" "$directorio/logiuncodigo.py" "$@"
