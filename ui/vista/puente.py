"""Puente: tocar un club en cualquier tabla abre su ficha; tocar un día del calendario lo elige.
"""

import json
import sys
import streamlit as st

from ui.vista.ficha import ver_equipo


# ---- Puente: tocar un club en cualquier tabla abre su ficha -----------------
# Las tablas son HTML (no widgets), así que un script chico escucha los toques sobre
# [data-club] y le pasa el nombre a un campo oculto de Streamlit; ese campo abre la misma
# ficha (ver_equipo) que usa la sección Clubes.
_PUENTE_JS = """
<script>
// Dos bloques con guardas separadas: si la página ya tenía instalada una versión vieja del puente (sólo
// clubes), el bloque de los días igual se instala sin tener que recargar ni duplicar el de los clubes.
(function () {                                     // ---- clubes y "Simular todo"
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
(function () {                                     // ---- días del calendario (elegir el destino de "simular hasta esa fecha")
  if (window.__afaPuenteDias) return;
  window.__afaPuenteDias = true;
  function abrirDia(iso) {
    const inp = document.querySelector('.st-key-puente_dia input');
    if (!inp) return;
    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    set.call(inp, iso);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
  }
  document.addEventListener('click', function (e) {
    const d = e.target.closest && e.target.closest('[data-dia]');
    if (!d) return;
    e.preventDefault();
    abrirDia(d.dataset.dia);
  });
  document.addEventListener('keydown', function (e) {
    const t = e.target;
    if ((e.key === 'Enter' || e.key === ' ') && t && t.matches && t.matches('[data-dia]')) {
      e.preventDefault();
      abrirDia(t.dataset.dia);
    }
  });
})();
</script>
"""


def _instalar_puente_js():
    """Corre el script en la página. En la web estática (stlite) con st.html(unsafe_allow_javascript);
    con Streamlit (Community Cloud o la PC) con un iframe que lo inyecta en la página de arriba,
    porque ahí el sanitizador de st.html puede descartar el script."""
    try:
        if sys.platform != "emscripten":
            raise TypeError
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


def _dia_elegido():
    """Llega un día del calendario ("2026-03-04"); lo lee la pestaña Calendario."""
    st.session_state["_dia_a_elegir"] = st.session_state.get("puente_dia", "")
    st.session_state["puente_dia"] = ""


def puente_clubes():
    """Campos ocultos + script que conectan los clubes de las tablas con su ficha y los días del calendario
    con su selección."""
    with st.container(key="puente"):
        st.text_input("club", key="puente_club", on_change=_club_elegido,
                      label_visibility="collapsed")
        st.text_input("dia", key="puente_dia", on_change=_dia_elegido,
                      label_visibility="collapsed")
        _instalar_puente_js()
    nombre = st.session_state.pop("_club_a_abrir", "")
    if nombre:
        ver_equipo(nombre)
