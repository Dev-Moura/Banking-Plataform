"""Testes de constraints, sequência e imutabilidade do ledger."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from banking.modules.account.infrastructure.persistence.models import Account
from banking.modules.audit.infrastructure.persistence.models import AuditEvent
from banking.modules.customer.infrastructure.persistence.models import Customer
from banking.modules.identity.infrastructure.persistence.models import (
    RefreshSession,
    User,
)
from banking.modules.ledger.infrastructure.persistence.models import LedgerEntry
from banking.modules.transaction.infrastructure.persistence.models import (
    Transaction,
)

pytestmark = pytest.mark.integration

_REQUEST_HASH = "a" * 64
_SESSION_HASH = "b" * 64


async def _create_user(session, email: str = "user@example.com") -> User:
    user = User(email=email, password_hash="argon2-hash")  # noqa: S106
    session.add(user)
    await session.flush()
    return user


async def _create_customer(
    session,
    user: User,
    document_reference: str = "DOC-0001",
) -> Customer:
    customer = Customer(
        user_id=user.id,
        full_name="Cliente de Teste",
        document_reference=document_reference,
    )
    session.add(customer)
    await session.flush()
    return customer


async def _create_account(
    session,
    customer: Customer,
    *,
    is_system: bool = False,
    balance: Decimal = Decimal("0.00"),
) -> Account:
    account = Account(
        customer_id=customer.id,
        account_type="CHECKING",
        currency="BRL",
        balance=balance,
        is_system=is_system,
    )
    session.add(account)
    await session.flush()
    return account


async def _create_transaction(
    session, user: User, source: Account, destination: Account
) -> Transaction:
    transaction = Transaction(
        source_account_id=source.id,
        destination_account_id=destination.id,
        amount=Decimal("50.00"),
        currency="BRL",
        idempotency_key="ledger-entry-key",
        request_hash=_REQUEST_HASH,
        created_by_user_id=user.id,
    )
    session.add(transaction)
    await session.flush()
    return transaction


async def _create_ledger_entry(session) -> LedgerEntry:
    user = await _create_user(session)
    customer = await _create_customer(session, user)
    source = await _create_account(session, customer)
    destination = await _create_account(session, customer)
    transaction = await _create_transaction(session, user, source, destination)

    entry = LedgerEntry(
        transaction_id=transaction.id,
        account_id=source.id,
        entry_type="DEBIT",
        amount=Decimal("50.00"),
        balance_after=Decimal("50.00"),
        currency="BRL",
    )
    session.add(entry)
    await session.flush()
    return entry


async def test_user_email_must_be_unique(db_session) -> None:
    await _create_user(db_session, email="duplicate@example.com")

    db_session.add(
        User(email="duplicate@example.com", password_hash="another-hash")  # noqa: S106
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_user_role_must_be_valid(db_session) -> None:
    db_session.add(
        User(
            email="invalid-role@example.com",
            password_hash="argon2-hash",  # noqa: S106
            role="INVALID",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_failed_login_attempts_must_be_non_negative(db_session) -> None:
    db_session.add(
        User(
            email="negative-attempts@example.com",
            password_hash="argon2-hash",  # noqa: S106
            failed_login_attempts=-1,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_refresh_session_requires_expiration_after_creation(db_session) -> None:
    user = await _create_user(db_session)
    now = datetime.now(UTC)

    db_session.add(
        RefreshSession(
            user_id=user.id,
            family_id=uuid4(),
            token_hash=_SESSION_HASH,
            created_at=now,
            expires_at=now,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_customer_birth_date_is_accepted(db_session) -> None:
    user = await _create_user(db_session)
    birth_date = date(1990, 5, 20)

    customer = Customer(
        user_id=user.id,
        full_name="Cliente com Data de Nascimento",
        document_reference="DOC-BIRTH",
        birth_date=birth_date,
    )
    db_session.add(customer)
    await db_session.flush()

    assert customer.birth_date == birth_date


async def test_transaction_idempotency_key_must_be_unique(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)
    source = await _create_account(db_session, customer)
    destination = await _create_account(db_session, customer)

    first = Transaction(
        source_account_id=source.id,
        destination_account_id=destination.id,
        amount=Decimal("10.00"),
        currency="BRL",
        idempotency_key="same-idempotency-key",
        request_hash=_REQUEST_HASH,
        created_by_user_id=user.id,
    )
    db_session.add(first)
    await db_session.flush()

    second = Transaction(
        source_account_id=source.id,
        destination_account_id=destination.id,
        amount=Decimal("20.00"),
        currency="BRL",
        idempotency_key="same-idempotency-key",
        request_hash=_REQUEST_HASH,
        created_by_user_id=user.id,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_transaction_requires_request_hash(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)
    source = await _create_account(db_session, customer)
    destination = await _create_account(db_session, customer)

    db_session.add(
        Transaction(
            source_account_id=source.id,
            destination_account_id=destination.id,
            amount=Decimal("10.00"),
            currency="BRL",
            idempotency_key="missing-request-hash",
            created_by_user_id=user.id,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_transaction_requires_created_by_user_id(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)
    source = await _create_account(db_session, customer)
    destination = await _create_account(db_session, customer)

    db_session.add(
        Transaction(
            source_account_id=source.id,
            destination_account_id=destination.id,
            amount=Decimal("10.00"),
            currency="BRL",
            idempotency_key="missing-creator",
            request_hash=_REQUEST_HASH,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_non_system_account_rejects_negative_balance(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)

    account = Account(
        customer_id=customer.id,
        account_type="CHECKING",
        currency="BRL",
        balance=Decimal("-0.01"),
        is_system=False,
    )
    db_session.add(account)
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_system_account_allows_negative_balance(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)

    account = Account(
        customer_id=customer.id,
        account_type="CHECKING",
        currency="BRL",
        balance=Decimal("-100.00"),
        is_system=True,
    )
    db_session.add(account)
    await db_session.flush()

    assert account.balance == Decimal("-100.00")


async def test_account_number_is_generated_from_sequence(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)

    account = await _create_account(db_session, customer)

    assert account.account_number >= 10_000_001


async def test_ledger_entry_requires_balance_after(db_session) -> None:
    user = await _create_user(db_session)
    customer = await _create_customer(db_session, user)
    source = await _create_account(db_session, customer)
    destination = await _create_account(db_session, customer)
    transaction = await _create_transaction(db_session, user, source, destination)

    db_session.add(
        LedgerEntry(
            transaction_id=transaction.id,
            account_id=source.id,
            entry_type="DEBIT",
            amount=Decimal("50.00"),
            currency="BRL",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_audit_event_metadata_defaults_to_empty_object(db_session) -> None:
    user = await _create_user(db_session)

    event = AuditEvent(
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        correlation_id=uuid4(),
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)

    assert event.event_metadata == {}


async def test_ledger_entry_cannot_be_updated(db_session) -> None:
    entry = await _create_ledger_entry(db_session)

    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("UPDATE ledger_entries SET amount = :amount WHERE id = :id"),
            {"amount": Decimal("1.00"), "id": entry.id},
        )


async def test_ledger_entry_cannot_be_deleted(db_session) -> None:
    entry = await _create_ledger_entry(db_session)

    with pytest.raises(IntegrityError):
        await db_session.execute(
            text("DELETE FROM ledger_entries WHERE id = :id"),
            {"id": entry.id},
        )
