"""Brasileirão Série C (la tercera división de Brasil, 20 clubes). Formato real de 2026 (CBF), con un cambio.

  * Primera fase: los 20 clubes, todos contra todos a una sola rueda (19 fechas).
  * Cuadrangulares: pasan los 8 primeros y se arman dos grupos de 4 (1°, 4°, 5° y 8° contra 2°, 3°, 6° y 7° en el otro),
    a doble rueda (6 fechas).
  * Ascienden a la Série B los 2 primeros de cada cuadrangular (4 clubes).
  * Final: los ganadores de cada cuadrangular juegan la final a ida y vuelta. La vuelta es en la cancha del que quedó
    mejor ubicado en la primera fase; si el global empata, penales.
  * Descienden a la Série D los 4 últimos de la primera fase.

Simplificaciones (a revisar; ver docs/LIGAS_EXTERIOR.md):
  * En 2026 el reglamento real baja sólo 2 clubes (la C crece a 24 en 2027 y a 28 en 2028). Como el simulador tiene la
    pirámide cerrada (cada división conserva sus 20 clubes), acá bajan 4, que es lo que suben de la Série D.
  * Los desempates de la tabla son puntos, diferencia de gol y goles a favor (el real agrega victorias y otros criterios).
"""

import numpy as np

from ligas.exterior import (FORMATOS, Formato, dias_semanales, espejo, partidos_de_ronda, ronda, rueda, stats_vacias,
                            tabla)
from ligas.uruguay import _completa, _indices, _jugada, _penales_del_global

PRIMERA = "Primera fase"
CUADRANGULARES = "Cuadrangulares"
FINAL_IDA = "Final · ida"
FINAL_VUELTA = "Final · vuelta"
CLASIFICAN = 8
POR_GRUPO = 2
GRUPOS = ("Cuadrangular A", "Cuadrangular B")
SEMILLAS_A = (0, 3, 4, 7)            # puestos de la primera fase que juegan el cuadrangular A (1°, 4°, 5° y 8°)
SEMILLAS_B = (1, 2, 5, 6)            # ... y el B (2°, 3°, 6° y 7°)


def _tabla_grupo(L, k):
    """Tabla del cuadrangular `k` (0 = A, 1 = B)."""
    return tabla(L, L["E"][CUADRANGULARES], L["grupos"][k])


class BrasilC(Formato):
    nombre = "brasil_c"
    descripcion = ("Primera fase a una rueda entre los 20 clubes; los 8 primeros juegan dos cuadrangulares a doble rueda. "
                   "Ascienden a la Série B los 2 primeros de cada cuadrangular y los ganadores juegan la final a ida y "
                   "vuelta por el título. Descienden a la Série D los 4 últimos de la primera fase.")
    etapas_definicion = (FINAL_IDA, FINAL_VUELTA)
    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        ida = rueda(rng, range(n))
        k_cuad = 2 * (len(SEMILLAS_A) - 1)
        dias = dias_semanales(anio, cfg["calendario"][PRIMERA], len(ida) + k_cuad + 2)
        rondas = [ronda(PRIMERA, f"Primera fase · fecha {k + 1}", PRIMERA, dias[k], pares=f, suma=PRIMERA)
                  for k, f in enumerate(ida)]
        for k in range(k_cuad):
            rondas.append(ronda(CUADRANGULARES, f"Cuadrangulares · fecha {k + 1}", CUADRANGULARES, dias[len(ida) + k],
                                suma=CUADRANGULARES))
        rondas.append(ronda(FINAL_IDA, "Final · ida", "Final", dias[-2], ida_vuelta="ida"))
        rondas.append(ronda(FINAL_VUELTA, "Final · vuelta", "Final", dias[-1], ida_vuelta="vuelta"))
        return {
            "formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
            "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
            "E": {PRIMERA: stats_vacias(n), CUADRANGULARES: stats_vacias(n)},
            "descensos": int(cfg.get("descensos", 0)), "ascensos": int(cfg.get("ascensos", 2 * POR_GRUPO)),
            "divisional": int(cfg.get("divisional", 3)),
            "grupos": None, "clasificados": [], "hecho": {PRIMERA: False, CUADRANGULARES: False},
            "ganadores": {}, "finalistas": None, "campeon": None, "subcampeon": None, "suben": [], "via": "",
        }
    def avanzar(self, L, rng):
        for _ in range(4):
            if not self._paso(L, rng):
                return

    def _paso(self, L, rng):
        nom = L["nombres"]
        if not L["hecho"][PRIMERA]:
            if not _completa(L, PRIMERA):
                return False
            top = [int(i) for i in tabla(L, L["E"][PRIMERA])["id"]][:CLASIFICAN]
            A, B = [top[i] for i in SEMILLAS_A], [top[i] for i in SEMILLAS_B]
            fa, fb = rueda(rng, A), rueda(rng, B)
            fa, fb = fa + espejo(fa), fb + espejo(fb)
            grupo_de = {**{i: GRUPOS[0] for i in A}, **{i: GRUPOS[1] for i in B}}
            for k, i in enumerate(_indices(L, CUADRANGULARES)):
                R = L["rondas"][i]
                R["pares"], R["grupo_de"] = fa[k] + fb[k], grupo_de
            L["grupos"], L["clasificados"], L["hecho"][PRIMERA] = [A, B], top, True
            return True
        if not L["hecho"][CUADRANGULARES]:
            if not _completa(L, CUADRANGULARES):
                return False
            tg = [_tabla_grupo(L, k) for k in (0, 1)]
            ganadores = [int(t.iloc[0]["id"]) for t in tg]
            L["ganadores"] = dict(zip(GRUPOS, ganadores))
            L["suben"] = [nom[int(i)] for t in tg for i in t["id"][:POR_GRUPO]][:int(L["ascensos"])]
            a, b = sorted(ganadores, key=L["clasificados"].index)       # a: mejor ubicado en la primera fase
            L["finalistas"] = [a, b]
            L["rondas"][_indices(L, FINAL_IDA)[0]]["pares"] = [(b, a)]  # la vuelta, en la cancha del mejor ubicado
            L["rondas"][_indices(L, FINAL_VUELTA)[0]]["pares"] = [(a, b)]
            L["hecho"][CUADRANGULARES] = True
            return True
        if L["campeon"] is None and _jugada(L, FINAL_VUELTA):
            a, b = L["finalistas"]
            p1 = partidos_de_ronda(L, _indices(L, FINAL_IDA)[0] + 1)[0]
            p2 = partidos_de_ronda(L, _indices(L, FINAL_VUELTA)[0] + 1)[0]
            g_a, g_b = p1["gv"] + p2["gl"], p1["gl"] + p2["gv"]
            ganador = _penales_del_global(L, p2, a, b, rng) if g_a == g_b else (a if g_a > g_b else b)
            perdedor = b if ganador == a else a
            L["campeon"], L["subcampeon"] = nom[ganador], nom[perdedor]
            L["global_final"] = {"a": nom[a], "b": nom[b], "ga": int(g_a), "gb": int(g_b)}
            L["via"] = (f"Campeón: {L['campeon']}, ganador de la final a ida y vuelta (global {max(g_a, g_b)}-{min(g_a, g_b)}"
                        f"{'' if g_a != g_b else ', por penales'}). Ascienden a la Série B: {', '.join(L['suben'])}.")
            return True
        return False
    def tablas(self, L):
        out = []
        df = tabla(L, L["E"][PRIMERA])
        n, d = len(df), int(L.get("descensos", 0))
        pasan = set(L["clasificados"]) if L["hecho"][PRIMERA] else None
        destinos = []
        for p, i in zip(df["Pos"], df["id"]):
            if d and p > n - d:
                destinos.append("Desciende")
            elif (int(i) in pasan) if pasan is not None else p <= CLASIFICAN:
                destinos.append("Cuadrangulares")
            else:
                destinos.append("")
        df["Destino"] = destinos
        out.append({"titulo": "Primera fase", "df": df, "tipo": "liga",
                    "nota": (f"Pasan a los cuadrangulares los {CLASIFICAN} primeros; descienden a la Série D los {d} últimos. "
                             + ("" if L["hecho"][PRIMERA] else "Destinos provisorios por la posición de hoy."))})
        if L["grupos"] is None:
            out.append({"titulo": "Cuadrangulares", "df": None, "tipo": "grupos",
                        "nota": f"Los cuadrangulares se arman al terminar la primera fase: pasan los {CLASIFICAN} primeros."})
            return out
        for k, titulo in enumerate(GRUPOS):
            dg = _tabla_grupo(L, k)
            destinos = []
            for p, eq in zip(dg["Pos"], dg["Equipo"]):
                if L["campeon"] == eq:
                    destinos.append("Campeón · Asciende")
                elif L["subcampeon"] == eq:
                    destinos.append("Subcampeón · Asciende")
                elif p <= POR_GRUPO:
                    destinos.append("Asciende" + (" · A la final" if p == 1 and not L["campeon"] else ""))
                else:
                    destinos.append("")
            dg["Destino"] = destinos
            out.append({"titulo": titulo, "df": dg, "tipo": "liga",
                        "nota": f"Ascienden a la Série B los {POR_GRUPO} primeros; los ganadores de cada cuadrangular "
                                f"juegan la final a ida y vuelta."})
        return out
    def cierre(self, L):
        """Campeón, orden final (campeón, subcampeón, otros ascendidos, el resto de los cuadrangulares y después la
        primera fase), puntos de la primera fase, los que bajan (últimos de la primera fase) y los que suben. Si se cierra
        antes de tiempo, suben los primeros de la primera fase."""
        reg = tabla(L, L["E"][PRIMERA])
        base = list(reg["Equipo"])
        suben = list(L["suben"]) or base[:int(L.get("ascensos", 2 * POR_GRUPO))]
        lugar = {}
        for i in (L["clasificados"] or []):
            lugar[L["nombres"][i]] = 3
        for n in suben:
            lugar[n] = 2
        if L["subcampeon"]:
            lugar[L["subcampeon"]] = 1
        if L["campeon"]:
            lugar[L["campeon"]] = 0
        orden = sorted(base, key=lambda n: (lugar.get(n, 4), base.index(n)))
        d = int(L.get("descensos", 0))
        return {"campeon": L["campeon"] or orden[0], "orden": orden,
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in reg.iterrows()},
                "descienden": base[len(base) - d:] if d else [], "suben": suben}


FORMATOS[BrasilC.nombre] = BrasilC()
