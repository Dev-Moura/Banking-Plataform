"""Repositório SQLAlchemy de contas."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.account.domain.entities import Account
from banking.modules.account.infrastructure.persistence.models import (
    Account as AccountModel,
)

ACCOUNT_NUMBER_NEXTVAL = "SELECT nextval('account_number_seq')"


def _to_domain(row: AccountModel) -> Account:
    return Account(
        id=row.id,
        customer_id=row.customer_id,
        account_number=row.account_number,
        account_type=row.account_type,
        status=row.status,
        currency=row.currency,
        balance=row.balance,
        is_system=row.is_system,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyAccountRepository:
    """Implementação de AccountRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: Account) -> Account:
        """Persiste a conta gerando o número via sequência do banco."""
        number = await self._session.scalar(text(ACCOUNT_NUMBER_NEXTVAL))
        row = AccountModel(
            id=account.id,
            customer_id=account.customer_id,
            account_number=int(number),
            account_type=account.account_type,
            status=account.status,
            currency=account.currency,
            balance=account.balance,
            is_system=account.is_system,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        account.account_number = int(number)
        return account

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """Busca conta por identificador."""
        row = await self._session.get(AccountModel, account_id)
        return _to_domain(row) if row is not None else None

    async def get_many(self, account_ids: Sequence[UUID]) -> dict[UUID, Account]:
        """Carrega contas por identificador."""
        if not account_ids:
            return {}
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id.in_(account_ids))
        )
        return {row.id: _to_domain(row) for row in result.scalars().all()}

    async def get_many_for_update(
        self, account_ids: Sequence[UUID]
    ) -> dict[UUID, Account]:
        """Carrega e bloqueia contas em ordem determinística."""
        locked: dict[UUID, Account] = {}
        for account_id in sorted(set(account_ids)):
            result = await self._session.execute(
                select(AccountModel)
                .where(AccountModel.id == account_id)
                .with_for_update()
            )
            row = result.scalar_one_or_none()
            if row is not None:
                locked[row.id] = _to_domain(row)
        return locked

    async def update_balances(self, accounts: Sequence[Account]) -> None:
        """Persiste os saldos atualizados."""
        for account in accounts:
            row = await self._session.get(AccountModel, account.id)
            if row is None:
                continue
            row.balance = account.balance
            row.updated_at = account.updated_at
        await self._session.flush()

    async def list_by_customer(
        self,
        customer_id: UUID,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]:
        """Lista contas de um cliente."""
        conditions = [
            AccountModel.customer_id == customer_id,
            AccountModel.is_system.is_(False),
        ]
        if status is not None:
            conditions.append(AccountModel.status == status)
        return await self._paginate(conditions, offset, limit)

    async def list_all(
        self,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]:
        """Lista contas não sistêmicas de todos os clientes."""
        conditions = [AccountModel.is_system.is_(False)]
        if status is not None:
            conditions.append(AccountModel.status == status)
        return await self._paginate(conditions, offset, limit)

    async def _paginate(
        self,
        conditions: list[object],
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(AccountModel).where(*conditions)
        )
        result = await self._session.execute(
            select(AccountModel)
            .where(*conditions)
            .order_by(AccountModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.scalars().all()
        return [_to_domain(row) for row in rows], int(total or 0)

    async def update_status(self, account: Account) -> None:
        """Atualiza status e timestamp da conta."""
        row = await self._session.get(AccountModel, account.id)
        if row is None:
            return
        row.status = account.status
        row.updated_at = account.updated_at
        await self._session.flush()
