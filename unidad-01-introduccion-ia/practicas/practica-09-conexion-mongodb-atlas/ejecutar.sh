#!/usr/bin/env bash
set -euo pipefail
directorio="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
proyecto="$(cd -- "$directorio/../../.." && pwd)"
exec "$proyecto/.venv/bin/python" "$directorio/09_conexion_mongodb_atlas.py"
