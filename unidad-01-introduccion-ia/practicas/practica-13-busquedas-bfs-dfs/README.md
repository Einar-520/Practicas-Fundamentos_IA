# Práctica 13: búsquedas en anchura y profundidad

**Materia:** Fundamentos de Inteligencia Artificial. **Objetivo:** representar
un problema de búsqueda y encontrar una ruta mediante BFS y DFS, explicando
el orden de exploración, el uso de la memoria y el costo del camino.

Se desarrollan los ejemplos `p11problema_busqueda.py` y
`p21busquedaciegadfs.py` del archivo `busquedas.rar`. La ampliación utiliza
**el mismo árbol de la imagen de clase para ambos algoritmos**, con G y H
como hijos de E. Las versiones anteriores se conservan en el historial de Git.
Las dos gráficas del archivo están en la
[práctica 12](../practica-12-grafica-matplotlib/README.md).

## Ejecutar en VS Code y WSL

Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
bash unidad-01-introduccion-ia/practicas/practica-13-busquedas-bfs-dfs/ejecutar.sh
```

Abre una ventana **Tkinter**; no utiliza localhost. El lanzador usa
`.venv/bin/python` si existe o `python3` en caso contrario. La lógica y la
terminal usan solo la biblioteca estándar de Python, versión 3.10 o posterior.
No se necesita instalar paquetes con pip. La ventana requiere Tkinter y soporte
gráfico WSLg. Si falta Tkinter en Ubuntu, instálalo para el Python que utilizas:

```bash
sudo apt install python3-tk
```

Si tu entorno utiliza una versión de Python diferente a la de Ubuntu, necesita
el paquete Tk correspondiente a esa versión. Puedes comprobar el intérprete
con `.venv/bin/python -m tkinter`.

Para ejecutar los ejemplos sin interfaz ni soporte gráfico:

```bash
bash unidad-01-introduccion-ia/practicas/practica-13-busquedas-bfs-dfs/ejecutar.sh --terminal --algoritmo bfs
bash unidad-01-introduccion-ia/practicas/practica-13-busquedas-bfs-dfs/ejecutar.sh --terminal --algoritmo dfs
```

Puedes elegir otros estados, por ejemplo `--inicio F --objetivo A`. El programa
valida que existan; esa consulta no tiene ruta porque las aristas van de
padres a hijos. Usa `--help` para consultar los parámetros.

## Uso de la interfaz

1. Selecciona **BFS** o **DFS**. Ambos recorren el mismo árbol, siguiendo el orden de hijos de izquierda a derecha.
2. Elige el inicio y la meta; de forma predeterminada son A y F.
3. Pulsa **Calcular**. Se muestra el primer paso y se imprime el recorrido en terminal.
4. Usa **Paso siguiente** o **Animar**; puedes pausar la animación. El panel
   muestra orden de visita, camino actual y cola o pila de llamadas. Arriba se
   actualizan profundidad actual, máxima explorada y retrocesos acumulados.
5. Pulsa **Ver resultado** para saltar al final. Se muestran ruta y costo,
   o un mensaje claro cuando no existe un camino.

Cambiar una selección cancela la animación y limpia el resultado anterior.
El camino se marca en verde y el nodo actual en ámbar; los textos permiten
seguir el recorrido sin depender exclusivamente de los colores.

## Modelo del problema: P = (S, A, s0, G, C)

| Elemento | Representación |
| --- | --- |
| S: estados | A, B, C, D, E, F, G y H |
| A: acciones | Moverse a un vecino del diccionario de adyacencias |
| s0: estado inicial | A por defecto; seleccionable |
| G: prueba de meta | El estado actual coincide con el objetivo, F por defecto |
| C: costo | Una unidad por arista recorrida |

### Árbol compartido: conexiones de la imagen

| Estado | Hijos, en orden | Profundidad desde A |
| --- | --- | ---: |
| A | B, C | 0 |
| B | D, E | 1 |
| C | F | 1 |
| D | Sin hijos | 2 |
| E | G, H | 2 |
| F | Sin hijos | 2 |
| G | Sin hijos | 3 |
| H | Sin hijos | 3 |

Las aristas son dirigidas de padre a hijo. G y H pueden elegirse como inicio o
meta, tanto en la ventana como en los argumentos de terminal.

### BFS: búsqueda en anchura

BFS usa una cola FIFO: el primero en entrar es el primero en salir.
`deque.popleft()` retira el primer camino. Se marcan los nodos al encolarlos
para evitar duplicados y ciclos. Con todas las aristas de costo 1, la primera
ruta encontrada tiene el menor número de movimientos.

### DFS: búsqueda en profundidad

DFS utiliza recursión: profundiza primero por B y retrocede cuando una rama no
alcanza la meta. Se mantiene un conjunto de visitados y una copia independiente
del camino encontrado. Devuelve la primera ruta según el orden de vecinos;
en un grafo general no garantiza la ruta más corta. La versión recursiva es
adecuada para estos ocho nodos; un grafo muy profundo necesitaría una pila
explícita para evitar el límite de recursión de Python.

## Profundidad y retrocesos

- **Profundidad actual:** número de aristas del camino actual desde el inicio
  seleccionado. El inicio tiene profundidad 0. Durante un retroceso se muestra
  la profundidad del padre al que se regresa; si ya no hay camino se muestra «—».
- **Máxima explorada:** mayor profundidad visitada hasta el paso que se está
  mostrando. Puede superar la profundidad de la solución porque DFS puede
  explorar otras ramas antes de encontrar la meta.
- **Retrocesos:** regresos efectivos de un hijo a su padre cuando esa rama no
  contiene la meta. Cada arista recorrida de regreso suma uno. No se cuenta
  salir de la raíz ni el retorno de funciones después de encontrar la solución.
  BFS muestra 0 porque extrae caminos de una cola, sin retroceder por el árbol.

La tabla de pasos incluye las columnas **Prof.** y **Retr.**, y la terminal
imprime las mismas métricas. Al cambiar inicio, objetivo o algoritmo se reinician
los indicadores. La máxima se calcula sobre los nodos explorados, no los que
solamente se han añadido a la cola.

## Resultados con inicio A

| Algoritmo | Meta | Ruta | Profundidad de la solución | Máxima explorada | Retrocesos |
| --- | --- | --- | ---: | ---: | ---: |
| BFS | F | A → C → F | 2 | 2 | 0 |
| DFS | F | A → C → F | 2 | 3 | 5 |
| BFS | G | A → B → E → G | 3 | 3 | 0 |
| DFS | G | A → B → E → G | 3 | 3 | 1 |
| BFS | H | A → B → E → H | 3 | 3 | 0 |
| DFS | H | A → B → E → H | 3 | 3 | 2 |

Para buscar F, BFS visita **A → B → C → D → E → F**; DFS visita
**A → B → D → E → G → H → C → F**. El orden de visita no es la ruta solución.
Los cinco retrocesos de DFS son D → B, G → E, H → E, E → B y B → A.

Por ejemplo, para buscar H y ver las métricas en terminal:

```bash
bash unidad-01-introduccion-ia/practicas/practica-13-busquedas-bfs-dfs/ejecutar.sh --terminal --algoritmo dfs --objetivo H
```

Si el inicio también es la meta, la profundidad y el costo son 0. Los programas
devuelven una ruta; no enumeran todas las rutas. Esta práctica es independiente
del árbol de la práctica 11.

## Archivos y mejoras

- `busquedas.py`: árbol compartido, validación, algoritmos, costo, profundidad,
  retrocesos y pasos inmutables.
  Las funciones no dependen de variables globales modificables ni de la interfaz.
- `13_busquedas.py`: salida de terminal, dibujo y controles de Tkinter.
  Importarlo no abre ventanas ni inicia recorridos.
- `ejecutar.sh`: selecciona el intérprete del proyecto.
- `test_busquedas.py`: comprueba rutas a F/G/H, profundidad, retrocesos, ciclos,
  ausencia de ruta, estado inicial igual a meta y entradas inválidas.

Se reemplaza `pop(0)` por una cola adecuada, se evita repetir estados, se separa
la presentación de la búsqueda y se agrega una traza para explicar la ejecución.
Las estructuras de cada búsqueda son locales, por lo que repetir una consulta
no conserva visitados de una ejecución anterior.

Para verificar los algoritmos, desde la raíz del proyecto:

```bash
python3 -m unittest discover -s unidad-01-introduccion-ia/practicas/practica-13-busquedas-bfs-dfs -p 'test_*.py' -v
```

Referencia: [colas con collections.deque](https://docs.python.org/3/library/collections.html#collections.deque).
