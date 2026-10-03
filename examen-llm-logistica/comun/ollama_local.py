"""Cliente pequeño para la API local de Ollama; nunca envía datos a la nube."""
import json
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler


class ErrorLLM(RuntimeError):
    pass


class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ErrorLLM('Ollama no debe redirigir las solicitudes a otro servidor.')


class OllamaLocal:
    def __init__(self, modelo='llama3.2:3b', url='http://127.0.0.1:11434', timeout=90):
        partes = urlparse(url)
        if (partes.scheme != 'http' or partes.hostname not in {'localhost', '127.0.0.1', '::1'}
                or partes.username or partes.password or partes.query or partes.fragment
                or partes.path not in {'', '/'}):
            raise ValueError('Ollama debe usar una dirección HTTP local, por ejemplo http://127.0.0.1:11434.')
        if not modelo.strip() or len(modelo) > 100:
            raise ValueError('Escribe un nombre de modelo válido de Ollama.')
        self.modelo, self.url, self.timeout = modelo.strip(), url.rstrip('/'), timeout

    def chat(self, mensajes, esquema=None):
        cuerpo = {'model': self.modelo, 'messages': mensajes, 'stream': False,
                  'options': {'temperature': 0, 'num_predict': 1200, 'num_ctx': 8192}}
        if esquema is not None:
            cuerpo['format'] = esquema
        solicitud = Request(self.url + '/api/chat',
                            data=json.dumps(cuerpo, ensure_ascii=False).encode(),
                            headers={'Content-Type': 'application/json'})
        inicio = perf_counter()
        try:
            # Evita que un proxy del sistema reciba los correos o el historial.
            cliente = build_opener(ProxyHandler({}), SinRedireccion())
            with cliente.open(solicitud, timeout=self.timeout) as respuesta:
                contenido = respuesta.read(2_000_001)
            if len(contenido) > 2_000_000:
                raise ErrorLLM('Ollama devolvió una respuesta demasiado grande.')
            datos = json.loads(contenido)
            texto = datos['message']['content']
            if not isinstance(texto, str) or not texto.strip():
                raise ErrorLLM('Ollama devolvió una respuesta vacía.')
            return texto, (perf_counter() - inicio) * 1000
        except HTTPError as error:
            if error.code == 404:
                raise ErrorLLM(f'No se encontró el modelo. Ejecuta: ollama pull {self.modelo}') from None
            raise ErrorLLM(f'Ollama respondió con error HTTP {error.code}.') from None
        except (URLError, TimeoutError, ConnectionError, OSError):
            raise ErrorLLM('No se pudo consultar Ollama. Comprueba ollama serve y el modelo instalado.') from None
        except (ValueError, KeyError, TypeError):
            raise ErrorLLM('La respuesta HTTP de Ollama no tiene el formato esperado.') from None
