"""Las fórmulas originales se conservan; la política final se expresa aparte."""
from itertools import product
from logismart.dominio.modelos import Premisas


def evaluar_camion(P, Q, R, S):
    for nombre, valor in zip('PQRS', (P, Q, R, S)):
        if type(valor) is not bool:
            raise TypeError(f'La premisa {nombre} debe ser booleana.')
    return {'acceso_estandar': P and S and not Q,
            'inspeccion_especial': P and (R or Q)}


def decidir(p: Premisas):
    original = evaluar_camion(p.P, p.Q, p.R, p.S)
    A, E = original['acceso_estandar'], original['inspeccion_especial']
    B = p.R and not p.H  # Nueva regla 1: peligrosos fuera de horario.
    F = p.P and p.T      # Nueva regla 2: camión autorizado con alerta de fatiga.
    pasos = [f'P={p.P}: autorización previa.', f'Q={p.Q}: exceso de peso.',
             f'R={p.R}: carga peligrosa.', f'S={p.S}: certificación vigente.',
             f'¬Q={not p.Q}; P∧S={p.P and p.S}; A=P∧S∧¬Q={A}.',
             f'R∨Q={p.R or p.Q}; E=P∧(R∨Q)={E}.',
             f'H={p.H}: horario permitido; B=R∧¬H={B}.',
             f'T={p.T}: alerta de fatiga; F=P∧T={F}.']
    if not p.P or not p.S:
        resultado, color = 'denegado', 'rojo'
        pasos.append('Se deniega por falta de autorización o certificación vigente.')
    elif B or F:
        resultado, color = 'retenido', 'rojo'
        pasos.append('Se retiene para atención humana por horario restringido o fatiga.')
    elif E:
        resultado, color = 'inspeccion', 'amarillo'
        pasos.append('La inspección tiene precedencia operativa sobre el acceso estándar.')
    elif A:
        resultado, color = 'autorizado', 'verde'
        pasos.append('Se cumplen los requisitos para acceso estándar.')
    else:
        resultado, color = 'denegado', 'rojo'
        pasos.append('No hay una regla de autorización aplicable.')
    return {'A': A, 'E': E, 'B': B, 'F': F, 'resultado': resultado,
            'semaforo': color, 'explicacion': pasos}


def tablas():
    base = []
    for P, Q, R, S in product((True, False), repeat=4):
        r = evaluar_camion(P, Q, R, S)
        base.append({'P': P, 'Q': Q, 'R': R, 'S': S, '¬Q': not Q,
                     'P∧S': P and S, 'R∨Q': R or Q,
                     'A': r['acceso_estandar'], 'E': r['inspeccion_especial']})
    horario = [{'R': R, 'H': H, 'B': R and not H} for R, H in product((True, False), repeat=2)]
    fatiga = [{'P': P, 'T': T, 'F': P and T} for P, T in product((True, False), repeat=2)]
    return {'A y E': base, 'B = R ∧ ¬H': horario, 'F = P ∧ T': fatiga}


def nivel_riesgo(puntaje):
    return 'crítico' if puntaje >= 17 else 'alto' if puntaje >= 10 else 'medio' if puntaje >= 5 else 'bajo'
