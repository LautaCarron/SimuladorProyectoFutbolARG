"""Cuánto se jugó de la temporada: qué terminó, porcentajes y avisos. Sin Streamlit.

Antes estos cálculos eran ~25 variables sueltas en simuladorafa.py que las pestañas leían por `globals()`.
"""

from dataclasses import dataclass

from copas.conmebol import terminadas as conmebol_terminadas
from copas.registro import REGISTRO
from ligas.nacional import total_b
from ligas.primera import primera_terminada, total_primera


def _pct(hecho, total):
    return 100 * hecho / total if total else 0


@dataclass(frozen=True)
class Progreso:
    terminada: bool            # Primera (incluye las fechas de desempate)
    terminada_b: bool
    terminada_f: bool
    terminada_fb: bool         # sin Federal B no hay nada que esperar
    terminada_pb: bool
    terminada_pc: bool
    terminada_pd: bool
    terminada_reg: bool
    terminada_copa: bool
    terminadas_extra: bool     # Copa Argentina, Supercopa y Mundial (si hay)
    terminadas_int: bool       # copas CONMEBOL
    todas: bool                # ¿se puede pasar a la próxima temporada?
    b_espera_primera: bool     # la B Nacional espera el 27° definitivo de Primera
    pct_p: float
    pct_b: float
    pct_f: float
    pct_fb: float
    pct_pb: float
    pct_pc: float
    pct_pd: float
    pct_reg: float
    pct_copa: float
    partidos_jugados: int

    @classmethod
    def desde_estado(cls, S):
        SB, SF, SFB, SPB, SPC, SPD, SR, SC = S["b"], S["f"], S.get("fb"), S["pb"], S["pc"], S["pd"], S["reg"], S["copa"]
        terminada = primera_terminada(S)
        t_b = SB["fecha"] >= total_b(SB)
        t_f = SF["fecha"] >= SF["total"]
        t_fb = SFB is None or SFB["fecha"] >= SFB["total"]
        t_pb = SPB["fecha"] >= SPB["total"]
        t_pc = SPC["fecha"] >= SPC["total"]
        t_pd = SPD["fecha"] >= SPD["total"]
        t_reg = SR["fecha"] >= SR["total"]
        t_copa = SC["sorteada"] and SC["ronda"] >= SC["total"]
        t_extra = all(comp.terminada(S) for comp in REGISTRO)
        t_int = conmebol_terminadas(S)
        jugados = (len(S["log"]) + len(SB["log"]) + len(SF["log"]) + (len(SFB["log"]) if SFB else 0)
                   + len(SPB["log"]) + len(SPC["log"]) + len(SR["log"])
                   + sum(len(comp.log(S)) for comp in REGISTRO))
        return cls(
            terminada=terminada, terminada_b=t_b, terminada_f=t_f, terminada_fb=t_fb, terminada_pb=t_pb,
            terminada_pc=t_pc, terminada_pd=t_pd, terminada_reg=t_reg, terminada_copa=t_copa,
            terminadas_extra=t_extra, terminadas_int=t_int,
            todas=(terminada and t_b and t_f and t_fb and t_pb and t_pc and t_pd and t_reg
                   and t_copa and t_extra and t_int),
            b_espera_primera=SB["fecha"] == total_b(SB) - 1 and not terminada,
            pct_p=_pct(S["fecha"], total_primera(S)), pct_b=_pct(SB["fecha"], total_b(SB)),
            pct_f=_pct(SF["fecha"], SF["total"]), pct_fb=_pct(SFB["fecha"], SFB["total"]) if SFB else 0,
            pct_pb=_pct(SPB["fecha"], SPB["total"]), pct_pc=_pct(SPC["fecha"], SPC["total"]),
            pct_pd=_pct(SPD["fecha"], SPD["total"]), pct_reg=_pct(SR["fecha"], SR["total"]),
            pct_copa=_pct(SC["ronda"], SC["total"]), partidos_jugados=jugados,
        )


def avisos_de_temporada(S):
    """Avisos (suspensiones y sanciones) de esta temporada, de todas las competencias."""
    ligas = (S, S["b"], S["f"], *([S["fb"]] if S.get("fb") else []), S["pb"], S["pc"], S["reg"], S["copa"])
    return [a for L in ligas for a in L.get("alertas", [])]
