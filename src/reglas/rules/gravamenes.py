"""
Reglas sobre hipotecas, gravámenes, prohibiciones.
"""
from src.reglas.rules._helpers import all_nodes, find_node


def regla_hipotecas_visibles(synthesis: dict) -> list[dict]:
    """
    R-G-001: Si una escritura de hipoteca aparece y no figura en el certificado
    de hipotecas/gravámenes vigentes, alertar.
    """
    hipotecas_actos = [
        n for n in all_nodes(synthesis)
        if n.get("type") == "acto" and (n.get("tipo_acto") or "").lower() == "hipoteca"
    ]
    if not hipotecas_actos:
        return []

    grav = find_node(synthesis, lambda n: n.get("source") == "cert_hipotecas_gravamenes")
    if not grav:
        return [{
            "descripcion": "Existen escrituras de hipoteca pero no se cargó el Certificado de Hipotecas y Gravámenes.",
            "recomendacion": "Solicitar el Certificado de Hipotecas y Gravámenes vigente al CBR.",
            "detalle": {"hipotecas_en_escrituras": len(hipotecas_actos)},
        }]

    n_en_cert = grav.get("n_hipotecas") or 0
    if n_en_cert < len(hipotecas_actos):
        return [{
            "descripcion": (
                f"En las escrituras se identifican {len(hipotecas_actos)} hipotecas, "
                f"pero el Certificado del CBR solo registra {n_en_cert}. "
                "Posible alzamiento no inscrito o registro incompleto."
            ),
            "detalle": {"en_escrituras": len(hipotecas_actos), "en_certificado": n_en_cert},
            "recomendacion": "Verificar inscripciones de alzamiento en el CBR; solicitar certificado actualizado.",
        }]
    return []


def regla_libre_de_gravamenes(synthesis: dict) -> list[dict]:
    """R-G-002: si el certificado dice 'libre de gravámenes' y hay hipotecas en actos, alertar."""
    grav = find_node(synthesis, lambda n: n.get("source") == "cert_hipotecas_gravamenes")
    if not grav or not grav.get("libre_de_gravamenes"):
        return []
    hipotecas_actos = [n for n in all_nodes(synthesis) if n.get("type") == "acto" and (n.get("tipo_acto") or "").lower() == "hipoteca"]
    if hipotecas_actos:
        return [{
            "descripcion": "El certificado declara la propiedad libre de gravámenes, pero hay escrituras de hipoteca asociadas.",
            "recomendacion": "Confirmar que los alzamientos correspondientes estén inscritos.",
            "detalle": {"hipotecas_en_escrituras": len(hipotecas_actos)},
        }]
    return []


REGLAS_GRAVAMENES = [
    {
        "id": "R-G-001",
        "titulo": "Hipotecas visibles en escrituras vs certificado CBR",
        "severidad": "alta",
        "categoria": "gravamenes",
        "check": regla_hipotecas_visibles,
    },
    {
        "id": "R-G-002",
        "titulo": "Coherencia certificado libre vs escrituras de hipoteca",
        "severidad": "critica",
        "categoria": "gravamenes",
        "check": regla_libre_de_gravamenes,
    },
]
