"""Mi club (modo manager): qué club dirige el manager, en qué competencias juega y cómo se marca en pantalla.

Va en ui/vista/mi_club.py. Sólo usa streamlit y funciones de lectura del estado S.

  * mi_club()                  -> nombre del club que dirige el manager (None si está libre o en modo simulación).
                                  simuladorafa.py lo deja en st.session_state["_mi_club"] en cada ejecución.
  * competencias_club(S, club) -> claves de las pestañas donde compite el club ("p", "ca", "lib", ...).
  * estilo_mi_club(club)       -> <style> que pinta de amarillo al club en tablas, grupos, cuadros y partidos.
"""

import streamlit as st

from motor.ofertas import categoria_de

AMARILLO = "rgba(250, 204, 21, {a})"
AMARILLO_BORDE = "#eab308"

# categoría -> clave de la pestaña de Ligas
CLAVE_LIGA = {"Primera División": "p", "Primera Nacional": "b", "Federal A": "f", "Regional Amateur": "reg",
              "Primera B": "pb", "Primera C": "pc", "Promocional Amateur": "pd"}


def mi_club():
    return st.session_state.get("_mi_club")


def _en_copa_int(C, club):
    if not C:
        return False
    if club in (C.get("via") or {}):
        return True
    if any(club in (p["local"], p["visita"]) for p in C.get("log", [])):
        return True
    if any(club in eq for eq in (C.get("grupos") or [])):
        return True
    return any(x and club in (x["a"], x["b"]) for series in (C.get("llaves") or {}).values() for x in series)


def competencias_club(S, club):
    """Claves de pestaña de las competencias en las que juega el club esta temporada."""
    out = set()
    if not club:
        return out
    cat = categoria_de(S, club)
    if cat in CLAVE_LIGA:
        out.add(CLAVE_LIGA[cat])
    SC = S.get("copa") or {}
    if SC.get("sorteada") and club in SC.get("nombres", []):
        out.add("ca")
    SS = S.get("supercopa") or {}
    if SS.get("jugada"):
        if club in (SS.get("a"), SS.get("b")):
            out.add("sup")
    else:
        try:
            from copas.argentina import rivales_supercopa, supercopa_lista
            if supercopa_lista(S):
                a, _, _, b, _, _ = rivales_supercopa(S)
                if club in (a, b):
                    out.add("sup")
        except Exception:
            pass
    for clave in ("lib", "sud", "rec"):
        if _en_copa_int((S.get("int") or {}).get(clave), club):
            out.add(clave)
    M = S.get("mundial") or {}
    if M.get("sorteado") and club in M.get("nombres", []):
        out.add("mun")
    return out


def estilo_mi_club(club):
    """CSS que marca a `club` en amarillo. Las tablas, grupos y cuadros llevan data-club en el nombre,
    así que se marca la fila entera con :has(). Los partidos usan la clase .mio y, en el fixture,
    un contenedor cuya key empieza con mi_partido_."""
    n = club.replace("\\", "\\\\").replace('"', '\\"')
    sel = f'[data-club="{n}"]'
    f = AMARILLO
    return f"""<style>
.tabla tbody tr:has({sel}) td {{ --rc: {f.format(a=0.36)} !important; }}
.tabla tbody tr:has({sel}) td:first-child {{ box-shadow: inset 3px 0 0 {AMARILLO_BORDE}; }}
.grp-t tr:has({sel}) {{ background: {f.format(a=0.28)} !important; }}
.grp-t tr:has({sel}) td.gp {{ box-shadow: inset 3px 0 0 {AMARILLO_BORDE}; }}
.kb-t:has({sel}) {{ background: {f.format(a=0.30)} !important; box-shadow: inset 3px 0 0 {AMARILLO_BORDE} !important; }}
.rk tr:has({sel}), .pal-f:has({sel}) {{ background: {f.format(a=0.26)} !important; }}
.mrow.mio, .cal-p.mio {{ background: {f.format(a=0.20)}; box-shadow: inset 3px 0 0 {AMARILLO_BORDE}; border-radius: 6px; }}
[class*="st-key-mi_partido_"] {{ background: {f.format(a=0.20)}; box-shadow: inset 3px 0 0 {AMARILLO_BORDE}; border-radius: 8px; }}
</style>"""
