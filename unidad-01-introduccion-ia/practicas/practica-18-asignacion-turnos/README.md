# Práctica 18: asignación de turnos con Hill Climbing

**Objetivo:** asignar cuatro empleados a cuatro turnos para maximizar el número
de preferencias cumplidas. Incluye interfaz Tkinter, gráficas Matplotlib,
recorrido en terminal y comprobación independiente de todas las asignaciones.

## Datos y reglas del ejercicio

| Empleado | Preferencia |
| --- | --- |
| Ana | Mañana |
| Luis | Tarde |
| Carlos | Noche |
| María | Mañana |

Turnos disponibles: **Mañana, Tarde, Noche y Mixto**.

- Cada empleado recibe exactamente un turno.
- Cada turno se asigna a exactamente un empleado.
- Una preferencia cumplida aporta **1 punto**; cualquier otro turno aporta **0**.
- Mixto es un turno diferente: no equivale parcialmente a Mañana, Tarde o Noche.
- Todos los empleados tienen el mismo peso en la función objetivo.

Se asume una sola plaza por turno, porque el ejercicio indica cuatro empleados
y cuatro turnos disponibles. No se agregan requisitos de antigüedad, salarios,
duración de jornadas ni restricciones que no estén en el enunciado.

La satisfacción es `sum(turno_asignado == turno_preferido)` y su porcentaje es
`preferencias_cumplidas / 4 * 100`.

## Resultado: dos asignaciones óptimas

| Empleado | Preferencia | Opción 1 | Opción 2 |
| --- | --- | --- | --- |
| Ana | Mañana | Mañana | Mixto |
| Luis | Tarde | Tarde | Tarde |
| Carlos | Noche | Noche | Noche |
| María | Mañana | Mixto | Mañana |

Ambas cumplen **3 de 4 preferencias: 75 %**. No es posible alcanzar el 100 %:
Ana y María solicitan Mañana y solo existe una plaza en ese turno. La otra
persona recibe Mixto. Luis y Carlos sí pueden recibir sus turnos preferidos.

La función objetivo no distingue entre las dos opciones. El ejercicio no
establece una regla para favorecer a Ana o a María; la interfaz muestra ambas
para que se pueda consultar el empate. El desempate interno de la búsqueda
solo permite reproducir sus pasos.

## Cómo funciona Hill Climbing

Un estado es una asignación completa, en el orden **Ana, Luis, Carlos, María**.
Un vecino intercambia los turnos de una pareja de empleados. Hay `4 × 3 / 2 = 6`
intercambios posibles por estado y todos conservan la asignación uno a uno.

En cada iteración se evalúan los seis vecinos, se elige el de mayor satisfacción
y solo se acepta si mejora estrictamente la puntuación actual. Los empates
entre vecinos mejores se resuelven conservando el primero en el orden de las
parejas de empleados. Si ningún vecino mejora, el algoritmo se detiene.

Se utiliza un inicio didáctico válido para observar los cambios:

| Paso | Ana | Luis | Carlos | María | Puntos | Intercambio |
| --- | --- | --- | --- | --- | ---: | --- |
| 0 | Tarde | Noche | Mixto | Mañana | 1 | Inicio |
| 1 | Noche | Tarde | Mixto | Mañana | 2 | Ana y Luis |
| 2 | Mixto | Tarde | Noche | Mañana | 3 | Ana y Carlos |

La **comprobación exhaustiva independiente** revisa `4! = 24` permutaciones y
encuentra las dos soluciones óptimas. No guía ni reemplaza los intercambios de
Hill Climbing. Las pruebas comprueban que, con estas preferencias y este tipo
de vecino, se alcanza una de las dos soluciones desde los 24 puntos de partida.
Esto no implica una garantía general para otros problemas de búsqueda local.

El algoritmo conserva el estado actual y el mejor vecino, sin una frontera como
la de BFS. Esta aplicación también almacena el historial para explicarlo y
graficarlo; por eso la aplicación completa usa memoria adicional para los pasos.

## Ejecutar desde VS Code con WSL

Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
git pull --ff-only origin main
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh
```

Requiere Python 3.10 o posterior y Matplotlib. Para la ventana se necesita Tkinter
y soporte gráfico WSLg. Si falta Tkinter en Ubuntu, instala
`sudo apt install python3-tk` para el Python utilizado. En VS Code selecciona
`.venv/bin/python` como intérprete. La práctica es independiente de las anteriores
y no usa MongoDB ni Ollama.

## Uso de la interfaz

1. Consulta la tabla de dos columnas con las preferencias originales.
2. Modifica la asignación inicial si lo deseas. Elegir un turno lo intercambia
   automáticamente con su ocupante para no duplicarlo.
3. Pulsa **Asignar turnos**. Se muestran el resultado y el porcentaje de satisfacción.
4. En **Mostrar**, elige el resultado de Hill Climbing o cualquiera de las dos
   asignaciones óptimas. La tabla y la gráfica de coincidencias se actualizan.
5. Abre **Intercambios paso a paso** para consultar la asignación de cada estado.
6. Pulsa **Guardar gráfica PNG** para exportar la asignación mostrada y el avance
   de la búsqueda. **Restablecer** recupera el inicio del ejemplo.

La gráfica de barras representa 1 si se cumple la preferencia y 0 si no se cumple.
La gráfica de línea corresponde al recorrido de Hill Climbing, aunque se consulte
otra solución óptima. Si cambias el inicio, los resultados anteriores se mantienen
identificados como pendientes y se desactiva la exportación hasta recalcular.

## Terminal y exportación sin pantalla

```bash
# Solo cálculos: no requiere Tkinter ni Matplotlib.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --terminal

# Generar salidas/Asignacion_turnos.png sin abrir la interfaz.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --sin-ventana

# Comenzar con una solución óptima: no hará intercambios.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --terminal --inicio Mañana Tarde Noche Mixto
```

`--salida ruta.png` permite elegir otro destino y activa la exportación sin
ventana. Se validan los nombres de los turnos, la cantidad de asignaciones y
que no existan turnos repetidos. Todos los mensajes están en español.

## Rotar turnos entre periodos

La pestaña **Rotación de turnos** utiliza como primer periodo la asignación
seleccionada en **Resultado y gráfica**. Permite generar entre **1 y 52 periodos**,
seleccionar una fila, avanzar con **Rolar al siguiente**, regresar con **Anterior**
y exportar el calendario CSV o su gráfica PNG. Los periodos son numerados:
pueden representar días o semanas según lo indique el profesor. No hay cambios
programados por reloj ni fechas asignadas automáticamente.

| Modo | Qué cambia | Satisfacción |
| --- | --- | --- |
| Todos pasan por los cuatro turnos | Cada empleado sigue Mañana → Tarde → Noche → Mixto → Mañana | 25 % en cada ciclo completo de cuatro periodos |
| Alternar Ana y María | Ana y María intercambian Mañana/Mixto; Luis conserva Tarde y Carlos Noche | 75 % en todos los periodos |

En la rotación completa, cada empleado ocupa cada turno una vez por ciclo.
En la alternancia por preferencias, Ana y María reciben Mañana la misma cantidad
de veces si el número de periodos es par; si es impar, quien inicia en Mañana
lo recibe una vez más. Este segundo modo mantiene las dos asignaciones óptimas,
pero Luis y Carlos no rotan. Las etiquetas de la interfaz distinguen ambos casos.

Ejemplo de rotación completa desde el resultado inicial de Hill Climbing:

| Periodo | Ana | Luis | Carlos | María | Satisfacción |
| --- | --- | --- | --- | --- | --- |
| 1 | Mixto | Tarde | Noche | Mañana | 75 % |
| 2 | Mañana | Noche | Mixto | Tarde | 25 % |
| 3 | Tarde | Mixto | Mañana | Noche | 0 % |
| 4 | Noche | Mañana | Tarde | Mixto | 0 % |

La gráfica izquierda muestra la satisfacción por periodo y resalta el
seleccionado. La derecha muestra en qué porcentaje de todo el calendario cada
empleado recibe su preferencia. Cambiar modo o cantidad marca los resultados
como pendientes y desactiva la navegación y las exportaciones hasta generar.
Cambiar la asignación inicial requiere pulsar **Asignar turnos** primero.

```bash
# Abrir directamente la pestaña de rotación.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --rotacion completa

# Revisar ocho periodos desde la terminal.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --terminal --rotacion completa --periodos 8

# Conservar 75 %, guardar calendario y gráfica sin ventana.
bash unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos/ejecutar.sh --rotacion preferencias --periodos 4 --csv /tmp/rotacion.csv --salida /tmp/rotacion.png
```

La búsqueda original por intercambios se conserva. La rotación se genera después
según el modo elegido; no se presenta como una mejora de la puntuación de Hill
Climbing ni como una planificación de descansos o jornadas.

## Archivos y pruebas

| Archivo | Función |
| --- | --- |
| `asignacion.py` | Datos, reglas, vecinos, Hill Climbing y verificación de las 24 permutaciones |
| `18_asignacion_turnos.py` | Ventana Tkinter y opciones para terminal |
| `graficas.py` | Gráficas de la asignación y de la rotación; exportación PNG |
| `rotacion.py` | Calendarios, validación, métricas y exportación CSV |
| `interfaz_rotacion.py` | Pestaña Tkinter para generar y recorrer los periodos |
| `test_rotacion.py` | Pruebas de ciclos, alternancia, límites y CSV |
| `test_asignacion.py` | Pruebas de los resultados, restricciones y todos los inicios |
| `ejecutar.sh` | Lanzador que utiliza el entorno virtual de la raíz si existe |

```bash
python3 -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-18-asignacion-turnos -p 'test_*.py' -v
```
