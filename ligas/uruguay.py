"""Liga AUF Uruguaya (primera división, 16 equipos): formato vigente en 2026.

Tres torneos cortos y una tabla acumulada:
  * Apertura: todos contra todos, una rueda (15 fechas).
  * Intermedio: dos grupos de 8 armados con la tabla final del Apertura (grupo A: 1°, 4°, 5°, 8°, 9°, 12°, 13° y 16°;
    grupo B: los demás), una rueda cada grupo (7 fechas) y una final entre los ganadores de grupo. Da la Supercopa
    (contra el campeón uruguayo); no da cupo propio a las copas ni cuenta para el campeonato ni para las tablas.
  * Clausura: igual que el Apertura con las localías invertidas (15 fechas).
  * Tabla Anual: puntos del Apertura + Intermedio + Clausura (las finales y los desempates no suman).
  * Descenso: tabla de promedios (puntos de la temporada anterior + los de esta, sobre los partidos jugados); bajan
    los dos de peor promedio. En la primera temporada del simulador sólo cuenta la actual.

Campeón uruguayo:
  * Si un mismo club gana el Apertura, el Clausura y la Tabla Anual, es campeón sin finales.
  * Si no, los campeones del Apertura y del Clausura juegan una semifinal a partido único (si es el mismo club, no hay
    semifinal) y el ganador enfrenta, en una final a ida y vuelta, al ganador de la Tabla Anual. Si el ganador de la
    semifinal ya era el de la Anual, es campeón.

Copas CONMEBOL (se arman con `asignar_cupos`; cantidades en copas/conmebol.py): campeón = Uruguay 1 y subcampeón =
Uruguay 2 (Libertadores, grupos); después, por Tabla Anual: Uruguay 3 (Fase 2), Uruguay 4 (Fase 1) y la Sudamericana.
En el reglamento real el Uruguay 4 es para el campeón de la Copa AUF Uruguay (si ya clasificó, el cupo vuelve a la
Anual): esa copa no se simula, así que acá sale de la Anual. La Sudamericana son 4 cupos (Fase 1
entre clubes uruguayos, ida y vuelta).

Simplificaciones (a revisar contra el reglamento de la AUF; ver docs/LIGAS_EXTERIOR.md):
  * Si dos o más clubes empatan en puntos en el primer puesto del Apertura, el Clausura o la Anual, los dos mejor
    ubicados (diferencia de gol, goles a favor) juegan un partido de desempate en cancha neutral, con penales.
  * Semifinal y desempates: partido único en cancha neutral. En la final, la ida es del ganador de la semifinal y la
    vuelta del ganador de la Anual; si el global empata, penales.
  * El desempate de las tablas de grupo, del Intermedio y de la Anual es diferencia de gol y goles a favor.
"""

import datetime as dt

import numpy as np

from ligas.exterior import (FORMATOS, UNA_SEMANA, Formato, asignar_cupos, dias_semanales, espejo, lideres_empatados,
                            partidos_de_ronda, ronda, rueda, stats_vacias, sumar_stats, tabla)
from motor.fechas import desde
from motor.nucleo import tanda_penales

DESEMPATE = "Desempate "
SEMIFINAL = "Semifinal"
FINAL_IDA, FINAL_VUELTA = "Final · ida", "Final · vuelta"
FINAL_INTERMEDIO = "Final del Intermedio"
TORNEOS = ("Apertura", "Intermedio", "Clausura")


def _rondas_de_grupo(m):
    """Fechas que juega un grupo de m equipos en una sola rueda."""
    return m - 1 if m % 2 == 0 else m


def _grupo_a(n):
    return [i for i in range(n) if i % 4 in (0, 3)]


def _indices(L, etapa):
    return [i for i, R in enumerate(L["rondas"]) if R["etapa"] == etapa]


def _completa(L, etapa):
    """True si la etapa tiene rondas y todas se jugaron."""
    idx = _indices(L, etapa)
    return bool(idx) and max(idx) < L["fecha"]


def _jugada(L, etapa):
    idx = _indices(L, etapa)
    return bool(idx) and idx[0] < L["fecha"]


def _ganador_de(L, etapa):
    """Id del ganador del partido único de la etapa (semifinal, desempate, final del Intermedio)."""
    i = _indices(L, etapa)[0]
    p = partidos_de_ronda(L, i + 1)[0]
    return L["nombres"].index(p["gana"])


def _ultimo_dia(L):
    return L["rondas"][-1]["dia"]


def _agregar(L, R, despues_de=None):
    """Suma una ronda al final del calendario o, con `despues_de`, justo detrás de la última ronda de esa etapa."""
    if despues_de is None:
        L["rondas"].append(R)
    else:
        L["rondas"].insert(_indices(L, despues_de)[-1] + 1, R)


def _desempate_primero(L, torneo, df):
    """Quién ganó `torneo` según la tabla `df`. True si quedó definido. Con empate en puntos arriba arma (una sola vez)
    el partido de desempate y devuelve False hasta que se juegue."""
    etapa = DESEMPATE + torneo
    if len(lideres_empatados(df)) > 1:
        idx = _indices(L, etapa)
        if not idx:
            a, b = int(df.iloc[0]["id"]), int(df.iloc[1]["id"])
            base = L["rondas"][_indices(L, torneo)[-1]] if torneo != "Anual" else L["rondas"][-1]
            R = ronda(etapa, f"Desempate por el {torneo}", f"Desempate · {torneo}", base["dia"] + dt.timedelta(days=4),
                      pares=[(a, b)], ko=True, neutral=True)
            _agregar(L, R, despues_de=torneo if torneo == "Apertura" else None)
            L["desempates"][torneo] = {"a": a, "b": b}
            return False
        if idx[0] >= L["fecha"]:
            return False
        L["ganadores"][torneo] = _ganador_de(L, etapa)
        return True
    L["ganadores"][torneo] = int(df.iloc[0]["id"])
    return True


def _armar_intermedio(L, rng):
    """Con la tabla final del Apertura se arman los dos grupos y sus cruces (las rondas ya estaban reservadas)."""
    orden = L["orden_apertura"]
    A = [orden[i] for i in _grupo_a(len(orden))]
    B = [orden[i] for i in range(len(orden)) if i not in set(_grupo_a(len(orden)))]
    L["grupos"] = [A, B]
    fa, fb = rueda(rng, A), rueda(rng, B)
    grupo_de = {**{i: "Intermedio · Grupo A" for i in A}, **{i: "Intermedio · Grupo B" for i in B}}
    for k, i in enumerate(_indices(L, "Intermedio")):
        L["rondas"][i]["pares"] = (fa[k] if k < len(fa) else []) + (fb[k] if k < len(fb) else [])
        L["rondas"][i]["grupo_de"] = grupo_de


def _tabla_anual(L):
    return tabla(L, sumar_stats(*(L["E"][t] for t in TORNEOS)))


def _penales_del_global(L, p_vuelta, a, b, rng):
    """Global empatado en la final: gana `a` o `b` por penales (algo más probable el de mejor media)."""
    p_a = float(np.clip(0.5 + (L["r"][a] - L["r"][b]) / 400, 0.35, 0.65))
    gana_a = bool(rng.random() < p_a)
    gana_local = (L["nombres"][a] == p_vuelta["local"]) == gana_a
    tanda = tanda_penales(rng, gana_local)
    p_vuelta["tanda"], p_vuelta["pen"] = tanda, (sum(tanda[0]), sum(tanda[1]))
    p_vuelta["gana"] = L["nombres"][a] if gana_a else L["nombres"][b]
    return a if gana_a else b


class Uruguay(Formato):
    nombre = "uruguay"
    descripcion = ("Apertura, Intermedio (dos grupos) y Clausura; la Tabla Anual define al finalista de las finales por "
                   "el campeonato. Descienden los tres de peor promedio de dos temporadas.")
    etapas_definicion = (FINAL_INTERMEDIO, DESEMPATE + "Apertura", DESEMPATE + "Clausura", DESEMPATE + "Anual",
                         SEMIFINAL, FINAL_IDA, FINAL_VUELTA)
    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        cal = cfg["calendario"]
        ida = rueda(rng, range(n))
        vuelta = espejo(ida)
        d_ap = dias_semanales(anio, cal["Apertura"], len(ida))
        d_cl = dias_semanales(anio, cal["Clausura"], len(vuelta))
        k_int = _rondas_de_grupo(max(len(_grupo_a(n)), n - len(_grupo_a(n))))
        d_int = dias_semanales(anio, cal["Intermedio"], k_int + 1)
        rondas = [ronda("Apertura", f"Apertura · fecha {k + 1}", "Apertura", d_ap[k], pares=f, suma="Apertura")
                  for k, f in enumerate(ida)]
        rondas += [ronda("Intermedio", f"Intermedio · fecha {k + 1}", "Intermedio", d_int[k], suma="Intermedio")
                   for k in range(k_int)]
        rondas.append(ronda(FINAL_INTERMEDIO, "Intermedio · final", "Final del Intermedio", d_int[k_int], ko=True,
                            neutral=True))
        rondas += [ronda("Clausura", f"Clausura · fecha {k + 1}", "Clausura", d_cl[k], pares=f, suma="Clausura")
                   for k, f in enumerate(vuelta)]
        return {
            "formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
            "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
            "E": {t: stats_vacias(n) for t in TORNEOS}, "descensos": int(cfg.get("descensos", 0)),
            "previo": {k: (int(v[0]), int(v[1])) for k, v in previo.items()},
            "definiciones": desde(anio, *cal["Definiciones"]),
            "grupos": None, "orden_apertura": None, "finalistas_intermedio": None,
            "ganadores": {"Apertura": None, "Intermedio": None, "Clausura": None, "Anual": None},
            "desempates": {}, "hecho": {"Apertura": False, "Intermedio": False, "Clausura": False, "Anual": False},
            "campeon_corto": None, "campeon": None, "subcampeon": None, "via": "",
        }
    def avanzar(self, L, rng):
        for _ in range(12):
            if not self._paso(L, rng):
                return

    def _paso(self, L, rng):
        H, G, E = L["hecho"], L["ganadores"], L["E"]
        if not H["Apertura"]:
            if not _completa(L, "Apertura"):
                return False
            df = tabla(L, E["Apertura"])
            if not _desempate_primero(L, "Apertura", df):
                return False
            orden = [int(i) for i in df["id"]]
            orden.remove(G["Apertura"])
            L["orden_apertura"] = [G["Apertura"]] + orden
            _armar_intermedio(L, rng)
            H["Apertura"] = True
            return True
        if not H["Intermedio"]:
            if not _completa(L, "Intermedio"):
                return False
            fin = L["rondas"][_indices(L, FINAL_INTERMEDIO)[0]]
            if fin["pares"] is None:
                L["finalistas_intermedio"] = [int(tabla(L, E["Intermedio"], g).iloc[0]["id"]) for g in L["grupos"]]
                fin["pares"] = [tuple(L["finalistas_intermedio"])]
                return False
            if not _jugada(L, FINAL_INTERMEDIO):
                return False
            G["Intermedio"] = _ganador_de(L, FINAL_INTERMEDIO)
            H["Intermedio"] = True
            return True
        if not H["Clausura"]:
            if not _completa(L, "Clausura"):
                return False
            if not _desempate_primero(L, "Clausura", tabla(L, E["Clausura"])):
                return False
            H["Clausura"] = True
            return True
        if not H["Anual"]:
            if not _desempate_primero(L, "Anual", _tabla_anual(L)):
                return False
            H["Anual"] = True
            return True
        if L["campeon"] is None:
            return self._definiciones(L, rng)
        return False

    def _definiciones(self, L, rng):
        """Semifinal (si hace falta) y finales por el campeonato. True si se definió algo y hay que seguir mirando."""
        G, nom = L["ganadores"], L["nombres"]
        A, C, Y = G["Apertura"], G["Clausura"], G["Anual"]
        if L["campeon_corto"] is None:
            if A == C:
                L["campeon_corto"] = A
            else:
                if not _indices(L, SEMIFINAL):
                    dia = max(L["definiciones"], _ultimo_dia(L) + dt.timedelta(days=4))
                    _agregar(L, ronda(SEMIFINAL, "Semifinal del campeonato", "Semifinal", dia, pares=[(A, C)], ko=True,
                                      neutral=True))
                    return False
                if not _jugada(L, SEMIFINAL):
                    return False
                L["campeon_corto"] = _ganador_de(L, SEMIFINAL)
            return True
        S = L["campeon_corto"]
        if S == Y:                                  # el campeón de los torneos cortos ya era el de la Anual
            if A == C:                              # ganó Apertura, Clausura y Anual: subcampeón = 2° de la Anual
                sub = L["nombres"][int(_tabla_anual(L).iloc[1]["id"])]
                L["via"] = "Ganó el Apertura, el Clausura y la Tabla Anual: campeón sin finales."
            else:                                   # ganó la Anual y la semifinal: subcampeón = el que perdió la semifinal
                sub = nom[C if Y == A else A]
                L["via"] = ("Ganó la Tabla Anual y la semifinal entre los campeones del Apertura y del Clausura: "
                            "campeón sin final.")
            L["campeon"], L["subcampeon"] = nom[Y], sub
            return True
        if not _indices(L, FINAL_IDA):
            dia = max(L["definiciones"] + UNA_SEMANA, _ultimo_dia(L) + UNA_SEMANA)
            _agregar(L, ronda(FINAL_IDA, "Final · ida", "Final", dia, pares=[(S, Y)], ida_vuelta="ida"))
            _agregar(L, ronda(FINAL_VUELTA, "Final · vuelta", "Final", dia + UNA_SEMANA, pares=[(Y, S)],
                              ida_vuelta="vuelta"))
            return False
        if not _jugada(L, FINAL_VUELTA):
            return False
        p1 = partidos_de_ronda(L, _indices(L, FINAL_IDA)[0] + 1)[0]
        p2 = partidos_de_ronda(L, _indices(L, FINAL_VUELTA)[0] + 1)[0]
        g_s, g_y = p1["gl"] + p2["gv"], p1["gv"] + p2["gl"]
        if g_s == g_y:
            ganador = _penales_del_global(L, p2, S, Y, rng)
        else:
            ganador = S if g_s > g_y else Y
        perdedor = Y if ganador == S else S
        L["campeon"], L["subcampeon"] = nom[ganador], nom[perdedor]
        L["global_final"] = {"a": nom[S], "b": nom[Y], "ga": int(g_s), "gb": int(g_y)}
        if ganador == S:
            L["via"] = f"Ganó la final a ida y vuelta al campeón de la Tabla Anual (global {g_s}-{g_y})."
        else:
            L["via"] = f"Ganó la final a ida y vuelta como campeón de la Tabla Anual (global {g_y}-{g_s})."
        return True
    def tablas(self, L):
        H, G = L["hecho"], L["ganadores"]
        out = []
        for t in ("Apertura", "Clausura"):
            df = tabla(L, L["E"][t])
            gan = G[t]
            df["Destino"] = ["Campeón" if gan is not None and i == gan else "Líder" if p == 1 else ""
                             for p, i in zip(df["Pos"], df["id"])]
            out.append({"titulo": t, "df": df, "tipo": "liga", "nota": ""})
        if L["grupos"] is None:
            out.insert(1, {"titulo": "Intermedio", "df": None, "tipo": "grupos",
                           "nota": "Los grupos se arman al terminar el Apertura."})
        else:
            for nombre, ids in zip(("A", "B"), L["grupos"]):
                df = tabla(L, L["E"]["Intermedio"], ids)
                fin = L["finalistas_intermedio"]
                df["Destino"] = ["A la final" if (fin and i in fin) or (not fin and p == 1) else ""
                                 for p, i in zip(df["Pos"], df["id"])]
                out.insert(1 + (nombre == "B"), {"titulo": f"Intermedio · Grupo {nombre}", "df": df, "tipo": "liga",
                                                "nota": ""})
        anual = _tabla_anual(L)
        cupos = asignar_cupos(self._orden_cupos(L, anual), L.get("cupos", []), L.get("camp_int"))
        anual["Destino"] = [" · ".join(x for x in (
            "Campeón" if L["campeon"] == n else "A la final" if G["Anual"] == i and L["campeon"] is None else "",
            cupos.get(n, "")) if x) for n, i in zip(anual["Equipo"], anual["id"])]
        nota = ("Apertura + Intermedio + Clausura. Quien la gana va directo a la final por el campeonato. "
                + ("Cupos: campeón y subcampeón, y después la tabla. " if L["campeon"] else
                   "Cupos provisorios por la posición de hoy; el campeón y el subcampeón van primero. ")
                + "Uruguay 4 (Libertadores · Fase 1) es del campeón de la Copa AUF Uruguay en el reglamento real, pero esa "
                  "copa no se simula: sale de esta tabla.")
        out.append({"titulo": "Tabla Anual", "df": anual, "tipo": "liga", "nota": nota})
        out.append({"titulo": "Descenso", "df": self._promedios(L), "tipo": "descenso",
                    "nota": f"Puntos de la temporada anterior + los de esta, sobre los partidos jugados. "
                            f"Descienden los {L['descensos']} de peor promedio."})
        return out

    def _orden_cupos(self, L, anual):
        """Orden en que se reparten los cupos: campeón, subcampeón y el resto por Tabla Anual. Mientras no haya campeón,
        la tabla de hoy."""
        if L["campeon"] is None:
            return list(anual["Equipo"])
        return [L["campeon"], L["subcampeon"]] + [n for n in anual["Equipo"] if n not in (L["campeon"], L["subcampeon"])]

    def _promedios(self, L):
        """Tabla del descenso, del mejor al peor promedio (puntos de dos temporadas sobre partidos jugados)."""
        anual = _tabla_anual(L)
        prev = L["previo"]
        df = anual[["Equipo", "DG"]].copy()
        df["Pts"] = [int(x) + prev.get(n, (0, 0))[0] for n, x in zip(anual["Equipo"], anual["Pts"])]
        df["PJ"] = [int(x) + prev.get(n, (0, 0))[1] for n, x in zip(anual["Equipo"], anual["PJ"])]
        df["Prom"] = [p / j if j else 0.0 for p, j in zip(df["Pts"], df["PJ"])]
        df = df.sort_values(["Prom", "Pts", "DG"], ascending=False).reset_index(drop=True)
        n, d = len(df), L["descensos"]
        df.insert(0, "Pos", df.index + 1)
        df["Destino"] = ["Desciende" if d and p > n - d else "" for p in df["Pos"]]
        return df[["Pos", "Equipo", "Pts", "PJ", "Prom", "Destino"]]
    def cierre(self, L):
        anual = _tabla_anual(L)
        prom = self._promedios(L)
        d = L["descensos"]
        orden = self._orden_cupos(L, anual)
        return {"campeon": L["campeon"], "orden": orden,
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in anual.iterrows()},
                "descienden": list(prom["Equipo"])[len(prom) - d:] if d else []}


FORMATOS[Uruguay.nombre] = Uruguay()
