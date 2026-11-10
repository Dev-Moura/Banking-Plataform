"""Schemas Pydantic do módulo de clientes."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateCustomerRequest(BaseModel):
    """Payload de criação de cliente."""

    full_name: str = Field(min_length=3, max_length=200)
    document_reference: str = Field(min_length=3, max_length=64)
    birth_date: date | None = None


class UpdateCustomerRequest(BaseModel):
    """Payload de atualização cadastral."""

    full_name: str | None = Field(default=None, min_length=3, max_length=200)
    birth_date: date | None = None


class CustomerResponse(BaseModel):
    """Representação pública do cliente."""

    id: UUID
    user_id: UUID
    full_name: str
    document_reference: str
    birth_date: date | None
    status: str
    created_at: datetime
