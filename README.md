# Prácticas de Fundamentos de Inteligencia Artificial

Ejercicios de Einar Ivan Lazcano Luna. Las prácticas **1 a 7** se ejecutan como
aplicaciones web independientes en el navegador, con Python y Flask para las
reglas y HTML, CSS y JavaScript para la interfaz.

## Inicio en WSL

Desde la carpeta del proyecto, después de descargar los cambios de GitHub:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-01-tablas-de-verdad/requirements.txt
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

Cada carpeta incluye el programa Python, templates/index.html, static/estilos.css,
static/app.js, requirements.txt, ejecutar.sh y sus instrucciones. La práctica 5
permite descargar el reporte en TXT. Las respuestas y resultados están en español.

[Consulta las reglas y las instrucciones completas](unidad-01-introduccion-ia/practicas/README.md).

## MongoDB

Las prácticas de conexión tienen sus propias instrucciones:

- [Práctica 8: MongoDB local](unidad-01-introduccion-ia/practicas/practica-08-conexion-mongodb/README.md).
- [Práctica 9: MongoDB Atlas](unidad-01-introduccion-ia/practicas/practica-09-conexion-mongodb-atlas/README.md).

Las prácticas 1 a 7 usan únicamente Flask. Para desarrollar en VS Code con WSL,
selecciona el intérprete .venv/bin/python del proyecto.
