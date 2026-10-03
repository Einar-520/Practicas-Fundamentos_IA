"""Casos de uso: validación, decisiones, CRUD y datos para el panel."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from uuid import uuid4
from logismart.dominio.modelos import (Camion, Premisas, Riesgo, Correo, EdicionIncidente,
                                     EvaluacionManual, validar)
from logismart.dominio.reglas import decidir, nivel_riesgo
from logismart.infraestructura.repositorio import ErrorDatos


class Aplicacion:
    def __init__(self, repositorio, clasificador, configuracion):
        self.repo, self.clasificador, self.config = repositorio, clasificador, configuracion

    def _guardar(self, coleccion, datos, anterior=None, motivo='Edición desde GUI'):
        if anterior:
            return self.repo.actualizar(coleccion, anterior['_id'], datos, self.config.operador,
                                       anterior['version'], motivo)
        return self.repo.crear(coleccion, datos, self.config.operador)

    def guardar_camion(self, datos, anterior=None):
        camion = validar(Camion, datos)
        return self._guardar('camiones', camion.model_dump(mode='json'), anterior)

    def buscar_placa(self, placa):
        placa = placa.strip().upper()
        if not placa:
            raise ValueError('Escribe una placa para buscar.')
        datos = self.repo.listar('camiones', {'placa': placa})
        if not datos:
            raise ValueError('No se encontró esa placa. Registra el camión o utiliza captura manual.')
        d = datos[0]
        hoy = datetime.now(ZoneInfo('America/Mexico_City')).date()
        return {**d, 'P': d['autorizacion'], 'S': d['certificacion_conductor'] and date.fromisoformat(d['certificacion_hasta']) >= hoy}

    def guardar_acceso(self, datos, anterior=None):
        p = validar(Premisas, {k: datos[k] for k in 'PQRSTH'})
        camion_id, placa = str(datos.get('camion_id', '')).strip().upper(), str(datos.get('placa', '')).strip().upper()
        if not camion_id or not placa:
            raise ValueError('Indica el identificador del camión y su placa.')
        import re
        if not re.fullmatch(r'CAM-\d{1,8}', camion_id) or not re.fullmatch(r'[A-Z0-9-]{5,15}', placa):
            raise ValueError('Usa un identificador como CAM-102 y una placa de 5 a 15 letras, números o guiones.')
        motivo = str(datos.get('motivo', '')).strip()
        if anterior and len(motivo) < 5:
            raise ValueError('Explica por qué corriges el acceso (mínimo 5 caracteres).')
        resultado = {**p.model_dump(), **decidir(p), 'camion_id': camion_id, 'placa': placa,
                     'operador': self.config.operador,
                     'observacion': str(datos.get('observacion', ''))[:500],
                     'horario_configurado': [self.config.hora_inicio, self.config.hora_fin]}
        return self._guardar('accesos', resultado, anterior, motivo or 'Evaluación de acceso')

    def guardar_riesgo(self, datos, anterior=None):
        riesgo = validar(Riesgo, datos)
        d = riesgo.model_dump()
        d['puntaje_inicial'] = riesgo.probabilidad * riesgo.impacto
        d['puntaje_residual'] = riesgo.probabilidad_residual * riesgo.impacto_residual
        d['nivel_inicial'] = nivel_riesgo(d['puntaje_inicial'])
        d['nivel_residual'] = nivel_riesgo(d['puntaje_residual'])
        return self._guardar('riesgos_eticos', d, anterior, 'Evaluación de riesgo y mitigación')

    def clasificar_correo(self, datos):
        correo = validar(Correo, datos)
        resultado = self.clasificador.clasificar(correo)
        lote = uuid4().hex
        evaluaciones = []
        for intento in resultado['intentos']:
            registro = self.repo.crear('evaluaciones_llm', {**intento, 'lote': lote}, self.config.operador)
            evaluaciones.append(registro['_id'])
        documento = {k: v for k, v in resultado.items() if k != 'intentos'}
        documento.update(correo_original=correo.model_dump(), estado='nuevo',
                         datos_extraidos=resultado['clasificacion']['entidades'],
                         evaluaciones=evaluaciones, lote=lote)
        try:
            return self._guardar('incidentes', documento)
        except ErrorDatos:
            raise ErrorDatos('La clasificación se calculó, pero no se confirmó el incidente. Puede haber evaluaciones guardadas; consulta la lista antes de repetir.') from None

    def editar_incidente(self, datos, anterior):
        edicion = validar(EdicionIncidente, datos)
        clasificacion = {'categoria': edicion.categoria, 'prioridad': edicion.prioridad,
                         'resumen': edicion.resumen, 'entidades': {k: getattr(edicion, k) for k in ('placa', 'camion_id', 'peso_reportado_kg', 'ubicacion')}}
        return self._guardar('incidentes', {'clasificacion': clasificacion,
                            'datos_extraidos': clasificacion['entidades'], 'estado': edicion.estado,
                            'requiere_revision_humana': edicion.requiere_revision_humana,
                            'revision_operador': self.config.operador}, anterior, edicion.motivo)

    def guardar_evaluacion_manual(self, datos, anterior=None):
        validado = validar(EvaluacionManual, datos).model_dump()
        # Una corrección no se hace pasar por una respuesta automática original.
        validado['tipo'] = 'manual'
        validado['estado'] = 'revisado_manualmente'
        return self._guardar('evaluaciones_llm', validado, anterior, validado['observacion'])

    def panel(self, desde='', hasta=''):
        accesos = self.repo.listar('accesos', desde=desde, hasta=hasta)
        incidentes = self.repo.listar('incidentes', desde=desde, hasta=hasta)
        riesgos = self.repo.listar('riesgos_eticos', desde=desde, hasta=hasta)
        return {'camiones_atendidos': len({d['camion_id'] for d in accesos}),
                'accesos': len(accesos),
                'incidentes_abiertos': sum(d['estado'] != 'cerrado' for d in incidentes),
                'riesgos_criticos': sum(d['puntaje_residual'] >= self.config.umbral_riesgo for d in riesgos),
                'por_semana': self.repo.agregar_incidentes(desde, hasta)}
