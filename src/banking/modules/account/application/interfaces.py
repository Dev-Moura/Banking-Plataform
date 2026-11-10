"""Portas de aplicação do módulo de contas."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from banking.modules.account.domain.entities import Account


class AccountRepository(Protocol):
    """Abstração de persistência de contas."""

    async def add(self, account: Account) -> Account: ...

    async def get_by_id(self, account_id: UUID) -> Account | None: ...

    async def get_many(self, account_ids: Sequence[UUID]) -> dict[UUID, Account]: ...

    async def get_many_for_update(
        self, account_ids: Sequence[UUID]
    ) -> dict[UUID, Account]: ...

    async def update_balances(self, accounts: Sequence[Account]) -> None: ...

    async def list_by_customer(
        self,
        customer_id: UUID,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]: ...

    async def list_all(
        self,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]: ...

    async def update_status(self, account: Account) -> None: ...
