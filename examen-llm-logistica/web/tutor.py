"""Adaptador HTTP del tutor: conserva el servicio, el historial y el prompt."""
from web.base import crear_base, cuerpo, texto, descargar, exclusivo


def crear_app(tutor):
    app, trabajos = crear_base('tutor')

    @app.get('/api/estado')
    def estado():
        return {'modelo': tutor.cliente.modelo, 'historial': tutor.historial,
                'consultas': sum(m['role'] == 'user' for m in tutor.historial),
                'trabajo_activo': trabajos.activo}

    @app.post('/api/preguntar')
    def preguntar():
        pregunta = texto(cuerpo(), 'pregunta')
        def tarea():
            respuesta, latencia = tutor.preguntar(pregunta)
            return {'pregunta': pregunta, 'respuesta': respuesta, 'latencia_ms': latencia}
        return trabajos.iniciar(tarea, 'El tutor está preparando tu respuesta')

    @app.post('/api/resumen')
    def resumen():
        return trabajos.iniciar(lambda: {'resumen': tutor.resumir()}, 'Resumiendo tu historial')

    @app.delete('/api/historial')
    @exclusivo(trabajos)
    def reiniciar():
        if cuerpo().get('confirmar') is not True:
            raise ValueError('Confirma que deseas iniciar una conversación nueva.')
        tutor.reiniciar()
        return {'mensaje': 'Conversación nueva. Tu historial local se ha vaciado.'}

    @app.get('/api/exportar')
    def exportar_historial():
        return descargar(tutor.historial, 'json', 'historial_tutor_sql')

    return app
