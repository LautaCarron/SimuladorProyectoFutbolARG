"""Piezas de interfaz de los formatos de Primera del Modo dios (va en ui/vista/formatos.py).

  * colorear_llaves(fila):  pinta a los que pasan a las llaves en las zonas del Apertura / Clausura.
  * cuadro_ac_html(S, t):   llaves (octavos, cuartos, semis, final y campeón) de un torneo del Apertura/Clausura,
                            con el mismo cuadro que la Copa Argentina.
"""

from ligas.apertura_clausura import NOMBRES
from ui.vista.base import COLORES_B
from ui.vista.cuadros import _kb, _kb_card, _kb_col, _kb_final


def colorear_llaves(fila):
    c = COLORES_B["Ascenso directo"] if fila.get("Destino") == "Pasa a las llaves" else ""
    return [f"background-color: {c}" if c else ""] * len(fila)


def cuadro_ac_html(S, t):
    """Llaves del torneo t (0 Apertura, 1 Clausura): rondas ya armadas y "A definir" en las que faltan."""
    T = S["ac"]["T"][t]
    SC = {"nombres": S["nombres"], "origen": ["Primera División"] * len(S["nombres"])}
    cols = []
    for k, (titulo, n) in enumerate((("Octavos", 8), ("Cuartos", 4), ("Semis", 2), ("Final", 1))):
        ronda = T["cuadro"][k] if k < len(T["cuadro"]) else [None] * n
        if n == 1:
            cols.append(_kb_col(titulo, f'<div class="kb-slot kb-solo">{_kb_card(SC, ronda[0])}</div>'))
        else:
            cuerpo = "".join(f'<div class="kb-pair"><div class="kb-slot">{_kb_card(SC, ronda[j])}</div>'
                             f'<div class="kb-slot">{_kb_card(SC, ronda[j + 1])}</div></div>' for j in range(0, n, 2))
            cols.append(_kb_col(titulo, cuerpo))
    c = T["campeon"]
    cols.append(_kb_final(f"Campeón · {NOMBRES[t]}", "Campeón", S["nombres"][c] if c is not None else None, ""))
    return _kb(cols, 8 * 74)
