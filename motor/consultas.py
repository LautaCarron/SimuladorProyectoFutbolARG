"""Consultas sobre los partidos (jugados y por jugar) de cada competencia. Sin Streamlit.

Antes vivían en ui/vista/partidos.py y leían `st.session_state.S` a escondidas; ahora todas reciben el estado `S`
por parámetro. La interfaz las usa a través de los envoltorios de ui/vista/partidos.py.
"""

from copas.conmebol import FIX4, CLAVE_INT, GRUPOS, PAIS_EXT
from copas.registro import REGISTRO, por_nombre
from datos.clubes_mundial import PAIS_MUNDIAL
from datos.equipos import F_GRUPOS_NOMBRES
from ligas.apertura_clausura import competencia as ac_competencia
from ligas.federal import rotulo_f
from ligas.nacional import B_ZONAS2, b_f1, b_f2, es_anual_b, rotulo_b, total_base_b
from ligas.primera import ZONAS, fechas_f1, formato, rotulo_p, total_base
from ligas.regional import rotulo_reg


def pendiente(liga, n, rotulo, comp, local, visita):
    """Partido todavía sin jugar (mismo formato que los del log, con el resultado en None)."""
    return {"liga": liga, "fecha": n, "rotulo": rotulo, "comp": comp, "local": local,
            "visita": visita, "gl": None, "gv": None, "gana": None, "tanda": None,
            "pen": None, "neutral": False}


# ---- Todos los partidos jugados y a qué categoría pertenece cada club --------------------------------
def todos_los_partidos(S):
    return (S["log"] + S["b"]["log"] + S["f"]["log"] + (S["fb"]["log"] if S.get("fb") else [])
            + S["pb"]["log"] + S["pc"]["log"] + S["pd"]["log"] + S["reg"]["log"]
            + [p for comp in REGISTRO for p in comp.log(S)]
            + [p for C in S.get("int", {}).values() for p in C["log"]])


def partidos_club(S, club):
    """Partidos ya jugados del club, en cualquier competencia."""
    return [p for p in todos_los_partidos(S) if club in (p["local"], p["visita"])]


def categoria_arg(S, nombre):
    """Categoría argentina del club ("" si no es de ninguna)."""
    if nombre in S["nombres"]:
        return "Primera División"
    if nombre in S["b"]["nombres"]:
        return "Primera Nacional"
    if nombre in S["federal"]:
        return "Federal A"
    if nombre in S.get("federal_b", []):
        return "Federal B"
    if nombre in S["primera_b"]:
        return "Primera B"
    if nombre in S["primera_c"]:
        return "Primera C"
    if nombre in S.get("promocional", []):
        return "Promocional Amateur"
    if nombre in S["reg"]["nombres"]:
        return "Regional Amateur"
    return ""


def categoria_de(S, nombre):
    """Categoría (clubes argentinos) o país (clubes del exterior)."""
    return categoria_arg(S, nombre) or PAIS_EXT.get(nombre) or PAIS_MUNDIAL.get(nombre)


# ---- Fechas de cada liga: jugadas y por jugar ----------------------------------------------------------
def fechas_conocidas_p(S):
    return len(S["fechas"])


def partidos_fecha_p(S, n):
    if n <= S["fecha"]:
        return [p for p in S["log"] if p["fecha"] == n]
    nom = S["nombres"]
    f = formato(S)

    def competencia(x, y):
        """Según el formato: fase 1, zona de la fase 2, zona del Apertura/Clausura, llaves o desempate."""
        if f == "apertura_clausura":
            return ac_competencia(S, n, x, y)
        if n > total_base(S):
            return "Desempate"
        if f != "actual":
            return "Liga"
        if n <= fechas_f1(S):
            return "Fase 1"
        return f"Zona {ZONAS[S['zona_de'][x]]}"

    return [pendiente("Primera División", n, rotulo_p(S, n), competencia(x, y), nom[x], nom[y])
            for x, y in S["fechas"][n - 1]]


def fechas_conocidas_b(S):
    SB = S["b"]
    if es_anual_b(SB):
        return max(SB["fecha"], total_base_b(SB))
    return max(SB["fecha"], b_f1(SB) if SB["fechas2"] is None else b_f1(SB) + len(SB["fechas2"]))


def partidos_fecha_b(S, n):
    SB = S["b"]
    if n <= SB["fecha"]:
        return [p for p in SB["log"] if p["fecha"] == n]
    nom = SB["nombres"]
    if es_anual_b(SB):
        return [pendiente("Primera Nacional", n, rotulo_b(SB, n), "Liga", nom[x], nom[y])
                for x, y in SB["fechas"][n - 1]] if n <= total_base_b(SB) else []
    f1, f2 = b_f1(SB), b_f2(SB)
    if n <= f1:
        return [pendiente("Primera Nacional", n, rotulo_b(SB, n), f"Zona {'AB'[SB['zona_de'][x]]}",
                          nom[x], nom[y]) for x, y in SB["fechas"][n - 1]]
    return [pendiente("Primera Nacional", n, rotulo_b(SB, n),
                      f"Zona {B_ZONAS2[SB['zona2_de'][x]]}" if n <= f1 + f2 else "Desempate Permanencia", nom[x], nom[y])
            for x, y in SB["fechas2"][n - 1 - f1]]


def fechas_conocidas_f(SF):
    """`SF`: la liga con formato Federal (el Federal A o el Federal B)."""
    return max(SF["fecha"], SF["f1_rondas"] if SF["fechas2"] is None else SF["f1_rondas"] + SF.get("f2_rondas", 0))


def partidos_fecha_f(SF, n):
    if n <= SF["fecha"]:
        return [p for p in SF["log"] if p["fecha"] == n]
    nom, liga = SF["nombres"], SF.get("liga", "Federal A")
    if n <= SF["f1_rondas"]:
        return [pendiente(liga, n, rotulo_f(SF, n), f"Zona {F_GRUPOS_NOMBRES[SF['grupo_de'][x]]}",
                          nom[x], nom[y]) for x, y in SF["fechas"][n - 1]]
    return [pendiente(liga, n, rotulo_f(SF, n),
                      "Campeonato" if SF["zona2_de"][x] == 0 else "Descenso", nom[x], nom[y])
            for x, y in SF["fechas2"][n - 1 - SF["f1_rondas"]]]


def fechas_conocidas_simple(L):
    return L["total"]


def partidos_fecha_simple(L, n, liga, rotulo=None, comp="Liga"):
    """Primera B, Primera C y Promocional: `rotulo` y `comp` los puede fijar quien llama (desempates de la B)."""
    if n <= L["fecha"]:
        return [p for p in L["log"] if p["fecha"] == n]
    nom = L["nombres"]
    return [pendiente(liga, n, rotulo or f"Fecha {n}", comp, nom[x], nom[y]) for x, y in L["fechas"][n - 1]]


def partidos_fecha_pb(S, n):
    SPB = S["pb"]
    rotulo, comp = f"Fecha {n}", "Liga"
    if SPB.get("desempate") and n > SPB["desempate"]["inicio"]:
        rotulo, comp = f"Desempate (F. {n - SPB['desempate']['inicio']})", "Desempate"
    return partidos_fecha_simple(SPB, n, "Primera B", rotulo, comp)


def partidos_fecha_pc(S, n):
    return partidos_fecha_simple(S["pc"], n, "Primera C")


def partidos_fecha_pd(S, n):
    return partidos_fecha_simple(S["pd"], n, "Promocional Amateur")


def fechas_conocidas_reg(S):
    return S["reg"]["total"]


def partidos_fecha_reg(S, n, region=None):
    """Partidos de la fecha n del Regional (jugados o por jugar). Con `region`, sólo los de
    esa región (en zonas compartidas, los partidos donde juega algún club de la región)."""
    SR = S["reg"]
    nom = SR["nombres"]
    if n <= SR["fecha"]:
        lista = [p for p in SR["log"] if p["fecha"] == n]
    elif n <= SR["f_liga"]:
        lista = []
        for x, y in SR["fechas"][n - 1]:
            p = pendiente("Regional Amateur", n, rotulo_reg(SR, n), f"Región {SR['zona_de'][x]}",
                          nom[x], nom[y])
            p["region"] = SR["region_de"][x]
            lista.append(p)
    else:
        lista = []                                   # desempates y finales: se arman al terminar la liga
    if region is None:
        return lista
    return [p for p in lista if region in {p["region"]} | set(p["region"].split(" / "))]


# (liga, partidos de la fecha n, hasta qué fecha se conocen los cruces) por competencia, para buscar el próximo partido
_COMPETENCIAS_DE_LIGA = (
    (lambda S: S, partidos_fecha_p, fechas_conocidas_p),
    (lambda S: S["b"], partidos_fecha_b, fechas_conocidas_b),
    (lambda S: S["f"], lambda S, n: partidos_fecha_f(S["f"], n), lambda S: fechas_conocidas_f(S["f"])),
    (lambda S: S.get("fb"), lambda S, n: partidos_fecha_f(S["fb"], n), lambda S: fechas_conocidas_f(S["fb"])),
    (lambda S: S["pb"], partidos_fecha_pb, lambda S: fechas_conocidas_simple(S["pb"])),
    (lambda S: S["pc"], partidos_fecha_pc, lambda S: fechas_conocidas_simple(S["pc"])),
    (lambda S: S.get("pd"), partidos_fecha_pd, lambda S: fechas_conocidas_simple(S["pd"])),
    (lambda S: S["reg"], partidos_fecha_reg, lambda S: S["reg"]["f_liga"]),
)


def proximo_partido(S, nombre):
    """Próximo partido sin jugar del club en su liga (None si no tiene ninguno conocido)."""
    for liga_de, partidos_fecha, conocidas in _COMPETENCIAS_DE_LIGA:
        L = liga_de(S)
        if L and nombre in L["nombres"]:
            for n in range(L["fecha"] + 1, conocidas(S) + 1):
                for p in partidos_fecha(S, n):
                    if nombre in (p["local"], p["visita"]):
                        return p
            return None
    return None


# ---- Copas -----------------------------------------------------------------------------------------------
def int_pendientes(C, n):
    """Partidos por jugar de la ronda n de una copa CONMEBOL (si ya se conocen los cruces)."""
    etapa = C["rondas"][n - 1]
    liga = C["nombre"]
    if etapa.startswith("Grupos"):
        if C["grupos"] is None:
            return []
        f = int(etapa.split()[-1]) - 1
        return [pendiente(liga, n, etapa, f"Grupo {GRUPOS[g]}", eq[i], eq[j])
                for g, eq in enumerate(C["grupos"]) for i, j in FIX4[f]]
    fase = "Recopa" if liga == "Recopa Sudamericana" else etapa.split(" · ")[0]
    series = C["llaves"].get("Final" if liga == "Recopa Sudamericana" else fase)
    if not series:
        return []
    if etapa == "Final":
        return [dict(pendiente(liga, n, etapa, "Final", series[0]["a"], series[0]["b"]), neutral=True)]
    ida = etapa.endswith("ida") or etapa == "Ida"
    return [pendiente(liga, n, etapa, fase, x["b"], x["a"]) if ida else pendiente(liga, n, etapa, fase, x["a"], x["b"])
            for x in series]


def partidos_de_calendario(S, liga, n):
    """Partidos (jugados o por jugar) de la fecha n de una liga, o la ronda n de una copa."""
    if liga in CLAVE_INT:
        C = S["int"][CLAVE_INT[liga]]
        return [p for p in C["log"] if p["fecha"] == n] or int_pendientes(C, n)
    comp = por_nombre(liga)
    if comp:                                       # Copa Argentina, Supercopa, Mundial de Clubes
        hechos = [p for p in comp.log(S) if p["fecha"] == n]
        return hechos or [pendiente(liga, n, rot, cmp_, a, b) for a, b, rot, cmp_ in comp.cruces(S, n)]
    obtener = {"Primera División": partidos_fecha_p, "Primera Nacional": partidos_fecha_b,
               "Federal A": lambda S, n: partidos_fecha_f(S["f"], n),
               "Federal B": lambda S, n: partidos_fecha_f(S["fb"], n),
               "Primera B": partidos_fecha_pb, "Primera C": partidos_fecha_pc,
               "Promocional Amateur": partidos_fecha_pd, "Regional Amateur": partidos_fecha_reg}[liga]
    try:
        return obtener(S, n)
    except (IndexError, KeyError, TypeError):
        return []
