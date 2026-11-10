"""Regras de acesso compartilhadas do módulo de transações."""

from __future__ import annotations

from banking.core.exceptions import ForbiddenError
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.transaction.domain.entities import Transaction
from banking.shared.contracts.security import Principal, Role

STAFF_ROLES = frozenset({Role.BANK_OPERATOR, Role.BANK_ADMIN, Role.AUDITOR})


async def ensure_transaction_access(
    principal: Principal,
    transaction: Transaction,
    accounts: AccountRepository,
    customers: CustomerRepository,
) -> None:
    """Garante que o principal participa da transação ou é staff."""
    if principal.role in STAFF_ROLES:
        return
    customer = await customers.get_by_user_id(principal.user_id)
    if customer is None:
        raise ForbiddenError("Acesso negado a esta transação.")
    account_ids = [
        account_id
        for account_id in (
            transaction.source_account_id,
            transaction.destination_account_id,
        )
        if account_id is not None
    ]
    involved = await accounts.get_many(account_ids)
    if customer.id not in {account.customer_id for account in involved.values()}:
        raise ForbiddenError("Acesso negado a esta transação.")
