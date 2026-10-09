# Práctica 13: búsquedas en anchura y profundidad

**Materia:** Fundamentos de Inteligencia Artificial. **Objetivo:** representar
un problema de búsqueda y encontrar una ruta mediante BFS y DFS, explicando
el orden de exploración, el uso de la memoria y el costo del camino.

Se desarrollan los ejemplos `p11problema_busqueda.py` y
`p21busquedaciegadfs.py` del archivo `busquedas.rar`. Los ejercicios conservan
sus grafos y el orden de vecinos originales. Las dos gráficas del mismo archivo
están en la [práctica 12](../practica-12-grafica-matplotlib/README.md).

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
valida que existan; en DFS esa consulta no tiene ruta porque las aristas van de
padres a hijos. Usa `--help` para consultar los parámetros.

## Uso de la interfaz

1. Selecciona **BFS** o **DFS**. El dibujo cambia al grafo original de ese ejercicio.
2. Elige el inicio y la meta; de forma predeterminada son A y F.
3. Pulsa **Calcular**. Se muestra el primer paso y se imprime el recorrido en terminal.
4. Usa **Paso siguiente** o **Animar**; puedes pausar la animación. El panel
   muestra orden de visita, camino actual y cola o pila de llamadas.
5. Pulsa **Ver resultado** para saltar al final. Se muestran ruta y costo,
   o un mensaje claro cuando no existe un camino.

Cambiar una selección cancela la animación y limpia el resultado anterior.
El camino se marca en verde y el nodo actual en ámbar; los textos permiten
seguir el recorrido sin depender exclusivamente de los colores.

## Modelo del problema: P = (S, A, s0, G, C)

| Elemento | Representación |
| --- | --- |
| S: estados | A, B, C, D, E y F |
| A: acciones | Moverse a un vecino del diccionario de adyacencias |
| s0: estado inicial | A por defecto; seleccionable |
| G: prueba de meta | El estado actual coincide con el objetivo, F por defecto |
| C: costo | Una unidad por arista recorrida |

### BFS: grafo no dirigido

| Estado | Vecinos, en orden |
| --- | --- |
| A | B, D |
| B | A, C |
| C | B, F |
| D | A, E |
| E | D, F |
| F | C, E |

BFS usa una cola FIFO: el primero en entrar es el primero en salir.
`deque.popleft()` retira el primer camino. Se marcan los nodos al encolarlos
para evitar duplicados y ciclos. Con todas las aristas de costo 1, la primera
ruta encontrada tiene el menor número de movimientos.

### DFS: árbol dirigido

| Estado | Hijos, en orden |
| --- | --- |
| A | B, C |
| B | D, E |
| C | F |
| D, E, F | Sin hijos |

DFS utiliza recursión: profundiza primero por B y retrocede cuando una rama no
alcanza la meta. Se mantiene un conjunto de visitados y una copia independiente
del camino encontrado. Devuelve la primera ruta según el orden de vecinos;
en un grafo general no garantiza la ruta más corta. La versión recursiva es
adecuada para estos seis nodos; un grafo muy profundo necesitaría una pila
explícita para evitar el límite de recursión de Python.

## Resultados con inicio A y objetivo F

| Ejercicio | Orden de visita | Ruta encontrada | Costo |
| --- | --- | --- | ---: |
| BFS | A → B → D → C → E → F | A → B → C → F | 3 |
| DFS | A → B → D → E → C → F | A → C → F | 2 |

**Orden de visita y ruta solución son diferentes.** BFS también podría llegar
por A → D → E → F con costo 3; la primera solución es la rama de B por el orden
de vecinos. Los ejemplos devuelven una ruta, no enumeran todas las rutas.

Los costos de la tabla no comparan la eficiencia de los algoritmos: los grafos
originales son distintos. El árbol DFS de esta práctica coloca E bajo B,
tal como el código recibido; el árbol de la práctica 11 permanece independiente.

## Archivos y mejoras

- `busquedas.py`: grafos, validación, algoritmos, costo y pasos inmutables.
  Las funciones no dependen de variables globales modificables ni de la interfaz.
- `13_busquedas.py`: salida de terminal, dibujo y controles de Tkinter.
  Importarlo no abre ventanas ni inicia recorridos.
- `ejecutar.sh`: selecciona el intérprete del proyecto.
- `test_busquedas.py`: comprueba rutas originales, ciclos, retroceso,
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
