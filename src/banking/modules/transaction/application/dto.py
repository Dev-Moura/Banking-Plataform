"""DTOs do módulo de transações."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TransferInput:
    """Dados de uma transferência idempotente."""

    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal
    idempotency_key: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class TransactionOutput:
    """Representação pública de uma transação."""

    id: UUID
    source_account_id: UUID | None
    destination_account_id: UUID | None
    amount: Decimal
    currency: str
    status: str
    description: str | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class TransferResult:
    """Resultado da transferência com indicação de replay."""

    transaction: TransactionOutput
    created: bool
