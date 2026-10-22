"""Imágenes con fondo blanco -> PNG transparente (logos de ligas y escudos de clubes).

Se baja la imagen una vez, se le borra el blanco que toca los bordes (el blanco de adentro del escudo queda) y se
guarda en la carpeta que se pida. Si ya existe el archivo se usa tal cual, así que se puede reemplazar por un PNG
transparente propio con el mismo nombre. Si no hay internet o falta Pillow, devuelve la URL original (con fondo).
"""

import base64
import io
import os
import unicodedata
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))


def slug(nombre):
    t = unicodedata.normalize("NFKD", nombre.lower())
    s = "".join(c if c.isalnum() else "-" for c in t if not unicodedata.combining(c))
    return "-".join(x for x in s.split("-") if x)


def sin_fondo(url, destino, tam=160):
    """Data URI (PNG transparente) de la imagen `url`; se guarda en `destino`. Si algo falla, devuelve `url`."""
    try:
        if not os.path.exists(destino):
            import numpy as np
            from PIL import Image, ImageDraw
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                im = Image.open(io.BytesIO(r.read())).convert("RGBA")
            im.thumbnail((tam, tam))
            w, h = im.size
            for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
                if min(im.getpixel(xy)[:3]) > 200:             # esquina blanca = fondo
                    ImageDraw.floodfill(im, xy, (255, 255, 255, 0), thresh=60)
            a = np.array(im)
            for _ in range(2):                                 # borra el halo blanco que deja el JPG en el borde
                vacio = a[:, :, 3] == 0
                vecino = np.zeros_like(vacio)
                vecino[1:, :] |= vacio[:-1, :]
                vecino[:-1, :] |= vacio[1:, :]
                vecino[:, 1:] |= vacio[:, :-1]
                vecino[:, :-1] |= vacio[:, 1:]
                a[vecino & (a[:, :, :3].min(axis=2) > 215), 3] = 0
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            Image.fromarray(a).save(destino)
        with open(destino, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return url


def escudos_sin_fondo(escudos, nombres):
    """{club: data URI} de los clubes `nombres` a los que se les pudo sacar el fondo (el resto sigue con su URL)."""
    out = {}
    for n in nombres:
        url = escudos.get(n)
        if not url:
            continue
        r = sin_fondo(url, os.path.join(AQUI, "escudos_sin_fondo", slug(n) + ".png"))
        if r.startswith("data:"):
            out[n] = r
    return out
