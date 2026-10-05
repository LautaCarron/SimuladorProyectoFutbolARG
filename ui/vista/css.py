"""Hoja de estilos (CSS) de toda la interfaz.
"""


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
[data-testid="stHeader"]{background:transparent;}
/* la franja superior de Streamlit no debe tapar lo que queda debajo al hacer scroll: nada de la cabecera
   recibe clics salvo sus botones (menú, Deploy, »). Con !important y en todos los hijos, porque algunas
   versiones de Streamlit ponen un contenedor a todo el ancho con pointer-events propio */
[data-testid="stHeader"],[data-testid="stHeader"] *,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{pointer-events:none !important;}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%;}
.st-key-puente{position:absolute !important;width:0 !important;height:0 !important;overflow:hidden !important;opacity:0;pointer-events:none;}
[data-testid="stHeader"] :is(button,a,[role="button"],[role="menuitem"]),[data-testid="stHeader"] :is(button,a) *,[data-testid="stToolbar"] :is(button,a,[role="button"]),[data-testid="stExpandSidebarButton"],[data-testid="stExpandSidebarButton"] *{pointer-events:auto !important;}
/* botón de parámetros (»): chip propio para que al hacer scroll no se mezcle con el contenido */
body:has([role="dialog"]) [data-testid="stHeader"]{visibility:hidden;}   /* con la ficha abierta no se superpone */
[data-testid="stExpandSidebarButton"]{width:36px !important;height:36px !important;background:var(--tiza) !important;border:1px solid var(--line-2) !important;border-radius:4px !important;color:var(--tinta-2) !important;}
[data-testid="stSidebar"]{background:var(--tiza-2);border-right:1px solid var(--line);}
[data-testid="stSidebar"] h2{font-size:.78rem;font-stretch:85%;text-transform:uppercase;letter-spacing:.14em;font-weight:700;color:var(--tinta-2);}
::selection{background:var(--cel);color:var(--tinta);}
/* ---------- "Simular todo": al tocarlo, el mismo botón dice "Simulando…" hasta que termina ---------- */
button.afa-simulando{position:relative;pointer-events:none;}
button.afa-simulando>*{visibility:hidden;}
button.afa-simulando::after{content:"Simulando…";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-weight:700;}
/* ---------- cabecera (masthead) ---------- */
.masthead{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;flex-wrap:wrap;padding:6px 0 16px;margin-bottom:8px;position:relative;}
.masthead::after{content:"";position:absolute;left:0;right:0;bottom:0;height:5px;background:linear-gradient(90deg,var(--cel) 0 33.33%,#fff 33.33% 66.66%,var(--cel) 66.66%);box-shadow:inset 0 0 0 1px var(--line);}
.mh-marca{display:flex;align-items:center;gap:12px;color:var(--tinta) !important;text-decoration:none !important;}
.mh-marca svg{width:30px;height:30px;color:var(--gold);flex:none;}
.mh-marca b{display:block;font-stretch:118%;font-weight:900;font-size:1.25rem;letter-spacing:.03em;text-transform:uppercase;line-height:1;}
.mh-marca span{display:block;font-stretch:80%;font-weight:600;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--tinta-2);margin-top:4px;}
/* la flecha "←" aparece sin ocupar lugar: si cambiara el ancho de la marca, la cabecera
   podía pasar a dos renglones y quedar titilando mientras el mouse está encima */
a.mh-marca span{position:relative;}
a.mh-marca span::before{content:"←";position:absolute;right:100%;margin-right:3px;opacity:0;transform:translateX(4px);transition:opacity .3s,transform .3s var(--ease);pointer-events:none;}
a.mh-marca:hover span::before{opacity:1;transform:none;}
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
.champ{container-type:inline-size;width:100%;box-sizing:border-box;border-radius:4px;padding:22px 18px;text-align:center;background:var(--papel);border:1px solid var(--line);border-top:3px solid var(--gold);}
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
.liguilla:not(.marcada) tr:first-child+tr td{background:color-mix(in srgb,var(--cel) 10%,transparent);}
/* desempates de 3 o más: verde los que logran el objetivo de la tabla, rojo los que no */
:root{--liga-ok:color-mix(in srgb,var(--win) 20%,transparent);--liga-out:color-mix(in srgb,var(--lose) 18%,transparent);}
.liguilla tr.ok td{background:var(--liga-ok);}
.liguilla tr.out td{background:var(--liga-out);}
.liguilla tr.ok td.pos{box-shadow:inset 3px 0 0 var(--win);}
.liguilla tr.out td.pos{box-shadow:inset 3px 0 0 var(--lose);}
/* Regional Amateur: las 6 finales por el ascenso */
.rf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:14px;margin:6px 0 16px;}
.rf{border:1px solid var(--line);border-radius:6px;background:var(--papel);overflow:hidden;display:flex;flex-direction:column;transition:border-color .2s;}
.rf:hover{border-color:var(--line-2);}
.rf-h{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line);background:var(--soft);}
.rf-n{font-stretch:85%;font-size:.66rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);}
.rf-reg{font-size:.76rem;font-weight:700;color:var(--tinta-2);text-align:right;}
.rf-reg i{font-style:normal;font-weight:500;color:var(--tinta-3);margin:0 2px;}
.rf-fila{display:grid;grid-template-columns:minmax(0,1fr) 34px 34px 50px;align-items:center;gap:4px;padding:9px 14px;}
.rf-fila+.rf-fila:not(.rf-cab){border-top:1px solid var(--line);}
.rf-cab{padding:7px 14px 0;font-stretch:85%;font-size:.58rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--tinta-3);}
.rf-cab span{text-align:center;}
.rf-eq{display:flex;align-items:center;gap:10px;min-width:0;}
.rf-nm{display:flex;flex-direction:column;min-width:0;line-height:1.2;}
.rf-nm .nm,.rf-nm b{font-size:.86rem;font-weight:700;overflow-wrap:break-word;}
.rf-nm small{font-size:.66rem;font-weight:600;color:var(--tinta-3);margin-top:2px;}
.rf-g{text-align:center;font-variant-numeric:tabular-nums;font-size:.86rem;font-weight:600;color:var(--tinta-2);}
.rf-tot{font-stretch:110%;font-size:1.12rem;font-weight:800;color:var(--tinta);}
.rf-tot sup{font-size:.62rem;font-weight:800;color:var(--pen);margin-left:2px;vertical-align:super;}
.rf-fila.win{box-shadow:inset 3px 0 0 var(--win);}
.rf-fila.win .nm{font-weight:800;}
.rf-fila.win .rf-tot{color:var(--win);}
.rf-fila.lose{opacity:.5;}
.rf-fila.tbd b{font-style:italic;font-weight:500;color:var(--tinta-3);}
.rf-vacio{width:30px;height:30px;flex:none;border:1.5px dashed var(--line-2);border-radius:50%;}
.rf-f{margin-top:auto;padding:9px 14px;border-top:1px dashed var(--line);font-size:.74rem;color:var(--tinta-2);line-height:1.4;}
.rf-f .nm{font-weight:800;color:var(--tinta);}
.rf-sube{font-stretch:85%;font-size:.62rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--win);margin-right:4px;}
.rf details.tanda{margin:0 12px 10px;font-size:.72rem;}
.rf .nm[data-club]{cursor:pointer;}
.rf .nm[data-club]:hover{color:var(--cel2);text-decoration:underline;text-underline-offset:3px;}
.bt .nm[data-club]:hover{color:var(--cel2);text-decoration:underline;text-underline-offset:3px;}
/* Copa Argentina: cuadro en formato llave (tarjetas iguales y líneas que unen cada cruce) */
.kb-wrap{overflow-x:auto;padding:4px 2px 12px;margin-bottom:6px;}
.kb{display:grid;grid-template-columns:repeat(var(--cols),minmax(200px,1fr));column-gap:30px;min-width:calc(var(--cols) * 200px + (var(--cols) - 1) * 30px);}
.kb-h{text-align:center;margin-bottom:10px;}
.kb-body{display:flex;flex-direction:column;height:var(--alto);}
.kb-pair{flex:1;display:flex;flex-direction:column;position:relative;}
.kb-slot{flex:1;display:flex;align-items:center;position:relative;}
.kb-slot>*{width:100%;}
.kb-pair::after{content:"";position:absolute;right:-15px;top:25%;bottom:25%;width:14px;border:1.5px solid var(--line-2);border-left:0;border-radius:0 6px 6px 0;}
.kb-pair::before{content:"";position:absolute;right:-30px;top:50%;width:15px;border-top:1.5px solid var(--line-2);}
.kb-solo::after{content:"";position:absolute;right:-30px;top:50%;width:30px;border-top:1.5px solid var(--line-2);}
.kb-m{position:relative;border:1px solid var(--line);border-radius:6px;background:var(--papel);overflow:hidden;box-shadow:0 1px 0 var(--soft2);}
.kb-t{display:flex;align-items:center;gap:7px;height:31px;padding:0 9px;font-size:.8rem;}
.kb-t+.kb-t{border-top:1px solid var(--line);}
.kb-n{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;cursor:pointer;}
.kb-n:hover{color:var(--cel2);}
.kb-g{min-width:14px;text-align:right;font-weight:800;font-variant-numeric:tabular-nums;font-size:.9rem;}
.kb-p{font-size:.66rem;font-weight:800;color:var(--pen);}
.kb-t.win{box-shadow:inset 3px 0 0 var(--cel2);background:color-mix(in srgb,var(--cel) 7%,transparent);}
.kb-t.win .kb-n{font-weight:800;}
.kb-t.lose{opacity:.48;}
.kb-t.tbd .kb-n{font-style:italic;font-weight:500;color:var(--tinta-3);cursor:default;}
.kb-vacio{width:20px;height:20px;flex:none;border:1.5px dashed var(--line-2);border-radius:50%;}
.kb-inc{position:absolute;right:4px;top:-1px;font-size:.62rem;color:var(--lose);}
.kb-champ{border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:6px;background:var(--papel);padding:14px 10px;text-align:center;}
.kb-champ .t{font-stretch:85%;font-size:.6rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:8px;}
.kb-champ .nm{font-weight:900;font-size:.95rem;text-transform:uppercase;margin-top:6px;line-height:1.15;}
.kb-champ .s{font-size:.7rem;color:var(--tinta-2);margin-top:2px;}
.kb-champ.vacio{opacity:.55;}
.kb .logo-mini,.bt .logo-mini{flex:none;opacity:.9;}
/* palmarés histórico (Historial) */
.pal-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:12px;margin:6px 0 10px;}
.pal{border:1px solid var(--line);border-radius:6px;background:var(--papel);overflow:hidden;display:flex;flex-direction:column;}
.pal-h{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid var(--line);background:var(--soft);}
.pal-tit{font-weight:900;font-size:.9rem;flex:1;min-width:0;}
.pal-tot{font-stretch:85%;font-size:.62rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--tinta-3);white-space:nowrap;}
.pal-lista{max-height:330px;overflow-y:auto;}
.pal-f{display:flex;align-items:center;gap:9px;padding:6px 12px;border-top:1px solid var(--line);font-size:.84rem;}
.pal-f:first-child{border-top:0;}
.pal-f.oro{background:color-mix(in srgb,var(--gold) 12%,transparent);}
.pal-pos{width:20px;flex:none;text-align:right;font-weight:800;color:var(--tinta-3);font-variant-numeric:tabular-nums;}
.pal-f.oro .pal-pos{color:var(--gold);}
.pal-nm{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;cursor:pointer;}
.pal-nm:hover{color:var(--cel2);text-decoration:underline;text-underline-offset:3px;}
.pal-t{min-width:26px;text-align:right;font-weight:900;font-size:.95rem;font-variant-numeric:tabular-nums;}
.pal-mas{font-size:.66rem;font-weight:800;color:var(--win);border:1px solid color-mix(in srgb,var(--win) 45%,transparent);border-radius:3px;padding:0 5px;}
.pal-vacio{padding:12px;color:var(--tinta-3);font-size:.84rem;}
/* copas CONMEBOL: grupos y banderas */
.bandera{flex:none;border-radius:2px;box-shadow:0 0 0 1px var(--line);vertical-align:middle;margin-left:4px;}
.grp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:12px;margin:6px 0 8px;}
.grp{border:1px solid var(--line);border-radius:6px;background:var(--papel);overflow:hidden;}
.grp-h{font-stretch:85%;font-size:.66rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);padding:8px 12px;border-bottom:1px solid var(--line);background:var(--soft);}
.grp-t{width:100%;border-collapse:collapse;font-size:.8rem;}
.grp-t th{font-size:.58rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--tinta-3);padding:5px 6px;text-align:center;}
.grp-t th:nth-child(2){text-align:left;}
.grp-t td{padding:6px;text-align:center;border-top:1px solid var(--line);font-variant-numeric:tabular-nums;}
.grp-t td.gc{text-align:left;max-width:0;width:100%;}
.grp-t .gcw{display:flex;align-items:center;gap:6px;min-width:0;}
.grp-t td.gc .nm{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;cursor:pointer;}
.grp-t td.gp{width:22px;color:var(--tinta-3);font-weight:700;}
.grp-t td.gpts{font-weight:900;}
.grp-t tr.oct td.gp{box-shadow:inset 3px 0 0 var(--win);}
.grp-t tr.oct{background:color-mix(in srgb,var(--win) 9%,transparent);}
.grp-t tr.sud td.gp{box-shadow:inset 3px 0 0 var(--cel2);}
.grp-t tr.sud{background:color-mix(in srgb,var(--cel) 9%,transparent);}
.grp-ley{display:flex;gap:16px;flex-wrap:wrap;font-size:.74rem;color:var(--tinta-2);margin-bottom:10px;}
.grp-ley i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;}
.grp-ley i.oct{background:var(--win);} .grp-ley i.sud{background:var(--cel2);}
/* avisos: suspensiones y sanciones */
.avisos{display:flex;flex-direction:column;gap:10px;}
.aviso{display:flex;gap:12px;border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:6px;background:var(--papel);padding:10px 14px;}
.aviso.grave{border-left-color:var(--lose);}
.aviso.gravisimo{border-left-color:var(--lose);background:color-mix(in srgb,var(--lose) 8%,var(--papel));}
.av-ico{font-size:1.4rem;line-height:1.2;}
.av-cuerpo{min-width:0;flex:1;}
.av-meta{font-size:.68rem;font-weight:700;color:var(--tinta-3);text-transform:uppercase;letter-spacing:.06em;display:flex;align-items:center;gap:4px;flex-wrap:wrap;}
.av-tit{font-weight:900;font-size:.98rem;margin-top:3px;}
.av-partido{font-size:.8rem;font-weight:700;margin-top:4px;display:flex;align-items:center;gap:5px;flex-wrap:wrap;}
.av-partido span{color:var(--tinta-3);font-weight:500;}
.av-txt{font-size:.82rem;color:var(--tinta-2);margin-top:4px;line-height:1.4;}
.av-sancion{font-size:.78rem;font-weight:700;margin-top:6px;color:var(--lose);}
.aviso:not(.grave) .av-sancion{color:var(--tinta-2);}
.aviso-banner{display:flex;align-items:center;gap:10px;border:1px solid color-mix(in srgb,var(--lose) 45%,transparent);background:color-mix(in srgb,var(--lose) 9%,transparent);border-radius:6px;padding:8px 12px;margin:6px 0 4px;font-size:.84rem;}
.aviso-banner b{font-weight:900;}
.inc-badge{font-size:.7rem;font-weight:800;color:var(--lose);border:1px solid color-mix(in srgb,var(--lose) 45%,transparent);border-radius:3px;padding:0 5px;}
.m-dia{font-size:.72rem;font-weight:700;color:var(--tinta-2);text-transform:capitalize;margin-left:4px;}
/* calendario */
.cal{display:flex;flex-direction:column;gap:8px;}
.cal-dia{display:flex;gap:12px;border:1px solid var(--line);border-radius:6px;background:var(--papel);padding:8px 12px;}
.cal-dia.jugado{opacity:.78;}
.cal-dia.hoy{border-color:var(--cel2);box-shadow:inset 3px 0 0 var(--cel2);}
.cal-num{width:44px;flex:none;text-align:center;}
.cal-num b{display:block;font-size:1.35rem;font-weight:900;line-height:1.1;}
.cal-num span{font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:var(--tinta-3);}
.cal-ev{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;}
.cal-comp summary{display:flex;align-items:center;gap:8px;cursor:pointer;font-size:.84rem;padding:3px 0;list-style:none;flex-wrap:wrap;}
.cal-comp summary::-webkit-details-marker{display:none;}
.cal-comp summary::before{content:"▸";color:var(--tinta-3);font-size:.7rem;width:8px;}
.cal-comp[open] summary::before{content:"▾";}
.cal-rot{color:var(--tinta-2);font-size:.78rem;}
.cal-est{margin-left:auto;font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--tinta-3);border:1px solid var(--line-2);border-radius:3px;padding:1px 6px;}
.cal-est.ok{color:var(--win);border-color:color-mix(in srgb,var(--win) 50%,transparent);}
.cal-ps{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:2px 18px;padding:6px 0 8px 16px;}
.cal-p{display:grid;grid-template-columns:minmax(0,1fr) 52px minmax(0,1fr);align-items:center;gap:6px;font-size:.78rem;padding:3px 0;border-bottom:1px dashed var(--line);}
.cal-p .cl{text-align:right;justify-self:end;display:flex;align-items:center;gap:5px;min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}
.cal-p .cv{display:flex;align-items:center;gap:5px;min-width:0;overflow:hidden;white-space:nowrap;}
.cal-p .cs{text-align:center;font-weight:800;font-variant-numeric:tabular-nums;}
.cal-p .cs i{font-style:normal;color:var(--lose);margin-left:2px;}
.cal-p .cn{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.cal-p .cs small{display:block;font-size:.62rem;color:var(--pen);font-weight:800;line-height:1;}
.cal-p .crest-img,.cal-p .crest{flex:none;}
.cal-vacio{font-size:.78rem;color:var(--tinta-3);padding:4px 0 6px 16px;}
.logo-comp{vertical-align:middle;object-fit:contain;}
/* escudos oscuros (p. ej. Central Norte): contorno claro para que se vean en modo oscuro */
:root[data-tema="oscuro"] .crest-img.crest-osc{filter:drop-shadow(0 0 .7px rgba(255,255,255,.9)) drop-shadow(0 0 .7px rgba(255,255,255,.6));}
@media (prefers-color-scheme:dark){:root:not([data-tema]) .crest-img.crest-osc{filter:drop-shadow(0 0 .7px rgba(255,255,255,.9)) drop-shadow(0 0 .7px rgba(255,255,255,.6));}}
/* menús de Ligas y Copas: logos en las pestañas */
[role="tab"] img{height:22px !important;width:22px !important;max-height:none !important;object-fit:contain;margin-right:7px;vertical-align:middle;}
.st-key-menu_ligas>[data-testid="stTabs"]>div>[role="tablist"],.st-key-menu_copas>[data-testid="stTabs"]>div>[role="tablist"]{background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:0 10px;margin-top:-4px;}
.catgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}
/* ---------- entrada suave del contenido al cambiar de pestaña ---------- */
.stTabs [role="tabpanel"]>div{animation:afa-in .45s var(--ease) both;}
@keyframes afa-in{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}
/* ---------- tablet y notebooks chicas: la cabecera no entra en una fila ---------- */
@media (min-width:641px) and (max-width:1180px){
.masthead{flex-direction:column;align-items:stretch;gap:14px;margin-top:34px;}
.mh-der{align-items:stretch;}
.mh-tabla{flex:1;display:grid;grid-template-columns:repeat(8,minmax(0,1fr));overflow:visible;border-top:1px solid var(--line);}
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
.round.last .round-b{display:flex;flex-direction:column;align-items:stretch;gap:14px;max-width:560px;}
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
/* cabecera en celular: Temporada y Partidos arriba, las 6 categorías en dos filas de 3 */
.mh-tabla{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));overflow:visible;border-top:1px solid var(--line);}
.mh-c,.mh-c:first-child{grid-column:span 2;min-width:0;padding:8px 6px 7px 8px;border-top:1px solid var(--line);}
.mh-c.temp,.mh-c:last-child{grid-column:span 3;border-top:0;padding-left:10px;}
.mh-c.temp{order:-2;border-left:0;padding-left:0;}
.mh-c:last-child{order:-1;}
.mh-c:nth-child(2),.mh-c:nth-child(5){border-left:0;padding-left:0;}
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
.mh-c:nth-child(2),.mh-c:nth-child(5){padding-left:0;}
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
