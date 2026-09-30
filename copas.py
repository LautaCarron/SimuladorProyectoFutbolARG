"""Copas: Copa Argentina.

Copa Argentina: 128 equipos, eliminación directa a partido único desde 64avos de final.
Todos los partidos en cancha neutral; si empatan, penales.

Clasifican (con las posiciones finales de la temporada, por eso se sortea cuando terminan
todas las ligas):
  * Primera División: los 30.
  * Primera Nacional: los 36.
  * Federal A: los 20 de la Zona Campeonato y los 8 mejores de la Zona Descenso.
  * Primera B: los 12 primeros.
  * Primera C: los 10 primeros.
  * Regional Amateur: los campeones de las 12 regiones.
Si alguna liga no llega a su cupo (p. ej. una región sin campeón), el lugar lo ocupa el
siguiente mejor de la Zona Descenso del Federal A.

Sorteo: bombo 1 con los 64 de mayor categoría (Primera y los mejores de la Primera Nacional
por media) y bombo 2 con el resto; cada partido de 64avos cruza uno de cada bombo. El cuadro
se divide en 8 llaves (A-H) de 16 equipos: el ganador de cada llave juega los cuartos.
"""

import numpy as np

from motor import jugar_ko, nuevo_partido, tanda_penales
from regional import REGIONES_REG
from torneos import primera_terminada, tabla_f_f2, tabla_pb, tabla_pc, total_b

COPA_ARG = "Copa Argentina"
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
    sumar(SF, camp, "Federal A", lambda k: "Zona Campeonato")
    sumar(SF, desc[:8], "Federal A", lambda k: f"{k + 1}° Zona Descenso")
    sumar(SPB, tabla_pb(SPB)["id"].to_numpy()[:12], "Primera B", lambda k: f"{k + 1}° de la tabla")
    sumar(SPC, tabla_pc(SPC)["id"].to_numpy()[:10], "Primera C", lambda k: f"{k + 1}° de la tabla")
    campeones = [(reg, SR["campeones"].get(reg)) for reg in REGIONES_REG]
    for reg, c in campeones:
        if c is not None:
            lista.append((SR["nombres"][c], float(SR["r"][c]), "Regional Amateur", f"Campeón {reg}"))
    extra = 8
    while len(lista) < COPA_EQUIPOS and extra < len(desc):      # cupos vacantes
        sumar(SF, desc[extra:extra + 1], "Federal A", lambda k, e=extra: f"{e + 1}° Zona Descenso")
        extra += 1
    return lista[:COPA_EQUIPOS]


def sortear_copa(S, rng):
    """Arma el cuadro de 64avos: bombo 1 (los 64 de mayor categoría) contra bombo 2."""
    SC = nueva_copa()
    lista = clasificados_copa(S)
    orden = sorted(range(len(lista)), key=lambda k: (_CATEGORIAS.index(lista[k][2]), -lista[k][1]))
    mitad = len(lista) // 2
    bombo1 = list(rng.permutation(orden[:mitad]))
    bombo2 = list(rng.permutation(orden[mitad:]))
    SC["nombres"] = [x[0] for x in lista]
    SC["r"] = np.array([x[1] for x in lista], dtype=float)
    SC["origen"] = [x[2] for x in lista]
    SC["criterio"] = [x[3] for x in lista]
    SC["cuadro"] = [[{"a": int(a), "b": int(b), "p": None, "gana": None}
                     for a, b in zip(bombo1, bombo2)]]
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
