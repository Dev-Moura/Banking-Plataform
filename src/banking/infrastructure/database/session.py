"""Engine e fábrica de sessões assíncronas."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from banking.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Cria (uma vez) a engine assíncrona do PostgreSQL."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Retorna a fábrica de sessões assíncronas."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency do FastAPI que fornece uma sessão por requisição."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Fecha o pool de conexões no encerramento da aplicação."""
    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
