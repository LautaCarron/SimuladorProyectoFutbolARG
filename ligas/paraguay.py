"""Paraguay: Copa de Primera (Apertura y Clausura) y División Intermedia, las dos con descenso por promedio.

Copa de Primera (formato `paraguay`, 12 clubes):
  * Apertura (22 fechas, ida y vuelta) y Clausura (22 fechas, con otro sorteo): cada torneo tiene su campeón. El título del
    año es UNO solo: los dos campeones juegan una final a partido único en cancha neutral (si un club gana los dos
    torneos es campeón directo).
  * Reclasificación (Apertura + Clausura): reparte los cupos CONMEBOL. Los dos campeones van a la fase de grupos de la
    Libertadores; el resto sale de la tabla acumulada (si un club gana los dos torneos, el segundo cupo sigue por la tabla).
  * Descenso: promedio de puntos por partido de las últimas tres temporadas en Primera; bajan los 2 peores. Los clubes
    recién ascendidos sólo cuentan lo que jugaron en Primera. Suben el campeón y el subcampeón de la Intermedia.

División Intermedia (formato `paraguay_segunda`, 16 clubes): todos contra todos a doble rueda (30 fechas). Suben el
campeón y el subcampeón; bajan los 3 peores promedios de tres temporadas a la tercera división (que no se simula).

Los puntos de 2024 y 2025 de cada club (`puntos_previos` de liga_paraguay.json) siembran el promedio de la primera
temporada simulada. Sin Streamlit: motor puro (ver ligas/exterior.py).
"""

import datetime as dt

import numpy as np
import pandas as pd

from ligas.exterior import (FORMATOS, Formato, TodosContraTodos, _cupos_de_pais, asignar_cupos, dias_cada, espejo,
                            partidos_de_ronda, ronda, rueda, stats_vacias, tabla)

ANIOS_PROMEDIO = 3          # temporadas que cuenta el promedio de descenso
PASO_DIAS = 6               # una fecha cada 6 días en Apertura y Clausura (hay fechas entre semana)


def _historial(previos, nombre, anio, anios):
    """Temporadas del club dentro de la ventana del promedio (las `anios - 1` anteriores a `anio`): {año: (pts, pj)}.
    `previos[club]` es una lista de [puntos, partidos, año]; si falta el año (partidas viejas) se cuenta hacia atrás."""
    lista = list(previos.get(nombre, []))
    out = {}
    for k, x in enumerate(lista):
        a = int(x[2]) if len(x) > 2 else anio - (len(lista) - k)
        if anio - anios < a < anio:
            out[a] = (int(x[0]), int(x[1]))
    return out


def tabla_promedio(L, E, d, excluir=()):
    """Tabla de descenso por promedio: puntos de cada una de las últimas tres temporadas, total, partidos y promedio
    (puntos / partidos). `E` son las estadísticas de la temporada en curso (las de este año). Los `d` peores bajan,
    salvo los de `excluir` (los que suben: en la Intermedia, el campeón y el subcampeón no pueden bajar)."""
    anios = int(L.get("anios_promedio", ANIOS_PROMEDIO))
    anio = int(L["anio"])
    previos = L.get("promedios_previos", {})
    años = list(range(anio - anios + 1, anio + 1))
    filas = []
    for i, nombre in enumerate(L["nombres"]):
        pj = int(E["pj"][i])
        pts = int(3 * E["g"][i] + E["e"][i])
        h = _historial(previos, nombre, anio, anios)
        if pj:
            h[anio] = (pts, pj)
        total_pts, total_pj = sum(v[0] for v in h.values()), sum(v[1] for v in h.values())
        fila = {"Equipo": nombre}
        for a in años:
            fila[f"Pts {a}"] = h[a][0] if a in h else None
        fila.update({"Pts": total_pts, "PJ": total_pj, "Promedio": total_pts / total_pj if total_pj else 0.0,
                     "_pts": pts, "_dg": int(E["gf"][i] - E["gc"][i]), "_gf": int(E["gf"][i])})
        filas.append(fila)
    df = pd.DataFrame(filas).sort_values(["Promedio", "_pts", "_dg", "_gf"], ascending=False,
                                         kind="stable").reset_index(drop=True)
    df = df.drop(columns=["_pts", "_dg", "_gf"])
    for a in años:                                       # "–" donde el club no jugó esa temporada en esta categoría
        df[f"Pts {a}"] = [("–" if pd.isna(v) else int(v)) for v in df[f"Pts {a}"]]
    df.insert(0, "Pos", range(1, len(df) + 1))
    excluir = set(excluir)
    bajan = [n for n in reversed(list(df["Equipo"])) if n not in excluir][:d] if d else []
    df["Destino"] = ["Desciende" if n in bajan else "" for n in df["Equipo"]]
    return df


def _bajan(df):
    """Clubes marcados para bajar en una tabla de `tabla_promedio` (del último al anterior)."""
    return [n for n, dest in zip(df["Equipo"], df["Destino"]) if dest == "Desciende"][::-1]


class Paraguay(Formato):
    """Copa de Primera: Apertura y Clausura, final entre los dos campeones (un título por año), reclasificación y promedio."""
    nombre = "paraguay"
    descripcion = ("Apertura y Clausura (22 fechas cada uno) y final entre los dos campeones: un título por año. "
                   "Descenso por el promedio de tres temporadas.")
    etapas_definicion = ("Final anual",)
    torneos = ("Apertura", "Clausura")

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        cal = cfg["calendario"]
        rondas = []
        for torneo in self.torneos:
            ida = rueda(rng, range(n))                 # cada torneo con su propio sorteo de fechas
            fechas = ida + espejo(ida)
            dias = dias_cada(anio, cal[torneo], len(fechas), PASO_DIAS)
            for k, f in enumerate(fechas):
                R = ronda(torneo, f"{torneo} · fecha {k + 1}", torneo, dias[k], pares=f, suma=torneo)
                R["suma_extra"] = "Anual"              # la reclasificación suma los dos torneos
                rondas.append(R)
        return {"formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
                "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
                "E": {"Apertura": stats_vacias(n), "Clausura": stats_vacias(n), "Anual": stats_vacias(n)},
                "descensos": int(cfg.get("descensos", 0)), "ascensos": int(cfg.get("ascensos", 0)),
                "campeon": None, "subcampeon": None, "ganadores": {}, "subs": {}, "titulos": [], "via": "",
                "divisional": int(cfg.get("divisional", 1)), "anio": int(anio),
                "anios_promedio": int(cfg.get("promedio_temporadas", ANIOS_PROMEDIO)),
                "promedios_previos": {k: list(v) for k, v in (previo or {}).items()}}

    def _terminado(self, L, torneo):
        ix = [i for i, R in enumerate(L["rondas"]) if R["etapa"] == torneo]
        return bool(ix) and ix[-1] < L["fecha"]

    def avanzar(self, L, rng):
        nom = L["nombres"]
        for t in self.torneos:                         # cada torneo se define solo, al jugarse su última fecha
            if t not in L["ganadores"] and self._terminado(L, t):
                df = tabla(L, L["E"][t])
                L["ganadores"][t], L["subs"][t] = int(df.iloc[0]["id"]), int(df.iloc[1]["id"])
        if L["campeon"] is None and len(L["ganadores"]) == len(self.torneos) and L["fecha"] >= len(L["rondas"]):
            a, c = L["ganadores"]["Apertura"], L["ganadores"]["Clausura"]
            if a == c:                                  # ganó los dos torneos: campeón directo, sin final
                L["campeon"], L["subcampeon"] = nom[a], nom[L["subs"]["Clausura"]]
                L["via"] = f"{nom[a]} ganó el Apertura y el Clausura: campeón directo, sin final."
            else:                                       # final a partido único entre los dos campeones
                L["rondas"].append(ronda("Final anual", "Final · campeón del Apertura vs campeón del Clausura", "Final",
                                         L["rondas"][-1]["dia"] + dt.timedelta(days=7), pares=[(a, c)], ko=True, neutral=True))
        ix = [i for i, R in enumerate(L["rondas"]) if R["etapa"] == "Final anual"]
        if L["campeon"] is None and ix and L["fecha"] > ix[0]:          # la final ya se jugó
            p = partidos_de_ronda(L, ix[0] + 1)[0]
            a, c = L["ganadores"]["Apertura"], L["ganadores"]["Clausura"]
            gana = p["gana"] if isinstance(p["gana"], str) else nom[int(p["gana"])]
            pierde = nom[c] if gana == nom[a] else nom[a]
            L["campeon"], L["subcampeon"] = gana, pierde
            otro = nom[c] if p["local"] == nom[a] else nom[a]
            L["via"] = (f"Apertura: {nom[a]} · Clausura: {nom[c]}. Final: {p['local']} {p['gl']}-{p['gv']} {otro}"
                        + (" (por penales)" if p.get("tanda") else "") + f". Campeón: {gana}.")
        if L["campeon"] is not None:
            L["titulos"] = [L["campeon"]]               # un título por año, el de la final (o el del club que ganó los dos)

    def _orden_final(self, L):
        """(orden, promedio, bajan): `orden` = campeones de los torneos ya definidos y después la reclasificación; los que
        bajan van al final (no clasifican a copas)."""
        nom = L["nombres"]
        agg = tabla(L, L["E"]["Anual"])
        prom = tabla_promedio(L, L["E"]["Anual"], int(L.get("descensos", 0)))
        bajan = _bajan(prom)
        camp = [nom[L["ganadores"][t]] for t in self.torneos if t in L["ganadores"]]
        orden = [n for n in dict.fromkeys(camp + list(agg["Equipo"])) if n not in set(bajan)] + bajan
        return orden, prom, bajan

    def tablas(self, L):
        out, nom = [], L["nombres"]
        for t in self.torneos:
            df = tabla(L, L["E"][t])
            hecho = t in L["ganadores"]
            df["Destino"] = [(f"Campeón {t}" if hecho else "Líder") if p == 1 else "" for p in df["Pos"]]
            out.append({"titulo": t, "df": df, "tipo": "liga",
                        "nota": f"22 fechas a doble rueda. Los campeones del Apertura y del Clausura juegan la final por el "
                                f"título del año (si es el mismo club, es campeón directo)."})
        orden, prom, _ = self._orden_final(L)
        cupos = L.get("cupos") or _cupos_de_pais(L.get("pais", ""))
        mapa = asignar_cupos(orden, cupos, L.get("camp_int")) if cupos else {}
        agg = tabla(L, L["E"]["Anual"])

        def destino(club):
            cupo = mapa.get(club, "")
            ts = [t for t in self.torneos if t in L["ganadores"] and nom[L["ganadores"][t]] == club]
            if ts:
                base = "Campeón " + " y ".join(ts)
                return f"{base} · {cupo}" if cupo else base
            return cupo

        agg["Destino"] = [destino(c) for c in agg["Equipo"]]
        try:
            from copas.conmebol import NOTA_COPA
            extra = NOTA_COPA.get(L.get("pais", ""), "")
        except ImportError:
            extra = ""
        out.append({"titulo": "Reclasificación · cupos", "df": agg, "tipo": "liga",
                    "nota": ("Suma Apertura y Clausura. Los campeones de cada torneo van a la fase de grupos de la "
                             "Libertadores y el resto de los cupos sigue por esta tabla. "
                             + ("" if len(L["ganadores"]) == len(self.torneos) else "Destinos provisorios. ") + extra).strip()})
        out.append({"titulo": "Tabla de descenso · promedio", "df": prom, "tipo": "descenso",
                    "nota": ("Puntos por partido de las últimas tres temporadas en Primera; bajan los dos peores a la "
                             "División Intermedia. Los recién ascendidos sólo cuentan lo que jugaron en Primera.")})
        return out

    def cierre(self, L):
        orden, prom, bajan = self._orden_final(L)
        anual = L["E"]["Anual"]
        return {"campeon": L["campeon"], "orden": orden,
                "puntos": {n: (int(3 * anual["g"][i] + anual["e"][i]), int(anual["pj"][i])) for i, n in enumerate(L["nombres"])},
                "descienden": bajan, "suben": [],
                "promedio": {r["Equipo"]: float(r["Promedio"]) for _, r in prom.iterrows()}}


class ParaguayIntermedia(TodosContraTodos):
    """División Intermedia: 16 clubes, 30 fechas a doble rueda. Suben los 2 primeros; bajan los 3 peores promedios."""
    nombre = "paraguay_segunda"
    descripcion = ("Todos contra todos a doble rueda (30 fechas). Suben el campeón y el subcampeón; bajan los tres "
                   "peores promedios de tres temporadas.")

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        L = super().nueva(cfg, nombres, r, previo, anio, rng)
        L.update({"anio": int(anio), "anios_promedio": int(cfg.get("promedio_temporadas", ANIOS_PROMEDIO)),
                  "promedios_previos": {k: list(v) for k, v in (previo or {}).items()}})
        return L

    def _promedio(self, L):
        a = int(L.get("ascensos", 0))
        df = tabla(L, L["E"]["Liga"])
        return df, tabla_promedio(L, L["E"]["Liga"], int(L.get("descensos", 0)), excluir=list(df["Equipo"])[:a])

    def tablas(self, L):
        df, prom = self._promedio(L)
        a = int(L.get("ascensos", 0))
        hecho = L.get("campeon") is not None
        df["Destino"] = [(("Campeón" if hecho else "Líder") + (" · Asciende" if a else "")) if p == 1
                         else ("Asciende" if a and p <= a else "") for p in df["Pos"]]
        try:
            from datos import ligas_ext
            sup = ligas_ext.CONFIG[ligas_ext.CONFIG[L["clave"]]["superior"]]["nombre"]
        except Exception:
            sup = "Primera División"
        nota = (f"Ascienden a {sup} los {a} primeros" + ("." if hecho else " (posiciones provisorias).")) if a else ""
        return [{"titulo": "Posiciones", "df": df, "tipo": "liga", "nota": nota},
                {"titulo": "Tabla de descenso · promedio", "df": prom, "tipo": "descenso",
                 "nota": (f"Puntos por partido de las últimas tres temporadas en la Intermedia; bajan los "
                          f"{int(L.get('descensos', 0))} peores a la tercera división (Primera B).")}]

    def cierre(self, L):
        df, prom = self._promedio(L)
        a = int(L.get("ascensos", 0))
        return {"campeon": L["campeon"], "orden": list(df["Equipo"]),
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in df.iterrows()},
                "descienden": _bajan(prom), "suben": list(df["Equipo"])[:a],
                "promedio": {r["Equipo"]: float(r["Promedio"]) for _, r in prom.iterrows()}}


FORMATOS[Paraguay.nombre] = Paraguay()
FORMATOS[ParaguayIntermedia.nombre] = ParaguayIntermedia()
