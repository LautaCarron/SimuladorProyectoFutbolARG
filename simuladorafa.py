"""
Simulador del fútbol argentino: Primera División + Categorías de Ascenso
-------------------------------------------------------------------------------
Ejecutar con:
    python -m pip install streamlit numpy pandas
    python -m streamlit run simuladorafa.py

PRIMERA DIVISIÓN (30 equipos)
  * Fase 1: todos contra todos, 29 fechas (una vuelta).
  * Fase 2: tres zonas de 10 según la tabla (Campeonato 1-10, Intermedia 11-20,
    Descenso 21-30), 9 fechas dentro de la zona con localía invertida.
  * Destinos: 1-5 Libertadores · 6-8 Sudamericana · 11 Fase previa Libertadores
    · 12-13 Sudamericana · 28-30 descienden · 27° juega la PROMOCIÓN.

PRIMERA NACIONAL (36 equipos)
  * Fase 1: 2 zonas de 18 (A y B), una sola rueda (17 fechas) + 8 fechas
    interzonales cruzadas entre ambas zonas antes de pasar a la fase 2.
  * Se reparten en 3 zonas de 12 y CONSERVAN los puntos acumulados:
      Campeonato: 1°-6° de cada zona · Intermedia: 7°-12° de cada zona
      Descenso: 13°-18° de cada zona.  Una sola rueda en cada una.
  * Campeonato: 1° campeón + ascenso · 2° ascenso · 3°-4° a cuartos del reducido
    · 5°-12° a octavos.   Intermedia: 1°-4° a octavos.
    Descenso: los 6 últimos descienden (al Federal A o Primera B según afiliación).
  * Reducido (14 equipos): a partido único. Localía y ventaja para el mejor
    ubicado. Final en cancha neutral con penales.
  * El campeón del reducido asciende. El perdedor de la final juega la PROMOCIÓN
    contra el 27° de Primera.

FEDERAL A (Equipos indirectamente afiliados)
  * Fase 1: 5 grupos por cercanía geográfica (Norte, Centro, Buenos Aires,
    Patagonia y Cuyo), ida y vuelta.
  * Fase 2: Pasan los 4 primeros de cada grupo a la Zona Campeonato (20 equipos).
    El resto a Zona Descenso. Puntos de vuelta a 0, una sola rueda.
  * Ascensos: 1°, 2° y 3° de la Zona Campeonato ascienden directo.
  * Reducido: Del 4° al 8° juegan eliminatorias a partido único por el cuarto
    ascenso a la Primera Nacional.

PRIMERA B (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera Nacional.
  * del 18 al ultimo bajan a la Primera C, si el campeonato son menos de
    18 equipos no hay descensos.

PRIMERA C (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera B.

Cada equipo tiene una "media interna" (fuerza) que cambia cada temporada.
Los partidos se simulan con goles Poisson y cada equipo tiene una "forma del
día" aleatoria: cuanto mayor es el nivel de sorpresas, más seguido gana el
que tiene menos media.
"""

import streamlit as st

st.set_page_config(page_title="Proyecto AFA · Simulador Fútbol Argentino", page_icon="⚽", layout="wide",
                   initial_sidebar_state="collapsed")

import sys

import numpy as np
import pandas as pd


from datos import (
    ESCUDOS,
    F_GRUPOS_NOMBRES,
    N,
    origen,
)
from motor import (
    MAX_R,
    MIN_R,
)
from torneos import (
    B_F1,
    B_F2,
    B_RED,
    B_TOTAL,
    B_ZONAS2,
    FECHAS_F1,
    TOTAL_FECHAS,
    VERSION_ESTADO,
    ZONAS,
    crear_estado,
    nueva_temporada,
    primera_terminada,
    simular_fecha,
    simular_fecha_b,
    simular_fecha_f,
    simular_fecha_liga,
    tabla_b_f1,
    tabla_b_f2,
    tabla_f_f2,
    tabla_f_grupo,
    tabla_final,
    tabla_general,
    tabla_pb,
    tabla_pc,
    tabla_zona,
    total_b,
    total_primera,
    tabla_reg,
)
from vista import (
    COLORES_B,
    COLORES_F,
    COLORES_ZONA,
    CSS,
    LEY_B,
    LEY_DESTINOS,
    LEY_F,
    LEY_ZONAS,
    aviso,
    barra_estado,
    bracket_html,
    bracket_html_f,
    chip,
    colorear_b,
    colorear_destino,
    colorear_f,
    colorear_fase1,
    colorear_pb,
    colorear_pc,
    crest,
    esc,
    fila_partido_html,
    leyenda,
    lista_equipos_html,
    mostrar_tabla,
    tabla_html,
    norm,
    render_ficha,
    render_movimientos,
    seccion,
    ver_equipo,
    vista_fixture,
)


def editar_medias(nombres, r, clave):
    """Editor de medias internas. En la versión web (stlite, corre en el navegador)
    st.data_editor no funciona, así que ahí se edita club por club."""
    if sys.platform != "emscripten":
        ed = st.data_editor(pd.DataFrame({"Equipo": nombres, "Media": r}),
                            disabled=["Equipo"], hide_index=True, width="stretch", key=clave)
        return np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
    r = np.array(r, dtype=float)
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    i = c1.selectbox("Club", range(len(nombres)), format_func=lambda k: nombres[k],
                     key=f"{clave}_club")
    r[i] = c2.number_input("Media", MIN_R, MAX_R, float(round(r[i], 1)), 0.5,
                           key=f"{clave}_media_{i}")
    return r


# ----------------------------------------------------------------------------
# INTERFAZ
# ----------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.header("Parámetros de simulación")
    sorpresa = st.slider("Nivel de sorpresas", 0.0, 15.0, 6.0, 0.5,
                         help="Qué tanto varía la 'forma del día' de cada equipo. "
                              "Más alto = más partidos donde gana el que tiene menos media.")
    volatilidad = st.slider("Volatilidad entre temporadas", 0.0, 10.0, 4.0, 0.5,
                            help="Qué tanto cambia la media de cada equipo al pasar de temporada.")
    acumular = st.checkbox("Arrastrar puntos de la fase 1 a las zonas (Primera)", value=True,
                           help="Solo Primera. Si está activado, las zonas parten con lo sumado en "
                                "las 29 fechas. Si no, cada zona arranca de cero. Se fija al "
                                "terminar la fase 1. (En la B Nacional ahora los puntos se conservan siempre).")
    st.caption("En cada partido, cada equipo rinde un poco mejor o peor que su "
               "media habitual. Los partidos del reducido y la promoción son a un solo "
               "partido y, si empatan, se definen por penales.")

P = dict(sorpresa=sorpresa)


if "S" not in st.session_state or st.session_state.S.get("version") != VERSION_ESTADO:
    st.session_state.S = crear_estado()
S = st.session_state.S
SB, SF, SPB, SPC = S["b"], S["f"], S["pb"], S["pc"]

terminada = primera_terminada(S)            # incluye las fechas de desempate
terminada_b = SB["fecha"] >= total_b(SB)
terminada_f = SF["fecha"] >= SF["total"]
terminada_pb = SPB["fecha"] >= SPB["total"]
terminada_pc = SPC["fecha"] >= SPC["total"]
ambas = terminada and terminada_b and terminada_f and terminada_pb and terminada_pc
b_espera_primera = SB["fecha"] == total_b(SB) - 1 and not terminada

pct_p = 100 * S["fecha"] / total_primera(S)
pct_b = 100 * SB["fecha"] / total_b(SB)
pct_f = 100 * SF["fecha"] / SF["total"]
pct_pb = 100 * SPB["fecha"] / SPB["total"] if SPB["total"] else 0
pct_pc = 100 * SPC["fecha"] / SPC["total"] if SPC["total"] else 0

# ---- Cabecera (masthead) · Proyecto AFA
# Sol de Mayo geométrico: 16 rayos alternando largo (mismo dibujo que la intro)
_RAYOS = "".join(
    f'<polygon points="-3.2,-21 0,-{36 if k % 2 else 47} 3.2,-21" transform="rotate({k * 22.5})"/>'
    for k in range(16))
SOL_SVG = (f'<svg viewBox="-50 -50 100 100" aria-hidden="true"><g fill="currentColor">{_RAYOS}'
           f'<circle r="16.5"/></g></svg>')


def _celda(nombre, fecha, total, pct):
    return (f'<div class="mh-c"><span>{nombre}</span><b>{fecha}/{total}</b>'
            f'<div class="bar"><i style="width:{pct:.1f}%"></i></div></div>')


# En la web el tema claro/oscuro lo maneja la intro (index.html): este botón le avisa.
_BOTON_TEMA = (
    '<a class="mh-tema" href="#tema" title="Cambiar entre modo claro y oscuro" '
    'aria-label="Cambiar entre modo claro y oscuro">'
    '<svg class="sol-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<circle cx="8" cy="8" r="3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13'
    'M3 13l1.4-1.4M11.6 4.4L13 3"/></svg>'
    '<svg class="luna" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">'
    '<path d="M13.5 9.8A6 6 0 0 1 6.2 2.5a6 6 0 1 0 7.3 7.3z"/></svg></a>')

# En la web (stlite) la marca vuelve a la intro de Proyecto AFA; en la PC no hay intro
_web = sys.platform == "emscripten"
_marca_tag = ('a class="mh-marca" href="#inicio" title="Volver al inicio de Proyecto AFA"'
              if _web else 'div class="mh-marca"')
_jugados = len(S["log"]) + len(SB["log"]) + len(SF["log"]) + len(SPB["log"]) + len(SPC["log"])
st.markdown(
    f'<header class="masthead"><{_marca_tag}>{SOL_SVG}<div><b>Proyecto AFA</b>'
    f'<span>Simulador Fútbol Argentino</span></div></{"a" if _web else "div"}>'
    f'<div class="mh-der"><div class="mh-tabla">'
    f'<div class="mh-c temp"><span>Temporada</span><b>{S["temp"]}</b></div>'
    + _celda("Primera", S["fecha"], total_primera(S), pct_p)
    + _celda("B Nacional", SB["fecha"], total_b(SB), pct_b)
    + _celda("Federal A", SF["fecha"], SF["total"], pct_f)
    + _celda("Primera B", SPB["fecha"], SPB["total"], pct_pb)
    + _celda("Primera C", SPC["fecha"], SPC["total"], pct_pc)
    + f'<div class="mh-c"><span>Partidos</span><b>{_jugados}</b></div></div>'
    + (_BOTON_TEMA if _web else "")
    + '</div></header>', unsafe_allow_html=True)

g0, g1, g2, g3 = st.container(key="acciones").columns([2.2, 1.3, 1.5, 1.1], vertical_alignment="center")
g0.caption("Avanzá fecha por fecha en cada categoría, o simulá todo junto.")
if g1.button(":material/fast_forward: Simular todo", disabled=ambas, width="stretch", type="primary"):
    # 1. Primero terminar Primera División, desempates incluidos
    #    (la B necesita saber el 27° definitivo para la Promoción)
    while not primera_terminada(S):
        simular_fecha(S, P, acumular)
        
    # 2. Ahora sí corre la B Nacional hasta el final sin trabarse
    while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
        simular_fecha_b(S, P)
        
    # 3. Resto de las categorías
    while SF["fecha"] < SF["total"]: 
        simular_fecha_f(SF, P, S["rng"])
    while SPB["fecha"] < SPB["total"]: 
        simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
    while SPC["fecha"] < SPC["total"]: 
        simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
    st.rerun()
if g2.button(":material/event_repeat: Nueva temporada", disabled=not ambas, width="stretch"):
    nueva_temporada(S, volatilidad)
    st.rerun()
if g3.button(":material/restart_alt: Reiniciar", width="stretch"):
    st.session_state.S = crear_estado()
    st.rerun()

tab_p, tab_b, tab_f, tab_pb, tab_pc, tab_c, tab_h = st.tabs([
    "Primera", "B Nacional", "Federal A", "Primera B", "Primera C", "Clubes", "Historial"
])

# (Esto va debajo de los imports y la configuración inicial de streamlit)

def html_tabla_liguilla(partidos):
    stats = {}
    for p in partidos:
        # Atrapamos "local" o "l", y "visita" o "v"
        l = p.get("local") or p.get("l")
        v = p.get("visita") or p.get("visitante") or p.get("v")
        gl = p.get("gl", 0)
        gv = p.get("gv", 0)
        gana = p.get("gana")
        
        # Inicializa los equipos si no existen
        for eq in (l, v):
            if eq not in stats: stats[eq] = {"Pts": 0, "PJ": 0, "G": 0, "P": 0, "GF": 0, "GC": 0, "DG": 0}
        
        stats[l]["PJ"] += 1; stats[v]["PJ"] += 1
        stats[l]["GF"] += gl; stats[l]["GC"] += gv
        stats[v]["GF"] += gv; stats[v]["GC"] += gl
        
        # Asigna los 3 puntos al que ganó (sea en 90 mins o penales)
        if gana == l: stats[l]["Pts"] += 3; stats[l]["G"] += 1; stats[v]["P"] += 1
        elif gana == v: stats[v]["Pts"] += 3; stats[v]["G"] += 1; stats[l]["P"] += 1
        
        stats[l]["DG"] = stats[l]["GF"] - stats[l]["GC"]
        stats[v]["DG"] = stats[v]["GF"] - stats[v]["GC"]
        
    # Convertimos a lista y ordenamos por Pts, DG y GF
    lista = [{"Club": k, **v} for k, v in stats.items()]
    lista.sort(key=lambda x: (x["Pts"], x["DG"], x["GF"]), reverse=True)
    
    # Construimos el HTML visual (colores del tema: se lee bien en claro y en oscuro)
    html = '<div class="liguilla-wrap"><table class="liguilla">'
    html += ('<tr><th>Pos</th><th class="club">Club</th><th>Pts</th><th>PJ</th><th>G</th><th>P</th>'
             '<th>GF</th><th>GC</th><th>DG</th></tr>')
    for i, row in enumerate(lista):
        html += '<tr>'
        html += f'<td class="pos">{i+1}</td>'
        html += f'<td class="club"><span>{crest(row["Club"], 24)} {esc(row["Club"])}</span></td>'
        html += f'<td class="pts">{row["Pts"]}</td>'
        html += f'<td>{row["PJ"]}</td><td>{row["G"]}</td><td>{row["P"]}</td>'
        html += f'<td>{row["GF"]}</td><td>{row["GC"]}</td><td>{row["DG"]:+d}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html


# ============================================================================
# PRIMERA DIVISIÓN
# ============================================================================
with tab_p:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip("Liga Profesional · 30 equipos", "#1e5aa8") + " " +
                chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                unsafe_allow_html=True)
                
    extra_p = S.get("extra_f2", 0)
    terminada_p_dyn = S["fecha"] >= TOTAL_FECHAS + extra_p
    
    if c2.button(":material/skip_next: Próxima fecha", key="p_next", disabled=terminada_p_dyn, width="stretch",
                 type="primary"):
        simular_fecha(S, P, acumular)
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key="p_all", disabled=terminada_p_dyn, width="stretch"):
        while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0):
            simular_fecha(S, P, acumular)
        st.rerun()

    jugados = int(S["pj"].sum() // 2)
    pct = 100 * S["sorpresas"] / jugados if jugados else 0
    pct_p = 100 * S["fecha"] / (TOTAL_FECHAS + extra_p) if (TOTAL_FECHAS + extra_p) else 0
    
    barra_estado([("Fase", "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"),
                  ("Fecha", f"{S['fecha']} / {TOTAL_FECHAS + extra_p}"),
                  ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)
                  
    if S["fase"] == 2 and S["fecha"] == FECHAS_F1:
        aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
              "Las 9 fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

    desempates_p = [p for p in S["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate_p = S.get("desempate_pendiente") or len(desempates_p) > 0
    
    titulos_p = ["Posiciones", "Fixture y resultados"]
    if mostrar_desempate_p: titulos_p.append("Desempate")
    titulos_p.extend(["Movimientos", "Definiciones"])
    
    sp = st.tabs(titulos_p)
    idx_p = 0
    
    with sp[idx_p]:
        if S["fase"] == 1:
            seccion("Tabla de posiciones", "Fase 1 · 29 fechas, todos contra todos", "#475569")
            mostrar_tabla(tabla_general(S), colorear_fase1, S["pos_hist"])
            leyenda(LEY_ZONAS)
        else:
            seccion("Fase 2 · Zonas", "9 fechas dentro de cada zona, localía invertida", "#16a34a")
            tabs = st.tabs([f"Zona {n}" for n in ZONAS] + ["Tabla fase 1"])
            for z, tab in enumerate(tabs[:3]):
                with tab:
                    mostrar_tabla(tabla_zona(S, z), colorear_destino, S["pos_hist"])
            with tabs[3]:
                mostrar_tabla(S["tabla_f1"], colorear_fase1)
                st.caption("Tabla final de las 29 fechas de la fase 1.")
            leyenda(LEY_DESTINOS + [("Desempate Campeonato", "rgba(249, 115, 22, 0.3)"), ("Desempate Permanencia/Promoción", "rgba(147, 51, 234, 0.3)")])
            
        if S["fecha"] == 0:
            with st.expander(":material/tune: Editar medias internas de esta temporada"):
                S["r"] = editar_medias(S["nombres"], S["r"], f"editor_p_{S['temp']}")
    idx_p += 1
    
    with sp[idx_p]:
        vista_fixture("p")
    idx_p += 1
    
    if mostrar_desempate_p:
        with sp[idx_p]:
            if S.get("desempate_pendiente"):
                seccion("Desempate en Primera", "Están empatados en puntos críticos. Jugarán un desempate.", "#9333ea")
                for z in [0, 2]:
                    df_des = tabla_zona(S, z)
                    df_des = df_des[df_des["id"].isin(S.get("ids_desempate", []))]
                    if not df_des.empty:
                        mostrar_tabla(df_des, colorear_destino)
            else:
                grupos = {}
                for p in desempates_p:
                    m = p["comp"]
                    if m not in grupos: grupos[m] = []
                    grupos[m].append(p)
                
                for motivo, parts in grupos.items():
                    if "Liguilla" in motivo:
                        seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx_p += 1
        
    with sp[idx_p]:
        render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")
    idx_p += 1
    
    with sp[idx_p]:
        seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
        if not terminada_p_dyn:
            aviso("Las definiciones aparecen acá cuando termina la temporada de Primera. "
                  "Destinos: 1°-5° Libertadores · 6°-8° y 12°-13° Sudamericana · 11° fase previa "
                  "de Libertadores · 27° Promoción · 28°-30° descienden.")
        else:
            final = tabla_final(S)
            def equipos(posiciones):
                sel = final[final["Pos"].isin(list(posiciones))]
                return lista_equipos_html([(r.Equipo, f"{r.Pos}°") for r in sel.itertuples()])

            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            e1, e2 = st.columns(2)
            with e1:
                with st.expander(":material/emoji_events: Campeón de Primera División", expanded=False):
                    campeon = final.iloc[0]["Equipo"]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(campeon, 64)}</div>'
                                f'<div class="nm">{esc(campeon)}</div></div>', unsafe_allow_html=True)
                with st.expander(":material/public: Clasificados · Copa Libertadores", expanded=False):
                    st.markdown('<div class="mlab">Fase de grupos (1° al 5°)</div>'
                                + equipos(range(1, 6)) + '<div class="mlab">Fase previa (11°)</div>'
                                + equipos([11]), unsafe_allow_html=True)
                with st.expander(":material/public: Copa Sudamericana", expanded=False):
                    st.markdown('<div class="mlab">6° al 8° y 12°-13°</div>'
                                + equipos(list(range(6, 9)) + [12, 13]), unsafe_allow_html=True)
            with e2:
                with st.expander(":material/swap_vert: Promoción", expanded=False):
                    txt = ('<div class="mlab">Juega la Promoción contra el perdedor de la final '
                           'del reducido (27°)</div>' + equipos([N - 3]))
                    if SB["promo_partido"]:
                        txt += fila_partido_html(SB["promo_partido"])
                    st.markdown(txt, unsafe_allow_html=True)
                with st.expander(":material/south: Descensos", expanded=False):
                    st.markdown('<div class="mlab">Descienden a la Primera Nacional (28° al 30°)</div>'
                                + equipos(range(N - 2, N + 1)), unsafe_allow_html=True)

# -----------------
# Recordá que, ARRIBA DE TODO, el botón general ("Simular todo") 
# debe arrancar así para leer el alargue:
# while S["fecha"] < TOTAL_FECHAS + S.get("extra_f2", 0): 
#     simular_fecha(S, P, acumular)

# ============================================================================
# PRIMERA NACIONAL
# ============================================================================
with tab_b:
    fb = SB["fecha"]
    nom_b = SB["nombres"]
    extra = SB.get("extra_f2", 0)  # Offset dinámico por si se alarga con un desempate
    
    if fb < B_F1:
        fase_txt = "1 · Zonas A y B"
    elif fb < B_F1 + B_F2 + extra:
        if fb < B_F1 + B_F2:
            fase_txt = "2 · Tres zonas"
        else:
            fase_txt = "Desempate"
    elif fb < B_F1 + B_F2 + extra + B_RED:
        fase_txt = "Reducido"
    elif fb < B_TOTAL + extra:
        fase_txt = "Promoción"
    else:
        fase_txt = "Terminada"

    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip("Primera Nacional · 36 equipos") + " " + chip(f"Fase {fase_txt}", "#475569"),
                unsafe_allow_html=True)
    
    if c2.button(":material/skip_next: Próxima fecha", key="b_next", width="stretch", type="primary",
                 disabled=terminada_b or b_espera_primera):
        simular_fecha_b(S, P)
        st.rerun()
        
    if c3.button(":material/fast_forward: Hasta el final", key="b_all", width="stretch",
                 disabled=terminada_b or b_espera_primera):
        while SB["fecha"] < total_b(SB) and not (SB["fecha"] == total_b(SB) - 1 and not primera_terminada(S)):
            simular_fecha_b(S, P)
        st.rerun()

    pct_b_dyn = 100 * fb / (B_TOTAL + extra) if (B_TOTAL + extra) else 0
    barra_estado([("Fase", fase_txt), ("Fecha", f"{fb} / {B_TOTAL + extra}"),
                  ("Partidos jugados", len(SB["log"]))], pct_b_dyn)
                  
    if b_espera_primera:
        aviso("La Promoción se juega contra el 27° de Primera: terminá primero la temporada "
              "de Primera División.")
    if fb == B_F1:
        aviso("Terminó la fase 1: se repartieron los equipos en las zonas Campeonato, "
              "Intermedia y Descenso y <b>se conservan todos los puntos acumulados</b>.")
    if fb == B_F1 + B_F2 + extra:
        aviso("Terminó la fase 2 y sus definiciones: quedaron definidos los 12 clasificados al reducido. "
              "Mirá el cuadro en la pestaña <b>Reducido</b>.")

    # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
    desempates_b = [p for p in SB["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate_b = SB.get("desempate_pendiente") or len(desempates_b) > 0
    
    titulos_b = ["Posiciones", "Fixture y resultados"]
    if mostrar_desempate_b: titulos_b.append("Desempate")
    titulos_b.extend(["Reducido", "Movimientos", "Definiciones"])
    
    sb = st.tabs(titulos_b)
    idx_b = 0
    
    with sb[idx_b]:
        if fb < B_F1:
            seccion("Fase 1 · Zonas A y B", "Una rueda + 8 fechas interzonales · 18 equipos por zona", "#4f46e5")
            tabs_b = st.tabs(["Zona A", "Zona B"])
            for z, tab in enumerate(tabs_b):
                with tab:
                    mostrar_tabla(tabla_b_f1(SB, z), colorear_b, SB["pos_hist"])
            leyenda([("1°-6° → Zona Campeonato", COLORES_ZONA[0]),
                     ("7°-12° → Zona Intermedia", COLORES_ZONA[1]),
                     ("13°-18° → Zona Descenso", COLORES_ZONA[2])])
        else:
            seccion("Fase 2 · Zonas", "Arrastran los puntos de la Fase 1 · una rueda por zona", "#16a34a")
            tabs_b = st.tabs([f"Zona {n}" for n in B_ZONAS2] + ["Fase 1"])
            for z in range(3):
                with tabs_b[z]:
                    mostrar_tabla(tabla_b_f2(SB, z), colorear_b, SB["pos_hist"])
            with tabs_b[3]:
                for z, nz in enumerate(["Zona A", "Zona B"]):
                    st.markdown(chip(nz), unsafe_allow_html=True)
                    mostrar_tabla(SB["tablas_f1"][z], colorear_b)
                st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
            leyenda(LEY_B + [("Desempate Permanencia", "rgba(147, 51, 234, 0.3)")])
            
        with st.expander(":material/info: Formato de la Primera Nacional"):
            st.markdown(
                "Fase 1: dos zonas de 18, una rueda, más 8 fechas interzonales (localía fija "
                "4 y 4) cruzando ambas zonas. "
                "Después, conservando los puntos acumulados, se arman "
                "Campeonato, Intermedia y Descenso (12 cada una), una rueda cada una "
                "(si dos equipos ya se cruzaron en la fase 1, la revancha es con la localía "
                "invertida). Campeonato: 1° campeón y ascenso, 2° ascenso, 3°-4° a cuartos, "
                "5°-12° a octavos. Intermedia: 1°-4° a octavos. Descenso: bajan los 6 últimos. "
                "Reducido a partido único con penales directos; el campeón asciende y el perdedor "
                "de la final juega la promoción contra el 27° de Primera.")
                
        if fb == 0:
            with st.expander(":material/tune: Editar medias internas de esta temporada (Primera Nacional)"):
                SB["r"] = editar_medias(SB["nombres"], SB["r"], f"editor_b_{S['temp']}")
    idx_b += 1
    
    with sb[idx_b]: 
        vista_fixture("b")
    idx_b += 1
    
    if mostrar_desempate_b:
        with sb[idx_b]:
            if SB.get("desempate_pendiente"):
                seccion("Desempate por el Descenso", "Jugarán un desempate por la permanencia.", "#9333ea")
                df_des = tabla_b_f2(SB, 2)
                df_des = df_des[df_des["id"].isin(SB["ids_desempate"])]
                mostrar_tabla(df_des, colorear_b)
            else:
                grupos = {}
                for p in desempates_b:
                    m = p["comp"]
                    if m not in grupos: grupos[m] = []
                    grupos[m].append(p)
                
                for motivo, parts in grupos.items():
                    if "Liguilla" in motivo:
                        seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx_b += 1

    with sb[idx_b]:
        seccion("Reducido por el tercer ascenso",
                "Octavos → Cuartos → Semifinal → Final · partido único, penales si empatan · "
                "L = local, V = visitante, N = neutral", "#2563eb")
        if fb < B_F1 + B_F2 + extra:
            aviso("El cuadro se completa al terminar la fase 2 y sus posibles desempates. Entran 3°-4° de Zona Campeonato "
                  "(directo a cuartos), 5°-12° de Campeonato y 1°-4° de Intermedia (octavos).")
        st.markdown(bracket_html(SB), unsafe_allow_html=True)
        if SB["entrantes"] is not None:
            with st.expander("Clasificados al reducido (orden de mérito)"):
                st.markdown(tabla_html(SB["entrantes"]), unsafe_allow_html=True)
    idx_b += 1
    
    with sb[idx_b]:
        render_movimientos(SB["log"], SB["pos_hist"], nom_b, "#0f766e")
    idx_b += 1
        
    with sb[idx_b]:
        seccion("Definiciones de la temporada", "Campeón, ascensos, promoción y descensos",
                "#b7860b")
        if SB["campeon"] is None:
            aviso("Las definiciones aparecen acá cuando termina la fase 2 de la Primera Nacional.")
        else:
            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            e1, e2 = st.columns(2)
            with e1:
                with st.expander(":material/emoji_events: Campeón de la Primera Nacional", expanded=False):
                    cb = nom_b[SB["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                f'<div class="nm">{esc(cb)}</div><div class="s">Asciende a Primera'
                                f'</div></div>', unsafe_allow_html=True)
                with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                    asc = [(nom_b[SB["asc_directo"][0]], "campeón"), (nom_b[SB["asc_directo"][1]], "2°")]
                    if SB["asc_reducido"] is not None:
                        asc.append((nom_b[SB["asc_reducido"]], "reducido"))
                    if SB["promo"] and SB["promo"]["gana_b"]:
                        asc.append((nom_b[SB["promo"]["b_id"]], "promoción"))
                    st.markdown(lista_equipos_html(asc) + (
                        '' if SB["asc_reducido"] is not None else
                        '<div style="font-size:.8rem;opacity:.65">El tercer ascenso sale del '
                        'reducido.</div>'), unsafe_allow_html=True)
            with e2:
                with st.expander(":material/swap_vert: Promoción", expanded=False):
                    if SB["promo_partido"]:
                        st.markdown(fila_partido_html(SB["promo_partido"], abierto=True),
                                    unsafe_allow_html=True)
                    elif SB["perdedor_final"] is not None:
                        st.markdown('<div class="mlab">Juega la promoción (perdedor de la final)</div>'
                                    + lista_equipos_html([(nom_b[SB["perdedor_final"]], "")]),
                                    unsafe_allow_html=True)
                    else:
                        st.caption("La juega el perdedor de la final del reducido contra el 27° "
                                   "de Primera.")
                with st.expander(":material/south: Descensos", expanded=False):
                    st.markdown(
                        '<div class="mlab">Descienden (7° al 12° de Zona Descenso): al Federal '
                        'A los del interior, a la Primera B los metropolitanos</div>'
                        + lista_equipos_html([
                            (nom_b[i], "Federal A" if origen(nom_b[i]) == "Interior" else "Primera B")
                            for i in SB["desc_b"]
                        ]), unsafe_allow_html=True)

# ============================================================================
# FEDERAL A
# ============================================================================
with tab_f:
    ff = SF["fecha"]
    nom_f = SF["nombres"]
    if ff < SF["f1_rondas"]:
        fase_txt_f = "1 · Grupos por cercanía"
    elif ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
        fase_txt_f = "2 · Campeonato y Descenso"
    elif ff < SF["total"]:
        fase_txt_f = "Reducido"
    else:
        fase_txt_f = "Terminada"

    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Federal A · {len(nom_f)} equipos") + " " +
                chip(f"Fase {fase_txt_f}", "#475569"), unsafe_allow_html=True)
    if c2.button(":material/skip_next: Próxima fecha", key="f_next", width="stretch", type="primary",
                 disabled=terminada_f):
        simular_fecha_f(SF, P, S["rng"])
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key="f_all", width="stretch", disabled=terminada_f):
        while SF["fecha"] < SF["total"]:
            simular_fecha_f(SF, P, S["rng"])
        st.rerun()

    barra_estado([("Fase", fase_txt_f), ("Fecha", f"{ff} / {SF['total']}"),
                  ("Partidos jugados", len(SF["log"]))], pct_f)
                  
    if ff == SF["f1_rondas"]:
        aviso("Terminó la fase 1: clasificaron los 4 primeros de cada grupo (20 equipos) a Zona Campeonato, "
              "el resto a Zona Descenso, y <b>todos los puntos se reiniciaron a 0</b>.")
    if ff == SF["f1_rondas"] + SF.get("f2_rondas", 0):
        aviso("Terminó la fase 2: 1°, 2° y 3° ascendieron directo a la B Nacional. "
              "El reducido arranca con el 7° y 8°. Mirá el cuadro en la pestaña <b>Reducido</b>.")

    # ------------------ SISTEMA DE PESTAÑAS DINÁMICAS ------------------
    desempate_f = SF.get("desempate_camp")
    titulos_f = ["Posiciones", "Fixture y resultados"]
    if desempate_f: titulos_f.append("Desempate")
    titulos_f.extend(["Reducido", "Movimientos", "Definiciones"])
    tab_f = dict(zip(titulos_f, st.tabs(titulos_f)))
                       
    with tab_f["Posiciones"]:
        if ff < SF["f1_rondas"]:
            seccion("Fase 1 · Grupos por cercanía", "Ida y vuelta · pasan los 4 primeros de "
                    "cada grupo", "#4f46e5")
            tabs_f = st.tabs(F_GRUPOS_NOMBRES)
            for g, tab in enumerate(tabs_f):
                with tab:
                    mostrar_tabla(tabla_f_grupo(SF, g), colorear_f, SF["pos_hist"])
            leyenda([("1°-4° → Zona Campeonato", COLORES_F["→ Zona Campeonato"])])
        else:
            seccion("Fase 2 · Zonas", "Puntos reiniciados a 0 · una rueda por zona", "#16a34a")
            tabs_f = st.tabs(["Campeonato", "Descenso", "Fase 1"])
            with tabs_f[0]:
                mostrar_tabla(tabla_f_f2(SF, 0), colorear_f, SF["pos_hist"])
            with tabs_f[1]:
                mostrar_tabla(tabla_f_f2(SF, 1), colorear_f, SF["pos_hist"])
            with tabs_f[2]:
                for g, dfg in zip(F_GRUPOS_NOMBRES, SF["tablas_f1"]):
                    st.markdown(chip(g), unsafe_allow_html=True)
                    mostrar_tabla(dfg, colorear_f)
                st.caption("Posiciones finales de la fase 1 (sus puntos ya no cuentan).")
            leyenda(LEY_F)
            
        if ff == 0:
            with st.expander(":material/tune: Editar medias internas de esta temporada (Federal A)"):
                SF["r"] = editar_medias(nom_f, SF["r"], f"editor_f_{S['temp']}")
                
    with tab_f["Fixture y resultados"]:
        vista_fixture("f")
        
    if desempate_f:
        with tab_f["Desempate"]:
            partes = desempate_f["partidos"]
            seccion("Desempate por el campeonato",
                    f"Igualaron en puntos en el 1° puesto: {', '.join(desempate_f['equipos'])}",
                    "#9333ea")
            if len(partes) > 1:
                seccion("Tabla final: Liguilla por el campeonato",
                        "Posiciones del mini-torneo a partido único", "#9333ea")
                st.markdown(html_tabla_liguilla(partes), unsafe_allow_html=True)
                with st.expander(f":material/visibility: Ver los {len(partes)} enfrentamientos",
                                 expanded=False):
                    for p in partes:
                        st.markdown(fila_partido_html(p), unsafe_allow_html=True)
            else:
                for p in partes:
                    st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
            st.caption("El título se define con desempate en cancha neutral (penales si empatan). "
                       "El resto de las posiciones se ordena por diferencia de gol.")

    with tab_f["Reducido"]:
        seccion("Reducido por el cuarto ascenso",
                "Eliminatoria → Semifinal → Final · partido único · gana el mejor ubicado si "
                "empatan, menos en la final (cancha neutral, penales) · L = local, V = "
                "visitante, N = neutral", "#2563eb")
        if ff < SF["f1_rondas"] + SF.get("f2_rondas", 0):
            aviso("El cuadro se completa al terminar la fase 2. Entran del 4° al 8° de Zona "
                  "Campeonato.")
        st.markdown(bracket_html_f(SF), unsafe_allow_html=True)
        if SF["entrantes"] is not None:
            with st.expander("Clasificados al reducido (orden de mérito)"):
                st.markdown(tabla_html(SF["entrantes"]), unsafe_allow_html=True)
                             
    with tab_f["Movimientos"]:
        render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
        
    with tab_f["Definiciones"]:
        seccion("Definiciones de la temporada", "Campeón y ascensos a la Primera Nacional",
                "#b7860b")
        if SF["campeon"] is None:
            aviso("Las definiciones aparecen acá cuando termina la fase 2 del Federal A.")
        else:
            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            with st.expander(":material/emoji_events: Campeón del Federal A", expanded=False):
                cf = nom_f[SF["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                            f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                            f'<div class="nm">{esc(cf)}</div><div class="s">Asciende a la Primera'
                            f' Nacional</div></div>', unsafe_allow_html=True)
                if SF.get("desempate_camp"):
                    dc = SF["desempate_camp"]
                    st.markdown(f'<div class="mlab" style="margin-top:14px">Título definido por '
                                f'desempate · igualaron en puntos: {esc(", ".join(dc["equipos"]))}'
                                f'</div>' + "".join(fila_partido_html(p) for p in dc["partidos"]),
                                unsafe_allow_html=True)
            with st.expander(":material/north: Clasificados · Ascensos", expanded=False):
                asc_f = [(nom_f[SF["asc_directo"][0]], "campeón"), 
                         (nom_f[SF["asc_directo"][1]], "2°"), 
                         (nom_f[SF["asc_directo"][2]], "3°")]
                if SF["asc_reducido"] is not None:
                    asc_f.append((nom_f[SF["asc_reducido"]], "reducido"))
                st.markdown(lista_equipos_html(asc_f) + (
                    '' if SF["asc_reducido"] is not None else
                    '<div style="font-size:.8rem;opacity:.65">El cuarto ascenso sale del '
                    'reducido.</div>'), unsafe_allow_html=True)


# ============================================================================
# PRIMERA B
# ============================================================================
with tab_pb:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Primera B · {len(SPB['nombres'])} equipos") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
    if c2.button(":material/skip_next: Próxima fecha", key="pb_next", width="stretch", type="primary", disabled=terminada_pb):
        simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key="pb_all", width="stretch", disabled=terminada_pb):
        while SPB["fecha"] < SPB["total"]: 
            simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
        st.rerun()
        
    barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPB['fecha']} / {SPB['total']}"), ("Partidos jugados", len(SPB["log"]))], pct_pb)
    
    desempates = [p for p in SPB["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate = SPB.get("desempate_pendiente") or len(desempates) > 0
    
    titulos = ["Posiciones", "Fixture y resultados"]
    if mostrar_desempate: titulos.append("Desempate")
    titulos.extend(["Movimientos", "Definiciones"])
    
    spb_tabs = st.tabs(titulos)
    idx = 0
    
    with spb_tabs[idx]:
        seccion("Tabla de posiciones", "Ida y vuelta · ascienden los 2 primeros, del 18° para abajo descienden", "#4f46e5")
        mostrar_tabla(tabla_pb(SPB), colorear_pb, SPB["pos_hist"])
        leyenda([("1°-2° Ascenso a Primera Nacional", COLORES_B["Ascenso directo"]), 
                 ("Desempate Campeonato / Ascenso", "rgba(249, 115, 22, 0.3)"),
                 ("Desempate Permanencia", "rgba(147, 51, 234, 0.3)"),
                 ("18° o peor Descenso a Primera C", COLORES_B["Desciende"])])
    idx += 1
            
    with spb_tabs[idx]: vista_fixture("pb")
    idx += 1
    
    if mostrar_desempate:
        with spb_tabs[idx]:
            if SPB.get("desempate_pendiente"):
                seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.", "#9333ea")
                df_des = tabla_pb(SPB)
                df_des = df_des[df_des["id"].isin(SPB["ids_desempate"])]
                mostrar_tabla(df_des, colorear_pb)
            else:
                grupos = {}
                for p in desempates:
                    m = p["comp"]
                    if m not in grupos: grupos[m] = []
                    grupos[m].append(p)
                
                for motivo, parts in grupos.items():
                    if "Liguilla" in motivo:
                        seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx += 1
            
    with spb_tabs[idx]: render_movimientos(SPB["log"], SPB["pos_hist"], SPB["nombres"], "#0f766e")
    idx += 1
        
    with spb_tabs[idx]:
        seccion("Definiciones de la temporada", "Campeón, ascensos y descensos", "#b7860b")
        if SPB["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
        else:
            with st.expander(":material/emoji_events: Campeón de la Primera B", expanded=False):
                cpb = SPB["nombres"][SPB["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpb, 64)}</div><div class="nm">{esc(cpb)}</div></div>', unsafe_allow_html=True)
                

# ============================================================================
# PRIMERA C
# ============================================================================
with tab_pc:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Primera C · {len(SPC['nombres'])} equipos") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
    if c2.button(":material/skip_next: Próxima fecha", key="pc_next", width="stretch", type="primary", disabled=terminada_pc):
        simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
        st.rerun()
    if c3.button(":material/fast_forward: Hasta el final", key="pc_all", width="stretch", disabled=terminada_pc):
        while SPC["fecha"] < SPC["total"]: 
            simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
        st.rerun()
        
    barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPC['fecha']} / {SPC['total']}"), ("Partidos jugados", len(SPC["log"]))], pct_pc)
    
    desempates_c = [p for p in SPC["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate_c = SPC.get("desempate_pendiente") or len(desempates_c) > 0
    
    titulos_c = ["Posiciones", "Fixture y resultados"]
    if mostrar_desempate_c: titulos_c.append("Desempate")
    titulos_c.extend(["Movimientos", "Definiciones"])
    
    spc_tabs = st.tabs(titulos_c)
    idx_c = 0
    
    with spc_tabs[idx_c]:
        seccion("Tabla de posiciones", "Ida y vuelta · ascienden los 2 primeros", "#4f46e5")
        mostrar_tabla(tabla_pc(SPC), colorear_pc, SPC["pos_hist"])
        leyenda([("1°-2° Ascenso a Primera B", COLORES_B["Ascenso directo"]), 
                 ("Desempate Campeonato / Ascenso", "rgba(249, 115, 22, 0.3)")])
    idx_c += 1
            
    with spc_tabs[idx_c]: vista_fixture("pc")
    idx_c += 1
    
    if mostrar_desempate_c:
        with spc_tabs[idx_c]:
            if SPC.get("desempate_pendiente"):
                seccion("Desempates por Posiciones", "Están empatados en puntos. Jugarán un partido único.", "#9333ea")
                df_des = tabla_pc(SPC)
                df_des = df_des[df_des["id"].isin(SPC["ids_desempate"])]
                mostrar_tabla(df_des, colorear_pc)
            else:
                grupos = {}
                for p in desempates_c:
                    m = p["comp"]
                    if m not in grupos: grupos[m] = []
                    grupos[m].append(p)
                
                for motivo, parts in grupos.items():
                    if "Liguilla" in motivo:
                        seccion(f"Tabla final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f":material/visibility: Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx_c += 1
            
    with spc_tabs[idx_c]: render_movimientos(SPC["log"], SPC["pos_hist"], SPC["nombres"], "#0f766e")
    idx_c += 1
        
    with spc_tabs[idx_c]:
        seccion("Definiciones de la temporada", "Campeón y ascensos", "#b7860b")
        if SPC["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
        else:
            with st.expander(":material/emoji_events: Campeón de la Primera C", expanded=False):
                cpc = SPC["nombres"][SPC["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpc, 64)}</div><div class="nm">{esc(cpc)}</div></div>', unsafe_allow_html=True)


# ============================================================================
# CLUBES
# ============================================================================
with tab_c:
    seccion("Clubes", "Elegí un club para ver su ficha y buscar sus partidos", "#1e5aa8")
    cat = st.segmented_control("Categoría",
                               ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C"],
                               default="Primera División", key="cat_clubes")
    cat = cat or "Primera División"
    lista = sorted({"Primera División": S["nombres"], "Primera Nacional": SB["nombres"],
                    "Federal A": S["federal"], "Primera B": S["primera_b"], "Primera C": S["primera_c"]}[cat], key=norm)
    elegido = st.selectbox(":material/search: Buscar club", lista, index=None,
                           placeholder="Escribí o elegí un club…", key=f"club_sel_{cat}")
    if elegido:
        with st.container(border=True):
            render_ficha(elegido, "clubes")
    st.markdown(f'<div class="mlab" style="margin-top:14px">{esc(cat)} · {len(lista)} clubes · '
                f'tocá uno para ver su ficha</div>', unsafe_allow_html=True)
    # Grilla de clubes: cada casilla es un botón (invisible, ocupa toda la casilla) que abre la ficha
    slug = norm(cat).replace(" ", "_")
    with st.container(key=f"cgrid_{slug}"):
        for i, n in enumerate(lista):
            with st.container(key=f"ctile_{slug}_{i}"):
                st.markdown(f'<div class="ct-in">{crest(n, 52)}<span>{esc(n)}</span></div>',
                            unsafe_allow_html=True)
                if st.button(n, key=f"clubbtn_{slug}_{i}"):
                    ver_equipo(n)


# ============================================================================
# HISTORIAL
# ============================================================================
with tab_h:
    seccion("Historial", "Campeones de cada temporada y cambios de categoría", "#b7860b")
    if S["movimientos"]:
        mv = S["movimientos"]
        with st.expander(f":material/swap_vert: Cambios de categoría para la temporada {S['temp']}", expanded=False):
            st.markdown(
                '<div class="catgrid">'
                f'<div><div class="mlab up">▲ Ascendieron a Primera</div>'
                f'{lista_equipos_html([(n, "directo") for n in mv["directos"]] + ([(mv["reducido"], "reducido")] if mv["reducido"] else []))}</div>'
                f'<div><div class="mlab down">▼ Descendieron a B Nacional</div>'
                f'{lista_equipos_html([(n, "") for n in mv["bajan_p"]])}</div>'
                
                f'<div><div class="mlab up">▲ Ascendieron a B Nacional</div>'
                f'{lista_equipos_html([(n, "del Federal A") for n in mv.get("suben_f_b", [])] + [(n, "de la B Metro") for n in mv.get("suben_pb_b", [])])}</div>'
                f'<div><div class="mlab down">▼ Descendieron al Federal A</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_fed", [])])}</div>'
                
                f'<div><div class="mlab down">▼ Descendieron a la B Metro</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_pb", [])])}</div>'
                f'<div><div class="mlab up">▲ Ascendieron a la B Metro</div>'
                f'{lista_equipos_html([(n, "de la C") for n in mv.get("suben_pc_pb", [])])}</div>'
                
                f'<div><div class="mlab down">▼ Descendieron a Primera C</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pb_pc", [])])}</div>'
                f'</div><div style="margin-top:6px;font-size:.88rem">{esc(mv.get("promo_texto", ""))}</div>',
                unsafe_allow_html=True)
    if S["campeones"]:
        with st.expander(":material/emoji_events: Campeones por temporada", expanded=False):
            df_c = pd.DataFrame(S["campeones"], columns=["Temporada", "Primera División", "Primera Nacional"])
            st.markdown(tabla_html(df_c, clubes=("Primera División", "Primera Nacional")),
                        unsafe_allow_html=True)