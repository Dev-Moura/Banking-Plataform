"""Portas de aplicação do módulo de ledger."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from banking.modules.ledger.domain.entities import LedgerEntry


class LedgerEntryRepository(Protocol):
    """Abstração de persistência de lançamentos contábeis."""

    async def add_many(self, entries: Sequence[LedgerEntry]) -> None: ...

    async def list_by_account(
        self,
        account_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[LedgerEntry], int]: ...

    async def list_by_transaction(self, transaction_id: UUID) -> list[LedgerEntry]: ...
