"""Entidades de domínio do módulo de ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class LedgerEntry:
    """Lançamento contábil imutável."""

    id: UUID
    transaction_id: UUID
    account_id: UUID
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    currency: str
    created_at: datetime
