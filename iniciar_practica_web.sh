#!/usr/bin/env bash
# Inicia una práctica independiente; no combina sus servidores ni sus reglas.
set -euo pipefail
if [[ $# != 1 || ! "$1" =~ ^0?[1-7]$ ]]; then
  echo "Uso: bash iniciar_practica_web.sh NUMERO"
  echo "Elige una práctica del 1 al 7. Ejemplo: bash iniciar_practica_web.sh 1"
  exit 2
fi
raiz="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
numero="$(printf '%02d' "$((10#$1))")"
carpetas=("$raiz/unidad-01-introduccion-ia/practicas/practica-$numero-"*)
if [[ ${#carpetas[@]} != 1 || ! -f "${carpetas[0]}/ejecutar.sh" ]]; then
  echo "No se encontró una única carpeta ejecutable para la práctica $numero."
  exit 1
fi
exec bash "${carpetas[0]}/ejecutar.sh"
