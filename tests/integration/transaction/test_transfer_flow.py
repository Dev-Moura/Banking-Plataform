"""Fluxo de integração de transferências e ledger com PostgreSQL real."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration

PASSWORD = "Correct@Pass123"


async def _auth(client: httpx.AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": PASSWORD},
    )
    login = await client.post(
        "/api/v1/identity/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def _headers(token: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def _setup_customer_account(
    client: httpx.AsyncClient, email: str, document: str
) -> tuple[str, str, str]:
    token = await _auth(client, email)
    customer = await client.post(
        "/api/v1/customers",
        json={"full_name": "Transfer User", "document_reference": document},
        headers=_headers(token),
    )
    assert customer.status_code == 201
    account = await client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_headers(token),
    )
    assert account.status_code == 201
    return token, customer.json()["id"], account.json()["id"]


async def _set_balance(session: AsyncSession, account_id: str, value: Decimal) -> None:
    await session.execute(
        text("UPDATE accounts SET balance = :value WHERE id = :account_id"),
        {"value": value, "account_id": account_id},
    )
    await session.commit()
    session.expire_all()


async def _transfer(
    client: httpx.AsyncClient,
    token: str,
    source: str,
    destination: str,
    amount: str,
    key: str,
) -> httpx.Response:
    return await client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": source,
            "destination_account_id": destination,
            "amount": amount,
        },
        headers=_headers(token, key),
    )


async def test_transfer_updates_balances_and_ledger(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "sender@example.com", "DOC-TX-1"
    )
    receiver, _, destination = await _setup_customer_account(
        api_client, "receiver@example.com", "DOC-TX-2"
    )
    await _set_balance(db_session, source, Decimal("1000.00"))

    response = await _transfer(
        api_client, owner, source, destination, "200.00", "tx-key-1"
    )
    assert response.status_code == 201
    transaction = response.json()
    assert transaction["status"] == "COMPLETED"
    assert transaction["amount"] == "200.00"
    assert transaction["currency"] == "BRL"

    source_balance = await api_client.get(
        f"/api/v1/accounts/{source}/balance", headers=_headers(owner)
    )
    destination_balance = await api_client.get(
        f"/api/v1/accounts/{destination}/balance", headers=_headers(receiver)
    )
    assert source_balance.json()["balance"] == "800.00"
    assert destination_balance.json()["balance"] == "200.00"

    statement = await api_client.get(
        f"/api/v1/accounts/{source}/statement", headers=_headers(owner)
    )
    assert statement.status_code == 200
    assert statement.json()["total"] == 1
    debit = statement.json()["items"][0]
    assert debit["entry_type"] == "DEBIT"
    assert debit["amount"] == "200.00"
    assert debit["balance_after"] == "800.00"

    destination_statement = await api_client.get(
        f"/api/v1/accounts/{destination}/statement", headers=_headers(receiver)
    )
    assert destination_statement.json()["items"][0]["entry_type"] == "CREDIT"
    assert destination_statement.json()["items"][0]["balance_after"] == "200.00"

    ledger = await api_client.get(
        f"/api/v1/ledger/transactions/{transaction['id']}",
        headers=_headers(owner),
    )
    assert ledger.status_code == 200
    assert ledger.json()["balanced"] is True
    assert len(ledger.json()["entries"]) == 2

    receiver_ledger = await api_client.get(
        f"/api/v1/ledger/transactions/{transaction['id']}",
        headers=_headers(receiver),
    )
    assert receiver_ledger.status_code == 200

    account_ledger = await api_client.get(
        f"/api/v1/ledger/accounts/{destination}", headers=_headers(receiver)
    )
    assert account_ledger.status_code == 200
    assert account_ledger.json()["total"] == 1

    source_ledger = await api_client.get(
        f"/api/v1/ledger/accounts/{source}", headers=_headers(owner)
    )
    assert source_ledger.status_code == 200
    assert source_ledger.json()["total"] == 1

    fetched = await api_client.get(
        f"/api/v1/transactions/{transaction['id']}", headers=_headers(owner)
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == transaction["id"]


async def test_transfer_is_idempotent(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "idem@example.com", "DOC-TX-IDEM"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "idem-dest@example.com", "DOC-TX-IDEM-DEST"
    )
    await _set_balance(db_session, source, Decimal("1000.00"))

    first = await _transfer(
        api_client, owner, source, destination, "200.00", "idem-key"
    )
    second = await _transfer(
        api_client, owner, source, destination, "200.00", "idem-key"
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    balance = await api_client.get(
        f"/api/v1/accounts/{source}/balance", headers=_headers(owner)
    )
    assert balance.json()["balance"] == "800.00"

    conflict = await _transfer(
        api_client, owner, source, destination, "50.00", "idem-key"
    )
    assert conflict.status_code == 409


async def test_transfer_rejects_insufficient_funds_without_side_effects(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "poor@example.com", "DOC-TX-POOR"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "rich@example.com", "DOC-TX-RICH"
    )
    await _set_balance(db_session, source, Decimal("50.00"))

    response = await _transfer(
        api_client, owner, source, destination, "100.00", "poor-key"
    )
    assert response.status_code == 422

    balance = await api_client.get(
        f"/api/v1/accounts/{source}/balance", headers=_headers(owner)
    )
    assert balance.json()["balance"] == "50.00"

    history = await api_client.get("/api/v1/transactions", headers=_headers(owner))
    assert history.json()["total"] == 0


async def test_transfer_rejects_inactive_destination(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "active@example.com", "DOC-TX-ACTIVE"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "blocked@example.com", "DOC-TX-BLOCKED"
    )
    await _set_balance(db_session, source, Decimal("1000.00"))
    await db_session.execute(
        text("UPDATE accounts SET status = 'BLOCKED' WHERE id = :id"),
        {"id": destination},
    )
    await db_session.commit()
    db_session.expire_all()

    response = await _transfer(
        api_client, owner, source, destination, "10.00", "blocked-key"
    )
    assert response.status_code == 422


async def test_transfer_to_same_account_is_rejected(
    api_client: httpx.AsyncClient,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "same@example.com", "DOC-TX-SAME"
    )
    response = await _transfer(api_client, owner, source, source, "10.00", "same-key")
    assert response.status_code == 422


async def test_transfer_requires_authentication(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": "00000000-0000-0000-0000-000000000001",
            "destination_account_id": "00000000-0000-0000-0000-000000000002",
            "amount": "10.00",
        },
        headers={"Idempotency-Key": "unauthenticated"},
    )
    assert response.status_code == 401


async def test_transfer_requires_idempotency_key(
    api_client: httpx.AsyncClient,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "nokey@example.com", "DOC-TX-NOKEY"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "nokey-dest@example.com", "DOC-TX-NOKEY-DEST"
    )
    response = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": source,
            "destination_account_id": destination,
            "amount": "10.00",
        },
        headers=_headers(owner),
    )
    assert response.status_code == 422


async def test_transaction_is_not_visible_to_unrelated_user(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "tx-owner@example.com", "DOC-TX-OWNER"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "tx-dest@example.com", "DOC-TX-DEST"
    )
    intruder, _, _ = await _setup_customer_account(
        api_client, "tx-intruder@example.com", "DOC-TX-INTRUDER"
    )
    await _set_balance(db_session, source, Decimal("1000.00"))

    response = await _transfer(
        api_client, owner, source, destination, "200.00", "visibility-key"
    )
    assert response.status_code == 201
    transaction_id = response.json()["id"]

    forbidden = await api_client.get(
        f"/api/v1/transactions/{transaction_id}", headers=_headers(intruder)
    )
    assert forbidden.status_code == 403

    ledger_forbidden = await api_client.get(
        f"/api/v1/ledger/transactions/{transaction_id}",
        headers=_headers(intruder),
    )
    assert ledger_forbidden.status_code == 403

    listed = await api_client.get("/api/v1/transactions", headers=_headers(intruder))
    assert listed.json()["total"] == 0


async def test_auditor_can_read_all_transactions(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner, _, source = await _setup_customer_account(
        api_client, "audit-owner@example.com", "DOC-AUDIT-OWNER"
    )
    _, _, destination = await _setup_customer_account(
        api_client, "audit-dest@example.com", "DOC-AUDIT-DEST"
    )
    await _set_balance(db_session, source, Decimal("1000.00"))
    transfer = await _transfer(
        api_client, owner, source, destination, "200.00", "audit-key"
    )
    assert transfer.status_code == 201

    await _auth(api_client, "auditor@example.com")
    await db_session.execute(
        text("UPDATE users SET role = 'AUDITOR' WHERE email = :email"),
        {"email": "auditor@example.com"},
    )
    await db_session.commit()
    db_session.expire_all()
    auditor_token = await _auth(api_client, "auditor@example.com")

    listed = await api_client.get(
        "/api/v1/transactions", headers=_headers(auditor_token)
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    ledger = await api_client.get(
        f"/api/v1/ledger/transactions/{transfer.json()['id']}",
        headers=_headers(auditor_token),
    )
    assert ledger.status_code == 200


@pytest.fixture
async def concurrent_client(
    db_engine: object, clean_db: None
) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente que abre uma sessão independente por requisição."""
    from banking.infrastructure.database.session import get_session
    from banking.main import create_app

    app = create_app()
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def _override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def _set_balance_engine(db_engine: object, account_id: str) -> None:
    from sqlalchemy.ext.asyncio import AsyncEngine

    assert isinstance(db_engine, AsyncEngine)
    async with db_engine.begin() as connection:
        await connection.execute(
            text("UPDATE accounts SET balance = 100.00 WHERE id = :id"),
            {"id": account_id},
        )


async def test_concurrent_transfers_do_not_overspend(
    concurrent_client: httpx.AsyncClient,
    db_engine: object,
) -> None:
    owner, _, source = await _setup_customer_account(
        concurrent_client, "race@example.com", "DOC-RACE"
    )
    _, _, first_destination = await _setup_customer_account(
        concurrent_client, "race-1@example.com", "DOC-RACE-1"
    )
    _, _, second_destination = await _setup_customer_account(
        concurrent_client, "race-2@example.com", "DOC-RACE-2"
    )
    await _set_balance_engine(db_engine, source)

    first, second = await asyncio.gather(
        _transfer(
            concurrent_client,
            owner,
            source,
            first_destination,
            "80.00",
            "race-key-1",
        ),
        _transfer(
            concurrent_client,
            owner,
            source,
            second_destination,
            "80.00",
            "race-key-2",
        ),
    )

    assert sorted([first.status_code, second.status_code]) == [201, 422]

    balance = await concurrent_client.get(
        f"/api/v1/accounts/{source}/balance", headers=_headers(owner)
    )
    assert balance.json()["balance"] == "20.00"

    history = await concurrent_client.get(
        "/api/v1/transactions", headers=_headers(owner)
    )
    assert history.json()["total"] == 1


async def test_concurrent_same_idempotency_key_is_applied_once(
    concurrent_client: httpx.AsyncClient,
    db_engine: object,
) -> None:
    owner, _, source = await _setup_customer_account(
        concurrent_client, "idem-race@example.com", "DOC-IDEM-RACE"
    )
    _, _, destination = await _setup_customer_account(
        concurrent_client, "idem-race-dest@example.com", "DOC-IDEM-RACE-DEST"
    )
    await _set_balance_engine(db_engine, source)

    first, second = await asyncio.gather(
        _transfer(
            concurrent_client,
            owner,
            source,
            destination,
            "80.00",
            "idem-race-key",
        ),
        _transfer(
            concurrent_client,
            owner,
            source,
            destination,
            "80.00",
            "idem-race-key",
        ),
    )

    assert sorted([first.status_code, second.status_code]) == [200, 201]
    assert first.json()["id"] == second.json()["id"]

    balance = await concurrent_client.get(
        f"/api/v1/accounts/{source}/balance", headers=_headers(owner)
    )
    assert balance.json()["balance"] == "20.00"

    history = await concurrent_client.get(
        "/api/v1/transactions", headers=_headers(owner)
    )
    assert history.json()["total"] == 1
