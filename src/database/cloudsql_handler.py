"""
CloudSQLHandler — lee dt_sintetizador, persiste hallazgos en dt_hallazgos.
"""
import json
import logging
import os
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy import text

from src.core.config import settings

logger = logging.getLogger(__name__)


class CloudSQLHandler:
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory = None

    def _build_url(self) -> str:
        if os.environ.get("K_SERVICE") and settings.INSTANCE_CONNECTION_NAME:
            return (
                f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@/{settings.DB_NAME}?host=/cloudsql/{settings.INSTANCE_CONNECTION_NAME}"
            )
        return (
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

    async def initialize(self):
        self.engine = create_async_engine(self._build_url(), pool_pre_ping=True, pool_size=5)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def health_check(self) -> bool:
        if not self.engine:
            return False
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("health_check failed: %s", exc)
            return False

    async def get_synthesis(self, folio: str) -> dict | None:
        sql = text(
            """
            SELECT datos, version
            FROM dt_sintetizador
            WHERE folio = :folio
            ORDER BY version DESC LIMIT 1
            """
        )
        async with self.session_factory() as session:
            row = (await session.execute(sql, {"folio": folio})).mappings().first()
        return dict(row) if row else None

    async def get_estudio_id(self, folio: str) -> int | None:
        sql = text("SELECT id_estudio FROM dt_estudio WHERE folio = :folio AND eliminado = FALSE")
        async with self.session_factory() as session:
            row = (await session.execute(sql, {"folio": folio})).first()
        return row[0] if row else None

    async def save_hallazgos(self, folio: str, hallazgos: list[dict]) -> int:
        id_estudio = await self.get_estudio_id(folio)
        if not id_estudio:
            return 0

        async with self.session_factory() as session:
            # Limpiar hallazgos anteriores que vienen del verificador automático
            await session.execute(
                text("DELETE FROM dt_hallazgos WHERE id_estudio = :id AND fuente = 'verificador'"),
                {"id": id_estudio},
            )

            insert_sql = text(
                """
                INSERT INTO dt_hallazgos (
                  id_estudio, regla_id, severidad, titulo, descripcion,
                  detalle, recomendacion, fuente, fecha
                ) VALUES (
                  :id_estudio, :regla_id, :severidad, :titulo, :descripcion,
                  CAST(:detalle AS JSONB), :recomendacion, 'verificador', NOW()
                )
                """
            )
            for h in hallazgos:
                await session.execute(insert_sql, {
                    "id_estudio": id_estudio,
                    "regla_id": h["regla_id"],
                    "severidad": h["severidad"],
                    "titulo": h["titulo"],
                    "descripcion": h.get("descripcion", ""),
                    "detalle": json.dumps(h.get("detalle") or {}),
                    "recomendacion": h.get("recomendacion"),
                })

            # Actualizar el estado del estudio si hay hallazgos críticos
            if any(h["severidad"] in ("alta", "critica") for h in hallazgos):
                await session.execute(
                    text("UPDATE dt_estudio SET id_estado = (SELECT id FROM dt_estados_estudio WHERE codigo = 'observado') WHERE id_estudio = :id"),
                    {"id": id_estudio},
                )
            elif hallazgos:
                # Hallazgos menores: mantener en análisis
                pass
            else:
                await session.execute(
                    text("UPDATE dt_estudio SET id_estado = (SELECT id FROM dt_estados_estudio WHERE codigo = 'verificado') WHERE id_estudio = :id"),
                    {"id": id_estudio},
                )

            await session.commit()
        return len(hallazgos)

    async def list_hallazgos(self, folio: str) -> list[dict]:
        sql = text(
            """
            SELECT h.* FROM dt_hallazgos h
            JOIN dt_estudio e ON e.id_estudio = h.id_estudio
            WHERE e.folio = :folio
            ORDER BY
              CASE h.severidad WHEN 'critica' THEN 0 WHEN 'alta' THEN 1
                               WHEN 'media' THEN 2 WHEN 'baja' THEN 3 ELSE 4 END,
              h.fecha DESC
            """
        )
        async with self.session_factory() as session:
            rows = (await session.execute(sql, {"folio": folio})).mappings().all()
        return [dict(r) for r in rows]

    async def close(self):
        if self.engine:
            await self.engine.dispose()
