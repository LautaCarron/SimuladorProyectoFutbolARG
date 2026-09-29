"""Vista: estilos, escudos, tablas, fixtures, fichas de club y cuadros del reducido.

Todo lo que dibuja algo en pantalla. Las funciones leen el estado de la sesión con
_estado(), así que funcionan bien aunque haya varios usuarios a la vez.
"""

import hashlib
import html
import json
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



COLOR_ORO = "rgba(227, 162, 26, 0.30)"
COLORES_DESTINO = {
    "Libertadores": "rgba(116, 172, 223, 0.36)",
    "Fase previa Libertadores": "rgba(116, 172, 223, 0.18)",
    "Sudamericana": "rgba(224, 138, 40, 0.20)",
    "Promoción": "rgba(109, 63, 192, 0.16)",
    "Desciende": "rgba(184, 58, 46, 0.17)",
}
COLORES_ZONA = ["rgba(46, 125, 79, 0.15)", "rgba(227, 162, 26, 0.15)", "rgba(184, 58, 46, 0.13)"]
COLORES_B = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 125, 79, 0.22)",
    "Cuartos del reducido": "rgba(116, 172, 223, 0.36)",
    "Octavos del reducido": "rgba(116, 172, 223, 0.18)",
    "Desciende": "rgba(184, 58, 46, 0.17)",
    "→ Zona Campeonato": COLORES_ZONA[0],
    "→ Zona Intermedia": COLORES_ZONA[1],
    "→ Zona Descenso": COLORES_ZONA[2],
}
COLORES_F = {
    "Campeón · Ascenso": COLOR_ORO,
    "Ascenso directo": "rgba(46, 125, 79, 0.22)",
    "Reducido": "rgba(116, 172, 223, 0.30)",
    "→ Fase 2": "rgba(46, 125, 79, 0.15)",
    "→ Zona Campeonato": "rgba(46, 125, 79, 0.15)",
}


# ----------------------------------------------------------------------------
# PRESENTACIÓN (estilos, escudos, tarjetas)
# ----------------------------------------------------------------------------
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&display=swap');
/* ============ PROYECTO AFA · sistema visual del simulador ============
   Papel + tinta, celeste como único color de marca, dorado sólo para campeones.
   Rótulos en Archivo condensada, marca en Archivo expandida, números tabulares. */
:root{--tiza:#F4F2EC;--tiza-2:#ECE9E0;--papel:#FBFAF6;--tinta:#0F1B2D;--tinta-2:#4A5566;--tinta-3:#8A919C;
--line:rgba(15,27,45,.13);--line-2:rgba(15,27,45,.22);--soft:rgba(15,27,45,.035);--soft2:rgba(15,27,45,.07);
--cel:#74ACDF;--cel2:#2F6DB0;--navy:#0F1B2D;--gold:#C8900E;--acc:#2F6DB0;--pen:#6D3FC0;--win:#2E7D4F;--lose:#B83A2E;
--ease:cubic-bezier(.16,1,.3,1);--mix:#000;}
/* Modo oscuro: en la web lo elige la intro (data-tema); en la PC sigue al sistema */
:root[data-tema="oscuro"]{--tiza:#0E141C;--tiza-2:#151D28;--papel:#121A24;--tinta:#E8E6DF;--tinta-2:#A7AEB9;--tinta-3:#6F7885;--line:rgba(232,230,223,.12);--line-2:rgba(232,230,223,.22);--soft:rgba(232,230,223,.04);--soft2:rgba(232,230,223,.08);--cel2:#8CC0EE;--acc:#8CC0EE;--gold:#E3A21A;--pen:#A98BEA;--win:#4CAF7A;--lose:#E0685C;--mix:#fff;}
@media (prefers-color-scheme:dark){:root:not([data-tema]){--tiza:#0E141C;--tiza-2:#151D28;--papel:#121A24;--tinta:#E8E6DF;--tinta-2:#A7AEB9;--tinta-3:#6F7885;--line:rgba(232,230,223,.12);--line-2:rgba(232,230,223,.22);--soft:rgba(232,230,223,.04);--soft2:rgba(232,230,223,.08);--cel2:#8CC0EE;--acc:#8CC0EE;--gold:#E3A21A;--pen:#A98BEA;--win:#4CAF7A;--lose:#E0685C;--mix:#fff;}}
[role="dialog"],[role="dialog"] :is(p,div,td,th,label,input,textarea,summary,h2,button),html,body,.stApp,.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3,.stApp button,.stApp input,.stApp textarea,.stApp [data-testid="stMarkdownContainer"],[role="dialog"] p{font-family:'Archivo',system-ui,sans-serif !important;}
.stApp{background:var(--tiza);}
.block-container{padding-top:1.1rem;padding-bottom:4rem;max-width:1320px;}
[data-testid="stHeader"]{background:transparent;pointer-events:none;}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%;}
.st-key-puente{position:absolute !important;width:0 !important;height:0 !important;overflow:hidden !important;opacity:0;pointer-events:none;}
[data-testid="stHeader"] button{pointer-events:auto;}
/* botón de parámetros (»): chip propio para que al hacer scroll no se mezcle con el contenido */
body:has([role="dialog"]) [data-testid="stHeader"]{visibility:hidden;}   /* con la ficha abierta no se superpone */
[data-testid="stExpandSidebarButton"]{width:36px !important;height:36px !important;background:var(--tiza) !important;border:1px solid var(--line-2) !important;border-radius:4px !important;color:var(--tinta-2) !important;}
[data-testid="stSidebar"]{background:var(--tiza-2);border-right:1px solid var(--line);}
[data-testid="stSidebar"] h2{font-size:.78rem;font-stretch:85%;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--tinta-2);}
::selection{background:var(--cel);color:var(--tinta);}
/* ---------- cabecera (masthead) ---------- */
.masthead{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;flex-wrap:wrap;padding:6px 0 16px;margin-bottom:8px;position:relative;}
.masthead::after{content:"";position:absolute;left:0;right:0;bottom:0;height:5px;background:linear-gradient(90deg,var(--cel) 0 33.33%,#fff 33.33% 66.66%,var(--cel) 66.66%);box-shadow:inset 0 0 0 1px var(--line);}
.mh-marca{display:flex;align-items:center;gap:12px;color:var(--tinta) !important;text-decoration:none !important;}
.mh-marca svg{width:30px;height:30px;color:var(--gold);flex:none;}
.mh-marca b{display:block;font-stretch:118%;font-weight:900;font-size:1.25rem;letter-spacing:.03em;text-transform:uppercase;line-height:1;}
.mh-marca span{display:block;font-stretch:80%;font-weight:600;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--tinta-2);margin-top:4px;}
a.mh-marca span::before{content:"← ";opacity:0;margin-left:-1.1em;transition:opacity .3s,margin .3s var(--ease);}
a.mh-marca:hover span::before{opacity:1;margin-left:0;}
.mh-tabla{display:flex;align-items:stretch;overflow-x:auto;scrollbar-width:none;}
.mh-tabla::-webkit-scrollbar{display:none;}
.mh-c{padding:0 16px;border-left:1px solid var(--line);min-width:104px;}
.mh-c:first-child{border-left:0;padding-left:0;}
.mh-c span{display:block;font-stretch:80%;font-size:.64rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--tinta-2);white-space:nowrap;}
.mh-c b{display:block;font-stretch:110%;font-weight:800;font-size:1.12rem;font-variant-numeric:tabular-nums;margin-top:2px;white-space:nowrap;}
.mh-c .bar{height:2px;background:var(--soft2);margin-top:6px;}
.mh-c .bar i{display:block;height:100%;background:var(--tinta);transition:width .6s var(--ease);}
.mh-c.temp b{color:var(--cel2);}
.mh-der{display:flex;align-items:flex-end;gap:18px;min-width:0;}
.mh-tema{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;flex:none;border:1px solid var(--line-2);border-radius:4px;color:var(--tinta-2) !important;text-decoration:none !important;transition:border-color .2s,color .2s;}
.mh-tema:hover{border-color:var(--tinta);color:var(--tinta) !important;}
.mh-tema svg{width:16px;height:16px;}
.mh-tema .luna{display:none;}
:root[data-tema="oscuro"] .mh-tema .luna{display:block;}
:root[data-tema="oscuro"] .mh-tema .sol-ico{display:none;}
/* ---------- navegación (cubre tabs viejos baseweb y nuevos react-aria) ---------- */
.stTabs [role="tablist"]{gap:2px;border-bottom:1.5px solid var(--tinta);}
.stTabs [role="tab"]{padding:10px 14px 9px;border-radius:0;transition:background-color .2s;}
.stTabs [role="tab"]:hover{background:var(--soft2);}
.stTabs [role="tab"] p{font-size:.86rem;font-weight:800;font-stretch:88%;letter-spacing:.08em;text-transform:uppercase;color:var(--tinta-2);transition:color .2s;}
.stTabs [role="tab"][aria-selected="true"] p,.stTabs [role="tab"]:hover p{color:var(--tinta);}
.stTabs [data-baseweb="tab-highlight"],.stTabs .react-aria-SelectionIndicator{background:var(--cel2) !important;height:3px !important;}
.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs .stTabs [role="tablist"]{border-bottom:1px solid var(--line);}
.stTabs .stTabs [role="tab"] p{font-size:.84rem;font-weight:600;font-stretch:100%;letter-spacing:0;text-transform:none;}
.stTabs .stTabs [role="tab"][aria-selected="true"] p{font-weight:700;}
.stTabs .stTabs [data-baseweb="tab-highlight"],.stTabs .stTabs .react-aria-SelectionIndicator{background:var(--tinta) !important;height:2px !important;}
.stTabs .stTabs .stTabs [role="tab"] p{font-size:.8rem;}
/* ---------- botones / widgets ---------- */
.stButton>button,[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"]{border-radius:4px;font-weight:700;transition:background-color .2s,border-color .2s,color .2s,transform .12s;}
[data-testid="stBaseButton-primary"]{background:var(--tinta);border-color:var(--tinta);color:var(--tiza);}
[data-testid="stBaseButton-primary"]:hover{background:var(--cel2);border-color:var(--cel2);color:var(--tiza);}
[data-testid="stBaseButton-secondary"]{background:transparent;border:1px solid var(--line-2);}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--tinta);color:var(--tinta);background:var(--papel);}
.stButton>button:active{transform:translateY(1px);}
.stButton>button:disabled{opacity:.45;}
.stButton>button p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
[data-testid="stExpander"] details{border-radius:4px;border:1px solid var(--line);background:var(--papel);}
[data-testid="stExpander"] summary{font-weight:700;}
[data-testid="stExpander"] summary:hover{color:var(--cel2);}
[data-testid="stDataFrame"]{border-radius:4px;overflow:hidden;border:1px solid var(--line);}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{border-radius:4px !important;}
[role="dialog"]{border-radius:6px !important;background:var(--tiza) !important;}
[role="dialog"] h2,[role="dialog"] h2 *{color:inherit !important;}
[data-testid="stCaptionContainer"]{color:var(--tinta-2);}
/* ---------- barra de estado de cada liga ---------- */
.status{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));margin:10px 0 14px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
.stc{padding:10px 16px;border-left:1px solid var(--line);}
.stc:first-child{border-left:0;padding-left:0;}
.stc span{display:block;font-stretch:80%;font-size:.64rem;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--tinta-2);}
.stc b{font-stretch:110%;font-size:1.2rem;font-weight:800;font-variant-numeric:tabular-nums;}
.stc .bar{height:2px;background:var(--soft2);margin-top:8px;}
.stc .bar i{display:block;height:100%;background:var(--tinta);transition:width .6s var(--ease);}
.aviso{border-left:3px solid var(--cel2);background:color-mix(in srgb,var(--cel) 12%,transparent);border-radius:0 4px 4px 0;padding:10px 14px;font-size:.88rem;margin:4px 0 12px;}
/* ---------- títulos de sección ---------- */
.sec{display:flex;align-items:baseline;gap:12px;margin:14px 0 12px;flex-wrap:wrap;}
.sec .tt{font-stretch:95%;font-size:1.28rem;font-weight:900;letter-spacing:.01em;text-transform:uppercase;line-height:1.1;display:inline-flex;align-items:center;gap:10px;}
.sec .tt::before{content:"";width:10px;height:10px;background:var(--c,#2F6DB0);flex:none;}
.sec .sub{font-size:.82rem;color:var(--tinta-2);}
.chip{display:inline-flex;align-items:center;gap:4px;padding:3px 8px 2px;border-radius:3px;font-stretch:85%;font-size:.66rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;background:color-mix(in srgb,var(--c) 11%,transparent);color:color-mix(in srgb,var(--c) 85%,var(--mix));white-space:nowrap;}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:.74rem;color:var(--tinta-2);margin:10px 2px 4px;}
.legend span{display:inline-flex;align-items:center;gap:6px;}
.legend i{width:10px;height:10px;border-radius:2px;display:inline-block;box-shadow:inset 0 0 0 1px var(--line);}
/* ---------- escudos ---------- */
.crest-img{object-fit:contain;flex:none;vertical-align:middle;}
.crest{display:inline-flex;align-items:center;justify-content:center;color:#fff;font-weight:800;border-radius:6px 6px 50% 50%/6px 6px 62% 62%;flex:none;letter-spacing:-.03em;line-height:1;}
/* ---------- partidos ---------- */
.score{display:flex;justify-content:center;align-items:center;gap:5px;font-stretch:110%;font-weight:800;font-size:1.1rem;font-variant-numeric:tabular-nums;white-space:nowrap;}
.score .n{background:var(--tinta);color:var(--tiza);border-radius:3px;min-width:28px;text-align:center;padding:0 7px;line-height:1.6;}
.score .n.w{background:var(--cel2);color:var(--tiza);}
.score small{font-weight:800;font-size:.84rem;color:var(--pen);}
.score .sep{color:var(--tinta-3);}
.score .vs{font-stretch:85%;font-size:.68rem;font-weight:800;letter-spacing:.14em;color:var(--tinta-2);border:1px solid var(--line-2);border-radius:3px;padding:3px 8px 2px;}
details.tanda{margin:0 0 8px;border-left:2px solid var(--pen);padding:5px 10px;background:color-mix(in srgb,var(--pen) 6%,transparent);font-size:.8rem;}
details.tanda summary{cursor:pointer;font-weight:700;color:var(--pen);}
.trow{display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap;}
.trow .tn{min-width:120px;font-weight:600;}
.trow .tt{font-weight:800;min-width:16px;}
.pk{display:inline-flex;width:18px;height:18px;border-radius:50%;align-items:center;justify-content:center;font-size:.64rem;font-weight:800;color:#fff;margin-right:3px;}
.pk.ok{background:var(--win);}.pk.no{background:var(--lose);}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;align-items:center;background:var(--papel);border:0;border-bottom:1px solid var(--line);border-radius:0;padding:7px 8px;margin-bottom:0;transition:background-color .2s;}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]:hover{background:color-mix(in srgb,var(--cel) 10%,var(--papel));}
[class*="st-key-fx"]>[data-testid="stVerticalBlock"]{border-top:1px solid var(--line-2);}
[class*="st-key-fx"] [data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:5 1 0 !important;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(2){flex:3.6 1 0 !important;}
[class*="st-key-fx"] [data-testid="stVerticalBlock"],[class*="st-key-fx"][data-testid="stVerticalBlock"]{gap:0;}
[class*="st-key-fx"] button{border:none !important;background:transparent !important;box-shadow:none !important;padding:2px 4px !important;min-height:0 !important;}
[class*="st-key-fx"] button p{font-weight:600;font-size:.88rem;line-height:1.2;}
[class*="st-key-fx"] button:hover p{color:var(--cel2);}
/* el marcador toma su ancho y los nombres el resto (en dos líneas si hace falta, nunca encimados) */
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(2){flex:0 0 auto !important;}
[class*="st-key-fx"] button p{white-space:normal;overflow:visible;text-overflow:clip;overflow-wrap:break-word;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(1) button p{text-align:right;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(3) button p{text-align:left;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(1) button>div{justify-content:flex-end;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(3) button>div{justify-content:flex-start;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(1) button{justify-content:flex-end;text-align:right;width:100%;}
[class*="st-key-fx"] [data-testid="stColumn"]:nth-child(3) button{justify-content:flex-start;text-align:left;width:100%;}
[class*="st-key-fx"] [data-testid="stMarkdownContainer"],[class*="st-key-fx"] [data-testid="stMarkdownContainer"]>*{margin:0 !important;}
[class*="st-key-fx"] [data-testid="stColumn"] [data-testid="stVerticalBlock"]{justify-content:center;}
[class*="st-key-fx_sel"] button{border:1px solid var(--line-2) !important;background:var(--papel) !important;min-height:40px !important;padding:0 !important;justify-content:center !important;}
[class*="st-key-fx_sel"] button:hover:not(:disabled){border-color:var(--tinta) !important;}
[class*="st-key-fx_sel"] button:disabled{opacity:.35;}
.fx-head{display:flex;align-items:center;gap:10px;margin:4px 0 10px;flex-wrap:wrap;}
.fx-head b{font-stretch:105%;font-weight:800;}
.mrow{border-bottom:1px solid var(--line);padding:9px 4px;margin-bottom:0;}
.mrow .meta{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:.74rem;margin-bottom:6px;color:var(--tinta-2);}
.mline{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:10px;}
.side{display:flex;align-items:center;gap:8px;font-weight:600;font-size:.9rem;}
.side.l{justify-content:flex-end;text-align:right;}
.side.w{font-weight:800;}
/* ---------- planilla de datos (movimientos) ---------- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:0 24px;margin:4px 0 16px;border-top:1.5px solid var(--tinta);}
.card{padding:14px 0;border-bottom:1px solid var(--line);position:relative;}
.card .k{font-stretch:80%;font-size:.66rem;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--tinta-2);display:flex;align-items:center;gap:8px;}
.card .k::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--c,#2F6DB0);flex:none;}
.card .v{display:flex;align-items:center;gap:8px;font-weight:700;font-size:.96rem;margin-top:8px;flex-wrap:wrap;}
.card .v.big{font-stretch:115%;font-weight:800;font-size:1.8rem;font-variant-numeric:tabular-nums;}
.card .s{font-size:.78rem;color:var(--tinta-2);margin-top:5px;}
.movlist{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 12px;}
.mv{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:3px;padding:3px 10px 3px 5px;font-size:.8rem;font-weight:600;background:var(--papel);}
.mv .d{font-weight:800;font-variant-numeric:tabular-nums;}
.up{color:var(--win);}.down{color:var(--lose);}
.mlab{font-stretch:80%;font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--tinta-2);margin:8px 0 6px;}
.tlist{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 8px;}
.tl{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:3px;padding:5px 10px 5px 6px;font-weight:600;font-size:.86rem;background:var(--papel);}
.tl small{color:var(--tinta-3);font-weight:700;}
.champ{container-type:inline-size;border-radius:4px;padding:22px 18px;text-align:center;background:var(--papel);border:1px solid var(--line);border-top:3px solid var(--gold);}
.champ .t{font-stretch:85%;font-size:.66rem;text-transform:uppercase;letter-spacing:.18em;font-weight:800;color:var(--gold);}
/* el nombre se ajusta al ancho de la tarjeta y sólo corta entre palabras (nunca a mitad) */
.champ .nm{font-stretch:108%;font-weight:900;font-size:clamp(.92rem,8.4cqi,1.45rem);line-height:1.12;margin-top:10px;text-transform:uppercase;overflow-wrap:normal;word-break:normal;hyphens:manual;text-wrap:balance;}
.champ .s{font-size:.76rem;color:var(--tinta-2);margin-top:3px;}
/* ---------- cuadro del reducido ---------- */
.bracket{display:grid;grid-template-columns:repeat(5,minmax(205px,1fr));gap:28px;overflow-x:auto;padding:4px 2px 14px;}
.round{display:flex;flex-direction:column;}
.round-h{text-align:center;margin-bottom:10px;}
.round-b{display:flex;flex-direction:column;justify-content:space-around;gap:14px;flex:1;}
.bm{position:relative;border:1px solid var(--line);border-radius:4px;background:var(--papel);transition:border-color .2s;}
.bm:hover{border-color:var(--line-2);}
.round:not(.last) .bm::after{content:"";position:absolute;right:-29px;top:50%;width:28px;border-top:1px solid var(--line-2);}
.bt{display:flex;align-items:center;gap:7px;padding:7px 10px;font-size:.84rem;}
.bt+.bt{border-top:1px solid var(--line);}
.bt .nm{flex:1;min-width:0;font-weight:600;line-height:1.2;overflow-wrap:break-word;}
.bt .g{font-stretch:110%;font-size:1rem;font-weight:800;min-width:14px;text-align:right;font-variant-numeric:tabular-nums;}
.bt .p{font-size:.74rem;font-weight:800;color:var(--pen);}
.bt .lv{font-stretch:85%;font-size:.58rem;font-weight:800;border:1px solid var(--line-2);border-radius:2px;padding:0 4px;color:var(--tinta-2);}
.bt.win{box-shadow:inset 3px 0 0 var(--cel2);}
.bt.win .nm{font-weight:800;}
.bt.lose{opacity:.5;}
.bt.tbd .nm{color:var(--tinta-3);font-style:italic;font-weight:500;}
.bfoot{font-size:.7rem;padding:5px 10px 6px;border-top:1px dashed var(--line);color:var(--tinta-2);}
.bfoot b{color:var(--cel2);}
.bm details.tanda{margin:0 8px 8px;font-size:.72rem;}
.bm .trow .tn{min-width:0;}
.promo{margin-top:14px;}
/* ---------- ficha de club ---------- */
.team-head{display:flex;align-items:center;gap:16px;margin-bottom:8px;flex-wrap:wrap;}
.team-head>div{container-type:inline-size;flex:1;min-width:0;}
.team-head .tn{font-stretch:110%;font-size:clamp(1.05rem,7.4cqi,1.75rem);font-weight:900;text-transform:uppercase;line-height:1.05;overflow-wrap:normal;word-break:normal;text-wrap:balance;}
.rec{display:flex;gap:0;flex-wrap:wrap;margin:10px 0 14px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
.rec>div{border-left:1px solid var(--line);padding:7px 14px;text-align:left;min-width:60px;}
.rec>div:first-child{border-left:0;padding-left:0;}
.rec b{display:block;font-stretch:110%;font-size:1.2rem;font-weight:800;font-variant-numeric:tabular-nums;}
.rec span{font-stretch:80%;font-size:.62rem;text-transform:uppercase;letter-spacing:.14em;color:var(--tinta-2);font-weight:700;}
.form{display:inline-flex;gap:3px;vertical-align:middle;margin-top:4px;}
.fm{width:20px;height:20px;border-radius:2px;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:.64rem;font-weight:800;}
.fm.G{background:var(--win);}.fm.E{background:#8A919C;}.fm.P{background:var(--lose);}
.next{border-left:3px solid var(--cel2);padding:8px 12px;background:var(--papel);font-size:.86rem;margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:0;margin-top:8px;border-top:1px solid var(--line);border-left:1px solid var(--line);}
.ct{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:16px 8px;font-weight:600;font-size:.82rem;background:var(--papel);transition:background-color .2s;}
.ct:hover{background:color-mix(in srgb,var(--cel) 10%,var(--papel));}
.ct img{transition:transform .35s var(--ease);}
.ct:hover img{transform:translateY(-2px) scale(1.04);}
/* grilla de clubes clickeable (sección Clubes) */
[class*="st-key-cgrid"]{display:grid !important;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0 !important;border-top:1px solid var(--line);border-left:1px solid var(--line);margin-top:6px;}
[class*="st-key-cgrid"]>div{min-width:0;display:flex;}
[class*="st-key-ctile"]{position:relative;flex:1 1 auto;width:100%;height:136px;gap:0 !important;justify-content:center;border-right:1px solid var(--line);border-bottom:1px solid var(--line);background:var(--papel);padding:18px 8px 16px;transition:background-color .2s;}
[class*="st-key-ctile"]:hover{background:color-mix(in srgb,var(--cel) 12%,var(--papel));}
[class*="st-key-ctile"]:has(button:focus-visible){outline:2px solid var(--cel2);outline-offset:-2px;}
[class*="st-key-ctile"] [data-testid="stElementContainer"]:has(.stButton),[class*="st-key-ctile"] .stButton,[class*="st-key-ctile"] button{position:absolute !important;inset:0 !important;width:auto !important;height:auto !important;max-width:none !important;min-height:0 !important;margin:0 !important;}
[class*="st-key-ctile"] [data-testid="stElementContainer"]:has(.stButton){z-index:1;}
[class*="st-key-ctile"] button{opacity:0;cursor:pointer;border:0 !important;}
[class*="st-key-ctile"] [data-testid="stMarkdownContainer"],[class*="st-key-ctile"] [data-testid="stMarkdownContainer"]>*,[class*="st-key-ctile"] [data-testid="stMarkdown"]{margin:0 !important;}
[class*="st-key-ctile"]>[data-testid="stElementContainer"]:first-child{height:auto !important;}
.ct-in{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;font-weight:600;font-size:.84rem;line-height:1.2;}
.ct-in img{transition:transform .35s var(--ease);}
[class*="st-key-ctile"]:hover .ct-in img{transform:translateY(-3px) scale(1.05);}
[class*="st-key-ctile"]:hover .ct-in span{color:var(--cel2);}
/* tabla de las liguillas de desempate */
/* ---------- tablas (posiciones, partidos de un club, clasificados, campeones) ----------
   Integradas a la hoja: filete de tinta arriba, filas con líneas finas, números tabulares.
   Si no entra en el ancho se desliza de costado con #, ± y club fijos a la izquierda. */
.tabla-wrap{overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;margin:2px 0 12px;border-top:1.5px solid var(--tinta);scrollbar-width:thin;scrollbar-color:var(--line-2) transparent;}
/* width:0 + min-width:100%: la tabla ocupa el ancho disponible sin empujar el de la página */
.tabla-wrap,.liguilla-wrap,.bracket{width:0;min-width:100%;}
.tabla-wrap::-webkit-scrollbar{height:4px;}
.tabla-wrap::-webkit-scrollbar-thumb{background:var(--line-2);border-radius:2px;}
.tabla-wrap.alto{max-height:460px;overflow-y:auto;}
.tabla{width:100%;border-collapse:separate;border-spacing:0;font-size:.88rem;line-height:1.2;font-variant-numeric:tabular-nums;color:var(--tinta);}
.tabla th{background:var(--tiza);font-stretch:80%;font-size:.64rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--tinta-2);padding:10px 8px 8px;text-align:center;border-bottom:1px solid var(--line-2);white-space:nowrap;cursor:default;}
.tabla-wrap.alto th{position:sticky;top:0;z-index:2;}
.tabla td{padding:6px 8px;height:40px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;background:linear-gradient(var(--hv,transparent),var(--hv,transparent)),linear-gradient(var(--rc,transparent),var(--rc,transparent)),var(--papel);}
.tabla tbody tr:hover td{--hv:var(--soft2);}
.tabla tbody tr:last-child td{border-bottom:0;}
.tabla .tb-club,.tabla .tb-txt{text-align:left;}
.tabla td.tb-txt{font-size:.82rem;}
.tabla td.tb-pts{font-weight:800;}
/* club (escudo + nombre): nunca sale de su celda; hasta 2 líneas y, si una palabra no entra, se corta */
.tabla .tb-cl{display:inline-flex;align-items:center;gap:9px;font-weight:600;max-width:100%;min-width:0;vertical-align:middle;}
.tabla .tb-cl img,.tabla .tb-cl .crest{flex:none;}
.tabla .tb-nm{min-width:0;overflow:hidden;text-overflow:ellipsis;}
[data-club]{cursor:pointer;border-radius:3px;}
[data-club]:hover .tb-nm{color:var(--cel2);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;}
[data-club]:hover img{transform:scale(1.08);}
[data-club] img{transition:transform .25s var(--ease);}
[data-club]:focus-visible{outline:2px solid var(--cel2);outline-offset:2px;}
/* bloque fijo (#, ±, club): una sola celda, así al deslizar no queda ninguna rendija */
.tabla .tb-fija{position:sticky;left:0;z-index:1;text-align:left;padding-left:0;}
.tabla th.tb-fija{z-index:3;}
.tb-f{display:flex;align-items:center;min-width:0;}
.tb-f .tb-pos{flex:0 0 34px;text-align:center;color:var(--tinta-2);font-weight:700;}
.tb-f .tb-mov{flex:0 0 38px;text-align:center;font-size:.78rem;}
.tb-f .tb-fc{flex:1 1 auto;min-width:0;padding-left:4px;}
th .tb-f .tb-pos,th .tb-f .tb-mov{font-size:inherit;color:inherit;font-weight:inherit;}
.liguilla-wrap{overflow-x:auto;margin:2px 0 14px;border-top:1.5px solid var(--tinta);background:var(--papel);}
.liguilla{width:100%;border-collapse:collapse;font-size:.88rem;font-variant-numeric:tabular-nums;color:var(--tinta);}
.liguilla th{font-stretch:80%;font-size:.64rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--tinta-2);padding:10px 8px;text-align:center;border-bottom:1px solid var(--line-2);white-space:nowrap;}
.liguilla td{padding:9px 8px;text-align:center;border-bottom:1px solid var(--line);color:var(--tinta);}
.liguilla tr:last-child td{border-bottom:0;}
.liguilla .club{text-align:left;}
.liguilla td.club .tb-cl{display:inline-flex;align-items:center;gap:8px;font-weight:600;white-space:nowrap;}
.liguilla .pos{color:var(--tinta-2);font-weight:700;}
.liguilla .pts{font-weight:800;}
.liguilla tr:first-child+tr td{background:color-mix(in srgb,var(--cel) 10%,transparent);}
.catgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}
/* ---------- entrada suave del contenido al cambiar de pestaña ---------- */
.stTabs [role="tabpanel"]>div{animation:afa-in .45s var(--ease) both;}
@keyframes afa-in{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}
/* ---------- tablet y notebooks chicas: la cabecera no entra en una fila ---------- */
@media (min-width:641px) and (max-width:1180px){
.masthead{flex-direction:column;align-items:stretch;gap:14px;margin-top:34px;}
.mh-der{align-items:stretch;}
.mh-tabla{flex:1;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));overflow:visible;border-top:1px solid var(--line);}
.mh-c,.mh-c:first-child{min-width:0;padding:9px 12px 0;}
.mh-c.temp{padding-left:0;}
.mh-tema{position:absolute;top:0;right:0;}
}
/* ---------- fixture en tablet: una sola columna de partidos (los nombres entran completos) ---------- */
@media (min-width:641px) and (max-width:920px){
[data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]>[class*="st-key-fx_"]:not([class*="fx_sel"])){flex-direction:column !important;gap:0 !important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]>[class*="st-key-fx_"]:not([class*="fx_sel"]))>[data-testid="stColumn"]{width:100% !important;flex:1 1 auto !important;}
[data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]>[class*="st-key-fx_"]:not([class*="fx_sel"]))>[data-testid="stColumn"]+[data-testid="stColumn"] [class*="st-key-fx_"]>[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]>[class*="st-key-fx_"]:not([class*="fx_sel"]))>[data-testid="stColumn"]+[data-testid="stColumn"] [class*="st-key-fx_"]{border-top:0;}
}
/* ---------- reducido en pantallas medianas y chicas: rondas apiladas (nombres completos) ---------- */
@media (max-width:1180px){
.bracket{display:flex;flex-direction:column;gap:20px;overflow:visible;padding:4px 0 8px;}
.round-h{text-align:left;margin-bottom:8px;display:flex;align-items:center;gap:10px;}
.round-h::after{content:"";flex:1;border-top:1px solid var(--line);}
.round-b{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:10px;align-items:start;}
.round.last .round-b{display:flex;flex-direction:column;gap:14px;max-width:560px;}
.round:not(.last) .bm::after{display:none;}
.bt{padding:8px 10px;}
.bt .nm{white-space:normal;overflow:visible;line-height:1.2;}
}
/* ---------- mobile ---------- */
@media (max-width:640px){
.block-container{padding-left:16px;padding-right:16px;padding-top:.6rem;}
.masthead{flex-direction:column;align-items:stretch;gap:12px;margin-top:26px;}
/* acciones globales: los 3 botones en una fila, sin el texto de ayuda */
.st-key-acciones [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:6px !important;}
.st-key-acciones [data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:1 1 0 !important;}
.st-key-acciones [data-testid="stColumn"]:first-child{display:none;}
.st-key-acciones button{padding:6px 4px !important;min-height:40px;}
.st-key-acciones button p{font-size:.76rem;white-space:normal;line-height:1.15;text-align:center;overflow:visible;}
/* acciones de cada liga: rótulos arriba, "Próxima fecha" y "Hasta el final" lado a lado */
[data-testid="stHorizontalBlock"]:has([class*="_next"]):has([class*="_all"]){flex-wrap:wrap !important;flex-direction:row !important;gap:8px !important;}
[data-testid="stHorizontalBlock"]:has([class*="_next"]):has([class*="_all"])>[data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:1 1 calc(50% - 8px) !important;}
[data-testid="stHorizontalBlock"]:has([class*="_next"]):has([class*="_all"])>[data-testid="stColumn"]:first-child{flex-basis:100% !important;}
.mh-marca b{font-size:1.05rem;}
.mh-der{flex-direction:column-reverse;align-items:stretch;gap:10px;}
.mh-tema{position:absolute;top:0;right:0;}
/* cabecera en celular: Temporada y Partidos arriba, las 5 categorías en una fila pareja */
.mh-tabla{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));overflow:visible;border-top:1px solid var(--line);}
.mh-c,.mh-c:first-child{grid-column:span 2;min-width:0;padding:8px 6px 7px 8px;border-top:1px solid var(--line);}
.mh-c.temp,.mh-c:last-child{grid-column:span 5;border-top:0;padding-left:10px;}
.mh-c.temp{order:-2;border-left:0;padding-left:0;}
.mh-c:last-child{order:-1;}
.mh-c:nth-child(2){border-left:0;padding-left:0;}
.mh-c span{font-size:.58rem;letter-spacing:.08em;overflow:hidden;text-overflow:ellipsis;}
.mh-c b{font-size:.98rem;}
.mh-c .bar{margin-top:5px;}
.status{grid-template-columns:repeat(2,1fr);}
.stc:nth-child(3){border-left:0;padding-left:0;}
.stc:nth-child(n+3){border-top:1px solid var(--line);}
.stc{padding:9px 12px;}
.stc b{font-size:1.04rem;line-height:1.25;display:block;margin-top:2px;}
.sec .tt{font-size:1.1rem;}
.cgrid{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));}
.ct{font-size:.74rem;padding:12px 4px;}
[class*="st-key-fx"] [data-testid="stHorizontalBlock"]{padding:8px 2px;gap:6px !important;}
[class*="st-key-fx"] button{padding:2px 0 !important;}
[class*="st-key-fx"] button p{font-size:.8rem;line-height:1.15;}
[class*="st-key-fx"] .score{gap:3px;}
[class*="st-key-fx"] .score img,[class*="st-key-fx"] .score .crest{width:18px;height:18px;}
[class*="st-key-fx"] .score .n{min-width:24px;padding:0 5px;}
[class*="st-key-fx"] .score small{font-size:.74rem;}
/* selector de fecha: ‹ [fecha] › en una sola fila */
[data-testid="stHorizontalBlock"]:has([class*="_prev"]):has([class*="_next"]){flex-wrap:nowrap !important;gap:6px !important;}
[data-testid="stHorizontalBlock"]:has([class*="_prev"]):has([class*="_next"])>[data-testid="stColumn"]{min-width:0 !important;width:auto !important;flex:0 0 44px !important;}
[data-testid="stHorizontalBlock"]:has([class*="_prev"]):has([class*="_next"])>[data-testid="stColumn"]:nth-child(2){flex:1 1 0 !important;}
details.tanda{font-size:.76rem;}
.trow .tn{min-width:0;flex:1 1 auto;}
[class*="st-key-cgrid"]{grid-template-columns:repeat(3,1fr);}
[class*="st-key-ctile"]{padding:10px 4px;height:118px;}
.ct-in{font-size:.72rem;gap:8px;}
.ct-in img{width:42px;height:42px;}
.score{font-size:1rem;gap:3px;}
.tabla{font-size:.8rem;}
.tabla th{padding:9px 6px 7px;font-size:.6rem;letter-spacing:.1em;}
.tabla td{padding:4px 6px;height:46px;}
.tabla td.tb-txt{font-size:.74rem;white-space:normal;min-width:84px;line-height:1.2;}
.tabla .tb-cl{gap:7px;line-height:1.15;}
.tabla .tb-cl img{width:20px;height:20px;}
/* la columna fija tiene ancho propio: los números nunca quedan debajo del nombre */
.tabla .tb-fija{width:min(212px,56vw);min-width:min(212px,56vw);max-width:min(212px,56vw);box-shadow:inset -1px 0 0 var(--line-2);}
.tb-f .tb-pos{flex-basis:28px;}
.tb-f .tb-mov{flex-basis:32px;}
.tabla td.tb-fija .tb-nm{white-space:normal;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow-wrap:break-word;}
.tabla td.tb-club{white-space:normal;min-width:144px;}
.tabla td.tb-club .tb-nm{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow-wrap:break-word;}
.tabla-wrap.alto{max-height:none;overflow-y:visible;}
/* ficha del club: los 7 números en una fila y la forma debajo */
.rec{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));}
.rec>div{min-width:0;padding:7px 4px 7px 8px;}
.rec>div:last-child{grid-column:1/-1;border-left:0;border-top:1px solid var(--line);padding-left:0;display:flex;align-items:center;gap:10px;}
.rec>div:last-child .form{margin-top:0;}
.rec b{font-size:1.05rem;}
.team-head{gap:12px;}
.team-head img{width:52px;height:52px;}
.liguilla{font-size:.8rem;}
.liguilla th,.liguilla td{padding:8px 4px;}
.liguilla th{font-size:.58rem;letter-spacing:.08em;}
.liguilla td.club .tb-cl{white-space:normal;line-height:1.15;gap:7px;}
.liguilla td.club img{width:20px;height:20px;flex:none;}
.cards{grid-template-columns:1fr 1fr;gap:0 16px;}
.mline{gap:8px;}
.side{font-size:.82rem;gap:6px;line-height:1.15;}
.side img{width:22px;height:22px;}
.card:has(.v>span>b){grid-column:1/-1;}   /* tarjetas con un partido: a lo ancho, en una línea */
.card:has(.v>span>b) .v{flex-wrap:nowrap;}
.card .v{font-size:.9rem;gap:7px;}
.card .v img{width:22px;height:22px;}
.card .v.big{font-size:1.5rem;}
}
/* celulares muy angostos (iPhone SE, Android chicos) */
@media (max-width:400px){
.mh-c:not(.temp):not(:last-child){padding-left:5px;padding-right:3px;}
.mh-c:nth-child(2){padding-left:0;}
.mh-c:not(.temp):not(:last-child) span{white-space:normal;word-break:normal;overflow-wrap:normal;hyphens:none;line-height:1.15;min-height:2.3em;overflow:visible;letter-spacing:.04em;font-size:.56rem;}
.mh-c b{font-size:.92rem;}
.st-key-acciones button p{font-size:.72rem;}
.tabla .tb-fija{width:60vw;min-width:60vw;max-width:60vw;}
.tb-f .tb-pos{flex-basis:24px;}
.tb-f .tb-mov{flex-basis:28px;}
.chip{font-size:.6rem;padding:3px 6px 2px;}
[class*="st-key-fx"] button p{font-size:.76rem;}
}
@media (max-width:359px){
[class*="st-key-fx"] .score img,[class*="st-key-fx"] .score .crest{display:none;}   /* sin lugar: quedan los nombres */
}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important;}}
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
    return S["log"] + S["b"]["log"] + S["f"]["log"] + S["pb"]["log"] + S["pc"]["log"] + S["reg"]["log"]


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
    if nombre in st.session_state.S["reg"]["nombres"]:
        return "Regional Amateur"
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
    return (f'<details class="tanda"{" open" if abierto else ""}><summary>Penales · '
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
    if n <= FECHAS_F1:
        comp = "Fase 1"
    elif n <= TOTAL_FECHAS:
        comp = f"Zona {ZONAS[S['zona_de'][x]]}" # Nota interna
    else:
        comp = "Desempate"
    
    # Construcción segura evitando KeyError
    return [pendiente("Primera División", n, rotulo_p(S, n),
                      comp if comp == "Desempate" else ("Fase 1" if n <= FECHAS_F1 else f"Zona {ZONAS[S['zona_de'][x]]}"),
                      nom[x], nom[y]) for x, y in S["fechas"][n - 1]]


def fechas_conocidas_b():
    S, SB, SF, SPB, SPC = _estado()
    return max(SB["fecha"], B_F1 if SB["fechas2"] is None else B_F1 + len(SB["fechas2"]))


def partidos_fecha_b(n):
    S, SB, SF, SPB, SPC = _estado()
    if n <= SB["fecha"]:
        return [p for p in SB["log"] if p["fecha"] == n]
    nom = SB["nombres"]
    if n <= B_F1:
        return [pendiente("Primera Nacional", n, rotulo_b(SB, n), f"Zona {'AB'[SB['zona_de'][x]]}",
                          nom[x], nom[y]) for x, y in SB["fechas"][n - 1]]
    return [pendiente("Primera Nacional", n, rotulo_b(SB, n),
                      f"Zona {B_ZONAS2[SB['zona2_de'][x]]}" if n <= B_F1 + B_F2 else "Desempate Permanencia", nom[x], nom[y])
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


def fechas_conocidas_reg():
    return st.session_state.S["reg"]["total"]

def partidos_fecha_reg(n):
    SREG = st.session_state.S["reg"]
    if n <= SREG["fecha"]: return [p for p in SREG["log"] if p["fecha"] == n]
    nom = SREG["nombres"]
    return [pendiente("Regional Amateur", n, f"Fecha {n}", "Liga", nom[x], nom[y]) for x, y in SREG["fechas"][n - 1]]


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
    elif nombre in st.session_state.S["reg"]["nombres"]:
        for n in range(st.session_state.S["reg"]["fecha"] + 1, fechas_conocidas_reg() + 1):
            for p in partidos_fecha_reg(n):
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
            desenlace = "Ganó"
        elif letra == "P":
            desenlace = "Perdió"
        elif p["pen"]:
            desenlace = ("Empató · ganó por penales" if p["gana"] == nombre
                         else "Empató · perdió por penales")
        else:
            desenlace = "Empató"
        cond = "Neutral" if p["neutral"] else ("Local" if local else "Visitante")
        comp = p["comp"] if p["comp"] == p["liga"] else f"{p['liga']} · {p['comp']}"
        filas.append({
            "Fecha": p["fecha"], "Competición": comp, "Condición": cond,
            "Rival": rival, "Resultado": res, "Desenlace": desenlace,
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

    q = st.text_input(":material/search: Buscar partido", key=f"q_{clave}_{nombre}",
                      placeholder="Rival, número de fecha, resultado (2-1), local, visitante, "
                                  "zona, octavos…")
    vis = [f for f in filas if coincide(q, f["_t"], f["Fecha"], f["_m"])] if q else filas
    if not vis:
        st.warning("No hay partidos que coincidan con la búsqueda.")
        return
    if q:
        st.caption(f"{len(vis)} de {len(filas)} partidos")
    # rival y resultado primero: en el celular se ven sin deslizar la tabla
    df = pd.DataFrame(vis)[["Fecha", "Rival", "Resultado", "Desenlace", "Condición", "Competición"]]

    def color_res(fila):
        d = fila["Desenlace"]
        c = ("rgba(46,125,79,.15)" if d == "Ganó" or "ganó por penales" in d else
             "rgba(184,58,46,.13)" if d == "Perdió" or "perdió por penales" in d else "rgba(15,27,45,.06)")
        return [f"background-color: {c}" if col in ("Resultado", "Desenlace") else ""
                for col in fila.index]

    st.markdown(tabla_html(df, color_res, clubes=("Rival",)).replace(
        'class="tabla-wrap"', 'class="tabla-wrap alto"', 1), unsafe_allow_html=True)
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
        # Lo separamos en dos líneas para que sea más claro
        total, jugadas, obtener = fechas_conocidas_p(), S["fecha"], partidos_fecha_p
        rotulo = lambda n: rotulo_p(S, n)
        extra = "" if S["fase"] == 2 else " · las 9 fechas de la fase 2 se arman al terminar la fase 1"
    elif liga == "b":
        total, jugadas, obtener = fechas_conocidas_b(), SB["fecha"], partidos_fecha_b
        rotulo = lambda n: rotulo_b(SB, n)
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
    elif liga == "reg":
        SREG = st.session_state.S["reg"]
        total, jugadas = fechas_conocidas_reg(), SREG["fecha"]
        obtener, rotulo = partidos_fecha_reg, lambda n: f"Fecha {n}"
        extra = " · Formato de liga provisional"
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
    c1.button(":material/chevron_left:", key=f"{key}_prev", width="stretch", on_click=_mover_fecha,
              args=(key, -1, total), disabled=st.session_state[key] <= 1)
    elegida = c2.selectbox("Fecha", list(range(1, total + 1)), key=key, format_func=lambda n:
                           rotulo(n) + (" · jugada" if n <= jugadas else " · por jugar"),
                           label_visibility="collapsed")
    c3.button(":material/chevron_right:", key=f"{key}_next", width="stretch", on_click=_mover_fecha,
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


# ---- Tabla HTML (integrada a la página; en mobile se desliza con el club fijo) ----
_COL_NUM = {"Pos", "Pts", "PJ", "G", "E", "P", "GF", "GC", "DG", "Media", "Fecha", "Mérito", "Resultado",
            "Temporada"}
_TITULOS = {"Pos": "#", "Equipo": "Club"}
_AYUDAS = {"±": "Puestos ganados o perdidos en la última fecha", "Media": "Fuerza interna del equipo",
           "Pts": "Puntos", "PJ": "Partidos jugados", "G": "Ganados", "E": "Empatados",
           "P": "Perdidos", "GF": "Goles a favor", "GC": "Goles en contra", "DG": "Diferencia de gol"}


def _valor(v, formato):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return formato.format(v) if formato else esc(str(v))


def club_link(nombre, size=22):
    """Escudo + nombre de un club que al tocarlo abre su ficha (la misma de la sección Clubes).
    El click lo recibe el puente de `puente_clubes()`."""
    n = esc(nombre)
    return (f'<span class="tb-cl" role="button" tabindex="0" data-club="{n}" '
            f'title="Ver la ficha de {n}">{crest(nombre, size)}<span class="tb-nm">{n}</span></span>')


def _th(c, clase=""):
    ayuda = f' title="{esc(_AYUDAS[c])}"' if c in _AYUDAS else ""
    return f'<th class="{clase}"{ayuda}>{esc(_TITULOS.get(c, c))}</th>'


def tabla_html(df, estilo=None, clubes=("Equipo",), formatos=None, fija=None, clic=True):
    """Dibuja un DataFrame como tabla HTML con el estilo del sitio.
    - `estilo(fila)` devuelve una lista de CSS por celda (como pandas Styler).
    - Las columnas de `clubes` llevan escudo y (con `clic`) abren la ficha del club.
    - `fija`: esa columna y las anteriores (#, ±, Club) forman un solo bloque que queda quieto
      al deslizar la tabla en pantallas chicas."""
    formatos = formatos or {}
    cols = list(df.columns)
    n_fijas = cols.index(fija) + 1 if fija in cols else 0
    fijas, resto = cols[:n_fijas], cols[n_fijas:]

    def clase(c):
        if c in clubes:
            return "tb-club"
        k = "tb-num" if c in _COL_NUM else "tb-txt"
        return k + (" tb-pts" if c == "Pts" else "")

    def contenido(c, v):
        if c in clubes and isinstance(v, str):
            return club_link(v) if clic else (f'<span class="tb-cl">{crest(v, 22)}'
                                              f'<span class="tb-nm">{esc(v)}</span></span>')
        return _valor(v, formatos.get(c))

    def parte_fija(c, v, e=""):
        cls = {"Pos": "tb-pos", "±": "tb-mov"}.get(c)
        if cls is None:                       # la columna del club ocupa el resto del bloque
            return f'<span class="tb-fc">{contenido(c, v)}</span>'
        e = ";".join(x for x in (e or "").split(";") if x.strip() and "background" not in x)
        return f'<span class="{cls}"' + (f' style="{e}"' if e else "") + f'>{_valor(v, None)}</span>'

    th = ""
    if fijas:
        th += ('<th class="tb-fija"><div class="tb-f">'
               + "".join(f'<span class="{ {"Pos": "tb-pos", "±": "tb-mov"}.get(c, "tb-fc") }"'
                         + (f' title="{esc(_AYUDAS[c])}"' if c in _AYUDAS else "")
                         + f'>{esc(_TITULOS.get(c, c))}</span>' for c in fijas)
               + '</div></th>')
    th += "".join(_th(c, clase(c)) for c in resto)

    filas = []
    for _, fila in df.iterrows():
        css = list(estilo(fila)) if estilo else [""] * len(cols)
        css = [(e or "").replace("background-color", "--rc").strip() for e in css]
        tds = ""
        if fijas:
            fondo = css[n_fijas - 1]                     # color de la fila (el de la celda del club)
            fondo = ";".join(x for x in fondo.split(";") if "--rc" in x)
            tds += (f'<td class="tb-fija"' + (f' style="{fondo}"' if fondo else "") + '><div class="tb-f">'
                    + "".join(parte_fija(c, fila[c], css[i]) for i, c in enumerate(fijas))
                    + '</div></td>')
        for i, c in enumerate(resto, start=n_fijas):
            e = css[i]
            tds += (f'<td class="{clase(c)}"' + (f' style="{e}"' if e else "")
                    + f'>{contenido(c, fila[c])}</td>')
        filas.append("<tr>" + tds + "</tr>")
    return (f'<div class="tabla-wrap"><table class="tabla{" con-fija" if fijas else ""}">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(filas)}</tbody></table></div>')


# ---- Puente: tocar un club en cualquier tabla abre su ficha -----------------
# Las tablas son HTML (no widgets), así que un script chico escucha los toques sobre
# [data-club] y le pasa el nombre a un campo oculto de Streamlit; ese campo abre la misma
# ficha (ver_equipo) que usa la sección Clubes.
_PUENTE_JS = """
<script>
(function () {
  if (window.__afaPuenteClubes) return;
  window.__afaPuenteClubes = true;
  function abrir(nombre) {
    const inp = document.querySelector('.st-key-puente_club input');
    if (!inp) return;
    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    set.call(inp, nombre);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
  }
  document.addEventListener('click', function (e) {
    const t = e.target.closest && e.target.closest('[data-club]');
    if (!t) return;
    e.preventDefault();
    abrir(t.dataset.club);
  });
  document.addEventListener('keydown', function (e) {
    const t = e.target;
    if ((e.key === 'Enter' || e.key === ' ') && t && t.matches && t.matches('[data-club]')) {
      e.preventDefault();
      abrir(t.dataset.club);
    }
  });
})();
</script>
"""


def _instalar_puente_js():
    """Corre el script en la página. st.html(unsafe_allow_javascript) es lo actual; en versiones
    de Streamlit que no lo tienen se usa un iframe que lo inyecta en la página de arriba."""
    try:
        st.html(_PUENTE_JS, unsafe_allow_javascript=True)
    except TypeError:
        import streamlit.components.v1 as components
        js = _PUENTE_JS.replace("<script>", "").replace("</script>", "")
        components.html("<script>const s = window.parent.document.createElement('script');"
                        f"s.textContent = {json.dumps(js)};"
                        "window.parent.document.head.appendChild(s);</script>", height=0)


def _club_elegido():
    st.session_state["_club_a_abrir"] = st.session_state.get("puente_club", "")
    st.session_state["puente_club"] = ""


def puente_clubes():
    """Campo oculto + script que conectan los clubes de las tablas con su ficha."""
    with st.container(key="puente"):
        st.text_input("club", key="puente_club", on_change=_club_elegido,
                      label_visibility="collapsed")
        _instalar_puente_js()
    nombre = st.session_state.pop("_club_a_abrir", "")
    if nombre:
        ver_equipo(nombre)


def mostrar_tabla(df, fn_color, hist=None):
    df = df.copy()
    mov = ultimos_movs(hist) if hist is not None else None
    if hist is not None:
        if mov:
            d = [int(x) for x in mov[0][df["id"].to_numpy()]]
            df.insert(1, "±", [f"▲{x}" if x > 0 else f"▼{-x}" if x < 0 else "=" for x in d])
        else:
            df.insert(1, "±", ["–"] * len(df))
    df = df.drop(columns="id")
    orden = [c for c in ["Pos", "±", "Equipo", "Pts", "PJ", "G", "E", "P", "GF", "GC",
                         "DG", "Destino", "Media"] if c in df.columns]
    df = df[orden]
    cols = list(df.columns)

    def estilo(fila):
        css = list(fn_color(fila))
        if "±" in cols:
            i = cols.index("±")
            css[i] = "; ".join(x for x in (css[i], color_mov(fila["±"])) if x)
        return css

    st.markdown(tabla_html(df, estilo, formatos={"Media": "{:.1f}"}, fija="Equipo"),
                unsafe_allow_html=True)


def colorear_fase1(fila):
    """Pinta según la zona a la que pasa (o pasaría) cada equipo de Primera."""
    c = COLORES_ZONA[(fila["Pos"] - 1) // ZONA_TAM]
    return [f"background-color: {c}"] * len(fila)


def colorear_destino(fila):
    """Pinta según el destino (copas / promoción / descenso); dorado para el líder."""
    pos = fila["Pos"]
    d = fila.get("Destino", "")
    if "Desempate" in d:
        if "Campeonato" in d:
            c = "rgba(249, 115, 22, 0.3)"
        else:
            c = "rgba(147, 51, 234, 0.3)"
        return [f"background-color: {c}"] * len(fila)
        
    c = COLOR_ORO if pos == 1 else COLORES_DESTINO.get(destino(pos), "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_b(fila):
    d = fila["Destino"]
    c = COLORES_B.get(d, "")
    if "Desempate" in d:
        c = "rgba(147, 51, 234, 0.3)"
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_f(fila):
    c = COLORES_F.get(fila["Destino"], "")
    return [f"background-color: {c}" if c else ""] * len(fila)


def colorear_pb(fila):
    d = fila["Destino"]
    c = COLORES_B["Ascenso directo"] if d == "Ascenso directo" else (
        COLORES_B["Desciende"] if d == "Desciende" else (
        "rgba(147, 51, 234, 0.3)" if d == "Desempate Permanencia" else (
        "rgba(249, 115, 22, 0.3)" if d in ("Desempate Campeonato", "Desempate Ascenso") else ""
        )))
    return [f"background-color: {c}" if c else ""] * len(fila)

def colorear_pc(fila):
    d = fila["Destino"]
    c = COLORES_B["Ascenso directo"] if d == "Ascenso directo" else (
        "rgba(249, 115, 22, 0.3)" if d in ("Desempate Campeonato", "Desempate Ascenso") else ""
    )
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
        cards += card("Mayor goleada", partido_corto(gole),
                      f"{gole['rotulo']} · {gole['comp']}", "#ea580c")
    mas = max(log, key=lambda p: (p["gl"] + p["gv"], -abs(p["gl"] - p["gv"])))
    cards += card("Partido con más goles", partido_corto(mas),
                  f"{mas['gl'] + mas['gv']} goles · {mas['rotulo']}", "#0891b2")
    (inv, n_inv), (sg, n_sg), (gan, n_gan) = rachas(log, nombres)
    if n_gan >= 2:
        cards += card("Racha ganadora", eq_html(gan), f"{n_gan} victorias seguidas", "#16a34a")
    cards += card("Racha invicta", eq_html(inv), f"{n_inv} partidos sin perder", "#2f7fd0")
    cards += card("Racha sin ganar", eq_html(sg), f"{n_sg} partidos sin ganar", "#64748b")
    goles = sum(p["gl"] + p["gv"] for p in log)
    emp = sum(p["gl"] == p["gv"] for p in log)
    cards += card("Goles por partido", f"{goles / len(log):.2f}",
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
    que = "Campeón" if final else "Avanza"
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