"""Exportación del conjunto consultado; CSV protegido ante fórmulas de hojas de cálculo."""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape


def valor_celda(valor):
    if isinstance(valor, (dict, list)):
        valor = json.dumps(valor, ensure_ascii=False)
    if valor is None: return ''
    texto = str(valor)
    if texto.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
        texto = "'" + texto
    return texto


def exportar(datos, ruta, titulo='Reporte LogiSmart'):
    ruta = Path(ruta)
    extension = ruta.suffix.lower()
    if extension == '.json':
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    elif extension == '.csv':
        filas = datos if isinstance(datos, list) else [datos]
        columnas = list(dict.fromkeys(k for d in filas for k in d))
        with ruta.open('w', encoding='utf-8-sig', newline='') as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=columnas)
            escritor.writeheader()
            escritor.writerows({k: valor_celda(v) for k, v in d.items()} for d in filas)
    elif extension == '.pdf':
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        estilos = getSampleStyleSheet()
        estilo = ParagraphStyle('Datos', parent=estilos['BodyText'], fontSize=9, leading=12, wordWrap='CJK')
        contenido = [Paragraph(escape(titulo), estilos['Title']), Spacer(1, 12)]
        filas = datos if isinstance(datos, list) else [datos]
        if not filas: contenido.append(Paragraph('No hay registros en el período seleccionado.', estilo))
        for numero, registro in enumerate(filas, 1):
            contenido.append(Paragraph(f'Registro {numero}', estilos['Heading2']))
            for k, v in registro.items():
                texto = json.dumps(v, ensure_ascii=False, indent=2) if isinstance(v, (dict, list)) else str(v)
                # Divide valores grandes para que ReportLab pueda paginar sin perder contenido.
                for inicio in range(0, max(1, len(texto)), 1800):
                    etiqueta = f'<b>{escape(k)}:</b> ' if inicio == 0 else ''
                    contenido.append(Paragraph(etiqueta + escape(texto[inicio:inicio + 1800]).replace('\n', '<br/>'), estilo))
            contenido.append(Spacer(1, 10))
        SimpleDocTemplate(str(ruta), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42).build(contenido)
    else:
        raise ValueError('Elige un archivo .pdf, .csv o .json.')
    return str(ruta)
