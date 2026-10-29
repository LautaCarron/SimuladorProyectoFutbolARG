"""Sección "Mi club" de la pestaña Partidas: crear UN solo club propio, verlo y darlo de baja.

El club vive en la partida (se guarda con ella y desaparece con una partida nueva). Al crearlo queda pendiente y entra al
Regional Amateur (si es del interior) o al Promocional Amateur (si es metropolitano) cuando empieza la temporada que
viene. Se eligen los datos con campos ya armados (provincia y liga salen
de las que existen en el Regional), la región se completa sola a partir de la liga (Liga Marplatense -> Pampeana Sur) y el
escudo es una foto de hasta 1 MB. Si se lo da de baja, pierde por 0-3 lo que le quede por jugar, desaparece al terminar
la temporada y sólo quedan su nombre y su escudo en el palmarés. Datos en datos/club_propio.py y lógica en
motor/club_usuario.py.
"""

import streamlit as st

from datos import club_propio as cp
from motor import club_usuario as cu
from ui.vista import aviso, chip, esc

_TIPOS = ["png", "jpg", "jpeg", "webp"]


def _tarjeta(club, etiqueta):
    img = (f'<img class="crest-img" src="{esc(club["escudo"])}" width="64" height="64" alt="">' if club["escudo"]
           else '<span class="crest" style="width:64px;height:66px;font-size:23px;background:linear-gradient(160deg,'
                'hsl(214,62%,44%),hsl(240,58%,28%))">'
                + esc("".join(w[0] for w in club["nombre"].split()[:2]).upper() or "?") + "</span>")
    st.markdown(
        f'<div class="team-head">{img}<div><div class="tn">{esc(club["nombre"])}</div><div style="margin-top:6px">'
        f'{chip(etiqueta)} {chip(club.get("region") or "Metropolitana", "#475569")}</div></div></div>'
        + (f'<div style="font-size:.85rem;opacity:.75;margin:-2px 0 8px">{esc(club["ciudad"])}, {esc(club["provincia"])} · '
           f'{esc(club["liga"])}</div>' if club.get("ciudad") else ""), unsafe_allow_html=True)


def _limpiar_formulario():
    for k in [k for k in st.session_state if str(k).startswith("cc_")]:
        del st.session_state[k]


def _formulario(S):
    """Campos del club nuevo. Devuelve el club armado, o None si falta algo (y muestra qué)."""
    errores = []
    origen = st.radio("¿De dónde es el club?", [cp.INTERIOR, cp.METROPOLITANA], key="cc_origen", horizontal=True,
                      captions=["Arranca en el Regional Amateur", "CABA / Gran Buenos Aires: arranca en el Promocional"])
    metro = origen == cp.METROPOLITANA
    nombre = st.text_input("Nombre del club", key="cc_nombre", max_chars=cp.MAX_NOMBRE,
                           placeholder="Ej: Club Atlético Los Pinos")
    provincia = liga = ciudad = None
    if not metro:
        c1, c2 = st.columns(2)
        provincia = c1.selectbox("Provincia", cp.PROVINCIAS, index=None, key="cc_provincia",
                                 placeholder="Elegí la provincia…")
        ligas = cp.LIGAS_POR_PROVINCIA.get(provincia, [])
        liga = c2.selectbox("Liga", ligas, index=None, key=f"cc_liga_{provincia}", disabled=not provincia,
                            placeholder="Elegí la liga…" if provincia else "Primero la provincia")
        c3, c4 = st.columns(2)
        ciudad = c3.text_input("Ciudad", key="cc_ciudad", max_chars=40, placeholder="Ej: Mar del Plata")
        region = cp.region_de_liga(provincia, liga) if provincia and liga else None
        c4.text_input("Región (automática)", value=region or "Según la liga", disabled=True, key=f"cc_region_{region}")
    media = st.slider("Nivel del club", cp.MEDIA_MIN, cp.MEDIA_MAX, cp.MEDIA_INICIAL_METRO if metro else cp.MEDIA_INICIAL,
                      key=f"cc_media_{origen}",
                      help=f"Mínimo {cp.MEDIA_MIN}. Referencia: en el Regional van de 20 a 33 y en el Promocional de 18 a 31. "
                           "Cambia solo de una temporada a otra, como la de todos.")
    archivo = st.file_uploader("Escudo (foto)", type=_TIPOS, key="cc_escudo",
                               help="PNG, JPG o WEBP de hasta 1 MB. Se achica para guardarlo con la partida.")
    escudo = ""
    if archivo is not None:
        escudo, err = cp.procesar_escudo(archivo.getvalue())
        if err:
            errores.append(err)
            escudo = ""
    else:
        st.caption("Opcional: sin foto se dibuja con las iniciales del club.")

    if not nombre.strip():
        errores.append("Falta el nombre del club.")
    elif (e := cp.nombre_valido(nombre)):
        errores.append(e)
    if not metro:
        if not provincia:
            errores.append("Elegí la provincia.")
        elif not liga:
            errores.append("Elegí la liga.")
        if not ciudad.strip():
            errores.append("Falta la ciudad.")
    if errores:
        for e in dict.fromkeys(errores):
            st.caption(f":material/error: {e}")
        return None
    club = cp.crear(nombre, provincia or "", liga or "", ciudad or "", media, escudo, ocupados=cu.nombres_ocupados(S),
                    origen=origen)
    if club["nombre"] != " ".join(nombre.split()):
        aviso(f"Ya existe un <b>{esc(' '.join(nombre.split()))}</b> en el palmarés: tu club entra como "
              f"<b>{esc(club['nombre'])}</b> para que sus títulos no se mezclen con los de ese club.")
    with st.container(border=True):
        _tarjeta(club, "Promocional Amateur" if metro else "Regional Amateur")
    return club


def render_seccion(ctx):
    S = ctx.S
    st.markdown('<div class="mlab" style="margin-top:22px">Mi club</div>', unsafe_allow_html=True)
    propio, pendiente = S.get("club_propio"), S.get("club_pendiente")
    en_manager = bool(ctx.manager) and propio and ctx.manager.get("club") == propio["nombre"]

    if propio and not propio.get("baja"):
        with st.container(border=True):
            _tarjeta(propio, "Mi club")
            if en_manager:
                st.caption("Lo estás dirigiendo en el modo Manager: no se puede dar de baja.")
            else:
                with st.popover(":material/delete: Dar de baja el club"):
                    st.markdown(
                        "Lo que le quede por jugar esta temporada lo **pierde 3-0** y el club **desaparece al "
                        "terminar la temporada**. Si ganó títulos, en el palmarés quedan su nombre y su escudo.")
                    if st.button("Sí, dar de baja", key="cc_baja", type="primary", width="stretch"):
                        cu.dar_de_baja(S)
                        st.rerun()
    elif propio:
        aviso(f"<b>{esc(propio['nombre'])}</b> está dado de baja: pierde 0-3 lo que le queda de la temporada y "
              "desaparece al terminarla. Mientras tanto ya podés crear un club nuevo.")

    if pendiente:
        with st.container(border=True):
            _tarjeta(pendiente, f"Entra en la temporada {S['temp'] + 1}")
            if st.button(":material/close: Cancelar", key="cc_cancelar", width="stretch"):
                cu.cancelar_pendiente(S)
                st.rerun()
        destino = "Promocional Amateur" if pendiente.get("origen") == cp.METROPOLITANA else "Regional Amateur"
        st.caption(f"Se suma al {destino} cuando empiece la temporada que viene.")
    elif cu.puede_crear(S):
        st.caption("Un solo club. Si es del interior entra al Regional Amateur; si es metropolitano, directo al Promocional "
                   "Amateur. Se suma cuando empieza la temporada que viene.")
        club = _formulario(S)
        if st.button(":material/add: Crear mi club", key="cc_crear", type="primary", width="stretch",
                     disabled=club is None):
            cu.crear_pendiente(S, club)
            _limpiar_formulario()
            st.rerun()
