"""
Motor de reglas legales para hipotecai.
--------------------------------------------------------------
Cada regla:
  · regla_id: identificador estable (ej. R-CBR-001)
  · severidad: 'critica' | 'alta' | 'media' | 'baja' | 'info'
  · check(synthesis): retorna lista[hallazgo] o []

Las reglas se importan desde sub-módulos por categoría:
  - cadena_dominio
  - gravamenes
  - vigencia_certificados
  - coherencia_dimensional
  - normativa_urbana
"""
from __future__ import annotations

import logging
from typing import Callable

from src.reglas.rules.cadena_dominio import REGLAS_CADENA_DOMINIO
from src.reglas.rules.coherencia_dimensional import REGLAS_COHERENCIA_DIMENSIONAL
from src.reglas.rules.gravamenes import REGLAS_GRAVAMENES
from src.reglas.rules.normativa_urbana import REGLAS_NORMATIVA_URBANA
from src.reglas.rules.vigencia_certificados import REGLAS_VIGENCIA

logger = logging.getLogger(__name__)


REGLAS: list[dict] = [
    *REGLAS_CADENA_DOMINIO,
    *REGLAS_GRAVAMENES,
    *REGLAS_VIGENCIA,
    *REGLAS_COHERENCIA_DIMENSIONAL,
    *REGLAS_NORMATIVA_URBANA,
]


def ejecutar_reglas(synthesis: dict) -> list[dict]:
    """
    Aplica todas las reglas registradas. `synthesis` es el body de
    /synthesis/{folio} del sintetizador-api.
    """
    hallazgos: list[dict] = []
    for regla in REGLAS:
        try:
            resultado = regla["check"](synthesis) or []
            for h in resultado:
                # Inyectar regla_id y severidad por defecto si no vienen
                h.setdefault("regla_id", regla["id"])
                h.setdefault("severidad", regla["severidad"])
                h.setdefault("titulo", regla["titulo"])
                hallazgos.append(h)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Regla %s falló", regla["id"])
            hallazgos.append({
                "regla_id": regla["id"],
                "severidad": "info",
                "titulo": f"Regla {regla['id']} no pudo ejecutarse",
                "descripcion": str(exc),
            })
    # Pasar incongruencias del sintetizador como hallazgos también
    for inc in synthesis.get("incongruencias") or []:
        hallazgos.append({
            "regla_id": "S-INC-001",
            "severidad": inc.get("severidad", "media"),
            "titulo": f"Discrepancia detectada en campo {inc.get('campo')}",
            "descripcion": f"Valores divergentes entre fuentes documentales para {inc.get('campo')}.",
            "detalle": inc,
            "recomendacion": "Verificar la fuente correcta y, de ser necesario, solicitar nuevo documento.",
        })
    return hallazgos
