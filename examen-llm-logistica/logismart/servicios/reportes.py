"""Exportación del conjunto consultado; CSV protegido ante fórmulas de hojas de cálculo."""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape
from logismart.servicios.informes_accesos import periodo_informe


def filas_informe(informe):
    """Una fila por acceso, con motivos y columnas de premisas fáciles de analizar."""
    return [{
        'camion_id': r['camion_id'], 'placa': r['placa'], 'fecha_utc': r['fecha_utc'],
        'resultado': r['resultado'], 'motivos': ' | '.join(r['motivos']),
        'fuente': r['fuente'], 'version': r['version'], 'operador': r['operador'],
        **r['premisas'], **r['reglas'], 'explicacion': ' | '.join(r['explicacion']),
        'generado_en': informe['generado_en'], 'almacenamiento': informe['almacenamiento'],
        'filtro_resultado': informe['filtros']['resultado'],
        'desde_utc': informe['filtros']['desde'], 'hasta_utc': informe['filtros']['hasta'],
    } for r in informe['registros']]


def pdf_informe(informe, ruta):
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # Las fuentes vienen con ReportLab; se incrustan para conservar la apariencia.
    fuentes = Path(reportlab.__file__).parent / 'fonts'
    for nombre, archivo in [('InformeVera', 'Vera.ttf'), ('InformeVera-Bold', 'VeraBd.ttf')]:
        if nombre not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(nombre, str(fuentes / archivo)))
    estilos = getSampleStyleSheet()
    for nombre in ('Title', 'Heading2', 'Heading3'):
        estilos[nombre].fontName = 'InformeVera-Bold'
    cuerpo = ParagraphStyle('Informe', parent=estilos['BodyText'], fontSize=9, leading=13,
                            spaceAfter=5, fontName='InformeVera')
    detalle = ParagraphStyle('Evidencia', parent=cuerpo, fontSize=8, leading=11,
                             textColor=colors.HexColor('#475569'))
    contenido = [Paragraph('LOGISMART / INFORME DE ACCESOS', estilos['Heading3']),
                 Paragraph(escape(informe['titulo']), estilos['Title'])]

    def parrafo(texto, estilo=cuerpo):
        # Las fórmulas se escriben con palabras para evitar glifos ausentes en PDF.
        texto = str(texto).replace('∧', ' Y ').replace('∨', ' O ').replace('¬', 'NO ')
        for inicio in range(0, max(1, len(texto)), 1800):
            contenido.append(Paragraph(escape(texto[inicio:inicio + 1800]).replace('\n', '<br/>'), estilo))

    parrafo(periodo_informe(informe))
    parrafo(f"Generado: {informe['generado_en']} | Almacenamiento: {informe['almacenamiento']}", detalle)
    for clave in ('camion_id', 'placa'):
        if informe['filtros'][clave]:
            parrafo(f"Unidad consultada: {informe['filtros'][clave]}")
    parrafo(f"Total de accesos: {informe['total_accesos']} | Camiones únicos: {informe['camiones_unicos']}")
    contenido.append(Paragraph('Resumen de motivos', estilos['Heading2']))
    if not informe['registros']:
        parrafo('No hay registros que coincidan con los filtros del informe.')
    else:
        for motivo, n in informe['resumen_motivos'].items():
            parrafo(f'{motivo} Accesos: {n}.')
        parrafo('Un acceso puede tener varios motivos. Se conserva la decisión guardada.', detalle)
    for numero, r in enumerate(informe['registros'], 1):
        contenido.append(Paragraph(escape(f"{numero}. {r['camion_id']} / {r['placa']}"), estilos['Heading2']))
        parrafo(f"Fecha UTC: {r['fecha_utc']} | Resultado: {r['resultado']}")
        parrafo('Motivos: ' + ' '.join(r['motivos']))
        parrafo(f"Fuente: {r['fuente']} | Versión: {r['version']} | Operador: {r['operador']}", detalle)
        parrafo('Explicación guardada: ' + ' '.join(r['explicacion']), detalle)
        contenido.append(Spacer(1, 7))
    parrafo('Copia de los registros al generar el informe. Los cambios posteriores no alteran esta descarga. '
            'Los totales y motivos se obtienen de la base de datos, sin generación de texto del LLM.', detalle)

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont('InformeVera', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(42, 24, 'LogiSmart | Evidencia de accesos')
        canvas.drawRightString(A4[0] - 42, 24, f'Página {documento.page}')
        canvas.restoreState()

    SimpleDocTemplate(str(ruta), pagesize=A4, rightMargin=42, leftMargin=42,
                      topMargin=42, bottomMargin=42, title=informe['titulo'], author='LogiSmart').build(
                          contenido, onFirstPage=pie, onLaterPages=pie)


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
    es_informe = isinstance(datos, dict) and datos.get('tipo') == 'informe_accesos'
    if extension == '.json':
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    elif extension == '.csv':
        filas = filas_informe(datos) if es_informe else (datos if isinstance(datos, list) else [datos])
        columnas = list(dict.fromkeys(k for d in filas for k in d))
        if es_informe and not filas:
            columnas = ['camion_id', 'placa', 'fecha_utc', 'resultado', 'motivos', 'fuente', 'version']
        with ruta.open('w', encoding='utf-8-sig', newline='') as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=columnas)
            escritor.writeheader()
            escritor.writerows({k: valor_celda(v) for k, v in d.items()} for d in filas)
    elif extension == '.pdf':
        if es_informe:
            pdf_informe(datos, ruta)
            return str(ruta)
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
