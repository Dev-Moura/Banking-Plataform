"""Caso de uso de listagem de transações."""

from __future__ import annotations

from uuid import UUID

from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.transaction.application.dto import TransactionOutput
from banking.modules.transaction.application.interfaces import TransactionRepository
from banking.modules.transaction.application.use_cases.transfer import to_output
from banking.shared.application.pagination import Page, normalize_pagination
from banking.shared.contracts.security import Principal, Role

STAFF_ROLES = frozenset({Role.BANK_OPERATOR, Role.BANK_ADMIN, Role.AUDITOR})


class ListTransactionsUseCase:
    """Lista transações visíveis ao principal autenticado."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._customers = customer_repository

    async def execute(
        self,
        principal: Principal,
        status: str | None,
        account_id: UUID | None,
        page: int,
        page_size: int,
    ) -> Page[TransactionOutput]:
        """Retorna transações do cliente ou todas para staff."""
        safe_page, safe_size, offset = normalize_pagination(page, page_size)

        if principal.role in STAFF_ROLES:
            items, total = await self._transactions.list_all(
                status, account_id, offset, safe_size
            )
        else:
            customer = await self._customers.get_by_user_id(principal.user_id)
            if customer is None:
                return Page(items=[], page=safe_page, page_size=safe_size, total=0)
            items, total = await self._transactions.list_for_customer(
                customer.id, status, account_id, offset, safe_size
            )

        return Page(
            items=[to_output(transaction) for transaction in items],
            page=safe_page,
            page_size=safe_size,
            total=total,
        )
