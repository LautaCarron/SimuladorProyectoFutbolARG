"""Puente: tocar un club en cualquier tabla abre su ficha.
"""

import json
import streamlit as st

from ui.vista.ficha import ver_equipo


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
  // "Simular todo": el botón pasa a decir "Simulando…" hasta que la app termina de trabajar
  let quieto = null;
  document.addEventListener('click', function (e) {
    const b = e.target.closest && e.target.closest('button');
    if (b && !b.disabled && b.innerText.trim().endsWith('Simular todo')) b.classList.add('afa-simulando');
  }, true);
  new MutationObserver(function () {
    const app = document.querySelector('.stApp');
    if (!app) return;
    clearTimeout(quieto);
    if (app.getAttribute('data-test-script-state') !== 'running') {
      quieto = setTimeout(function () {
        document.querySelectorAll('button.afa-simulando').forEach(function (x) { x.classList.remove('afa-simulando'); });
      }, 600);
    }
  }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['data-test-script-state'] });
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
