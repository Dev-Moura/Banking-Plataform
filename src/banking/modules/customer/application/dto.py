"""DTOs do módulo de clientes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateCustomerInput:
    """Dados para criação de cliente."""

    full_name: str
    document_reference: str
    birth_date: date | None


@dataclass(frozen=True, slots=True)
class UpdateCustomerInput:
    """Campos atualizáveis do cliente."""

    full_name: str | None = None
    birth_date: date | None = None


@dataclass(frozen=True, slots=True)
class CustomerOutput:
    """Representação pública do cliente."""

    id: UUID
    user_id: UUID
    full_name: str
    document_reference: str
    birth_date: date | None
    status: str
    created_at: datetime
