"""Repositório SQLAlchemy de transações."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.account.infrastructure.persistence.models import (
    Account as AccountModel,
)
from banking.modules.transaction.domain.entities import Transaction
from banking.modules.transaction.infrastructure.persistence.models import (
    Transaction as TransactionModel,
)


def _to_domain(row: TransactionModel) -> Transaction:
    return Transaction(
        id=row.id,
        source_account_id=row.source_account_id,
        destination_account_id=row.destination_account_id,
        amount=row.amount,
        currency=row.currency,
        status=row.status,
        idempotency_key=row.idempotency_key,
        request_hash=row.request_hash,
        description=row.description,
        created_by_user_id=row.created_by_user_id,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _filters(
    status: str | None,
    account_id: UUID | None,
    customer_id: UUID | None,
) -> list[object]:
    conditions: list[object] = []
    if status is not None:
        conditions.append(TransactionModel.status == status)
    if account_id is not None:
        conditions.append(
            or_(
                TransactionModel.source_account_id == account_id,
                TransactionModel.destination_account_id == account_id,
            )
        )
    if customer_id is not None:
        customer_accounts = select(AccountModel.id).where(
            AccountModel.customer_id == customer_id
        )
        conditions.append(
            or_(
                TransactionModel.source_account_id.in_(customer_accounts),
                TransactionModel.destination_account_id.in_(customer_accounts),
            )
        )
    return conditions


class SqlAlchemyTransactionRepository:
    """Implementação de TransactionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transaction: Transaction) -> None:
        """Persiste a transação."""
        self._session.add(
            TransactionModel(
                id=transaction.id,
                source_account_id=transaction.source_account_id,
                destination_account_id=transaction.destination_account_id,
                amount=transaction.amount,
                currency=transaction.currency,
                status=transaction.status,
                idempotency_key=transaction.idempotency_key,
                request_hash=transaction.request_hash,
                description=transaction.description,
                created_by_user_id=transaction.created_by_user_id,
                completed_at=transaction.completed_at,
                created_at=transaction.created_at,
                updated_at=transaction.updated_at,
            )
        )
        await self._session.flush()

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        """Busca transação por identificador."""
        row = await self._session.get(TransactionModel, transaction_id)
        return _to_domain(row) if row is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        """Busca transação pela chave de idempotência."""
        result = await self._session.execute(
            select(TransactionModel).where(
                TransactionModel.idempotency_key == idempotency_key
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def list_all(
        self,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]:
        """Lista transações de todos os clientes."""
        return await self._paginate(_filters(status, account_id, None), offset, limit)

    async def list_for_customer(
        self,
        customer_id: UUID,
        status: str | None,
        account_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]:
        """Lista transações em que o cliente participa."""
        return await self._paginate(
            _filters(status, account_id, customer_id), offset, limit
        )

    async def _paginate(
        self,
        conditions: list[object],
        offset: int,
        limit: int,
    ) -> tuple[list[Transaction], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(TransactionModel).where(*conditions)
        )
        result = await self._session.execute(
            select(TransactionModel)
            .where(*conditions)
            .order_by(TransactionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.scalars().all()
        return [_to_domain(row) for row in rows], int(total or 0)
