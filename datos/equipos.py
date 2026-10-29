"""Datos: equipos, medias, escudos, origen y región de cada club.

Es el único archivo que hay que tocar para cambiar planteles, medias iniciales o
escudos. No tiene lógica de simulación.
"""

from datos.cargador import cargar
from datos.clubes_int import CLUBES_INT, OSCUROS_INT
from datos.datos_regional import GRUPO_FEDERAL_REG, REGIONAL
from datos.clubes_mundial import MUNDIAL_CLUBES
from datos.clubes_interior import DATOS_INTERIOR, datos_club  # noqa: F401  (ciudad, provincia y liga)

# ----------------------------------------------------------------------------
# DATOS: equipos reales de la temporada 2026 (medias orientativas, escala ~40-95).
# Primera: 30 equipos (ESPN, Liga Profesional 2026) · Primera Nacional: 36 (ESPN,
# Primera Nacional 2026) · debajo de la Primera Nacional el fútbol argentino se divide
# geográficamente: Federal A (clubes del interior, indirectamente afiliados) y Primera B
# (clubes metropolitanos, CABA/Gran Buenos Aires, directamente afiliados). Debajo de la
# Primera B está la Primera C. Todas las categorías se simulan (ver ligas/ y motor/temporada.py).
# ----------------------------------------------------------------------------
_EQ = cargar("equipos")        # datos/json/equipos.json
EQUIPOS = _EQ["primera"]
EQUIPOS_B = _EQ["nacional"]
# Federal A (interior): ascienden 4 a la Primera Nacional (1°, 2°, 3° y el campeón del
# reducido) y bajan a esta categoría los descendidos de la B que sean del interior.
EQUIPOS_FEDERAL = _EQ["federal_a"]
# Primera B (Metropolitana): clubes de CABA / Gran Buenos Aires. Es el equivalente del
# Federal A pero para el lado metropolitano: liga todos contra todos ida y vuelta, ascienden
# 2 a la Primera Nacional y bajan 2 a la Primera C.
EQUIPOS_PRIMERA_B = _EQ["primera_b"]
# Primera C (Metropolitana)
EQUIPOS_PRIMERA_C = _EQ["primera_c"]
# Torneo Promocional Amateur (Primera D)
EQUIPOS_PRIMERA_D = _EQ["primera_d"]

# Torneo Regional Amateur: 316 clubes en 12 regiones (datos completos en datos/datos_regional.py,
# generado del JSON oficial del torneo). Acá sólo nombre -> media inicial.
EQUIPOS_REGIONAL = {x["nombre"]: x["media"] for x in REGIONAL}


# Escudos oficiales: ESPN (Primera y Primera Nacional), Wikimedia Commons / Wikipedia y
# TheSportsDB (Federal A). Van ligados al nombre: si un club cambia de categoría,
# conserva su nombre y su escudo.
_ESC = cargar("escudos")      # datos/json/escudos.json
ESCUDOS = dict(_ESC["clubes"])
# Regional Amateur: escudos del JSON del torneo (interiorfutbolero.com.ar)
ESCUDOS.update({x["nombre"]: x["escudo"] for x in REGIONAL})
# Clubes de los otros países de la CONMEBOL (copas internacionales)
ESCUDOS.update({n: url for n, _, _, url in CLUBES_INT})
# Si la fila tiene 5 elementos, agarra el nombre (x[0]) y la URL del escudo (x[4])
ESCUDOS.update({x[0]: x[4] for x in MUNDIAL_CLUBES if len(x) >= 5})

# Escudos de borde oscuro (negro, bordó, azul marino): en modo oscuro se les dibuja un
# contorno claro para que no se pierdan contra el fondo (p. ej. Central Norte).
ESCUDOS_OSCUROS = set(_ESC["oscuros"])
ESCUDOS_OSCUROS |= set(OSCUROS_INT)

# Escudos que vienen con fondo blanco: se les saca el fondo (ver imagenes.py). Si otro escudo se ve con fondo, sumá
# acá su nombre; si querés usar un PNG transparente propio, copialo en datos/escudos_sin_fondo/ con el nombre del
# club en minúsculas y con guiones (por ejemplo sarmiento-leones.png).
from datos.imagenes import escudos_sin_fondo, slug
ESCUDOS_SIN_FONDO = escudos_sin_fondo(ESCUDOS, _ESC["sin_fondo"])
ESCUDOS_CSS = "<style>" + "".join(
    f".cr-{slug(n)}{{background-image:url({u});}}" for n, u in ESCUDOS_SIN_FONDO.items()) + "</style>"

# Origen geográfico real de cada club: "Interior" o "Metropolitana" (CABA / Gran
# Buenos Aires). Sirve para mandar a cada equipo a su categoría real (Federal A o
# Primera B) el día que descienda del todo. Los del Federal A ya son todos del
# interior y los de Primera B ya son todos metropolitanos, así que acá sólo hace
# falta etiquetar a mano los de Primera y Primera Nacional.
_GEO = cargar("geografia")     # datos/json/geografia.json
ORIGEN = _GEO["origen"]


def origen(nombre):
    from datos import club_propio
    if (propio := club_propio.origen(nombre)):          # club propio: el que eligió la persona
        return propio
    if nombre in EQUIPOS_FEDERAL or nombre in EQUIPOS_REGIONAL:
        return "Interior"
    if nombre in EQUIPOS_PRIMERA_B or nombre in EQUIPOS_PRIMERA_C or nombre in EQUIPOS_PRIMERA_D:
        return "Metropolitana"
    return ORIGEN.get(nombre, "Interior")


# Región de cada club del Federal A (y de cualquier club "Interior" de Primera o la
# Primera Nacional que algún día pueda terminar ahí): sirve para armar los 5 grupos
# de la fase 1 "por cercanía". Los que no están acá caen en "Centro" por defecto.
F_GRUPOS_NOMBRES = _GEO["grupos_federal"]
REGION = dict(_GEO["grupo_federal"])


# Clubes del Regional Amateur: si ascienden, van al grupo del Federal A de su región
REGION.update({x["nombre"]: GRUPO_FEDERAL_REG[x["region"]] for x in REGIONAL})


def region_de(nombre):
    from datos import club_propio
    if (reg := club_propio.region(nombre)):             # club propio: el grupo del Federal A de su región
        return GRUPO_FEDERAL_REG[reg]
    return REGION.get(nombre, "Centro")


# Región del Torneo Regional Amateur (una de las 12 del JSON) de cada club del interior que
# no está en el JSON: los del Federal A y los del interior de Primera y la Primera Nacional.
# Es la liga que juegan si algún día descienden al Regional (se respeta su provincia/ciudad).
REGION_REGIONAL = dict(_GEO["region_regional"])
REGION_REGIONAL.update({x["nombre"]: x["region"] for x in REGIONAL})
# Si aparece un club del interior sin región del Regional asignada, va a la región del
# Regional que corresponde a su grupo del Federal A
_GRUPO_A_REGION = _GEO["grupo_a_region"]


def region_regional(nombre):
    from datos import club_propio
    return club_propio.region(nombre) or REGION_REGIONAL.get(nombre) or _GRUPO_A_REGION.get(region_de(nombre), "Centro")


N = len(EQUIPOS)            # Primera
NB = len(EQUIPOS_B)         # Primera Nacional
NF = len(EQUIPOS_FEDERAL)   # Federal A
NPB = len(EQUIPOS_PRIMERA_B)  # Primera B
NPC = len(EQUIPOS_PRIMERA_C)  # Primera C
NPD = len(EQUIPOS_PRIMERA_D)  # TPA (Primera D)

ERROR_DATOS = None        # texto del error si los datos no cierran (lo muestra la interfaz)
_todos = (list(EQUIPOS) + list(EQUIPOS_B) + list(EQUIPOS_FEDERAL) + list(EQUIPOS_PRIMERA_B)
          + list(EQUIPOS_PRIMERA_C) + list(EQUIPOS_PRIMERA_D) + [x["nombre"] for x in REGIONAL])
_sin_datos = [n for n in [*EQUIPOS, *EQUIPOS_B, *EQUIPOS_FEDERAL] if origen(n) == "Interior" and datos_club(n) is None]
if _sin_datos:
    ERROR_DATOS = "Faltan ciudad/provincia/liga de clubes del interior: " + ", ".join(_sin_datos)
elif N != 30 or NB != 36 or NF < 6 or NPB < 6 or NPC < 6 or NPD < 6 or len(set(_todos)) != len(_todos):
    ERROR_DATOS = "Hay un error en la cantidad de equipos o nombres repetidos."