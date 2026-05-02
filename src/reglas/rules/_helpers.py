"""Helpers comunes para las reglas legales."""
from datetime import datetime
from typing import Iterable

from dateutil import parser as dparser


def find_node(synthesis: dict, predicate) -> dict | None:
    nodes = (synthesis.get("grafo") or {}).get("nodes") or []
    for n in nodes:
        if predicate(n):
            return n
    return None


def all_nodes(synthesis: dict) -> Iterable[dict]:
    return (synthesis.get("grafo") or {}).get("nodes") or []


def parse_chilean_date(s: str | None) -> datetime | None:
    """Parser permisivo de fechas chilenas: '12 de marzo de 2022', '12-03-2022', '2022-03-12'."""
    if not s:
        return None
    try:
        return dparser.parse(s, dayfirst=True, fuzzy=True)
    except Exception:  # noqa: BLE001
        return None


def days_between(a: datetime, b: datetime) -> int:
    return abs((a - b).days)
