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

st.set_page_config(page_title="Simulador Fútbol Argentino", page_icon="⚽", layout="wide")

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
    norm,
    render_ficha,
    render_movimientos,
    seccion,
    vista_fixture,
)


# ----------------------------------------------------------------------------
# INTERFAZ
# ----------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Parámetros")
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

terminada = S["fecha"] >= TOTAL_FECHAS
terminada_b = SB["fecha"] >= B_TOTAL
terminada_f = SF["fecha"] >= SF["total"]
terminada_pb = SPB["fecha"] >= SPB["total"]
terminada_pc = SPC["fecha"] >= SPC["total"]
ambas = terminada and terminada_b and terminada_f and terminada_pb and terminada_pc
b_espera_primera = SB["fecha"] == B_TOTAL - 1 and not terminada

pct_p = 100 * S["fecha"] / TOTAL_FECHAS
pct_b = 100 * SB["fecha"] / B_TOTAL
pct_f = 100 * SF["fecha"] / SF["total"]
pct_pb = 100 * SPB["fecha"] / SPB["total"] if SPB["total"] else 0
pct_pc = 100 * SPC["fecha"] / SPC["total"] if SPC["total"] else 0

st.markdown(
    f'<div class="hero"><span class="sol">☀</span><div class="hero-top"><div>'
    f'<div class="hero-k">Temporada {S["temp"]} · Fútbol argentino</div>'
    f'<h1>Simulador de la Liga Argentina</h1>'
    f'<p>Primera División · Primera Nacional · Federal A · Primera B · Primera C</p></div>'
    f'<div class="hero-stats">'
    f'<div class="hs"><span>Primera División</span><b>Fecha {S["fecha"]}/{TOTAL_FECHAS}</b>'
    f'<div class="bar"><i style="width:{pct_p:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Primera Nacional</span><b>Fecha {SB["fecha"]}/{B_TOTAL}</b>'
    f'<div class="bar"><i style="width:{pct_b:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Federal A</span><b>Fecha {SF["fecha"]}/{SF["total"]}</b>'
    f'<div class="bar"><i style="width:{pct_f:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Primera B</span><b>Fecha {SPB["fecha"]}/{SPB["total"]}</b>'
    f'<div class="bar"><i style="width:{pct_pb:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Primera C</span><b>Fecha {SPC["fecha"]}/{SPC["total"]}</b>'
    f'<div class="bar"><i style="width:{pct_pc:.1f}%"></i></div></div>'
    f'<div class="hs"><span>Partidos jugados</span>'
    f'<b>{len(S["log"]) + len(SB["log"]) + len(SF["log"]) + len(SPB["log"]) + len(SPC["log"])}</b></div>'
    f'</div></div></div>', unsafe_allow_html=True)

g0, g1, g2, g3 = st.columns([3, 1.4, 1.4, 1.2], vertical_alignment="center")
g0.caption("Simulá fecha por fecha desde cada categoría, o todo junto con los botones de la derecha.")
if g1.button("⏩ Simular todo", disabled=ambas, width="stretch", type="primary"):
    # 1. Primero terminar Primera División (la B necesita saber el 27° para la Promoción)
    while S["fecha"] < TOTAL_FECHAS: 
        simular_fecha(S, P, acumular)
        
    # 2. Ahora sí corre la B Nacional hasta el final sin trabarse
    while SB["fecha"] < B_TOTAL + SB.get("extra_f2", 0) and not (SB["fecha"] == B_TOTAL + SB.get("extra_f2", 0) - 1 and S["fecha"] < TOTAL_FECHAS): 
        simular_fecha_b(S, P)
        
    # 3. Resto de las categorías
    while SF["fecha"] < SF["total"]: 
        simular_fecha_f(SF, P, S["rng"])
    while SPB["fecha"] < SPB["total"]: 
        simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
    while SPC["fecha"] < SPC["total"]: 
        simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
    st.rerun()
if g2.button("📅 Nueva temporada", disabled=not ambas, width="stretch"):
    nueva_temporada(S, volatilidad)
    st.rerun()
if g3.button("🔄 Reiniciar", width="stretch"):
    st.session_state.S = crear_estado()
    st.rerun()

tab_p, tab_b, tab_f, tab_pb, tab_pc, tab_c, tab_h = st.tabs([
    "🏆 Primera", "🥈 B Nacional", "🌎 Federal A", "🚍 Primera B", "🚂 Primera C", "🛡️ Clubes", "📜 Historial"
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
    
    # Construimos el HTML visual
    html = '<table style="width:100%; text-align:center; border-collapse:collapse; font-size:14px; margin-bottom:1rem; background:white; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
    html += '<tr style="background:#f8fafc; border-bottom:2px solid #e2e8f0; color:#64748b; font-size:12px; text-transform:uppercase;">'
    html += '<th style="padding:10px;">Pos</th><th style="text-align:left;">Club</th><th>Pts</th><th>PJ</th><th>G</th><th>P</th><th>GF</th><th>GC</th><th>DG</th></tr>'
    
    for i, row in enumerate(lista):
        html += f'<tr style="border-bottom:1px solid #f1f5f9;">'
        html += f'<td style="padding:10px; color:#94a3b8; font-weight:bold;">{i+1}</td>'
        html += f'<td style="text-align:left; display:flex; align-items:center; gap:8px; font-weight:500;">{crest(row["Club"], 24)} {esc(row["Club"])}</td>'
        html += f'<td style="font-weight:bold; color:#0f172a; font-size:15px;">{row["Pts"]}</td>'
        html += f'<td>{row["PJ"]}</td><td>{row["G"]}</td><td>{row["P"]}</td>'
        html += f'<td>{row["GF"]}</td><td>{row["GC"]}</td><td>{row["DG"]}</td>'
        html += '</tr>'
    html += '</table>'
    return html


# ============================================================================
# PRIMERA DIVISIÓN
# ============================================================================
with tab_p:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip("Liga Profesional · 30 equipos", "#1e5aa8") + " " +
                chip("Fase 1 · todos contra todos" if S["fase"] == 1 else "Fase 2 · zonas"),
                unsafe_allow_html=True)
    if c2.button("▶️ Próxima fecha", key="p_next", disabled=terminada, width="stretch",
                 type="primary"):
        simular_fecha(S, P, acumular)
        st.rerun()
    if c3.button("⏩ Hasta el final", key="p_all", disabled=terminada, width="stretch"):
        while S["fecha"] < TOTAL_FECHAS:
            simular_fecha(S, P, acumular)
        st.rerun()

    jugados = int(S["pj"].sum() // 2)
    pct = 100 * S["sorpresas"] / jugados if jugados else 0
    barra_estado([("Fase", "1 · Todos contra todos" if S["fase"] == 1 else "2 · Zonas"),
                  ("Fecha", f"{S['fecha']} / {TOTAL_FECHAS}"),
                  ("Sorpresas", f"{S['sorpresas']} ({pct:.0f}%)")], pct_p)
    if S["fase"] == 2 and S["fecha"] == FECHAS_F1:
        aviso("Terminó la fase 1: se armaron las zonas Campeonato, Intermedia y Descenso. "
              "Las 9 fechas siguientes se juegan dentro de cada zona, con la localía invertida.")

    sp = st.tabs(["📊 Posiciones", "📅 Fixture y resultados", "🔄 Movimientos", "🏁 Definiciones"])
    with sp[0]:
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
            leyenda(LEY_DESTINOS)
        if S["fecha"] == 0:
            with st.expander("✏️ Editar medias internas de esta temporada"):
                ed = st.data_editor(
                    pd.DataFrame({"Equipo": S["nombres"], "Media": S["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_p_{S['temp']}",
                )
                S["r"] = np.clip(ed["Media"].to_numpy(float), MIN_R, MAX_R)
    with sp[1]:
        vista_fixture("p")
    with sp[2]:
        render_movimientos(S["log"], S["pos_hist"], S["nombres"], "#1e5aa8")
    with sp[3]:
        seccion("Definiciones de la temporada", "Campeón, copas, promoción y descensos", "#b7860b")
        if not terminada:
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
                with st.expander("🏆 Campeón de Primera División", expanded=False):
                    campeon = final.iloc[0]["Equipo"]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(campeon, 64)}</div>'
                                f'<div class="nm">{esc(campeon)}</div></div>', unsafe_allow_html=True)
                with st.expander("🌎 Clasificados · Copa Libertadores", expanded=False):
                    st.markdown('<div class="mlab">Fase de grupos (1° al 5°)</div>'
                                + equipos(range(1, 6)) + '<div class="mlab">Fase previa (11°)</div>'
                                + equipos([11]), unsafe_allow_html=True)
                with st.expander("🌎 Copa Sudamericana", expanded=False):
                    st.markdown('<div class="mlab">6° al 8° y 12°-13°</div>'
                                + equipos(list(range(6, 9)) + [12, 13]), unsafe_allow_html=True)
            with e2:
                with st.expander("🔁 Promoción", expanded=False):
                    txt = ('<div class="mlab">Juega la Promoción contra el perdedor de la final '
                           'del reducido (27°)</div>' + equipos([N - 3]))
                    if SB["promo_partido"]:
                        txt += fila_partido_html(SB["promo_partido"])
                    st.markdown(txt, unsafe_allow_html=True)
                with st.expander("⬇️ Descensos", expanded=False):
                    st.markdown('<div class="mlab">Descienden a la Primera Nacional (28° al 30°)</div>'
                                + equipos(range(N - 2, N + 1)), unsafe_allow_html=True)

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
    
    if c2.button("▶️ Próxima fecha", key="b_next", width="stretch", type="primary",
                 disabled=terminada_b or b_espera_primera):
        simular_fecha_b(S, P)
        st.rerun()
        
    if c3.button("⏩ Hasta el final", key="b_all", width="stretch",
                 disabled=terminada_b or b_espera_primera):
        while SB["fecha"] < B_TOTAL + SB.get("extra_f2", 0) and not (SB["fecha"] == B_TOTAL + SB.get("extra_f2", 0) - 1 and S["fecha"] < TOTAL_FECHAS):
            simular_fecha_b(S, P)
        st.rerun()

    pct_b_dyn = 100 * fb / (B_TOTAL + extra) if (B_TOTAL + extra) else 0
    barra_estado([("Fase", fase_txt), ("Fecha", f"{fb} / {B_TOTAL + extra}"),
                  ("Partidos jugados", len(SB["log"]))], pct_b_dyn)
                  
    if b_espera_primera:
        aviso("⏳ La Promoción se juega contra el 27° de Primera: terminá primero la temporada "
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
    
    titulos_b = ["📊 Posiciones", "📅 Fixture y resultados"]
    if mostrar_desempate_b: titulos_b.append("⚔️ Desempate")
    titulos_b.extend(["🏟️ Reducido", "🔄 Movimientos", "🏁 Definiciones"])
    
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
            
        with st.expander("ℹ️ Formato de la Primera Nacional"):
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
            with st.expander("✏️ Editar medias internas de esta temporada (Primera Nacional)"):
                edb = st.data_editor(
                    pd.DataFrame({"Equipo": SB["nombres"], "Media": SB["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_b_{S['temp']}",
                )
                SB["r"] = np.clip(edb["Media"].to_numpy(float), MIN_R, MAX_R)
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
                        seccion(f"📊 Tabla Final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f"👀 Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"⚔️ Desempate: {motivo}", "Partido único definitorio", "#dc2626")
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
                ent = SB["entrantes"].copy()
                ent.insert(1, " ", [ESCUDOS.get(n) for n in ent["Equipo"]])
                st.dataframe(ent, hide_index=True, width="stretch",
                             column_config={" ": st.column_config.ImageColumn(" ", width=40)})
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
                with st.expander("🏆 Campeón de la Primera Nacional", expanded=False):
                    cb = nom_b[SB["campeon"]]
                    st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                                f'</div><div style="margin-top:10px">{crest(cb, 64)}</div>'
                                f'<div class="nm">{esc(cb)}</div><div class="s">Asciende a Primera'
                                f'</div></div>', unsafe_allow_html=True)
                with st.expander("⬆️ Clasificados · Ascensos", expanded=False):
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
                with st.expander("🔁 Promoción", expanded=False):
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
                with st.expander("⬇️ Descensos", expanded=False):
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
    if c2.button("▶️ Próxima fecha", key="f_next", width="stretch", type="primary",
                 disabled=terminada_f):
        simular_fecha_f(SF, P, S["rng"])
        st.rerun()
    if c3.button("⏩ Hasta el final", key="f_all", width="stretch", disabled=terminada_f):
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

    sf_tabs = st.tabs(["📊 Posiciones", "📅 Fixture y resultados", "🏟️ Reducido", "🔄 Movimientos",
                       "🏁 Definiciones"])
                       
    with sf_tabs[0]:
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
            with st.expander("✏️ Editar medias internas de esta temporada (Federal A)"):
                edf = st.data_editor(
                    pd.DataFrame({"Equipo": nom_f, "Media": SF["r"]}),
                    disabled=["Equipo"], hide_index=True, width="stretch",
                    key=f"editor_f_{S['temp']}",
                )
                SF["r"] = np.clip(edf["Media"].to_numpy(float), MIN_R, MAX_R)
                
    with sf_tabs[1]:
        vista_fixture("f")
        
    with sf_tabs[2]:
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
                ent = SF["entrantes"].copy()
                ent.insert(1, " ", [ESCUDOS.get(n) for n in ent["Equipo"]])
                st.dataframe(ent, hide_index=True, width="stretch",
                             column_config={" ": st.column_config.ImageColumn(" ", width=40)})
                             
    with sf_tabs[3]:
        render_movimientos(SF["log"], SF["pos_hist"], nom_f, "#0f766e")
        
    with sf_tabs[4]:
        seccion("Definiciones de la temporada", "Campeón y ascensos a la Primera Nacional",
                "#b7860b")
        if SF["campeon"] is None:
            aviso("Las definiciones aparecen acá cuando termina la fase 2 del Federal A.")
        else:
            st.caption("Están cerradas para no spoilear: tocá cada una para verla.")
            with st.expander("🏆 Campeón del Federal A", expanded=False):
                cf = nom_f[SF["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón · Temporada {S["temp"]}'
                            f'</div><div style="margin-top:10px">{crest(cf, 64)}</div>'
                            f'<div class="nm">{esc(cf)}</div><div class="s">Asciende a la Primera'
                            f' Nacional</div></div>', unsafe_allow_html=True)
            with st.expander("⬆️ Clasificados · Ascensos", expanded=False):
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
    
    if c2.button("▶️ Próxima fecha", key="pb_next", width="stretch", type="primary", disabled=terminada_pb):
        simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
        st.rerun()
    if c3.button("⏩ Hasta el final", key="pb_all", width="stretch", disabled=terminada_pb):
        while SPB["fecha"] < SPB["total"]: 
            simular_fecha_liga(SPB, P, S["rng"], "Primera B", tabla_pb)
        st.rerun()
        
    barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPB['fecha']} / {SPB['total']}"), ("Partidos jugados", len(SPB["log"]))], pct_pb)
    
    desempates = [p for p in SPB["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate = SPB.get("desempate_pendiente") or len(desempates) > 0
    
    titulos = ["📊 Posiciones", "📅 Fixture y resultados"]
    if mostrar_desempate: titulos.append("⚔️ Desempate")
    titulos.extend(["🔄 Movimientos", "🏁 Definiciones"])
    
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
                        seccion(f"📊 Tabla Final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f"👀 Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"⚔️ Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx += 1
            
    with spb_tabs[idx]: render_movimientos(SPB["log"], SPB["pos_hist"], SPB["nombres"], "#0f766e")
    idx += 1
        
    with spb_tabs[idx]:
        seccion("Definiciones de la temporada", "Campeón, ascensos y descensos", "#b7860b")
        if SPB["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
        else:
            with st.expander("🏆 Campeón de la Primera B", expanded=False):
                cpb = SPB["nombres"][SPB["campeon"]]
                st.markdown(f'<div class="champ"><div class="t">Campeón</div><div style="margin-top:10px">{crest(cpb, 64)}</div><div class="nm">{esc(cpb)}</div></div>', unsafe_allow_html=True)
                

# ============================================================================
# PRIMERA C
# ============================================================================
with tab_pc:
    c1, c2, c3 = st.columns([3, 1.4, 1.4], vertical_alignment="center")
    c1.markdown(chip(f"Primera C · {len(SPC['nombres'])} equipos") + " " + chip("Todos contra todos", "#475569"), unsafe_allow_html=True)
    
    if c2.button("▶️ Próxima fecha", key="pc_next", width="stretch", type="primary", disabled=terminada_pc):
        simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
        st.rerun()
    if c3.button("⏩ Hasta el final", key="pc_all", width="stretch", disabled=terminada_pc):
        while SPC["fecha"] < SPC["total"]: 
            simular_fecha_liga(SPC, P, S["rng"], "Primera C", tabla_pc)
        st.rerun()
        
    barra_estado([("Fase", "Liga ida y vuelta"), ("Fecha", f"{SPC['fecha']} / {SPC['total']}"), ("Partidos jugados", len(SPC["log"]))], pct_pc)
    
    desempates_c = [p for p in SPC["log"] if p["rotulo"] == "Desempate"]
    mostrar_desempate_c = SPC.get("desempate_pendiente") or len(desempates_c) > 0
    
    titulos_c = ["📊 Posiciones", "📅 Fixture y resultados"]
    if mostrar_desempate_c: titulos_c.append("⚔️ Desempate")
    titulos_c.extend(["🔄 Movimientos", "🏁 Definiciones"])
    
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
                        seccion(f"📊 Tabla Final: {motivo}", "Posiciones del mini-torneo a partido único", "#9333ea")
                        st.markdown(html_tabla_liguilla(parts), unsafe_allow_html=True)
                        with st.expander(f"👀 Ver los {len(parts)} enfrentamientos", expanded=False):
                            for p in parts:
                                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
                    else:
                        seccion(f"⚔️ Desempate: {motivo}", "Partido único definitorio", "#dc2626")
                        for p in parts:
                            st.markdown(fila_partido_html(p, abierto=True), unsafe_allow_html=True)
        idx_c += 1
            
    with spc_tabs[idx_c]: render_movimientos(SPC["log"], SPC["pos_hist"], SPC["nombres"], "#0f766e")
    idx_c += 1
        
    with spc_tabs[idx_c]:
        seccion("Definiciones de la temporada", "Campeón y ascensos", "#b7860b")
        if SPC["campeon"] is None: aviso("Las definiciones aparecen acá cuando termina la liga.")
        else:
            with st.expander("🏆 Campeón de la Primera C", expanded=False):
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
    elegido = st.selectbox("Club", lista, index=None, placeholder="Elegí un club…", key=f"club_sel_{cat}")
    if elegido:
        with st.container(border=True):
            render_ficha(elegido, "clubes")
    st.markdown('<div class="mlab" style="margin-top:14px">'
                f'{esc(cat)} · {len(lista)} clubes</div><div class="cgrid">'
                + "".join(f'<div class="ct">{crest(n, 52)}<span>{esc(n)}</span></div>' for n in lista)
                + "</div>", unsafe_allow_html=True)


# ============================================================================
# HISTORIAL
# ============================================================================
with tab_h:
    seccion("Historial", "Campeones de cada temporada y cambios de categoría", "#b7860b")
    if S["movimientos"]:
        mv = S["movimientos"]
        with st.expander(f"📋 Cambios de categoría para la temporada {S['temp']}", expanded=False):
            st.markdown(
                '<div class="catgrid">'
                f'<div><div class="mlab up">⬆️ Ascendieron a Primera</div>'
                f'{lista_equipos_html([(n, "directo") for n in mv["directos"]] + ([(mv["reducido"], "reducido")] if mv["reducido"] else []))}</div>'
                f'<div><div class="mlab down">⬇️ Descendieron a B Nacional</div>'
                f'{lista_equipos_html([(n, "") for n in mv["bajan_p"]])}</div>'
                
                f'<div><div class="mlab up">⬆️ Ascendieron a B Nacional</div>'
                f'{lista_equipos_html([(n, "del Federal A") for n in mv.get("suben_f_b", [])] + [(n, "de la B Metro") for n in mv.get("suben_pb_b", [])])}</div>'
                f'<div><div class="mlab down">⬇️ Descendieron al Federal A</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_fed", [])])}</div>'
                
                f'<div><div class="mlab down">⬇️ Descendieron a la B Metro</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_b_pb", [])])}</div>'
                f'<div><div class="mlab up">⬆️ Ascendieron a la B Metro</div>'
                f'{lista_equipos_html([(n, "de la C") for n in mv.get("suben_pc_pb", [])])}</div>'
                
                f'<div><div class="mlab down">⬇️ Descendieron a Primera C</div>'
                f'{lista_equipos_html([(n, "") for n in mv.get("bajan_pb_pc", [])])}</div>'
                f'</div><div style="margin-top:6px;font-size:.88rem">🔁 {esc(mv.get("promo_texto", ""))}</div>',
                unsafe_allow_html=True)
    if S["campeones"]:
        with st.expander("🏆 Campeones por temporada", expanded=False):
            df_c = pd.DataFrame(S["campeones"], columns=["Temporada", "Primera División", "Primera Nacional"])
            st.dataframe(df_c, hide_index=True, width="stretch")