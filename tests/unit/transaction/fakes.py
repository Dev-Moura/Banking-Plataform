"""Dublês em memória para testes de transações e ledger."""

from __future__ import annotations

from uuid import UUID

from banking.modules.ledger.domain.entities import LedgerEntry
from banking.modules.transaction.domain.entities import Transaction


class FakeTransactionRepository:
    """Repositório de transações em memória."""

    def __init__(self) -> None:
        self.transactions: dict[UUID, Transaction] = {}

    async def add(self, transaction: Transaction) -> None:
        self.transactions[transaction.id] = transaction

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self.transactions.get(transaction_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        return next(
            (
                transaction
                for transaction in self.transactions.values()
                if transaction.idempotency_key == idempotency_key
            ),
            None,
        )

    async def list_all(
        self,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]:
        items = [
            transaction
            for transaction in self.transactions.values()
            if (status is None or transaction.status == status)
            and (
                account_id is None
                or transaction.source_account_id == account_id
                or transaction.destination_account_id == account_id
            )
        ]
        return items[offset : offset + limit], len(items)

    async def list_for_customer(
        self,
        customer_id: UUID,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]:
        return await self.list_all(status, account_id, offset, limit)


class FakeLedgerEntryRepository:
    """Repositório de lançamentos em memória."""

    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []

    async def add_many(self, entries: list[LedgerEntry]) -> None:
        self.entries.extend(entries)

    async def list_by_account(
        self,
        account_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[LedgerEntry], int]:
        items = [entry for entry in self.entries if entry.account_id == account_id]
        return items[offset : offset + limit], len(items)

    async def list_by_transaction(self, transaction_id: UUID) -> list[LedgerEntry]:
        return [
            entry for entry in self.entries if entry.transaction_id == transaction_id
        ]
