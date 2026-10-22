"""Guardar y cargar partidas (va en motor/guardado.py). Sin Streamlit: sólo numpy y pandas.

Una partida es un archivo `.afa` con tres partes:

    MAGIC (8 bytes) | largo del encabezado (4 bytes) | encabezado JSON | datos comprimidos (zlib + pickle)

  * El ENCABEZADO (JSON) se lee sin tocar los datos: temporada, año, modo, manager, fecha de guardado y la
    versión del estado. Sirve para mostrar qué partida es antes de cargarla y para rechazar una partida de
    otra versión del simulador.
  * Los DATOS son el estado S, el del manager (st.session_state["manager"]) y el modo en que se estaba.

Por qué no es un pickle común:
  * Al GUARDAR, los DataFrame, los arrays y el generador de números aleatorios de numpy se convierten a
    estructuras simples (listas, textos, diccionarios). Así la partida no depende de la versión de pandas /
    numpy con la que se guardó (la web estática y la PC no tienen por qué coincidir).
  * Al CARGAR, el unpickler sólo acepta una lista cerrada de nombres (ver _PERMITIDOS). Un archivo `.afa`
    ajeno no puede ejecutar código: si trae cualquier otra cosa, se rechaza.

API:
  empaquetar(S, manager=None, modo="simulador", nombre="") -> bytes
  leer_encabezado(datos)  -> dict (lanza ErrorPartida si el archivo no sirve)
  desempaquetar(datos)    -> {"S": ..., "manager": ... o None, "modo": ..., "encabezado": {...}}
  nombre_archivo(S, ...)  -> nombre sugerido para descargar
"""

import datetime as dt
import io
import json
import pickle
import re
import struct
import zlib

import numpy as np
import pandas as pd

from motor.temporada import VERSION_ESTADO

MAGIC = b"AFASAVE1"
FORMATO = 1
MAX_BYTES = 200 * 1024 * 1024        # tope de los datos ya descomprimidos (contra archivos bomba)
EXTENSION = "afa"


class ErrorPartida(Exception):
    """El archivo no es una partida válida o no se puede cargar (el mensaje se le muestra al usuario)."""


# ---- Conversión a estructuras simples (y vuelta) ---------------------------------------------------------
def _arr(datos, dtype, forma):
    return np.array(datos, dtype=np.dtype(dtype)).reshape(forma)


def _esc(valor):
    return valor


def _rng(estado):
    bg = np.random.PCG64()
    bg.state = estado
    return np.random.Generator(bg)


def _df(columnas, datos, indice, nombre_indice, rango, nombre_columnas):
    if rango is not None:
        idx = pd.RangeIndex(rango[0], rango[1], rango[2], name=nombre_indice)
    else:
        idx = pd.Index(indice, name=nombre_indice)
    df = pd.DataFrame({c: pd.Series(v, dtype=dt_, index=idx) for c, (v, dt_) in zip(columnas, datos)}, index=idx)
    if len(columnas) == 0:
        df = pd.DataFrame(index=idx)
    df.columns.name = nombre_columnas
    return df


class _Pickler(pickle.Pickler):
    """Pickler que reemplaza los objetos de numpy / pandas por llamadas a _arr, _rng y _df."""

    def reducer_override(self, obj):
        if isinstance(obj, pd.DataFrame):
            if isinstance(obj.columns, pd.MultiIndex) or isinstance(obj.index, pd.MultiIndex):
                raise ErrorPartida("El estado tiene una tabla con índice múltiple y no se puede guardar.")
            rango = None
            if isinstance(obj.index, pd.RangeIndex):
                rango = (obj.index.start, obj.index.stop, obj.index.step)
            cols = list(obj.columns)
            datos = [(obj.iloc[:, k].tolist(), str(obj.dtypes.iloc[k])) for k in range(len(cols))]
            return _df, (cols, datos, None if rango else obj.index.tolist(), obj.index.name, rango,
                         obj.columns.name)
        if isinstance(obj, np.ndarray):
            if obj.dtype == object:
                return _arr, (obj.tolist(), "object", obj.shape)
            return _arr, (obj.ravel().tolist(), obj.dtype.str, obj.shape)
        if isinstance(obj, np.random.Generator):
            return _rng, (obj.bit_generator.state,)
        if isinstance(obj, np.generic):          # np.float64, np.int64, np.bool_... -> escalares de Python
            return _esc, (obj.item(),)
        if type(obj).__module__.split(".")[0] in ("numpy", "pandas"):
            raise ErrorPartida(f"El estado tiene un objeto ({type(obj).__name__}) que no se puede guardar.")
        return NotImplemented


# ---- Carga restringida -----------------------------------------------------------------------------------
_PERMITIDOS = {
    ("motor.guardado", "_arr"), ("motor.guardado", "_rng"), ("motor.guardado", "_df"),
    ("motor.guardado", "_esc"),
    ("builtins", "set"), ("builtins", "frozenset"), ("builtins", "slice"), ("builtins", "range"),
    ("builtins", "complex"), ("builtins", "bytearray"),
    ("collections", "OrderedDict"), ("collections", "defaultdict"), ("collections", "deque"),
    ("datetime", "date"), ("datetime", "datetime"), ("datetime", "timedelta"), ("datetime", "time"),
}


class _Unpickler(pickle.Unpickler):
    def find_class(self, modulo, nombre):
        if (modulo, nombre) in _PERMITIDOS:
            return super().find_class(modulo, nombre)
        raise ErrorPartida("El archivo trae datos que el simulador no reconoce: no es una partida válida.")


# ---- Empaquetar / desempaquetar --------------------------------------------------------------------------
def _resumen(S, manager, modo):
    """Datos para el encabezado: qué partida es, sin tener que cargarla."""
    enc = {"temp": int(S["temp"]), "anio": 2025 + int(S["temp"]), "modo": modo, "dia": None,
           "manager": None, "club": None}
    try:
        from motor.calendario import proximos, texto_dia
        prox = proximos(S)
        if prox:
            enc["dia"] = texto_dia(min(d for d, _ in prox.values()))
    except Exception:                                # el día es un dato de cortesía: nunca frena el guardado
        pass
    if manager:
        enc["manager"] = f'{manager.get("nombre", "")} {manager.get("apellido", "")}'.strip() or None
        enc["club"] = manager.get("club")
    return enc


def empaquetar(S, manager=None, modo="simulador", nombre=""):
    """bytes de un archivo `.afa` con la partida actual."""
    if modo not in ("simulador", "manager"):
        modo = "simulador"
    enc = {"app": "afa", "formato": FORMATO, "version": VERSION_ESTADO,
           "guardado": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
           "nombre": str(nombre).strip()[:80], **_resumen(S, manager, modo)}
    buf = io.BytesIO()
    _Pickler(buf, protocol=pickle.HIGHEST_PROTOCOL).dump({"S": S, "manager": manager, "modo": modo})
    cuerpo = zlib.compress(buf.getvalue(), 6)
    cab = json.dumps(enc, ensure_ascii=False).encode("utf-8")
    return MAGIC + struct.pack(">I", len(cab)) + cab + cuerpo


def _partir(datos):
    datos = bytes(datos)
    if len(datos) < len(MAGIC) + 4 or not datos.startswith(MAGIC):
        raise ErrorPartida("Ese archivo no es una partida del simulador (.afa).")
    (n,) = struct.unpack(">I", datos[len(MAGIC):len(MAGIC) + 4])
    ini = len(MAGIC) + 4
    if n > 64 * 1024 or len(datos) < ini + n:
        raise ErrorPartida("El archivo está dañado (encabezado incompleto).")
    try:
        enc = json.loads(datos[ini:ini + n].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ErrorPartida("El archivo está dañado (encabezado ilegible).") from None
    if not isinstance(enc, dict) or enc.get("app") != "afa":
        raise ErrorPartida("Ese archivo no es una partida del simulador (.afa).")
    return enc, datos[ini + n:]


def _compatible(enc):
    if enc.get("formato") != FORMATO:
        raise ErrorPartida("La partida se guardó con un formato de archivo distinto y no se puede abrir.")
    if enc.get("version") != VERSION_ESTADO:
        raise ErrorPartida(f"La partida es de otra versión del simulador (estado {enc.get('version')}, esta es la "
                           f"{VERSION_ESTADO}): cambió la estructura de los datos y no se puede cargar.")


def leer_encabezado(datos):
    """Encabezado de la partida (sin cargarla). Lanza ErrorPartida si no sirve o es de otra versión."""
    enc, _ = _partir(datos)
    _compatible(enc)
    return enc


def desempaquetar(datos):
    """Carga la partida: {"S", "manager", "modo", "encabezado"}. Lanza ErrorPartida si no se puede."""
    enc, cuerpo = _partir(datos)
    _compatible(enc)
    d = zlib.decompressobj()
    try:
        crudo = d.decompress(cuerpo, MAX_BYTES)
        if d.unconsumed_tail:
            raise ErrorPartida("La partida es demasiado grande.")
        carga = _Unpickler(io.BytesIO(crudo)).load()
    except ErrorPartida:
        raise
    except Exception:
        raise ErrorPartida("El archivo está dañado y no se pudo leer.") from None
    S = carga.get("S") if isinstance(carga, dict) else None
    M = carga.get("manager") if isinstance(carga, dict) else None
    modo = carga.get("modo") if isinstance(carga, dict) else None
    if (not isinstance(S, dict) or S.get("version") != VERSION_ESTADO
            or not all(k in S for k in ("rng", "temp", "b", "f", "pb", "pc", "pd", "reg", "nombres", "r"))):
        raise ErrorPartida("El archivo no tiene una partida completa.")
    if M is not None and not isinstance(M, dict):
        raise ErrorPartida("Los datos del manager están dañados.")
    return {"S": S, "manager": M, "modo": "manager" if (modo == "manager" and M) else "simulador",
            "encabezado": enc}


def nombre_archivo(S, manager=None, nombre=""):
    """Nombre sugerido: partida_<nombre o temporada>_<fecha>.afa (sólo letras, números y guiones)."""
    base = str(nombre).strip() or f"temporada {S['temp']}" + (f" {manager.get('apellido', '')}" if manager else "")
    base = re.sub(r"[^A-Za-z0-9áéíóúüñÁÉÍÓÚÜÑ]+", "-", base).strip("-")[:40] or "partida"
    return f"partida_{base}_{dt.datetime.now().strftime('%Y%m%d-%H%M')}.{EXTENSION}"
