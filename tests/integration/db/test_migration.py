"""Testes de integração das migrations Alembic."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "users",
    "customers",
    "refresh_sessions",
    "accounts",
    "transactions",
    "ledger_entries",
    "audit_events",
}

FetchAll = Callable[..., list[asyncpg.Record]]


def _table_names(fetch_all: FetchAll) -> set[str]:
    rows = fetch_all("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return {row["tablename"] for row in rows}


@pytest.fixture
def schema_at_base(alembic_config: Config) -> Iterator[None]:
    """Inicia o teste com o schema removido e restaura ao final."""
    command.downgrade(alembic_config, "base")
    yield
    command.upgrade(alembic_config, "head")


@pytest.fixture
def schema_at_head(alembic_config: Config) -> Iterator[None]:
    """Inicia o teste com o schema no head e restaura ao final."""
    command.upgrade(alembic_config, "head")
    yield
    command.upgrade(alembic_config, "head")


def test_upgrade_creates_expected_schema(
    alembic_config: Config,
    schema_at_base: None,
    fetch_all: FetchAll,
) -> None:
    """O upgrade deve criar tabelas, sequência, função e trigger."""
    command.upgrade(alembic_config, "head")

    assert _table_names(fetch_all) >= EXPECTED_TABLES

    sequence_rows = fetch_all(
        "SELECT start_value FROM pg_sequences "
        "WHERE schemaname = 'public' AND sequencename = 'account_number_seq'"
    )
    assert len(sequence_rows) == 1
    assert sequence_rows[0]["start_value"] == 10_000_001

    function_rows = fetch_all(
        "SELECT proname FROM pg_proc WHERE proname = 'prevent_ledger_mutation'"
    )
    assert function_rows

    trigger_rows = fetch_all(
        "SELECT tgname FROM pg_trigger "
        "WHERE tgname = 'trg_ledger_entries_immutable' AND NOT tgisinternal"
    )
    assert trigger_rows


def test_downgrade_removes_schema(
    alembic_config: Config,
    schema_at_head: None,
    fetch_all: FetchAll,
) -> None:
    """O downgrade deve remover tabelas, sequência, função e trigger."""
    command.downgrade(alembic_config, "base")

    assert EXPECTED_TABLES.isdisjoint(_table_names(fetch_all))

    function_rows = fetch_all(
        "SELECT proname FROM pg_proc WHERE proname = 'prevent_ledger_mutation'"
    )
    assert not function_rows

    sequence_rows = fetch_all(
        "SELECT sequencename FROM pg_sequences "
        "WHERE sequencename = 'account_number_seq'"
    )
    assert not sequence_rows


def test_upgrade_downgrade_upgrade_cycle(
    alembic_config: Config,
    schema_at_head: None,
    fetch_all: FetchAll,
) -> None:
    """O ciclo completo deve ser reversível e reaplicável."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    assert _table_names(fetch_all) >= EXPECTED_TABLES
