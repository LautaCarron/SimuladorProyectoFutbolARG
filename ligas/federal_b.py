"""Federal B (va en ligas/federal_b.py): categoría que se crea desde el Modo dios entre el Federal A y el
Regional Amateur.

* Formato: el mismo del Federal A (grupos por cercanía, zonas Campeonato y Descenso y reducido); el motor es el
  de ligas/federal.py, que sabe jugar cualquiera de las dos (ver `SF["liga"]` y `SF["cfg_clave"]`).
* Se crea al terminar la temporada en la que se elige en el Modo dios: los que bajan del Federal A pasan al
  Federal B y se completan 20 equipos con los mejores del Regional Amateur (ver `elegir_del_regional`).
* Desde entonces: los ascendidos del Federal B suben al Federal A, los que bajan del Federal A caen al Federal B,
  los ganadores de las finales del Regional suben al Federal B y los que descienden del Federal B bajan al Regional.
* Estado: `S["fb"]` es la liga (igual que `S["f"]`), `S["federal_b"]` la lista de clubes (como `S["federal"]`) y
  `S["cfg"]["federal_b"]` lo elegido en el Modo dios. Hasta que se crea, `S.get("fb")` es None y la categoría no se
  ve en ninguna parte (tampoco su palmarés, `S["hist_federalB"]`).
"""

import numpy as np

from datos.equipos import F_GRUPOS_NOMBRES  # noqa: F401  (los grupos por cercanía son los del Federal A)
from ligas.federal import cfg_federal, nueva_estructura_f

LIGA_FB = "Federal B"
FB_EQUIPOS = 20                    # equipos con los que nace el Federal B

# Qué pasa con los 6 ganadores de las finales del Regional el año en que se crea el Federal B:
#   True  -> suben al Federal A como siempre (el Federal A conserva su tamaño) y el Federal B se completa con los
#            mejores del Regional que no ascienden.
#   False -> suben directo al Federal B (se cuentan entre los 20) y el Federal A queda con 6 equipos menos.
CREACION_MANTIENE_FEDERAL_A = True


def cfg_federal_b(S):
    """Lo elegido en el Modo dios para el Federal B (ascensos, reducido y descensos) y si hay que crearlo."""
    c = cfg_federal(S, "federal_b")
    c.setdefault("crear", False)
    return c


def activo(S):
    """True si el Federal B ya existe y se está jugando."""
    return S.get("fb") is not None


def pendiente(S):
    """True si se pidió crearlo en el Modo dios pero todavía no se armó (se arma en el pase de temporada)."""
    return bool(cfg_federal_b(S).get("crear")) and not activo(S)


def destino_ascenso_regional(S):
    """A dónde suben los 6 ganadores de las finales del Regional esta temporada: al Federal B si ya existe (o si se
    crea y no se mantiene el tamaño del Federal A), si no al Federal A."""
    if activo(S) or (pendiente(S) and not CREACION_MANTIENE_FEDERAL_A):
        return LIGA_FB
    return "Federal A"


def destino_descenso_federal_a(S):
    """A dónde bajan los que descienden del Federal A: al Federal B si existe o se está por crear."""
    return LIGA_FB if (activo(S) or pendiente(S)) else "Regional Amateur"


def elegir_del_regional(SR, excluir, cantidad):
    """Los `cantidad` mejores del Regional Amateur (fuera de los de `excluir`), según cómo salieron en la temporada.

    Se ordenan por puesto en la liga de su región (los 6 campeones regionales que perdieron la final por el
    ascenso salen primero, después los segundos de cada región y así), y a igual puesto por puntos por partido,
    diferencia de gol por partido, goles a favor por partido y media interna."""
    from ligas.regional import tabla_reg_region
    if cantidad <= 0:
        return []
    excluir = set(excluir)
    candidatos = []
    for reg, ids in SR["grupos"].items():
        if len(ids) == 0:
            continue
        df = tabla_reg_region(SR, reg)
        for _, f in df.iterrows():
            nom = SR["nombres"][int(f["id"])]
            if nom in excluir:
                continue
            pj = max(int(f["PJ"]), 1)
            candidatos.append((int(f["Pos"]), -float(f["Pts"]) / pj, -float(f["DG"]) / pj,
                               -float(f["GF"]) / pj, -float(SR["r"][int(f["id"])]), nom))
    candidatos.sort()
    return [c[-1] for c in candidatos[:cantidad]]


def nueva_liga_fb(S, rng):
    """Arma la liga del Federal B con los clubes de `S["federal_b"]` (la primera vez la crea; después la
    renueva para la temporada que empieza). Devuelve el estado de la liga."""
    nombres = list(S["federal_b"])
    SFB = S.get("fb") or {"liga": LIGA_FB, "cfg_clave": "federal_b"}
    SFB["nombres"] = nombres
    SFB["r"] = np.array([S["rating"][n] for n in nombres], dtype=float)
    nueva_estructura_f(SFB, rng, S)
    S["fb"] = SFB
    return SFB
