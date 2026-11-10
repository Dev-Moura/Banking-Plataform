"""Schemas Pydantic do módulo de transações."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TransferRequest(BaseModel):
    """Payload de transferência."""

    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal = Field(gt=0, max_digits=19, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _distinct_accounts(self) -> TransferRequest:
        if self.source_account_id == self.destination_account_id:
            raise ValueError("Conta de origem e destino devem ser distintas.")
        return self


class TransactionResponse(BaseModel):
    """Representação pública de uma transação."""

    id: UUID
    source_account_id: UUID | None
    destination_account_id: UUID | None
    amount: str
    currency: str
    status: str
    description: str | None
    created_at: datetime
    completed_at: datetime | None


class TransactionPageResponse(BaseModel):
    """Página de transações."""

    items: list[TransactionResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
