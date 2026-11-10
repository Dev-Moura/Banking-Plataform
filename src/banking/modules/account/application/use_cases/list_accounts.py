"""Caso de uso de listagem de contas."""

from __future__ import annotations

from banking.modules.account.application.dto import AccountOutput
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.account.domain.entities import Account
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.shared.application.pagination import Page, normalize_pagination
from banking.shared.contracts.security import Principal, Role

STAFF_ROLES = frozenset({Role.BANK_OPERATOR, Role.BANK_ADMIN, Role.AUDITOR})


def to_output(account: Account) -> AccountOutput:
    """Converte entidade de conta em DTO."""
    return AccountOutput(
        id=account.id,
        customer_id=account.customer_id,
        account_number=account.account_number,
        account_type=account.account_type,
        status=account.status,
        currency=account.currency,
        balance=account.balance,
        created_at=account.created_at,
    )


class ListAccountsUseCase:
    """Lista contas visíveis ao principal autenticado."""

    def __init__(
        self,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository

    async def execute(
        self,
        principal: Principal,
        status: str | None,
        page: int,
        page_size: int,
    ) -> Page[AccountOutput]:
        """Retorna contas do cliente ou todas para staff."""
        safe_page, safe_size, offset = normalize_pagination(page, page_size)

        if principal.role in STAFF_ROLES:
            accounts, total = await self._accounts.list_all(status, offset, safe_size)
        else:
            customer = await self._customers.get_by_user_id(principal.user_id)
            if customer is None:
                return Page(items=[], page=safe_page, page_size=safe_size, total=0)
            accounts, total = await self._accounts.list_by_customer(
                customer.id, status, offset, safe_size
            )

        return Page(
            items=[to_output(account) for account in accounts],
            page=safe_page,
            page_size=safe_size,
            total=total,
        )
