"""Ejercicio 1 del examen: ejecutar antes de logiuncodigo.py."""
import argparse
from pathlib import Path
from comun.ollama_local import OllamaLocal
from tutor.servicio import TutorSQL


def main():
    parser = argparse.ArgumentParser(description='Tutor local de SQL con interfaz gráfica.')
    parser.add_argument('--modelo', default='llama3.2:3b')
    parser.add_argument('--historial', type=Path, default=Path(__file__).parent / '.datos/tutor_historial.json')
    args = parser.parse_args()
    try:
        from tutor.interfaz import iniciar
        iniciar(TutorSQL(OllamaLocal(args.modelo), args.historial))
    except ImportError:
        raise SystemExit('Falta Tkinter. En Ubuntu/WSL ejecuta: sudo apt install python3-tk') from None
    except Exception as error:
        from tkinter import TclError
        if isinstance(error, TclError):
            raise SystemExit('No se pudo abrir la ventana. Comprueba el soporte gráfico de WSLg.') from None
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
