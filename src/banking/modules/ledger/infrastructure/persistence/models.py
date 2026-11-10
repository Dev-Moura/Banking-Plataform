"""Modelos ORM do módulo ledger."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from banking.infrastructure.database.base import Base


class LedgerEntry(Base):
    """Lançamento contábil imutável de débito ou crédito."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('DEBIT', 'CREDIT')",
            name="entry_type_valid",
        ),
        CheckConstraint(
            "amount > 0",
            name="amount_positive",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="currency_format_valid",
        ),
        Index(
            "ix_ledger_entries_transaction_id_entry_type",
            "transaction_id",
            "entry_type",
        ),
        Index("ix_ledger_entries_account_id", "account_id"),
        Index(
            "ix_ledger_entries_account_created_at",
            "account_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    transaction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
