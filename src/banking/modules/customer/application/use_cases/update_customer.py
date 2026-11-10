"""Caso de uso de atualização cadastral."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import ForbiddenError, NotFoundError
from banking.modules.customer.application.dto import (
    CustomerOutput,
    UpdateCustomerInput,
)
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.customer.application.use_cases.get_customer import to_output
from banking.modules.identity.application.interfaces import Clock, UnitOfWorkPort
from banking.shared.contracts.security import Principal, Role

UPDATE_ROLES = frozenset({Role.BANK_ADMIN})


class UpdateCustomerUseCase:
    """Atualiza dados cadastrais do cliente."""

    def __init__(
        self,
        customer_repository: CustomerRepository,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._customers = customer_repository
        self._uow = unit_of_work
        self._clock = clock

    async def execute(
        self,
        principal: Principal,
        customer_id: UUID,
        data: UpdateCustomerInput,
    ) -> CustomerOutput:
        """Atualiza nome e data de nascimento."""
        customer = await self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Cliente não encontrado.")
        is_owner = customer.user_id == principal.user_id
        if not is_owner and principal.role not in UPDATE_ROLES:
            raise ForbiddenError("Acesso negado a este cliente.")

        if data.full_name is not None:
            customer.full_name = data.full_name.strip()
        if data.birth_date is not None:
            customer.birth_date = data.birth_date
        customer.updated_at = self._clock.now()

        await self._customers.update(customer)
        await self._uow.commit()
        return to_output(customer)
