"""
Reglas de vigencia: los certificados CBR/SII tienen ventana de validez para
operaciones hipotecarias (en general 30 días para CBR, 6 meses para SII).
"""
from datetime import datetime

from src.core.config import settings
from src.reglas.rules._helpers import all_nodes, parse_chilean_date


def _check_vigencia(node: dict, max_dias: int) -> dict | None:
    fecha_str = node.get("fecha_emision")
    fecha = parse_chilean_date(fecha_str)
    if not fecha:
        return None
    dias = (datetime.now() - fecha).days
    if dias <= max_dias:
        return None
    return {
        "descripcion": (
            f"El {node.get('label')} tiene {dias} días desde su emisión "
            f"(máximo recomendado: {max_dias})."
        ),
        "detalle": {"fecha_emision": fecha_str, "dias_transcurridos": dias, "max_dias": max_dias, "source": node.get("source")},
        "recomendacion": "Solicitar un certificado actualizado antes de proceder con la operación hipotecaria.",
    }


def regla_vigencia_cbr(synthesis: dict) -> list[dict]:
    out = []
    for n in all_nodes(synthesis):
        if n.get("source") in ("cert_dominio_vigente", "cert_hipotecas_gravamenes"):
            issue = _check_vigencia(n, settings.DIAS_VALIDEZ_CERTIFICADOS_CBR)
            if issue:
                out.append(issue)
    return out


def regla_vigencia_sii(synthesis: dict) -> list[dict]:
    out = []
    for n in all_nodes(synthesis):
        if n.get("source") == "cert_avaluo_sii":
            issue = _check_vigencia(n, settings.DIAS_VALIDEZ_CERTIFICADOS_SII)
            if issue:
                out.append(issue)
    return out


REGLAS_VIGENCIA = [
    {
        "id": "R-V-001",
        "titulo": "Vigencia certificados CBR (30 días)",
        "severidad": "media",
        "categoria": "vigencia",
        "check": regla_vigencia_cbr,
    },
    {
        "id": "R-V-002",
        "titulo": "Vigencia certificado de avalúo SII (180 días)",
        "severidad": "baja",
        "categoria": "vigencia",
        "check": regla_vigencia_sii,
    },
]
