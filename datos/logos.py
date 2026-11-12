"""Logos de cada liga y copa (embebidos como data URI: andan en la web y en la PC sin
descargar nada). Fuentes: ESPN (Liga Profesional, Copa Argentina y copas CONMEBOL) y TheSportsDB
(Primera Nacional, Federal A, Primera B, Primera C). El del Regional Amateur es un
distintivo propio del simulador."""

from datos.cargador import cargar

LOGOS = cargar("logos")      # datos/json/logos.json


def _clase(nombre):
    import unicodedata
    t = unicodedata.normalize("NFKD", nombre.lower())
    return "lg-" + "".join(c if c.isalnum() else "-" for c in t if not unicodedata.combining(c))


# Cada logo se define una sola vez en el CSS (antes iba embebido en cada lugar donde aparecía y
# la página pesaba cientos de KB de más)
LOGOS_CSS = ("<style>.lg{display:inline-block;flex:none;vertical-align:middle;background:center/contain "
             "no-repeat;}" + "".join(f".{_clase(n)}{{background-image:url({u});}}" for n, u in LOGOS.items() if u)
             + "</style>")


def logo_img(nombre, size=22, clase="logo-comp"):
    """Logo de una liga o copa (o nada si no tiene)."""
    if not LOGOS.get(nombre):                    # sin logo (o con la URL todavía vacía en logos.json)
        return ""
    return (f'<span class="lg {clase} {_clase(nombre)}" style="width:{size}px;height:{size}px" '
            f'role="img" aria-label="{nombre}" title="{nombre}"></span>')