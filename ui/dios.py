"""Modo dios del simulador (va en ui/dios.py): cambiar los campeonatos desde la barra lateral.

Por ahora: Primera División (formato y cantidad de descensos). Cuando Primera todavía no empezó la temporada
los cambios se aplican en el momento; si ya empezó, se guardan para la temporada que viene. Lo que se elige
queda guardado en S["cfg"]["primera"] y se usa cada vez que se arma una temporada (ver ligas/primera.py).
"""

import streamlit as st
from datos.equipos import N
from ligas.primera import DESCENSOS_MAX, FORMATOS, cfg_primera, descensos, formato, nueva_estructura

DETALLE = {
    "actual": "Fase 1 de 29 fechas todos contra todos y fase 2 de 9 fechas en tres zonas (Campeonato, Intermedia "
              "y Descenso). Campeón: el 1° de la zona Campeonato.",
    "anual_ida": "29 fechas todos contra todos, una sola tabla. Campeón: el 1°.",
    "anual_ida_vuelta": "58 fechas, todos contra todos ida y vuelta, una sola tabla. Campeón: el 1°.",
    "apertura_clausura": "Dos torneos con dos zonas de 15 (15 fechas cada uno) y llaves con los 8 primeros de cada "
                         "zona. Hay campeón del Apertura, del Clausura y de Liga: el 1° de la tabla anual (suma de "
                         "las dos etapas regulares), que además define la copa y los descensos.",
}


def panel_dios(S):
    cfg = cfg_primera(S)
    empezo = S["fecha"] > 0 or bool(S["log"])
    formatos = list(FORMATOS)
    with st.sidebar:
        st.divider()
        st.header("Modo dios")          # mismo estilo (h2) que "Parámetros de simulación", siempre desplegado
        st.caption("Cambiá los campeonatos. " + ("Primera ya empezó: lo que elijas rige desde la próxima temporada."
                                                  if empezo else "Primera no empezó: se aplica ahora mismo."))
        st.markdown("**Primera División**")
        fmt = st.selectbox("Formato", formatos, format_func=FORMATOS.get, key="dios_formato",
                           index=formatos.index(cfg["formato"] if cfg["formato"] in formatos else "actual"))
        k = st.slider("Descienden a la B", 0, DESCENSOS_MAX, int(cfg["descensos"]), key="dios_k",
                      help="El puesto N-k juega la promoción contra el perdedor del reducido de la B; "
                           "suben de la B tantos como bajan.")
        st.caption(DETALLE[fmt])
        st.caption(f"Descienden {k} directo a la B" + (f" (puestos {N - k + 1}° a {N}°)" if k else "")
                   + f"; el {N - k}° juega la promoción. Suben {k} de la B: campeón, 2°, ganador del reducido y, "
                   "si hacen falta más, los siguientes de la Zona Campeonato.")
        cambio = (fmt != cfg["formato"]) or (k != int(cfg["descensos"]))
        if st.button(":material/save: " + ("Guardar para la próxima temporada" if empezo else "Aplicar ahora"),
                     key="dios_aplicar", width="stretch", type="primary", disabled=not cambio):
            cfg["formato"], cfg["descensos"] = fmt, int(k)
            if not empezo:
                nueva_estructura(S)                    # Primera no empezó: se rearma con el formato nuevo
            st.rerun()
        if formato(S) != cfg["formato"] or descensos(S) != int(cfg["descensos"]):
            st.caption(f"Esta temporada se juega con: {FORMATOS[formato(S)]}, {descensos(S)} descensos.")
