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
| 10 | [Agente de climatización con Tkinter y Matplotlib](practica-10-agente-climatizacion/README.md) | Ventana Tkinter |
| 11 | [Árbol binario: rutas de A a F](practica-11-arbol-binario/README.md) | Ventana Tkinter o terminal |
| 12 | [Gráficas de ventas y paletas](practica-12-grafica-matplotlib/README.md) | Ventana Matplotlib o PNG |
| 13 | [Búsquedas BFS y DFS](practica-13-busquedas-bfs-dfs/README.md) | Ventana Tkinter o terminal |
| 14 | [Búsqueda de costo uniforme (UCS)](practica-14-costo-uniforme/README.md) | Ventana Tkinter o terminal |
| 15 | [Heurísticas y búsqueda A*](practica-15-busqueda-a-estrella/README.md) | Ventana Tkinter o terminal |
| 16 | [Distancias Manhattan y Euclidiana](practica-16-distancias-heuristicas/README.md) | Ventana Tkinter o PNG |
| 17 | [Hill Climbing: lista y productos](practica-17-hill-climbing/README.md) | Ventana Tkinter, terminal o PNG |
| 18 | [Asignación de turnos](practica-18-asignacion-turnos/README.md) | Ventana Tkinter, terminal o PNG |
| 19 | [Catálogo de 24 gráficas y paletas](practica-19-catalogo-graficas/README.md) | Ventana Matplotlib o PNG |

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

El agente captura temperatura y humedad y conserva las reglas condición-acción
del profesor. Tkinter muestra el selector de acción arriba, los registros al
centro y sus gráficas de Matplotlib abajo. El panel lateral permite crear, editar y eliminar
lecturas. El filtro se aplica en MongoDB antes de paginar; la tabla y las gráficas
usan los mismos registros de la página consultada.

Se ejecuta de forma independiente con ejecutar.sh dentro de
practica-10-agente-climatizacion y abre una ventana Tkinter. Su .env
apunta por defecto a la colección climatizacion de Einar_Ivan_Lazcano_Luna en el
clúster del profesor. Las consultas y los cambios se limitan al alumno y práctica.

## Práctica 11: árbol binario

A es la raíz; B y D forman la rama izquierda, y C, E y F la derecha.
La búsqueda en profundidad muestra A → B → D, A → C → E y A → C → F.
La única ruta de A hasta F es A → C → F. Ejecuta el archivo ejecutar.sh de
practica-11-arbol-binario para abrir la ventana Tkinter: dibuja el árbol, muestra
las rutas y permite resaltar el camino a F. Añade --terminal para ver únicamente
la salida de terminal. Requiere Tkinter y soporte gráfico para abrir la ventana.

## Práctica 12: gráficas de ventas y paletas

Desarrolla los ejemplos `graficas1.py` y `graficas3.py`: ventas simuladas de
EcoMart con promedio y máximo, y comparación de quince paletas con los mismos
datos y escala. Cada programa exporta un PNG a 300 dpi. El lanzador abre ventas;
con `--paletas` abre la galería. Ambos admiten `--sin-ventana`.

## Práctica 13: BFS y DFS

Desarrolla `p11problema_busqueda.py` y `p21busquedaciegadfs.py` sobre el mismo
árbol de la imagen de clase: A a H, con G y H como hijos de E. La ventana Tkinter
permite elegir inicio y objetivo, animar, consultar la ruta y ver profundidad
actual, máxima explorada y retrocesos. Usa `--terminal --algoritmo bfs` o
`--terminal --algoritmo dfs` para trabajar sin interfaz. La lógica valida el grafo,
evita ciclos y distingue el orden de visita del camino solución.

## Práctica 14: búsqueda de costo uniforme

Utiliza `heapq` y costo acumulado para encontrar una ruta de costo mínimo en
el grafo de A a J del pizarrón. Tkinter muestra el recorrido, los pesos y la cola
de prioridad; permite cambiar inicio, meta y costos. Los pesos deben ser finitos
y no negativos. La búsqueda también puede ejecutarse con `--terminal`.

La meta se confirma al extraer el mínimo de la cola. El programa conserva la
mejor ruta conocida y descarta entradas antiguas. El ejemplo A → C → F → J
suma 3 + 2 + 3 = 8. Las instrucciones y pruebas están en su propia carpeta.

## Práctica 15: heurísticas y búsqueda A*

Busca de A a J con `f(n) = g(n) + h(n)`. Conserva las h del ejercicio y usa
el grafo de su imagen: F → I → J. Como no se indicaron pesos, cada movimiento
cuesta inicialmente 1; la ruta A → C → F → I → J tiene costo 4.

La ventana muestra g, h, f, profundidad, frontera y pasos. Permite animar y
editar los costos y heurísticas. Incluye una revisión didáctica de h: con
pesos unitarios, A, C y F sobreestiman el costo real restante. El algoritmo
mantiene mejores costos, reabre estados y descarta entradas antiguas del heap.
Se ejecuta con `ejecutar.sh` en su carpeta; `--terminal` evita abrir la ventana.

## Práctica 16: distancias Manhattan y Euclidiana

Calcula `|xB-xA| + |yB-yA|` y `sqrt((xB-xA)² + (yB-yA)²)`, y dibuja ambas
líneas con Matplotlib dentro de Tkinter. Con A=(1,2) y B=(5,5) obtiene 7 y 5
unidades. Incluye puntos editables, dos órdenes para el recorrido Manhattan,
tabla comparativa, validación y exportación PNG. Los puntos iguales o alineados
se representan sin errores. Usa `--terminal` para calcular o `--sin-ventana`
para exportar el gráfico sin abrir la interfaz.

## Práctica 17: Hill Climbing

Búsqueda local con mejora estricta en la lista 2, 5, 8, 12, 9, 6, 3 y en un
catálogo de cinco productos. Desde el primer valor, el recorrido es 2 → 5 → 8 → 12.
Con presupuesto $1,000, la selección C, D y E cuesta $1,000 y genera beneficio 170.

Tkinter permite cambiar el inicio, el presupuesto y la selección inicial;
Matplotlib muestra el recorrido, los productos y la evolución del beneficio.
La verificación exhaustiva independiente revisa 32 combinaciones y permite ver
cuándo el algoritmo queda atrapado en un máximo local. Incluye terminal, PNG,
validación, documentación y pruebas en su propia carpeta.

## Práctica 18: asignación de turnos

Asigna cuatro empleados a cuatro turnos, sin repetir horarios. Cada preferencia
cumplida suma un punto. Hill Climbing intercambia los turnos de una pareja y
acepta solo mejoras; una revisión independiente verifica las 24 permutaciones.

Luis recibe Tarde, Carlos recibe Noche y Ana/María se reparten Mañana y Mixto.
Existen dos soluciones óptimas, ambas con 3 de 4 preferencias cumplidas (75 %).
La interfaz Tkinter incluye la tabla de preferencias, inicio editable, historial,
consulta de ambas soluciones y gráficas Matplotlib exportables a PNG.

La pestaña Rotación de turnos permite que todos pasen por los cuatro horarios
o que Ana y María alternen Mañana/Mixto conservando el 75 %. Genera de 1 a 52
periodos, permite recorrerlos y exporta el calendario CSV y sus gráficas PNG.

## Práctica 19: catálogo de gráficas y paletas

Incluye los 24 ejemplos del archivo de clase: líneas, barras, proporciones,
distribuciones, relaciones, superficies y coordenadas polares. Genera PNG y
permite elegir tres paletas con los mismos datos ficticios. Las gráficas son
funciones independientes; se puede ejecutar una, varias o todo el catálogo.

`bash practica-19-catalogo-graficas/ejecutar.sh` genera todas las imágenes.
Añade `--grafica 10 --paleta oceano --mostrar` para abrir la dona, o `--listar`
para consultar los tipos. El README incluye ejercicios, dependencias y pruebas.
