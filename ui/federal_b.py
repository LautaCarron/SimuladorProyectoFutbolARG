"""Pestaña Ligas · Federal B (va en ui/federal_b.py).

El Federal B se crea desde el Modo dios (ver ligas/federal_b.py) y tiene el mismo formato que el Federal A, así que
dibuja la misma pestaña (ui/federal.py) con su propia liga. Mientras no exista no hay pestaña y esto no hace nada.
"""

from ui.federal import render_liga_f


def render(ctx):
    SFB = ctx.S.get("fb")
    if SFB is None or ctx.tab_fb is None:
        return
    render_liga_f(ctx, SFB, ctx.tab_fb, ctx.terminada_fb, ctx.pct_fb, "fb")
