"""Ejercicio 2: LogiSmart modular, MongoDB, Ollama e interfaz web local."""
import argparse
from pathlib import Path


def crear_servicio(demo=False):
    from comun.ollama_local import OllamaLocal
    from logismart.infraestructura.configuracion import cargar_configuracion, datos_mongo, RAIZ
    from logismart.infraestructura.repositorio import DemoRepositorio, MongoRepositorio
    from logismart.servicios.clasificador import ClasificadorHibrido
    from logismart.servicios.aplicacion import Aplicacion
    config = cargar_configuracion()
    # El modo de ensayo parte sin LLM; se puede activar desde Configuración.
    if demo: config = config.model_copy(update={'usar_llm': False})
    repo = DemoRepositorio(RAIZ / '.datos/demo.json') if demo else MongoRepositorio(*datos_mongo())
    cliente = OllamaLocal(config.modelo, config.url_ollama, config.timeout)
    return Aplicacion(repo, ClasificadorHibrido(cliente, config.usar_llm), config)


def main():
    parser = argparse.ArgumentParser(description='LogiSmart: examen de reglas, MongoDB y LLM local.')
    parser.add_argument('--demo', action='store_true', help='usar almacenamiento JSON local, sin MongoDB')
    parser.add_argument('--cargar-demo', action='store_true', help='agregar datos ficticios sin reemplazar los existentes')
    parser.add_argument('--puerto', type=int, default=8012, help='puerto local de la interfaz web (8012)')
    parser.add_argument('--evaluar', type=Path, metavar='CORPUS', help='ejecutar la evaluación sin abrir la GUI')
    parser.add_argument('--solo-reglas', action='store_true', help='evaluar sin consultar Ollama')
    parser.add_argument('--salida', type=Path, default=Path(__file__).parent / '.datos/evaluacion.json')
    args = parser.parse_args()
    servicio = crear_servicio(args.demo or bool(args.evaluar))
    try:
        if args.evaluar:
            from logismart.servicios.evaluacion import evaluar_corpus
            from logismart.servicios.reportes import exportar
            # La evaluación CLI no necesita ni escribe en MongoDB; produce un artefacto local.
            servicio.clasificador.usar_llm = not args.solo_reglas
            resultado = evaluar_corpus(args.evaluar, servicio.clasificador)
            args.salida.parent.mkdir(parents=True, exist_ok=True)
            exportar(resultado, args.salida, 'Experimento de clasificación')
            print(f'Resultados guardados en {args.salida}')
            print('Etiquetado:', resultado['estado_etiquetado'])
        else:
            if args.cargar_demo:
                from logismart.servicios.demostracion import cargar_demo
                servicio.repo.comprobar()
                print(cargar_demo(servicio))
            from web.logistica import crear_app
            from web.base import servir
            servir(crear_app(servicio), args.puerto)
    finally:
        servicio.repo.cerrar()


if __name__ == '__main__':
    try:
        main()
    except ImportError as error:
        raise SystemExit(f'Falta una dependencia: {error.name}. Instala requirements.txt.') from None
    except Exception as error:
        raise SystemExit(str(error)) from None
