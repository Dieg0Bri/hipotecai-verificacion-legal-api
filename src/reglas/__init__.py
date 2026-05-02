"""
Reglas de verificación legal sobre la síntesis del estudio.

Cada regla es una función que recibe el grafo + metadata y devuelve
una lista de hallazgos (dicts). El motor las ejecuta todas y agrega
los resultados.
"""
from src.reglas.engine import REGLAS, ejecutar_reglas

__all__ = ["REGLAS", "ejecutar_reglas"]
