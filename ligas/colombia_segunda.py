"""Torneo BetPlay (Primera B): dos torneos semestrales con cuadrangulares y final.

La estructura reproduce el esquema DIMAYOR 2026: 16 clubes, 15 fechas todos contra todos,
cuadrangulares semifinales de seis fechas y final ida/vuelta en cada semestre. La reclasificación
acumula los partidos de ambas fases regulares y cuadrangulares. El ascenso sigue los escenarios
reglamentarios de campeones semestrales, Gran Final y repechaje.
"""
import datetime as dt
import numpy as np
import pandas as pd
from ligas.exterior import (FORMATOS, Formato, UNA_SEMANA, dias_semanales, espejo, partidos_de_ronda,
                            ronda, rueda, stats_vacias, sumar_stats, tabla)
from motor.fechas import desde
from motor.nucleo import tanda_penales

TORNEOS = ("Apertura", "Clausura")

class ColombiaSegunda(Formato):
    nombre = "colombia_segunda"
    descripcion = ("Apertura y Clausura: 15 fechas, cuadrangulares semifinales de seis fechas y final ida/vuelta. "
                   "Ascensos por campeones semestrales, reclasificación, Gran Final y repechaje.")
    etapas_definicion = ("Apertura · final", "Clausura · final", "Gran Final", "Repechaje")

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres); rondas=[]
        for torneo in TORNEOS:
            ida = rueda(rng, range(n))
            dias = dias_semanales(anio, cfg["calendario"][torneo], len(ida))
            rondas += [ronda(torneo, f"{torneo} · fecha {k+1}", torneo, dias[k], pares=f, suma=torneo)
                       for k,f in enumerate(ida)]
        return {"formato":self.nombre,"clave":cfg["clave"],"nombre":cfg["nombre"],"pais":cfg["pais"],
                "nombres":list(nombres),"r":np.array(r,dtype=float),"rondas":rondas,"fecha":0,"log":[],
                "E":{**{t:stats_vacias(n) for t in TORNEOS},"Reclasificacion":stats_vacias(n)},"descensos":int(cfg.get("descensos",0)),
                "ascensos":int(cfg.get("ascensos",2)),"grupos":{},"ganadores":{},"hecho":{},
                "suben":[],"campeon":None,"subcampeon":None,"via":"","promocion":None,
                "clasificados_apertura":[]}

    def _idx(self,L,etapa): return [i for i,x in enumerate(L["rondas"]) if x["etapa"]==etapa]
    def _finish(self,L,etapa):
        ix=self._idx(L,etapa); return bool(ix) and ix[-1] < L["fecha"]
    def _add(self,L,etapa,rotulo,comp,pares,dia,ko=False,neutral=False,ida_vuelta=None,suma=None):
        R=ronda(etapa,rotulo,comp,dia,pares=pares,suma=suma,ko=ko,neutral=neutral,ida_vuelta=ida_vuelta)
        if comp.startswith("Apertura") or comp.startswith("Clausura"):
            R["suma_extra"] = "Reclasificacion"
            prev=[i for i,x in enumerate(L["rondas"]) if x["comp"].startswith(comp.split(" · ")[0])]
            pos=prev[-1]+1 if prev else len(L["rondas"])
            L["rondas"].insert(pos,R)
        else:
            L["rondas"].append(R)
    def _schedule_series(self,L,etapa,comp,a,b,day):
        self._add(L,etapa,f"{comp} · ida",comp,[(a,b)],day,ida_vuelta="ida")
        self._add(L,etapa,f"{comp} · vuelta",comp,[(b,a)],day+UNA_SEMANA,ida_vuelta="vuelta")
    def _winner(self,L,etapa,rng):
        ix=self._idx(L,etapa); p1=partidos_de_ronda(L,ix[0]+1)[0]; p2=partidos_de_ronda(L,ix[1]+1)[0]
        a,b=L["nombres"].index(p1["local"]),L["nombres"].index(p1["visita"])
        ga,gb=p1["gl"]+p2["gv"],p1["gv"]+p2["gl"]
        if ga==gb:
            pa=float(np.clip(.5+(L["r"][a]-L["r"][b])/400,.35,.65)); w=a if rng.random()<pa else b
            p2["tanda"] = tanda_penales(rng, w == L["nombres"].index(p2["local"]))
            p2["pen"] = (sum(p2["tanda"][0]), sum(p2["tanda"][1]))
            p2["gana"] = L["nombres"][w]
            return w
        return a if ga>gb else b
    def _tabla_anual(self,L): return tabla(L,L["E"]["Reclasificacion"])
    def _armar_cuadrangulares(self,L,t,day,rng):
        df=tabla(L,L["E"][t]); ids=[int(i) for i in df["id"][:8]]
        grupos=[[ids[i] for i in (0,3,4,7)],[ids[i] for i in (1,2,5,6)]]
        L["grupos"][t]=grupos
        if t == "Apertura": L["clasificados_apertura"] = list(ids)
        fxs=[rueda(rng,g) for g in grupos]
        fxs=[fx+espejo(fx) for fx in fxs]
        for k in range(6):
            self._add(L,f"{t} · cuadrangulares",f"{t} · cuadrangulares · fecha {k+1}",
                      f"{t} · cuadrangulares",fxs[0][k]+fxs[1][k],day+k*UNA_SEMANA,suma=t)
        L["hecho"][f"{t} · grupos"]="pendiente"
    def _paso_torneo(self,L,t,rng):
        if t in L["ganadores"]: return False
        if not L["hecho"].get(f"{t} · grupos"):
            if not self._finish(L,t): return False
            last=L["rondas"][self._idx(L,t)[-1]]["dia"]
            self._armar_cuadrangulares(L,t,last+dt.timedelta(days=4),rng); return True
        if L["hecho"].get(f"{t} · grupos")=="pendiente":
            if not self._finish(L,f"{t} · cuadrangulares"): return False
            winners=[int(tabla(L,L["E"][t],g).iloc[0]["id"]) for g in L["grupos"][t]]
            self._schedule_series(L,f"{t} · final",f"{t} · final",winners[0],winners[1],L["rondas"][-1]["dia"]+dt.timedelta(days=4))
            L["hecho"][f"{t} · grupos"]="listo"; L["hecho"][f"{t} · final"]="pendiente"; return True
        if L["hecho"].get(f"{t} · final")=="pendiente" and self._finish(L,f"{t} · final"):
            L["ganadores"][t]=self._winner(L,f"{t} · final",rng)
            L["hecho"][f"{t} · final"]="listo"; return True
        return False
    def _armar_ascensos(self,L,rng):
        """Aplica escenarios de ascenso 2026: dos campeones, reclasificación, Gran Final y repechaje."""
        if L.get("promocion") is not None: return False
        nom=L["nombres"]; anual=[int(i) for i in self._tabla_anual(L)["id"]]
        a,b=L["ganadores"]["Apertura"],L["ganadores"]["Clausura"]
        if a==b:
            L["suben"]=[nom[a]]
            rivales=[i for i in anual if i!=a][:2]
            if len(rivales)>=2:
                self._schedule_series(L,"Repechaje","Repechaje por el ascenso",rivales[0],rivales[1],L["rondas"][-1]["dia"]+dt.timedelta(days=7))
                L["promocion"]={"tipo":"repechaje","espera":"Repechaje","directo":[a]}
            else: L["promocion"]={"tipo":"resuelto","directo":[a]}
            L["campeon"]=nom[a]; L["via"]="Ganó ambos torneos semestrales; asciende automáticamente. El segundo ascenso se define por repechaje."
            return True
        top2=set(anual[:2]); champs={a,b}
        if champs.issubset(top2):
            L["suben"]=[nom[a],nom[b]]; L["campeon"]=nom[b]
            L["promocion"]={"tipo":"resuelto","directo":[a,b]}
            L["via"]="Los dos campeones semestrales ocuparon los dos primeros puestos de la reclasificación; ambos ascienden."
            return True
        if champs & top2:
            directo=next(iter(champs & top2)); otro=b if directo==a else a
            rival=next((i for i in anual if i not in champs),None)
            L["suben"]=[nom[directo]]
            if rival is not None:
                self._schedule_series(L,"Repechaje","Repechaje por el ascenso",otro,rival,L["rondas"][-1]["dia"]+dt.timedelta(days=7))
                L["promocion"]={"tipo":"repechaje","espera":"Repechaje","directo":[directo]}
            else: L["promocion"]={"tipo":"resuelto","directo":[directo]}
            L["campeon"]=nom[directo]; L["via"]="Un campeón quedó entre los dos primeros de la reclasificación; el otro disputa el repechaje."
            return True
        self._schedule_series(L,"Gran Final","Gran Final del Torneo BetPlay",a,b,L["rondas"][-1]["dia"]+dt.timedelta(days=7))
        L["promocion"]={"tipo":"gran_final","espera":"Gran Final"}
        return True
    def avanzar(self,L,rng):
        for _ in range(12):
            cambio=False
            for t in TORNEOS:
                if self._paso_torneo(L,t,rng): cambio=True; break
            if cambio: continue
            if all(t in L["ganadores"] for t in TORNEOS) and L.get("promocion") is None:
                self._armar_ascensos(L,rng); continue
            P=L.get("promocion") or {}
            if P.get("tipo")=="gran_final" and self._finish(L,"Gran Final"):
                ganador=self._winner(L,"Gran Final",rng); perdedor=L["ganadores"]["Clausura"] if ganador==L["ganadores"]["Apertura"] else L["ganadores"]["Apertura"]
                anual=[int(i) for i in self._tabla_anual(L)["id"]]
                rival=next((i for i in anual if i not in (ganador,perdedor)),None)
                L["suben"]=[L["nombres"][ganador]]; L["campeon"]=L["nombres"][ganador]
                L["via"]="Ganador de la Gran Final; el perdedor disputa el repechaje por el segundo ascenso."
                if rival is not None:
                    self._schedule_series(L,"Repechaje","Repechaje por el ascenso",perdedor,rival,L["rondas"][-1]["dia"]+dt.timedelta(days=7))
                    L["promocion"]={"tipo":"repechaje","espera":"Repechaje","directo":[ganador]}
                else: L["promocion"]={"tipo":"resuelto","directo":[ganador]}
                continue
            if P.get("tipo")=="repechaje" and self._finish(L,"Repechaje"):
                w=self._winner(L,"Repechaje",rng); L["suben"]=[L["nombres"][i] for i in P.get("directo",[])]
                if L["nombres"][w] not in L["suben"]: L["suben"].append(L["nombres"][w])
                P["tipo"]="resuelto"; L["via"] += f" Ascenso por repechaje: {L['nombres'][w]}."; continue
            if P.get("tipo")=="resuelto" and L["fecha"]>=len(L["rondas"]):
                if L["campeon"] is None:
                    L["campeon"]=L["nombres"][L["ganadores"]["Clausura"]]
                return
            return
    def tablas(self,L):
        out=[]
        for t in TORNEOS:
            df=tabla(L,L["E"][t]); grupos=L["grupos"].get(t)
            df["Destino"]=["Cuadrangulares" if p<=8 else "" for p in df["Pos"]]
            out.append({"titulo":t,"df":df,"tipo":"liga","nota":"15 fechas; los ocho primeros avanzan a cuadrangulares semifinales."})
            if grupos:
                for label,ids in zip(("A","B"),grupos):
                    grupo_df = tabla(L,L["E"][t],ids)
                    grupo_df["Destino"] = ["A la final" if pos == 1 else "" for pos in grupo_df["Pos"]]
                    out.append({"titulo":f"{t} · Grupo {label}","df":grupo_df,"tipo":"liga",
                                "nota":"El ganador clasifica a la final semestral."})
        anual=self._tabla_anual(L)
        anual["Destino"]=["Asciende" if eq in L.get("suben",[]) else "Reclasificación" if pos<=4 else ""
                          for pos,eq in zip(anual["Pos"],anual["Equipo"])]
        out.append({"titulo":"Reclasificación total","df":anual,"tipo":"liga",
                    "nota":"Suma Apertura y Clausura, incluidas las fases de cuadrangulares. Define los escenarios de ascenso."})
        return out
    def cierre(self,L):
        anual=self._tabla_anual(L); orden=list(anual["Equipo"]); d=int(L.get("descensos",0))
        return {"campeon":L.get("campeon") or (L["nombres"][L["ganadores"]["Clausura"]] if "Clausura" in L["ganadores"] else orden[0]),
                "orden":orden,"puntos":{x["Equipo"]:(int(x["Pts"]),int(x["PJ"])) for _,x in anual.iterrows()},
                "descienden":orden[len(orden)-d:] if d else [],"suben":list(L.get("suben",[])) or orden[:int(L.get("ascensos",2))]}

FORMATOS[ColombiaSegunda.nombre]=ColombiaSegunda()
