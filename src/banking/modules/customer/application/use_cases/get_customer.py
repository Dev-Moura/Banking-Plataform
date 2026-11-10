"""Casos de uso de consulta de clientes com ownership."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import ForbiddenError, NotFoundError
from banking.modules.customer.application.dto import CustomerOutput
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.customer.domain.entities import Customer
from banking.shared.contracts.security import Principal, Role

STAFF_ROLES = frozenset({Role.BANK_OPERATOR, Role.BANK_ADMIN, Role.AUDITOR})


def to_output(customer: Customer) -> CustomerOutput:
    """Converte entidade de domínio em DTO de saída."""
    return CustomerOutput(
        id=customer.id,
        user_id=customer.user_id,
        full_name=customer.full_name,
        document_reference=customer.document_reference,
        birth_date=customer.birth_date,
        status=customer.status,
        created_at=customer.created_at,
    )


class GetMyCustomerUseCase:
    """Retorna o cliente do usuário autenticado."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customers = customer_repository

    async def execute(self, principal: Principal) -> CustomerOutput:
        """Consulta o cliente vinculado ao usuário."""
        customer = await self._customers.get_by_user_id(principal.user_id)
        if customer is None:
            raise NotFoundError("Cliente não encontrado para este usuário.")
        return to_output(customer)


class GetCustomerUseCase:
    """Consulta cliente por id com verificação de ownership."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customers = customer_repository

    async def execute(self, principal: Principal, customer_id: UUID) -> CustomerOutput:
        """Consulta cliente respeitando RBAC e propriedade."""
        customer = await self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Cliente não encontrado.")
        if customer.user_id != principal.user_id and principal.role not in STAFF_ROLES:
            raise ForbiddenError("Acesso negado a este cliente.")
        return to_output(customer)
