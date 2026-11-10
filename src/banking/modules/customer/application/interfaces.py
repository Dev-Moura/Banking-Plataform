"""Portas de aplicação do módulo de clientes."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from banking.modules.customer.domain.entities import Customer


class CustomerRepository(Protocol):
    """Abstração de persistência de clientes."""

    async def get_by_user_id(self, user_id: UUID) -> Customer | None: ...

    async def get_by_id(self, customer_id: UUID) -> Customer | None: ...

    async def get_by_document(self, document_reference: str) -> Customer | None: ...

    async def add(self, customer: Customer) -> None: ...

    async def update(self, customer: Customer) -> None: ...
