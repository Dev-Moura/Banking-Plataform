"""DTOs do módulo de contas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateAccountInput:
    """Dados para abertura de conta."""

    account_type: str
    currency: str = "BRL"


@dataclass(frozen=True, slots=True)
class AccountOutput:
    """Representação pública de uma conta."""

    id: UUID
    customer_id: UUID
    account_number: int
    account_type: str
    status: str
    currency: str
    balance: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BalanceOutput:
    """Saldo consolidado de uma conta."""

    account_id: UUID
    balance: Decimal
    currency: str
    as_of: datetime
