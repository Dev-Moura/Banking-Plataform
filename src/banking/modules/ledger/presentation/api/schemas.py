"""Schemas Pydantic do módulo de ledger."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LedgerEntryResponse(BaseModel):
    """Representação pública de um lançamento contábil."""

    id: UUID
    transaction_id: UUID
    account_id: UUID
    entry_type: str
    amount: str
    balance_after: str
    currency: str
    created_at: datetime


class LedgerEntryPageResponse(BaseModel):
    """Página de lançamentos contábeis."""

    items: list[LedgerEntryResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)


class TransactionLedgerResponse(BaseModel):
    """Lançamentos de uma transação com verificação de equilíbrio."""

    transaction_id: UUID
    entries: list[LedgerEntryResponse]
    balanced: bool
