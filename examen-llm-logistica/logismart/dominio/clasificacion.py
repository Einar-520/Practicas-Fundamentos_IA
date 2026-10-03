"""Clasificador determinista del profesor, con el contrato JSON del examen."""
import re
import unicodedata
from logismart.dominio.modelos import Clasificacion, Entidades, PRIORIDADES

CATEGORIAS_CLAVE = {
    'materiales_peligrosos': ['peligroso', 'derrame', 'fuga', 'quimico', 'inflamable', 'toxico', 'corrosivo'],
    'sobrepeso': ['sobrepeso', 'excede', 'bascula', 'exceso de peso', 'sobrecarga'],
    'acceso_no_autorizado': ['sin autorizacion', 'no autorizado', 'acceso denegado', 'barrera', 'intruso'],
    'falla_hardware': ['camara', 'sensor', 'lector', 'rfid', 'no enciende', 'apagado', 'danado', 'falla electrica'],
    'falla_software': ['sistema', 'error', 'pantalla', 'caido', 'no carga', 'lento', 'software', 'aplicacion'],
    'somnolencia_conductor': ['somnolencia', 'dormido', 'cansancio', 'fatiga', 'sueno'],
}
PRIORIDAD_BASE = {'materiales_peligrosos': 'critica', 'somnolencia_conductor': 'alta',
                  'acceso_no_autorizado': 'alta', 'sobrepeso': 'media',
                  'falla_hardware': 'media', 'falla_software': 'baja', 'otro': 'baja'}
URGENTES = ['urgente', 'emergencia', 'accidente', 'incendio', 'herido', 'critico', 'inmediato']


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if not unicodedata.combining(c))


def extraer_datos(asunto, cuerpo):
    texto = f'{asunto}\n{cuerpo}'
    placa = re.search(r'\b[A-Z0-9]{2,3}-\d{2,3}-[A-Z0-9]{1,2}\b', texto.upper())
    camion = re.search(r'\bCAM-\d+\b', texto.upper())
    peso = re.search(r'(\d+(?:[.,]\d+)?)\s*(toneladas|tonelada|ton|t|kg)\b', texto.lower())
    ubicacion = re.search(r'\b(and[eé]n|puerta|muelle|caseta|dock)\s+([A-Za-z0-9]+)', texto, re.I)
    kg = None
    if peso:
        kg = float(peso[1].replace(',', '.')) * (1 if peso[2] == 'kg' else 1000)
        if kg > 1_000_000:
            kg = None
    return Entidades(placa=placa[0] if placa else None, camion_id=camion[0] if camion else None,
                     peso_reportado_kg=kg, ubicacion=ubicacion[0].lower() if ubicacion else None)


def clasificar_reglas(correo):
    texto = normalizar(correo.asunto + ' ' + correo.cuerpo)
    coincidencias = {cat: [p for p in palabras if p in texto] for cat, palabras in CATEGORIAS_CLAVE.items()}
    categoria = max(coincidencias, key=lambda c: len(coincidencias[c]))
    if not coincidencias[categoria]:
        categoria = 'otro'
    prioridad = PRIORIDAD_BASE[categoria]
    urgentes = [p for p in URGENTES if p in texto]
    if urgentes:
        prioridad = PRIORIDADES[min(PRIORIDADES.index(prioridad) + 1, 3)]
    claves = coincidencias.get(categoria, []) + urgentes
    resumen = 'Reglas por palabras clave: ' + (', '.join(claves) if claves else 'sin coincidencias; revisión recomendada')
    return Clasificacion(categoria=categoria, prioridad=prioridad,
                         entidades=extraer_datos(correo.asunto, correo.cuerpo), resumen=resumen[:500])


def fusionar(reglas, llm):
    if llm is None:
        return reglas, True
    discrepan = (reglas.categoria, reglas.prioridad) != (llm.categoria, llm.prioridad)
    # En empate de prioridad se conserva la categoría determinista.
    ganador = llm if PRIORIDADES.index(llm.prioridad) > PRIORIDADES.index(reglas.prioridad) else reglas
    datos = ganador.model_dump()
    # Las entidades persistidas se verifican por extracción literal del correo.
    datos['entidades'] = reglas.entidades.model_dump()
    revision = discrepan or llm.entidades != reglas.entidades or ganador.categoria == 'otro'
    return Clasificacion.model_validate(datos), revision
