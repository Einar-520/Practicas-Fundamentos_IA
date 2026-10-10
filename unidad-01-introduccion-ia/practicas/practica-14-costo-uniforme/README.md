# Práctica 14: búsqueda de costo uniforme (UCS)

**Materia:** Fundamentos de Inteligencia Artificial.

**Objetivo:** encontrar un camino desde un estado inicial hasta un objetivo,
seleccionando siempre el camino pendiente de menor **costo acumulado**. Se usa
`heapq`, la cola de prioridad de la biblioteca estándar de Python.

La práctica es independiente de BFS/DFS y de las demás aplicaciones. Incluye
interfaz **Tkinter**, animación, edición de costos y salida en terminal.

## Grafo de la imagen de clase

Se modela como un árbol dirigido de padre a hijo. No se añaden aristas inversas.
El inicio predeterminado es **A** y la meta **J**; ambos se pueden cambiar.

| Origen | Destino | Costo |
| --- | --- | ---: |
| A | B | 2 |
| A | C | 3 |
| B | D | 4 |
| B | E | 1 |
| C | F | 2 |
| C | G | 6 |
| D | H | 3 |
| E | I | 2 |
| F | J | 3 |

Los estados son **A, B, C, D, E, F, G, H, I y J**. En esta práctica H es hijo
de D, I de E y J de F, como en la nueva imagen. Su grafo no es el de la práctica 13.

## Ejecutar desde VS Code con WSL

Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
bash unidad-01-introduccion-ia/practicas/practica-14-costo-uniforme/ejecutar.sh
```

El lanzador utiliza `.venv/bin/python` si existe, o `python3` en caso contrario.
Se requiere Python 3.10 o posterior. **No se instalan paquetes con pip:**
`heapq`, `dataclasses`, `itertools`, `math` y `argparse` pertenecen a Python.

La interfaz abre una ventana de escritorio, no un sitio localhost. En Ubuntu/WSL
necesitas Tkinter y soporte gráfico WSLg. Si falta Tkinter:

```bash
sudo apt install python3-tk
```

Ese paquete debe corresponder a la versión de Python de tu entorno. Comprueba
la instalación con `.venv/bin/python -m tkinter`.

Puedes ejecutar sin Tkinter ni pantalla gráfica:

```bash
bash unidad-01-introduccion-ia/practicas/practica-14-costo-uniforme/ejecutar.sh --terminal
bash unidad-01-introduccion-ia/practicas/practica-14-costo-uniforme/ejecutar.sh --terminal --inicio A --objetivo I
```

El modo terminal utiliza los costos originales del pizarrón. El argumento
`--help` muestra las opciones. Para abrir la ventana con otra meta, usa por
ejemplo `--objetivo H` sin `--terminal`.

## Uso de la interfaz

1. Elige **Inicio** y **Objetivo** y pulsa **Calcular**.
2. Observa el primer nodo extraído, su costo acumulado y la frontera pendiente.
3. Usa **Paso siguiente** o **Animar**; el mismo botón permite pausar.
4. La pestaña **Frontera** muestra los caminos pendientes en orden de prioridad.
   La pestaña **Pasos** registra nodo, costo acumulado y profundidad.
5. Pulsa **Ver resultado** para consultar la ruta final y su costo mínimo.
6. Usa **Editar costos** para experimentar. Acepta cero y decimales con punto
   o coma. **Aplicar** valida todo y reinicia la búsqueda. **Cargar originales**
   recupera los números del pizarrón; pulsa Aplicar para utilizarlos.

Los cambios de costos duran hasta cerrar el programa y no modifican el archivo
Python. Cancelar la edición conserva el grafo actual. Los valores negativos,
infinitos, vacíos o no numéricos se rechazan con un mensaje claro.

El dibujo muestra el peso de cada arista, el camino actual en verde y el nodo
extraído en ámbar. Los indicadores muestran **g(n)**, el menor costo todavía
pendiente, la profundidad actual y el número de estados visitados.

## Cómo funciona UCS

El costo inicial es cero. Para un vecino `v` de un estado `n`:

```text
g(v) = g(n) + costo(n, v)
```

En `busqueda_ucs.py`, la función `ucs()` sigue estos pasos:

1. Valida el grafo y crea una copia con costos finitos mayores o iguales a cero.
2. Introduce el inicio con `heapq.heappush()` y prioridad cero.
3. Extrae mediante `heapq.heappop()` la entrada de menor costo acumulado.
4. Omite entradas antiguas que hayan sido reemplazadas por un costo mejor.
5. Si el estado extraído es la meta, devuelve el camino y el costo óptimo.
6. Calcula el costo de cada vecino; lo introduce si mejora el mejor costo conocido.
7. Repite hasta alcanzar la meta o vaciar la cola.

Cada entrada es `(costo, turno, estado, camino)`. `itertools.count()` proporciona
el turno para desempatar por orden de inserción. Si dos rutas tienen el mismo
costo, se conserva la primera descubierta. `mejores` guarda el menor costo
conocido; `resueltos` evita procesar nuevamente un estado ya extraído de forma válida.

**La meta se verifica al extraerla, no al insertarla.** Un camino caro podría
descubrir la meta primero y ser superado después por otra ruta más barata.
UCS utiliza el costo total desde el inicio, no solo el peso de la última arista
ni la cantidad de movimientos. No emplea una heurística.

La garantía de costo mínimo de esta implementación requiere un grafo finito
con pesos no negativos. Se admiten ciclos de costo cero sin repetir estados.
Si el inicio es la meta, el costo es 0. Si no hay ruta se informa explícitamente.

La tabla de frontera es una **copia ordenada para visualizar** las prioridades;
el algoritmo usa el heap para extraer elementos. Una lista usada como heap no
tiene todos sus elementos ordenados: garantiza que el mínimo está al principio.
La traza se conserva en memoria para explicar estos ejemplos pequeños.

## Resultado del ejemplo A → J

| Paso | Estado extraído | Costo acumulado g(n) |
| --- | --- | ---: |
| 1 | A | 0 |
| 2 | B | 2 |
| 3 | C | 3 |
| 4 | E | 3 |
| 5 | F | 5 |
| 6 | I | 5 |
| 7 | D | 6 |
| 8 | J | 8 |

- **Ruta solución:** A → C → F → J.
- **Costo:** 3 + 2 + 3 = **8**.
- **Profundidad de la solución:** 3 aristas.
- **Orden de visita:** A → B → C → E → F → I → D → J.

C se procesa antes que E porque entró primero con costo 3. F se procesa antes
que I por la misma razón, con costo 5. G y H quedan pendientes con costo 9
cuando se encuentra J. El orden de visita no es la ruta solución.

| Meta desde A | Ruta | Costo mínimo |
| --- | --- | ---: |
| H | A → B → D → H | 9 |
| I | A → B → E → I | 5 |
| J | A → C → F → J | 8 |
| G | A → C → G | 9 |

El árbol del pizarrón tiene una sola ruta desde A a cada estado. Los tests
incluyen además grafos con varias rutas para comprobar que UCS elige la más
barata y no devuelve prematuramente la primera meta descubierta.

## Archivos y verificación

- `busqueda_ucs.py`: datos, validación, cola de prioridad y traza inmutable.
- `14_costo_uniforme.py`: ventana Tkinter y modo terminal.
- `ejecutar.sh`: selecciona el intérprete del proyecto.
- `test_ucs.py`: rutas, costos, empates, ciclos, mejora de rutas, entradas
  obsoletas, pesos inválidos, desbordamiento, ausencia de ruta y costo cero.

Importar los módulos no abre ventanas ni ejecuta la búsqueda. Para correr las
pruebas desde la raíz:

```bash
python3 -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-14-costo-uniforme -p 'test_*.py' -v
```

Referencia: [documentación oficial de heapq](https://docs.python.org/3/library/heapq.html).
