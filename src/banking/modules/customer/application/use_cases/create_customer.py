"""Caso de uso de criação de cliente."""

from __future__ import annotations

from uuid import uuid4

from banking.core.exceptions import ConflictError
from banking.modules.customer.application.dto import (
    CreateCustomerInput,
    CustomerOutput,
)
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.customer.domain.entities import Customer
from banking.modules.identity.application.interfaces import Clock, UnitOfWorkPort
from banking.shared.contracts.security import Principal


class CreateCustomerUseCase:
    """Cria o cadastro de cliente do usuário autenticado."""

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
        self, principal: Principal, data: CreateCustomerInput
    ) -> CustomerOutput:
        """Executa o cadastro do cliente."""
        existing = await self._customers.get_by_user_id(principal.user_id)
        if existing is not None:
            raise ConflictError(
                "Este usuário já possui cadastro de cliente.",
                errors=[],
            )
        document = data.document_reference.strip()
        if await self._customers.get_by_document(document) is not None:
            raise ConflictError(
                "Documento já cadastrado.",
                errors=[],
            )

        now = self._clock.now()
        customer = Customer(
            id=uuid4(),
            user_id=principal.user_id,
            full_name=data.full_name.strip(),
            document_reference=document,
            birth_date=data.birth_date,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        await self._customers.add(customer)
        await self._uow.commit()

        return CustomerOutput(
            id=customer.id,
            user_id=customer.user_id,
            full_name=customer.full_name,
            document_reference=customer.document_reference,
            birth_date=customer.birth_date,
            status=customer.status,
            created_at=customer.created_at,
        )
