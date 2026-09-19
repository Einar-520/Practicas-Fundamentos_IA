"""Punto de entrada de la práctica 10: ventana Tkinter y agente de climatización."""


def main():
    try:
        from interfaz import iniciar
    except ImportError:
        print('Faltan dependencias. Usa ejecutar.sh o consulta el README de la práctica 10.')
        return 1
    return iniciar()


if __name__ == '__main__':
    raise SystemExit(main())
