"""Paletas categóricas y mapas de color para magnitudes y correlaciones."""
from dataclasses import dataclass
from matplotlib.colors import to_rgb


@dataclass(frozen=True)
class Paleta:
    principal: str
    secundario: str
    acento: str
    extra: str
    alerta: str
    positivo: str
    secuencial: str
    divergente: str

    @property
    def categorias(self):
        return (self.principal, self.secundario, self.acento,
                self.extra, self.alerta, self.positivo)


PALETAS = {
    "original": Paleta("#2563EB", "#0D9488", "#F59E0B", "#7C3AED", "#DC2626", "#16A34A", "viridis", "coolwarm"),
    "oceano": Paleta("#075985", "#0F766E", "#C2410C", "#6D28D9", "#BE123C", "#3F6212", "cividis", "BrBG"),
    "tierra": Paleta("#92400E", "#3F6212", "#CA8A04", "#7E22CE", "#9F1239", "#0F766E", "YlOrBr", "PuOr"),
}


def estilo(paleta: Paleta) -> dict:
    """Se aplica con rc_context para no cambiar otros programas al importar."""
    from cycler import cycler
    return {
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": "#CBD5E1", "axes.labelcolor": "#1E293B",
        "text.color": "#1E293B", "xtick.color": "#1E293B", "ytick.color": "#1E293B",
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.labelsize": 10,
        "font.family": "DejaVu Sans", "font.size": 10,
        "grid.color": "#E2E8F0", "grid.linestyle": "--", "grid.alpha": 0.8,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "axes.prop_cycle": cycler(color=paleta.categorias),
    }


def color_texto(color) -> str:
    """Elige blanco o negro según el mayor contraste con el fondo sRGB."""
    canales = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
               for c in to_rgb(color)]
    luminancia = sum(c * peso for c, peso in zip(canales, (.2126, .7152, .0722)))
    return "#FFFFFF" if 1.05 / (luminancia + .05) > (luminancia + .05) / .05 else "#111111"
