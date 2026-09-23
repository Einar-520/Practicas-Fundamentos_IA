"""Punto de entrada de la práctica 10: ejecutar con Streamlit o ejecutar.sh."""


def main():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        from interfaz import iniciar
    except ImportError:
        print('Faltan dependencias. Usa ejecutar.sh o consulta el README de la práctica 10.')
        return 1
    if get_script_run_ctx(suppress_warning=True) is None:
        print('Abre la interfaz con ejecutar.sh o con python -m streamlit run ' + __file__)
        return 1
    iniciar()
    return 0


if __name__ == '__main__':
    main()
