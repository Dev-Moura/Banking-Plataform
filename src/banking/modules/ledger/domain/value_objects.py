"""Value objects do módulo de ledger."""

from __future__ import annotations

from enum import StrEnum


class EntryType(StrEnum):
    """Natureza de um lançamento contábil."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
