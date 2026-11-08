"""Primera Amateur de Uruguay (la tercera división, 20 clubes): formato propio del simulador.

Antes la tercera división era una lista de clubes que no se jugaba. Ahora es una liga simulada más, que cuelga de la
Segunda División Profesional (`divisional` 3):

  * Fase regular: dos series de 10 clubes (se sortean cada temporada), todos contra todos a doble rueda (18 fechas).
  * Fase final: pasan los 4 primeros de cada serie. Cuartos de final (1° de una serie contra el 4° de la otra y 2° contra
    3°), semifinales y final, todo a partido único con penales si empatan. Local el mejor ubicado de la fase regular; la
    final, en cancha neutral.
  * Campeón: el que gana la final. Ascienden a la Segunda División el campeón y el subcampeón.
  * No hay descenso (no existe una división más abajo). Los que bajan de la Segunda ocupan los lugares de los dos que
    suben, así la Primera Amateur sigue con 20 clubes.

Simplificaciones (a revisar contra el reglamento de la AUF; ver docs/LIGAS_EXTERIOR.md):
  * En la realidad la Divisional C (hoy "Primera División Amateur") la organiza la AUF con otro calendario y con
    ascensos por tabla y repechajes; acá se usa un formato propio con fase final por llaves.
  * Las series se arman al azar (el sorteo real separa a los clubes del interior).
  * Las llaves previas a la final son a partido único.
"""

import numpy as np

from ligas.exterior import (FORMATOS, UNA_SEMANA, Formato, dias_semanales, espejo, partidos_de_ronda, ronda, rueda,
                            stats_vacias, tabla)
from ligas.uruguay import _completa, _indices, _jugada
from motor.fechas import desde

REGULAR = "Regular"
CUARTOS = "Cuartos de final"
SEMIS = "Semifinal"
FINAL = "Final"
ETAPAS_FINALES = (CUARTOS, SEMIS, FINAL)
TITULOS_FINALES = {CUARTOS: "Cuartos", SEMIS: "Semifinales", FINAL: "Final"}
PASAN_POR_SERIE = 4
ASCIENDEN = 2


def _posiciones(L):
    """{id: puesto (0 = mejor)} según la tabla de la fase regular de los 20 clubes (puntos, diferencia de gol, goles a favor)."""
    return {int(i): k for k, i in enumerate(tabla(L, L["E"][REGULAR])["id"])}


def _cruce(L, a, b):
    """(local, visita): local el mejor ubicado en la fase regular."""
    pos = _posiciones(L)
    return (a, b) if pos[a] <= pos[b] else (b, a)


def _ganadores(L, etapa):
    """Ids de los ganadores de la ronda `etapa`, en el orden de sus cruces."""
    i = _indices(L, etapa)[0]
    return [L["nombres"].index(p["gana"]) for p in partidos_de_ronda(L, i + 1)]


def _por_serie(L):
    """[ids ordenados de la serie A, ids ordenados de la serie B] según la tabla de la fase regular."""
    return [[int(i) for i in tabla(L, L["E"][REGULAR], g)["id"]] for g in L["grupos"]]


def clasificados(L):
    """Ids de los 8 que juegan la fase final (4 de cada serie)."""
    return [i for s in _por_serie(L) for i in s[:PASAN_POR_SERIE]]


class UruguayAmateur(Formato):
    nombre = "uruguay_amateur"
    descripcion = ("Dos series de 10 clubes a doble rueda; pasan los 4 primeros de cada una a una fase final por llaves "
                   "(cuartos, semifinales y final, a partido único). Ascienden a la Segunda División el campeón y el "
                   "subcampeón. No hay descenso: los que bajan de la Segunda ocupan los lugares de los que suben.")
    etapas_definicion = ETAPAS_FINALES
    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        cal = cfg["calendario"]
        orden = [int(i) for i in rng.permutation(n)]
        mitad = (n + 1) // 2
        A, B = sorted(orden[:mitad]), sorted(orden[mitad:])
        ra, rb = rueda(rng, A), rueda(rng, B)
        fa, fb = ra + espejo(ra), rb + espejo(rb)
        k_reg = max(len(fa), len(fb))
        dias = dias_semanales(anio, cal[REGULAR], k_reg)
        grupo_de = {**{i: "Serie A" for i in A}, **{i: "Serie B" for i in B}}
        rondas = []
        for k in range(k_reg):
            R = ronda(REGULAR, f"Fase regular · fecha {k + 1}", "Fase regular", dias[k],
                      pares=(fa[k] if k < len(fa) else []) + (fb[k] if k < len(fb) else []), suma=REGULAR)
            R["grupo_de"] = grupo_de
            rondas.append(R)
        dia = max(desde(anio, *cal["Definiciones"]), dias[-1] + UNA_SEMANA)
        rondas.append(ronda(CUARTOS, "Fase final · cuartos de final", CUARTOS, dia, ko=True))
        rondas.append(ronda(SEMIS, "Fase final · semifinales", SEMIS, dia + UNA_SEMANA, ko=True))
        rondas.append(ronda(FINAL, "Fase final · final", FINAL, dia + 2 * UNA_SEMANA, ko=True, neutral=True))
        return {
            "formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
            "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
            "E": {REGULAR: stats_vacias(n)}, "descensos": int(cfg.get("descensos", 0)),
            "ascensos": int(cfg.get("ascensos", ASCIENDEN)), "divisional": int(cfg.get("divisional", 3)),
            "grupos": [A, B], "hecho": {REGULAR: False}, "ganadores": {},
            "campeon": None, "subcampeon": None, "suben": [], "via": "",
        }
    def avanzar(self, L, rng):
        for _ in range(8):
            if not self._paso(L):
                return

    def _paso(self, L):
        if not L["hecho"][REGULAR]:
            if not _completa(L, REGULAR):
                return False
            (a1, a2, a3, a4), (b1, b2, b3, b4) = (s[:PASAN_POR_SERIE] for s in _por_serie(L))
            i = _indices(L, CUARTOS)[0]
            L["rondas"][i]["pares"] = [_cruce(L, *c) for c in ((a1, b4), (a2, b3), (b1, a4), (b2, a3))]
            L["hecho"][REGULAR] = True
            return True
        for etapa, siguiente in ((CUARTOS, SEMIS), (SEMIS, FINAL)):
            j = _indices(L, siguiente)[0]
            if L["rondas"][j]["pares"] is None and _jugada(L, etapa):
                g = _ganadores(L, etapa)
                L["rondas"][j]["pares"] = [_cruce(L, g[k], g[k + 1]) for k in range(0, len(g), 2)]
                return True
        if L["campeon"] is None and _jugada(L, FINAL):
            p = partidos_de_ronda(L, _indices(L, FINAL)[0] + 1)[0]
            L["campeon"] = p["gana"]
            L["subcampeon"] = p["local"] if p["gana"] == p["visita"] else p["visita"]
            L["suben"] = [L["campeon"], L["subcampeon"]][:int(L.get("ascensos", ASCIENDEN))]
            L["via"] = (f"Campeón: {L['campeon']}, ganador de la final. Ascienden a la Segunda División "
                        f"{' y '.join(L['suben'])}.")
            return True
        return False
    def llaves(self, L):
        """Datos del cuadro de la fase final: [(título, [partido o None])] de cuartos a final. Un partido es un dict con
        local, visita, gl, gv, gana, pen, neutral y dia (con gl, gv y gana vacíos si todavía no se jugó)."""
        out = []
        for etapa, n in ((CUARTOS, 4), (SEMIS, 2), (FINAL, 1)):
            i = _indices(L, etapa)[0]
            R = L["rondas"][i]
            if R["pares"] is None:
                ms = [None] * n
            elif i < L["fecha"]:
                ms = [{**p, "dia": R["dia"]} for p in partidos_de_ronda(L, i + 1)]
            else:
                ms = [{"local": L["nombres"][a], "visita": L["nombres"][b], "gl": "", "gv": "", "gana": None,
                       "pen": None, "neutral": R["neutral"], "dia": R["dia"]} for a, b in R["pares"]]
            out.append((TITULOS_FINALES[etapa], ms))
        return out
    def tablas(self, L):
        out = []
        pasan = set(clasificados(L)) if L["hecho"][REGULAR] else None
        for nombre, ids in zip(("A", "B"), L["grupos"]):
            df = tabla(L, L["E"][REGULAR], ids)
            destinos = []
            for p, i, eq in zip(df["Pos"], df["id"], df["Equipo"]):
                if L["campeon"] == eq:
                    destinos.append("Campeón · Asciende")
                elif L["subcampeon"] == eq:
                    destinos.append("Subcampeón · Asciende")
                elif (int(i) in pasan) if pasan is not None else p <= PASAN_POR_SERIE:
                    destinos.append("Fase final")
                else:
                    destinos.append("")
            df["Destino"] = destinos
            out.append({"titulo": f"Serie {nombre}", "df": df, "tipo": "liga",
                        "nota": (f"Pasan a la fase final los {PASAN_POR_SERIE} primeros de cada serie. "
                                 + ("" if L["hecho"][REGULAR] else "Destinos provisorios por la posición de hoy. ")
                                 + f"Ascienden a la Segunda División el campeón y el subcampeón.")})
        return out
    def cierre(self, L):
        """Campeón, orden final (campeón, subcampeón, semifinalistas, cuartofinalistas y el resto por la tabla de la fase
        regular), puntos y los que suben. Si se cierra antes de tiempo, suben los dos primeros de ese orden."""
        reg = tabla(L, L["E"][REGULAR])
        etapa_de = {}
        for etapa, valor in ((CUARTOS, 3), (SEMIS, 2), (FINAL, 1)):
            idx = _indices(L, etapa)
            if idx and idx[0] < L["fecha"]:
                for p in partidos_de_ronda(L, idx[0] + 1):
                    for n in (p["local"], p["visita"]):
                        etapa_de[n] = valor
        if L["campeon"]:
            etapa_de[L["campeon"]] = 0
        base = list(reg["Equipo"])
        orden = sorted(base, key=lambda n: (etapa_de.get(n, 4), base.index(n)))
        suben = list(L["suben"]) or orden[:int(L.get("ascensos", ASCIENDEN))]
        return {"campeon": L["campeon"] or orden[0], "orden": orden,
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in reg.iterrows()},
                "descienden": [], "suben": suben}


FORMATOS[UruguayAmateur.nombre] = UruguayAmateur()
