"""Entidades de domínio do módulo de transações."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Transaction:
    """Operação financeira entre contas."""

    id: UUID
    source_account_id: UUID | None
    destination_account_id: UUID | None
    amount: Decimal
    currency: str
    status: str
    idempotency_key: str
    request_hash: str
    description: str | None
    created_by_user_id: UUID
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
