"""DTOs do módulo de ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LedgerEntryOutput:
    """Representação pública de um lançamento contábil."""

    id: UUID
    transaction_id: UUID
    account_id: UUID
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    currency: str
    created_at: datetime
