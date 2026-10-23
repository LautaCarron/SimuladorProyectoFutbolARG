"""Correr JavaScript en la página de la app (va en ui/js.py).

st.html(..., unsafe_allow_javascript=True) no siempre ejecuta el script (según la versión de Streamlit el
sanitizador lo descarta), así que se usa un iframe chiquito que agrega el script a la página de arriba:
st.iframe en las versiones nuevas (components.html quedó deprecado) y components.html en las viejas.
El iframe va en un contenedor escondido para que no ocupe lugar.
"""

import json

import streamlit as st


def inyectar_js(js, clave):
    """Agrega el script `js` (con o sin <script>) a la página. `clave`: nombre único del contenedor."""
    cuerpo = js.replace("<script>", "").replace("</script>", "")
    html = ("<script>const s = window.parent.document.createElement('script');"
            f"s.textContent = {json.dumps(cuerpo)};"
            "window.parent.document.head.appendChild(s);</script>")
    st.html(f"<style>.st-key-{clave}{{position:absolute !important;width:0;height:0;overflow:hidden;"
            "opacity:0;pointer-events:none;}</style>")
    with st.container(key=clave):
        if hasattr(st, "iframe"):
            st.iframe(html, height=1)
        else:
            import streamlit.components.v1 as components
            components.html(html, height=0)
