"""Vista: estilos, escudos, tablas, fixtures, fichas de club y cuadros del reducido.

Todo lo que dibuja algo en pantalla. Las funciones leen el estado de la sesión con
_estado(), así que funcionan bien aunque haya varios usuarios a la vez.
"""

import hashlib
import html
import numpy as np
import pandas as pd
import re
import unicodedata
import streamlit as st

from datos import (
    ESCUDOS,
    F_GRUPOS_NOMBRES,
)
from torneos import (
    B_F1,
    B_F2,
    B_ZONAS2,
    FECHAS_F1,
    ZONAS,
    ZONA_TAM,
    destino,
    rotulo_b,
    rotulo_f,
    rotulo_p,
)


def _estado():
    """Estado de la sesión actual: Primera, B Nacional, Federal A, Primera B y Primera C."""
    S = st.session_state.S
    return S, S["b"], S["f"], S["pb"], S["pc"]



COLOR_ORO = "rgba(255, 215, 0, 0.40)"
COLORES_DESTINO = {
    "Libertadores": "rgba(52, 152, 219, 0.28)",
    "Fase previa Libertadores": "rgba(133, 193, 233, 0.30)",
    "Sudamericana": "rgba(243, 156, 18, 0.28)",
    "Promoción": "rgba(155, 89, 182, 0.30)",
    "Desciende": "rgba(231, 76, 60, 0.25)",
}
COLORES_ZONA = ["rgba(46, 204, 113, 0.22)", "rgba(241, 196, 15, 0.22)", "rgba(231, 76, 60, 0.20)"]
COLORES_B = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 204, 113, 0.30)",
    "Cuartos del reducido": "rgba(52, 152, 219, 0.28)",
    "Octavos del reducido": "rgba(133, 193, 233, 0.30)",
    "Desciende": "rgba(231, 76, 60, 0.25)",
    "→ Zona Campeonato": COLORES_ZONA[0],
    "→ Zona Intermedia": COLORES_ZONA[1],
    "→ Zona Descenso": COLORES_ZONA[2],
}
COLORES_F = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 204, 113, 0.30)",
    "Reducido": "rgba(52, 152, 219, 0.28)",
    "→ Fase 2": "rgba(46, 204, 113, 0.22)",
    "→ Zona Campeonato": "rgba(46, 204, 113, 0.22)",
}


# ----------------------------------------------------------------------------
# PRESENTACIÓN (estilos, escudos, tarjetas)
# ----------------------------------------------------------------------------
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Barlow+Condensed:wght@600;700;800&display=swap');
:root{--cel:#74ACDF;--cel2:#4a90d0;--navy:#0b1d3a;--gold:#d4a017;--line:rgba(128,128,128,.2);--soft:rgba(128,128,128,.055);--soft2:rgba(128,128,128,.1);--acc:#2f7fd0;--pen:#7c3aed;--win:#16a34a;--lose:#dc2626;}
html,body,.stApp,.stMarkdown,button,input,textarea,[data-testid="stMetricValue"]{font-family:'Inter',system-ui,-apple-system,sans-serif !important;}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1440px;}
[data-testid="stSidebar"] h2{font-size:1.05rem;}
/* ---------- cabecera ---------- */
.hero{position:relative;overflow:hidden;background:radial-gradient(circle at 88% 20%,rgba(116,172,223,.35),transparent 42%),linear-gradient(120deg,#07142b 0%,#0b1d3a 45%,#123a6b 100%);color:#fff;border-radius:18px;padding:24px 28px 20px;margin-bottom:12px;box-shadow:0 14px 34px rgba(7,20,43,.28);}
.hero::before{content:"";position:absolute;left:0;right:0;top:0;height:6px;background:linear-gradient(90deg,var(--cel) 0 33.3%,#fff 33.3% 66.6%,var(--cel) 66.6%);}
.hero .sol{position:absolute;right:26px;top:14px;font-size:64px;opacity:.14;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;flex-wrap:wrap;}
.hero-k{text-transform:uppercase;letter-spacing:.18em;font-size:.68rem;font-weight:700;color:var(--cel);}
.hero h1{color:#fff !important;font-family:'Barlow Condensed',sans-serif !important;font-size:2.35rem;font-weight:800;margin:2px 0 0;padding:0;letter-spacing:.01em;line-height:1.05;text-transform:uppercase;}
.hero p{margin:4px 0 0;opacity:.72;font-size:.9rem;}
.hero-stats{display:flex;gap:10px;flex-wrap:wrap;}
.hs{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:8px 14px;min-width:128px;}
.hs span{display:block;font-size:.64rem;opacity:.7;text-transform:uppercase;letter-spacing:.09em;font-weight:600;}
.hs b{font-family:'Barlow Condensed',sans-serif;font-size:1.35rem;font-weight:700;letter-spacing:.02em;}
.hs .bar{height:4px;border-radius:3px;background:rgba(255,255,255,.15);margin-top:4px;overflow:hidden;}
.hs .bar i{display:block;height:100%;background:var(--cel);}
/* ---------- navegación ---------- */
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{font-weight:700;padding:10px 16px;border-radius:10px 10px 0 0;}
.stTabs [data-baseweb="tab"] p{font-size:.95rem;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--cel2);height:3px;}
.stTabs .stTabs [data-baseweb="tab"] p{font-size:.86rem;}
.stTabs .stTabs [data-baseweb="tab"]{padding:8px 12px;}
/* ---------- botones / widgets ---------- */
.stButton>button,[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"]{border-radius:10px;font-weight:600;}
[data-testid="stExpander"] details{border-radius:12px;border:1px solid var(--line);background:var(--soft);}
[data-testid="stExpander"] summary{font-weight:700;}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;border:1px solid var(--line);}
/* ---------- barra de estado de cada liga ---------- */
.status{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:6px 0 10px;}
.stc{border:1px solid var(--line);background:var(--soft);border-radius:12px;padding:10px 14px;}
.stc span{display:block;font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.65;}
.stc b{font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;font-weight:700;}
.stc .bar{height:5px;border-radius:3px;background:var(--soft2);margin-top:6px;overflow:hidden;}
.stc .bar i{display:block;height:100%;background:linear-gradient(90deg,var(--cel2),var(--cel));}
.aviso{border-left:4px solid var(--cel2);background:color-mix(in srgb,var(--cel) 10%,transparent);border-radius:8px;padding:9px 14px;font-size:.88rem;margin:4px 0 10px;}
/* ---------- títulos de sección ---------- */
.sec{display:flex;align-items:baseline;gap:10px;margin:8px 0 10px;flex-wrap:wrap;}
.sec .tt{font-family:'Barlow Condensed',sans-serif;font-size:1.45rem;font-weight:700;letter-spacing:.01em;text-transform:uppercase;border-left:5px solid var(--c,#2f7fd0);padding-left:10px;line-height:1.1;}
.sec .sub{font-size:.82rem;opacity:.62;}
.chip{display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:999px;font-size:.7rem;font-weight:700;letter-spacing:.03em;background:color-mix(in srgb,var(--c) 14%,transparent);color:var(--c);border:1px solid color-mix(in srgb,var(--c) 38%,transparent);white-space:nowrap;}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.76rem;opacity:.85;margin:8px 2px 4px;}
.legend span{display:inline-flex;align-items:center;gap:6px;}
.legend i{width:12px;height:12px;border-radius:3px;display:inline-block;}
/* ---------- escudos ---------- */
.crest-img{object-fit:contain;flex:none;vertical-align:middle;filter:drop-shadow(0 1px 1px rgba(0,0,0,.18));}
.crest{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-weight:800;border-radius:7px 7px 50% 50%/7px 7px 62% 62%;flex:none;letter-spacing:-.03em;line-height:1;}
/* ---------- partidos ---------- */
.score{display:flex;justify-content:center;align-items:center;gap:6px;font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:1.25rem;font-variant-numeric:tabular-nums;white-space:nowrap;}
.score .n{background:var(--soft2);border-radius:7px;min-width:28px;text-align:center;padding:0 7px;line-height:1.5;}
.score .n.w{background:color-mix(in srgb,var(--win) 20%,transparent);color:color-mix(in srgb,var(--win) 80%,currentColor);}
.score small{font-weight:700;font-size:.92rem;color:var(--pen);}
.score .sep{opacity:.4;}
.score .vs{font-family:'Inter',sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.08em;opacity:.55;border:1px dashed var(--line);border-radius:6px;padding:2px 8px;}
details.tanda{margin:0 0 8px;border:1px dashed color-mix(in srgb,var(--pen) 45%,transparent);border-radius:10px;padding:5px 10px;background:color-mix(in srgb,var(--pen) 6%,transparent);font-size:.8rem;}
details.tanda summary{cursor:pointer;font-weight:700;color:var(--pen);}
.trow{display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap;}
.trow .tn{min-width:120px;font-weight:600;}
.trow .tt{font-weight:800;min-width:16px;}
.pk{display:inline-flex;width:19px;height:19px;border-radius:50%;align-items:center;justify-content:center;font-size:.66rem;font-weight:800;color:#fff;margin-right:3px;}
.pk.ok{background:var(--win);}.pk.no{background:var(--lose);}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;align-items:center;background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:6px 8px;margin-bottom:2px;transition:border-color .15s;}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]:hover{border-color:color-mix(in srgb,var(--cel2) 60%,transparent);}
[class*="st-key-fx"] [data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:5 1 0 !important;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(2){flex:3.6 1 0 !important;}
[class*="st-key-fx"] [data-testid="stVerticalBlock"]{gap:.45rem;}
[class*="st-key-fx"] button{border:none !important;background:transparent !important;box-shadow:none !important;padding:2px 4px !important;min-height:0 !important;}
[class*="st-key-fx"] button p{font-weight:600;font-size:.88rem;line-height:1.2;}
[class*="st-key-fx"] button:hover p{color:var(--cel2);text-decoration:underline;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(1) button{justify-content:flex-end;text-align:right;width:100%;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(3) button{justify-content:flex-start;text-align:left;width:100%;}
.fx-head{display:flex;align-items:center;gap:8px;margin:2px 0 8px;flex-wrap:wrap;}
.mrow{border:1px solid var(--line);border-radius:12px;padding:8px 12px;margin-bottom:8px;background:var(--soft);}
.mrow .meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:.74rem;margin-bottom:5px;}
.mline{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;}
.side{display:flex;align-items:center;gap:8px;font-weight:600;font-size:.9rem;}
.side.l{justify-content:flex-end;text-align:right;}
.side.w{font-weight:800;}
/* ---------- tarjetas ---------- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:4px 0 14px;}
.card{border:1px solid var(--line);background:var(--soft);border-radius:14px;padding:13px 16px;border-top:3px solid var(--c,#2f7fd0);}
.card .k{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.68;}
.card .v{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.98rem;margin-top:8px;flex-wrap:wrap;}
.card .v.big{font-family:'Barlow Condensed',sans-serif;font-size:1.7rem;}
.card .s{font-size:.78rem;opacity:.7;margin-top:5px;}
.movlist{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 12px;}
.mv{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:3px 11px 3px 5px;font-size:.8rem;font-weight:600;background:var(--soft);}
.mv .d{font-weight:800;}
.up{color:var(--win);}.down{color:var(--lose);}
.mlab{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;opacity:.72;margin:6px 0 4px;}
.tlist{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 8px;}
.tl{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:10px;padding:5px 10px 5px 6px;font-weight:600;font-size:.86rem;background:var(--soft);}
.tl small{opacity:.6;font-weight:700;}
.champ{border-radius:14px;padding:18px;text-align:center;background:linear-gradient(135deg,rgba(212,160,23,.25),rgba(212,160,23,.05));border:1px solid rgba(212,160,23,.55);}
.champ .t{font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#b7860b;}
.champ .nm{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:1.5rem;margin-top:8px;text-transform:uppercase;}
.champ .s{font-size:.76rem;opacity:.75;margin-top:2px;}
/* ---------- cuadro del reducido ---------- */
.bracket{display:grid;grid-template-columns:repeat(5,minmax(205px,1fr));gap:28px;overflow-x:auto;padding:4px 2px 14px;}
.round{display:flex;flex-direction:column;}
.round-h{text-align:center;margin-bottom:10px;}
.round-b{display:flex;flex-direction:column;justify-content:space-around;gap:14px;flex:1;}
.bm{position:relative;border:1px solid var(--line);border-radius:12px;background:var(--soft);}
.round:not(.last) .bm::after{content:"";position:absolute;right:-29px;top:50%;width:28px;border-top:2px solid var(--line);}
.bt{display:flex;align-items:center;gap:7px;padding:7px 10px;font-size:.84rem;}
.bt+.bt{border-top:1px solid var(--line);}
.bt .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;}
.bt .g{font-family:'Barlow Condensed',sans-serif;font-size:1.05rem;font-weight:700;min-width:14px;text-align:right;}
.bt .p{font-size:.74rem;font-weight:800;color:var(--pen);}
.bt .lv{font-size:.58rem;font-weight:800;border:1px solid var(--line);border-radius:4px;padding:0 4px;opacity:.7;}
.bt.win{background:color-mix(in srgb,var(--win) 12%,transparent);box-shadow:inset 3px 0 0 var(--win);}
.bt.win .nm{font-weight:800;}
.bt.lose{opacity:.5;}
.bt.tbd .nm{opacity:.5;font-style:italic;font-weight:500;}
.bfoot{font-size:.7rem;padding:4px 10px 6px;border-top:1px dashed var(--line);}
.bfoot b{color:var(--win);}
.bm details.tanda{margin:0 8px 8px;font-size:.72rem;}
.bm .trow .tn{min-width:0;}
.promo{margin-top:14px;}
/* ---------- ficha de club ---------- */
.team-head{display:flex;align-items:center;gap:16px;margin-bottom:8px;flex-wrap:wrap;}
.team-head .tn{font-family:'Barlow Condensed',sans-serif;font-size:1.9rem;font-weight:800;text-transform:uppercase;line-height:1;}
.rec{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px;}
.rec div{border:1px solid var(--line);background:var(--soft);border-radius:10px;padding:5px 12px;text-align:center;min-width:54px;}
.rec b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;}
.rec span{font-size:.64rem;text-transform:uppercase;letter-spacing:.07em;opacity:.7;font-weight:600;}
.form{display:inline-flex;gap:4px;vertical-align:middle;margin-top:3px;}
.fm{width:22px;height:22px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:.68rem;font-weight:800;}
.fm.G{background:var(--win);}.fm.E{background:#64748b;}.fm.P{background:var(--lose);}
.next{border:1px solid var(--line);border-left:4px solid var(--cel2);border-radius:10px;padding:8px 12px;background:var(--soft);font-size:.86rem;margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:8px;}
.ct{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;border:1px solid var(--line);background:var(--soft);border-radius:14px;padding:14px 8px;font-weight:600;font-size:.84rem;}
.catgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}
</style>"""

COLOR_COMP = [
    ("Campeonato", "#16a34a"), ("Intermedia", "#d97706"), ("Descenso", "#dc2626"),
    ("Zona A", "#4f46e5"), ("Zona B", "#0891b2"), ("Octavos", "#2563eb"),
    ("Cuartos", "#1d4ed8"), ("Semifinal", "#7c3aed"), ("Final", "#b7860b"),
    ("Promoción", "#9333ea"), ("Fase 1", "#475569"), ("Federal A", "#b45309"),
    ("Primera B", "#0369a1"),
    ("Primera División", "#1e5aa8"), ("Primera Nacional", "#0f766e"),
]
esc = html.escape


def color_de(txt):
    for k, c in COLOR_COMP:
        if k in txt:
            return c
    return "#64748b"


def chip(txt, color=None):
    return f'<span class="chip" style="--c:{color or color_de(txt)}">{esc(txt)}</span>'


def seccion(titulo, sub="", color="#2f7fd0"):
    sub = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    st.markdown(f'<div class="sec" style="--c:{color}"><span class="tt">{titulo}</span>{sub}</div>',
                unsafe_allow_html=True)


def aviso(txt):
    st.markdown(f'<div class="aviso">{txt}</div>', unsafe_allow_html=True)


def leyenda(items):
    st.markdown('<div class="legend">' + "".join(
        f'<span><i style="background:{c}"></i>{esc(t)}</span>' for t, c in items) + "</div>",
        unsafe_allow_html=True)


def iniciales(nombre):
    base = nombre.split("(")[0].replace("'", "").strip()
    w = base.split()
    return (w[0][0] + w[1][0]).upper() if len(w) >= 2 else base[:3].upper()


def crest(nombre, size=26):
    """Escudo real del club (o un distintivo con sus iniciales si no hay imagen)."""
    url = ESCUDOS.get(nombre)
    if url:
        return (f'<img class="crest-img" src="{esc(url)}" width="{size}" height="{size}" '
                f'alt="" loading="lazy" title="{esc(nombre)}">')
    h = int(hashlib.md5(nombre.encode("utf-8")).hexdigest()[:6], 16)
    return (f'<span class="crest" style="width:{size}px;height:{size + 2}px;'
            f'font-size:{max(8, round(size * 0.36))}px;background:linear-gradient(160deg,'
            f'hsl({h % 360},62%,44%),hsl({(h // 360 + 25) % 360},58%,28%))">'
            f'{esc(iniciales(nombre))}</span>')


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_STOP = {"fecha", "vs", "contra", "de", "del", "la", "el", "y", "-", "fch", "f"}


def coincide(consulta, texto, fecha, marcadores):
    """Cada palabra de la búsqueda tiene que aparecer. Un número = número de fecha;
    algo como 2-1 = resultado (en cualquier orden)."""
    for t in norm(consulta).replace("–", "-").split():
        if t in _STOP:
            continue
        if t.isdigit():
            if int(t) != fecha:
                return False
        elif re.fullmatch(r"\d+-\d+", t):
            if t not in marcadores:
                return False
        elif t not in texto:
            return False
    return True


def todos_los_partidos():
    S, SB, SF, SPB, SPC = _estado()
    return S["log"] + S["b"]["log"] + S["f"]["log"] + S["pb"]["log"] + S["pc"]["log"]


def categoria_de(nombre):
    S, SB, SF, SPB, SPC = _estado()
    if nombre in S["nombres"]:
        return "Primera División"
    if nombre in S["b"]["nombres"]:
        return "Primera Nacional"
    if nombre in S["federal"]:
        return "Federal A"
    if nombre in S["primera_b"]:
        return "Primera B"
    if nombre in S["primera_c"]:
        return "Primera C"
    return ""


def marcador_html(p, crests=False):
    cl = crest(p["local"], 22) if crests else ""
    cv = crest(p["visita"], 22) if crests else ""
    if p["gl"] is None:
        return f'<div class="score">{cl}<span class="vs">VS</span>{cv}</div>'
    wl = ' w' if p["gana"] == p["local"] else ''
    wv = ' w' if p["gana"] == p["visita"] else ''
    pl = pv = ""
    if p["pen"]:
        pl, pv = f"<small>({p['pen'][0]})</small>", f"<small>({p['pen'][1]})</small>"
    return (f'<div class="score">{cl}<span class="n{wl}">{p["gl"]}</span>{pl}<span class="sep">–</span>'
            f'{pv}<span class="n{wv}">{p["gv"]}</span>{cv}</div>')


def tanda_html(p, abierto=False):
    if not p.get("tanda"):
        return ""
    filas = ""
    for nombre, serie, total in ((p["local"], p["tanda"][0], p["pen"][0]),
                                 (p["visita"], p["tanda"][1], p["pen"][1])):
        dots = "".join('<span class="pk ok">✓</span>' if x else '<span class="pk no">✗</span>'
                       for x in serie)
        filas += (f'<div class="trow">{crest(nombre, 18)}<span class="tn">{esc(nombre)}:</span>'
                  f'<span class="tt">{total}</span><span>{dots}</span></div>')
    return (f'<details class="tanda"{" open" if abierto else ""}><summary>🥅 Penales · '
            f'{esc(p["local"])} {p["pen"][0]} – {p["pen"][1]} {esc(p["visita"])}</summary>'
            f'{filas}</details>')


def fila_partido_html(p, abierto=False):
    """Partido en formato tarjeta."""
    wl = " w" if p["gana"] == p["local"] else ""
    wv = " w" if p["gana"] == p["visita"] else ""
    meta = (chip(p["liga"]) + (chip(p["comp"]) if p["comp"] != p["liga"] else "")
            + f'<span style="opacity:.7;font-weight:600">{esc(p["rotulo"])}</span>'
            + ('<span style="opacity:.6">· cancha neutral</span>' if p["neutral"] else ""))
    return (f'<div class="mrow"><div class="meta">{meta}</div><div class="mline">'
            f'<div class="side l{wl}">{esc(p["local"])} {crest(p["local"], 26)}</div>'
            f'{marcador_html(p)}'
            f'<div class="side{wv}">{crest(p["visita"], 26)} {esc(p["visita"])}</div></div>'
            f'{tanda_html(p, abierto)}</div>')


def lista_equipos_html(items):
    """items: lista de (nombre, detalle)."""
    if not items:
        return '<div style="opacity:.6">Por definir</div>'
    return '<div class="tlist">' + "".join(
        f'<span class="tl">{crest(n, 26)}{esc(n)}{f" <small>{esc(d)}</small>" if d else ""}</span>'
        for n, d in items) + "</div>"


def resultado_para(p, nombre):
    local = p["local"] == nombre
    gf, gc = (p["gl"], p["gv"]) if local else (p["gv"], p["gl"])
    letra = "G" if gf > gc else "P" if gf < gc else "E"
    return local, gf, gc, letra


# ---- Calendario: partidos jugados y por jugar -------------------------------
def pendiente(liga, n, rotulo, comp, local, visita):
    return {"liga": liga, "fecha": n, "rotulo": rotulo, "comp": comp, "local": local,
            "visita": visita, "gl": None, "gv": None, "gana": None, "tanda": None,
            "pen": None, "neutral": False}


def fechas_conocidas_p():
    S, SB, SF, SPB, SPC = _estado()
    return len(S["fechas"])


def partidos_fecha_p(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= S["fecha"]:
        return [p for p in S["log"] if p["fecha"] == n]
    nom = S["nombres"]
    return [pendiente("Primera División", n, rotulo_p(n),
                      "Fase 1" if n <= FECHAS_F1 else f"Zona {ZONAS[S['zona_de'][x]]}",
                      nom[x], nom[y]) for x, y in S["fechas"][n - 1]]


def fechas_conocidas_b():
    S, SB, SF, SPB, SPC = _estado()
    return max(SB["fecha"], B_F1 if SB["fechas2"] is None else B_F1 + B_F2)


def partidos_fecha_b(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SB["fecha"]:
        return [p for p in SB["log"] if p["fecha"] == n]
    nom = SB["nombres"]
    if n <= B_F1:
        return [pendiente("Primera Nacional", n, rotulo_b(n), f"Zona {'AB'[SB['zona_de'][x]]}",
                          nom[x], nom[y]) for x, y in SB["fechas"][n - 1]]
    return [pendiente("Primera Nacional", n, rotulo_b(n),
                      f"Zona {B_ZONAS2[SB['zona2_de'][x]]}", nom[x], nom[y])
            for x, y in SB["fechas2"][n - 1 - B_F1]]


def fechas_conocidas_f():
    S, SB, SF, SPB, SPC = _estado()
    return max(SF["fecha"], SF["f1_rondas"] if SF["fechas2"] is None else SF["f1_rondas"] + SF.get("f2_rondas", 0))

def partidos_fecha_f(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SF["fecha"]:
        return [p for p in SF["log"] if p["fecha"] == n]
    nom = SF["nombres"]
    if n <= SF["f1_rondas"]:
        return [pendiente("Federal A", n, rotulo_f(SF, n), f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][x]]}",
                          nom[x], nom[y]) for x, y in SF["fechas"][n - 1]]
    return [pendiente("Federal A", n, rotulo_f(SF, n),
                      "Campeonato" if SF["zona2_de"][x] == 0 else "Descenso", nom[x], nom[y])
            for x, y in SF["fechas2"][n - 1 - SF["f1_rondas"]]]


def fechas_conocidas_pb():
    S, SB, SF, SPB, SPC = _estado()
    return SPB["total"]

def partidos_fecha_pb(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SPB["fecha"]:
        return [p for p in SPB["log"] if p["fecha"] == n]
    nom = SPB["nombres"]
    
    rotulo = f"Fecha {n}"
    comp = "Liga"
    if SPB.get("desempate") and n > SPB["desempate"]["inicio"]:
        rotulo = f"Desempate (F. {n - SPB['desempate']['inicio']})"
        comp = "Desempate"
        
    return [pendiente("Primera B", n, rotulo, comp, nom[x], nom[y])
            for x, y in SPB["fechas"][n - 1]]


def fechas_conocidas_pc():
    S, SB, SF, SPB, SPC = _estado()
    return SPC["total"]

def partidos_fecha_pc(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SPC["fecha"]: return [p for p in SPC["log"] if p["fecha"] == n]
    nom = SPC["nombres"]
    return [pendiente("Primera C", n, f"Fecha {n}", "Liga", nom[x], nom[y]) for x, y in SPC["fechas"][n - 1]]


def proximo_partido(nombre):
    S, SB, SF, SPB, SPC = _estado()
    if nombre in S["nombres"]:
        for n in range(S["fecha"] + 1, fechas_conocidas_p() + 1):
            for p in partidos_fecha_p(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SB["nombres"]:
        for n in range(SB["fecha"] + 1, fechas_conocidas_b() + 1):
            for p in partidos_fecha_b(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SF["nombres"]:
        for n in range(SF["fecha"] + 1, fechas_conocidas_f() + 1):
            for p in partidos_fecha_f(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SPB["nombres"]:
        for n in range(SPB["fecha"] + 1, fechas_conocidas_pb() + 1):
            for p in partidos_fecha_pb(n):
                if nombre in (p["local"], p["visita"]):
                    return p
    elif nombre in SPC["nombres"]:
        for n in range(SPC["fecha"] + 1, fechas_conocidas_pc() + 1):
            for p in partidos_fecha_pc(n):
                if nombre in (p["local"], p["visita"]): return p
    return None


# ---- Ficha de un club (con buscador de sus partidos) ------------------------
def render_ficha(nombre, clave):
    S, SB, SF, SPB, SPC = _estado()
    partidos = [p for p in todos_los_partidos() if nombre in (p["local"], p["visita"])]
    cat = categoria_de(nombre)
    filas, letras = [], []
    gf_t = gc_t = 0
    for p in partidos:
        local, gf, gc, letra = resultado_para(p, nombre)
        letras.append(letra)
        gf_t, gc_t = gf_t + gf, gc_t + gc
        rival = p["visita"] if local else p["local"]
        res = f"{gf}-{gc}"
        if p["pen"]:
            pf, pc = p["pen"] if local else p["pen"][::-1]
            res += f" ({pf}-{pc} pen.)"
        if letra == "G":
            desenlace = "✅ Ganó"
        elif letra == "P":
            desenlace = "❌ Perdió"
        elif p["pen"]:
            desenlace = ("✅ Empató · ganó por penales" if p["gana"] == nombre
                         else "❌ Empató · perdió por penales")
        else:
            desenlace = "➖ Empató"
        cond = "Neutral" if p["neutral"] else ("Local" if local else "Visitante")
        comp = p["comp"] if p["comp"] == p["liga"] else f"{p['liga']} · {p['comp']}"
        filas.append({
            "Fecha": p["fecha"], "Competición": comp, "Condición": cond,
            " ": ESCUDOS.get(rival), "Rival": rival, "Resultado": res, "Desenlace": desenlace,
            "_t": norm(f"{rival} {nombre} {comp} {cond} {desenlace} {p['rotulo']}"),
            "_m": f" {gf}-{gc} {gc}-{gf} ",
        })

    g, e, pp = letras.count("G"), letras.count("E"), letras.count("P")
    forma = "".join(f'<span class="fm {x}">{x}</span>' for x in letras[-5:])
    st.markdown(
        f'<div class="team-head">{crest(nombre, 64)}<div><div class="tn">{esc(nombre)}</div>'
        f'<div style="margin-top:6px">{chip(cat) if cat else ""} '
        f'<span style="font-size:.8rem;opacity:.65">Temporada {S["temp"]}</span></div></div></div>',
        unsafe_allow_html=True)
    st.markdown(
        f'<div class="rec"><div><b>{len(partidos)}</b><span>PJ</span></div>'
        f'<div><b>{g}</b><span>G</span></div><div><b>{e}</b><span>E</span></div>'
        f'<div><b>{pp}</b><span>P</span></div><div><b>{gf_t}</b><span>GF</span></div>'
        f'<div><b>{gc_t}</b><span>GC</span></div><div><b>{gf_t - gc_t:+d}</b><span>DG</span></div>'
        f'<div><span>Últimos 5</span><div class="form">{forma or "—"}</div></div></div>',
        unsafe_allow_html=True)
    prox = proximo_partido(nombre)
    if prox:
        rival = prox["visita"] if prox["local"] == nombre else prox["local"]
        cond = "Local" if prox["local"] == nombre else "Visitante"
        st.markdown(f'<div class="next"><b>Próximo partido</b> · {esc(prox["rotulo"])} · '
                    f'{chip(prox["comp"])} {cond} vs {crest(rival, 20)} <b>{esc(rival)}</b></div>',
                    unsafe_allow_html=True)
    if not filas:
        st.info("Este club todavía no jugó partidos esta temporada.")
        return

    q = st.text_input("🔍 Buscar partido", key=f"q_{clave}_{nombre}",
                      placeholder="Rival, número de fecha, resultado (2-1), local, visitante, "
                                  "zona, octavos…")
    vis = [f for f in filas if coincide(q, f["_t"], f["Fecha"], f["_m"])] if q else filas
    if not vis:
        st.warning("No hay partidos que coincidan con la búsqueda.")
        return
    if q:
        st.caption(f"{len(vis)} de {len(filas)} partidos")
    df = pd.DataFrame(vis).drop(columns=["_t", "_m"])

    def color_res(fila):
        d = fila["Desenlace"]
        c = ("rgba(22,163,74,.16)" if d.startswith("✅") else
             "rgba(220,38,38,.14)" if d.startswith("❌") else "rgba(100,116,139,.12)")
        return [f"background-color: {c}" if col in ("Resultado", "Desenlace") else ""
                for col in fila.index]

    st.dataframe(df.style.apply(color_res, axis=1), hide_index=True, width="stretch",
                 height=min(35 * (len(df) + 1) + 3, 460),
                 column_config={"Fecha": st.column_config.NumberColumn("Fecha", width="small"),
                                " ": st.column_config.ImageColumn(" ", width="small")})
    penales = [p for p in partidos if p["pen"]]
    if penales:
        st.markdown('<div class="mlab">Definiciones por penales</div>'
                    + "".join(fila_partido_html(p) for p in penales), unsafe_allow_html=True)


@st.dialog("Ficha del club", width="large")
def ver_equipo(nombre):
    render_ficha(nombre, "dlg")


# ---- Fixture y resultados ---------------------------------------------------
def render_fecha(partidos, clave):
    """Partidos de una fecha en dos columnas; cada club se puede tocar para ver su ficha."""
    grupos = []
    for p in partidos:
        if not grupos or grupos[-1][0] != p["comp"]:
            grupos.append((p["comp"], []))
        grupos[-1][1].append(p)
    for g, (comp, lista) in enumerate(grupos):
        if len(grupos) > 1 or comp not in ("Fase 1",):
            st.markdown(chip(comp) + (' <span style="opacity:.6;font-size:.75rem">cancha neutral'
                                      '</span>' if lista[0]["neutral"] else ""),
                        unsafe_allow_html=True)
        mitad = (len(lista) + 1) // 2
        cols = st.columns(2, gap="medium") if len(lista) > 1 else [st.container()]
        for lado, (c, sub) in enumerate(zip(cols, (lista[:mitad], lista[mitad:]))):
            with c, st.container(key=f"fx_{clave}_{g}_{lado}"):
                for i, p in enumerate(sub):
                    k = f"{clave}_{g}_{p['local']}_{p['visita']}"
                    c1, c2, c3 = st.columns([5, 3.6, 5], vertical_alignment="center", gap="small")
                    if c1.button(p["local"], key=f"{k}_l", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["local"])
                    c2.markdown(marcador_html(p, crests=True), unsafe_allow_html=True)
                    if c3.button(p["visita"], key=f"{k}_v", help="Ver la ficha del club",
                                 width="stretch"):
                        ver_equipo(p["visita"])
                    if p["tanda"]:
                        st.markdown(tanda_html(p), unsafe_allow_html=True)


def _mover_fecha(key, delta, maximo):
    st.session_state[key] = min(max(1, st.session_state.get(key, 1) + delta), maximo)


def vista_fixture(liga):
    S, SB, SF, SPB, SPC = _estado()
    if liga == "p":
        total, jugadas, obtener, rotulo = fechas_conocidas_p(), S["fecha"], partidos_fecha_p, rotulo_p
        extra = "" if S["fase"] == 2 else " · las 9 fechas de la fase 2 se arman al terminar la fase 1"
    elif liga == "b":
        total, jugadas, obtener, rotulo = fechas_conocidas_b(), SB["fecha"], partidos_fecha_b, rotulo_b
        extra = ("" if SB["fechas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    elif liga == "pb":
        total, jugadas = fechas_conocidas_pb(), SPB["fecha"]
        obtener, rotulo = partidos_fecha_pb, lambda n: f"Fecha {n}"
        extra = ""
    elif liga == "pc":
        total, jugadas = fechas_conocidas_pc(), SPC["fecha"]
        obtener, rotulo = partidos_fecha_pc, lambda n: f"Fecha {n}"
        extra = ""
    else:
        total, jugadas = fechas_conocidas_f(), SF["fecha"]
        obtener, rotulo = partidos_fecha_f, lambda n: rotulo_f(SF, n)
        extra = ("" if SF["zonas2"] is not None else
                 " · la fase 2 se arma al terminar la fase 1")
    seccion("Fixture y resultados", "Tocá un club para ver su ficha" + extra, "#1e5aa8")
    if total == 0:
        st.info("Todavía no hay fechas programadas.")
        return
    key = f"fx_sel_{liga}_{S['temp']}_{jugadas}"
    if key not in st.session_state:
        st.session_state[key] = max(1, min(jugadas, total))
    c1, c2, c3 = st.columns([1, 6, 1], vertical_alignment="bottom")
    c1.button("◀", key=f"{key}_prev", width="stretch", on_click=_mover_fecha,
              args=(key, -1, total), disabled=st.session_state[key] <= 1)
    elegida = c2.selectbox("Fecha", list(range(1, total + 1)), key=key, format_func=lambda n:
                           rotulo(n) + (" · ✔ jugada" if n <= jugadas else " · por jugar"),
                           label_visibility="collapsed")
    c3.button("▶", key=f"{key}_next", width="stretch", on_click=_mover_fecha,
              args=(key, 1, total), disabled=elegida >= total)
    estado = chip("Jugada", "#16a34a") if elegida <= jugadas else (
        chip("Próxima fecha", "#2f7fd0") if elegida == jugadas + 1 else chip("Por jugar", "#64748b"))
    st.markdown(f'<div class="fx-head"><b style="font-size:1.05rem">{esc(rotulo(elegida))}</b>'
                f'{estado}</div>', unsafe_allow_html=True)
    render_fecha(obtener(elegida), f"{liga}{S['temp']}_{elegida}")


# ---- Tablas -----------------------------------------------------------------
def ultimos_movs(hist):
    if len(hist) < 2 or hist[-1][0] != hist[-2][0]:
        return None
    return hist[-2][1] - hist[-1][1], hist[-1][1]


def color_mov(v):
    if str(v).startswith("▲"):
        return "color: #16a34a; font-weight: 700"
    if str(v).startswith("▼"):
        return "color: #dc2626; font-weight: 700"
    return "color: #94a3b8"


def mostrar_tabla(df, fn_color, hist=None):
    df = df.copy()
    mov = ultimos_movs(hist) if hist is not None else None
    if hist is not None:
        if mov:
            d = [int(x) for x in mov[0][df["id"].to_numpy()]]
            df.insert(1, "±", [f"▲{x}" if x > 0 else f"▼{-x}" if x < 0 else "=" for x in d])
        else:
            df.insert(1, "±", ["–"] * len(df))
    df.insert(2 if "±" in df.columns else 1, "Escudo", [ESCUDOS.get(n) for n in df["Equipo"]])
    df = df.drop(columns="id")
    orden = [c for c in ["Pos", "±", "Escudo", "Equipo", "Pts", "PJ", "G", "E", "P", "GF", "GC",
                         "DG", "Destino", "Media"] if c in df.columns]
    df = df[orden]
    sty = df.style.apply(fn_color, axis=1)
    if "±" in df.columns:
        sty = sty.map(color_mov, subset=["±"])
    sty = sty.set_properties(subset=["Pts"], **{"font-weight": "700"})
    st.dataframe(sty, hide_index=True, width="stretch", height=35 * (len(df) + 1) + 3,
                 column_config={
                     "Pos": st.column_config.NumberColumn("#", width=38),
                     "±": st.column_config.TextColumn("±", width=46,
                                                      help="Puestos ganados o perdidos en la última fecha"),
                     "Escudo": st.column_config.ImageColumn("", width=40),
                     "Equipo": st.column_config.TextColumn("Club", width="medium"),
                     "Pts": st.column_config.NumberColumn("Pts", width=52),
                     "Media": st.column_config.NumberColumn("Media", format="%.1f", width=62,
                                                            help="Fuerza interna del equipo"),
                 })


def colorear_fase1(fila):
    """Pinta según la zona a la que pasa (o pasaría) cada equipo de Primera."""
    c = COLORES_ZONA[(fila["Pos"] - 1) // ZONA_TAM]
    return [f"background-color: {c}"] * len(fila)


def colorear_destino(fila):
    """Pinta según el destino (copas / promoción / descenso); dorado para el líder."""
    pos = fila["Pos"]
    c = COLOR_ORO if pos == 1 else COLORES_DESTINO.get(destino(pos), "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_b(fila):
    c = COLORES_B.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_f(fila):
    c = COLORES_F.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pb(fila):
    c = COLORES_B["Ascenso directo"] if fila["Destino"] == "Ascenso directo" else (COLORES_B["Desciende"] if fila["Destino"] == "Desciende" else "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pc(fila):
    c = COLORES_B["Ascenso directo"] if fila["Destino"] == "Ascenso directo" else ""
    return [f"background-color: {c}" if c else ""] * len(fila)


LEY_ZONAS = [("Pasa a Zona Campeonato", COLORES_ZONA[0]), ("Zona Intermedia", COLORES_ZONA[1]),
             ("Zona Descenso", COLORES_ZONA[2])]
LEY_DESTINOS = [("Líder", COLOR_ORO), ("Libertadores", COLORES_DESTINO["Libertadores"]),
                ("Fase previa Libertadores", COLORES_DESTINO["Fase previa Libertadores"]),
                ("Sudamericana", COLORES_DESTINO["Sudamericana"]),
                ("Promoción", COLORES_DESTINO["Promoción"]), ("Descenso", COLORES_DESTINO["Desciende"])]
LEY_B = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_B["Ascenso directo"]),
         ("Cuartos del reducido", COLORES_B["Cuartos del reducido"]),
         ("Octavos del reducido", COLORES_B["Octavos del reducido"]),
         ("Desciende", COLORES_B["Desciende"])]
LEY_F = [("Campeón", COLOR_ORO), ("Ascenso directo", COLORES_F["Ascenso directo"]),
         ("Juega el reducido", COLORES_F["Reducido"])]


# ---- Movimientos de la temporada -------------------------------------------
def rachas(log, nombres):
    seq = {n: [] for n in nombres}
    for p in log:
        for eq in (p["local"], p["visita"]):
            if eq in seq:
                seq[eq].append(resultado_para(p, eq)[3])

    def cola(lst, ok):
        n = 0
        for x in reversed(lst):
            if x not in ok:
                break
            n += 1
        return n

    invicto = max(nombres, key=lambda n: cola(seq[n], "GE"))
    sin_ganar = max(nombres, key=lambda n: cola(seq[n], "EP"))
    ganando = max(nombres, key=lambda n: cola(seq[n], "G"))
    return ((invicto, cola(seq[invicto], "GE")), (sin_ganar, cola(seq[sin_ganar], "EP")),
            (ganando, cola(seq[ganando], "G")))


def card(k, v, s="", color="#2f7fd0", big=False):
    return (f'<div class="card" style="--c:{color}"><div class="k">{k}</div>'
            f'<div class="v{" big" if big else ""}">{v}</div><div class="s">{s}</div></div>')


def eq_html(n, size=26):
    return f'{crest(n, size)}<span>{esc(n)}</span>'


def partido_corto(p):
    pen = f" ({p['pen'][0]}-{p['pen'][1]} pen.)" if p["pen"] else ""
    return (f'{crest(p["local"], 22)}<span>{esc(p["local"])} <b>{p["gl"]}-{p["gv"]}</b>'
            f'{pen} {esc(p["visita"])}</span>{crest(p["visita"], 22)}')


def render_movimientos(log, hist, nombres, color):
    seccion("Movimientos de la temporada", "Cambios en la tabla, rachas y partidos destacados",
            color)
    log = [p for p in log if p["local"] in nombres or p["visita"] in nombres]
    if not log:
        st.info("Simulá una fecha para ver los movimientos de la temporada.")
        return
    cards = ""
    mov = ultimos_movs(hist)
    if mov:
        d, cur = mov
        iu, idn = int(np.argmax(d)), int(np.argmin(d))
        if d[iu] > 0:
            cards += card("▲ Mayor subida · última fecha", eq_html(nombres[iu]),
                          f"Ganó {d[iu]} puesto{'s' if d[iu] > 1 else ''}: del "
                          f"{cur[iu] + d[iu]}° al {cur[iu]}°", "#16a34a")
        if d[idn] < 0:
            cards += card("▼ Mayor caída · última fecha", eq_html(nombres[idn]),
                          f"Perdió {-d[idn]} puesto{'s' if d[idn] < -1 else ''}: del "
                          f"{cur[idn] + d[idn]}° al {cur[idn]}°", "#dc2626")
    gole = max(log, key=lambda p: (abs(p["gl"] - p["gv"]), p["gl"] + p["gv"]))
    if gole["gl"] != gole["gv"]:
        cards += card("💥 Mayor goleada", partido_corto(gole),
                      f"{gole['rotulo']} · {gole['comp']}", "#ea580c")
    mas = max(log, key=lambda p: (p["gl"] + p["gv"], -abs(p["gl"] - p["gv"])))
    cards += card("⚽ Partido con más goles", partido_corto(mas),
                  f"{mas['gl'] + mas['gv']} goles · {mas['rotulo']}", "#0891b2")
    (inv, n_inv), (sg, n_sg), (gan, n_gan) = rachas(log, nombres)
    if n_gan >= 2:
        cards += card("🔥 Racha ganadora", eq_html(gan), f"{n_gan} victorias seguidas", "#16a34a")
    cards += card("🛡️ Racha invicta", eq_html(inv), f"{n_inv} partidos sin perder", "#2f7fd0")
    cards += card("🧊 Racha sin ganar", eq_html(sg), f"{n_sg} partidos sin ganar", "#64748b")
    goles = sum(p["gl"] + p["gv"] for p in log)
    emp = sum(p["gl"] == p["gv"] for p in log)
    cards += card("📈 Goles por partido", f"{goles / len(log):.2f}",
                  f"{goles} goles en {len(log)} partidos · {100 * emp / len(log):.0f}% empates",
                  "#7c3aed", big=True)
    st.markdown(f'<div class="cards">{cards}</div>', unsafe_allow_html=True)

    if mov:
        d, cur = mov
        orden = np.argsort(-d)
        suben = [i for i in orden if d[i] > 0][:8]
        bajan = [i for i in orden[::-1] if d[i] < 0][:8]

        def lista(ids, cls, signo):
            return "".join(f'<span class="mv">{crest(nombres[i], 20)}{esc(nombres[i])}'
                           f'<span class="d {cls}">{signo}{abs(d[i])}</span>'
                           f'<span style="opacity:.6">{cur[i]}°</span></span>' for i in ids) or "—"

        c1, c2 = st.columns(2)
        c1.markdown('<div class="mlab up">▲ Subieron en la última fecha</div><div class="movlist">'
                    + lista(suben, "up", "+") + "</div>", unsafe_allow_html=True)
        c2.markdown('<div class="mlab down">▼ Bajaron en la última fecha</div><div class="movlist">'
                    + lista(bajan, "down", "−") + "</div>", unsafe_allow_html=True)


# ---- Cuadro del reducido ----------------------------------------------------
def bracket_card(m, final=False):
    if m is None:
        fila = '<div class="bt tbd"><span class="nm">Por definir</span></div>'
        return f'<div class="bm">{fila}{fila}</div>'
    filas = ""
    for i, (nombre, g) in enumerate(((m["local"], m["gl"]), (m["visita"], m["gv"]))):
        cls = "win" if m["gana"] == nombre else "lose"
        pk = f'<span class="p">({m["pen"][i]})</span>' if m["pen"] else ""
        lv = "N" if m["neutral"] else ("L" if i == 0 else "V")
        tit = "Neutral" if lv == "N" else "Local" if lv == "L" else "Visitante"
        filas += (f'<div class="bt {cls}">{crest(nombre, 24)}<span class="nm" title="{esc(nombre)}">'
                  f'{esc(nombre)}</span><span class="lv" title="{tit}">{lv}</span>{pk}'
                  f'<span class="g">{g}</span></div>')
    pen = f"Penales {m['pen'][0]}-{m['pen'][1]} · " if m["pen"] else ""
    que = "🏆 Campeón" if final else "Avanza"
    return (f'<div class="bm">{filas}<div class="bfoot">{pen}{que}: <b>{esc(m["gana"])}</b></div>'
            f'{tanda_html(m)}</div>')


def bracket_html(SB):
    rondas = [list(r) for r in SB["bracket"]]
    # Ordena cada ronda según la siguiente para que el cuadro se lea de izquierda a derecha
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Octavos", "Cuartos", "Semifinal", "Final"]
    tam = [4, 4, 2, 1]
    cols = ""
    for r in range(4):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 3)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 4:
        c = rondas[3][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a Primera División</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a Primera</div></div>')
    promo = ""
    if SB["promo_partido"]:
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'{bracket_card(SB["promo_partido"])}</div>')
    elif len(rondas) == 4:
        perd = SB["nombres"][SB["perdedor_final"]]
        promo = (f'<div class="promo"><div class="round-h">{chip("Promoción")}</div>'
                 f'<div class="bm"><div class="bt">{crest(perd, 24)}<span class="nm">{esc(perd)}'
                 f'</span></div><div class="bt tbd"><span class="nm">27° de Primera</span></div>'
                 f'</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}{promo}</div></div>')
    return f'<div class="bracket">{cols}</div>'


def bracket_html_f(SF):
    rondas = [list(r) for r in SF["bracket"]]
    for k in range(len(rondas) - 1, 0, -1):
        nuevo = []
        for m in rondas[k]:
            for t in (m["local"], m["visita"]):
                for pm in rondas[k - 1]:
                    if pm["gana"] == t and all(pm is not x for x in nuevo):
                        nuevo.append(pm)
        nuevo += [pm for pm in rondas[k - 1] if all(pm is not x for x in nuevo)]
        rondas[k - 1] = nuevo
    titulos = ["Eliminatoria", "Semifinal", "Final"]
    tam = [1, 2, 1]
    cols = ""
    for r in range(3):
        ms = rondas[r] if r < len(rondas) else [None] * tam[r]
        cards = "".join(bracket_card(m, final=(r == 2)) for m in ms)
        cols += (f'<div class="round"><div class="round-h">{chip(titulos[r])}</div>'
                 f'<div class="round-b">{cards}</div></div>')
    if len(rondas) == 3:
        c = rondas[2][0]["gana"]
        champ = (f'<div class="champ"><div class="t">Campeón del reducido</div>'
                 f'<div style="margin-top:10px">{crest(c, 56)}</div><div class="nm">{esc(c)}</div>'
                 f'<div class="s">Asciende a la Primera Nacional</div></div>')
    else:
        champ = ('<div class="champ" style="opacity:.55"><div class="t">Campeón del reducido</div>'
                 '<div class="nm">Por definir</div><div class="s">Asciende a la Primera Nacional'
                 '</div></div>')
    cols += (f'<div class="round last"><div class="round-h">{chip("Campeón", "#b7860b")}</div>'
             f'<div class="round-b" style="justify-content:center">{champ}</div></div>')
    return f'<div class="bracket">{cols}</div>'


def barra_estado(items, progreso):
    celdas = "".join(f'<div class="stc"><span>{esc(k)}</span><b>{esc(str(v))}</b></div>'
                     for k, v in items)
    celdas += (f'<div class="stc"><span>Progreso</span><b>{progreso:.0f}%</b>'
               f'<div class="bar"><i style="width:{progreso:.1f}%"></i></div></div>')
    st.markdown(f'<div class="status">{celdas}</div>', unsafe_allow_html=True)