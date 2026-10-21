# Práctica 19: catálogo de gráficas y paletas de colores

**Materia:** Extracción de conocimiento en bases de datos.  
**Objetivo:** crear 24 tipos de gráficas con Matplotlib y NumPy, elegir el tipo
apropiado y comparar paletas manteniendo los mismos datos.

Desarrolla el archivo `graficas.py` compartido en clase. Los datos son ficticios,
se conservan las series originales y cada práctica sigue siendo independiente.
No requiere una conexión a MongoDB, Ollama ni a las otras prácticas.

## Ejecutar en VS Code con WSL

Desde la raíz del proyecto:

```bash
cd ~/universidad/fundamentos-ia
git pull --ff-only origin main
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-19-catalogo-graficas/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-19-catalogo-graficas/ejecutar.sh
```

Requiere Python 3.10 o posterior, NumPy y Matplotlib 3.9 o posterior. En VS Code
selecciona `.venv/bin/python`. El comando genera **24 PNG**, por defecto a 180 dpi,
dentro de `salida_graficas/original/` en la carpeta de esta práctica. No abre
ventanas salvo que se indique `--mostrar`. Repetir la misma selección y paleta
actualiza sus PNG; cada paleta tiene una subcarpeta diferente.

Desde la carpeta de la práctica también puedes ejecutar:

```bash
# Ver el catálogo y para qué sirve cada tipo.
python3 19_catalogo_graficas.py --listar

# Generar y abrir únicamente la dona con otra paleta.
python3 19_catalogo_graficas.py --grafica 10 --paleta oceano --mostrar

# Comparar barras, dona y mapa de calor con colores tierra.
python3 19_catalogo_graficas.py --grafica 4 10 16 --paleta tierra

# Crear las 24 gráficas con alta resolución en otra carpeta.
python3 19_catalogo_graficas.py --paleta oceano --dpi 300 --salida ./entrega
```

Para abrir las ventanas en WSL necesitas WSLg y un backend gráfico, por ejemplo
Tkinter (`sudo apt install python3-tk` en Ubuntu, para el Python utilizado).
Con `--mostrar` se abre una gráfica a la vez; ciérrala para continuar con la
siguiente. Puedes ampliar, desplazar y guardar desde la barra de Matplotlib.
`--sin-ventana` funciona sin pantalla y equivale al comportamiento predeterminado.
Si usas el entorno virtual, ejecuta con su Python o mediante `bash ejecutar.sh`.

## Paletas y significado

| Paleta | Categorías | Magnitudes ordenadas | Valores alrededor de cero |
| --- | --- | --- | --- |
| `original` | Azul, turquesa, naranja, morado, rojo y verde del ejemplo | `viridis` | `coolwarm` |
| `oceano` | Tonos profundos con acentos cálidos | `cividis` | `BrBG` |
| `tierra` | Marrón, oliva, ocre y acentos contrastantes | `YlOrBr` | `PuOr` |

Los colores categóricos identifican productos o grupos sin indicar un orden.
Los mapas secuenciales representan magnitudes, como cantidad de observaciones.
Los divergentes separan valores negativos y positivos; la correlación conserva
la escala de −1 a 1 y la superficie y las curvas de nivel comparten esa escala.
Las etiquetas y las formas de los marcadores complementan el color.

Los colores se editan en **`paletas.py`**, dentro de `PALETAS`. Cada `Paleta`
contiene seis colores hexadecimales y dos nombres de mapas de Matplotlib.
La fábrica `generar_datos()` de **`datos.py`** reúne las series compartidas.
Los datos propios de un solo ejemplo están dentro de su función en
**`graficas.py`**. Las semillas fijas hacen reproducibles los datos aleatorios.

Referencia: [guía oficial de mapas de color de Matplotlib](https://matplotlib.org/stable/users/explain/colors/colormaps.html).

## Catálogo

| N.º | Tipo | ¿Para qué utilizarlo? |
| --- | --- | --- |
| 1 | Líneas | Observar tendencias a través del tiempo. |
| 2 | Líneas múltiples | Comparar varias series a través del tiempo. |
| 3 | Barras verticales | Comparar categorías. |
| 4 | Barras horizontales | Categorías con nombres largos. |
| 5 | Barras agrupadas | Comparar dos o más grupos por categoría. |
| 6 | Barras apiladas | Mostrar componentes de un total. |
| 7 | Área | Destacar la magnitud mensual; no representa un acumulado. |
| 8 | Áreas apiladas | Comparar la composición de varias series. |
| 9 | Pastel | Mostrar proporciones de un total. |
| 10 | Dona | Proporciones con un espacio central para destacar un indicador o texto. |
| 11 | Histograma | Observar la distribución de una variable numérica. |
| 12 | Caja y bigotes | Comparar medianas, dispersión y posibles valores atípicos entre grupos. |
| 13 | Violín | Observar la forma de la distribución de cada grupo. |
| 14 | Dispersión | Investigar la relación entre dos variables. |
| 15 | Burbujas | Representar tres variables numéricas. x e y son posiciones; el tamaño representa una tercera variable. |
| 16 | Mapa de calor de correlación | Observar relaciones lineales entre variables. |
| 17 | Barras de error | Mostrar una estimación y su incertidumbre. |
| 18 | Escalones | Valores que cambian por periodos o etapas. |
| 19 | Stem o tallos | Visualizar valores discretos y sus magnitudes. |
| 20 | Hexbin | Visualizar concentraciones cuando hay muchos puntos y un scatter normal se vuelve difícil de leer. |
| 21 | Curvas de nivel | Representar una función con dos variables. |
| 22 | Superficie 3d | Estudiar funciones con dos variables independientes. |
| 23 | Coordenadas polares | Datos relacionados con ángulos, dirección o ciclos. |
| 24 | Función matemática con relleno | Resaltar máximos, mínimos o regiones de interés. |

## Ejercicios para practicar

1. Genera la gráfica **3** con las tres paletas. Compara la legibilidad de las
   etiquetas; los datos y el orden de productos deben permanecer iguales.
2. Cambia las cinco cantidades de `ventas_productos` en `datos.py`. Genera las
   gráficas **3 y 4**: comprueba que el ranking coloca arriba el producto con
   más ventas y que conserva su color de la gráfica vertical.
3. Cambia `participacion` por `(25, 25, 35, 15)` y genera **9 y 10**. Explica
   cómo `autopct` calcula el porcentaje de cada categoría sobre la suma total.
4. En `grafica_histograma`, cambia `bins=15` por `bins=8`. Explica por qué
   cambia la apariencia aunque se conservan las mismas 200 calificaciones.
5. Compara **14** (dispersión) con **20** (concentración): identifica cuándo
   el solapamiento de puntos hace útil agruparlos en hexágonos. Los conjuntos
   de datos de esos dos ejemplos son distintos y no deben compararse como
   si fueran las mismas observaciones.
6. Revisa **21 y 22**: ambas muestran `sin(sqrt(X²+Y²))` sobre la misma malla.
   Explica la diferencia entre verla en niveles y verla como superficie.

Entrega sugerida: tres gráficas PNG, la paleta elegida y una explicación breve
sobre el tipo de gráfica, sus ejes, unidades y significado de los colores.

## Cambios respecto al archivo compartido

- Cada gráfica es una función independiente; importar el módulo no genera archivos.
- Se puede ejecutar cualquiera sin haber ejecutado las anteriores, incluida la 3D.
- El ranking horizontal se ordena de mayor a menor y conserva el color del producto.
- Los porcentajes de la dona se colocan dentro del anillo; el texto usa blanco
  o negro según el contraste del fondo. El mapa de calor aplica el mismo criterio.
- Se indican las unidades en ventas, áreas, escalones y tallos.
- Las leyendas distinguen media y mediana en cajas y violines.
- Los márgenes de error del ejemplo 17 se identifican como **simulados**: no se
  afirman intervalos de confianza ni un nivel de significancia.
- El área del ejemplo 7 representa ventas mensuales, no una suma acumulada.
- El estilo se aplica en un contexto temporal; se cierran las figuras al terminar.
- Se validan números de gráfica, paleta y resolución, con destinos explícitos.

## Archivos y comprobación

| Archivo | Responsabilidad |
| --- | --- |
| `19_catalogo_graficas.py` | Argumentos, selección, exportación y apertura de ventanas |
| `graficas.py` | 24 funciones de dibujo y registro `CATALOGO` |
| `datos.py` | Series compartidas y datos reproducibles |
| `paletas.py` | Colores, estilo y contraste de etiquetas |
| `test_graficas.py` | Ranking, posición de porcentajes e independencia de los ejemplos |
| `ejecutar.sh` | Lanzador para WSL que elige el entorno virtual del proyecto |

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

La ejecución de referencia se comprobó con Matplotlib 3.10.8: 24 imágenes
con la paleta original y los ejemplos 4, 10, 16 y 22 con las otras dos paletas.
Las pruebas ejecutan las 24 funciones en orden inverso para comprobar que no
dependen de una gráfica creada previamente. La apertura de una ventana requiere
un escritorio disponible en el equipo donde se ejecute.
