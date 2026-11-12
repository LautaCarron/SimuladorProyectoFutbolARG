"""Ligas de otros países: motor genérico (Uruguay hoy; Brasil y las demás después).

Una liga del exterior es una lista de RONDAS que se juegan de a una, en orden. Cada ronda trae sus cruces (o todavía
no, si dependen de lo que pase antes: el Intermedio uruguayo necesita la tabla final del Apertura), su día y a qué
tabla suma. El motor sabe:

  * armar ruedas todos contra todos y espejarlas (`rueda`, `espejo`),
  * jugar la próxima ronda, de liga o eliminatoria, y anotar los partidos (`jugar_ronda`),
  * llevar las estadísticas de cada torneo y armar sus tablas (`stats_vacias`, `tabla`),
  * elegir el formato según la configuración de la liga (`FORMATOS`).

Cada FORMATO (ligas/uruguay.py, ligas/uruguay_segunda.py, ligas/uruguay_amateur.py, ligas/brasil_d.py y
`TodosContraTodos` más abajo, el de las Séries A y B de Brasil) decide qué rondas hay, qué tablas
muestra y quién sale campeón, asciende y desciende. El estado de la liga (`L`) es un diccionario común y corriente
(números, textos, listas, arrays y fechas), así que se guarda en el `.afa` sin tocar motor/guardado.py.

Lo conecta con el resto del simulador copas/registro.py (clase `LigaExterior`): el calendario, "Simular todo", el
historial y el progreso ya recorren ese registro. Sin Streamlit: es motor puro.
"""

import datetime as dt

import numpy as np

from motor.fechas import desde
from motor.nucleo import (LOCALIA, STATS, df_stats, generar_fixture, jugar, jugar_ko, nuevo_partido, sumar_partidos,
                          tanda_penales)

UNA_SEMANA = dt.timedelta(weeks=1)
def stats_vacias(n):
    """Estadísticas en cero de un torneo de n equipos (las mismas claves que usan df_stats y sumar_partidos)."""
    return {k: np.zeros(n, dtype=int) for k in STATS}


def sumar_stats(*estadisticas):
    """Suma torneo a torneo (por ejemplo: Apertura + Intermedio + Clausura = tabla anual)."""
    return {k: sum(E[k] for E in estadisticas) for k in STATS}


def rueda(rng, ids):
    """Todos contra todos, una vuelta, entre los equipos `ids`. El orden de los equipos se sortea, así los clásicos no
    caen siempre en la misma fecha. Devuelve una lista de fechas; cada fecha es una lista de (local, visita)."""
    ids = [int(i) for i in ids]
    orden = [ids[i] for i in rng.permutation(len(ids))]
    return [[(orden[a], orden[b]) for a, b in fecha] for fecha in generar_fixture(len(ids))]


def espejo(fechas):
    """La misma rueda con las localías invertidas (la revancha: segunda rueda, Clausura)."""
    return [[(v, l) for l, v in fecha] for fecha in fechas]


def dias_semanales(anio, inicio, cantidad):
    """`cantidad` días, uno por semana, desde la primera fecha de `inicio` = [mes, día, día de la semana]."""
    primero = desde(anio, inicio[0], inicio[1], inicio[2])
    return [primero + k * UNA_SEMANA for k in range(cantidad)]
def dias_cada(anio, inicio, cantidad, paso):
    """`cantidad` días, uno cada `paso` días, desde la primera fecha de `inicio` = [mes, día, día de la semana].
    Sirve para los torneos cortos que meten fechas entre semana (Apertura y Clausura de Paraguay: 22 fechas en 4 meses)."""
    primero = desde(anio, inicio[0], inicio[1], inicio[2])
    return [primero + dt.timedelta(days=k * paso) for k in range(cantidad)]


def ronda(etapa, rotulo, comp, dia, pares=None, suma=None, ko=False, neutral=False, ida_vuelta=None):
    """Una ronda de la liga.

    etapa      nombre interno de la etapa ("Apertura", "Semifinal"...): el formato lo usa para saber qué se completó.
    rotulo     lo que se lee en el fixture ("Apertura · fecha 3").
    comp       la competencia que muestra el partido ("Apertura", "Intermedio · Grupo A", "Final"...).
    dia        datetime.date en que se juega.
    pares      [(id local, id visita)]; None mientras los cruces dependan de rondas anteriores.
    suma       clave del torneo (en L["E"]) al que le cuentan estos partidos para la tabla; None si no cuentan
               (finales, desempates).
    ko         eliminatoria a partido único: si empatan, penales.
    neutral    cancha neutral (sin ventaja de local).
    ida_vuelta "ida" o "vuelta" en una serie a doble partido: el que define es el global, no cada partido.
    """
    return {"etapa": etapa, "rotulo": rotulo, "comp": comp, "dia": dia, "pares": pares, "suma": suma, "ko": ko,
            "neutral": neutral, "ida_vuelta": ida_vuelta}


def comp_de(R, local):
    """Competencia que se anota en el partido: la de la ronda o, si la ronda juega por grupos (Intermedio uruguayo),
    la del grupo del local (R["grupo_de"] = {id de equipo: texto})."""
    grupo = R.get("grupo_de")
    return grupo[local] if grupo else R["comp"]


def jugar_ronda(L, P, rng):
    """Juega la próxima ronda de la liga, anota los partidos en L["log"] y suma a las estadísticas que corresponda.
    Devuelve la lista de partidos jugados. No decide nada de lo que viene después: eso lo hace el formato."""
    n = L["fecha"] + 1
    R = L["rondas"][n - 1]
    if not R["pares"]:
        raise RuntimeError(f"{L['nombre']}: la ronda {n} ({R['rotulo']}) todavía no tiene cruces")
    h = np.array([x[0] for x in R["pares"]])
    a = np.array([x[1] for x in R["pares"]])
    r, nom = L["r"], L["nombres"]
    partidos = []
    if R["ko"]:
        gl, gv, gana_local, pen = jugar_ko(rng, r[h], r[a], localia=0.0 if R["neutral"] else LOCALIA, **P)
        for x, y, g1, g2, gl_, pe in zip(h, a, gl, gv, gana_local, pen):
            tanda = tanda_penales(rng, bool(gl_)) if pe else None
            partidos.append(nuevo_partido(L["nombre"], n, R["rotulo"], R["comp"], nom[x], nom[y], g1, g2, tanda=tanda,
                                          gana=nom[x] if gl_ else nom[y], neutral=R["neutral"]))
        if R.get("suma_extra"):
            sumar_partidos(L["E"][R["suma_extra"]], h, a, gl, gv)
    else:
        gl, gv = jugar(rng, r[h], r[a], **P)
        if R["suma"]:
            sumar_partidos(L["E"][R["suma"]], h, a, gl, gv)
        if R.get("suma_extra"):
            sumar_partidos(L["E"][R["suma_extra"]], h, a, gl, gv)
        for x, y, g1, g2 in zip(h, a, gl, gv):
            partidos.append(nuevo_partido(L["nombre"], n, R["rotulo"], comp_de(R, x), nom[x], nom[y], g1, g2,
                                          neutral=R["neutral"]))
    L["log"].extend(partidos)
    L["fecha"] = n
    return partidos


def partidos_de_ronda(L, n):
    """Partidos ya jugados de la ronda n."""
    return [p for p in L["log"] if p["fecha"] == n]
def tabla(L, E, ids=None):
    """Tabla ordenada (puntos, diferencia de gol, goles a favor) de los equipos `ids` (todos si no se pasa) según las
    estadísticas `E`, con columna 'Pos'. Misma forma que las tablas de las ligas argentinas, así se dibuja igual."""
    ids = np.arange(len(L["nombres"])) if ids is None else np.asarray(ids)
    df = df_stats(L["nombres"], L["r"], E, ids)
    df.insert(0, "Pos", df.index + 1)
    return df


def asignar_cupos(orden, cupos, fijos=None):
    """Reparte cupos internacionales por orden de clasificación.

    orden  nombres de los clubes, del primero al último (campeón, subcampeón y después la tabla acumulada).
    cupos  [(etiqueta, cantidad)] en orden de importancia: el primero se queda con los primeros clubes, y así.
    fijos  {club: etiqueta} de los que ya tienen su lugar por otra vía (el campeón de la Libertadores o de la Sudamericana
           de la temporada, `L["camp_int"]`): se pintan con su etiqueta y no ocupan cupo de la tabla, el cupo pasa al
           que sigue.
    Devuelve {club: etiqueta}. Es el mismo reparto que usan las copas CONMEBOL al armar la temporada que viene
    (copas/conmebol.py, `_sortear_pais`), así que lo que muestra la tabla es lo que después se juega."""
    fijos = {n: e for n, e in (fijos or {}).items() if n in orden}
    resto = [n for n in orden if n not in fijos]
    out, i = {}, 0
    for etiqueta, k in cupos:
        for n in resto[i:i + k]:
            out[n] = etiqueta
        i += k
    out.update(fijos)
    return out


def lideres_empatados(df):
    """Posiciones de la tabla `df` (ya ordenada) que empatan en puntos con el líder, de 0 en adelante."""
    pts = df["Pts"].to_numpy()
    return [i for i in range(len(pts)) if pts[i] == pts[0]]
class Formato:
    """Interfaz que cumple cada formato de liga. Todos los métodos reciben el estado de la liga `L` (un dict)."""
    nombre = ""            # clave que se escribe en ligas_ext.json
    descripcion = ""       # una línea para la interfaz
    etapas_definicion = ()  # etapas (campo "etapa" de las rondas) que definen títulos y ascensos: semifinales, finales...
    lugares_fijos = False   # True: el que sube deja su lugar en la lista al que baja (grupos fijos, ver `mover_clubes_en_lugar`)

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        """Estado de la temporada que empieza. `previo` = {club: (puntos, partidos)} de la temporada anterior."""
        raise NotImplementedError

    def avanzar(self, L, rng):
        """Se llama después de cada ronda jugada (y una vez al crear la liga): arma lo que sigue (cruces que faltaban,
        desempates, finales) o define al campeón. Tiene que dejar siempre una ronda por jugar o L["campeon"] cargado."""
        raise NotImplementedError

    def tablas(self, L):
        """Tablas para mostrar: [{"titulo": str, "df": DataFrame, "tipo": "liga"|"descenso"|..., "nota": str}]."""
        raise NotImplementedError

    def cierre(self, L):
        """Al terminar la temporada: {"campeon": nombre, "orden": [nombres], "puntos": {club: (pts, pj)},
        "descienden": [nombres]} (orden = posición final de cada club en la tabla que manda en ese país)."""
        raise NotImplementedError


def _cupos_de_pais(pais):
    """Cupos CONMEBOL del país si están definidos en copas/conmebol.py."""
    try:
        from copas.conmebol import CUPOS_LIB_GRUPOS, cupos_liga
        if pais in CUPOS_LIB_GRUPOS:
            return cupos_liga(pais)
    except ImportError:
        pass
    return []


def _divisional_de(L):
    """Divisional de la liga: 1 para primera, 2 para segunda."""
    if "divisional" in L:
        return int(L["divisional"])
    try:
        from datos import ligas_ext
        cfg = ligas_ext.CONFIG.get(L.get("clave", ""))
        if cfg and "divisional" in cfg:
            return int(cfg["divisional"])
    except Exception:
        pass
    return 2 if str(L.get("clave", "")).endswith("2") else 1


class TodosContraTodos(Formato):
    """Liga larga a doble rueda (como el Brasileirão): gana el que más puntos suma, bajan los últimos.
    Lo que pide ligas_ext.json: `descensos` y `calendario.Liga` = [mes, día, día de la semana] de la primera fecha;
    `vueltas` (opcional, 2 por defecto): 1 la juega a una sola rueda."""
    nombre = "todos_contra_todos"
    descripcion = "Todos contra todos, ida y vuelta. Campeón el que más puntos suma; descienden los últimos."

    def nueva(self, cfg, nombres, r, previo, anio, rng):
        n = len(nombres)
        ida = rueda(rng, range(n))
        fechas = ida if int(cfg.get("vueltas", 2)) == 1 else ida + espejo(ida)      # `vueltas` 1: a una sola rueda (Copa Simón Bolívar)
        dias = dias_semanales(anio, cfg["calendario"]["Liga"], len(fechas))
        rondas = [ronda("Liga", f"Fecha {k + 1}", "Liga", dias[k], pares=f, suma="Liga") for k, f in enumerate(fechas)]
        div = int(cfg.get("divisional", 1))
        out = {"formato": self.nombre, "nombre": cfg["nombre"], "pais": cfg["pais"], "clave": cfg["clave"],
               "nombres": list(nombres), "r": np.array(r, dtype=float), "rondas": rondas, "fecha": 0, "log": [],
               "E": {"Liga": stats_vacias(n)}, "campeon": None, "descensos": int(cfg.get("descensos", 0)),
               "ascensos": int(cfg.get("ascensos", 0)), "divisional": div}
        if div > 1:
            out["suben"] = []
        elif cfg.get("pais"):
            c = _cupos_de_pais(cfg["pais"])
            if c:
                out["cupos"] = c
        return out

    def avanzar(self, L, rng):
        if L["fecha"] >= len(L["rondas"]) and L["campeon"] is None:
            df = tabla(L, L["E"]["Liga"])
            L["campeon"], L["subcampeon"] = df.iloc[0]["Equipo"], df.iloc[1]["Equipo"]
            L["via"] = "Campeón por puntos al terminar la liga."
            div = _divisional_de(L)
            if div > 1:
                a = int(L.get("ascensos", 0))
                L["suben"] = list(df["Equipo"])[:a]

    def tablas(self, L):
        df = tabla(L, L["E"]["Liga"])
        n = len(df)
        d = int(L.get("descensos", 0))
        div = _divisional_de(L)

        if div > 1:
            a = int(L.get("ascensos", 0))
            if not a:
                try:
                    from datos import ligas_ext
                    cfg = ligas_ext.CONFIG.get(L.get("clave", ""))
                    if cfg:
                        a = int(cfg.get("ascensos", 0))
                except Exception:
                    pass

            def _destino_segunda(p):
                if d and p > n - d:
                    return "Desciende"
                if p == 1:
                    base = "Campeón" if L.get("campeon") else "Líder"
                    return f"{base} · Asciende" if a else base
                if a and p <= a:
                    return "Asciende"
                return ""

            df["Destino"] = [_destino_segunda(p) for p in df["Pos"]]
            try:                                       # a qué liga ascienden: la de arriba (Série A, Série B...)
                from datos import ligas_ext
                sup = ligas_ext.CONFIG[ligas_ext.CONFIG[L["clave"]]["superior"]]["nombre"]
            except Exception:
                sup = "Primera División"
            nota = (f"Ascienden a {sup} los {a} primeros." if L.get("campeon")
                    else f"Ascienden a {sup} los {a} primeros (posiciones provisorias).") if a else ""
        else:
            cupos = _cupos_de_pais(L.get("pais", "")) or L.get("cupos")
            if cupos:
                L["cupos"] = cupos
            cupos_map = asignar_cupos(list(df["Equipo"]), cupos, L.get("camp_int")) if cupos else {}

            def _destino_primera(p, eq):
                if d and p > n - d:
                    return "Desciende"
                cupo = cupos_map.get(eq, "")
                if p == 1:
                    base = "Campeón" if L.get("campeon") else "Líder"
                    return f"{base} · {cupo}" if cupo else base
                return cupo

            df["Destino"] = [_destino_primera(p, eq) for p, eq in zip(df["Pos"], df["Equipo"])]
            nota = ("Cupos a copas internacionales y descensos por la posición en la tabla. "
                    + ("" if L.get("campeon") else "Destinos provisorios por la posición de hoy.")) if (cupos or d) else ""
            try:
                from copas.conmebol import NOTA_COPA
                nota = (nota + " " + NOTA_COPA.get(L.get("pais", ""), "")).strip()
            except ImportError:
                pass

        return [{"titulo": "Posiciones", "df": df, "tipo": "liga", "nota": nota}]

    def cierre(self, L):
        df = tabla(L, L["E"]["Liga"])
        d = int(L.get("descensos", 0))
        div = _divisional_de(L)
        suben = [] if div == 1 else (list(L.get("suben", [])) or list(df["Equipo"])[:int(L.get("ascensos", 0))])
        return {"campeon": L["campeon"], "orden": list(df["Equipo"]),
                "puntos": {x["Equipo"]: (int(x["Pts"]), int(x["PJ"])) for _, x in df.iterrows()},
                "descienden": list(df["Equipo"])[len(df) - d:] if d else [],
                "suben": suben}


# El registro de formatos lo completan ligas/uruguay.py y ligas/uruguay_segunda.py al importarse (ver `formato_de`).
FORMATOS = {TodosContraTodos.nombre: TodosContraTodos()}


def formato_de(cfg):
    """El formato de la liga `cfg` (una entrada de ligas_ext.json)."""
    from ligas import brasil_d, colombia, colombia_segunda, ecuador, paraguay, uruguay, uruguay_amateur, uruguay_segunda  # noqa: F401  (se registran solos: evita importaciones circulares)
    try:
        return FORMATOS[cfg["formato"]]
    except KeyError:
        raise ValueError(f"Formato de liga desconocido: {cfg['formato']!r} (liga {cfg['clave']!r})") from None


def mover_clubes(nombres, descienden, ascienden):
    """Plantel de la temporada que viene: los que se quedan (en su orden) y después los que suben."""
    return [n for n in nombres if n not in set(descienden)] + list(ascienden)


def mover_clubes_en_lugar(nombres, salen, entran):
    """Como `mover_clubes`, pero cada club que sale deja su lugar en la lista al que entra (en orden). Sirve para las ligas
    con grupos fijos (Série D): los grupos salen de cortar la lista de a 6, así que quien entra hereda el grupo de quien sale.
    Si entran más de los que salen, los que sobran van al final; si salen más, los lugares sobrantes se borran."""
    salen, entran = set(salen), list(entran)
    out = []
    for n in nombres:
        if n not in salen:
            out.append(n)
        elif entran:
            out.append(entran.pop(0))
    return out + entran
