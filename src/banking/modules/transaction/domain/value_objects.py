"""Value objects do módulo de transações."""

from __future__ import annotations

from enum import StrEnum


class TransactionStatus(StrEnum):
    """Estados de uma transação financeira."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
