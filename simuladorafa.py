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
from datos.paises import PAIS_BASE  # noqa: E402

if not ES_WEB:    # pantalla de inicio ("Elegí un modo"); en la web estática la muestra index.html
    from ui.inicio import mostrar_inicio
    mostrar_inicio()

from datos import club_propio  # noqa: E402
from datos.equipos import ERROR_DATOS, ESCUDOS_CSS  # noqa: E402

if ERROR_DATOS:   # datos/equipos.py no depende de Streamlit: el aviso lo muestra la interfaz
    st.error(ERROR_DATOS)
    st.stop()

from datos.logos import LOGOS_CSS  # noqa: E402
from motor.calendario import proximos  # noqa: E402
from motor.manager import sincronizar_manager  # noqa: E402
from motor.nucleo import con_tacticas  # noqa: E402
from motor.progreso import Progreso, avisos_de_temporada, avisos_del_pais_en  # noqa: E402
from motor.temporada import VERSION_ESTADO, crear_estado  # noqa: E402
from ui import (  # noqa: E402
    avisos as ui_avisos,
    clubes as ui_clubes,
    copa_argentina as ui_copa_argentina,
    crear_club as ui_crear_club,
    historial as ui_historial,
    ligas_simples as ui_ligas_simples,
    manager as ui_manager,
    supercopa as ui_supercopa,
    ui_calendario,
    ui_conmebol,
    ui_copa_brasil,
    ui_copa_chile,
    ui_copa_colombia,
    ui_copa_uruguay,
    ui_estaduales,
    ui_supercopa_br,
    ui_supercopa_cl,
    ui_supercopa_co,
    ui_supercopa_uy,
    ui_federal,
    ui_federal_b,
    ui_guardado,
    ui_ligas_ext,
    ui_mundial,
    ui_mundo,
    ui_nacional,
    ui_primera,
    ui_regional,
    ui_regionales,
)
from ui.acciones import render_acciones  # noqa: E402
from ui.contexto import Contexto  # noqa: E402
from motor import incidentes  # noqa: E402
from ui.dios import panel_dios  # noqa: E402
from ui.pais_activo import pais_activo  # noqa: E402
from ui.pestanas import crear_pestanas  # noqa: E402
from ui.vista import CSS, puente_clubes  # noqa: E402
from ui.vista.cabecera import render_cabecera  # noqa: E402
from ui.vista.mi_club import competencias_club, estilo_mi_club  # noqa: E402

# Pestañas de la interfaz, en el orden en que se dibujan
PESTANAS_UI = (ui_manager, ui_primera, ui_nacional, ui_federal, ui_federal_b, ui_ligas_simples, ui_regional,
               ui_copa_argentina, ui_supercopa, ui_regionales, ui_estaduales, ui_copa_brasil, ui_copa_chile, ui_copa_colombia, ui_supercopa_br, ui_supercopa_cl, ui_supercopa_co, ui_copa_uruguay, ui_supercopa_uy, ui_conmebol, ui_mundial, ui_ligas_ext, ui_mundo, ui_calendario,
               ui_clubes, ui_avisos, ui_historial, ui_guardado)


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
    if st.session_state.get("afa_pantalla") == "crear_club":      # "Crear mi club" (desde la pantalla de inicio)
        ui_crear_club.render()
        st.stop()
    S = _estado_de_la_partida()
    incidentes.fijar(S)                                  # Tribunal de Disciplina encendido o apagado (Avisos)
    club_propio.activar(S.get("club_propio"))            # el club que creó la persona (región, liga y escudo)
    st.markdown(club_propio.css(), unsafe_allow_html=True)
    modo_mgr = _es_modo_manager()
    pais = pais_activo()                                 # el que se elige en Mundo
    if modo_mgr:
        _preparar_manager(S)
    else:
        if pais == PAIS_BASE:
            panel_dios(S)                                # Modo dios (sólo modo simulación): formatos desde la barra lateral
        else:                                            # por ahora el Modo dios es sólo de Argentina
            with st.sidebar:
                st.divider()
                st.header("Modo dios")
                st.caption(f"Por ahora el Modo dios es sólo de Argentina. Elegí Argentina en la pestaña Mundo para "
                           f"cambiar sus formatos (estás viendo {pais}).")
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
    render_acciones(S, P, progreso, modo_mgr, ACUMULAR_PUNTOS, hoy, pais)

    # Avisos (suspensiones y sanciones) del país activo: los de esta temporada y los anteriores; los nuevos se cuentan
    # en la pestaña Avisos
    avisos, avisos_hist, sin_leer = avisos_del_pais_en(S, avisos_de_temporada(S), pais)
    total_avisos = len(avisos_hist) + len(avisos)

    ui_mundo.indicador(pais, movil=True)                         # qué país se está viendo (se cambia en Mundo)
    pestanas = crear_pestanas(S, modo_mgr, competencias, kclub, sin_leer,
                              pestana_inicial=st.session_state.get("afa_tab_inicial"), pais=pais)
    ctx = Contexto(S=S, P=P, acumular=ACUMULAR_PUNTOS, modo_mgr=modo_mgr, manager=manager, progreso=progreso, pestanas=pestanas,
                   avisos=avisos, total_avisos=total_avisos, sin_leer=sin_leer, prox=prox, hoy=hoy,
                   pais=pais, avisos_hist=avisos_hist)
    for modulo in PESTANAS_UI:
        modulo.render(ctx)


main()
