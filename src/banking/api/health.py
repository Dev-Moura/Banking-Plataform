"""Endpoints de liveness e readiness."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from banking.core.problem_details import problem_response
from banking.infrastructure.cache.redis import get_redis
from banking.infrastructure.database.session import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Indica que o processo está vivo."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def readiness(request: Request) -> JSONResponse:
    """Verifica PostgreSQL e Redis antes de declarar prontidão."""
    checks: dict[str, str] = {}

    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.warning("Readiness: banco indisponível")
        checks["database"] = "unavailable"

    try:
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception:
        logger.warning("Readiness: redis indisponível")
        checks["redis"] = "unavailable"

    if all(value == "ok" for value in checks.values()):
        return JSONResponse(status_code=200, content={"status": "ready", **checks})

    return problem_response(
        request,
        status=503,
        title="Service Unavailable",
        type_uri="https://moura-banking.local/problems/service-unavailable",
        detail="Dependências obrigatórias indisponíveis.",
        errors=[
            {"dependency": name, "status": status} for name, status in checks.items()
        ],
    )
