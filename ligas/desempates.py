"""Piezas comunes de los desempates por puntos (las usan Primera, la B Nacional y las ligas simples)."""


def bloque_empatado(pts, idx):
    """Bloque de equipos igualados en puntos con el del índice `idx` (tabla ordenada): devuelve (inicio, fin)."""
    inicio = idx
    while inicio > 0 and pts[inicio - 1] == pts[idx]:
        inicio -= 1
    fin = idx + 1
    while fin < len(pts) and pts[fin] == pts[idx]:
        fin += 1
    return inicio, fin


def duelo_o_liguilla(ids_bloque):
    """Cómo se desempata el bloque: con 2 equipos un duelo ("Duelo", (a, b)); con 3 o más una liguilla todos contra
    todos ("Liguilla", (a, a): el par sólo marca que hay un desempate de ese bloque)."""
    if len(ids_bloque) == 2:
        return "Duelo", (ids_bloque[0], ids_bloque[1])
    return "Liguilla", (ids_bloque[0], ids_bloque[0])
