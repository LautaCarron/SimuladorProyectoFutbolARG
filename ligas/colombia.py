"""Formato Liga BetPlay de Colombia: Apertura y Clausura con cuadrangulares semifinales."""
import datetime as dt
import numpy as np
from ligas.exterior import (FORMATOS, Formato, UNA_SEMANA, dias_semanales, espejo, ronda, rueda,
                            stats_vacias, sumar_stats, tabla, partidos_de_ronda)
from motor.fechas import desde
from motor.nucleo import tanda_penales

class Colombia(Formato):
    nombre = "colombia"
    descripcion = ("Apertura y Clausura: 19 fechas, cuadrangulares semifinales de seis fechas "
                   "y final ida/vuelta. Campeón anual en partido único entre ambos ganadores.")
    etapas_definicion = ("Apertura · cuadrangulares", "AF", "Clausura · cuadrangulares", "CF", "Final anual")

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        ida = rueda(rng, range(n))
        vuelta = espejo(ida)
        cal = cfg["calendario"]
        da = dias_semanales(anio, cal["Apertura"], len(ida))
        dc = dias_semanales(anio, cal["Clausura"], len(vuelta))
        rondas = [ronda("Apertura", f"Apertura · fecha {i+1}", "Apertura", da[i], pares=f, suma="Apertura")
                  for i, f in enumerate(ida)]
        for R in rondas: R["suma_extra"] = "Reclasificacion"
        # Se reservan las fechas del Clausura; las fases finales se insertan antes cuando corresponda.
        clausura = [ronda("Clausura", f"Clausura · fecha {i+1}", "Clausura", dc[i], pares=f, suma="Clausura")
                    for i, f in enumerate(vuelta)]
        for R in clausura: R["suma_extra"] = "Reclasificacion"
        rondas += clausura
        return {"formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
                "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
                "E": {"Apertura": stats_vacias(n), "Clausura": stats_vacias(n),
                      "Apertura_Cuadrangulares": stats_vacias(n), "Clausura_Cuadrangulares": stats_vacias(n),
                      "Reclasificacion": stats_vacias(n)},
                "descensos": int(cfg.get("descensos", 0)), "ascensos": int(cfg.get("ascensos", 0)),
                "campeon": None, "subcampeon": None, "ganadores": {}, "hecho": {},
                "grupos": {"Apertura": None, "Clausura": None}, "previo": {}, "promedios_previos": dict(previo or {}), "via": ""}

    def _idx(self, L, etapa):
        return [i for i, x in enumerate(L["rondas"]) if x["etapa"] == etapa]

    def _add(self, L, etapa, rotulo, comp, pares, dia, ko=False, neutral=False, ida_vuelta=None):
        R = ronda(etapa, rotulo, comp, dia, pares=pares, ko=ko, neutral=neutral, ida_vuelta=ida_vuelta)
        if comp.startswith(("Apertura", "Clausura")):
            R["suma_extra"] = "Reclasificacion"
        if etapa.endswith("cuadrangulares"):
            torneo = "Apertura" if etapa.startswith("Apertura") else "Clausura"
            R["suma"] = f"{torneo}_Cuadrangulares"
        # Las definiciones del Apertura deben jugarse antes de iniciar el Clausura.
        if comp.startswith("Apertura"):
            prev = [i for i, x in enumerate(L["rondas"]) if x["comp"].startswith("Apertura")]
            pos = prev[-1] + 1 if prev else len(L["rondas"])
            L["rondas"].insert(pos, R)
        elif comp.startswith("Clausura"):
            prev = [i for i, x in enumerate(L["rondas"]) if x["comp"].startswith("Clausura")]
            pos = prev[-1] + 1 if prev else len(L["rondas"])
            L["rondas"].insert(pos, R)
        else:
            L["rondas"].append(R)

    def _finish(self, L, etapa):
        ix = self._idx(L, etapa)
        return bool(ix) and ix[-1] < L["fecha"]

    def _series_winner(self, L, etapa, rng):
        ix = self._idx(L, etapa)
        p1 = partidos_de_ronda(L, ix[0]+1)[0]
        p2 = partidos_de_ronda(L, ix[1]+1)[0]
        a, b = L["nombres"].index(p1["local"]), L["nombres"].index(p1["visita"])
        ga, gb = p1["gl"] + p2["gv"], p1["gv"] + p2["gl"]
        if ga == gb:
            pa = float(np.clip(.5 + (L["r"][a]-L["r"][b])/400, .35, .65))
            winner = a if rng.random() < pa else b
            p2["tanda"] = tanda_penales(rng, winner == L["nombres"].index(p2["local"]))
            p2["pen"] = (sum(p2["tanda"][0]), sum(p2["tanda"][1]))
            p2["gana"] = L["nombres"][winner]
            return winner
        return a if ga > gb else b

    def _schedule_series(self, L, etapa, comp, a, b, day):
        self._add(L, etapa, f"{comp} · ida", comp, [(a,b)], day, ida_vuelta="ida")
        self._add(L, etapa, f"{comp} · vuelta", comp, [(b,a)], day+UNA_SEMANA, ida_vuelta="vuelta")

    def avanzar(self, L, rng):
        n = len(L["nombres"])
        if not isinstance(L.get("grupos"), dict):
            L["grupos"] = {"Apertura": None, "Clausura": None}
        for torneo in ("Apertura", "Clausura"):
            L["E"].setdefault(f"{torneo}_Cuadrangulares", stats_vacias(n))
        # Ambos semestres: los ocho primeros pasan a dos cuadrangulares semifinales.
        # Se distribuyen 1-4-5-8 y 2-3-6-7; el ganador de cada grupo juega la final.
        for t, etapa, final_etapa in (("Apertura", "Apertura · cuadrangulares", "AF"),
                                      ("Clausura", "Clausura · cuadrangulares", "CF")):
            if etapa not in L["hecho"] and self._finish(L, t):
                df = tabla(L, L["E"][t])
                ids = [int(x) for x in df["id"][:8]]
                L[f"clasificados_{t.lower()}"] = list(ids)
                if len(ids) >= 8:
                    groups = [[ids[i] for i in (0, 3, 4, 7)],
                              [ids[i] for i in (1, 2, 5, 6)]]
                    L["grupos"][t] = groups
                    fa, fb = rueda(rng, groups[0]), rueda(rng, groups[1])
                    fa, fb = fa + espejo(fa), fb + espejo(fb)
                    day = L["rondas"][self._idx(L, t)[-1]]["dia"] + dt.timedelta(days=4)
                    for k in range(6):
                        self._add(L, etapa, f"{t} · cuadrangulares · fecha {k+1}", etapa,
                                  fa[k] + fb[k], day + k * UNA_SEMANA)
                    L["hecho"][etapa] = "pendiente"
                    return
            if L["hecho"].get(etapa) == "pendiente" and self._finish(L, etapa):
                groups = L["grupos"].get(t) or []
                winners = [int(tabla(L, L["E"][f"{t}_Cuadrangulares"], group).iloc[0]["id"]) for group in groups]
                if len(winners) == 2:
                    self._schedule_series(L, final_etapa, f"{t} · final", winners[0], winners[1],
                                          L["rondas"][-1]["dia"] + dt.timedelta(days=4))
                    L["hecho"][etapa] = "listo"
                    L["hecho"][f"{t} · final"] = "pendiente"
                    return
            if L["hecho"].get(f"{t} · final") == "pendiente" and self._finish(L, final_etapa):
                L["ganadores"][t] = self._series_winner(L, final_etapa, rng)
                L["hecho"][f"{t} · final"] = "listo"
        # Superfinal anual: partido único, sólo si son campeones distintos.
        if "Apertura" in L["ganadores"] and "Clausura" in L["ganadores"] and L["campeon"] is None:
            a,b=L["ganadores"]["Apertura"],L["ganadores"]["Clausura"]
            if a==b:
                L["campeon"]=L["nombres"][a]
                ix=self._idx(L,"CF")
                if ix:
                    p=partidos_de_ronda(L,ix[0]+1)[0]
                    L["subcampeon"]=p["visita"] if p["local"]==L["campeon"] else p["local"]
                L["via"]="Ganó Apertura y Clausura; no se disputó la final anual."
            else:
                if "Final anual" not in L["hecho"]:
                    self._add(L,"Final anual","Final anual Colombia","Final anual",[(a,b)],
                              L["rondas"][-1]["dia"]+dt.timedelta(days=7),ko=True,neutral=True)
                    L["hecho"]["Final anual"]="pendiente"
                elif self._finish(L,"Final anual"):
                    p=partidos_de_ronda(L,self._idx(L,"Final anual")[0]+1)[0]
                    L["campeon"]=p["gana"]
                    L["subcampeon"]=L["nombres"][b if p["gana"]==L["nombres"][a] else a]
                    L["via"]="Ganador del partido único entre los campeones del Apertura y el Clausura."

    def _tabla_descenso(self, L):
        """Promedio de descenso: hasta las tres últimas temporadas disputadas en Primera."""
        actual = sumar_stats(L["E"]["Apertura"], L["E"]["Clausura"])
        filas = []
        previos = L.get("promedios_previos", {})
        for i, nombre in enumerate(L["nombres"]):
            pj = int(actual["pj"][i])
            pts = int(3 * actual["g"][i] + actual["e"][i])
            temporadas = list(previos.get(nombre, []))[-2:] + ([(pts, pj)] if pj else [])
            total_pts = sum(int(x[0]) for x in temporadas)
            total_pj = sum(int(x[1]) for x in temporadas)
            promedio = total_pts / total_pj if total_pj else 0.0
            filas.append({"Equipo": nombre, "Pts": total_pts, "PJ": total_pj,
                          "Promedio": promedio, "Pts temporada": pts,
                          "DG temporada": int(actual["gf"][i] - actual["gc"][i]),
                          "GF temporada": int(actual["gf"][i]), "id": i})
        import pandas as pd
        df = pd.DataFrame(filas).sort_values(
            ["Promedio", "Pts temporada", "DG temporada", "GF temporada"],
            ascending=[False, False, False, False], kind="stable").reset_index(drop=True)
        df.insert(0, "Pos", range(1, len(df) + 1))
        d = int(L.get("descensos", 0))
        df["Destino"] = ["Desciende" if d and pos > len(df) - d else "" for pos in df["Pos"]]
        return df

    def tablas(self,L):
        out=[]
        if not isinstance(L.get("grupos"), dict):
            L["grupos"] = {"Apertura": None, "Clausura": None}
        for torneo in ("Apertura", "Clausura"):
            L["E"].setdefault(f"{torneo}_Cuadrangulares", stats_vacias(len(L["nombres"])))
        for t in ("Apertura", "Clausura"):
            df = tabla(L, L["E"][t])
            champ = L["ganadores"].get(t)
            df["Destino"] = ["Campeón" if champ is not None and i == champ else
                             "Cuadrangulares" if p <= 8 else "" for p, i in zip(df["Pos"], df["id"])]
            out.append({"titulo": t, "df": df, "tipo": "liga",
                        "nota": "Los ocho primeros avanzan a los cuadrangulares semifinales."})
            groups = (L.get("grupos") or {}).get(t) or []
            for label, ids in zip(("A", "B"), groups):
                group_df = tabla(L, L["E"][f"{t}_Cuadrangulares"], ids)
                group_df["Destino"] = ["A la final" if pos == 1 else "" for pos in group_df["Pos"]]
                out.append({"titulo": f"{t} · Grupo {label}", "df": group_df, "tipo": "liga",
                            "nota": f"El ganador del grupo clasifica a la final del {t}."})
        rec = tabla(L, L["E"]["Reclasificacion"])
        orden = list(rec["Equipo"])
        copa = L.get("campeon_copa_colombia")
        asignados = {}
        for i, club in enumerate(orden):
            if i < 2: asignados[club] = "Libertadores · Fase de grupos"
            elif i < 4: asignados[club] = "Libertadores · Fase 2"
        sud = []
        if copa in L["nombres"] and copa not in asignados:
            sud.append(copa)
            asignados[copa] = "Sudamericana · campeón Copa Colombia"
        for club in orden:
            if len(sud) >= 4: break
            if club not in asignados:
                sud.append(club)
                asignados[club] = "Sudamericana"
        rec["Destino"] = [asignados.get(eq, "") for eq in rec["Equipo"]]
        out.append({"titulo":"Reclasificación total · cupos internacionales","df":rec,"tipo":"liga",
                    "nota":"Acumula los partidos de todos contra todos y cuadrangulares de ambos semestres. "
                          "Los cupos de Copa Colombia se muestran cuando se define su campeón."})
        descenso = self._tabla_descenso(L)
        out.append({"titulo":"Tabla de descenso · promedio","df":descenso,"tipo":"descenso",
                    "nota":"Promedio de puntos por partido de las últimas tres temporadas disputadas en Primera. "
                          "Los dos últimos descienden. En partidas nuevas sólo se cuentan las temporadas simuladas."})
        return out

    def cierre(self,L):
        df=tabla(L,L["E"]["Clausura"])
        anual = sumar_stats(L["E"]["Apertura"], L["E"]["Clausura"])
        d=int(L.get("descensos",0))
        descenso=self._tabla_descenso(L)
        bajan=list(descenso.tail(d)["Equipo"]) if d else []
        return {"campeon":L["campeon"],"orden":list(df["Equipo"]),
                "puntos":{n:(int(3*anual["g"][i]+anual["e"][i]),int(anual["pj"][i])) for i,n in enumerate(L["nombres"])},
                "descienden":bajan,"suben":[],
                "promedio":{r["Equipo"]:float(r["Promedio"]) for _,r in descenso.iterrows()}}

FORMATOS[Colombia.nombre]=Colombia()
