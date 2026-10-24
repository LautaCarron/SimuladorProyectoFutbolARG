import os
import sys

os.environ["AFA_TODAS_LAS_PESTANAS"] = "1"          # las pruebas dibujan todas las pestañas a la vez
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
