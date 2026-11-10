"""Caso de uso de consulta de conta."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.access import (
    STAFF_ROLES,
    ensure_account_access,
)
from banking.modules.account.application.dto import AccountOutput
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.account.application.use_cases.list_accounts import to_output
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.shared.contracts.security import Principal


class GetAccountUseCase:
    """Consulta conta por id com ownership/RBAC."""

    def __init__(
        self,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository

    async def execute(self, principal: Principal, account_id: UUID) -> AccountOutput:
        """Retorna a conta quando autorizado."""
        account = await self._accounts.get_by_id(account_id)
        if account is None:
            raise NotFoundError("Conta não encontrada.")
        if account.is_system and principal.role not in STAFF_ROLES:
            raise NotFoundError("Conta não encontrada.")
        await ensure_account_access(principal, account, self._customers)
        return to_output(account)
