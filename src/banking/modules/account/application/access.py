"""Regras de acesso compartilhadas do módulo de contas."""

from __future__ import annotations

from banking.core.exceptions import ForbiddenError
from banking.modules.account.domain.entities import Account
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.shared.contracts.security import Principal, Role

STAFF_ROLES = frozenset({Role.BANK_OPERATOR, Role.BANK_ADMIN, Role.AUDITOR})


async def ensure_account_access(
    principal: Principal,
    account: Account,
    customers: CustomerRepository,
) -> None:
    """Garante que o principal pode acessar a conta (owner ou staff)."""
    if principal.role in STAFF_ROLES:
        return
    customer = await customers.get_by_user_id(principal.user_id)
    if customer is None or not account.belongs_to(customer.id):
        raise ForbiddenError("Acesso negado a esta conta.")
