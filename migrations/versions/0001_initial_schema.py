"""Cria o schema inicial da plataforma bancária.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEDGER_MUTATION_FUNCTION = """
CREATE OR REPLACE FUNCTION prevent_ledger_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'ledger_entries é imutável: operação % bloqueada', TG_OP
        USING ERRCODE = '23000';
END;
$$;
"""

LEDGER_MUTATION_TRIGGER = """
CREATE TRIGGER trg_ledger_entries_immutable
BEFORE UPDATE OR DELETE ON ledger_entries
FOR EACH ROW
EXECUTE FUNCTION prevent_ledger_mutation();
"""


def upgrade() -> None:
    """Cria sequência, tabelas, constraints, índices e trigger do ledger."""
    op.execute("CREATE SEQUENCE account_number_seq START WITH 10000001 INCREMENT BY 1")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.String(length=32),
            server_default=sa.text("'CUSTOMER'"),
            nullable=False,
        ),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('CUSTOMER', 'BANK_OPERATOR', 'BANK_ADMIN', 'AUDITOR', 'SYSTEM')",
            name=op.f("ck_users_role_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'LOCKED', 'DISABLED')",
            name=op.f("ck_users_status_valid"),
        ),
        sa.CheckConstraint(
            "failed_login_attempts >= 0",
            name=op.f("ck_users_failed_login_attempts_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_status", "users", ["status"], unique=False)

    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "document_reference",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'BLOCKED')",
            name=op.f("ck_customers_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_customers_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.UniqueConstraint("user_id", name="uq_customers_user_id"),
        sa.UniqueConstraint(
            "document_reference",
            name="uq_customers_document_reference",
        ),
    )
    op.create_index("ix_customers_status", "customers", ["status"], unique=False)

    op.create_table(
        "refresh_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "replaced_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("token_hash", sa.CHAR(length=64), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name=op.f("ck_refresh_sessions_expires_after_created"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_refresh_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"],
            ["refresh_sessions.id"],
            name="fk_refresh_sessions_replaced_by_id_refresh_sessions",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_sessions"),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_refresh_sessions_token_hash",
        ),
    )
    op.create_index(
        "ix_refresh_sessions_user_id",
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_family_id",
        "refresh_sessions",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_expires_at",
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_number",
            sa.BigInteger(),
            server_default=sa.text("nextval('account_number_seq')"),
            nullable=False,
        ),
        sa.Column(
            "account_type",
            sa.String(length=20),
            server_default=sa.text("'CHECKING'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.CHAR(length=3),
            server_default=sa.text("'BRL'"),
            nullable=False,
        ),
        sa.Column(
            "balance",
            sa.Numeric(precision=19, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account_type IN ('CHECKING', 'SAVINGS')",
            name=op.f("ck_accounts_account_type_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'BLOCKED', 'CLOSED')",
            name=op.f("ck_accounts_status_valid"),
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name=op.f("ck_accounts_currency_format_valid"),
        ),
        sa.CheckConstraint(
            "is_system OR balance >= 0",
            name=op.f("ck_accounts_balance_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_accounts_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
        sa.UniqueConstraint(
            "account_number",
            name="uq_accounts_account_number",
        ),
    )
    op.create_index(
        "ix_accounts_customer_id",
        "accounts",
        ["customer_id"],
        unique=False,
    )
    op.create_index("ix_accounts_status", "accounts", ["status"], unique=False)

    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "source_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "destination_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=19, scale=2),
            nullable=False,
        ),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.CHAR(length=64), nullable=False),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name=op.f("ck_transactions_amount_positive"),
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED', 'REVERSED')",
            name=op.f("ck_transactions_status_valid"),
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name=op.f("ck_transactions_currency_format_valid"),
        ),
        sa.CheckConstraint(
            "source_account_id IS NOT NULL OR destination_account_id IS NOT NULL",
            name=op.f("ck_transactions_accounts_present"),
        ),
        sa.CheckConstraint(
            "source_account_id IS NULL "
            "OR destination_account_id IS NULL "
            "OR source_account_id <> destination_account_id",
            name=op.f("ck_transactions_accounts_distinct"),
        ),
        sa.ForeignKeyConstraint(
            ["source_account_id"],
            ["accounts.id"],
            name="fk_transactions_source_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["destination_account_id"],
            ["accounts.id"],
            name="fk_transactions_destination_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_transactions_created_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transactions"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_transactions_idempotency_key",
        ),
    )
    op.create_index(
        "ix_transactions_source_account_id_created_at",
        "transactions",
        ["source_account_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_destination_account_id_created_at",
        "transactions",
        ["destination_account_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_created_by_user_id",
        "transactions",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_status",
        "transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_created_at",
        "transactions",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "ledger_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", sa.String(length=10), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=19, scale=2),
            nullable=False,
        ),
        sa.Column(
            "balance_after",
            sa.Numeric(precision=19, scale=2),
            nullable=False,
        ),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "entry_type IN ('DEBIT', 'CREDIT')",
            name=op.f("ck_ledger_entries_entry_type_valid"),
        ),
        sa.CheckConstraint(
            "amount > 0",
            name=op.f("ck_ledger_entries_amount_positive"),
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name=op.f("ck_ledger_entries_currency_format_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_ledger_entries_transaction_id_transactions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_ledger_entries_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_entries"),
    )
    op.create_index(
        "ix_ledger_entries_transaction_id_entry_type",
        "ledger_entries",
        ["transaction_id", "entry_type"],
        unique=False,
    )
    op.create_index(
        "ix_ledger_entries_account_id",
        "ledger_entries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_ledger_entries_account_created_at",
        "ledger_entries",
        ["account_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column(
            "correlation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_audit_events_actor_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
    )
    op.create_index(
        "ix_audit_events_actor_id",
        "audit_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_resource",
        "audit_events",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_correlation_id",
        "audit_events",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
        unique=False,
    )

    op.execute(LEDGER_MUTATION_FUNCTION)
    op.execute(LEDGER_MUTATION_TRIGGER)


def downgrade() -> None:
    """Remove trigger, função, tabelas e sequência na ordem correta."""
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_immutable ON ledger_entries")
    op.execute("DROP FUNCTION IF EXISTS prevent_ledger_mutation()")

    op.drop_table("audit_events")
    op.drop_table("ledger_entries")
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("refresh_sessions")
    op.drop_table("customers")
    op.drop_table("users")

    op.execute("DROP SEQUENCE IF EXISTS account_number_seq")
