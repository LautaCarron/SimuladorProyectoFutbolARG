"""Segunda División Profesional de Uruguay (14 clubes): formato vigente en 2026.

Dos etapas que se suman en una Tabla Anual:
  * Torneo Competencia: dos series de 7 clubes, una rueda cada una (7 fechas; en una serie de 7 siempre descansa
    alguien) y final a partido único entre los ganadores de serie. El campeón de la Competencia tiene asegurado un lugar
    en el playoff por el tercer ascenso. Sus puntos cuentan para la Tabla Anual; la final no.
  * Fase regular: todos contra todos a doble rueda (26 fechas). Sus puntos se suman a los de la Competencia.
  * Tabla Anual = Competencia + Fase regular. El campeón de la Segunda División es el primero de la Tabla Anual.

Ascensos (3 en total, los mismos que bajan de la Liga AUF Uruguaya):
  * Suben directo los dos primeros de la Tabla Anual.
  * Los clubes ubicados del 3° al 6° juegan el playoff por el tercer ascenso (semifinales 3° vs 6° y 4° vs 5°, y final).
    Si el campeón de la Competencia quedó afuera de esos puestos, ocupa el lugar del 6°.

Descenso: en 2026 el reglamento real anuló los descensos directos a la Primera Divisional C (hay un repechaje con
clubes de la C que acá no se simula). Acá la tercera división es una lista de clubes que NO se juega ("tercera" en
datos/json/liga_uruguay.json): bajan los últimos de la Tabla Anual (`descensos`, hoy 2) y suben, al azar, la misma
cantidad de clubes de esa lista, así que la Segunda sigue con 14.

Simplificaciones (a revisar contra el reglamento de la AUF; ver docs/LIGAS_EXTERIOR.md):
  * Las series de la Competencia se arman al azar (el sorteo real separa a los clubes del interior).
  * Semifinales del playoff a partido único en la cancha del mejor ubicado; la final, a partido único en cancha neutral.
    Todas con penales si empatan. El reglamento real puede prever otra instancia.
  * Si hay empate total en los puestos de ascenso, manda el orden de la tabla (puntos, diferencia de gol, goles a favor);
    no se juega ningún desempate extra.
"""

import datetime as dt

import numpy as np

from ligas.exterior import (FORMATOS, UNA_SEMANA, Formato, dias_semanales, espejo, partidos_de_ronda, ronda, rueda,
                            stats_vacias, sumar_stats, tabla)
from ligas.uruguay import _agregar, _completa, _ganador_de, _indices, _jugada, _ultimo_dia
from motor.fechas import desde

FINAL_COMPETENCIA = "Final de la Competencia"
PLAYOFF_SEMIS = "Playoff · semifinales"
PLAYOFF_FINAL = "Playoff · final"
TORNEOS = ("Competencia", "Regular")
DIRECTOS = 2                  # ascensos directos (los dos primeros de la Tabla Anual)
CUPOS_PLAYOFF = 4             # del 3° al 6° de la Tabla Anual


def _tabla_anual(L):
    return tabla(L, sumar_stats(*(L["E"][t] for t in TORNEOS)))


class UruguaySegunda(Formato):
    nombre = "uruguay_segunda"
    descripcion = ("Torneo Competencia (dos series de 7 y final) y fase regular a doble rueda; la Tabla Anual los suma. "
                   "Ascienden los dos primeros y el ganador del playoff entre el 3° y el 6°; descienden los últimos "
                   "de la Tabla Anual a la tercera división (que no se simula).")
    etapas_definicion = (FINAL_COMPETENCIA, PLAYOFF_SEMIS, PLAYOFF_FINAL)

    # ---- armado de la temporada ---------------------------------------------------------------------------
    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        cal = cfg["calendario"]
        orden = [int(i) for i in rng.permutation(n)]
        mitad = (n + 1) // 2
        A, B = sorted(orden[:mitad]), sorted(orden[mitad:])
        fa, fb = rueda(rng, A), rueda(rng, B)
        k_comp = max(len(fa), len(fb))
        grupo_de = {**{i: "Competencia · Serie A" for i in A}, **{i: "Competencia · Serie B" for i in B}}
        d_comp = dias_semanales(anio, cal["Competencia"], k_comp + 1)
        rondas = []
        for k in range(k_comp):
            R = ronda("Competencia", f"Competencia · fecha {k + 1}", "Competencia", d_comp[k],
                      pares=(fa[k] if k < len(fa) else []) + (fb[k] if k < len(fb) else []), suma="Competencia")
            R["grupo_de"] = grupo_de
            rondas.append(R)
        rondas.append(ronda(FINAL_COMPETENCIA, "Competencia · final", "Final de la Competencia", d_comp[k_comp],
                            ko=True, neutral=True))
        ida = rueda(rng, range(n))
        fechas = ida + espejo(ida)
        d_reg = dias_semanales(anio, cal["Regular"], len(fechas))
        rondas += [ronda("Regular", f"Fase regular · fecha {k + 1}", "Fase regular", d_reg[k], pares=f, suma="Regular")
                   for k, f in enumerate(fechas)]
        return {
            "formato": self.nombre, "clave": cfg["clave"], "nombre": cfg["nombre"], "pais": cfg["pais"],
            "nombres": list(nombres), "r": np.array(r, dtype=float),
            "rondas": rondas, "fecha": 0, "log": [],
            "E": {t: stats_vacias(n) for t in TORNEOS}, "descensos": int(cfg.get("descensos", 0)),
            "ascensos": int(cfg.get("ascensos", DIRECTOS + 1)),
            "definiciones": desde(anio, *cal["Definiciones"]),
            "grupos": [A, B], "finalistas_competencia": None,
            "ganadores": {"Competencia": None}, "hecho": {"Competencia": False, "Regular": False, "Playoff": False},
            "directos": [], "playoff": None, "campeon": None, "subcampeon": None, "suben": [], "via": "",
        }

    # ---- lo que viene después de cada ronda ---------------------------------------------------------------
    def avanzar(self, L, rng):
        for _ in range(12):                      # cada paso deja listo el siguiente; corta cuando hay que jugar
            if not self._paso(L):
                return

    def _paso(self, L):
        H, G = L["hecho"], L["ganadores"]
        if not H["Competencia"]:
            if not _completa(L, "Competencia"):
                return False
            fin = L["rondas"][_indices(L, FINAL_COMPETENCIA)[0]]
            if fin["pares"] is None:             # con las dos series terminadas se arma la final
                L["finalistas_competencia"] = [int(tabla(L, L["E"]["Competencia"], g).iloc[0]["id"])
                                               for g in L["grupos"]]
                fin["pares"] = [tuple(L["finalistas_competencia"])]
                return False
            if not _jugada(L, FINAL_COMPETENCIA):
                return False
            G["Competencia"] = _ganador_de(L, FINAL_COMPETENCIA)
            H["Competencia"] = True
            return True
        if not H["Regular"]:
            if not _completa(L, "Regular"):
                return False
            self._cerrar_regular(L)
            H["Regular"] = True
            return True
        if not H["Playoff"]:
            return self._playoff(L)
        return False

    def _cerrar_regular(self, L):
        """Con la Tabla Anual definida: campeón, ascensos directos y armado del playoff (3° al 6°)."""
        nom = L["nombres"]
        ids = [int(i) for i in _tabla_anual(L)["id"]]
        L["directos"] = ids[:DIRECTOS]
        L["campeon"], L["subcampeon"] = nom[ids[0]], nom[ids[1]]
        cupos = ids[DIRECTOS:DIRECTOS + CUPOS_PLAYOFF]
        gc = L["ganadores"]["Competencia"]
        if gc in ids[DIRECTOS + CUPOS_PLAYOFF:]:                 # el de la Competencia, afuera: ocupa el lugar del 6°
            cupos = cupos[:CUPOS_PLAYOFF - 1] + [gc]
        L["playoff"] = {"cupos": cupos, "finalistas": None, "ganador": None}
        dia = max(L["definiciones"], _ultimo_dia(L) + dt.timedelta(days=4))
        mitad = len(cupos) // 2                                    # 1° vs último y 2° vs anteúltimo (3°-6° y 4°-5°)
        cruces = [(cupos[i], cupos[len(cupos) - 1 - i]) for i in range(mitad)]
        _agregar(L, ronda(PLAYOFF_SEMIS, "Playoff · semifinales", "Playoff · semifinal", dia, pares=cruces, ko=True))
        _agregar(L, ronda(PLAYOFF_FINAL, "Playoff · final", "Playoff · final", dia + UNA_SEMANA, ko=True,
                          neutral=True))
        L["via"] = (f"Campeón: {L['campeon']}, primero de la Tabla Anual. Ascienden directo {nom[ids[0]]} y "
                    f"{nom[ids[1]]}; el tercer ascenso se define en el playoff.")

    def _playoff(self, L):
        """Semifinales y final del playoff por el tercer ascenso. True si se definió algo y hay que seguir mirando."""
        P, nom = L["playoff"], L["nombres"]
        i_sem, i_fin = _indices(L, PLAYOFF_SEMIS)[0], _indices(L, PLAYOFF_FINAL)[0]
        if L["rondas"][i_fin]["pares"] is None:
            if not _jugada(L, PLAYOFF_SEMIS):
                return False
            P["finalistas"] = [nom.index(p["gana"]) for p in partidos_de_ronda(L, i_sem + 1)]
            L["rondas"][i_fin]["pares"] = [tuple(P["finalistas"])]
            return False
        if not _jugada(L, PLAYOFF_FINAL):
            return False
        P["ganador"] = _ganador_de(L, PLAYOFF_FINAL)
        L["suben"] = [nom[i] for i in L["directos"]] + [nom[P["ganador"]]]
        L["hecho"]["Playoff"] = True
        return True

    # ---- tablas para la interfaz ---------------------------------------------------------------------------
    def tablas(self, L):
        out = []
        fin = L["finalistas_competencia"]
        for nombre, ids in zip(("A", "B"), L["grupos"]):
            df = tabla(L, L["E"]["Competencia"], ids)
            df["Destino"] = ["A la final" if (fin and i in fin) or (not fin and p == 1) else ""
                             for p, i in zip(df["Pos"], df["id"])]
            out.append({"titulo": f"Competencia · Serie {nombre}", "df": df, "tipo": "liga", "nota": ""})
        reg = tabla(L, L["E"]["Regular"])
        reg["Destino"] = [""] * len(reg)
        out.append({"titulo": "Fase regular", "df": reg, "tipo": "liga",
                    "nota": "Sólo los puntos de la fase regular. Para el ascenso cuenta la Tabla Anual."})
        anual = _tabla_anual(L)
        anual["Destino"] = self._destinos(L, anual)
        listo = L["hecho"]["Regular"]
        d = int(L.get("descensos", 0))
        nota = ("Competencia + Fase regular. Los dos primeros ascienden y el campeón es el primero. Del 3° al 6° juegan "
                "el playoff por el tercer ascenso (si el ganador de la Competencia quedó afuera, ocupa el lugar del 6°). "
                + ("" if listo else "Destinos provisorios por la posición de hoy. ")
                + (f"Los {d} últimos descienden a la tercera división, que no se simula: la misma cantidad de clubes "
                   "suben al azar de ella." if d else "No hay descenso."))
        out.append({"titulo": "Tabla Anual", "df": anual, "tipo": "liga", "nota": nota})
        return out

    def _destinos(self, L, anual):
        """Destino de cada fila de la Tabla Anual (provisorio hasta que termina la fase regular)."""
        P = L["playoff"]
        ganador = P["ganador"] if P else None
        cupos = set(P["cupos"]) if P else None
        out = []
        n, n_desc = len(anual), int(L.get("descensos", 0))
        for p, i in zip(anual["Pos"], anual["id"]):
            i = int(i)
            if n_desc and p > n - n_desc:
                out.append("Desciende")
                continue
            if L["hecho"]["Regular"]:
                if i in L["directos"]:
                    d = "Campeón · Asciende" if L["campeon"] == L["nombres"][i] else "Asciende"
                elif ganador == i:
                    d = "Asciende (playoff)"
                elif i in cupos:
                    d = "Playoff"
                else:
                    d = ""
            else:
                d = "Asciende" if p <= DIRECTOS else "Playoff" if p <= DIRECTOS + CUPOS_PLAYOFF else ""
                d = "Líder" if p == 1 else d
            out.append(d)
        return out

    # ---- fin de temporada ------------------------------------------------------------------------------------
    def cierre(self, L):
        """Campeón, orden final, puntos (para el promedio) y los que suben. Si se cierra antes de tiempo, suben los
        tres primeros de la Tabla Anual de hoy."""
        anual = _tabla_anual(L)
        orden = list(anual["Equipo"])
        suben = list(L["suben"]) or orden[:L.get("ascensos", DIRECTOS + 1)]
        d = int(L.get("descensos", 0))
        return {"campeon": L["campeon"] or orden[0], "orden": orden,
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in anual.iterrows()},
                "descienden": orden[len(orden) - d:] if d else [], "suben": suben}

    def reglas(self):
        return self.descripcion


FORMATOS[UruguaySegunda.nombre] = UruguaySegunda()
