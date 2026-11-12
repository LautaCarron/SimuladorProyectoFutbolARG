"""LigaPro Serie A de Ecuador (formato 2026): primera etapa y tres grupos finales con los puntos arrastrados.

  * Primera etapa: los 16 clubes, todos contra todos a doble rueda (30 fechas).
  * Fase final (los puntos y los goles de la primera etapa se arrastran completos; cada club suma 10 o 6 partidos más):
      - Hexagonal por el título (1° a 6°): todos contra todos a ida y vuelta (10 fechas). El 1° es el campeón.
      - Cuadrangular (7° a 10°): ida y vuelta (6 fechas) por el último cupo ecuatoriano a la Sudamericana.
      - Hexagonal del descenso (11° a 16°): ida y vuelta (10 fechas). Bajan los 2 últimos a la Serie B.
  * Cupos CONMEBOL: salen de la posición final (`orden` = hexagonal, cuadrangular y descenso, en ese orden) y se reparten
    con los cupos de `copas/conmebol.py`: 2 a grupos de la Libertadores, 1 a la Fase 2, 1 a la Fase 1 y 4 a la Sudamericana.
    Quien liderea la primera etapa ya no clasifica directo (cambio de 2026).

La Copa Ecuador no se simula: el cupo del campeón de la copa (Libertadores · Fase 1) lo toma el 4° del hexagonal, y el
cuarto cupo a la Sudamericana sigue por la tabla (subcampeón del cuadrangular). La Serie B es una reserva sin simular
(ver `datos/ligas_ext.py`). Sin Streamlit: motor puro (ver ligas/exterior.py).
"""

import datetime as dt

import numpy as np

from ligas.exterior import (FORMATOS, Formato, _cupos_de_pais, asignar_cupos, dias_semanales, espejo, ronda, rueda,
                            stats_vacias, tabla)
from motor.fechas import desde

PASO_FINAL = 9          # días entre fechas de la fase final (20/9 al 13/12 en 2026: 10 fechas)
GRUPOS = ("Hexagonal final", "Cuadrangular Sudamericana", "Hexagonal del descenso")


class Ecuador(Formato):
    """Primera etapa de 30 fechas y fase final en tres grupos (título, Sudamericana y descenso) con puntos arrastrados."""
    nombre = "ecuador"
    descripcion = ("Primera etapa (30 fechas) y fase final con los puntos arrastrados: hexagonal por el título, "
                   "cuadrangular por la Sudamericana y hexagonal del descenso.")
    etapas_definicion = ()

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        ida = rueda(rng, range(n))
        fechas = ida + espejo(ida)
        dias = dias_semanales(anio, cfg["calendario"]["Liga"], len(fechas))
        rondas = []
        for k, f in enumerate(fechas):
            R = ronda("Primera etapa", f"Primera etapa · fecha {k + 1}", "Primera etapa", dias[k], pares=f, suma="Etapa1")
            R["suma_extra"] = "Total"                  # lo que se arrastra a la fase final
            rondas.append(R)
        return {"formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
                "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
                "E": {"Etapa1": stats_vacias(n), "Total": stats_vacias(n)}, "campeon": None, "subcampeon": None,
                "descensos": int(cfg.get("descensos", 0)), "ascensos": int(cfg.get("ascensos", 0)),
                "divisional": int(cfg.get("divisional", 1)), "anio": int(anio), "n_etapa1": len(fechas),
                "cal_final": list(cfg["calendario"]["Fase final"]),
                "n_titulo": int(cfg.get("grupo_titulo", 6)), "n_sud": int(cfg.get("grupo_sudamericana", 4)),
                "grupos": None, "via": "", "paso": PASO_FINAL, "suben": [],
                "nombres_grupos": list(GRUPOS), "tam_grupos": [int(cfg.get("grupo_titulo", 6)), int(cfg.get("grupo_sudamericana", 4)), None]}

    # ------------------------------------------------------------------ armado de la fase final
    def _armar_final(self, L, rng):
        """Cuando termina la primera etapa: parte la tabla en los tres grupos y suma las 10 fechas de la fase final.
        Cada fecha juega los tres grupos a la vez (el cuadrangular termina antes: tiene 6 fechas)."""
        ids = [int(i) for i in tabla(L, L["E"]["Etapa1"])["id"]]
        grupos, ini = [], 0
        for t in L["tam_grupos"]:                      # el último grupo (tamaño None) se lleva a los que quedan
            fin = len(ids) if t is None else min(ini + int(t), len(ids))
            grupos.append(ids[ini:fin])
            ini = fin
        L["grupos"] = grupos
        calendario = []                                # por grupo: lista de fechas (cada una, lista de cruces)
        for g in grupos:
            if len(g) < 2:
                calendario.append([])
                continue
            ida = rueda(rng, g)
            calendario.append(ida + espejo(ida))
        cantidad = max(len(c) for c in calendario)
        ultimo = L["rondas"][L["n_etapa1"] - 1]["dia"]
        dia0 = max(desde(L["anio"], *L["cal_final"]), ultimo + dt.timedelta(days=7))
        paso = L["paso"] if dia0 + dt.timedelta(days=L["paso"] * (cantidad - 1)) <= dt.date(L["anio"], 12, 20) else L["paso"] - 1
        for j in range(cantidad):
            pares, grupo_de = [], {}
            for g, nombre in zip(calendario, L["nombres_grupos"]):
                if j < len(g):
                    pares += g[j]
                    grupo_de.update({a: nombre for a, _ in g[j]})
            R = ronda("Fase final", f"Fase final · fecha {j + 1}", "Fase final", dia0 + dt.timedelta(days=paso * j),
                      pares=pares, suma="Total")
            R["grupo_de"] = grupo_de
            L["rondas"].append(R)

    def avanzar(self, L, rng):
        if L["grupos"] is None and L["fecha"] >= L["n_etapa1"]:
            self._armar_final(L, rng)
        if L["campeon"] is None and L["grupos"] is not None and L["fecha"] >= len(L["rondas"]):
            hexa = tabla(L, L["E"]["Total"], L["grupos"][0])
            L["campeon"] = hexa.iloc[0]["Equipo"]
            L["subcampeon"] = hexa.iloc[1]["Equipo"] if len(hexa) > 1 else None
            L["via"] = (f"Campeón del hexagonal final (con los puntos de la primera etapa): {L['campeon']}.")

    # ------------------------------------------------------------------ tablas y cierre
    def _tabla_grupo(self, L, i):
        return tabla(L, L["E"]["Total"], L["grupos"][i])

    def _orden_final(self, L):
        """Posición final de los 16: hexagonal, cuadrangular y descenso, cada uno por su tabla. Antes de la fase final,
        la tabla de la primera etapa."""
        if L["grupos"] is None:
            return list(tabla(L, L["E"]["Etapa1"])["Equipo"])
        return [n for i in range(len(L["grupos"])) for n in self._tabla_grupo(L, i)["Equipo"]]

    def tablas(self, L):
        d = int(L.get("descensos", 0))
        cupos = L.get("cupos") or _cupos_de_pais(L.get("pais", ""))
        hecho = L["campeon"] is not None
        out = []
        t1 = tabla(L, L["E"]["Etapa1"])
        k, q = int(L["n_titulo"]), int(L["n_sud"])
        if L["grupos"] is None:                                    # la etapa sigue: destino por la posición de hoy
            t1["Destino"] = ["Clasifica al hexagonal final" if p <= k else "Clasifica al cuadrangular" if p <= k + q
                             else "Hexagonal del descenso" for p in t1["Pos"]]
            nota = ("Los 6 primeros juegan el hexagonal por el título, del 7° al 10° el cuadrangular y los 6 últimos el "
                    "hexagonal del descenso. Los puntos y los goles se arrastran. Destinos provisorios.")
        else:
            t1["Destino"] = ["Hexagonal final" if p <= k else "Cuadrangular" if p <= k + q else "Hexagonal del descenso"
                             for p in t1["Pos"]]
            nota = "Primera etapa terminada: los puntos y los goles pasan a la fase final."
        out.append({"titulo": "Primera etapa", "df": t1, "tipo": "liga", "nota": nota})
        if L["grupos"] is None:
            for g in GRUPOS:
                out.append({"titulo": g, "df": None, "tipo": "liga", "nota": "Se arma cuando termina la primera etapa (30 fechas)."})
            return out
        orden = self._orden_final(L)
        mapa = asignar_cupos(orden, cupos, L.get("camp_int")) if cupos else {}
        h = self._tabla_grupo(L, 0)
        h["Destino"] = [(("Campeón" if hecho else "Líder") if p == 1 else "") +
                        (" · " if p == 1 and mapa.get(e) else "") + mapa.get(e, "") for p, e in zip(h["Pos"], h["Equipo"])]
        try:
            from copas.conmebol import NOTA_COPA
            extra = NOTA_COPA.get(L.get("pais", ""), "")
        except ImportError:
            extra = ""
        out.append({"titulo": GRUPOS[0], "df": h, "tipo": "liga",
                    "nota": ("10 fechas a ida y vuelta con los puntos de la primera etapa. El 1° es el campeón. "
                             + ("" if hecho else "Destinos provisorios. ") + extra).strip()})
        s = self._tabla_grupo(L, 1)
        s["Destino"] = [mapa.get(e, "") for e in s["Equipo"]]
        out.append({"titulo": GRUPOS[1], "df": s, "tipo": "liga",
                    "nota": "6 fechas a ida y vuelta por el último cupo a la Sudamericana (el 2° también entra si el 4° del "
                            "hexagonal toma el cupo de la Copa Ecuador, que no se simula)."})
        b = self._tabla_grupo(L, 2)
        b["Destino"] = ["Desciende" if d and p > len(b) - d else "" for p in b["Pos"]]
        out.append({"titulo": GRUPOS[2], "df": b, "tipo": "liga",
                    "nota": f"10 fechas a ida y vuelta con los puntos de la primera etapa. Bajan a la Serie B los {d} últimos."})
        return out

    def cierre(self, L):
        d = int(L.get("descensos", 0))
        orden = self._orden_final(L)
        total = L["E"]["Total"]
        return {"campeon": L["campeon"], "orden": orden,
                "puntos": {n: (int(3 * total["g"][i] + total["e"][i]), int(total["pj"][i])) for i, n in enumerate(L["nombres"])},
                "descienden": orden[len(orden) - d:] if d else [], "suben": []}


class EcuadorSegunda(Ecuador):
    """LigaPro Serie B (formato 2026): 12 clubes, 22 fechas a doble rueda y dos hexagonales con los puntos arrastrados.
      * Hexagonal por el ascenso (1° a 6°, 10 fechas): el 1° es el campeón y suben los 2 primeros.
      * Hexagonal de permanencia (7° a 12°, 10 fechas).
    Los filiales (`filiales` del JSON: Independiente Juniors y San Antonio) no pueden ascender: si terminan en un puesto
    de ascenso sube el siguiente mejor. Bajan los 2 últimos del hexagonal de permanencia a la Segunda Categoría."""
    nombre = "ecuador_segunda"
    descripcion = ("Etapa regular de 22 fechas y dos hexagonales con los puntos arrastrados: ascenso (suben 2; los "
                   "filiales no pueden subir) y permanencia.")

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        L = super().nueva(cfg, nombres, r, previo, anio, rng)
        L.update(nombres_grupos=["Hexagonal por el ascenso", "Hexagonal de permanencia"], tam_grupos=[6, None],
                 paso=7, filiales=list(cfg.get("filiales", [])))
        return L

    def _suben(self, L):
        """Los que ascienden: los primeros del hexagonal por el ascenso que no son filiales."""
        asc = self._tabla_grupo(L, 0)["Equipo"]
        return [e for e in asc if e not in set(L.get("filiales", []))][:int(L.get("ascensos", 2))]

    def avanzar(self, L, rng):
        super().avanzar(L, rng)
        if L["campeon"] is not None and not L["suben"]:
            L["suben"] = self._suben(L)
            L["via"] = (f"Campeón de la Serie B: {L['campeon']}. Ascienden {' y '.join(L['suben'])}"
                        + (" (los filiales no pueden ascender)." if any(e in L["filiales"] for e in
                                                                           self._tabla_grupo(L, 0)["Equipo"][:L["ascensos"]]) else "."))

    def tablas(self, L):
        k = int(L["tam_grupos"][0])
        hecho = L["campeon"] is not None
        t1 = tabla(L, L["E"]["Etapa1"])
        if L["grupos"] is None:
            t1["Destino"] = ["Clasifica al hexagonal por el ascenso" if p <= k else "Hexagonal de permanencia" for p in t1["Pos"]]
            nota = ("Los 6 primeros juegan el hexagonal por el ascenso y los otros 6 el de permanencia. Los puntos y los goles "
                    "se arrastran. Destinos provisorios.")
        else:
            t1["Destino"] = ["Hexagonal por el ascenso" if p <= k else "Hexagonal de permanencia" for p in t1["Pos"]]
            nota = "Etapa regular terminada: los puntos y los goles pasan a los hexagonales."
        out = [{"titulo": "Etapa regular", "df": t1, "tipo": "liga", "nota": nota}]
        if L["grupos"] is None:
            for g in L["nombres_grupos"]:
                out.append({"titulo": g, "df": None, "tipo": "liga", "nota": "Se arma cuando termina la etapa regular (22 fechas)."})
            return out
        suben = L["suben"] if hecho else self._suben(L)
        a = self._tabla_grupo(L, 0)
        a["Destino"] = [(("Campeón" if hecho else "Líder") if p == 1 else "")
                        + (" · " if p == 1 and e in suben else "") + ("Asciende" if e in suben else "")
                        for p, e in zip(a["Pos"], a["Equipo"])]
        out.append({"titulo": L["nombres_grupos"][0], "df": a, "tipo": "liga",
                    "nota": "10 fechas a ida y vuelta con los puntos de la etapa regular. El 1° es el campeón y suben los 2 "
                            "primeros que no sean filiales." + ("" if hecho else " Destinos provisorios.")})
        perm = self._tabla_grupo(L, 1)
        d = int(L.get("descensos", 0))
        perm["Destino"] = ["Desciende" if d and p > len(perm) - d else "" for p in perm["Pos"]]
        out.append({"titulo": L["nombres_grupos"][1], "df": perm, "tipo": "liga",
                    "nota": f"10 fechas a ida y vuelta con los puntos de la etapa regular. Bajan a la Segunda Categoría los {d} últimos."})
        return out

    def cierre(self, L):
        orden = self._orden_final(L)
        total = L["E"]["Total"]
        return {"campeon": L["campeon"], "orden": orden,
                "puntos": {n: (int(3 * total["g"][i] + total["e"][i]), int(total["pj"][i])) for i, n in enumerate(L["nombres"])},
                "descienden": orden[len(orden) - int(L.get("descensos", 0)):] if L.get("descensos") else [],
                "suben": list(L["suben"]) or self._suben(L)}


class EcuadorTercera(Formato):
    """Segunda Categoría (Ascenso Nacional 2026): 48 clubes que llegan de los torneos provinciales (no se simulan).
      * Primera fase: 8 grupos de 6, ida y vuelta (10 fechas). Pasan los 2 primeros de cada grupo (16).
      * Cuadrangulares: 4 grupos de 4, ida y vuelta (6 fechas). Pasa el 1° de cada uno.
      * Cuadrangular final: los 4 ganadores, ida y vuelta (6 fechas). El 1° es el campeón y suben los 2 primeros a la Serie B.
    Cada fase empieza de cero (no se arrastran puntos). Los grupos de la primera temporada son los del sorteo real de 2026
    (`grupos` del JSON); después se sortean. El sorteo de los cuadrangulares es fijo y evita que se crucen clubes del
    mismo grupo (1° de A, 2° de B, 1° de C y 2° de D, etcétera): el real depende de la geografía."""
    nombre = "ecuador_tercera"
    descripcion = ("Ascenso Nacional: 8 grupos de 6, cuadrangulares semifinales y cuadrangular final; suben los 2 primeros "
                   "del cuadrangular final.")
    etapas_definicion = ()
    LETRAS = "ABCDEFGH"
    PASOS = (7, 7, 4)                                   # días entre fechas de cada fase (la final termina a mediados de diciembre)

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        indice = {x: i for i, x in enumerate(nombres)}
        reales = [[indice[c] for c in g] for g in cfg.get("grupos", []) if all(c in indice for c in g)]
        if len(reales) == len(cfg.get("grupos", [])) and sorted(i for g in reales for i in g) == list(range(n)) and reales:
            grupos = reales
        else:                                           # sorteo al azar en grupos de 6 (o lo más parejo posible)
            ids = [int(i) for i in rng.permutation(n)]
            k = max(1, n // 6)
            grupos = [ids[j::k] for j in range(k)]
        calendarios = []
        for g in grupos:
            ida = rueda(rng, g)
            calendarios.append(ida + espejo(ida))
        dias = dias_semanales(anio, cfg["calendario"]["Zonal"], max(len(c) for c in calendarios))
        rondas = []
        for j in range(len(dias)):
            pares, grupo_de = [], {}
            for k, c in enumerate(calendarios):
                if j < len(c):
                    pares += c[j]
                    grupo_de.update({a: f"Grupo {self.LETRAS[k]}" for a, _ in c[j]})
            R = ronda("Primera fase", f"Primera fase · fecha {j + 1}", "Primera fase", dias[j], pares=pares, suma="Zonal")
            R["grupo_de"] = grupo_de
            rondas.append(R)
        return {"formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
                "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
                "E": {"Zonal": stats_vacias(n), "Semifinal": stats_vacias(n), "Final": stats_vacias(n)},
                "campeon": None, "subcampeon": None, "descensos": int(cfg.get("descensos", 0)),
                "ascensos": int(cfg.get("ascensos", 0)), "divisional": int(cfg.get("divisional", 3)), "anio": int(anio),
                "cal": {k: list(v) for k, v in cfg["calendario"].items()}, "n_zonal": len(dias), "grupos": grupos,
                "semis": None, "finalistas": None, "suben": [], "via": ""}

    # ------------------------------------------------------------------ fases
    def _fase(self, L, rng, grupos, etapa, nombre, suma, paso, clave_cal, grupo_nombre):
        """Suma las rondas de una fase en la que juegan varios grupos a la vez (ida y vuelta)."""
        calendarios = []
        for g in grupos:
            ida = rueda(rng, g)
            calendarios.append(ida + espejo(ida))
        ultimo = L["rondas"][-1]["dia"]
        dia0 = max(desde(L["anio"], *L["cal"][clave_cal]), ultimo + dt.timedelta(days=7))
        for j in range(max(len(c) for c in calendarios)):
            pares, grupo_de = [], {}
            for k, c in enumerate(calendarios):
                if j < len(c):
                    pares += c[j]
                    grupo_de.update({a: grupo_nombre(k) for a, _ in c[j]})
            R = ronda(etapa, f"{nombre} · fecha {j + 1}", etapa, dia0 + dt.timedelta(days=paso * j), pares=pares, suma=suma)
            R["grupo_de"] = grupo_de
            L["rondas"].append(R)

    def _tabla_zonal(self, L, k):
        return tabla(L, L["E"]["Zonal"], L["grupos"][k])

    def avanzar(self, L, rng):
        if L["semis"] is None and L["fecha"] >= L["n_zonal"]:
            top = [[int(i) for i in self._tabla_zonal(L, k)["id"][:2]] for k in range(len(L["grupos"]))]
            mitades = []                                        # por cada par de grupos (A, B): [1°A, 2°B] y [1°B, 2°A]
            for b in range(0, len(top) - 1, 2):
                mitades += [[top[b][0], top[b + 1][1]], [top[b + 1][0], top[b][1]]]
            L["semis"] = []                                     # cada cuadrangular junta mitades de dos pares de grupos
            for b in range(0, len(mitades) - 3, 4):
                L["semis"] += [mitades[b] + mitades[b + 2], mitades[b + 1] + mitades[b + 3]]
            self._fase(L, rng, L["semis"], "Cuadrangulares", "Cuadrangulares semifinales", "Semifinal", self.PASOS[1],
                       "Semifinal", lambda k: f"Cuadrangular {k + 1}")
        elif L["finalistas"] is None and L["semis"] is not None and L["fecha"] >= L["n_zonal"] + 6:
            L["finalistas"] = [int(tabla(L, L["E"]["Semifinal"], g)["id"].iloc[0]) for g in L["semis"]]
            paso = self.PASOS[2]
            self._fase(L, rng, [L["finalistas"]], "Cuadrangular final", "Cuadrangular final", "Final", paso, "Final",
                       lambda k: "Cuadrangular final")
        if L["campeon"] is None and L["finalistas"] is not None and L["fecha"] >= len(L["rondas"]):
            t = tabla(L, L["E"]["Final"], L["finalistas"])
            L["campeon"] = t.iloc[0]["Equipo"]
            L["subcampeon"] = t.iloc[1]["Equipo"]
            L["suben"] = list(t["Equipo"][:int(L["ascensos"])])
            L["via"] = f"Campeón de la Segunda Categoría: {L['campeon']}. Ascienden {' y '.join(L['suben'])} a la Serie B."

    # ------------------------------------------------------------------ tablas y cierre
    def tablas(self, L):
        out = []
        for k in range(len(L["grupos"])):
            t = self._tabla_zonal(L, k)
            t["Destino"] = ["Clasifica" if p <= 2 else "" for p in t["Pos"]]
            out.append({"titulo": f"Grupo {self.LETRAS[k]}", "df": t, "tipo": "liga", "agrupa": "Primera fase",
                        "nota": "Pasan los 2 primeros de cada grupo."})
        if L["semis"] is None:
            out.append({"titulo": "Cuadrangulares", "df": None, "tipo": "liga",
                        "nota": "Se arman cuando termina la primera fase (10 fechas): los 16 clasificados juegan 4 cuadrangulares."})
        else:
            for k, g in enumerate(L["semis"]):
                t = tabla(L, L["E"]["Semifinal"], g)
                t["Destino"] = ["Clasifica a la final" if p == 1 else "" for p in t["Pos"]]
                out.append({"titulo": f"Cuadrangular {k + 1}", "df": t, "tipo": "liga", "agrupa": "Cuadrangulares",
                            "nota": "Pasa el 1° de cada cuadrangular."})
        if L["finalistas"] is None:
            out.append({"titulo": "Cuadrangular final", "df": None, "tipo": "liga",
                        "nota": "Se arma con los 4 ganadores de los cuadrangulares. Suben los 2 primeros a la Serie B."})
        else:
            hecho = L["campeon"] is not None
            t = tabla(L, L["E"]["Final"], L["finalistas"])
            ya = len(L["rondas"]) <= L["fecha"]
            t["Destino"] = [("Campeón · Asciende" if hecho else "Líder · Asciende") if p == 1 else
                            ("Asciende" if p <= int(L["ascensos"]) else "") for p in t["Pos"]]
            out.append({"titulo": "Cuadrangular final", "df": t, "tipo": "liga",
                        "nota": "6 fechas a ida y vuelta. El 1° es el campeón y suben los 2 primeros a la Serie B."
                                + ("" if ya else " Destinos provisorios.")})
        return out

    def _orden_final(self, L):
        """Posición final: el cuadrangular final, el resto de los semifinalistas (por su tabla de cuadrangulares) y el
        resto (por su tabla de la primera fase)."""
        fin = list(tabla(L, L["E"]["Final"], L["finalistas"])["Equipo"])
        semis = [i for g in L["semis"] for i in g if i not in set(L["finalistas"])]
        resto = [i for i in range(len(L["nombres"])) if i not in set(semis) | set(L["finalistas"])]
        return (fin + list(tabla(L, L["E"]["Semifinal"], semis)["Equipo"]) + list(tabla(L, L["E"]["Zonal"], resto)["Equipo"]))

    def cierre(self, L):
        orden = self._orden_final(L)
        puntos = {}
        for i, n in enumerate(L["nombres"]):
            e = L["E"]
            puntos[n] = (int(sum(3 * e[k]["g"][i] + e[k]["e"][i] for k in e)), int(sum(e[k]["pj"][i] for k in e)))
        return {"campeon": L["campeon"], "orden": orden, "puntos": puntos, "descienden": [], "suben": list(L["suben"])}


FORMATOS[Ecuador.nombre] = Ecuador()
FORMATOS[EcuadorSegunda.nombre] = EcuadorSegunda()
FORMATOS[EcuadorTercera.nombre] = EcuadorTercera()
