"""Brasileirão Série D (la cuarta división de Brasil, 96 clubes desde 2026). Formato real de 2026 (CBF), simplificado.

  * Fase de grupos: 16 grupos de 6 clubes, todos contra todos a doble rueda (10 fechas). Los grupos son regionales: la
    primera temporada son los reales de 2026 (A1 a A16) y cada club que sube a la Série C deja su lugar al que baja de ella.
  * Pasan los 4 primeros de cada grupo (64 clubes). Se ordenan por su campaña (puesto en el grupo, puntos, diferencia de
    gol y goles a favor) y arman un cuadro único: segunda fase (32 cruces), tercera fase (16), octavos, cuartos,
    semifinales y final. Todos los cruces son a ida y vuelta; la vuelta es en la cancha del mejor sembrado y, si el global
    empata, hay penales.
  * Ascienden a la Série C los 4 semifinalistas. El campeón es el ganador de la final. No hay descenso.

Simplificaciones (a revisar; ver docs/LIGAS_EXTERIOR.md):
  * En 2026 el reglamento real da 6 ascensos (los 4 semifinalistas más 2 por un playoff entre los eliminados en cuartos)
    porque la Série C crece de 20 a 28 clubes hasta 2028. Como el simulador tiene la pirámide cerrada, acá suben 4, que
    es lo que baja de la Série C.
  * El cuadro real se sortea y las fases no se re-siembran; acá es un cuadro fijo por siembra (1° contra 64°, etc.).
  * Los 4 clubes que bajan de la Série C ocupan, sin criterio geográfico, los lugares de los 4 que suben.
"""

import numpy as np

from ligas.exterior import (FORMATOS, Formato, dias_semanales, espejo, partidos_de_ronda, ronda, rueda, stats_vacias,
                            tabla)
from ligas.uruguay import _completa, _indices, _jugada, _penales_del_global

GRUPOS = "Fase de grupos"
POR_GRUPO = 6
PASAN = 4
NOMBRE_FASE = {32: "Segunda fase", 16: "Tercera fase", 8: "Octavos de final", 4: "Cuartos de final", 2: "Semifinales",
               1: "Final"}
EN_LLAVES = ("Octavos de final", "Cuartos de final", "Semifinales", "Final")
CRUCES_DE = {v: k for k, v in NOMBRE_FASE.items()}


def _ida(fase):
    return f"{fase} · ida"


def _vuelta(fase):
    return f"{fase} · vuelta"


def _orden_cuadro(m):
    """Siembras 1..m en el orden en que se leen de arriba abajo en el cuadro (1 contra m, 4 contra m-3...), así los mejores
    sembrados se cruzan lo más tarde posible."""
    o = [1]
    while len(o) < m:
        t = 2 * len(o)
        o = [x for s in o for x in (s, t + 1 - s)]
    return o


class BrasilD(Formato):
    nombre = "brasil_d"
    lugares_fijos = True                         # el que sube a la Série C deja su lugar (su grupo) al que baja
    descripcion = ("16 grupos regionales de 6 clubes a doble rueda; pasan los 4 primeros de cada uno (64 clubes) a un cuadro "
                   "de eliminación directa a ida y vuelta (segunda fase, tercera fase, octavos, cuartos, semifinales y "
                   "final). Ascienden a la Série C los 4 semifinalistas. No hay descenso.")
    etapas_definicion = (_ida("Semifinales"), _vuelta("Semifinales"), _ida("Final"), _vuelta("Final"))
    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        grupos = [list(range(i, min(i + POR_GRUPO, n))) for i in range(0, n, POR_GRUPO)]
        pasan = PASAN * len(grupos)
        if pasan & (pasan - 1) or pasan < 2:
            raise ValueError(f"{cfg['nombre']}: {len(grupos)} grupos dejan {pasan} clubes y el cuadro necesita una potencia de 2")
        ruedas = [rueda(rng, g) for g in grupos]
        fechas = [[par for ru in ruedas for par in ru[k]] for k in range(len(ruedas[0]))]
        fechas += [[par for ru in ruedas for par in espejo(ru)[k]] for k in range(len(ruedas[0]))]
        fases, c = [], pasan // 2
        while c >= 1:
            fases.append(NOMBRE_FASE[c])
            c //= 2
        dias = dias_semanales(anio, cfg["calendario"][GRUPOS], len(fechas) + 2 * len(fases))
        grupo_de = {i: f"Grupo A{k + 1}" for k, g in enumerate(grupos) for i in g}
        rondas = []
        for k, f in enumerate(fechas):
            R = ronda(GRUPOS, f"Fase de grupos · fecha {k + 1}", GRUPOS, dias[k], pares=f, suma=GRUPOS)
            R["grupo_de"] = grupo_de
            rondas.append(R)
        for j, fase in enumerate(fases):
            d0 = len(fechas) + 2 * j
            rondas.append(ronda(_ida(fase), f"{fase} · ida", fase, dias[d0], ida_vuelta="ida"))
            rondas.append(ronda(_vuelta(fase), f"{fase} · vuelta", fase, dias[d0 + 1], ida_vuelta="vuelta"))
        return {
            "formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
            "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
            "E": {GRUPOS: stats_vacias(n)}, "descensos": int(cfg.get("descensos", 0)),
            "ascensos": int(cfg.get("ascensos", 4)), "divisional": int(cfg.get("divisional", 4)),
            "grupos": grupos, "fases": fases, "hecho": {GRUPOS: False}, "clasificados": [], "semillas": {},
            "cruces": {}, "series": {}, "campeon": None, "subcampeon": None, "suben": [], "via": "", "ganadores": {},
        }
    def avanzar(self, L, rng):
        for _ in range(len(L["fases"]) + 3):
            if not self._paso(L, rng):
                return

    def _armar(self, L, fase, cruces):
        """Deja listos los dos partidos de la fase: `cruces` = [[mejor sembrado, peor sembrado]]; la vuelta es del mejor."""
        L["cruces"][fase] = [[int(a), int(b)] for a, b in cruces]
        L["rondas"][_indices(L, _ida(fase))[0]]["pares"] = [(b, a) for a, b in L["cruces"][fase]]
        L["rondas"][_indices(L, _vuelta(fase))[0]]["pares"] = [(a, b) for a, b in L["cruces"][fase]]

    def _paso(self, L, rng):
        nom, sem = L["nombres"], L["semillas"]
        if not L["hecho"][GRUPOS]:
            if not _completa(L, GRUPOS):
                return False
            clas = []
            for ids in L["grupos"]:
                t = tabla(L, L["E"][GRUPOS], ids)
                for p, i, pts, dg, gf in zip(t["Pos"], t["id"], t["Pts"], t["DG"], t["GF"]):
                    if p <= PASAN:
                        clas.append((p, -int(pts), -int(dg), -int(gf), int(i)))
            clas.sort()
            L["clasificados"] = [c[-1] for c in clas]
            L["semillas"] = {str(i): k for k, i in enumerate(L["clasificados"])}
            orden = _orden_cuadro(len(clas))
            s = L["clasificados"]
            self._armar(L, L["fases"][0], [(s[orden[2 * k] - 1], s[orden[2 * k + 1] - 1]) for k in range(len(orden) // 2)])
            L["hecho"][GRUPOS] = True
            return True
        for j, fase in enumerate(L["fases"]):
            if fase in L["series"]:
                continue
            if fase not in L["cruces"] or not _jugada(L, _vuelta(fase)):
                return False
            ida = partidos_de_ronda(L, _indices(L, _ida(fase))[0] + 1)
            vta = partidos_de_ronda(L, _indices(L, _vuelta(fase))[0] + 1)
            res = []
            for (a, b), p1, p2 in zip(L["cruces"][fase], ida, vta):       # a: mejor sembrado (juega la vuelta de local)
                g_a, g_b = p1["gv"] + p2["gl"], p1["gl"] + p2["gv"]
                ganador = _penales_del_global(L, p2, a, b, rng) if g_a == g_b else (a if g_a > g_b else b)
                res.append({"a": a, "b": b, "ga": int(g_a), "gb": int(g_b), "ganador": int(ganador),
                            "pen": list(p2["pen"]) if p2.get("pen") else None})
            L["series"][fase] = res
            ganadores = [x["ganador"] for x in res]
            if j + 1 < len(L["fases"]):          # el cuadro es fijo: el ganador de un cruce juega con el del de al lado
                par = [sorted((ganadores[2 * k], ganadores[2 * k + 1]), key=lambda i: sem[str(i)])
                       for k in range(len(ganadores) // 2)]
                self._armar(L, L["fases"][j + 1], par)
            else:
                x = res[0]
                perdedor = x["b"] if x["ganador"] == x["a"] else x["a"]
                L["campeon"], L["subcampeon"] = nom[x["ganador"]], nom[perdedor]
                L["suben"] = self._orden_final(L)[:int(L["ascensos"])]
                L["via"] = (f"Campeón: {L['campeon']}, ganador de la final a ida y vuelta (global "
                            f"{max(x['ga'], x['gb'])}-{min(x['ga'], x['gb'])}"
                            f"{'' if x['ga'] != x['gb'] else ', por penales'}). Ascienden a la Série C: "
                            f"{', '.join(L['suben'])}.")
            return True
        return False
    def _orden_final(self, L):
        """Los 96 clubes del mejor al peor: campeón, subcampeón, semifinalistas, cuartofinalistas... y, entre los que no
        pasaron de grupo, por su puesto en el grupo (puntos, diferencia de gol, goles a favor)."""
        nom = L["nombres"]
        profundidad = {}                         # cuanto más chico, más lejos llegó
        for j, fase in enumerate(L["fases"]):
            for x in L["series"].get(fase, []):
                perdedor = x["b"] if x["ganador"] == x["a"] else x["a"]
                profundidad[perdedor] = len(L["fases"]) - j
                if j == len(L["fases"]) - 1:
                    profundidad[x["ganador"]] = 0
        campania = {}
        for ids in L["grupos"]:
            t = tabla(L, L["E"][GRUPOS], ids)
            for p, i, pts, dg, gf in zip(t["Pos"], t["id"], t["Pts"], t["DG"], t["GF"]):
                campania[int(i)] = (int(p), -int(pts), -int(dg), -int(gf))
        pasaron = set(L["clasificados"])
        return [nom[i] for i in sorted(range(len(nom)), key=lambda i: (
            profundidad.get(i, len(L["fases"]) + 1 + (i not in pasaron)), campania.get(i, (9, 0, 0, 0)), i))]
    def llaves(self, L):
        """Cuadro de octavos a la final: [(título, [cruce o None])]. Un cruce es un dict con local, visita, gl, gv (goles del
        global), gana, pen, neutral y dia (con gl, gv y gana vacíos si todavía no se jugó). Local: el mejor sembrado."""
        nom, out = L["nombres"], []
        for fase in EN_LLAVES:
            if fase not in L["fases"]:
                continue
            n = CRUCES_DE[fase]
            cruces = L["cruces"].get(fase)
            dia = L["rondas"][_indices(L, _vuelta(fase))[0]]["dia"]
            if cruces is None:
                out.append((fase, [None] * n))
                continue
            res = L["series"].get(fase)
            ms = []
            for k, (a, b) in enumerate(cruces):
                x = res[k] if res else None
                ms.append({"local": nom[a], "visita": nom[b], "gl": x["ga"] if x else "", "gv": x["gb"] if x else "",
                           "gana": nom[x["ganador"]] if x else None, "pen": tuple(x["pen"]) if x and x["pen"] else None,
                           "neutral": False, "dia": dia})
            out.append((fase, ms))
        return out

    def llaves_info(self, L):
        """(aviso mientras no está armado, subtítulo del campeón, nota al pie) del cuadro, para la interfaz."""
        aviso = (None if L["hecho"][GRUPOS] else
                 "El cuadro se arma cuando termina la fase de grupos: pasan los 4 primeros de cada grupo (64 clubes).")
        return (aviso, "Asciende a la Série C",
                "Cuadro por siembra a ida y vuelta (el número es el global; entre paréntesis, los penales). Local: el mejor "
                "sembrado. Se muestran desde octavos; la segunda y la tercera fase están en Fixture y resultados. "
                "Ascienden los 4 semifinalistas.")
    def tablas(self, L):
        out = []
        pasan = set(L["clasificados"]) if L["hecho"][GRUPOS] else None
        suben = set(L["suben"])
        for k, ids in enumerate(L["grupos"]):
            df = tabla(L, L["E"][GRUPOS], ids)
            destinos = []
            for p, i, eq in zip(df["Pos"], df["id"], df["Equipo"]):
                if L["campeon"] == eq:
                    destinos.append("Campeón · Asciende")
                elif L["subcampeon"] == eq:
                    destinos.append("Subcampeón · Asciende")
                elif eq in suben:
                    destinos.append("Asciende")
                elif (int(i) in pasan) if pasan is not None else p <= PASAN:
                    destinos.append("Segunda fase")
                else:
                    destinos.append("")
            df["Destino"] = destinos
            out.append({"titulo": f"Grupo A{k + 1}", "df": df, "tipo": "liga", "agrupa": "Fase de grupos",
                        "nota": (f"Pasan a la segunda fase los {PASAN} primeros de cada grupo (64 clubes). "
                                 + ("" if L["hecho"][GRUPOS] else "Destinos provisorios por la posición de hoy. ")
                                 + "Ascienden a la Série C los 4 semifinalistas.") if k == 0 else ""})
        return out
    def cierre(self, L):
        """Campeón, orden final de los 96 clubes, puntos de la fase de grupos y los que suben (los semifinalistas). Si se
        cierra antes de tiempo, suben los primeros de ese orden."""
        orden = self._orden_final(L)
        t = {}
        for ids in L["grupos"]:
            df = tabla(L, L["E"][GRUPOS], ids)
            t.update({x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in df.iterrows()})
        return {"campeon": L["campeon"] or orden[0], "orden": orden, "puntos": t, "descienden": [],
                "suben": list(L["suben"]) or orden[:int(L.get("ascensos", 4))]}


FORMATOS[BrasilD.nombre] = BrasilD()
