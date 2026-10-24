"""Prueba "dorada" para refactorizar el motor sin cambiar su comportamiento.

Juega N temporadas con una semilla fija y imprime un hash del estado completo después de cada paso. Si dos versiones del
código imprimen los mismos hashes, simulan exactamente lo mismo.

    python tests/golden.py <raíz del proyecto> <semilla> <temporadas> [fb] [tam]

    fb   crea el Federal B (Modo dios)         tam   fija tamaños objetivo (Modo dios)

Uso típico: copiar el proyecto antes de tocarlo (cp -r . /tmp/base) y comparar la salida de /tmp/base con la del proyecto
modificado, para varias semillas. Una temporada tarda unos 2-3 segundos."""
import hashlib, os, sys, time
root, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, root); os.chdir(root)
import numpy as np, pandas as pd
import motor.temporada as mt
time.time_ns = lambda: seed * 7919 + 1            # crear_estado queda determinista

def feed(h, o):
    if isinstance(o, dict):
        h.update(b"{")
        for k in sorted(o, key=repr): feed(h, k); feed(h, o[k])
        h.update(b"}")
    elif isinstance(o, (list, tuple)):
        h.update(b"["); [feed(h, x) for x in o]; h.update(b"]")
    elif isinstance(o, (set, frozenset)):
        feed(h, sorted(o, key=repr))
    elif isinstance(o, np.ndarray):
        h.update(str((o.dtype, o.shape)).encode()); h.update(np.ascontiguousarray(o).tobytes())
    elif isinstance(o, np.random.Generator):
        feed(h, o.bit_generator.state)
    elif isinstance(o, pd.DataFrame):
        h.update(o.to_json().encode())
    elif hasattr(o, "bit_generator") or hasattr(o, "generator") or type(o).__name__.startswith("Con"):
        feed(h, {k: v for k, v in vars(o).items()} if hasattr(o, "__dict__") else repr(o))
    elif isinstance(o, (int, float, str, bool, type(None), np.generic)):
        h.update(repr(o).encode())
    elif callable(o):
        h.update(getattr(o, "__qualname__", "fn").encode())
    else:
        h.update(repr(o).encode())

def digest(S):
    h = hashlib.sha256(); feed(h, S); return h.hexdigest()[:12]

from config import VOLATILIDAD, parametros_partido
from motor.simulacion import simular_todo
S, P = mt.crear_estado(), parametros_partido()
esc = sys.argv[4] if len(sys.argv) > 4 else ""
if "fb" in esc:                                   # Modo dios: crear el Federal B
    from ligas.federal_b import cfg_federal_b
    cfg_federal_b(S)["crear"] = True
if "tam" in esc:                                  # Modo dios: tamaños objetivo distintos
    from motor.tamanos import objetivos
    objetivos(S).update({"p": 24, "b": 40, "pb": 20, "pc": 18})
out = [digest(S)]
for _ in range(n):
    simular_todo(S, P); out.append(digest(S))
    mt.nueva_temporada(S, VOLATILIDAD); out.append(digest(S))
print(" ".join(out))
