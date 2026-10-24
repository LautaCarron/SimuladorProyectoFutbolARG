"""Cómo se juega cada competencia: una sola tabla de despacho y el "Simular todo".

Antes esta lógica estaba duplicada: una cadena de if/elif en motor/calendario.py (para "Próximo día") y un
bloque de bucles `while` pegado en simuladorafa.py (para "Simular todo"). Ahora las dos usan lo mismo.
Este módulo no depende de Streamlit.
"""

from copas.argentina import simular_ronda_copa
from copas.conmebol import CLAVE_INT, simular_ronda_int, terminadas
from copas.registro import REGISTRO, por_nombre
from ligas.federal import simular_fecha_f
from ligas.nacional import simular_fecha_b, total_b
from ligas.primera import primera_terminada, simular_fecha
from ligas.regional import simular_fecha_reg
from ligas.simples import simular_fecha_liga, tabla_pb, tabla_pc, tabla_pd

MAX_PASOS = 10_000            # tope de seguridad: si una competencia no avanza, se corta en vez de colgar la app


def _liga_simple(clave, nombre, tabla):
    return lambda S, P, acumular: simular_fecha_liga(S[clave], P, S["rng"], nombre, tabla)


# nombre de la competencia -> función(S, P, acumular) que juega su próxima fecha
_JUGADORES = {
    "Primera División": lambda S, P, acumular: simular_fecha(S, P, acumular),
    "Primera Nacional": lambda S, P, acumular: simular_fecha_b(S, P),
    "Federal A": lambda S, P, acumular: simular_fecha_f(S["f"], P, S["rng"]),
    "Federal B": lambda S, P, acumular: simular_fecha_f(S["fb"], P, S["rng"]),
    "Primera B": _liga_simple("pb", "Primera B", tabla_pb),
    "Primera C": _liga_simple("pc", "Primera C", tabla_pc),
    "Promocional Amateur": _liga_simple("pd", "Promocional Amateur", tabla_pd),
    "Regional Amateur": lambda S, P, acumular: simular_fecha_reg(S["reg"], P, S["rng"]),
}

# ligas "de una sola categoría" que "Simular todo" juega después de Primera y Nacional, en este orden
_LIGAS_RESTANTES = (("Federal A", "f"), ("Federal B", "fb"), ("Primera B", "pb"), ("Primera C", "pc"),
                    ("Promocional Amateur", "pd"), ("Regional Amateur", "reg"))


def jugar_competencia(S, P, nombre, acumular=True):
    """Juega la próxima fecha / ronda de la competencia `nombre` (liga, copa del registro o CONMEBOL)."""
    jugador = _JUGADORES.get(nombre)
    if jugador:
        jugador(S, P, acumular)
    elif por_nombre(nombre):                       # Copa Argentina, Supercopa, Mundial de Clubes
        por_nombre(nombre).jugar(S, P, S["rng"])
    elif nombre in CLAVE_INT:
        simular_ronda_int(S, CLAVE_INT[nombre], P, S["rng"])
    else:
        raise ValueError(f"Competencia desconocida: {nombre!r}")


def _repetir(terminado, paso, nombre):
    """Repite `paso()` hasta que `terminado()` sea verdadero, con tope de seguridad."""
    for _ in range(MAX_PASOS):
        if terminado():
            return
        paso()
    raise RuntimeError(f"La simulación de {nombre} no avanza (más de {MAX_PASOS} pasos).")


def simular_todo(S, P, acumular=True):
    """Juega todo lo que falta de la temporada, categoría por categoría (el modo Manager usa otro camino: día por día)."""
    # 1. Primera con sus desempates: la B Nacional necesita saber el 27° definitivo para la Promoción
    _repetir(lambda: primera_terminada(S), lambda: simular_fecha(S, P, acumular), "Primera División")
    # 2. Primera Nacional
    _repetir(lambda: S["b"]["fecha"] >= total_b(S["b"]), lambda: simular_fecha_b(S, P), "Primera Nacional")
    # 3. Resto de las categorías (el Federal B sólo existe si se creó desde el Modo dios)
    for nombre, clave in _LIGAS_RESTANTES:
        L = S.get(clave)
        if L is not None:
            _repetir(lambda L=L: L["fecha"] >= L["total"],
                     lambda nombre=nombre: _JUGADORES[nombre](S, P, acumular), nombre)
    # 4. Copa Argentina (se juega en el medio de las ligas; acá se completa lo que falte)
    _repetir(lambda: S["copa"]["ronda"] >= S["copa"]["total"],
             lambda: simular_ronda_copa(S["copa"], P, S["rng"]), "Copa Argentina")
    # 5. Copas del registro (Supercopa y Mundial de Clubes): cada una sabe si le toca jugar ahora
    for comp in REGISTRO:
        comp.jugar_todo(S, P, S["rng"])
    # 6. Copas CONMEBOL (la Sudamericana espera lo que necesita de la Libertadores)
    def _ronda_conmebol():
        for clave in ("rec", "lib", "sud"):
            simular_ronda_int(S, clave, P, S["rng"])
    _repetir(lambda: terminadas(S), _ronda_conmebol, "las copas CONMEBOL")
