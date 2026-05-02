"""
verificacion-legal-api · FastAPI principal
--------------------------------------------------------------
  GET  /health
  GET  /reglas                     → listado del catálogo de reglas
  POST /verificar                  → corre todas las reglas sobre el estudio
  GET  /hallazgos/{folio}          → últimos hallazgos persistidos en dt_hallazgos
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings  # noqa: E402
from src.core.structured_logging import configure_logging  # noqa: E402
from src.database.cloudsql_handler import CloudSQLHandler  # noqa: E402
from src.middleware.analytics import AnalyticsMiddleware  # noqa: E402
from src.middleware.oauth import GoogleOAuthMiddleware  # noqa: E402
from src.reglas import REGLAS, ejecutar_reglas  # noqa: E402
from src.utils.responses import error_response, success_response  # noqa: E402

configure_logging()
logger = logging.getLogger(__name__)

db: Optional[CloudSQLHandler] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global db
    logger.info("Starting verificacion-legal-api...")
    db = CloudSQLHandler()
    try:
        await db.initialize()
    except Exception as exc:  # noqa: BLE001
        logger.warning("CloudSQL init failed: %s", exc)
    yield
    if db:
        await db.close()


app = FastAPI(
    title="verificacion-legal-api",
    description="Aplica reglas legales sobre la síntesis del estudio hipotecario.",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])
app.add_middleware(AnalyticsMiddleware)
app.add_middleware(GoogleOAuthMiddleware)


class VerificarRequest(BaseModel):
    folio: str
    persistir: bool = True


@app.get("/health")
async def health():
    db_ok = await db.health_check() if db else False
    return success_response(data={
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "database": "ok" if db_ok else "error",
        "n_reglas": len(REGLAS),
    })


@app.get("/reglas")
async def listar_reglas():
    out = [
        {
            "id": r["id"],
            "titulo": r["titulo"],
            "severidad": r["severidad"],
            "categoria": r["categoria"],
        }
        for r in REGLAS
    ]
    return success_response(data=out)


@app.post("/verificar")
async def verificar(req: VerificarRequest):
    if not db:
        return error_response("DB no inicializada", code="NOT_READY", status_code=503)

    # 1) Obtener síntesis (de la BDD; fallback a llamar al sintetizador-api)
    synth = await db.get_synthesis(req.folio)
    if not synth:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.SINTETIZADOR_URL}/synthesize",
                    json={"folio": req.folio, "force": False},
                )
                if resp.is_success:
                    body = resp.json()
                    synth = {"datos": body.get("data") or body, "version": (body.get("data") or {}).get("version")}
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo invocar sintetizador-api: %s", exc)

    if not synth:
        return error_response(
            f"No hay síntesis para el folio {req.folio}. Genérela primero en sintetizador-api.",
            code="NO_SYNTHESIS",
            status_code=404,
        )

    synthesis_data = synth.get("datos") or {}

    # 2) Ejecutar reglas
    hallazgos = ejecutar_reglas(synthesis_data)

    # 3) Persistir
    if req.persistir:
        try:
            await db.save_hallazgos(req.folio, hallazgos)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not persist hallazgos: %s", exc)

    # 4) Resumen por severidad
    resumen = {"critica": 0, "alta": 0, "media": 0, "baja": 0, "info": 0}
    for h in hallazgos:
        sev = h.get("severidad") or "info"
        resumen[sev] = resumen.get(sev, 0) + 1

    return success_response(
        data={
            "folio": req.folio,
            "hallazgos": hallazgos,
            "resumen_severidad": resumen,
            "n_total": len(hallazgos),
        },
        message=(
            f"Verificación completada: {len(hallazgos)} hallazgos. "
            f"Críticos: {resumen.get('critica', 0)}, Altos: {resumen.get('alta', 0)}."
        ),
    )


@app.get("/hallazgos/{folio}")
async def listar_hallazgos(folio: str):
    if not db:
        return error_response("DB no inicializada", code="NOT_READY", status_code=503)
    items = await db.list_hallazgos(folio)
    return success_response(data=items, message=f"{len(items)} hallazgos para {folio}")
