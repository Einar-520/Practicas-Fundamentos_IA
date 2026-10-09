# Práctica 12: gráficas de ventas y paletas con Matplotlib

**Materia:** Extracción de Conocimiento en Bases de Datos. Se conserva la
numeración consecutiva del repositorio. Este programa es independiente de
LogiSmart y de las demás prácticas.

**Objetivo:** construir una gráfica de las ventas mensuales simuladas de EcoMart
en 2026, comparar cada observación con el promedio y destacar el máximo anual.

## Datos originales

| Mes | Ventas (miles de pesos, MXN) |
| --- | ---: |
| Ene | 85 |
| Feb | 90 |
| Mar | 96 |
| Abr | 105 |
| May | 120 |
| Jun | 135 |
| Jul | 150 |
| Ago | 148 |
| Sep | 160 |
| Oct | 172 |
| Nov | 181 |
| Dic | 195 |

Son datos simulados proporcionados en la consigna, no ventas reales ni un
pronóstico. **195 mil pesos equivalen a $195,000 MXN.**

## Mejoras del código

- Se comentaron los separadores y descripciones, se corrigieron las cadenas
  partidas, la indentación, el carácter `s` en `savefig` y `print("=" * 60)`.
- `crear_grafica()` utiliza `fig, ax` para distinguir la figura completa de
  los ejes donde se dibujan los datos. El estilo se limita a esta figura.
- Hay un encabezado, indicadores y un pie con fuente y autor. Cada mes conserva
  su valor visible; el máximo tiene una anotación con flecha.
- La leyenda se crea después de dibujar todos los elementos, de modo que incluye
  ventas, promedio y máximo. Las etiquetas no dependen de una altura fija de 185.
- El eje vertical parte de cero. La cuadrícula horizontal y el relleno suave
  ayudan a leer la evolución sin exagerar su escala.
- `validar_datos()` comprueba doce meses distintos, cantidades coincidentes,
  valores numéricos finitos y ventas no negativas.
- `main()` guarda una imagen PNG a 300 dpi antes de abrir la ventana. Importar
  el archivo para revisar sus funciones no crea imágenes ni abre ventanas.

## Ejecutar desde VS Code con WSL

Desde la raíz del proyecto, instala las dependencias en tu entorno:

```bash
cd ~/universidad/fundamentos-ia
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/requirements.txt
bash unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/ejecutar.sh
```

Si aún no existe `.venv`, créalo una sola vez con `python3 -m venv .venv`.
Selecciona ese intérprete en VS Code. La aplicación abre una **ventana de
Matplotlib**, con su barra para acercar, mover y guardar; no utiliza un servidor
web ni una dirección localhost. En WSL la ventana requiere soporte gráfico y
un backend interactivo instalado, por ejemplo Tkinter.

El PNG se genera en:

```text
practica-12-grafica-matplotlib/salidas/Grafica_Profesional_01.png
```

Puedes abrir ese archivo directamente en VS Code. Si solo necesitas exportar
la imagen, funciona también sin entorno gráfico:

```bash
bash unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/ejecutar.sh --sin-ventana
```

Para elegir otro destino:

```bash
bash unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/ejecutar.sh --sin-ventana --salida "$HOME/ventas_ecomart.png"
```

Volver a ejecutar el programa actualiza el PNG del destino elegido. Los archivos
de `salidas/` se excluyen de Git porque pueden regenerarse con el programa.

## Resultados y explicación

| Indicador | Cálculo | Resultado |
| --- | --- | ---: |
| Total anual | `np.sum(ventas)` | 1,637 mil pesos |
| Promedio mensual | `np.mean(ventas)` | 136.42 mil pesos |
| Máximo | `np.argmax(ventas)` | Diciembre: 195 mil pesos |
| Cambio de enero a diciembre | `(195 / 85 - 1) * 100` | +129.41 % |

El porcentaje compara el último mes con el primero; no es un crecimiento
interanual, ya que no se proporcionaron ventas de 2025. La serie presenta una
leve disminución entre julio y agosto (150 a 148). El resto de los intervalos
mensuales aumenta. Si enero vale cero, el porcentaje se muestra como **N/D**.
Si hay empate en el máximo, se destaca su primera aparición.

Para cambiar datos en futuros ejercicios, edita `MESES`, `VENTAS` y `ANIO` al
inicio de `12_grafica_ventas.py`; los indicadores se recalculan.

## Segundo ejercicio: quince paletas de colores

El archivo `graficas3.py` de `busquedas.rar` se desarrolló como
`12_paletas_colores.py`, un programa independiente de la gráfica de ventas.
Conserva las quince paletas: deep, muted, bright, pastel, dark, colorblind,
Blues, Greens, Reds, Purples, viridis, plasma, inferno, magma y cividis.

Las mejoras son una distribución de **5 filas por 3 columnas**, etiquetas de
valores y una escala común. Los diez números simulados son iguales en todos
los paneles y se pueden repetir mediante una semilla. La semilla predeterminada
es 42; los valores están entre 10 y 99, como en el ejercicio original.

```bash
bash unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/ejecutar.sh --paletas
```

Para exportar sin ventana y repetir otro conjunto de datos:

```bash
bash unidad-01-introduccion-ia/practicas/practica-12-grafica-matplotlib/ejecutar.sh --paletas --sin-ventana --semilla 7
```

La galería se guarda como `salidas/Capitulo03_Paletas_Profesionales.png` a
300 dpi. También admite `--salida otra_ruta.png`. `--paletas` debe ser el primer
argumento del lanzador.

Las paletas categóricas distinguen observaciones; las secuenciales ilustran una
progresión de tonos. En esta comparación el color se asigna **por posición**,
igual que en el ejemplo: el valor lo representa la altura, no el color. En un
mapa de calor sí convendría asignar los colores secuenciales al valor numérico.

## Correspondencia con el material del profesor

| Original | Versión desarrollada |
| --- | --- |
| Código de EcoMart / `graficas1.py` | `12_grafica_ventas.py` |
| `graficas3.py` | `12_paletas_colores.py` |

Los otros dos archivos de `busquedas.rar`, de BFS y DFS, se desarrollan en la
[práctica 13](../practica-13-busquedas-bfs-dfs/README.md).

## Documentación utilizada

- [Figura y ejes con subplots](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html).
- [Elección de paletas en Seaborn](https://seaborn.pydata.org/tutorial/color_palettes.html).
- [Exportación con Figure.savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.savefig.html).
