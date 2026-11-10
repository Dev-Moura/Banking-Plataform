"""Fluxo ponta a ponta: cadastro, conta, transferência e ledger."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

PASSWORD = "Correct@Pass123"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register_and_login(client: httpx.AsyncClient, email: str) -> str:
    register = await client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": PASSWORD},
    )
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/identity/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


async def _open_account(client: httpx.AsyncClient, token: str, email: str) -> str:
    customer = await client.post(
        "/api/v1/customers",
        json={
            "full_name": f"Customer {email}",
            "document_reference": f"DOC-{email}",
        },
        headers=_auth(token),
    )
    assert customer.status_code == 201
    account = await client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_auth(token),
    )
    assert account.status_code == 201
    return account.json()["id"]


async def test_complete_banking_journey(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    sender_token = await _register_and_login(api_client, "e2e-sender@example.com")
    sender_account = await _open_account(
        api_client, sender_token, "e2e-sender@example.com"
    )
    receiver_token = await _register_and_login(api_client, "e2e-receiver@example.com")
    receiver_account = await _open_account(
        api_client, receiver_token, "e2e-receiver@example.com"
    )

    await db_session.execute(
        text("UPDATE accounts SET balance = :balance WHERE id = :id"),
        {"balance": Decimal("500.00"), "id": sender_account},
    )
    await db_session.commit()
    db_session.expire_all()

    transfer = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": sender_account,
            "destination_account_id": receiver_account,
            "amount": "150.00",
            "description": "E2E transfer",
        },
        headers={**_auth(sender_token), "Idempotency-Key": "e2e-transfer-1"},
    )
    assert transfer.status_code == 201
    transaction = transfer.json()
    assert transaction["status"] == "COMPLETED"

    replay = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": sender_account,
            "destination_account_id": receiver_account,
            "amount": "150.00",
            "description": "E2E transfer",
        },
        headers={**_auth(sender_token), "Idempotency-Key": "e2e-transfer-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == transaction["id"]

    sender_balance = await api_client.get(
        f"/api/v1/accounts/{sender_account}/balance",
        headers=_auth(sender_token),
    )
    receiver_balance = await api_client.get(
        f"/api/v1/accounts/{receiver_account}/balance",
        headers=_auth(receiver_token),
    )
    assert sender_balance.json()["balance"] == "350.00"
    assert receiver_balance.json()["balance"] == "150.00"

    statement = await api_client.get(
        f"/api/v1/accounts/{sender_account}/statement",
        headers=_auth(sender_token),
    )
    assert statement.status_code == 200
    assert statement.json()["total"] == 1
    assert statement.json()["items"][0]["entry_type"] == "DEBIT"

    ledger = await api_client.get(
        f"/api/v1/ledger/transactions/{transaction['id']}",
        headers=_auth(receiver_token),
    )
    assert ledger.status_code == 200
    assert ledger.json()["balanced"] is True

    intruder_token = await _register_and_login(api_client, "e2e-intruder@example.com")
    forbidden = await api_client.get(
        f"/api/v1/transactions/{transaction['id']}",
        headers=_auth(intruder_token),
    )
    assert forbidden.status_code == 403
