"""Copas: Copa Argentina.

Copa Argentina: 128 equipos, eliminación directa a partido único desde 64avos de final.
Todos los partidos en cancha neutral; si empatan, penales. Se juega durante la temporada
(los miércoles, en el medio de las ligas: ver calendario.py).

Clasifican, como en la vida real, por lo hecho en la temporada anterior:
  * Primera División: los 30.
  * Primera Nacional: los 36.
  * Federal A: los 20 de la Zona Campeonato y los 8 mejores de la Zona Descenso.
  * Primera B: los 12 primeros.
  * Primera C: los 10 primeros.
  * Regional Amateur: los campeones de las 12 regiones.
En la temporada 1 (no hay anterior) entran los de mejor media de cada liga. Si alguna liga no
llega a su cupo (p. ej. una región sin campeón), el lugar lo ocupa el siguiente mejor de la
Zona Descenso del Federal A.

Supercopa Argentina: partido único en cancha neutral entre el campeón de Primera y el campeón de
la Copa Argentina (si es el mismo club, el rival es el subcampeón de Primera). Se juega al terminar
las dos competencias; si empatan, penales.

Cruces de 64avos (por categoría, lo más justo): la categoría más alta contra la más baja,
la segunda contra la anteúltima y así (Primera vs. Regional Amateur, B Nacional vs. Primera C,
Federal A vs. Primera B); los que sobran se vuelven a cruzar con la misma regla. Dentro de
cada cruce de categorías el rival se sortea. El cuadro se divide en 8 llaves (A-H) de 16
equipos: el ganador de cada llave juega los cuartos.
"""

import numpy as np

from motor.incidentes import revisar_copa
from motor.nucleo import jugar_ko, nuevo_partido, tanda_penales
from datos.regional import REGIONES_REG
from ligas.federal import tabla_f_f2
from ligas.nacional import total_b
from ligas.primera import primera_terminada, tabla_final
from ligas.simples import tabla_pb, tabla_pc

COPA_ARG = "Copa Argentina"
SUPERCOPA = "Supercopa Argentina"
COPA_RONDAS = ["64avos de final", "32avos de final", "16avos de final", "Octavos de final",
               "Cuartos de final", "Semifinales", "Final"]
COPA_CORTO = ["64avos", "32avos", "16avos", "Octavos", "Cuartos", "Semifinal", "Final"]
COPA_LLAVES = "ABCDEFGH"
COPA_EQUIPOS = 128
_CATEGORIAS = ["Primera División", "Primera Nacional", "Federal A", "Primera B", "Primera C",
               "Regional Amateur"]


def nueva_copa():
    """Copa de la temporada, todavía sin sortear (se sortea al terminar las ligas)."""
    return {"sorteada": False, "nombres": [], "r": np.array([]), "origen": [], "criterio": [],
            "cuadro": [], "ronda": 0, "total": len(COPA_RONDAS), "log": [], "campeon": None}


def ligas_terminadas(S):
    SB, SF, SPB, SPC, SR = S["b"], S["f"], S["pb"], S["pc"], S["reg"]
    return (primera_terminada(S) and SB["fecha"] >= total_b(SB) and SF["fecha"] >= SF["total"]
            and SPB["fecha"] >= SPB["total"] and SPC["fecha"] >= SPC["total"]
            and SR["fecha"] >= SR["total"])


def clasificados_copa(S):
    """Los 128 clasificados: lista de (nombre, media, categoría, criterio)."""
    SB, SF, SPB, SPC, SR = S["b"], S["f"], S["pb"], S["pc"], S["reg"]
    lista = []

    def sumar(L, ids, cat, criterio):
        for k, i in enumerate(ids):
            lista.append((L["nombres"][int(i)], float(L["r"][int(i)]), cat, criterio(k)))

    sumar(S, range(len(S["nombres"])), "Primera División", lambda k: "Primera División")
    sumar(SB, range(len(SB["nombres"])), "Primera Nacional", lambda k: "Primera Nacional")
    camp = tabla_f_f2(SF, 0)["id"].to_numpy()
    desc = tabla_f_f2(SF, 1)["id"].to_numpy()
    sumar(SF, camp, "Federal A", lambda k: "Federal A · Zona Campeonato")
    sumar(SF, desc[:8], "Federal A", lambda k: f"Federal A · {k + 1}° Zona Descenso")
    sumar(SPB, tabla_pb(SPB)["id"].to_numpy()[:12], "Primera B", lambda k: f"Primera B · {k + 1}°")
    sumar(SPC, tabla_pc(SPC)["id"].to_numpy()[:10], "Primera C", lambda k: f"Primera C · {k + 1}°")
    campeones = [(reg, SR["campeones"].get(reg)) for reg in REGIONES_REG]
    for reg, c in campeones:
        if c is not None:
            lista.append((SR["nombres"][c], float(SR["r"][c]), "Regional Amateur", f"Campeón Regional {reg}"))
    extra = 8
    while len(lista) < COPA_EQUIPOS and extra < len(desc):      # cupos vacantes
        sumar(SF, desc[extra:extra + 1], "Federal A", lambda k, e=extra: f"Federal A · {e + 1}° Zona Descenso")
        extra += 1
    return lista[:COPA_EQUIPOS]


def clasificados_inicial(S):
    """Temporada 1: no hay temporada anterior, entran los de mejor media de cada liga."""
    SB, SF, SPB, SPC, SR = S["b"], S["f"], S["pb"], S["pc"], S["reg"]
    lista = [(n, "Primera División") for n in S["nombres"]] + [(n, "Primera Nacional") for n in SB["nombres"]]

    def mejores(L, k, criterio):
        orden = np.argsort(-np.asarray(L["r"]))[:k]
        return [(L["nombres"][int(i)], criterio) for i in orden]

    lista += mejores(SF, 28, "Federal A (por media)")
    lista += mejores(SPB, 12, "Primera B (por media)")
    lista += mejores(SPC, 10, "Primera C (por media)")
    for reg in REGIONES_REG:
        ids = [i for i, rg in enumerate(SR["region_de"]) if rg == reg]
        if ids:
            i = max(ids, key=lambda k: SR["r"][k])
            lista.append((SR["nombres"][i], f"Regional {reg} (por media)"))
    ya = {n for n, _ in lista}
    extra = [n for n in (SF["nombres"][int(i)] for i in np.argsort(-np.asarray(SF["r"]))) if n not in ya]
    while len(lista) < COPA_EQUIPOS and extra:
        lista.append((extra.pop(0), "Federal A (por media)"))
    return lista[:COPA_EQUIPOS]


def categoria_actual(S):
    """{club: (categoría, media)} de la temporada en curso."""
    out = {}
    for L, cat in ((S, "Primera División"), (S["b"], "Primera Nacional"), (S["f"], "Federal A"),
                   (S["pb"], "Primera B"), (S["pc"], "Primera C"), (S["reg"], "Regional Amateur")):
        for n, x in zip(L["nombres"], L["r"]):
            out[n] = (cat, float(x))
    return out


def _cruces_por_categoria(por_cat):
    """Arma los 64 cruces: la categoría más alta contra la más baja, la segunda contra la
    anteúltima, etc.; con los que sobran se repite la misma regla."""
    cruces = []
    while True:
        vivas = [c for c in _CATEGORIAS if por_cat.get(c)]
        if not vivas:
            return cruces
        if len(vivas) == 1:
            eq = por_cat[vivas[0]]
            while len(eq) >= 2:
                cruces.append((eq.pop(0), eq.pop(0)))
            return cruces
        for k in range(len(vivas) // 2):
            alta, baja = por_cat[vivas[k]], por_cat[vivas[-1 - k]]
            while alta and baja:
                cruces.append((alta.pop(0), baja.pop(0)))


def sortear_copa(S, rng, lista=None):
    """Sorteo de la Copa de la temporada en curso con los clasificados `lista`
    [(club, cómo clasificó)] (por defecto, los de la temporada anterior)."""
    SC = nueva_copa()
    lista = lista or S.get("copa_clasif") or clasificados_inicial(S)
    actual = categoria_actual(S)
    lista = [(n, c) for n, c in lista if n in actual][:COPA_EQUIPOS]
    SC["nombres"] = [n for n, _ in lista]
    SC["criterio"] = [c for _, c in lista]
    SC["origen"] = [actual[n][0] for n in SC["nombres"]]
    SC["r"] = np.array([actual[n][1] for n in SC["nombres"]], dtype=float)
    por_cat = {}
    for i in rng.permutation(len(lista)):
        por_cat.setdefault(SC["origen"][int(i)], []).append(int(i))
    cruces = _cruces_por_categoria(por_cat)
    orden = rng.permutation(len(cruces))                 # lugar de cada cruce en el cuadro
    SC["cuadro"] = [[{"a": cruces[k][0], "b": cruces[k][1], "p": None, "gana": None} for k in orden]]
    SC["sorteada"] = True
    return SC


def simular_ronda_copa(SC, P, rng):
    """Juega la ronda que sigue (partido único, cancha neutral, penales si empatan) y arma
    los cruces de la siguiente: ganador del partido 2k contra el del 2k+1."""
    if not SC["sorteada"] or SC["ronda"] >= SC["total"]:
        return
    k = SC["ronda"]
    nom, r = SC["nombres"], SC["r"]
    llaves = SC["cuadro"][k]
    a = np.array([m["a"] for m in llaves])
    b = np.array([m["b"] for m in llaves])
    gl, gv, gana_l, pen = jugar_ko(rng, r[a], r[b], P["sorpresa"], localia=0.0)
    for m, g1, g2, gl_, pe in zip(llaves, gl, gv, gana_l, pen):
        tanda = tanda_penales(rng, bool(gl_)) if pe else None
        m["gana"] = m["a"] if gl_ else m["b"]
        m["p"] = nuevo_partido(COPA_ARG, k + 1, COPA_RONDAS[k], COPA_RONDAS[k], nom[m["a"]], nom[m["b"]],
                               g1, g2, tanda=tanda, gana=nom[m["gana"]], neutral=True)
        SC["log"].append(m["p"])
    revisar_copa(SC, llaves, rng)                       # suspensiones y exclusiones (rarísimo)
    SC["ronda"] += 1
    if SC["ronda"] < SC["total"]:
        SC["cuadro"].append([{"a": llaves[2 * j]["gana"], "b": llaves[2 * j + 1]["gana"], "p": None,
                              "gana": None} for j in range(len(llaves) // 2)])
    else:
        SC["campeon"] = llaves[0]["gana"]


def llave_de(k_ronda, j):
    """Letra de la llave (A-H) del partido j de la ronda k (sólo hasta octavos)."""
    por_llave = 8 >> k_ronda                      # partidos de cada llave en esa ronda
    return COPA_LLAVES[j // por_llave] if por_llave else None


# ----------------------------------------------------------------------------
# SUPERCOPA ARGENTINA
# ----------------------------------------------------------------------------
def nueva_supercopa():
    """Supercopa de la temporada, todavía sin jugar (a = campeón de Primera, b = su rival)."""
    return {"jugada": False, "a": None, "b": None, "crit_a": "", "crit_b": "", "p": None,
            "campeon": None, "log": []}


def copa_terminada(S):
    SC = S["copa"]
    return bool(SC["sorteada"] and SC["ronda"] >= SC["total"] and SC["campeon"] is not None)


def supercopa_lista(S):
    """Se puede jugar cuando terminaron Primera División (con desempates) y la Copa Argentina."""
    return (not S["supercopa"]["jugada"]) and primera_terminada(S) and copa_terminada(S)


def rivales_supercopa(S):
    """(club A, media A, cómo clasificó A, club B, media B, cómo clasificó B).

    A es el campeón de Primera; B es el campeón de la Copa Argentina. Si es el mismo club,
    B pasa a ser el subcampeón de Primera.
    """
    final = tabla_final(S)
    camp = final.iloc[0]
    SC = S["copa"]
    c_copa = SC["nombres"][SC["campeon"]]
    a, ra = camp["Equipo"], float(S["r"][int(camp["id"])])
    if a == c_copa:
        sub = final.iloc[1]
        return (a, ra, "Campeón de Primera y de la Copa Argentina",
                sub["Equipo"], float(S["r"][int(sub["id"])]),
                "Subcampeón de Primera (el campeón también ganó la Copa)")
    return (a, ra, "Campeón de Primera", c_copa, float(SC["r"][SC["campeon"]]),
            "Campeón de la Copa Argentina")


def simular_supercopa(S, P, rng):
    """Juega la Supercopa (partido único, cancha neutral, penales si empatan)."""
    if not supercopa_lista(S):
        return
    SS = S["supercopa"]
    a, ra, crit_a, b, rb, crit_b = rivales_supercopa(S)
    gl, gv, gana_l, pen = jugar_ko(rng, np.array([ra]), np.array([rb]), P["sorpresa"], localia=0.0)
    g1, g2, gana_local, hubo_pen = int(gl[0]), int(gv[0]), bool(gana_l[0]), bool(pen[0])
    tanda = tanda_penales(rng, gana_local) if hubo_pen else None
    gana = a if gana_local else b
    p = nuevo_partido(SUPERCOPA, 1, "Final", "Final", a, b, g1, g2, tanda=tanda, gana=gana, neutral=True)
    SS.update(jugada=True, a=a, b=b, crit_a=crit_a, crit_b=crit_b, p=p, campeon=gana)
    SS["log"].append(p)
