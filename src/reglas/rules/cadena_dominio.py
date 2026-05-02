"""
Reglas de cadena de dominio:
  R-CD-001: Titular en cert_dominio_vigente debe coincidir con el último
            comprador en escrituras de compraventa.
"""
from src.reglas.rules._helpers import all_nodes, find_node


def _ultimo_comprador(synthesis: dict) -> str | None:
    """Recorre los nodos 'acto' tipo compraventa y devuelve el último comprador."""
    actos = [n for n in all_nodes(synthesis) if n.get("type") == "acto" and (n.get("tipo_acto") or "").lower() == "compraventa"]
    if not actos:
        return None
    actos.sort(key=lambda n: n.get("fecha_otorgamiento") or "", reverse=True)
    compradores = actos[0].get("compradores") or []
    return compradores[0] if compradores else None


def regla_titular_concuerda(synthesis: dict) -> list[dict]:
    titularidad = find_node(synthesis, lambda n: n.get("id") == "titularidad" or n.get("source") == "cert_dominio_vigente")
    if not titularidad:
        return [{
            "descripcion": "No se encontró Certificado de Dominio Vigente. La cadena de dominio no se puede acreditar.",
            "recomendacion": "Solicitar al cliente el Certificado de Dominio Vigente actualizado del CBR competente.",
        }]

    titular_cbr = (titularidad.get("titular_actual") or "").upper()
    ultimo_comprador = (_ultimo_comprador(synthesis) or "").upper()

    if not ultimo_comprador:
        return []  # No hay escrituras de compraventa para comparar

    # Comparación tolerante: que el RUT o nombre principal aparezca en ambos
    if titular_cbr and ultimo_comprador:
        nombre_cbr = titular_cbr.split(",")[0].strip()
        nombre_acto = ultimo_comprador.split(",")[0].strip()
        if nombre_cbr and nombre_acto and nombre_cbr not in ultimo_comprador and nombre_acto not in titular_cbr:
            return [{
                "descripcion": (
                    f"El titular según el Certificado de Dominio Vigente ({nombre_cbr}) "
                    f"no coincide con el último comprador en las escrituras ({nombre_acto})."
                ),
                "detalle": {"titular_cbr": titular_cbr, "ultimo_comprador": ultimo_comprador},
                "recomendacion": (
                    "Investigar la cadena de dominio: puede haber una transferencia posterior no inscrita, "
                    "una sucesión, o un cambio de razón social/persona jurídica."
                ),
            }]
    return []


REGLAS_CADENA_DOMINIO = [
    {
        "id": "R-CD-001",
        "titulo": "Concordancia entre titular CBR y último comprador",
        "severidad": "alta",
        "categoria": "cadena_dominio",
        "check": regla_titular_concuerda,
    },
]
