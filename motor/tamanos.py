"""Tamaño de las ligas (va en motor/tamanos.py). Sin Streamlit.

Se corre al final del pase de temporada, después de los ascensos y descensos normales, y hace dos cosas:

  * TAMAÑO OBJETIVO (Modo dios): si para una liga se eligió, por ejemplo, 20 equipos, cada temporada se acerca
    a ese número de a PASO equipos como máximo (bajan de más los más flojos o suben de más los mejores de la liga
    de abajo) y, cuando llega, queda fija ahí: desde entonces suben y bajan los que hagan falta para que siempre
    sean 20.
  * PISO: ninguna liga queda con menos de MINIMO equipos, aunque en el Modo dios se pongan muchos ascensos y
    ningún descenso (o al revés). Primero se deshacen los movimientos de más (vuelven los que se iban de esa
    liga) y, si no alcanza, se completa con los de la liga vecina.

Las ligas: p (Primera), b (Primera Nacional), fa (Federal A), fb (Federal B), pb (Primera B), pc (Primera C),
pd (Promocional Amateur) y reg (Regional Amateur, que no tiene objetivo: es la base de la pirámide del interior).
El Promocional es el último escalón de las metropolitanas: si sobran clubes, quedan ahí (su objetivo sólo sirve para
que no le falten equipos).
"""

import math

from datos.equipos import origen

PASO = 4                          # equipos que, como mucho, cambia una liga por temporada para llegar al objetivo
ORDEN = ["p", "b", "fa", "pb", "fb", "pc", "pd"]          # de arriba hacia abajo
NOMBRES = {"p": "Primera División", "b": "Primera Nacional", "fa": "Federal A", "fb": "Federal B",
           "pb": "Primera B", "pc": "Primera C", "pd": "Promocional Amateur", "reg": "Regional Amateur"}
MINIMO = {"p": 14, "b": 20, "fa": 14, "fb": 14, "pb": 14, "pc": 14, "pd": 14, "reg": 60}
MAXIMO = {"p": 48, "b": 60, "fa": 60, "fb": 60, "pb": 40, "pc": 40, "pd": 40}


def objetivos(S):
    """Tamaño objetivo de cada liga elegido en el Modo dios ({clave: int}; sin clave = sin objetivo)."""
    return S.setdefault("cfg", {}).setdefault("tamanos", {})


def meta(actual, objetivo, paso=PASO):
    """Cuántos equipos tiene que tener la liga la temporada que viene para acercarse al objetivo de a `paso`."""
    if objetivo is None:
        return None
    if abs(actual - objetivo) <= paso:
        return objetivo
    return actual + paso if objetivo > actual else actual - paso


def camino(actual, objetivo, paso=PASO):
    """Tamaños temporada por temporada hasta llegar al objetivo (para mostrarlo en el Modo dios)."""
    out = [actual]
    while out[-1] != objetivo and len(out) < 40:
        out.append(meta(out[-1], objetivo, paso))
    return out


class _Piramide:
    """Las listas de equipos de la temporada que viene y quién está arriba / abajo de quién."""

    def __init__(self, S, listas, hay_fb):
        self.S, self.L, self.hay_fb = S, listas, hay_fb
        self.movidos = []                      # (club, de, a, motivo) para el Historial

    def r(self, n):
        return self.S["rating"].get(n, 50.0)

    def arriba(self, k):
        return {"b": "p", "fa": "b", "pb": "b", "fb": "fa", "pc": "pb", "pd": "pc",
                "reg": "fb" if self.hay_fb else "fa"}.get(k)

    def abajo(self, k, club=None):
        if k == "b":
            if club is None:
                return ["fa", "pb"]
            return "fa" if origen(club) == "Interior" else "pb"
        d = {"p": "b", "fa": "fb" if self.hay_fb else "reg", "fb": "reg", "pb": "pc", "pc": "pd"}.get(k)
        return d if club is not None else ([d] if d else [])

    def mover(self, club, de, a, motivo):
        self.L[de].remove(club)
        self.L[a].append(club)
        self.movidos.append((club, de, a, motivo))

    def puede_ceder(self, k, cuantos=1):
        """¿La liga k puede quedarse con `cuantos` equipos menos sin bajar de su piso?"""
        return len(self.L[k]) - cuantos >= MINIMO[k]

    def puede_recibir(self, k):
        return k not in MAXIMO or len(self.L[k]) < MAXIMO[k]


def ajustar(S, listas, viejas, hay_fb):
    """Corrige las listas de la temporada que viene (`listas`: clave -> lista de clubes, se modifican en el lugar).
    `viejas`: las listas de la temporada que termina (para saber quién jugaba dónde). Devuelve los movimientos
    hechos: [(club, de, a, motivo)]."""
    P = _Piramide(S, listas, hay_fb)
    obj = objetivos(S)
    claves = [k for k in ORDEN if k in listas and (k != "fb" or hay_fb)]

    # ---- 1. tamaño objetivo, de arriba hacia abajo
    for k in claves:
        T = obj.get(k)
        if T is None:
            continue
        T = max(MINIMO[k], min(MAXIMO[k], int(T)))
        m = meta(len(viejas.get(k) or listas[k]), T)
        sobran = len(listas[k]) - m
        if sobran > 0:
            # bajan de más los más flojos (primero los que jugaron acá esta temporada, no los recién llegados)
            cand = sorted(listas[k], key=lambda n: (n not in (viejas.get(k) or []), P.r(n)))
            for n in cand:
                if sobran <= 0:
                    break
                destino = P.abajo(k, n)
                if destino is None:                  # el Promocional es el último escalón: los que sobran quedan ahí
                    break
                if destino not in listas or not P.puede_recibir(destino):
                    continue
                P.mover(n, k, destino, "tamaño objetivo")
                sobran -= 1
        elif sobran < 0:
            # suben de más los mejores de la liga de abajo (los que jugaron allá, no los que recién bajaron)
            fuentes = [x for x in P.abajo(k) if x in listas]
            cand = sorted(((n, f) for f in fuentes for n in listas[f]),
                          key=lambda nf: (nf[0] in (viejas.get(k) or []), -P.r(nf[0])))
            for n, f in cand:
                if sobran >= 0:
                    break
                if not P.puede_ceder(f):
                    continue
                P.mover(n, f, k, "tamaño objetivo")
                sobran += 1

    # ---- 2. piso: ninguna liga por debajo de su mínimo (de abajo hacia arriba, dos pasadas por las cascadas)
    def ceder(v, prof=0):
        """Deja a la liga v en condiciones de ceder un equipo: si está en su mínimo, primero recibe uno de la liga
        de arriba (en cadena: si la de arriba también está justa, ella recibe de la suya)."""
        if P.puede_ceder(v):
            return True
        a = P.arriba(v)
        if a is None or a not in listas or prof > 8 or not ceder(a, prof + 1):
            return False
        # de la B sólo bajan al Federal A los del interior y a la Primera B los metropolitanos
        eleg = [n for n in listas[a] if a != "b" or P.abajo("b", n) == v]
        if not eleg:
            return False
        eran = set(viejas.get(v) or [])
        n = min(eleg, key=lambda x: (x not in eran, P.r(x)))      # primero los que acaban de subir desde v
        P.mover(n, a, v, "mínimo de equipos")
        return True

    def ceder_abajo(v, prof=0):
        """Igual que ceder(), pero la liga v (que está debajo) se repone con el mejor de su liga de abajo."""
        if P.puede_ceder(v):
            return True
        if prof > 8:
            return False
        for d in P.abajo(v):
            if d not in listas or not ceder_abajo(d, prof + 1):
                continue
            eleg = [n for n in listas[d] if v != "b" or P.abajo("b", n) == d]
            if eleg:
                P.mover(max(eleg, key=P.r), d, v, "mínimo de equipos")
                return True
        return False

    for _ in range(3):
        for k in reversed(claves):
            falta = MINIMO[k] - len(listas[k])
            if falta <= 0:
                continue
            eran = set(viejas.get(k) or [])
            arr = P.arriba(k)
            vecinos = [v for v in [arr, *P.abajo(k)] if v in listas]
            # a) vuelven los que se fueron de esta liga (primero los que subieron, el más flojo primero)
            cand = [(n, v) for v in vecinos for n in listas[v] if n in eran]
            cand.sort(key=lambda nv: (nv[1] != arr, P.r(nv[0]) if nv[1] == arr else -P.r(nv[0])))
            # b) si no alcanza, los mejores de abajo y, por último, los más flojos de arriba
            abajo = [(n, v) for v in P.abajo(k) if v in listas for n in sorted(listas[v], key=P.r, reverse=True)]
            arriba = ([(n, arr) for n in sorted(listas[arr], key=P.r) if arr != "b" or P.abajo("b", n) == k]
                      if arr in listas else [])
            for n, v in cand + abajo + arriba:
                if falta <= 0:
                    break
                if n not in listas[v]:
                    continue
                if not P.puede_ceder(v) and not (ceder(v) if v == arr else ceder_abajo(v)):
                    continue
                if n not in listas[v]:                      # ceder() pudo haber movido justo a este
                    continue
                P.mover(n, v, k, "mínimo de equipos")
                falta -= 1
    return P.movidos


# ---------------------------------------------------------------- ascensos y descensos parejos
REG_ASC = 6                       # el Regional Amateur sube siempre 6 (los ganadores de las finales)


def intercambio(n):
    """Cuántos equipos razonable que cambien por año entre una liga de `n` equipos y la de abajo: 2 con 14,
    3 con 20, 4 con 30, 5 con 36 y hasta 6."""
    return max(2, min(6, round(n / 7)))


def plan_equilibrado(S, tamanos=None):
    """Con tamaño objetivo, los ascensos y descensos se acomodan solos y quedan parejos: entre cada liga y la de
    abajo bajan tantos como suben, en una cantidad razonable para el tamaño de la liga (ver `intercambio`).
    Así, cuando una liga llega a su tamaño, ya no hacen falta movimientos de más para mantenerla.

    Sólo toca las fronteras de las ligas que tienen objetivo. El reducido que se haya elegido se respeta: si hay
    reducido, los ascensos directos son uno menos. Devuelve {clave: texto} con lo que quedó (para el Modo dios)."""
    from ligas.federal import cfg_federal
    from ligas.nacional import asc_elegido, cfg_b, formato_efectivo
    from ligas.primera import DESCENSOS_MAX, cfg_primera
    from ligas.simples import cfg_simple

    obj = objetivos(S)
    if not obj:
        return {}
    hay_fb = bool(S.get("fb"))
    tam = dict(tamanos or {})
    actual = {"p": len(S["nombres"]), "b": len(S["b"]["nombres"]), "fa": len(S["f"]["nombres"]),
              "fb": len(S["fb"]["nombres"]) if hay_fb else 0, "pb": len(S["pb"]["nombres"]),
              "pc": len(S["pc"]["nombres"]), "pd": len(S["pd"]["nombres"])}
    for k, v in actual.items():
        tam.setdefault(k, obj.get(k, v))

    def con(*claves):                     # ¿alguna de estas ligas tiene objetivo?
        return any(k in obj for k in claves)

    def ascensos(c, total):               # total de ascensos: directos + (1 si hay reducido)
        total = max(0, int(total))
        red = bool(c.get("reducido")) and total > 0
        c["reducido"], c["directos"] = red, total - int(red)

    # Primera <-> B Nacional
    if con("p", "b"):
        k = min(DESCENSOS_MAX, intercambio(tam["p"]))
        cfg_primera(S)["descensos"] = k
        cb = cfg_b(S)
        _, r, _ = asc_elegido(S, formato_efectivo(len(S["b"]["nombres"]), cb["formato"]))
        cb["reducido"] = bool(r)
        ascensos(cb, k)
    # B Nacional <-> Federal A (los del interior) y Primera B (los metropolitanos)
    if con("b", "fa", "pb"):
        k = intercambio(tam["b"])
        al_fa, al_pb = max(2, math.ceil(k / 2)), max(2, k // 2)     # de cada una suben al menos 2
        cfg_b(S)["descensos"] = al_fa + al_pb
        ascensos(cfg_federal(S), al_fa)
        ascensos(cfg_simple(S, "pb"), al_pb)
    # Federal A <-> Federal B (si existe) y Federal B <-> Regional; sin Federal B, Federal A <-> Regional
    if hay_fb:
        if con("fa", "fb"):
            k = intercambio(tam["fa"])
            cfg_federal(S)["descensos"] = k
            ascensos(cfg_federal(S, "federal_b"), k)
        if con("fb"):
            cfg_federal(S, "federal_b")["descensos"] = REG_ASC
    elif con("fa"):
        cfg_federal(S)["descensos"] = REG_ASC
    # Primera B <-> Primera C <-> Promocional
    if con("pb", "pc"):
        k = intercambio(tam["pb"])
        cfg_simple(S, "pb")["descensos"] = k
        ascensos(cfg_simple(S, "pc"), k)
    if con("pc", "pd"):
        k = intercambio(tam["pc"])
        cfg_simple(S, "pc")["descensos"] = k
        ascensos(cfg_simple(S, "pd"), k)
    return tam
