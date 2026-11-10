"""Repositório SQLAlchemy de clientes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.customer.domain.entities import Customer
from banking.modules.customer.infrastructure.persistence.models import (
    Customer as CustomerModel,
)


def _to_domain(row: CustomerModel) -> Customer:
    return Customer(
        id=row.id,
        user_id=row.user_id,
        full_name=row.full_name,
        document_reference=row.document_reference,
        birth_date=row.birth_date,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyCustomerRepository:
    """Implementação de CustomerRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> Customer | None:
        """Busca cliente pelo usuário."""
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        """Busca cliente por identificador."""
        row = await self._session.get(CustomerModel, customer_id)
        return _to_domain(row) if row is not None else None

    async def get_by_document(self, document_reference: str) -> Customer | None:
        """Busca cliente pelo documento de referência."""
        result = await self._session.execute(
            select(CustomerModel).where(
                CustomerModel.document_reference == document_reference
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def add(self, customer: Customer) -> None:
        """Persiste um novo cliente."""
        self._session.add(
            CustomerModel(
                id=customer.id,
                user_id=customer.user_id,
                full_name=customer.full_name,
                document_reference=customer.document_reference,
                birth_date=customer.birth_date,
                status=customer.status,
                created_at=customer.created_at,
                updated_at=customer.updated_at,
            )
        )
        await self._session.flush()

    async def update(self, customer: Customer) -> None:
        """Atualiza dados cadastrais."""
        row = await self._session.get(CustomerModel, customer.id)
        if row is None:
            return
        row.full_name = customer.full_name
        row.birth_date = customer.birth_date
        row.status = customer.status
        row.updated_at = customer.updated_at
        await self._session.flush()
