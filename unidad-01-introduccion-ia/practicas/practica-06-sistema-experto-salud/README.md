# Práctica 6: Sistema experto de salud

Ejercicio académico de tres síntomas. El resultado es orientativo y no sustituye una valoración médica.

## Ejecutar en WSL

Desde la raíz de fundamentos-ia, prepara el entorno una vez:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r unidad-01-introduccion-ia/practicas/practica-06-sistema-experto-salud/requirements.txt
```

Después inicia esta práctica:

```bash
bash unidad-01-introduccion-ia/practicas/practica-06-sistema-experto-salud/ejecutar.sh
```

Abre http://localhost:5106 en tu navegador. Mantén la terminal abierta;
Ctrl+C detiene el servidor. También puedes ejecutar `bash iniciar_practica_web.sh 6`
desde la raíz del repositorio. Requiere Python 3.9 o superior y Flask.

## Interfaz y archivos

| Archivo | Función |
| --- | --- |
| `06_sistema_experto_salud.py` | Reglas de la práctica, validación y servidor Flask. |
| `templates/index.html` | Página, campos y botones. |
| `static/estilos.css` | Diseño adaptable y estilos de los resultados. |
| `static/app.js` | Envía el formulario a Python y presenta la respuesta. |
| `requirements.txt` | Dependencia necesaria para ejecutar esta práctica. |
| `ejecutar.sh` | Usa el Python del entorno virtual del proyecto. |

Los resultados aparecen en la página. Las reglas del programa de consola se
conservan. Python rechaza datos vacíos, números no finitos y opciones inválidas.
Las respuestas Sí/No se seleccionan en el formulario. En números decimales usa
punto. El botón Limpiar, cuando aparece, reinicia el formulario y el resultado.

Cada práctica es independiente y tiene sus propios archivos y su propia sesión.
Puedes abrir varias a la vez usando terminales separadas. Para ejecutar únicamente
este programa fuera del repositorio, instala su requirements.txt en tu entorno y
ejecuta `06_sistema_experto_salud.py` con Python desde cualquier directorio.

El formulario se comunica con Python mediante `POST /evaluar` y recibe JSON.
JavaScript muestra el texto como texto, conserva los datos cuando hay errores y
avisa cuando el resultado pertenece a un formulario que ya modificaste.
Las prácticas 1 a 7 no usan MongoDB ni guardan los formularios en una base de datos.
