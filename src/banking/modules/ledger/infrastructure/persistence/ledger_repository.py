"""Repositório SQLAlchemy de lançamentos contábeis."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.ledger.domain.entities import LedgerEntry
from banking.modules.ledger.infrastructure.persistence.models import (
    LedgerEntry as LedgerEntryModel,
)


def _to_domain(row: LedgerEntryModel) -> LedgerEntry:
    return LedgerEntry(
        id=row.id,
        transaction_id=row.transaction_id,
        account_id=row.account_id,
        entry_type=row.entry_type,
        amount=row.amount,
        balance_after=row.balance_after,
        currency=row.currency,
        created_at=row.created_at,
    )


class SqlAlchemyLedgerEntryRepository:
    """Implementação de LedgerEntryRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, entries: Sequence[LedgerEntry]) -> None:
        """Persiste lançamentos contábeis."""
        self._session.add_all(
            [
                LedgerEntryModel(
                    id=entry.id,
                    transaction_id=entry.transaction_id,
                    account_id=entry.account_id,
                    entry_type=entry.entry_type,
                    amount=entry.amount,
                    balance_after=entry.balance_after,
                    currency=entry.currency,
                    created_at=entry.created_at,
                )
                for entry in entries
            ]
        )
        await self._session.flush()

    async def list_by_account(
        self,
        account_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[LedgerEntry], int]:
        """Lista lançamentos da conta em ordem cronológica."""
        total = await self._session.scalar(
            select(func.count())
            .select_from(LedgerEntryModel)
            .where(LedgerEntryModel.account_id == account_id)
        )
        result = await self._session.execute(
            select(LedgerEntryModel)
            .where(LedgerEntryModel.account_id == account_id)
            .order_by(LedgerEntryModel.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.scalars().all()
        return [_to_domain(row) for row in rows], int(total or 0)

    async def list_by_transaction(self, transaction_id: UUID) -> list[LedgerEntry]:
        """Lista lançamentos de uma transação."""
        result = await self._session.execute(
            select(LedgerEntryModel)
            .where(LedgerEntryModel.transaction_id == transaction_id)
            .order_by(LedgerEntryModel.entry_type.asc())
        )
        return [_to_domain(row) for row in result.scalars().all()]
