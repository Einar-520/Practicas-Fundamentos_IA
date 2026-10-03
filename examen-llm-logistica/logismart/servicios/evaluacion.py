"""Experimento reproducible: no convierte fallos del LLM en predicciones ficticias."""
import hashlib
import json
import math
from statistics import mean, median
from uuid import uuid4
from logismart.dominio.modelos import CATEGORIAS, PRIORIDADES, Correo, validar
from logismart.infraestructura.repositorio import ahora


def cargar_corpus(ruta):
    try:
        datos = json.loads(ruta.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('No se pudo leer el corpus JSON.') from None
    if not isinstance(datos, list) or len(datos) < 30:
        raise ValueError('El corpus debe contener al menos 30 correos etiquetados.')
    identificadores = set()
    for d in datos:
        if (not isinstance(d, dict) or not isinstance(d.get('id'), str) or d['id'] in identificadores
                or d.get('categoria_esperada') not in CATEGORIAS
                or d.get('prioridad_esperada') not in PRIORIDADES
                or d.get('registro') not in {'formal', 'informal'}):
            raise ValueError('Revisa identificadores únicos, etiquetas y registro formal/informal del corpus.')
        validar(Correo, {k: d.get(k) for k in ('remitente', 'asunto', 'cuerpo')})
        identificadores.add(d['id'])
    return datos


def metricas(casos, metodo):
    if metodo == 'llm' and all(c['llm_ejecutado'] is False for c in casos):
        return {'estado': 'no_ejecutado', 'exactitud_categoria': None, 'matriz_confusion': None, 'latencia_ms_media': None}
    categorias = list(CATEGORIAS)
    columnas = categorias + ['sin_respuesta']
    matriz = [[0 for _ in columnas] for _ in categorias]
    aciertos = prioridad = conjunto = validos = 0
    tiempos = []
    for c in casos:
        pred = c[metodo]
        real = c['categoria_esperada']
        categoria = pred['categoria'] if pred else 'sin_respuesta'
        matriz[categorias.index(real)][columnas.index(categoria)] += 1
        if pred:
            validos += 1
            aciertos += categoria == real
            prioridad += pred['prioridad'] == c['prioridad_esperada']
            conjunto += categoria == real and pred['prioridad'] == c['prioridad_esperada']
        tiempo = c[f'latencia_{metodo}_ms']
        if tiempo is not None: tiempos.append(tiempo)
    tiempos.sort()
    n = len(casos)
    return {'estado': 'medido', 'n': n, 'exactitud_categoria': aciertos / n,
            'exactitud_prioridad': prioridad / n, 'coincidencia_conjunta': conjunto / n,
            'respuestas_validas': validos, 'cobertura': validos / n,
            'latencia_ms_media': mean(tiempos) if tiempos else None,
            'latencia_ms_mediana': median(tiempos) if tiempos else None,
            'latencia_ms_p95': tiempos[max(0, math.ceil(len(tiempos) * .95) - 1)] if tiempos else None,
            'filas_reales': categorias, 'columnas_predichas': columnas, 'matriz_confusion': matriz}


def evaluar_corpus(ruta, motor, repo=None, operador='Evaluación'):
    corpus = cargar_corpus(ruta)
    lote = uuid4().hex
    casos = []
    for d in corpus:
        correo = validar(Correo, {k: d[k] for k in ('remitente', 'asunto', 'cuerpo')})
        resultado = motor.clasificar(correo)
        for intento in resultado['intentos']:
            if repo is not None:
                repo.crear('evaluaciones_llm', {**intento, 'experimento': lote, 'correo_id': d['id']}, operador)
        casos.append({'id': d['id'], 'registro': d['registro'],
                      'categoria_esperada': d['categoria_esperada'], 'prioridad_esperada': d['prioridad_esperada'],
                      'reglas': resultado['reglas'], 'llm': resultado['llm'], 'hibrido': resultado['clasificacion'],
                      'llm_ejecutado': motor.usar_llm,
                      'latencia_reglas_ms': resultado['latencia_reglas_ms'],
                      'latencia_llm_ms': resultado['latencia_llm_ms'],
                      'latencia_hibrido_ms': resultado['latencia_hibrido_ms'],
                      'requiere_revision_humana': resultado['requiere_revision_humana'],
                      'intentos': resultado['intentos']})
    revisados = sum(d.get('revisado_humano') is True and bool(d.get('revisor', '').strip()) for d in corpus)
    metricas_metodos = {m: metricas(casos, m) for m in ('reglas', 'llm', 'hibrido')}
    return {'experimento': lote, 'fecha_utc': ahora().isoformat(),
            'modelo_configurado': motor.cliente.modelo, 'llm_habilitado': motor.usar_llm,
            'sha256_corpus': hashlib.sha256(ruta.read_bytes()).hexdigest(),
            'correos': len(casos), 'etiquetas_revisadas_por_persona': revisados,
            'estado_etiquetado': 'revisado' if revisados == len(casos) else 'provisional_requiere_revision_humana',
            'advertencia': 'El híbrido usa respaldo por reglas cuando no existe salida LLM válida. No equivale a una medición del LLM. Latencia de pared, incluye carga del modelo y reintento.',
            'metricas': metricas_metodos,
            'por_registro': {registro: {m: metricas([c for c in casos if c['registro'] == registro], m)
                                      for m in ('reglas', 'llm', 'hibrido')}
                             for registro in ('formal', 'informal') if any(c['registro'] == registro for c in casos)},
            'casos': casos}
