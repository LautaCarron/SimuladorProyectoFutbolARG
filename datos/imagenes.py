"""Utilidades de imágenes: `slug` arma el nombre en minúsculas y con guiones que usan las clases CSS de los escudos."""

import unicodedata


def slug(nombre):
    t = unicodedata.normalize("NFKD", nombre.lower())
    s = "".join(c if c.isalnum() else "-" for c in t if not unicodedata.combining(c))
    return "-".join(x for x in s.split("-") if x)
