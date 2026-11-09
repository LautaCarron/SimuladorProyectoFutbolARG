"""Tarjeta de palmarés de una liga o copa (la usan el Historial y las pestañas de copas)."""

from datos.logos import logo_img
from ui.vista.base import crest, esc


def tabla_ranking_html(titulo, logo, actual, base):
    """Tarjeta de palmarés de una liga o copa: posición, escudo, club y títulos. Los ganados
    en las temporadas simuladas se marcan aparte (+n).

    `actual` es el conteo total (histórico + simulado) y `base` el histórico cargado de datos/json/palmares_*.json."""
    lista = sorted(((n, t) for n, t in actual.items() if t > 0), key=lambda x: (-x[1], x[0]))
    total = sum(t for _, t in lista)
    filas, pos, previo = "", 0, None
    for k, (n, t) in enumerate(lista):
        if t != previo:
            pos, previo = k + 1, t
        extra = t - base.get(n, 0)
        clase = " oro" if pos == 1 else ""
        filas += (f'<div class="pal-f{clase}"><span class="pal-pos">{pos}</span>{crest(n, 22)}'
                  f'<span class="pal-nm" role="button" tabindex="0" data-club="{esc(n)}" title="{esc(n)}">{esc(n)}</span>'
                  + (f'<span class="pal-mas" title="Ganados en las temporadas simuladas">+{extra}</span>' if extra > 0 else "")
                  + f'<b class="pal-t">{t}</b></div>')
    if not filas:
        filas = '<div class="pal-vacio">Todavía no hay campeones.</div>'
    return (f'<div class="pal"><div class="pal-h">{logo_img(logo, 26)}<span class="pal-tit">{esc(titulo)}</span>'
            f'<span class="pal-tot">{total} títulos</span></div><div class="pal-lista">{filas}</div></div>')
