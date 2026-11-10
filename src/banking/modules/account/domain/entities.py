"""Entidades de domínio do módulo de contas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Account:
    """Conta bancária de um cliente."""

    id: UUID
    customer_id: UUID
    account_number: int
    account_type: str
    status: str
    currency: str
    balance: Decimal
    is_system: bool
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        """Indica se a conta permite movimentação."""
        return self.status == "ACTIVE"

    def belongs_to(self, customer_id: UUID) -> bool:
        """Indica se a conta pertence ao cliente informado."""
        return self.customer_id == customer_id
