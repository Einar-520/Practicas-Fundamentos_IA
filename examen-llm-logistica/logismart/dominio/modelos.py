"""Contratos de entrada y salida; no contienen código de GUI ni de MongoDB."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, field_validator, model_validator

CATEGORIAS = ('materiales_peligrosos', 'sobrepeso', 'acceso_no_autorizado',
              'falla_hardware', 'falla_software', 'somnolencia_conductor', 'otro')
PRIORIDADES = ('baja', 'media', 'alta', 'critica')
ESTADOS = ('nuevo', 'en_atencion', 'cerrado')
CATEGORIAS_ETICAS = ('sesgo', 'privacidad', 'transparencia', 'seguridad', 'responsabilidad', 'otro')
Categoria = Literal['materiales_peligrosos', 'sobrepeso', 'acceso_no_autorizado', 'falla_hardware', 'falla_software', 'somnolencia_conductor', 'otro']
Prioridad = Literal['baja', 'media', 'alta', 'critica']


class Modelo(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class Entidades(Modelo):
    placa: str | None = Field(max_length=20)
    camion_id: str | None = Field(max_length=20)
    peso_reportado_kg: float | None = Field(ge=0, le=1_000_000)
    ubicacion: str | None = Field(max_length=100)


class Clasificacion(Modelo):
    categoria: Categoria
    prioridad: Prioridad
    entidades: Entidades
    resumen: str = Field(min_length=1, max_length=500)


class Correo(Modelo):
    remitente: str = Field(min_length=3, max_length=180, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    asunto: str = Field(min_length=1, max_length=200)
    cuerpo: str = Field(min_length=1, max_length=10000)


class Camion(Modelo):
    placa: str = Field(pattern=r'^[A-Z0-9-]{5,15}$')
    camion_id: str = Field(pattern=r'^CAM-\d{1,8}$')
    empresa: str = Field(min_length=2, max_length=120)
    autorizacion: StrictBool
    certificacion_conductor: StrictBool
    certificado_id: str = Field(min_length=1, max_length=60)
    certificacion_hasta: date

    @field_validator('placa', 'camion_id', mode='before')
    @classmethod
    def mayusculas(cls, valor):
        return valor.strip().upper() if isinstance(valor, str) else valor


class Premisas(Modelo):
    P: StrictBool
    Q: StrictBool
    R: StrictBool
    S: StrictBool
    H: StrictBool = True
    T: StrictBool = False


class Riesgo(Modelo):
    modulo: str = Field(min_length=2, max_length=120)
    descripcion: str = Field(min_length=5, max_length=1000)
    categoria: Literal['sesgo', 'privacidad', 'transparencia', 'seguridad', 'responsabilidad', 'otro']
    probabilidad: int = Field(strict=True, ge=1, le=5)
    impacto: int = Field(strict=True, ge=1, le=5)
    mitigacion: str = Field(min_length=5, max_length=1000)
    probabilidad_residual: int = Field(strict=True, ge=1, le=5)
    impacto_residual: int = Field(strict=True, ge=1, le=5)
    evidencia: str = Field(min_length=5, max_length=1000)


class EdicionIncidente(Modelo):
    categoria: Categoria
    prioridad: Prioridad
    estado: Literal['nuevo', 'en_atencion', 'cerrado']
    resumen: str = Field(min_length=1, max_length=500)
    requiere_revision_humana: StrictBool
    motivo: str = Field(min_length=5, max_length=500)
    placa: str | None = Field(default=None, max_length=20)
    camion_id: str | None = Field(default=None, max_length=20)
    peso_reportado_kg: float | None = Field(default=None, ge=0, le=1_000_000)
    ubicacion: str | None = Field(default=None, max_length=100)


class EvaluacionManual(Modelo):
    prompt: str = Field(min_length=1, max_length=20000)
    respuesta: str = Field(max_length=20000)
    modelo: str = Field(min_length=1, max_length=100)
    latencia_ms: float = Field(ge=0)
    coincidio_reglas: StrictBool | None
    observacion: str = Field(min_length=5, max_length=1000)


class SeleccionFuentes(Modelo):
    fuentes: list[str] = Field(max_length=5)


class Configuracion(Modelo):
    modelo: str = Field(default='llama3.2:3b', min_length=1, max_length=100)
    url_ollama: str = 'http://127.0.0.1:11434'
    timeout: int = Field(default=90, ge=5, le=300)
    usar_llm: bool = True
    operador: str = Field(default='Einar', min_length=2, max_length=80)
    umbral_riesgo: int = Field(default=17, ge=1, le=25)
    hora_inicio: int = Field(default=6, ge=0, le=23)
    hora_fin: int = Field(default=18, ge=1, le=24)
    simulacion_correo: bool = True

    @model_validator(mode='after')
    def horario(self):
        if self.hora_inicio >= self.hora_fin:
            raise ValueError('La hora inicial debe ser anterior a la final.')
        return self


def validar(modelo, datos):
    try:
        return modelo.model_validate(datos)
    except ValidationError as error:
        campos = ', '.join(dict.fromkeys('.'.join(map(str, e['loc'])) or 'formulario' for e in error.errors()))
        raise ValueError(f'Revisa estos campos: {campos}. Completa los obligatorios y respeta los tipos, opciones y límites indicados.') from None
