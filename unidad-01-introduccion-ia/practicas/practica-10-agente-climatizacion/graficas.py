"""Preparar y dibujar las lecturas consultadas, sin depender de una ventana."""

from datetime import datetime, timedelta, timezone
from math import isfinite

from matplotlib import dates as mdates


def fecha_utc(valor):
    try:
        fecha = datetime.fromisoformat(valor.replace('Z', '+00:00')) if isinstance(valor, str) else valor
        if not isinstance(fecha, datetime):
            return None
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def preparar_serie(registros, campo):
    """Ordenar una serie por fecha, manteniendo la identidad de cada registro."""
    serie = []
    for registro in registros:
        fecha = fecha_utc(registro.get('fecha'))
        valor = registro.get(campo)
        if fecha is None or isinstance(valor, bool):
            continue
        try:
            valor = float(valor)
        except (TypeError, ValueError, OverflowError):
            continue
        if not isfinite(valor) or (campo == 'humedad' and not 0 <= valor <= 100):
            continue
        serie.append((fecha, str(registro['_id']), valor))
    return sorted(serie, key=lambda punto: (punto[0], punto[1]))


def dibujar_graficas(figura, registros, mensaje_vacio='Sin registros para esta consulta'):
    """Redibujar temperatura y humedad usando solo los registros de la tabla."""
    figura.clear()
    ejes = figura.subplots(1, 2)
    resumen = [f'{len(registros)} registros en esta página']
    for eje, campo, titulo, color in zip(
        ejes, ('temperatura', 'humedad'), ('Temperatura (°C)', 'Humedad (%)'),
        ('#c85b32', '#167d98'),
    ):
        serie = preparar_serie(registros, campo)
        eje.set_title(titulo, fontsize=10, color='#183447')
        eje.set_xlabel('Fecha de registro (UTC)', fontsize=8)
        eje.tick_params(labelsize=8)
        eje.grid(True, alpha=0.2)
        if not serie:
            eje.text(0.5, 0.5, mensaje_vacio if not registros else 'Sin fechas y valores válidos',
                     ha='center', va='center', transform=eje.transAxes, fontsize=9, wrap=True)
            eje.set_xticks([])
            eje.set_yticks([])
        else:
            fechas = [punto[0] for punto in serie]
            valores = [punto[2] for punto in serie]
            eje.plot(fechas, valores, color=color, marker='o', markersize=4, linewidth=1.6)
            localizador = mdates.AutoDateLocator(minticks=3, maxticks=6, tz=timezone.utc)
            eje.xaxis.set_major_locator(localizador)
            eje.xaxis.set_major_formatter(mdates.ConciseDateFormatter(localizador, tz=timezone.utc))
            if min(fechas) == max(fechas):
                eje.set_xlim(fechas[0] - timedelta(minutes=1), fechas[0] + timedelta(minutes=1))
            if campo == 'humedad':
                eje.set_ylim(0, 100)
            promedio = sum(valor / len(valores) for valor in valores)
            resumen.append(f'{titulo}: promedio {promedio:.1f}')
        omitidos = len(registros) - len(serie)
        if omitidos:
            resumen.append(f'{campo}: {omitidos} registros sin datos válidos para graficar')
    return ' · '.join(resumen)
