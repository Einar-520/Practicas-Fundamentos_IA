"""Informes verificables de accesos: filtros permitidos y evidencia guardada."""
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from logismart.dominio.clasificacion import normalizar
from logismart.infraestructura.repositorio import rango_fechas

RESULTADOS = {
    'todos': 'Todos los accesos',
    'denegado': 'Camiones rechazados',
    'retenido': 'Camiones retenidos',
    'inspeccion': 'Camiones enviados a inspección',
    'autorizado': 'Camiones autorizados',
}
MAX_REGISTROS = 1000
MAX_VISTA_CHAT = 20


def filtros_desde_pregunta(pregunta):
    """Devuelve None para preguntas individuales; nunca ejecuta consultas del LLM."""
    texto = normalizar(pregunta)
    estados = {
        'denegado': r'\b(?:rechazad[oa]s?|denegad[oa]s?)\b',
        'retenido': r'\bretenid[oa]s?\b',
        'inspeccion': r'\binspeccion(?:es)?\b',
        'autorizado': r'\bautorizad[oa]s?\b',
    }
    elegidos = [estado for estado, patron in estados.items() if re.search(patron, texto)]
    solicitud = re.search(r'\b(?:informe|reporte|listado|lista|cuantos|cuales)\b', texto)
    if not solicitud and not (elegidos and re.search(r'\b(?:camiones|accesos)\b', texto)):
        return None
    if not re.search(r'\b(?:camiones|camion|accesos|acceso|cam-\d+)\b', texto):
        return None
    if len(elegidos) > 1 or re.search(r'\b(?:no|excepto|excluir|menos)\b', texto):
        raise ValueError('Elige un resultado por informe: rechazados, retenidos, inspección, '
                         'autorizados o todos los accesos. También puedes usar la pantalla Reportes.')
    if re.search(r'\b(?:empresa|operador|peso|fatiga|certificacion|autorizacion)\b', texto):
        raise ValueError('El informe admite resultado, fecha y camión o placa. '
                         'Solicita, por ejemplo: «Informe de camiones rechazados y sus motivos».')

    filtros = {'resultado': elegidos[0] if elegidos else 'todos', 'desde': '', 'hasta': ''}
    fechas = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', texto)
    relativas = re.findall(r'\b(?:hoy|ayer|esta semana|este mes)\b', texto)
    if len(fechas) > 2 or len(relativas) > 1 or (fechas and relativas):
        raise ValueError('Usa un solo período: hoy, ayer, esta semana, este mes o desde AAAA-MM-DD hasta AAAA-MM-DD.')
    if fechas:
        filtros['desde'] = fechas[0]
        filtros['hasta'] = fechas[-1]
        if len(fechas) == 1:
            if re.search(r'\bdesde\s+' + re.escape(fechas[0]), texto):
                filtros['hasta'] = ''
            elif re.search(r'\bhasta\s+' + re.escape(fechas[0]), texto):
                filtros['desde'] = ''
    elif relativas:
        hoy = datetime.now(timezone.utc).date()
        inicio = fin = hoy
        if relativas[0] == 'ayer':
            inicio = fin = hoy - timedelta(days=1)
        elif relativas[0] == 'esta semana':
            inicio = hoy - timedelta(days=hoy.weekday())
        elif relativas[0] == 'este mes':
            inicio = hoy.replace(day=1)
        filtros.update(desde=inicio.isoformat(), hasta=fin.isoformat())
    # No interpretar un período no admitido como si el usuario hubiera pedido todo.
    resto = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', texto)
    resto = re.sub(r'\b(?:hoy|ayer|esta semana|este mes)\b', '', resto)
    if re.search(r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|'
                 r'noviembre|diciembre|dia|dias|semana|semanas|mes|meses|ano|anos|ultimo|ultimos|'
                 r'ultima|ultimas|anoche|anteayer|antes|despues)\b|\d{1,4}[/-]\d{1,2}', resto):
        raise ValueError('Indica las fechas como «desde AAAA-MM-DD hasta AAAA-MM-DD». '
                         'También se aceptan hoy, ayer, esta semana y este mes; se usa UTC.')
    if not fechas and not relativas and re.search(r'\b(?:desde|hasta|fecha|fechas)\b', texto):
        raise ValueError('Indica el período con fechas AAAA-MM-DD o déjalo sin fechas para incluir todo.')
    rango_fechas(filtros['desde'], filtros['hasta'])
    camiones = set(re.findall(r'\bCAM-\d+\b', pregunta.upper()))
    placas = set(re.findall(r'\b[A-Z0-9]{2,3}-\d{2,3}-[A-Z0-9]{1,2}\b', pregunta.upper()))
    if len(camiones) > 1 or len(placas) > 1:
        raise ValueError('Solicita una unidad por informe o quita los identificadores para incluir todas.')
    if camiones:
        filtros['camion_id'] = camiones.pop()
    if placas:
        filtros['placa'] = placas.pop()
    return filtros


def motivos_guardados(registro):
    """Desglosa premisas del acceso; no recalcula ni modifica la decisión histórica."""
    resultado = registro.get('resultado')
    motivos = []
    if resultado == 'denegado':
        if registro.get('P') is False:
            motivos.append('Falta de autorización previa (P=False).')
        if registro.get('S') is False:
            motivos.append('Certificación del conductor no vigente (S=False).')
    elif resultado == 'retenido':
        if registro.get('B') is True:
            motivos.append('Carga peligrosa fuera del horario permitido (B=True).')
        if registro.get('F') is True:
            motivos.append('Alerta de fatiga en una unidad autorizada (F=True).')
    elif resultado == 'inspeccion':
        if registro.get('R') is True:
            motivos.append('Carga peligrosa (R=True).')
        if registro.get('Q') is True:
            motivos.append('Exceso de peso (Q=True).')
    explicacion = registro.get('explicacion') or []
    return motivos or [explicacion[-1] if explicacion else 'Sin motivo registrado; requiere revisión humana.']


def construir_informe(repo, resultado='todos', desde='', hasta='', camion_id='', placa=''):
    if resultado not in RESULTADOS:
        raise ValueError('Elige un resultado válido para el informe de accesos.')
    filtro = {} if resultado == 'todos' else {'resultado': resultado}
    if camion_id:
        filtro['camion_id'] = camion_id
    if placa:
        filtro['placa'] = placa
    accesos = repo.listar('accesos', filtro, desde=desde, hasta=hasta)
    if len(accesos) > MAX_REGISTROS:
        raise ValueError(f'Hay más de {MAX_REGISTROS} accesos. Reduce el período para generar el informe completo.')
    registros = []
    for acceso in accesos:
        registros.append({
            'fuente': f"accesos:{acceso['_id']}", 'version': acceso['version'],
            'camion_id': acceso.get('camion_id', ''), 'placa': acceso.get('placa', ''),
            'fecha_utc': acceso['creado_en'], 'resultado': acceso.get('resultado', ''),
            'operador': acceso.get('operador', ''), 'motivos': motivos_guardados(acceso),
            'premisas': {k: acceso.get(k) for k in 'PQRSHT'},
            'reglas': {k: acceso.get(k) for k in 'AEBF'},
            'explicacion': acceso.get('explicacion', []),
        })
    conteo = Counter(m for r in registros for m in r['motivos'])
    return {
        'tipo': 'informe_accesos', 'titulo': RESULTADOS[resultado],
        'generado_en': datetime.now(timezone.utc).isoformat(), 'almacenamiento': repo.modo,
        'filtros': {'resultado': resultado, 'desde': desde, 'hasta': hasta,
                    'camion_id': camion_id, 'placa': placa, 'zona_horaria': 'UTC'},
        'total_accesos': len(registros),
        'camiones_unicos': len({r['camion_id'] or r['placa'] for r in registros}),
        'resumen_motivos': dict(conteo), 'registros': registros,
    }


def periodo_informe(informe):
    filtros = informe['filtros']
    return (f"Desde {filtros['desde'] or 'el primer registro'} hasta "
            f"{filtros['hasta'] or 'el último registro disponible'} (UTC).")


def texto_informe(informe):
    lineas = [informe['titulo'], periodo_informe(informe),
              f"Almacenamiento: {informe['almacenamiento']}.",
              f"Accesos: {informe['total_accesos']}. Camiones únicos: {informe['camiones_unicos']}."]
    for clave in ('camion_id', 'placa'):
        if informe['filtros'][clave]:
            lineas.append(f"Unidad consultada: {informe['filtros'][clave]}.")
    if not informe['registros']:
        lineas.append('No hay registros que coincidan con estos filtros.')
    else:
        lineas.append('\nMotivos registrados (un acceso puede tener varios):')
        lineas.extend(f'- {motivo} Accesos: {n}.' for motivo, n in informe['resumen_motivos'].items())
        for registro in informe['registros'][:MAX_VISTA_CHAT]:
            lineas.append(f"\n{registro['camion_id']} · {registro['placa']} · {registro['fecha_utc']}\n"
                          f"Resultado: {registro['resultado']}. " + ' '.join(registro['motivos']) +
                          f"\n[Fuente: {registro['fuente']} · versión {registro['version']}]")
        if informe['total_accesos'] > MAX_VISTA_CHAT:
            lineas.append(f'\nVista previa: {MAX_VISTA_CHAT} accesos. Las descargas incluyen los '
                          f"{informe['total_accesos']} accesos del informe.")
    lineas.append('\nInforme calculado con registros guardados; no requiere una respuesta de Ollama.')
    return '\n'.join(lineas)
