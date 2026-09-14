# Prácticas de Fundamentos de Inteligencia Artificial

Ejercicios de Einar Ivan Lazcano Luna. Las prácticas **1 a 9** se ejecutan como
aplicaciones web independientes en el navegador, con Python y Flask para las
reglas y HTML/CSS para la interfaz; las prácticas 1 a 7 y 9 también usan JavaScript.

## Inicio en WSL

Desde la carpeta del proyecto, después de descargar los cambios de GitHub:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/requirements.txt
bash iniciar_practica_web.sh 1
```

Abre **http://localhost:5101**. Mantén abierta la terminal y detén el servidor
con Ctrl+C. Cambia el último número del comando para iniciar otra práctica.
La interfaz se sirve desde Python; abre la dirección localhost indicada.

| N.º | Práctica | Puerto |
| --- | --- | --- |
| 1 | [Tablas de verdad](unidad-01-introduccion-ia/practicas/practica-01-tablas-de-verdad/README.md) | 5101 |
| 2 | [Sistema de examen](unidad-01-introduccion-ia/practicas/practica-02-sistema-examen/README.md) | 5102 |
| 3 | [Examen con lista oficial](unidad-01-introduccion-ia/practicas/practica-03-sistema-examen-lista-oficial/README.md) | 5103 |
| 4 | [Diagnóstico de equipo](unidad-01-introduccion-ia/practicas/practica-04-diagnostico-equipo/README.md) | 5104 |
| 5 | [Diagnóstico con reporte](unidad-01-introduccion-ia/practicas/practica-05-diagnostico-equipo-reporte/README.md) | 5105 |
| 6 | [Sistema experto de salud](unidad-01-introduccion-ia/practicas/practica-06-sistema-experto-salud/README.md) | 5106 |
| 7 | [Sistema experto de salud mejorado](unidad-01-introduccion-ia/practicas/practica-07-sistema-experto-salud-mejorado/README.md) | 5107 |
| 8 | [Guardar un dato en MongoDB local](unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/README.md) | 5000 |
| 9 | [Guardar un dato en MongoDB Atlas](unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/README.md) | 5001 |

Cada carpeta incluye el programa Python, templates/index.html, static/estilos.css,
requirements.txt, ejecutar.sh y sus instrucciones; las prácticas 1 a 7 y 9 también incluyen static/app.js. La práctica 5
permite descargar el reporte en TXT. Las respuestas y resultados están en español.

[Consulta las reglas y las instrucciones completas](unidad-01-introduccion-ia/practicas/README.md).

## MongoDB

Las prácticas de conexión tienen sus propias instrucciones:

- [Práctica 8: MongoDB local](unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/README.md).
- [Práctica 9: MongoDB Atlas](unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/README.md).

Las prácticas 1 a 7 usan únicamente Flask. Para desarrollar en VS Code con WSL,
selecciona el intérprete .venv/bin/python del proyecto.

## Una versión por práctica

Las nueve carpetas contienen las interfaces web vigentes. Las versiones anteriores
se consultan en el historial de Git; los ZIP e instaladores antiguos se retiraron.
El archivo Python de cada carpeta es el servidor de su interfaz web y se conserva.

Para actualizar una copia anterior abierta en VS Code, guarda los archivos del
editor y detén los servidores. Ejecuta desde WSL:

```bash
cd ~/universidad/fundamentos-ia &&
git fetch origin main &&
actualizador_practicas="$(mktemp)" &&
git show origin/main:sincronizar_practicas.py > "$actualizador_practicas" &&
python3 "$actualizador_practicas" "$PWD" &&
rm -- "$actualizador_practicas"
```

El actualizador requiere la rama main sin commits locales pendientes de integrar.
Primero respalda las prácticas y sus cambios locales fuera del proyecto, en una
carpeta hermana cuyo nombre muestra en la terminal. Conserva el .env de cada
práctica vigente. Sustituye el código por origin/main y retira los respaldos,
ZIP e instaladores antiguos de la carpeta de trabajo. El entorno .venv de la raíz,
los apuntes y las tareas locales quedan fuera de la limpieza. No reescribe el
historial ni envía cambios a GitHub. Si Git detecta un conflicto con otros archivos,
restaura el contenido respaldado y detiene la actualización.

Instala las dependencias de las nueve prácticas en el intérprete del proyecto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/requirements.txt
bash iniciar_practica_web.sh 1
```

Cambia el último número por cualquiera del 1 al 9. MongoDB local debe estar
iniciado para la 8; la 9 utiliza el .env de Atlas. Si todavía no existe, créalo con
el preparar_env.py de esa práctica siguiendo sus instrucciones.
