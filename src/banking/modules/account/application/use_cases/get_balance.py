"""Caso de uso de consulta de saldo."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.access import (
    STAFF_ROLES,
    ensure_account_access,
)
from banking.modules.account.application.dto import BalanceOutput
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.identity.application.interfaces import Clock
from banking.shared.contracts.security import Principal


class GetBalanceUseCase:
    """Consulta o saldo de uma conta autorizada."""

    def __init__(
        self,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
        clock: Clock,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository
        self._clock = clock

    async def execute(self, principal: Principal, account_id: UUID) -> BalanceOutput:
        """Retorna saldo e moeda da conta."""
        account = await self._accounts.get_by_id(account_id)
        if account is None:
            raise NotFoundError("Conta não encontrada.")
        if account.is_system and principal.role not in STAFF_ROLES:
            raise NotFoundError("Conta não encontrada.")
        await ensure_account_access(principal, account, self._customers)
        return BalanceOutput(
            account_id=account.id,
            balance=account.balance,
            currency=account.currency,
            as_of=self._clock.now(),
        )
