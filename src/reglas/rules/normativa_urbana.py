"""
Reglas de normativa urbana: confronta el destino/uso de la propiedad
con la zonificación del plan regulador.
"""
from src.reglas.rules._helpers import find_node


# Mapping rough de destinos SII → categorías de uso del plan regulador.
DESTINO_A_USO = {
    "habitacional":  "residencial",
    "vivienda":      "residencial",
    "comercial":     "comercio",
    "industrial":    "industria",
    "oficina":       "oficina",
    "agrícola":      "rural",
    "agricola":      "rural",
}


def regla_uso_permitido(synthesis: dict) -> list[dict]:
    sii = find_node(synthesis, lambda n: n.get("source") == "cert_avaluo_sii")
    pr = find_node(synthesis, lambda n: n.get("source") == "plan_regulador")
    if not sii or not pr:
        return []

    destino = (sii.get("destino") or "").lower().strip()
    if not destino:
        return []
    uso_canon = DESTINO_A_USO.get(destino)
    if not uso_canon:
        return []

    permitidos = [u.lower() for u in (pr.get("usos_permitidos") or [])]
    if not permitidos:
        return []

    # Match laxo: el uso canónico aparece como substring de algún permitido
    if not any(uso_canon in p for p in permitidos):
        return [{
            "descripcion": (
                f"El destino del inmueble según SII es '{destino}' (uso canónico '{uso_canon}'), "
                f"pero la zonificación '{pr.get('zonificacion')}' del plan regulador solo permite: "
                f"{', '.join(pr.get('usos_permitidos') or [])}."
            ),
            "detalle": {
                "destino_sii": destino, "uso_canon": uso_canon,
                "zonificacion": pr.get("zonificacion"),
                "usos_permitidos": pr.get("usos_permitidos"),
            },
            "recomendacion": (
                "Revisar Certificado de Informaciones Previas o solicitar cambio de uso de suelo si corresponde. "
                "El destino actual podría no estar regularizado."
            ),
        }]
    return []


REGLAS_NORMATIVA_URBANA = [
    {
        "id": "R-N-001",
        "titulo": "Uso del suelo coherente con plan regulador",
        "severidad": "alta",
        "categoria": "normativa",
        "check": regla_uso_permitido,
    },
]
