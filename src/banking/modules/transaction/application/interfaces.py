"""Portas de aplicação do módulo de transações."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from banking.modules.transaction.domain.entities import Transaction


class TransactionRepository(Protocol):
    """Abstração de persistência de transações."""

    async def add(self, transaction: Transaction) -> None: ...

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None: ...

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Transaction | None: ...

    async def list_all(
        self,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]: ...

    async def list_for_customer(
        self,
        customer_id: UUID,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]: ...
