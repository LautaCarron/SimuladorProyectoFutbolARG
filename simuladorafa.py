"""Simulador del fútbol argentino (Proyecto AFA): punto de entrada de Streamlit.

    python -m pip install -r requirements.txt
    python -m streamlit run simuladorafa.py

Acá sólo se arma la página; cada parte vive en su módulo:
  config.py             parámetros fijos y detección del entorno (PC o web estática)
  motor/                simulación pura, sin Streamlit (estado, calendario, "Simular todo", progreso)
  ui/cabecera, acciones, pestanas, contexto   las piezas de la página
  ui/ui_*.py, ui/*.py   una pestaña por módulo; cada una expone render(ctx)

Los formatos de cada competencia están en docs/FORMATOS.md y la estructura completa en el README.
"""

import streamlit as st

st.set_page_config(page_title="Proyecto AFA · Simulador Fútbol Argentino", page_icon="⚽", layout="wide",
                   initial_sidebar_state="collapsed")

from config import ACUMULAR_PUNTOS, ES_WEB, parametros_partido  # noqa: E402

if not ES_WEB:    # pantalla de inicio ("Elegí un modo"); en la web estática la muestra index.html
    from ui.inicio import mostrar_inicio
    mostrar_inicio()

from datos.equipos import ERROR_DATOS, ESCUDOS_CSS  # noqa: E402

if ERROR_DATOS:   # datos/equipos.py no depende de Streamlit: el aviso lo muestra la interfaz
    st.error(ERROR_DATOS)
    st.stop()

from datos.logos import LOGOS_CSS  # noqa: E402
from motor.calendario import proximos  # noqa: E402
from motor.manager import sincronizar_manager  # noqa: E402
from motor.nucleo import con_tacticas  # noqa: E402
from motor.progreso import Progreso, avisos_de_temporada  # noqa: E402
from motor.temporada import VERSION_ESTADO, crear_estado  # noqa: E402
from ui import (  # noqa: E402
    avisos as ui_avisos,
    clubes as ui_clubes,
    copa_argentina as ui_copa_argentina,
    historial as ui_historial,
    ligas_simples as ui_ligas_simples,
    manager as ui_manager,
    supercopa as ui_supercopa,
    ui_calendario,
    ui_conmebol,
    ui_federal,
    ui_federal_b,
    ui_guardado,
    ui_mundial,
    ui_nacional,
    ui_primera,
    ui_regional,
)
from ui.acciones import render_acciones  # noqa: E402
from ui.contexto import Contexto  # noqa: E402
from ui.dios import panel_dios  # noqa: E402
from ui.pestanas import crear_pestanas  # noqa: E402
from ui.vista import CSS, puente_clubes  # noqa: E402
from ui.vista.cabecera import render_cabecera  # noqa: E402
from ui.vista.mi_club import competencias_club, estilo_mi_club  # noqa: E402

# Pestañas de la interfaz, en el orden en que se dibujan
PESTANAS_UI = (ui_manager, ui_primera, ui_nacional, ui_federal, ui_federal_b, ui_ligas_simples, ui_regional,
               ui_copa_argentina, ui_supercopa, ui_conmebol, ui_mundial, ui_calendario, ui_clubes, ui_avisos,
               ui_historial, ui_guardado)


def _estado_de_la_partida():
    """La partida vive en st.session_state.S; se crea de nuevo si cambió la estructura del estado guardado."""
    if "S" not in st.session_state or st.session_state.S.get("version") != VERSION_ESTADO:
        st.session_state.S = crear_estado()
    S = st.session_state.S
    if mensaje := st.session_state.pop("afa_msg_partida", None):      # lo deja la pestaña Partidas al cargar
        st.toast(mensaje, icon=":material/check_circle:")
    return S


def _es_modo_manager():
    return st.session_state.get("afa_pantalla") == "manager" or st.query_params.get("modo") == "manager"


def _preparar_manager(S):
    """Modo Manager: se muestra el simulador completo y se suma la pestaña "Manager" (oficina, mi club, carrera).
    Corta la ejecución mientras falte cargar los datos del manager o haya un evento por resolver."""
    if not st.session_state.get("manager"):
        ui_manager.alta_manager(S)                       # primero se cargan los datos del manager
        st.stop()
    M = st.session_state["manager"]
    for texto in sincronizar_manager(S, M):   # ofertas y ascensos de los días jugados
        st.toast(texto)
    if M.get("evento"):                                  # evento por resolver: todo queda en pausa
        ui_manager.pantalla_evento(S, M)
        st.stop()


def main():
    P = parametros_partido()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(LOGOS_CSS, unsafe_allow_html=True)       # logos de ligas y copas (una sola vez)
    st.markdown(ESCUDOS_CSS, unsafe_allow_html=True)     # escudos a los que se les sacó el fondo (una sola vez)
    S = _estado_de_la_partida()
    modo_mgr = _es_modo_manager()
    if modo_mgr:
        _preparar_manager(S)
    else:
        panel_dios(S)                                    # Modo dios (sólo modo simulación): formatos desde la barra lateral
        if getattr(S["rng"], "tacticas", None):          # modo simulación: nadie juega con táctica
            S["rng"] = con_tacticas(S["rng"], {})

    # Mi club (modo manager): se marca en amarillo y se señalan las competencias donde juega
    manager = st.session_state["manager"] if modo_mgr else None
    club = manager.get("club") if manager else None
    puente_clubes(S, club)                               # tocar un club en cualquier tabla abre su ficha
    competencias = competencias_club(S, club) if club else set()
    kclub = "_" + "".join(c if c.isalnum() else "_" for c in club) if club else ""
    if club:
        st.markdown(estilo_mi_club(club), unsafe_allow_html=True)

    progreso = Progreso.desde_estado(S)
    prox = proximos(S)
    hoy = min((d for d, _ in prox.values()), default=None)     # próximo día con partidos
    render_cabecera(S, progreso, hoy)
    render_acciones(S, P, progreso, modo_mgr, ACUMULAR_PUNTOS, hoy)

    # Avisos (suspensiones y sanciones): los de esta temporada y los anteriores; los nuevos se cuentan en la pestaña Avisos
    avisos = avisos_de_temporada(S)
    total_avisos = len(S.get("alertas_hist", [])) + len(avisos)
    sin_leer = max(0, total_avisos - S.get("avisos_leidos", 0))

    pestanas = crear_pestanas(S, modo_mgr, competencias, kclub, sin_leer,
                              pestana_inicial=st.session_state.get("afa_tab_inicial"))
    ctx = Contexto(S=S, P=P, acumular=ACUMULAR_PUNTOS, modo_mgr=modo_mgr, manager=manager, progreso=progreso, pestanas=pestanas,
                   avisos=avisos, total_avisos=total_avisos, sin_leer=sin_leer, prox=prox, hoy=hoy)
    for modulo in PESTANAS_UI:
        modulo.render(ctx)


main()
