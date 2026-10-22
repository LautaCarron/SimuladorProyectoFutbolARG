"""Pestaña Partidas (va en ui/ui_guardado.py): guardar la partida en un archivo y cargarla después.

Guardar: el botón descarga un archivo `.afa` con todo (ligas, copas, calendario, historial y, si se juega en
modo Manager, la carrera). Cargar: se elige el archivo, se ve de qué partida se trata y se confirma; eso
reemplaza la partida actual. Se puede cargar también ANTES de empezar a simular: la pantalla de inicio
(ui/inicio.py) tiene la opción "Cargar partida", que abre el simulador directamente en esta pestaña.

Los archivos se guardan en el dispositivo de cada persona (descarga / subida) y no en el servidor: así andan
igual en la PC, en Streamlit Cloud y en la web estática, y nadie ve las partidas de otro.
El formato y la validación están en motor/guardado.py. `ctx` trae el estado y los ayudantes compartidos.
"""

import streamlit as st

from motor.guardado import (EXTENSION, ErrorPartida, desempaquetar, empaquetar, leer_encabezado,
                            nombre_archivo)
from ui.vista import aviso, esc, seccion

# Claves de session_state que dependen de la partida en curso y no tienen sentido con la partida cargada
_CLAVES_PARTIDA = ("mgr_msg", "mgr_ultimo", "cal_dia_sel", "_dia_a_elegir", "_club_a_abrir", "puente_dia",
                   "puente_club")


def instalar_partida(carga):
    """Pone la partida cargada (salida de motor.guardado.desempaquetar) como la partida en curso."""
    st.session_state.S = carga["S"]
    if carga["modo"] == "manager":
        st.session_state["manager"] = carga["manager"]
    else:
        st.session_state.pop("manager", None)
    st.session_state["afa_pantalla"] = carga["modo"]
    if st.query_params.get("modo"):                       # el parámetro de la URL no debe pisar el modo cargado
        st.query_params["modo"] = carga["modo"]
    for k in _CLAVES_PARTIDA:
        st.session_state.pop(k, None)
    for k in [k for k in st.session_state if str(k).startswith("dios_")]:
        st.session_state.pop(k, None)                      # los controles del Modo dios se rearman con lo cargado
    st.session_state.pop("afa_tab_inicial", None)          # ya no hay que abrir esta pestaña: se vuelve al juego
    st.session_state["afa_up_n"] = st.session_state.get("afa_up_n", 0) + 1     # vacía el selector de archivos


def _descripcion(enc):
    """Texto (HTML) de qué partida es, a partir del encabezado del archivo."""
    lineas = [f'<b>Temporada {enc.get("temp")} · {enc.get("anio")}</b>'
              + (f' · {esc(enc["dia"])}' if enc.get("dia") else "")]
    if enc.get("modo") == "manager":
        quien = enc.get("manager") or "Manager"
        lineas.append(f'Modo Manager · {esc(quien)}' + (f' en {esc(enc["club"])}' if enc.get("club") else " (libre)"))
    else:
        lineas.append("Modo Simulador")
    pie = f'Guardada el {esc(enc.get("guardado", "?"))}'
    if enc.get("nombre"):
        pie = f'«{esc(enc["nombre"])}» · ' + pie
    lineas.append(f'<small>{pie}</small>')
    return "<br>".join(lineas)


def _guardar(ctx):
    S = ctx.S
    M = st.session_state.get("manager") if ctx.modo_mgr else None
    st.markdown('<div class="mlab">Guardar partida</div>', unsafe_allow_html=True)
    nombre = st.text_input("Nombre de la partida (opcional)", max_chars=40, key="afa_guardar_nombre",
                           placeholder=f"Temporada {S['temp']}")
    try:
        datos = empaquetar(S, M, "manager" if M else "simulador", nombre)
    except ErrorPartida as e:
        st.error(str(e))
        return
    st.download_button(f":material/download: Descargar partida (temporada {S['temp']})", data=datos,
                       file_name=nombre_archivo(S, M, nombre), mime="application/octet-stream",
                       key="afa_descargar", type="primary", width="stretch")
    st.caption(f"{len(datos) / 1024:.0f} KB · se guarda en tu dispositivo, en la carpeta de descargas. "
               "Guarda el momento exacto: lo que simules después no entra en este archivo.")


def _cargar(ctx):
    st.markdown('<div class="mlab">Cargar partida</div>', unsafe_allow_html=True)
    ok = st.session_state.pop("afa_ultima_carga", None)
    if ok:
        st.success(ok, icon=":material/check_circle:")
    arch = st.file_uploader(f"Archivo de partida (.{EXTENSION})", type=[EXTENSION],
                            key=f"afa_up_{st.session_state.get('afa_up_n', 0)}")
    if arch is None:
        st.caption("Elegí un archivo .afa que hayas descargado antes. Antes de empezar a simular o cuando quieras: "
                   "la partida que cargues reemplaza a la actual.")
        return
    datos = arch.getvalue()
    try:
        enc = leer_encabezado(datos)
    except ErrorPartida as e:
        st.error(str(e), icon=":material/error:")
        return
    st.markdown(f'<div class="aviso">{_descripcion(enc)}</div>', unsafe_allow_html=True)
    if st.button(":material/upload: Cargar esta partida", key="afa_cargar", type="primary", width="stretch"):
        try:
            carga = desempaquetar(datos)
        except ErrorPartida as e:
            st.error(str(e), icon=":material/error:")
            return
        instalar_partida(carga)
        enc = carga["encabezado"]
        msg = f"Partida cargada: temporada {enc.get('temp')} ({enc.get('anio')})."
        st.session_state["afa_msg_partida"] = msg                 # lo muestra simuladorafa.py como aviso emergente
        st.session_state["afa_ultima_carga"] = msg + " Ya podés seguir jugando desde donde la dejaste."
        st.rerun()


def render(ctx):
    (_abierta, tab_pa) = (ctx._abierta, ctx.tab_pa)
    # ============================================================================
    # PARTIDAS
    # ============================================================================
    if _abierta(tab_pa):
        with tab_pa:
            seccion("Partidas", "Guardá tu progreso en un archivo y retomalo cuando quieras", "#2f7fd0")
            aviso("El archivo guarda <b>todo</b>: ligas, copas, calendario, historial y, si jugás en modo Manager, "
                  "tu carrera. Podés cargarlo antes de empezar a simular o en cualquier momento.")
            c1, c2 = st.columns(2, gap="large")
            with c1:
                _guardar(ctx)
            with c2:
                _cargar(ctx)
