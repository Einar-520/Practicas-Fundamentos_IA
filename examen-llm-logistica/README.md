# Examen: tutor LLM y LogiSmart

Desarrollo de los dos ejercicios entregados por el profesor, en el orden solicitado.
Alumno: **Einar Ivan Lazcano Luna**. Ambos programas se ejecutan de forma independiente
y tienen una interfaz web con **HTML, CSS y JavaScript**, servida localmente por
**Flask**. Las gráficas SVG se dibujan a partir de los registros consultados, sin
servicios externos ni dependencias de Node para ejecutar la aplicación.

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
.venv/bin/python -m pip install -r examen-llm-logistica/requirements.txt
```

En VS Code selecciona `.venv/bin/python`. Abre las direcciones indicadas en el
navegador de Windows; no se requiere WSLg ni una ventana de Tkinter.

| Ejercicio | Dirección predeterminada |
| --- | --- |
| Tutor SQL | http://localhost:8011 |
| LogiSmart | http://localhost:8012 |

Los dos servidores se ejecutan de forma independiente. Mantén su terminal abierta
y usa `Ctrl+C` para detenerlos. Puedes cambiar el puerto agregando `--puerto 8020`.

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
página. Si Ollama falla, la pregunta fallida no se agrega al historial. El resumen
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
| Asistente con fuentes | Preguntar por un camión o generar informes de rechazados, retenidos, autorizados o inspección, con motivos, fuentes y descarga PDF/CSV/JSON. El historial persistido se carga al entrar. |
| Riesgos éticos | CRUD, evidencia, probabilidad/impacto iniciales y residuales, gráfica comparativa. |
| Evaluaciones LLM | Ver prompts, respuestas, intentos, modelo, latencia y coincidencia; las altas o correcciones manuales se identifican como tales. |
| Experimento | Revisar etiquetas una a una, ejecutar comparación y exportar métricas. |
| Reportes | Filtrar accesos por resultado y fecha; descargar totales, motivos y evidencia en PDF/CSV/JSON. Las demás colecciones conservan su exportación con historial. |
| Configuración | Elegir modelo, tiempos de espera, operador, umbral de riesgo, horario y simulación de correo. |

Las tablas se cargan al entrar a cada pantalla. Usa la búsqueda, el filtro de
estado o prioridad y la paginación. El botón del ojo abre el detalle y el historial;
el lápiz permite editar y la papelera realiza una baja con confirmación. Las bajas se ocultan de las listas activas,
pero quedan almacenadas para auditoría. No existe un borrado físico desde la GUI.
Si otro operador modificó el registro, actualiza la lista antes de corregirlo.

Las notificaciones de soporte son simuladas por defecto. Desactivar la simulación
no envía nada automáticamente: se necesitan variables SMTP en `.env`, pulsar
**Notificar a soporte** y confirmar el envío. El programa no controla una barrera real.

### Informes desde el asistente

Escribe, por ejemplo: **«Genera un informe de los camiones que fueron rechazados
y sus motivos»**. No necesitas indicar un CAM individual. Cada informe contiene
accesos, camiones únicos, fechas, motivos, premisas, explicación y referencias a
los registros consultados. «Rechazados» filtra el resultado `denegado`; las
retenciones se consultan por separado para conservar el significado de las reglas.

Puedes pedir autorizados, retenidos, inspección o todos los accesos. Se admite un
camión o placa, y fechas como `desde 2026-10-01 hasta 2026-10-07`, `hoy`, `ayer`,
`esta semana` o `este mes` (UTC). Sin fechas se incluyen todos los registros activos.
Los períodos no reconocidos muestran un mensaje para aclararlos; no se interpretan
como consultas sin filtro. Para elegir los filtros con controles, usa **Reportes**.

Debajo de la respuesta aparecen **Descargar PDF**, **Descargar CSV** y **Descargar
JSON**. El historial conserva una copia de los datos al generar el informe: editar
un acceso después no cambia esa descarga. Solicita otro informe para consultar
los datos actualizados. La vista del chat muestra hasta 20 accesos; las descargas
incluyen el conjunto completo. Si hay más de 1000, se pide reducir el período.

Los totales y motivos se calculan directamente sobre el almacenamiento activo
(MongoDB, o JSON si abriste `--demo`), sin depender de Ollama. La evaluación queda
identificada como `informe_registros` y `llm_consultado: false`; no representa una
inferencia del modelo. Las preguntas individuales conservan su RAG extractivo.

## 7. Evaluación de al menos 30 correos

Se incluyen 30 correos sintéticos, con etiquetas propuestas **aún no confirmadas
por una persona**. No se presentan como correos operativos ni como etiquetado humano
ya realizado. En **Experimento → Revisar correos**, lee cada mensaje,
corrige categoría/prioridad si corresponde, marca la confirmación y pulsa
**Guardar y siguiente**. La copia revisada se conserva en `.datos/correos_revisados.json`
y se usa en las siguientes evaluaciones. Exportar permite conservar una copia.
También puedes importar otro conjunto JSON con el mismo esquema.

Para la evaluación final activa **Incluir Ollama local** y pulsa **Ejecutar comparación**.
El último resultado se conserva en `.datos/ultimo_experimento.json` y se puede
descargar como PDF o JSON desde la pantalla.
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

## 8. Interfaz local y seguridad

La aplicación está pensada para un operador en su equipo. Escucha únicamente en
`127.0.0.1`, con depuración desactivada; no se debe exponer en una red pública.
Las solicitudes de la interfaz llevan un token local; se comprueban el host y
el origen, se limita el tamaño de entrada y los textos se escapan antes de
mostrarlos. Los datos del correo y las respuestas del modelo nunca se ejecutan
como HTML o JavaScript. No hay autenticación multiusuario ni despliegue público.

Las operaciones lentas se ejecutan como trabajos y la página consulta su estado.
Se muestra el tiempo transcurrido; puedes navegar mientras el modelo responde.
Solo se permite una escritura o trabajo lento a la vez. El historial y las
versiones del repositorio siguen protegiendo las correcciones de registros.

## 9. Pruebas

```bash
.venv/bin/python -m pip install -r examen-llm-logistica/requirements-dev.txt
cd examen-llm-logistica
../.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas de MongoDB usan un sustituto en memoria; no escriben en el clúster del
profesor. Los dobles del LLM comprueban contratos y errores, no su calidad lingüística.
Consulta el informe técnico para distinguir las verificaciones realizadas de las
pruebas que requieren tu instancia real de MongoDB y Ollama.

### Pruebas opcionales en navegador

En una terminal, desde `examen-llm-logistica`:

```bash
../.venv/bin/python tests/servidores_web.py
```

Ese servidor utiliza datos temporales y un sustituto explícito del LLM. En otra
terminal, desde la misma carpeta, con Node.js instalado:

```bash
npm install --prefix tests --no-save playwright
npx --prefix tests playwright install chromium
node tests/navegador.mjs
```

Estas dependencias se usan solo para pruebas. La aplicación normal no necesita npm.
Las capturas se generan en `tests/capturas`; no contienen credenciales reales.
