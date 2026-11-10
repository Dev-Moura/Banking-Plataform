"""Entidades de domínio do módulo de clientes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True)
class Customer:
    """Cliente bancário associado a um usuário."""

    id: UUID
    user_id: UUID
    full_name: str
    document_reference: str
    birth_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
