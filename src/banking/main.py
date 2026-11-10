"""Ponto de entrada da aplicação FastAPI."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from banking.api.router import api_router
from banking.core.config import get_settings
from banking.core.logging import configure_logging
from banking.core.middleware import (
    CorrelationIdMiddleware,
    MaxBodySizeMiddleware,
    SecurityHeadersMiddleware,
)
from banking.core.problem_details import register_exception_handlers
from banking.infrastructure.cache.redis import close_redis
from banking.infrastructure.database.session import dispose_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gerencia recursos de longa duração da aplicação."""
    settings = get_settings()
    configure_logging(logging.DEBUG if settings.app_debug else logging.INFO)
    logger.info(
        "Aplicação iniciada",
        extra={"app_env": settings.app_env},
    )
    try:
        yield
    finally:
        await dispose_engine()
        try:
            await close_redis()
        except Exception:  # pragma: no cover - encerramento best-effort
            logger.warning("Falha ao encerrar Redis")
        logger.info("Aplicação encerrada")


def create_app() -> FastAPI:
    """Cria e configura a instância FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Plataforma bancária educacional com FastAPI, DDD e Clean Architecture. "
            "Não processa dinheiro real."
        ),
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(MaxBodySizeMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
