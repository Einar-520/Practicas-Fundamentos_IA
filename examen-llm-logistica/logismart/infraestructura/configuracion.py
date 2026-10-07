"""Credenciales en .env; preferencias operativas editables desde la GUI."""
import json
import os
from pathlib import Path
from urllib.parse import quote_plus, urlsplit
from dotenv import load_dotenv
from logismart.dominio.modelos import Configuracion, validar

RAIZ = Path(__file__).resolve().parents[2]


def cargar_configuracion():
    ruta = RAIZ / '.datos/configuracion.json'
    if ruta.exists():
        try:
            return validar(Configuracion, json.loads(ruta.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            raise ValueError('No se pudo leer .datos/configuracion.json. Conserva una copia y corrige sus valores.') from None
    return Configuracion()


def guardar_configuracion(config):
    from comun.ollama_local import OllamaLocal
    OllamaLocal(config.modelo, config.url_ollama, config.timeout)
    ruta = RAIZ / '.datos/configuracion.json'
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix('.tmp')
    temporal.write_text(config.model_dump_json(indent=2), encoding='utf-8')
    temporal.replace(ruta)


def datos_mongo(exigir_atlas=False):
    load_dotenv(RAIZ / '.env', override=False)
    uri = os.getenv('MONGO_URI', '').strip()
    if not uri:
        usuario = os.getenv('Mongo_User', '').strip()
        password = os.getenv('Mongo_Password', '')
        cluster = os.getenv('Mongo_Cluster', os.getenv('Mongo_Closter', '')).strip()
        if usuario and password and cluster:
            if '/' in cluster or '@' in cluster or ':' in cluster:
                raise ValueError('Mongo_Cluster debe contener solamente el dominio del clúster.')
            uri = f'mongodb+srv://{quote_plus(usuario)}:{quote_plus(password)}@{cluster}/?retryWrites=true&w=majority'
        else:
            uri = 'mongodb://127.0.0.1:27017/'
    base = os.getenv('Mongo_DB', 'Einar_Ivan_Lazcano_Luna_Examen').strip()
    if not base or any(c in base for c in ' /\\.\"$*<>:|?'):
        raise ValueError('Mongo_DB debe ser un nombre sin espacios ni caracteres especiales; usa guiones bajos.')
    if exigir_atlas:
        destino = urlsplit(uri)
        if destino.scheme != 'mongodb+srv' or not (destino.hostname or '').endswith('.mongodb.net'):
            raise ValueError('El modo --atlas requiere la conexión del clúster en examen-llm-logistica/.env. '
                             'Deja MONGO_URI vacío y completa Mongo_User, Mongo_Password, Mongo_Cluster y Mongo_DB, '
                             'o utiliza una MONGO_URI de Atlas con mongodb+srv://. No se inició MongoDB local.')
    return uri, base
