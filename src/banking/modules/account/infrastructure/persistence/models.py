"""Modelos ORM do módulo account."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from banking.infrastructure.database.base import Base

ACCOUNT_NUMBER_SEQUENCE = "account_number_seq"


class Account(Base):
    """Conta bancária pertencente a um cliente."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('CHECKING', 'SAVINGS')",
            name="account_type_valid",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'BLOCKED', 'CLOSED')",
            name="status_valid",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="currency_format_valid",
        ),
        CheckConstraint(
            "is_system OR balance >= 0",
            name="balance_non_negative",
        ),
        UniqueConstraint(
            "account_number",
            name="uq_accounts_account_number",
        ),
        Index("ix_accounts_customer_id", "customer_id"),
        Index("ix_accounts_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    account_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text(f"nextval('{ACCOUNT_NUMBER_SEQUENCE}')"),
    )
    account_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'CHECKING'"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    currency: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False,
        server_default=text("'BRL'"),
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 2),
        nullable=False,
        server_default=text("0.00"),
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
