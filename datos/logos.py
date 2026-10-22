"""Logos de cada liga y copa (embebidos como data URI: andan en la web y en la PC sin
descargar nada). Fuentes: ESPN (Liga Profesional, Copa Argentina y copas CONMEBOL) y TheSportsDB
(Primera Nacional, Federal A, Primera B, Primera C). El del Regional Amateur es un
distintivo propio del simulador."""

import os

from datos.imagenes import AQUI, sin_fondo

LOGOS = {
    "Primera División": "https://a.espncdn.com/i/leaguelogos/soccer/500/1.png",
    "Primera Nacional": "https://assets.football-logos.cc/logos/argentina/700x700/primera-nacional.b9471424.png",
    "Federal A": "https://api.promiedos.com.ar/images/league/fahi/1",
    "Federal B": "https://api.promiedos.com.ar/images/league/fahi/1",     # mismo escudo que el Federal A (cambialo si tenés el del B)
    "Primera B": "https://assets.football-logos.cc/logos/argentina/700x700/primera-b-metropolitana.bee87767.png",
    "Primera C": "https://api.promiedos.com.ar/images/league/ffjb/1",
    "Regional Amateur": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRseADn79McS3QsDbMFi-atkrcnARcxmyS1DMFyser3Og&s=10",
    "Copa Argentina": "https://api.promiedos.com.ar/images/league/gea/1",
    "Copa Libertadores": "https://api.promiedos.com.ar/images/league/bac/1",
    "Copa Sudamericana": "https://api.promiedos.com.ar/images/league/dij/1",
    "Recopa Sudamericana": "https://static.wikia.nocookie.net/football_ranking/images/f/f1/Conmebolrecopa.png/revision/latest?cb=20241105145225",
    "Mundial de Clubes": "https://api.promiedos.com.ar/images/league/fajg/1",
    "Promocional Amateur": "https://api.promiedos.com.ar/images/league/iage/1",
    "Supercopa Argentina": "https://static.wikia.nocookie.net/logopedia/images/4/4b/SupercopaAr.png/revision/latest?cb=20180728022302",

}     


# El logo del Regional Amateur viene con fondo blanco: se le saca una vez y queda en datos/logo_regional.png (ver
# imagenes.py; si ya tenés un PNG transparente, copialo con ese nombre y se usa tal cual).
LOGOS["Regional Amateur"] = sin_fondo(LOGOS["Regional Amateur"], os.path.join(AQUI, "logo_regional.png"))


def _clase(nombre):
    import unicodedata
    t = unicodedata.normalize("NFKD", nombre.lower())
    return "lg-" + "".join(c if c.isalnum() else "-" for c in t if not unicodedata.combining(c))


# Cada logo se define una sola vez en el CSS (antes iba embebido en cada lugar donde aparecía y
# la página pesaba cientos de KB de más)
LOGOS_CSS = ("<style>.lg{display:inline-block;flex:none;vertical-align:middle;background:center/contain "
             "no-repeat;}" + "".join(f".{_clase(n)}{{background-image:url({u});}}" for n, u in LOGOS.items())
             + "</style>")


def logo_img(nombre, size=22, clase="logo-comp"):
    """Logo de una liga o copa (o nada si no tiene)."""
    if nombre not in LOGOS:
        return ""
    return (f'<span class="lg {clase} {_clase(nombre)}" style="width:{size}px;height:{size}px" '
            f'role="img" aria-label="{nombre}" title="{nombre}"></span>')