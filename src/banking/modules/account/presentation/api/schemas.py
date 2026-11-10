"""Schemas Pydantic do módulo de contas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from banking.modules.account.domain.value_objects import (
    AccountStatus,
    AccountType,
    Currency,
)


class CreateAccountRequest(BaseModel):
    """Payload de abertura de conta."""

    account_type: AccountType = AccountType.CHECKING
    currency: Currency = Currency.BRL


class UpdateAccountStatusRequest(BaseModel):
    """Payload de alteração de status."""

    status: AccountStatus


class AccountResponse(BaseModel):
    """Representação pública de conta."""

    id: UUID
    customer_id: UUID
    account_number: int
    account_type: str
    status: str
    currency: str
    balance: str
    created_at: datetime


class BalanceResponse(BaseModel):
    """Saldo da conta."""

    account_id: UUID
    balance: str
    currency: str
    as_of: datetime


class AccountPageResponse(BaseModel):
    """Página de contas."""

    items: list[AccountResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
