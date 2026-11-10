"""Caso de uso de extrato contábil por conta."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.access import (
    STAFF_ROLES,
    ensure_account_access,
)
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.ledger.application.dto import LedgerEntryOutput
from banking.modules.ledger.application.interfaces import LedgerEntryRepository
from banking.modules.ledger.domain.entities import LedgerEntry
from banking.shared.application.pagination import Page, normalize_pagination
from banking.shared.contracts.security import Principal


def to_output(entry: LedgerEntry) -> LedgerEntryOutput:
    """Converte lançamento em DTO."""
    return LedgerEntryOutput(
        id=entry.id,
        transaction_id=entry.transaction_id,
        account_id=entry.account_id,
        entry_type=entry.entry_type,
        amount=entry.amount,
        balance_after=entry.balance_after,
        currency=entry.currency,
        created_at=entry.created_at,
    )


class GetAccountStatementUseCase:
    """Retorna os lançamentos de uma conta autorizada."""

    def __init__(
        self,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
        ledger_repository: LedgerEntryRepository,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository
        self._ledger = ledger_repository

    async def execute(
        self,
        principal: Principal,
        account_id: UUID,
        page: int,
        page_size: int,
    ) -> Page[LedgerEntryOutput]:
        """Lista o extrato paginado da conta."""
        account = await self._accounts.get_by_id(account_id)
        if account is None:
            raise NotFoundError("Conta não encontrada.")
        if account.is_system and principal.role not in STAFF_ROLES:
            raise NotFoundError("Conta não encontrada.")
        await ensure_account_access(principal, account, self._customers)

        safe_page, safe_size, offset = normalize_pagination(page, page_size)
        entries, total = await self._ledger.list_by_account(
            account_id, offset, safe_size
        )
        return Page(
            items=[to_output(entry) for entry in entries],
            page=safe_page,
            page_size=safe_size,
            total=total,
        )
