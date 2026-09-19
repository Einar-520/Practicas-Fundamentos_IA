# Prácticas de la unidad 1

Las prácticas 1 a 7 tienen interfaz web en español con **Python, Flask, HTML,
CSS y JavaScript**. Cada carpeta contiene un programa independiente con sus
propias reglas, plantillas, estilos y JavaScript.

| N.º | Práctica e instrucciones | Dirección |
| --- | --- | --- |
| 1 | [Tablas de verdad](practica-01-tablas-de-verdad/README.md) | http://localhost:5101 |
| 2 | [Sistema de examen](practica-02-sistema-examen/README.md) | http://localhost:5102 |
| 3 | [Examen con lista oficial](practica-03-sistema-examen-lista-oficial/README.md) | http://localhost:5103 |
| 4 | [Diagnóstico de equipo](practica-04-diagnostico-equipo/README.md) | http://localhost:5104 |
| 5 | [Diagnóstico con reporte](practica-05-diagnostico-equipo-reporte/README.md) | http://localhost:5105 |
| 6 | [Sistema experto de salud](practica-06-sistema-experto-salud/README.md) | http://localhost:5106 |
| 7 | [Sistema experto de salud mejorado](practica-07-sistema-experto-salud-mejorado/README.md) | http://localhost:5107 |
| 8 | [MongoDB local](practica-08-conexion-mongodb/README.md) | http://localhost:5000 |
| 9 | [MongoDB Atlas](practica-09-conexion-mongodb-atlas/README.md) | http://localhost:5001 o ventana Tkinter |
| 10 | [Agente de climatización](practica-10-agente-climatizacion/README.md) | Ventana Tkinter |

## Preparar el entorno

En la terminal WSL, desde la raíz del proyecto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-01-tablas-de-verdad/requirements.txt
bash iniciar_practica_web.sh 1
```

Las siete prácticas usan la misma dependencia, Flask; basta instalarla una vez
en ese entorno. Selecciona `.venv/bin/python` como intérprete en VS Code.
Abre la dirección de la práctica que iniciaste. Para cambiar de práctica, detén
el servidor con Ctrl+C y cambia el número del último comando. Para abrir varias
a la vez, inicia cada una en una terminal distinta. No necesitas Live Server.

También puedes ejecutar el archivo ejecutar.sh dentro de cada carpeta. El
lanzador de la raíz solo elige qué programa iniciar; no mezcla las prácticas.

## Funcionalidad conservada

1. **Tablas de verdad:** cuatro combinaciones de P y Q con negación, conjunción,
   disyunción, implicación y equivalencia.
2. **Examen:** asistencia mínima de 80, promedio mínimo de 8, proyecto entregado
   y sin adeudos; la autorización especial es una alternativa.
3. **Lista oficial:** además de las reglas del examen, aparecer en la lista es
   obligatorio incluso con autorización especial.
4. **Diagnóstico:** electricidad, encendido e imagen, en ese orden; los daños
   físicos se informan como resultado adicional.
5. **Reporte:** datos del usuario y del equipo, folio, fecha, diagnóstico,
   consistencia de respuestas, proposiciones, observaciones y descarga TXT.
6. **Salud:** tres síntomas evaluados con las reglas originales.
7. **Salud mejorado:** siete síntomas y selección de la primera regla aplicable,
   con explicación y recomendación. Los ejercicios de salud son académicos.

Los campos vacíos, las opciones inválidas y los números no finitos se rechazan
en Python. El servidor conserva las funciones originales que deciden los
resultados. El navegador recibe JSON y muestra los resultados sin recargar la
página. Las sesiones se separan por práctica para poder utilizarlas a la vez.

## Prácticas con MongoDB

- [Práctica 8: conexión local](practica-08-conexion-mongodb/README.md).
- [Práctica 9: conexión con Atlas](practica-09-conexion-mongodb-atlas/README.md).

Cada una tiene sus propias dependencias e instrucciones. Las prácticas 1 a 7
pueden ejecutarse sin tener MongoDB instalado ni conectado.

Las prácticas 8 y 9 también tienen interfaz web. El lanzador acepta números del 1 al 9.
Se conserva una sola implementación por carpeta; las anteriores están en el historial de Git.


## Práctica 10: agente reactivo simple

El agente captura temperatura y humedad, conserva las reglas condición-acción del
profesor e inserta en Atlas la percepción, la acción y la fecha. Se ejecuta de forma
independiente con ejecutar.sh dentro de practica-10-agente-climatizacion. Su .env
apunta por defecto a la colección climatizacion de Einar_Ivan_Lazcano_Luna.
