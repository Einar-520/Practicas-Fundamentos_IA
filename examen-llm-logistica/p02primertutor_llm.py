"""Ejercicio 1 del examen: ejecutar antes de logiuncodigo.py."""
import argparse
from pathlib import Path
from comun.ollama_local import OllamaLocal
from tutor.servicio import TutorSQL


def main():
    parser = argparse.ArgumentParser(description='Tutor local de SQL con interfaz web.')
    parser.add_argument('--modelo', default='llama3.2:3b')
    parser.add_argument('--historial', type=Path, default=Path(__file__).parent / '.datos/tutor_historial.json')
    parser.add_argument('--puerto', type=int, default=8011, help='puerto local de la interfaz web (8011)')
    args = parser.parse_args()
    try:
        from web.tutor import crear_app
        from web.base import servir
        servir(crear_app(TutorSQL(OllamaLocal(args.modelo), args.historial)), args.puerto)
    except ImportError as error:
        raise SystemExit(f'Falta {error.name}. Instala las dependencias de requirements.txt.') from None
    except Exception as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
