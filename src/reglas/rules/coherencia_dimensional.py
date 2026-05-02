"""
Reglas dimensionales: superficies en avalúo SII vs plano vs escritura.
Tolerancia: 1 m² (configurable).
"""
from src.reglas.rules._helpers import find_node

TOLERANCIA_M2 = 1.0


def regla_superficie_construida(synthesis: dict) -> list[dict]:
    sii = find_node(synthesis, lambda n: n.get("source") == "cert_avaluo_sii")
    plano = find_node(synthesis, lambda n: n.get("source") == "plano_propiedad")

    if not sii or not plano:
        return []

    s_sii = sii.get("superficie_construida_m2")
    s_plano = plano.get("superficie_construida_m2")
    if s_sii is None or s_plano is None:
        return []

    diff = abs(float(s_sii) - float(s_plano))
    if diff > TOLERANCIA_M2:
        return [{
            "descripcion": (
                f"La superficie construida en el avalúo SII ({s_sii} m²) difiere del plano ({s_plano} m²) "
                f"en {diff:.2f} m²."
            ),
            "detalle": {"sii": s_sii, "plano": s_plano, "diferencia_m2": diff, "tolerancia_m2": TOLERANCIA_M2},
            "recomendacion": "Confirmar superficies en terreno o solicitar regularización si corresponde.",
        }]
    return []


REGLAS_COHERENCIA_DIMENSIONAL = [
    {
        "id": "R-CD-D-001",
        "titulo": "Coherencia de superficie construida (SII vs plano)",
        "severidad": "media",
        "categoria": "dimensional",
        "check": regla_superficie_construida,
    },
]
