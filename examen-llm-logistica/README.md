# Examen: tutor LLM y LogiSmart

Desarrollo de los dos ejercicios entregados por el profesor, en el orden solicitado.
Alumno: **Einar Ivan Lazcano Luna**. Ambos programas se ejecutan de forma independiente
y tienen interfaz de escritorio con **Tkinter**. Las gráficas usan **Matplotlib**.

1. **p02primertutor_llm.py:** tutor de SQL para principiantes, con Ollama, chat,
   historial local y resumen breve.
2. **logiuncodigo.py:** aplicación modular de logística, con reglas, MongoDB,
   clasificación híbrida, asistente con fuentes, riesgos éticos y reportes.

Lee [el informe técnico](docs/INFORME_TECNICO.md),
[la matriz de cumplimiento](docs/CUMPLIMIENTO.md) y
[el guion de exposición](docs/EXPOSICION.md).

## 1. Preparar el entorno en VS Code y WSL

Desde tu proyecto:

```bash
cd ~/universidad/fundamentos-ia &&
git pull --ff-only origin main
```

Si aún no existe el entorno virtual, créalo:

```bash
python3 -m venv .venv
```

Instala las dependencias en ese intérprete:

```bash
sudo apt install -y python3-tk
.venv/bin/python -m pip install -r examen-llm-logistica/requirements.txt
```

En VS Code selecciona `.venv/bin/python`. Las ventanas requieren soporte gráfico
en WSLg. Compruébalo con `.venv/bin/python -m tkinter`. Tkinter se instala con el
gestor del sistema; no con `pip install tkinter`.

## 2. Preparar Ollama

Instala Ollama siguiendo su [documentación oficial para Linux](https://docs.ollama.com/linux).
Ejecuta el servidor y descarga el modelo dentro de **la misma distribución WSL**
en la que ejecutas Python:

```bash
ollama serve
```

Deja esa terminal abierta si el servidor no está funcionando como servicio.
En otra terminal:

```bash
ollama pull llama3.2:3b
ollama list
```

El modelo debe existir en tu equipo; cambiar su nombre en la GUI no lo descarga.
El tiempo de respuesta depende de RAM, CPU/GPU y del tamaño del modelo.
La aplicación usa `http://127.0.0.1:11434/api/chat` y rechaza servidores remotos.
No requiere una clave de OpenAI ni envía los correos a una API en la nube.

## 3. Primer ejercicio: tutor de SQL

```bash
bash examen-llm-logistica/ejecutar.sh 1
```

Ejemplo de pregunta: «¿Cómo consulto los títulos de una tabla libros?».
Pulsa **Enviar**, luego **Resumen de mi historial**. El tutor usa una biblioteca
escolar ficticia para explicar SELECT, WHERE, JOIN y GROUP BY. Puedes exportar el
historial o comenzar una conversación nueva.

El historial completo se guarda en `.datos/tutor_historial.json`; el contexto del
chat y del resumen se limita a las últimas seis interacciones y se informa en la
ventana. Si Ollama falla, la pregunta fallida no se agrega al historial. El resumen
local de respaldo muestra el número de consultas y las últimas preguntas, sin
simular una respuesta del modelo.

Otro modelo instalado:

```bash
bash examen-llm-logistica/ejecutar.sh 1 --modelo llama3.2:1b
```

## 4. Segundo ejercicio: ensayo sin servicios externos

```bash
bash examen-llm-logistica/ejecutar.sh 2 --demo --cargar-demo
```

Este modo usa el archivo `.datos/demo.json`, se identifica como **DEMOSTRACIÓN
LOCAL** y comienza con el LLM deshabilitado. Sirve para ensayar formularios, CRUD,
tablas, gráficas, respaldo por reglas y exportaciones. **No demuestra la conexión
a MongoDB ni el funcionamiento de un LLM real.** Puedes activar Ollama desde
Configuración para probarlo con los datos locales.

La carga añade 4 camiones, 4 accesos, 3 incidentes y 6 riesgos ficticios. Es
idempotente: al repetirla no reemplaza registros ya existentes. No se generan
respuestas falsas del LLM para rellenar su colección de evaluaciones.

## 5. Segundo ejercicio: MongoDB local o Atlas

Crea el archivo de configuración una sola vez, sin reemplazar uno existente:

```bash
cd ~/universidad/fundamentos-ia
test -f examen-llm-logistica/.env || cp examen-llm-logistica/.env.example examen-llm-logistica/.env
code examen-llm-logistica/.env
```

**MongoDB local:** deja `MONGO_URI=mongodb://127.0.0.1:27017/` y asegúrate de tener
el servidor `mongod` iniciado. MongoDB Compass es el cliente para visualizar la
base; Compass por sí solo no inicia un servidor.

**Atlas del profesor:** deja `MONGO_URI=` vacío y completa `Mongo_User`,
`Mongo_Password`, `Mongo_Cluster` y `Mongo_DB`. Usa una base separada para el examen,
por ejemplo `Einar_Ivan_Lazcano_Luna_Examen`, si tu usuario tiene permiso para ella.
Si el profesor limita el acceso a otra base, utiliza la autorizada. La aplicación
filtra además por alumno y proyecto en todas las colecciones. Atlas debe permitir
la IP desde la cual se conecta tu WSL; solicita al profesor los permisos necesarios.

La contraseña se codifica al construir la URL y no se imprime. Se acepta la
variable antigua `Mongo_Closter`, aunque se recomienda `Mongo_Cluster`.
El archivo `.env` y la carpeta `.datos` están excluidos de Git.

Ejecuta:

```bash
bash examen-llm-logistica/ejecutar.sh 2
```

En **Configuración**, comprueba la conexión. Si deseas insertar datos ficticios
en la base real, pulsa **Cargar datos de demostración** y confirma el destino.
La aplicación no cambia silenciosamente a almacenamiento local si falla MongoDB.

## 6. Operación desde la interfaz

| Pantalla | Uso |
| --- | --- |
| Panel de control | Filtrar por fechas de creación UTC y ver camiones únicos atendidos, accesos, incidentes abiertos, riesgos residuales críticos y agregación por semana ISO. |
| Camiones | Alta, consulta, edición y baja lógica; placa e identificador únicos. |
| Control de acceso | Crear una decisión, buscar por placa para cargar P/S, confirmar Q/R/H/T y observar semáforo y explicación. Las correcciones exigen motivo. |
| Tablas de verdad | Cambiar seis interruptores y ver A/E/B/F en vivo; consultar las tablas completas. No guarda accesos. |
| Incidentes | Pegar correo y clasificar; editar categoría, prioridad, entidades y estado; consultar historial. |
| Asistente con fuentes | Preguntar por CAM-102 o una placa; ver explicación y registros citados. Cargar historial persistido. |
| Riesgos éticos | CRUD, evidencia, probabilidad/impacto iniciales y residuales, gráfica comparativa. |
| Evaluaciones LLM | Ver prompts, respuestas, intentos, modelo, latencia y coincidencia; las altas o correcciones manuales se identifican como tales. |
| Experimento | Revisar etiquetas una a una, ejecutar comparación y exportar métricas. |
| Reportes | Exportar los registros consultados, con historial, a PDF/CSV/JSON. |
| Configuración | Elegir modelo, tiempos de espera, operador, umbral de riesgo, horario y simulación de correo. |

En las tablas pulsa **Actualizar** para cargar datos. **Detalle e historial**
permite inspeccionar la evidencia. Las bajas se ocultan de las listas activas,
pero quedan almacenadas para auditoría. No existe un borrado físico desde la GUI.
Si otro operador modificó el registro, actualiza la lista antes de corregirlo.

Las notificaciones de soporte son simuladas por defecto. Desactivar la simulación
no envía nada automáticamente: se necesitan variables SMTP en `.env`, pulsar
**Notificar soporte** y confirmar el envío. El programa no controla una barrera real.

## 7. Evaluación de al menos 30 correos

Se incluyen 30 correos sintéticos, con etiquetas propuestas **aún no confirmadas
por una persona**. No se presentan como correos operativos ni como etiquetado humano
ya realizado. En **Experimento → Revisar etiquetas manualmente**, lee cada mensaje,
corrige categoría/prioridad si corresponde, marca la confirmación y guarda el conjunto.
La GUI usa el archivo revisado en la siguiente ejecución.

Para la evaluación final activa el LLM real y pulsa **Ejecutar comparación**.
Se calculan exactitud de categoría y prioridad, matriz de confusión y latencia
media/mediana/p95 para reglas, LLM e híbrido. El informe distingue ausencia de
respuesta, reintentos, respaldo por reglas y diferencias formal/informal.

También puedes ejecutar sin interfaz ni MongoDB, desde la raíz del proyecto:

```bash
.venv/bin/python examen-llm-logistica/logiuncodigo.py \
  --evaluar examen-llm-logistica/datos/correos_etiquetados.json \
  --salida examen-llm-logistica/.datos/evaluacion_ollama.json
```

Para la entrega sustituye el corpus por tu archivo revisado. La evaluación por
terminal guarda un JSON local; la evaluación desde GUI registra además cada
intento del LLM en `evaluaciones_llm`.

Para reproducir únicamente la línea base:

```bash
.venv/bin/python examen-llm-logistica/logiuncodigo.py \
  --evaluar examen-llm-logistica/datos/correos_etiquetados.json --solo-reglas \
  --salida examen-llm-logistica/.datos/evaluacion_reglas.json
```

El resultado incluido en `docs/resultados_reglas.json` fue medido con el LLM
deshabilitado. Sus campos de métricas LLM son `null`; la salida híbrida en esa
ejecución corresponde exclusivamente al respaldo por reglas.

## 8. Pruebas

```bash
.venv/bin/python -m pip install -r examen-llm-logistica/requirements-dev.txt
cd examen-llm-logistica
../.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas de MongoDB usan un sustituto en memoria; no escriben en el clúster del
profesor. Los dobles del LLM comprueban contratos y errores, no su calidad lingüística.
Consulta el informe técnico para distinguir las verificaciones realizadas de las
pruebas que requieren tu instancia real de MongoDB y Ollama.
