"""Mi club (modo manager): qué club dirige el manager, en qué competencias juega y cómo se marca en pantalla.

Va en ui/vista/mi_club.py. Sólo usa streamlit y funciones de lectura del estado S.

  * mi_club()                  -> nombre del club que dirige el manager (None si está libre o en modo simulación).
                                  simuladorafa.py lo deja en st.session_state["_mi_club"] en cada ejecución.
  * competencias_club(S, club) -> claves de las pestañas donde compite el club ("p", "ca", "lib", ...).
  * estilo_mi_club(club)       -> <style> que pinta de amarillo al club en tablas, grupos, cuadros y partidos.
  * mi_zona(S, liga, fase1)    -> zona / grupo / región de mi club dentro de una liga ("p", "b", "f", "reg").
  * tabs_zona(etiquetas, zona, clave) -> st.tabs con ⭐ y abierta por defecto en la zona de mi club.
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


def modo_manager():
    """True si se está jugando en modo manager (con o sin club). simuladorafa.py lo deja en cada ejecución."""
    return bool(st.session_state.get("_modo_manager"))


# ---- En qué zona / región juega mi club dentro de su liga --------------------------------------
# Devuelven la MISMA etiqueta que usa la pestaña de esa zona (o None si el club no juega esa liga), para
# abrirla sola y marcarla con ⭐. Usan la misma condición de fase que cada pestaña.
def marcar(etiquetas, mia):
    """Agrega ⭐ a la etiqueta `mia`. Devuelve (etiquetas nuevas, etiqueta a abrir por defecto o None)."""
    return [e + " ⭐" if e == mia else e for e in etiquetas], (mia + " ⭐" if mia in etiquetas else None)


def zona_primera(S, club):
    """Primera: en la fase 2, "Zona Campeonato / Intermedia / Descenso". En la fase 1 hay una sola tabla."""
    from ligas.primera import ZONAS
    if S["fase"] != 2 or S.get("zona_de") is None or club not in S["nombres"]:
        return None
    return f"Zona {ZONAS[S['zona_de'][S['nombres'].index(club)]]}"


def zona_nacional(SB, club):
    """Primera Nacional: fase 1 "Zona A / Zona B"; fase 2 "Zona Campeonato / Intermedia / Descenso"."""
    from ligas.nacional import B_F1, B_ZONAS2
    if club not in SB["nombres"]:
        return None
    i = SB["nombres"].index(club)
    if SB["fecha"] < B_F1:
        return f"Zona {'AB'[SB['zona_de'][i]]}"
    if SB.get("zona2_de") is None:
        return None
    return f"Zona {B_ZONAS2[SB['zona2_de'][i]]}"


def zona_federal(SF, club):
    """Federal A: fase 1 el grupo por cercanía; fase 2 "Campeonato" o "Descenso"."""
    from datos.equipos import F_GRUPOS_NOMBRES
    if club not in SF["nombres"]:
        return None
    i = SF["nombres"].index(club)
    if SF["fecha"] < SF["f1_rondas"]:
        return F_GRUPOS_NOMBRES[SF["grupo_de"][i]]
    if SF.get("zona2_de") is None or SF["zona2_de"][i] < 0:
        return None
    return ["Campeonato", "Descenso"][SF["zona2_de"][i]]


def region_de_club(SR, club):
    """Regional Amateur: la región del club."""
    if club not in SR["nombres"]:
        return None
    return SR["region_de"][SR["nombres"].index(club)]


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


# ---- Zona de mi club dentro de su liga -------------------------------------------
def mi_zona(S, liga, fase1=False):
    """Zona de mi club en la fase actual de la liga (None si no juega esa liga o todavía no hay zonas):
       "p"   Primera: 0 Campeonato, 1 Intermedia, 2 Descenso (desde la fase 2).
       "b"   Primera Nacional: fase 1 -> 0 Zona A / 1 Zona B; fase 2 -> 0 Campeonato, 1 Intermedia, 2 Descenso.
       "f"   Federal A: fase 1 -> grupo 0-4 (por cercanía); fase 2 -> 0 Campeonato / 1 Descenso.
       "reg" Regional Amateur: nombre de la región.
    `fase1` lo calcula cada pestaña con la misma condición que ya usa para dibujar la fase."""
    club = mi_club()
    if not club:
        return None
    try:
        if liga == "reg":
            SR = S["reg"]
            return SR["region_de"][SR["nombres"].index(club)] if club in SR["nombres"] else None
        L = {"p": S, "b": S["b"], "f": S["f"]}[liga]
        if club not in L["nombres"]:
            return None
        if liga == "p":
            z = L.get("zona_de")                              # sólo existe desde la fase 2
        elif liga == "b":
            z = L.get("zona_de") if fase1 else L.get("zona2_de")
        else:
            z = L.get("grupo_de") if fase1 else L.get("zona2_de")
        if z is None:
            return None
        v = int(z[L["nombres"].index(club)])
        return v if v >= 0 else None
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def tabs_zona(etiquetas, zona, clave):
    """st.tabs de zonas/grupos. Con un club dirigido, la zona de mi club lleva ⭐ y se abre sola.
    La key lleva el club y la zona: si cambia cualquiera de los dos, vuelve a abrirse en la zona nueva."""
    club = mi_club()
    if not club or zona is None or not (0 <= zona < len(etiquetas)):
        return st.tabs(etiquetas)
    marcadas = list(etiquetas)
    marcadas[zona] = f"{etiquetas[zona]} ⭐"
    slug = "".join(c if c.isalnum() else "_" for c in club)
    return st.tabs(marcadas, default=marcadas[zona], key=f"{clave}_{slug}_{zona}")
