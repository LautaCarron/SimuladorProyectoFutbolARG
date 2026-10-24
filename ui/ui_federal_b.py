"""Pestaña Ligas · Federal B (va en ui/ui_federal_b.py).

El Federal B se crea desde el Modo dios (ver ligas/federal_b.py) y tiene el mismo formato que el Federal A, así que
dibuja la misma pestaña (ui/ui_federal.py) con su propia liga. Mientras no exista no hay pestaña y esto no hace nada.
"""

from ui.ui_federal import render_liga_f


def render(ctx):
    SFB = ctx.S.get("fb")
    if SFB is None or ctx.pestanas.tab_fb is None:
        return
    render_liga_f(ctx, SFB, ctx.pestanas.tab_fb, ctx.progreso.terminada_fb, ctx.progreso.pct_fb, "fb")
