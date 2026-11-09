"""Registro de competencias por rondas: Copa Argentina, Supercopa Argentina, Regionales y Mundial de Clubes.

Cada competencia declara en UN solo lugar cómo se juega: cuál es su estado en S, qué ronda toca,
cómo se juega, qué día cae cada ronda, qué partidos muestra el calendario y cómo se cierra la
temporada. El calendario, "Simular todo", "Nueva temporada", el historial y el palmarés recorren
REGISTRO en vez de nombrar cada competencia a mano.

Para sumar una competencia nueva: escribir su lógica en un módulo propio, agregar acá una clase
(heredando de PorRondas o de Competencia) y sumarla a REGISTRO. Sin Streamlit: es motor puro.
Importa copas/argentina.py, copas/mundial.py y motor/fechas.py (que no dependen de él): no hay importaciones circulares.
"""

import datetime as dt

import numpy as np

from copas.argentina import (COPA_RONDAS, nueva_supercopa, rivales_supercopa, simular_ronda_copa, simular_supercopa,
                   supercopa_lista)
from copas import brasil as copa_br
from copas import estaduales as est_br
from copas import chile as copa_cl
from copas import colombia as copa_co
from copas import uruguay as copa_uy
from copas.conmebol import CUPOS_LIB_GRUPOS, MEDIA_EXT, cupos_liga
from datos import ligas_ext
from ligas.exterior import comp_de, formato_de, jugar_ronda, mover_clubes, mover_clubes_en_lugar, tabla
from motor.fechas import desde as _desde, dia_liga, total_liga
from motor.nucleo import LOCALIA, jugar_ko, nuevo_partido, tanda_penales
from copas.regionales import (campeones as campeones_regionales, cruces_ronda as cruces_regionales,
                              regionales_vacios, rotulo_ronda as rotulo_regionales, simular_ronda_regionales,
                              sortear_regionales)
from copas.mundial import (RONDAS as RONDAS_MUNDIAL, actualizar_ratings, cerrar_temporada, es_temporada_mundial,
                     nuevo_mundial, partidos_ronda, simular_ronda_mundial, sortear_mundial)


def _anio(S):
    return 2025 + S["temp"]        # la temporada 1 del simulador es 2026


class Competencia:
    """Interfaz que cumple cada competencia del registro."""
    nombre = ""            # nombre en el calendario y en los partidos (campo "liga")
    clave = ""             # clave de S donde vive su estado
    col_historial = None   # columna de campeones del Historial (None: la maneja otro código)
    hist = None            # clave de S con el palmarés acumulado (None: la maneja otro código)
    crea_estado = False    # True: Nueva temporada (y la partida nueva) arman S[clave] con nueva()

    def estado(self, S):
        return S[self.clave]

    def nueva(self, S, rng):
        """Estado de la temporada nueva (se asigna a S[clave])."""
        raise NotImplementedError

    def activa(self, S):
        """Falso si esta temporada no se juega (p. ej. el Mundial fuera de su año)."""
        return True

    def total(self, S):
        raise NotImplementedError

    def hechas(self, S):
        """Rondas ya jugadas."""
        raise NotImplementedError

    def pendiente(self, S):
        """Número de la próxima ronda que se puede jugar, o None si no hay ninguna."""
        raise NotImplementedError

    def jugar(self, S, P, rng):
        """Juega la próxima ronda pendiente."""
        raise NotImplementedError

    def jugar_todo(self, S, P, rng):
        """Juega todo lo que se pueda jugar ahora (con tope por seguridad)."""
        for _ in range(100):
            if self.pendiente(S) is None:
                return
            self.jugar(S, P, rng)

    def terminada(self, S):
        return self.hechas(S) >= self.total(S)

    def log(self, S):
        return S.get(self.clave, {}).get("log", [])

    def cruces(self, S, n):
        """Partidos aún no jugados de la ronda n: [(local, visita, rótulo, competencia)]."""
        return []

    def rotulo(self, S, n):
        return f"Ronda {n}"

    def dia(self, S, n):
        raise NotImplementedError

    def campeon(self, S):
        return None

    def cerrar(self, S, rng):
        """Al terminar la temporada (antes de armar la siguiente)."""


class PorRondas(Competencia):
    """Competencia cuyo estado tiene "ronda", "total" y "log" (Copa Argentina, Mundial)."""

    def total(self, S):
        return self.estado(S)["total"]

    def hechas(self, S):
        return self.estado(S)["ronda"]

    def pendiente(self, S):
        E = self.estado(S)
        return E["ronda"] + 1 if self.activa(S) and E["ronda"] < E["total"] else None

    def terminada(self, S):
        E = self.estado(S)
        return (not self.activa(S)) or E["ronda"] >= E["total"]
class CopaArgentina(PorRondas):
    nombre = "Copa Argentina"
    clave = "copa"
    DIAS = [(3, 4), (4, 8), (5, 13), (6, 24), (8, 12), (9, 23), (11, 4)]     # miércoles

    def activa(self, S):
        return bool(S["copa"]["sorteada"])

    def jugar(self, S, P, rng):
        simular_ronda_copa(S["copa"], P, rng)

    def cruces(self, S, n):
        SC = S["copa"]
        if n - 1 >= len(SC["cuadro"]):
            return []
        nom = SC["nombres"]
        return [(nom[m["a"]], nom[m["b"]], "", "") for m in SC["cuadro"][n - 1]]

    def rotulo(self, S, n):
        return COPA_RONDAS[n - 1]

    def dia(self, S, n):
        mes, dia = self.DIAS[min(n, len(self.DIAS)) - 1]
        return _desde(_anio(S), mes, dia, 2)

    def campeon(self, S):
        SC = S["copa"]
        return SC["nombres"][SC["campeon"]] if SC["campeon"] is not None else None


class SupercopaArgentina(Competencia):
    nombre = "Supercopa Argentina"
    clave = "supercopa"
    col_historial = "Supercopa"
    hist = "hist_super"
    crea_estado = True

    def nueva(self, S, rng):
        return nueva_supercopa()

    def total(self, S):
        return 1

    def hechas(self, S):
        return 1 if S["supercopa"]["jugada"] else 0

    def pendiente(self, S):
        return 1 if supercopa_lista(S) else None

    def jugar(self, S, P, rng):
        simular_supercopa(S, P, rng)

    def terminada(self, S):
        return bool(S["supercopa"]["jugada"])

    def cruces(self, S, n):
        if not supercopa_lista(S):
            return []
        a, _, _, b, _, _ = rivales_supercopa(S)
        return [(a, b, "Final", "Final")]

    def rotulo(self, S, n):
        return "Final"

    def dia(self, S, n):
        """Miércoles siguiente a la última fecha de Primera."""
        return dia_liga(S, "Primera División", total_liga(S, "Primera División")) + dt.timedelta(days=3)

    def campeon(self, S):
        return S["supercopa"]["campeon"]


class Regionales(PorRondas):
    """Torneos regionales por zona (estilo Campeonato Carioca). Es opcional: sólo se juega si la persona los activó
    (S["regionales_on"]). Hay muchos campeones por temporada (uno por torneo), así que el historial y el palmarés
    los anota `cerrar` y no las columnas genéricas del registro (ver copas/regionales.py)."""
    nombre = "Regionales"
    clave = "regionales"
    crea_estado = True
    DIA_INICIAL = (1, 7)                               # arrancan el 7 de enero; una ronda cada 3 días

    def nueva(self, S, rng):
        return sortear_regionales(S, rng) if S.get("regionales_on") else regionales_vacios()

    def activa(self, S):
        return bool(S.get("regionales", {}).get("activo"))

    def jugar(self, S, P, rng):
        simular_ronda_regionales(S, P, rng)

    def cruces(self, S, n):
        return cruces_regionales(S, n)

    def rotulo(self, S, n):
        return rotulo_regionales(S, n)

    def dia(self, S, n):
        return dt.date(_anio(S), *self.DIA_INICIAL) + dt.timedelta(days=3 * (n - 1))

    def cerrar(self, S, rng):
        """Anota los campeones de cada torneo en el Historial (S["campeones"]); el palmarés por torneo sale de ahí."""
        camps = campeones_regionales(S)
        if camps:
            S["campeones"][-1]["Regionales"] = camps


class Estaduales(PorRondas):
    """Campeonatos estaduales de Brasil (Paulista, Carioca, Mineiro...), ver copas/estaduales.py. Se sortean al armar la
    temporada con los clubes de las cuatro divisiones (por eso van después de las ligas en REGISTRO). Hay un campeón por
    estado, así que el Historial y el palmarés los anota `cerrar` en S["campeones"][-1]["Estaduales"]."""
    nombre = est_br.NOMBRE
    clave = "estaduales"
    crea_estado = True
    DIA_INICIAL = (1, 10)                              # arrancan el 10 de enero; una ronda cada 4 días

    def nueva(self, S, rng):
        return est_br.sortear_estaduales(S, rng) if S.get("ext_br") is not None else est_br.estaduales_vacios()

    def activa(self, S):
        return bool(S.get("estaduales", {}).get("activo"))

    def jugar(self, S, P, rng):
        est_br.simular_ronda_estaduales(S, P, rng)

    def cruces(self, S, n):
        return est_br.cruces_ronda(S, n)

    def rotulo(self, S, n):
        return est_br.rotulo_ronda(S, n)

    def dia(self, S, n):
        return dt.date(_anio(S), *self.DIA_INICIAL) + dt.timedelta(days=4 * (n - 1))

    def cerrar(self, S, rng):
        camps = est_br.campeones(S)
        if camps:
            S["campeones"][-1][self.nombre] = camps


class MundialDeClubes(PorRondas):
    nombre = "Mundial de Clubes"
    clave = "mundial"
    col_historial = "Mundial"
    hist = "hist_mundial"
    crea_estado = True
    DIAS = [(6, 15), (6, 19), (6, 23), (6, 28), (7, 4), (7, 8), (7, 13)]     # 3 de grupos y 4 eliminatorias

    def nueva(self, S, rng):
        """Cada 4 temporadas (2029 = temporada 4) se arman clasificados y grupos."""
        if S["temp"] > 1:
            actualizar_ratings(S, rng)
        return sortear_mundial(S, rng) if es_temporada_mundial(S["temp"]) else nuevo_mundial()

    def activa(self, S):
        return bool(S.get("mundial", {}).get("sorteado"))

    def jugar(self, S, P, rng):
        simular_ronda_mundial(S, P, rng)

    def cruces(self, S, n):
        return partidos_ronda(S["mundial"], n)

    def rotulo(self, S, n):
        return RONDAS_MUNDIAL[n - 1]

    def dia(self, S, n):
        mes, dia = self.DIAS[min(n, len(self.DIAS)) - 1]
        return dt.date(_anio(S), mes, dia)

    def campeon(self, S):
        return S.get("mundial", {}).get("campeon")

    def cerrar(self, S, rng):
        """Registra los campeones continentales del año y los puntos del ranking CONMEBOL."""
        cerrar_temporada(S, rng)


class LigaExterior(Competencia):
    """Liga de primera división de otro país (Uruguay, y las que vengan): la arma ligas/exterior.py con el formato que
    pide su entrada de datos/json/ligas_ext.json. Las medias son las de S["rating_int"] (las mismas que usan las copas
    CONMEBOL) y al cerrar la temporada suben y bajan clubes entre la liga y la reserva de su país.
    Estado en S[clave] (ver `Formato.nueva`); extras de la partida: S["ext_clubes"] (quién juega cada liga, por país:
    "Uruguay" para la primera y "Uruguay|2" para la segunda), S["ext_prev"] (puntos y partidos de la temporada anterior,
    para el descenso por promedio) y S["ext_mov"] (quién subió y bajó, para mostrarlo).

    Un país puede tener una segunda división simulada (cfg["inferior"], ver datos/ligas_ext.py): es otra LigaExterior
    (cfg["divisional"] = 2) y los ascensos y descensos de la primera salen de sus tablas finales, no del azar. Lo mismo
    vale para la tercera (divisional 3) y la cuarta (divisional 4: Brasil). Al cerrar la temporada, la primera mueve a
    todas: S["ext_mov"] (primera y segunda), S["ext_mov3"] (segunda y tercera) y S["ext_mov4"] (tercera y cuarta)."""
    crea_estado = True

    def __init__(self, cfg):
        self.cfg = cfg
        self.nombre = cfg["nombre"]
        self.clave = "ext_" + cfg["clave"]
        self.divisional = int(cfg.get("divisional", 1))
        self.clubes_key = ligas_ext.clave_clubes(cfg)
        # la columna del Historial: la primera usa el nombre del país; las de abajo suman su divisional
        self.col_historial = cfg["pais"] if self.divisional == 1 else f"{cfg['pais']} · D{self.divisional}"
        self.hist = "hist_" + self.clave
        self.formato = formato_de(cfg)

    def nueva(self, S, rng):
        pais = self.cfg["pais"]
        nombres = list(S.setdefault("ext_clubes", {}).get(self.clubes_key) or self.cfg["clubes"])
        ri = S.setdefault("rating_int", dict(MEDIA_EXT))
        r = [ri.get(n, MEDIA_EXT[n]) for n in nombres]
        previo = (S.setdefault("ext_prom_hist", {}).get(pais, {}) if pais == "Colombia" else
                  S.setdefault("ext_prev", {}).get(pais, {})) if self.divisional == 1 else {}
        L = self.formato.nueva(self.cfg, nombres, r, previo, _anio(S), rng)
        S["ext_clubes"][self.clubes_key] = nombres
        if self.divisional == 1 and self.cfg.get("tercera"):      # tercera división falsa: sólo es una lista de clubes
            S["ext_clubes"].setdefault(ligas_ext.clave_tercera(self.cfg), list(self.cfg["tercera"]))
        if self.divisional == 1 and pais in CUPOS_LIB_GRUPOS:     # cupos CONMEBOL del país, en el orden en que se reparten
            L["cupos"] = cupos_liga(pais)
        self.formato.avanzar(L, rng)
        return L

    def total(self, S):
        return len(S[self.clave]["rondas"])

    def hechas(self, S):
        return S[self.clave]["fecha"]

    def pendiente(self, S):
        L = S[self.clave]
        return L["fecha"] + 1 if L["fecha"] < len(L["rondas"]) else None

    def terminada(self, S):
        L = S[self.clave]
        return L["campeon"] is not None and L["fecha"] >= len(L["rondas"])

    def jugar(self, S, P, rng):
        L = S[self.clave]
        jugar_ronda(L, P, rng)
        self.formato.avanzar(L, rng)

    def cruces(self, S, n):
        L = S[self.clave]
        if n <= L["fecha"] or n > len(L["rondas"]) or not L["rondas"][n - 1]["pares"]:
            return []
        R, nom = L["rondas"][n - 1], L["nombres"]
        return [(nom[a], nom[b], R["rotulo"], comp_de(R, a)) for a, b in R["pares"]]

    def rotulo(self, S, n):
        L = S[self.clave]
        return L["rondas"][min(n, len(L["rondas"])) - 1]["rotulo"]

    def dia(self, S, n):
        L = S[self.clave]
        return L["rondas"][min(n, len(L["rondas"])) - 1]["dia"]

    def campeon(self, S):
        return S[self.clave]["campeon"]

    def definiciones(self, S, L):
        """Cómo se definió el título de la temporada de `L`: campeón, subcampeón, quién ganó cada torneo y los partidos
        decisivos (semifinales, finales, desempates), cada uno con su día. Es lo que muestra la sección Campeones."""
        etapas = set(self.formato.etapas_definicion)
        partidos = [{**p, "dia": L["rondas"][p["fecha"] - 1]["dia"]} for p in L["log"]
                    if L["rondas"][p["fecha"] - 1]["etapa"] in etapas]
        nom = L["nombres"]
        return {"temp": S["temp"], "campeon": L["campeon"], "subcampeon": L.get("subcampeon"), "via": L.get("via", ""),
                "suben": list(L.get("suben", [])),
                "ganadores": {t: nom[i] for t, i in L.get("ganadores", {}).items() if i is not None},
                "partidos": partidos}

    @staticmethod
    def _sortear_tercera(S, rng, tercera, k):
        """k clubes de la tercera división falsa que suben a la segunda: al azar, con un poco más de chances los de mejor
        media (misma idea que cuando la segunda no se simula)."""
        ri = S.setdefault("rating_int", dict(MEDIA_EXT))
        k = min(k, len(tercera))
        w = np.exp((np.array([ri.get(n, MEDIA_EXT[n]) for n in tercera]) - max(ri.get(n, MEDIA_EXT[n]) for n in tercera)) / 6.0)
        return [tercera[int(i)] for i in rng.choice(len(tercera), size=k, replace=False, p=w / w.sum())]

    def _inferior(self):
        """La LigaExterior de la segunda división simulada de este país (None si no la hay)."""
        clave = self.cfg.get("inferior")
        return next((c for c in LIGAS_EXTERIOR if c.cfg["clave"] == clave), None) if clave else None

    def cerrar(self, S, rng):
        """Guarda las medias, los puntos del año y los movimientos. En una primera división: bajan los que dice el
        formato y suben los de la segunda (su tabla, si se simula; si no, al azar entre la reserva, los de mejor media
        más seguido). En una segunda simulada sólo guarda las medias y anota quién subió."""
        L, pais = S[self.clave], self.cfg["pais"]
        c = self.formato.cierre(L)
        if pais == "Colombia" and self.divisional == 1:
            historial = S.setdefault("ext_prom_hist", {}).setdefault(pais, {})
            for club, (pts, pj) in c.get("puntos", {}).items():
                if pj:
                    historial.setdefault(club, []).append((int(pts), int(pj)))
                    historial[club] = historial[club][-3:]
        ri = S.setdefault("rating_int", dict(MEDIA_EXT))
        for n, x in zip(L["nombres"], L["r"]):
            ri[n] = float(x)
        S.setdefault("ext_def", {}).setdefault(self.clave, []).append(self.definiciones(S, L))
        if self.divisional > 1:       # quién juega la temporada que viene lo arma la liga de arriba; acá sólo se anota
            S.setdefault("ext_mov", {})[self.clubes_key] = {"temp": S["temp"], "suben": list(c.get("suben", [])),
                                                            "bajan": list(c.get("descienden", [])), "orden": c["orden"]}
            return
        bajan = list(c["descienden"])
        inferior = self._inferior()
        if inferior:                  # segunda simulada: suben los que ascendieron en su tabla y ahí van los que bajan
            L2 = S[inferior.clave]
            c2 = inferior.formato.cierre(L2)
            suben = [n for n in c2["suben"] if n not in set(L["nombres"])][:len(bajan)]
            suben += [n for n in c2["orden"] if n not in set(suben)][:max(len(bajan) - len(suben), 0)]
            bajan2, sube3 = list(c2.get("descienden", [])), []     # los últimos de la segunda bajan a la tercera
            tercera_liga = inferior._inferior()                    # Primera Amateur (simulada), si la hay
            if bajan2 and tercera_liga is not None and S.get(tercera_liga.clave):
                L3 = S[tercera_liga.clave]
                c3 = tercera_liga.formato.cierre(L3)
                sube3 = list(c3["suben"])[:len(bajan2)]
                sube3 += [n for n in c3["orden"] if n not in set(sube3)][:max(len(bajan2) - len(sube3), 0)]
                bajan3, sube4 = list(c3.get("descienden", [])), []     # los últimos de la tercera bajan a la cuarta (Brasil)
                cuarta_liga = tercera_liga._inferior()                 # Série D (simulada), si la hay
                if bajan3 and cuarta_liga is not None and S.get(cuarta_liga.clave):
                    L4 = S[cuarta_liga.clave]
                    c4 = cuarta_liga.formato.cierre(L4)
                    sube4 = list(c4["suben"])[:len(bajan3)]
                    sube4 += [n for n in c4["orden"] if n not in set(sube4)][:max(len(bajan3) - len(sube4), 0)]
                    mover4 = mover_clubes_en_lugar if cuarta_liga.formato.lugares_fijos else mover_clubes
                    S["ext_clubes"][cuarta_liga.clubes_key] = mover4(L4["nombres"], sube4, bajan3)
                    S.setdefault("ext_mov4", {})[pais] = {"temp": S["temp"], "suben": list(sube4), "bajan": list(bajan3)}
                else:
                    bajan3 = []
                S["ext_clubes"][tercera_liga.clubes_key] = mover_clubes(L3["nombres"], sube3 + bajan3, bajan2 + sube4)
                S.setdefault("ext_mov3", {})[pais] = {"temp": S["temp"], "suben": list(sube3), "bajan": list(bajan2)}
            elif bajan2 and self.cfg.get("tercera"):
                clave3 = ligas_ext.clave_tercera(self.cfg)
                tercera = list(S["ext_clubes"].get(clave3) or self.cfg["tercera"])
                sube3 = self._sortear_tercera(S, rng, tercera, len(bajan2))
                S["ext_clubes"][clave3] = mover_clubes(tercera, sube3, bajan2)
                S.setdefault("ext_mov3", {})[pais] = {"temp": S["temp"], "suben": list(sube3), "bajan": list(bajan2)}
            else:
                bajan2 = []
            S["ext_clubes"][inferior.clubes_key] = mover_clubes(L2["nombres"], suben + bajan2, bajan + sube3)
        else:                         # segunda sin simular: suben al azar de la reserva, los de mejor media más seguido
            reserva = [n for n in ligas_ext.clubes_de_la_liga(self.cfg) if n not in set(L["nombres"])]
            k = min(int(self.cfg.get("ascensos", 0)), len(reserva))
            suben = []
            if k:
                w = np.exp((np.array([ri.get(n, MEDIA_EXT[n]) for n in reserva]) - 50.0) / 6.0)
                suben = [reserva[int(i)] for i in rng.choice(len(reserva), size=k, replace=False, p=w / w.sum())]
        S["ext_clubes"][pais] = mover_clubes(L["nombres"], bajan, suben)
        S.setdefault("ext_prev", {})[pais] = {n: v for n, v in c["puntos"].items() if n not in set(bajan)}
        S.setdefault("ext_mov", {})[pais] = {"temp": S["temp"], "suben": suben, "bajan": bajan, "orden": c["orden"]}


class CopaUruguay(Competencia):
    """Copa AUF Uruguay (ver copas/uruguay.py). El estado de S["copa_uy"] tiene la forma del de una liga del exterior, así
    que se juega con `jugar_ronda`. No se sortea al arrancar la temporada sino cuando termina el Torneo Competencia de la
    Segunda División (de ahí salen 8 de sus 40 clubes): hasta entonces no está activa y no figura en el calendario.
    Va después de las ligas en REGISTRO: "Simular todo" juega primero las ligas y la copa ya encuentra sus clubes.
    Al cerrar la temporada anota el campeón en S["ext_copa"]["Uruguay"]: es el Uruguay 4 de la Libertadores."""
    nombre = copa_uy.NOMBRE
    clave = copa_uy.CLAVE
    col_historial = copa_uy.NOMBRE
    hist = "hist_copa_uy"
    crea_estado = True
    LIGA_1, LIGA_2 = "ext_uy", "ext_uy2"          # claves de S de la Liga AUF y de la Segunda División

    def nueva(self, S, rng):
        return copa_uy.nueva_copa(_anio(S))

    def _asegurar(self, S):
        """Sortea la copa en cuanto la Segunda terminó el Torneo Competencia (una sola vez por temporada)."""
        L = S[self.clave]
        L2 = S.get(self.LIGA_2)
        if L["sorteada"] or not (L2 and L2["hecho"]["Competencia"]):
            return L
        rng, L1 = S["rng"], S[self.LIGA_1]
        ri = S.setdefault("rating_int", dict(MEDIA_EXT))
        media = lambda n: ri.get(n, MEDIA_EXT[n])
        de_segunda = list(tabla(L2, L2["E"]["Competencia"])["Equipo"])[:copa_uy.DE_SEGUNDA]
        r2 = dict(zip(L2["nombres"], L2["r"]))
        pool = S["ext_clubes"].get(ligas_ext.clave_tercera(ligas_ext.CONFIG["uy"]), [])
        amateurs = copa_uy.sortear_amateurs(rng, pool, media)
        copa_uy.sortear(L, rng, list(L1["nombres"]) + de_segunda,
                        [float(x) for x in L1["r"]] + [float(r2[n]) for n in de_segunda],
                        amateurs, [media(n) for n in amateurs])
        return L

    def activa(self, S):
        return self._asegurar(S)["sorteada"]

    def total(self, S):
        return len(S[self.clave]["rondas"])

    def hechas(self, S):
        return S[self.clave]["fecha"]

    def pendiente(self, S):
        L = self._asegurar(S)
        if L["sorteada"] and L["fecha"] < len(L["rondas"]) and L["rondas"][L["fecha"]]["pares"]:
            return L["fecha"] + 1
        return None

    def terminada(self, S):
        L = self._asegurar(S)
        return L["sorteada"] and L["campeon"] is not None

    def jugar(self, S, P, rng):
        L = self._asegurar(S)
        if self.pendiente(S) is None:
            return
        jugar_ronda(L, P, rng)
        copa_uy.avanzar(L, rng)

    def cruces(self, S, n):
        L = S[self.clave]
        if not L["sorteada"] or n <= L["fecha"] or n > len(L["rondas"]) or not L["rondas"][n - 1]["pares"]:
            return []
        R, nom = L["rondas"][n - 1], L["nombres"]
        return [(nom[a], nom[b], R["rotulo"], comp_de(R, a)) for a, b in R["pares"]]

    def rotulo(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["rotulo"]

    def dia(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["dia"]

    def campeon(self, S):
        return S[self.clave]["campeon"]

    def cerrar(self, S, rng):
        """Anota el campeón (Uruguay 4 de la Libertadores) y cómo se definió la copa (sección Campeones)."""
        L = S[self.clave]
        if not (L["sorteada"] and L["campeon"]):
            S.setdefault("ext_copa", {})[copa_uy.PAIS] = None
            return
        S.setdefault("ext_copa", {})[copa_uy.PAIS] = L["campeon"]
        S.setdefault("ext_def", {}).setdefault(self.clave, []).append(copa_uy.definicion(L, S["temp"]))


class CopaBrasil(Competencia):
    """Copa do Brasil (ver copas/brasil.py): 126 clubes, nueve fases, a ida y vuelta desde la quinta (donde entra la Série A)
    y final única. Sale de las cuatro ligas de Brasil del simulador (Série A a D), así que se sortea al armar la temporada,
    después de ellas (por eso va después de las ligas en REGISTRO). El estado de S["copa_br"] tiene la forma del de una liga
    del exterior y se juega con `jugar_ronda`.
    Al cerrar la temporada anota el campeón en S["ext_copa"]["Brasil"] (cupo a los grupos de la Libertadores) y el subcampeón en
    S["ext_copa_sub"]["Brasil"] (Fase 2): copas/conmebol.py los pone primeros y, si ya clasificaron por la Série A, el cupo
    sigue por la tabla."""
    nombre = copa_br.NOMBRE
    clave = copa_br.CLAVE
    col_historial = copa_br.NOMBRE
    hist = "hist_copa_br"
    crea_estado = True
    LIGA_A = "ext_br"                                                     # clave de S de la Série A
    INFERIORES = (("ext_br2", "Série B"), ("ext_br3", "Série C"), ("ext_br4", "Série D"))

    def nueva(self, S, rng):
        L = copa_br.nueva_copa(_anio(S))
        if S.get(self.LIGA_A) is not None:
            self._sortear(S, L, rng)
        return L

    def _sortear(self, S, L, rng):
        """Arma la copa con los clubes que hoy juegan las cuatro divisiones de Brasil."""
        ri = S.setdefault("rating_int", dict(MEDIA_EXT))
        media = lambda n: ri.get(n, MEDIA_EXT[n])
        por_division = {div: list(S[clave]["nombres"]) for clave, div in self.INFERIORES if S.get(clave)}
        campeones = {}
        for clave, div in self.INFERIORES[1:]:                            # campeones de la C y de la D de la temporada anterior
            anteriores = S.get("ext_def", {}).get(clave) or []
            if anteriores and anteriores[-1].get("campeon"):
                campeones[div] = anteriores[-1]["campeon"]
        tercera = copa_br.elegir_tercera_fase(por_division, campeones, media)
        copa_br.sortear(L, rng, list(S[self.LIGA_A]["nombres"]), por_division, tercera, media)

    def _asegurar(self, S):
        """Devuelve el estado de la copa (el sorteo se realiza al crear la temporada)."""
        return S[self.clave]

    def activa(self, S):
        return S[self.clave]["sorteada"]

    def total(self, S):
        return len(S[self.clave]["rondas"])

    def hechas(self, S):
        return S[self.clave]["fecha"]

    def pendiente(self, S):
        L = self._asegurar(S)
        if L["sorteada"] and L["fecha"] < len(L["rondas"]) and L["rondas"][L["fecha"]]["pares"]:
            return L["fecha"] + 1
        return None

    def terminada(self, S):
        L = self._asegurar(S)
        return (not L["sorteada"]) or L["campeon"] is not None

    def jugar(self, S, P, rng):
        L = self._asegurar(S)
        if self.pendiente(S) is None:
            return
        jugar_ronda(L, P, rng)
        copa_br.avanzar(L, rng)

    def cruces(self, S, n):
        L = S[self.clave]
        if not L["sorteada"] or n <= L["fecha"] or n > len(L["rondas"]) or not L["rondas"][n - 1]["pares"]:
            return []
        R, nom = L["rondas"][n - 1], L["nombres"]
        return [(nom[a], nom[b], R["rotulo"], comp_de(R, a)) for a, b in R["pares"]]

    def rotulo(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["rotulo"]

    def dia(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["dia"]

    def campeon(self, S):
        return S[self.clave]["campeon"]

    def cerrar(self, S, rng):
        """Anota el campeón (grupos de la Libertadores) y el subcampeón (Fase 2) y cómo se definió la copa."""
        L = S[self.clave]
        if not (L["sorteada"] and L["campeon"]):
            S.setdefault("ext_copa", {})[copa_br.PAIS] = None
            S.setdefault("ext_copa_sub", {})[copa_br.PAIS] = None
            return
        S.setdefault("ext_copa", {})[copa_br.PAIS] = L["campeon"]
        S.setdefault("ext_copa_sub", {})[copa_br.PAIS] = L["subcampeon"]
        S.setdefault("ext_def", {}).setdefault(self.clave, []).append(copa_br.definicion(L, S["temp"]))


class CopaChile(Competencia):
    """Copa Chile (ver copas/chile.py): 32 clubes (los 16 de la Liga de Primera y los 16 de la Primera B), ocho grupos de cuatro y
    octavos a final (ida y vuelta, final única). Se sortea al armar la temporada, después de las dos ligas (por eso va después de
    ellas en REGISTRO). El estado de S["copa_cl"] tiene la forma del de una liga del exterior y se juega con `jugar_ronda`.
    Al cerrar la temporada anota el campeón en S["ext_copa"]["Chile"]: copas/conmebol.py le da el Chile 4 (Libertadores · Fase 2)
    si juega en Primera; si ya clasificó por la tabla, el cupo sigue por ella."""
    nombre = copa_cl.NOMBRE
    clave = copa_cl.CLAVE
    col_historial = copa_cl.NOMBRE
    hist = "hist_copa_cl"
    crea_estado = True
    LIGA_1, LIGA_2 = "ext_cl", "ext_cl2"                                  # claves de S de la Liga de Primera y de la Primera B

    def nueva(self, S, rng):
        L = copa_cl.nueva_copa(_anio(S))
        if S.get(self.LIGA_1) is not None and S.get(self.LIGA_2) is not None:
            ri = S.setdefault("rating_int", dict(MEDIA_EXT))
            try:
                copa_cl.sortear(L, rng, list(S[self.LIGA_1]["nombres"]), list(S[self.LIGA_2]["nombres"]),
                                lambda n: ri.get(n, MEDIA_EXT[n]))
            except ValueError:                                            # sin 16 + 16 clubes no hay copa (la interfaz lo avisa)
                pass
        return L

    def _asegurar(self, S):
        """Devuelve el estado de la copa (el sorteo se realiza al crear la temporada)."""
        return S[self.clave]

    def activa(self, S):
        return S[self.clave]["sorteada"]

    def total(self, S):
        return len(S[self.clave]["rondas"])

    def hechas(self, S):
        return S[self.clave]["fecha"]

    def pendiente(self, S):
        L = self._asegurar(S)
        if L["sorteada"] and L["fecha"] < len(L["rondas"]) and L["rondas"][L["fecha"]]["pares"]:
            return L["fecha"] + 1
        return None

    def terminada(self, S):
        L = self._asegurar(S)
        return (not L["sorteada"]) or L["campeon"] is not None

    def jugar(self, S, P, rng):
        L = self._asegurar(S)
        if self.pendiente(S) is None:
            return
        jugar_ronda(L, P, rng)
        copa_cl.avanzar(L, rng)

    def cruces(self, S, n):
        L = S[self.clave]
        if not L["sorteada"] or n <= L["fecha"] or n > len(L["rondas"]) or not L["rondas"][n - 1]["pares"]:
            return []
        R, nom = L["rondas"][n - 1], L["nombres"]
        return [(nom[a], nom[b], R["rotulo"], comp_de(R, a)) for a, b in R["pares"]]

    def rotulo(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["rotulo"]

    def dia(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["dia"]

    def campeon(self, S):
        return S[self.clave]["campeon"]

    def cerrar(self, S, rng):
        """Anota el campeón (Chile 4 de la Libertadores) y cómo se definió la copa."""
        L = S[self.clave]
        if not (L["sorteada"] and L["campeon"]):
            S.setdefault("ext_copa", {})[copa_cl.PAIS] = None
            S.setdefault("ext_copa_sub", {})[copa_cl.PAIS] = None
            return
        S.setdefault("ext_copa", {})[copa_cl.PAIS] = L["campeon"]
        S.setdefault("ext_copa_sub", {})[copa_cl.PAIS] = L["subcampeon"]
        S.setdefault("ext_def", {}).setdefault(self.clave, []).append(copa_cl.definicion(L, S["temp"]))


class CopaColombia(Competencia):
    """Copa Colombia (ver copas/colombia.py): 36 clubes (los 20 de la Liga BetPlay y los 16 del Torneo BetPlay), cuatro grupos de cinco,
    series a ida y vuelta, octavos y cuartos a partido único, y semifinales y final a ida y vuelta. Se sortea al armar la temporada,
    después de las dos ligas (por eso va después de ellas en REGISTRO). El estado de S["copa_co"] tiene la forma del de una liga del
    exterior y se juega con `jugar_ronda`. El sorteo espera a que terminen las fases clasificatorias del primer semestre: los ocho mejores
    de cada división entran a Fase 1B y el resto a grupos. Al cerrar, el campeón obtiene el cupo a Sudamericana si juega en Primera."""
    nombre = copa_co.NOMBRE
    clave = copa_co.CLAVE
    col_historial = copa_co.NOMBRE
    hist = "hist_copa_co"
    crea_estado = True
    LIGA_1, LIGA_2 = "ext_co", "ext_co2"                                  # claves de S de la Liga BetPlay y del Torneo BetPlay

    def nueva(self, S, rng):
        # Los participantes de Fase 1B dependen de la clasificación real del Apertura;
        # por eso el sorteo se difiere hasta que terminen ambos torneos del primer semestre.
        return copa_co.nueva_copa(_anio(S))

    def _asegurar(self, S):
        L = S[self.clave]
        if L["sorteada"]:
            return L
        L1, L2 = S.get(self.LIGA_1), S.get(self.LIGA_2)
        if not (L1 and L2):
            return L
        if L1.get("hecho", {}).get("Apertura · final") != "listo":
            return L
        if L2.get("hecho", {}).get("Apertura · final") != "listo":
            return L
        try:
            ri = S.setdefault("rating_int", dict(MEDIA_EXT))
            clas_p = [L1["nombres"][i] for i in L1.get("clasificados_apertura", [])]
            clas_t = [L2["nombres"][i] for i in L2.get("clasificados_apertura", [])]
            copa_co.sortear(L, S["rng"], list(L1["nombres"]), list(L2["nombres"]),
                            lambda n: ri.get(n, MEDIA_EXT[n]), clas_p, clas_t)
        except (ValueError, KeyError, IndexError):
            return L
        return L

    def activa(self, S):
        return self._asegurar(S)["sorteada"]

    def total(self, S):
        return len(S[self.clave]["rondas"])

    def hechas(self, S):
        return S[self.clave]["fecha"]

    def pendiente(self, S):
        L = self._asegurar(S)
        if L["sorteada"] and L["fecha"] < len(L["rondas"]) and L["rondas"][L["fecha"]]["pares"]:
            return L["fecha"] + 1
        return None

    def terminada(self, S):
        L = self._asegurar(S)
        return (not L["sorteada"]) or L["campeon"] is not None

    def jugar(self, S, P, rng):
        L = self._asegurar(S)
        if self.pendiente(S) is None:
            return
        jugar_ronda(L, P, rng)
        copa_co.avanzar(L, rng)
        if L.get("campeon") and S.get(self.LIGA_1):
            S[self.LIGA_1]["campeon_copa_colombia"] = L["campeon"]

    def cruces(self, S, n):
        L = S[self.clave]
        if not L["sorteada"] or n <= L["fecha"] or n > len(L["rondas"]) or not L["rondas"][n - 1]["pares"]:
            return []
        R, nom = L["rondas"][n - 1], L["nombres"]
        return [(nom[a], nom[b], R["rotulo"], comp_de(R, a)) for a, b in R["pares"]]

    def rotulo(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["rotulo"]

    def dia(self, S, n):
        return S[self.clave]["rondas"][min(n, self.total(S)) - 1]["dia"]

    def campeon(self, S):
        return S[self.clave]["campeon"]

    def cerrar(self, S, rng):
        """Anota el campeón (cupo a la Sudamericana) y cómo se definió la copa."""
        L = S[self.clave]
        if not (L["sorteada"] and L["campeon"]):
            S.setdefault("ext_copa", {})[copa_co.PAIS] = None
            S.setdefault("ext_copa_sub", {})[copa_co.PAIS] = None
            return
        S.setdefault("ext_copa", {})[copa_co.PAIS] = L["campeon"]
        S.setdefault("ext_copa_sub", {})[copa_co.PAIS] = L["subcampeon"]
        S.setdefault("ext_def", {}).setdefault(self.clave, []).append(copa_co.definicion(L, S["temp"]))


class SupercopaChile(Competencia):
    """Supercopa de Chile (Final Four desde 2026): el 1° y el 2° de la Liga de Primera y el campeón y el subcampeón de la Copa Chile
    juegan semifinales (1° de la liga contra el subcampeón de la copa y 2° contra el campeón) y final, a partido único en cancha
    neutral y con penales directos. Si un club clasifica por dos vías, su lugar lo toma el que sigue en la tabla de la liga. Se juega
    después de que terminan las dos (acá, como las otras supercopas, cierra la temporada actual; en la realidad abre la siguiente)."""
    nombre = "Supercopa de Chile"
    clave = "supercopa_cl"
    col_historial = "Supercopa de Chile"
    hist = "hist_supercopa_cl"
    crea_estado = True
    LIGA = "ext_cl"                                    # clave de S de la Liga de Primera
    COPA = copa_cl.CLAVE                               # clave de S de la Copa Chile

    def nueva(self, S, rng):
        return {"finalistas": None, "campeon": None, "subcampeon": None, "log": [], "fecha": 0}

    def estado(self, S):
        return S.setdefault(self.clave, self.nueva(S, None))        # las partidas guardadas antes de la Supercopa no la traen

    def clasificados(self, S):
        """[(club, motivo)] de los cuatro clasificados en el orden del cuadro (1° liga, 2° liga, campeón copa, subcampeón copa), o None
        si todavía no terminaron la liga y la copa."""
        L, C = S.get(self.LIGA), S.get(self.COPA)
        if not L or not C or not C.get("sorteada") or L.get("campeon") is None or C.get("campeon") is None:
            return None
        tab = list(tabla(L, L["E"]["Liga"])["Equipo"])
        cand = [(tab[0], "Campeón de la Liga de Primera"), (tab[1], "Subcampeón de la Liga de Primera"),
                (C["campeon"], "Campeón de la Copa Chile"), (C["subcampeon"], "Subcampeón de la Copa Chile")]
        propios = {c for c, _ in cand}
        sobran = iter([(i + 1, c) for i, c in enumerate(tab) if i >= 2 and c not in propios])
        out, usados = [], set()
        for club, motivo in cand:
            if club in usados:                          # ya clasificó por otra vía: entra el que sigue en la tabla de la liga
                pos, club = next(sobran)
                motivo = f"{pos}° de la Liga de Primera (el cupo de la copa estaba repetido)"
            usados.add(club)
            out.append((club, motivo))
        return out

    def semifinales(self, S):
        q = self.clasificados(S)
        return [(q[0][0], q[3][0]), (q[1][0], q[2][0])] if q else []

    def activa(self, S):
        C = S.get(self.COPA)
        return bool(S.get(self.LIGA)) and bool(C) and bool(C.get("sorteada"))

    def total(self, S):
        return 2

    def hechas(self, S):
        return self.estado(S)["fecha"]

    def pendiente(self, S):
        E = self.estado(S)
        if E["fecha"] >= 2:
            return None
        return E["fecha"] + 1 if (E["fecha"] == 1 or self.clasificados(S)) else None

    def terminada(self, S):
        return self.estado(S)["fecha"] >= 2 or not self.activa(S)

    def jugar(self, S, P, rng):
        E = self.estado(S)
        if self.pendiente(S) is None:
            return
        r = {**dict(zip(S[self.LIGA]["nombres"], S[self.LIGA]["r"])), **dict(zip(S[self.COPA]["nombres"], S[self.COPA]["r"]))}
        rot = "Semifinales" if E["fecha"] == 0 else "Final"
        pares = self.semifinales(S) if E["fecha"] == 0 else [E["finalistas"]]
        ganadores = []
        for a, b in pares:
            gl, gv, gana_local, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), localia=0.0, **P)
            tanda = tanda_penales(rng, bool(gana_local[0])) if pen[0] else None
            p = nuevo_partido(self.nombre, E["fecha"] + 1, rot, rot, a, b, gl[0], gv[0], tanda=tanda,
                              gana=a if gana_local[0] else b, neutral=True)
            E["log"].append(p)
            ganadores.append(p["gana"])
        E["fecha"] += 1
        if rot == "Semifinales":
            E["finalistas"] = tuple(ganadores)
        else:
            E["campeon"] = ganadores[0]
            E["subcampeon"] = a if ganadores[0] == b else b

    def cruces(self, S, n):
        E = self.estado(S)
        if n != E["fecha"] + 1 or n > 2:
            return []
        if n == 1:
            return [(a, b, "Semifinales", "Semifinales") for a, b in self.semifinales(S)]
        return [(E["finalistas"][0], E["finalistas"][1], "Final", "Final")]

    def rotulo(self, S, n):
        return "Semifinales" if n == 1 else "Final"

    def dia(self, S, n):
        """Una semana después de lo último que termina (la liga o la final de la Copa Chile); la final, cuatro días después."""
        base = max(S[self.LIGA]["rondas"][-1]["dia"], S[self.COPA]["rondas"][-1]["dia"]) + dt.timedelta(days=7)
        return base if n == 1 else base + dt.timedelta(days=4)

    def campeon(self, S):
        return self.estado(S)["campeon"]


class SupercopaBrasil(Competencia):
    """Supercopa do Brasil: partido único en cancha neutral entre el campeón de la Série A y el campeón de la Copa do Brasil
    (si es el mismo club, el rival es el subcampeón de la Série A). Se juega una semana después de que terminan las dos
    (en la vida real abre la temporada siguiente; acá, como la Supercopa Argentina, cierra la actual)."""
    nombre = "Supercopa do Brasil"
    clave = "supercopa_br"
    col_historial = "Supercopa do Brasil"
    hist = "hist_supercopa_br"
    crea_estado = True
    LIGA = "ext_br"                                    # clave de S de la Série A
    COPA = copa_br.CLAVE                               # clave de S de la Copa do Brasil

    def nueva(self, S, rng):
        return {"jugada": False, "a": None, "b": None, "campeon": None, "log": [], "fecha": 0}

    def estado(self, S):
        return S.setdefault(self.clave, self.nueva(S, None))        # las partidas guardadas antes de la Supercopa no la traen

    def rivales(self, S):
        """(campeón de la Série A, rival) o None si todavía no se definen la liga y la copa. El rival es el campeón de la Copa\n        do Brasil o, si es el mismo club, el subcampeón de la Série A."""
        L, C = S.get(self.LIGA), S.get(self.COPA)
        if not L or not C or not C.get("sorteada") or L.get("campeon") is None or C.get("campeon") is None:
            return None
        return L["campeon"], (L.get("subcampeon") if C["campeon"] == L["campeon"] else C["campeon"])

    def rival_es_copero(self, S):
        """True si el rival es el campeón de la Copa do Brasil (False: el subcampeón de la Série A, por doblete)."""
        C = S.get(self.COPA) or {}
        riv = self.rivales(S)
        return bool(riv) and riv[1] == C.get("campeon")

    def activa(self, S):
        return bool(S.get(self.LIGA)) and bool(S.get(self.COPA))

    def total(self, S):
        return 1

    def hechas(self, S):
        return 1 if self.estado(S)["jugada"] else 0

    def pendiente(self, S):
        riv = self.rivales(S)
        return 1 if not self.estado(S)["jugada"] and riv and riv[1] else None

    def terminada(self, S):
        return bool(self.estado(S)["jugada"]) or not self.activa(S)

    def jugar(self, S, P, rng):
        riv = self.rivales(S)
        E = self.estado(S)
        if E["jugada"] or not riv or not riv[1]:
            return
        r = {**dict(zip(S[self.LIGA]["nombres"], S[self.LIGA]["r"])), **dict(zip(S[self.COPA]["nombres"], S[self.COPA]["r"]))}
        a, b = riv
        gl, gv, gana_local, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), localia=0.0, **P)
        tanda = tanda_penales(rng, bool(gana_local[0])) if pen[0] else None
        p = nuevo_partido(self.nombre, 1, "Final", "Final", a, b, gl[0], gv[0], tanda=tanda,
                          gana=a if gana_local[0] else b, neutral=True)
        E.update(jugada=True, a=a, b=b, campeon=p["gana"], fecha=1)
        E["log"].append(p)

    def cruces(self, S, n):
        riv = self.rivales(S)
        return [(riv[0], riv[1], "Final", "Final")] if riv and not self.estado(S)["jugada"] and riv[1] else []

    def rotulo(self, S, n):
        return "Final"

    def dia(self, S, n):
        """Una semana después de lo último que termina: la Série A o la final de la Copa do Brasil."""
        return max(S[self.LIGA]["rondas"][-1]["dia"], S[self.COPA]["rondas"][-1]["dia"]) + dt.timedelta(days=7)

    def campeon(self, S):
        return self.estado(S)["campeon"]


class SupercopaUruguaya(Competencia):
    """Supercopa Uruguaya: partido único en cancha neutral entre el campeón de la Liga AUF y el ganador del Intermedio
    (si es el mismo club, el rival es el subcampeón de la liga). Se juega el sábado siguiente al final de la liga."""
    nombre = "Supercopa Uruguaya"
    clave = "supercopa_uy"
    col_historial = "Supercopa Uruguaya"
    hist = "hist_supercopa_uy"
    crea_estado = True
    LIGA = "ext_uy"

    def nueva(self, S, rng):
        return {"jugada": False, "a": None, "b": None, "campeon": None, "log": [], "fecha": 0}

    def rivales(self, S):
        """(campeón de la liga, rival) o None si todavía no se definen."""
        L = S[self.LIGA]
        if L["campeon"] is None or L["ganadores"].get("Intermedio") is None:
            return None
        inter = L["nombres"][L["ganadores"]["Intermedio"]]
        return L["campeon"], (L["subcampeon"] if inter == L["campeon"] else inter)

    def total(self, S):
        return 1

    def hechas(self, S):
        return 1 if S[self.clave]["jugada"] else 0

    def pendiente(self, S):
        return 1 if not S[self.clave]["jugada"] and self.rivales(S) else None

    def terminada(self, S):
        return bool(S[self.clave]["jugada"])

    def jugar(self, S, P, rng):
        riv = self.rivales(S)
        if S[self.clave]["jugada"] or not riv or not riv[1]:
            return
        E, L = S[self.clave], S[self.LIGA]
        r = dict(zip(L["nombres"], L["r"]))
        a, b = riv
        gl, gv, gana_local, pen = jugar_ko(rng, np.array([r[a]]), np.array([r[b]]), localia=0.0, **P)
        tanda = tanda_penales(rng, bool(gana_local[0])) if pen[0] else None
        p = nuevo_partido(self.nombre, 1, "Final", "Final", a, b, gl[0], gv[0], tanda=tanda,
                          gana=a if gana_local[0] else b, neutral=True)
        E.update(jugada=True, a=a, b=b, campeon=p["gana"], fecha=1)
        E["log"].append(p)

    def cruces(self, S, n):
        riv = self.rivales(S)
        return [(riv[0], riv[1], "Final", "Final")] if riv and not S[self.clave]["jugada"] and riv[1] else []

    def rotulo(self, S, n):
        return "Final"

    def dia(self, S, n):
        return S[self.LIGA]["rondas"][-1]["dia"] + dt.timedelta(days=7)

    def campeon(self, S):
        return S[self.clave]["campeon"]


# El orden importa: es el orden en que "Simular todo" las juega y en que el calendario las lista.
# La Copa do Brasil (y su Supercopa) y la Copa AUF Uruguay van después de las ligas del exterior: la primera se sortea con los clubes de las
# cuatro divisiones de Brasil y la segunda necesita la Segunda ya jugada.
REGISTRO = [CopaArgentina(), SupercopaArgentina(), Regionales(), MundialDeClubes(),
            *[LigaExterior(cfg) for cfg in ligas_ext.LIGAS_EXT], Estaduales(), CopaBrasil(), SupercopaBrasil(), CopaChile(), SupercopaChile(), CopaColombia(),
            CopaUruguay(), SupercopaUruguaya()]
LIGAS_EXTERIOR = [c for c in REGISTRO if isinstance(c, LigaExterior)]
_POR_NOMBRE = {c.nombre: c for c in REGISTRO}


def por_nombre(nombre):
    """La competencia del registro con ese nombre (o None si es una liga u otra copa)."""
    return _POR_NOMBRE.get(nombre)
