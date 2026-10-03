"""Entorno E2E aislado: MongoDB no se usa y el modelo es un sustituto identificado."""
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from werkzeug.serving import make_server
from logismart.dominio.modelos import Configuracion
from logismart.infraestructura.repositorio import DemoRepositorio
from logismart.servicios.aplicacion import Aplicacion
from logismart.servicios.clasificador import ClasificadorHibrido
from logismart.servicios.demostracion import cargar_demo
from tutor.servicio import TutorSQL
from web.logistica import crear_app
from web.tutor import crear_app as crear_tutor


class ModeloDePrueba:
    modelo = 'sustituto_de_prueba_no_es_llm_real'

    def chat(self, mensajes, esquema=None):
        time.sleep(.1)
        if mensajes[0]['content'].startswith('Resume'):
            return 'Practicamos SELECT para consultar los títulos de una biblioteca.', 100
        return 'Puedes consultar los libros así:\n```sql\nSELECT titulo FROM libros;\n```\nIntenta filtrar por autor.', 100


def main():
    with tempfile.TemporaryDirectory(prefix='logismart_web_') as temporal:
        ruta = Path(temporal)
        cliente = ModeloDePrueba()
        servicio = Aplicacion(DemoRepositorio(ruta / 'demo.json'), ClasificadorHibrido(cliente, False), Configuracion(usar_llm=False))
        cargar_demo(servicio)
        apps = [(9161, crear_tutor(TutorSQL(cliente, ruta / 'tutor.json'))),
                (9162, crear_app(servicio, ruta, lambda config: None))]
        servidores = [make_server('127.0.0.1', puerto, app, threaded=True) for puerto, app in apps]
        for servidor in servidores:
            threading.Thread(target=servidor.serve_forever, daemon=True).start()
        print('Pruebas web: tutor 9161 / LogiSmart 9162. Datos temporales y LLM sustituido.', flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            for servidor in servidores:
                servidor.shutdown()


if __name__ == '__main__':
    main()
