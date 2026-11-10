"""Configuração global de testes e fixtures de banco."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "testing-secret-key-not-for-production")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://banking:banking@localhost:5432/banking_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://banking:banking@localhost:5432/banking_test",
)
REPO_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


def _connection_kwargs(url_str: str, database: str | None) -> dict[str, Any]:
    """Monta parâmetros de conexão do asyncpg a partir da URL SQLAlchemy."""
    url = make_url(url_str)
    return {
        "host": url.host,
        "port": url.port or 5432,
        "user": url.username,
        "password": url.password,
        "database": database,
    }


async def _create_database_if_missing() -> None:
    """Cria o banco de teste quando ele ainda não existe."""
    url = make_url(TEST_DATABASE_URL)
    connection = await asyncpg.connect(
        **_connection_kwargs(TEST_DATABASE_URL, "postgres")
    )
    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            url.database,
        )
        if not exists:
            await connection.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await connection.close()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """URL do banco isolado utilizado pelos testes de integração."""
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def ensure_test_database() -> None:
    """Garante a existência do banco de teste sem tocar no banco de dev."""
    asyncio.run(_create_database_if_missing())


@pytest.fixture(scope="session")
def alembic_config(ensure_test_database: None) -> Config:
    """Configuração do Alembic apontando para o banco de teste."""
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    config.set_main_option("prepend_sys_path", str(REPO_ROOT / "src"))
    config.set_main_option("path_separator", "os")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return config


@pytest.fixture(scope="session")
def migrated_database(alembic_config: Config) -> Iterator[None]:
    """Recria o schema de teste na última revisão antes dos testes."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture(scope="session")
def fetch_all(
    test_database_url: str,
) -> Callable[..., list[asyncpg.Record]]:
    """Executa uma query síncrona de inspeção no banco de teste."""

    def _fetch(query: str, *args: Any) -> list[asyncpg.Record]:
        async def _run() -> list[asyncpg.Record]:
            connection = await asyncpg.connect(
                **_connection_kwargs(
                    test_database_url,
                    make_url(test_database_url).database,
                )
            )
            try:
                return await connection.fetch(query, *args)
            finally:
                await connection.close()

        return asyncio.run(_run())

    return _fetch


@pytest.fixture
async def db_engine(migrated_database: None) -> AsyncIterator[AsyncEngine]:
    """Engine assíncrona isolada por teste, sem pool persistente."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Sessão cujas alterações são revertidas ao final de cada teste."""
    session = AsyncSession(bind=db_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest.fixture
async def clean_db(db_engine: AsyncEngine) -> AsyncIterator[None]:
    """Limpa as tabelas antes de cada teste que persiste dados reais."""
    from sqlalchemy import text

    async with db_engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE audit_events, ledger_entries, transactions, "
                "accounts, customers, refresh_sessions, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture
async def api_client(db_session: AsyncSession, clean_db: None) -> AsyncIterator[Any]:
    """Cliente HTTP com a sessão de teste injetada na aplicação."""
    import httpx

    from banking.infrastructure.database.session import get_session
    from banking.main import create_app

    app = create_app()

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
