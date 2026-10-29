"""Club propio: UN solo club creado por la persona desde la pantalla de inicio, que entra al Regional Amateur.

Los datos del club (nombre, provincia, liga, ciudad, región, media y escudo) viajan dentro de la partida
(`S["club_propio"]`), así se guardan en el `.afa` y no se mezclan entre personas que usan el mismo servidor. Las
funciones de datos que no reciben `S` (`datos_club`, `region_regional`, `crest`...) lo consultan acá: en cada pasada
de la app se llama a `activar()` con el club de la partida (ver simuladorafa.py). Es por hilo (threading.local), así
que dos sesiones a la vez no se pisan.

El club puede ser del Interior (entra al Regional Amateur, con provincia, liga, ciudad y región) o Metropolitano
(CABA / Gran Buenos Aires: no lleva esos datos y arranca directo en el Promocional Amateur).

Sin Streamlit: lo usan los datos y el motor.
"""

import base64
import io
import threading
from collections import Counter

from datos.datos_regional import REGIONAL
from datos.imagenes import slug

MAX_ESCUDO = 1024 * 1024        # 1 MB
LADO_ESCUDO = 192               # el escudo se guarda achicado a este lado (px) para no cargar la partida
MAX_NOMBRE = 40
MEDIA_MIN, MEDIA_MAX, MEDIA_INICIAL = 10, 33, 27     # mínimo 10 (piso del motor); los del Regional van de 20 a 33
MEDIA_INICIAL_METRO = 22                              # los del Promocional Amateur van de 18 a 31
INTERIOR, METROPOLITANA = "Interior", "Metropolitana"

WO_RATING = -1000.0             # media de un club dado de baja: motor.nucleo.jugar le da por perdidos 0-3 los partidos

_hilo = threading.local()


def activar(club, ex=()):
    """Deja a disposición de este hilo el club propio de la partida (o None) y los que ya se fueron (`ex`)."""
    _hilo.club = club or None
    _hilo.ex = list(ex or [])


def actual():
    return getattr(_hilo, "club", None)


def es_propio(nombre):
    c = actual()
    return bool(c) and c["nombre"] == nombre


def origen(nombre):
    """"Interior" o "Metropolitana" si `nombre` es el club propio; si no, None (las partidas viejas son del Interior)."""
    c = actual()
    return c.get("origen", INTERIOR) if c and c["nombre"] == nombre else None


def datos(nombre):
    """{'ciudad', 'provincia', 'liga'} si `nombre` es el club propio del Interior; si no, None (el metropolitano no tiene)."""
    c = actual()
    if c and c["nombre"] == nombre and c.get("origen", INTERIOR) == INTERIOR:
        return {"ciudad": c["ciudad"], "provincia": c["provincia"], "liga": c["liga"]}
    return None


def region(nombre):
    c = actual()
    return (c["region"] or None) if c and c["nombre"] == nombre else None


def _con_escudo():
    c = actual()
    return [x for x in ([c] if c else []) + getattr(_hilo, "ex", []) if x.get("escudo")]


def escudo(nombre):
    """Data URI del escudo del club propio o de uno que ya se fue (sigue en el palmarés); '' si no tiene."""
    return next((x["escudo"] for x in _con_escudo() if x["nombre"] == nombre), "")


def css():
    """CSS con los escudos del club propio y de los que ya se fueron (una sola vez, como ESCUDOS_CSS)."""
    return "".join(f"<style>.cr-{slug(x['nombre'])}{{background-image:url({x['escudo']});}}</style>"
                   for x in _con_escudo())


# ---- Provincias, ligas y regiones que ya existen en el Regional Amateur --------------------------------------
def _tabla():
    """({provincia: [ligas]}, {(provincia, liga): región más habitual}) con los clubes que ya juegan el Regional."""
    ligas, votos = {}, {}
    for x in REGIONAL:
        ligas.setdefault(x["provincia"], set()).add(x["liga"])
        votos.setdefault((x["provincia"], x["liga"]), Counter())[x["region"]] += 1
    return ({p: sorted(l) for p, l in sorted(ligas.items())},
            {k: v.most_common(1)[0][0] for k, v in votos.items()})


LIGAS_POR_PROVINCIA, _REGION_DE_LIGA = _tabla()
PROVINCIAS = list(LIGAS_POR_PROVINCIA)


def region_de_liga(provincia, liga):
    """Región del Regional que le corresponde a una liga (por ejemplo, Liga Marplatense -> Pampeana Sur)."""
    return _REGION_DE_LIGA.get((provincia, liga))


# ---- Validaciones --------------------------------------------------------------------------------------------
def nombre_valido(nombre):
    """Devuelve un texto de error o None (un nombre repetido no es error: ver nombre_unico)."""
    n = " ".join((nombre or "").split())
    if not n:
        return "Falta el nombre del club."
    if len(n) > MAX_NOMBRE:
        return f"El nombre es muy largo (máximo {MAX_NOMBRE} letras)."
    if "<" in n or ">" in n:
        return "El nombre no puede llevar < ni >."
    return None


def nombre_unico(nombre, ocupados):
    """Nombre con el que entra el club. Si ya existe uno igual (un club de verdad, o uno propio que dejó títulos en el
    palmarés) se le agrega "(propio)" para que sus títulos no se sumen a los de ese club: Aldosivi -> Aldosivi (propio)."""
    n = " ".join((nombre or "").split())
    usados = {o.casefold() for o in ocupados}
    if n.casefold() not in usados:
        return n
    base, k = f"{n} (propio)", 2
    cand = base
    while cand.casefold() in usados:
        cand, k = f"{n} (propio {k})", k + 1
    return cand


def procesar_escudo(datos_img):
    """Valida y achica la imagen subida. Devuelve (data URI PNG, None) o (None, texto de error).

    Acepta PNG, JPG y WEBP de hasta 1 MB. Se guarda achicada a LADO_ESCUDO px (PNG con transparencia)."""
    if len(datos_img) > MAX_ESCUDO:
        return None, f"La imagen pesa {len(datos_img) / MAX_ESCUDO:.1f} MB: el máximo es 1 MB."
    try:
        from PIL import Image
    except ImportError:             # sin Pillow (web estática): se guarda tal cual, si es de un tipo conocido
        tipos = ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))
        mime = next((m for firma, m in tipos if datos_img.startswith(firma)), None)
        if not mime:
            return None, "La imagen tiene que ser PNG o JPG."
        return f"data:{mime};base64," + base64.b64encode(datos_img).decode(), None
    try:
        im = Image.open(io.BytesIO(datos_img))
        if im.format not in ("PNG", "JPEG", "WEBP"):
            return None, "La imagen tiene que ser PNG, JPG o WEBP."
        im = im.convert("RGBA")
    except Exception:
        return None, "No se pudo leer la imagen: probá con otro archivo."
    im.thumbnail((LADO_ESCUDO, LADO_ESCUDO))
    salida = io.BytesIO()
    im.save(salida, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(salida.getvalue()).decode(), None


def crear(nombre, provincia="", liga="", ciudad="", media=MEDIA_INICIAL, escudo_uri="", ocupados=(), origen=INTERIOR):
    """Arma el diccionario del club propio (la región sale de la liga y el nombre se diferencia si ya existe).

    Con origen Metropolitana sólo hacen falta nombre, media y escudo: no tiene provincia, liga, ciudad ni región."""
    nombre = nombre_unico(nombre, ocupados)
    media = max(float(MEDIA_MIN), min(float(MEDIA_MAX), float(media)))
    if origen == METROPOLITANA:
        return {"nombre": nombre, "origen": METROPOLITANA, "provincia": "", "liga": "", "ciudad": "", "region": "",
                "media": media, "escudo": escudo_uri or ""}
    reg = region_de_liga(provincia, liga)
    if reg is None:
        raise ValueError(f"No hay una región para {liga} ({provincia}).")
    return {"nombre": nombre, "origen": INTERIOR, "provincia": provincia, "liga": liga,
            "ciudad": " ".join((ciudad or "").split()), "region": reg,
            "media": media, "escudo": escudo_uri or ""}


def nombres_ocupados():
    """Nombres de todos los clubes que ya existen (argentinos, del exterior y del Mundial de Clubes)."""
    from datos import equipos as eq
    return (set(eq.EQUIPOS) | set(eq.EQUIPOS_B) | set(eq.EQUIPOS_FEDERAL) | set(eq.EQUIPOS_PRIMERA_B)
            | set(eq.EQUIPOS_PRIMERA_C) | set(eq.EQUIPOS_PRIMERA_D) | set(eq.EQUIPOS_REGIONAL) | set(eq.ESCUDOS))
