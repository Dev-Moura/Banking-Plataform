"""Fluxo de integração do módulo de contas com PostgreSQL real."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

PASSWORD = "Correct@Pass123"
FIRST_ACCOUNT_NUMBER = 10_000_001


async def _authenticate(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": PASSWORD},
    )
    login = await client.post(
        "/api/v1/identity/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    return login.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_customer(
    client: httpx.AsyncClient, tokens: dict[str, str], document: str
) -> str:
    response = await client.post(
        "/api/v1/customers",
        json={"full_name": "Account Owner", "document_reference": document},
        headers=_auth(tokens["access_token"]),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_open_list_and_read_account(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _authenticate(api_client, "account@example.com")
    customer_id = await _create_customer(api_client, tokens, "DOC-ACC-1")

    created = await api_client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_auth(tokens["access_token"]),
    )
    assert created.status_code == 201
    account = created.json()
    assert account["customer_id"] == customer_id
    assert account["account_number"] >= FIRST_ACCOUNT_NUMBER
    assert account["status"] == "ACTIVE"
    assert account["balance"] == "0.00"
    account_id = account["id"]

    listed = await api_client.get(
        "/api/v1/accounts", headers=_auth(tokens["access_token"])
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["pages"] == 1

    fetched = await api_client.get(
        f"/api/v1/accounts/{account_id}",
        headers=_auth(tokens["access_token"]),
    )
    assert fetched.status_code == 200
    assert fetched.json()["account_number"] == account["account_number"]

    balance = await api_client.get(
        f"/api/v1/accounts/{account_id}/balance",
        headers=_auth(tokens["access_token"]),
    )
    assert balance.status_code == 200
    assert balance.json()["balance"] == "0.00"
    assert balance.json()["currency"] == "BRL"


async def test_open_account_requires_customer_profile(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _authenticate(api_client, "nocustomer@example.com")

    response = await api_client.post(
        "/api/v1/accounts",
        json={"account_type": "SAVINGS", "currency": "BRL"},
        headers=_auth(tokens["access_token"]),
    )
    assert response.status_code == 404


async def test_account_requires_authentication(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/accounts")
    assert response.status_code == 401


async def test_account_is_not_visible_to_other_customer(
    api_client: httpx.AsyncClient,
) -> None:
    owner = await _authenticate(api_client, "acc-owner@example.com")
    intruder = await _authenticate(api_client, "acc-intruder@example.com")
    await _create_customer(api_client, owner, "DOC-ACC-OWNER")

    created = await api_client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_auth(owner["access_token"]),
    )
    assert created.status_code == 201
    account_id = created.json()["id"]

    for path in (
        f"/api/v1/accounts/{account_id}",
        f"/api/v1/accounts/{account_id}/balance",
    ):
        response = await api_client.get(path, headers=_auth(intruder["access_token"]))
        assert response.status_code == 403

    listed = await api_client.get(
        "/api/v1/accounts", headers=_auth(intruder["access_token"])
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 0


async def test_operator_can_block_account(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    tokens = await _authenticate(api_client, "blocked@example.com")
    await _create_customer(api_client, tokens, "DOC-ACC-BLOCK")

    created = await api_client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_auth(tokens["access_token"]),
    )
    assert created.status_code == 201
    account_id = created.json()["id"]

    customer_update = await api_client.patch(
        f"/api/v1/accounts/{account_id}/status",
        json={"status": "BLOCKED"},
        headers=_auth(tokens["access_token"]),
    )
    assert customer_update.status_code == 403

    await db_session.execute(
        text("UPDATE users SET role = 'BANK_OPERATOR' WHERE email = :email"),
        {"email": "blocked@example.com"},
    )
    await db_session.commit()
    db_session.expire_all()

    operator = await api_client.post(
        "/api/v1/identity/login",
        json={"email": "blocked@example.com", "password": PASSWORD},
    )
    assert operator.status_code == 200
    operator_token = operator.json()["access_token"]

    updated = await api_client.patch(
        f"/api/v1/accounts/{account_id}/status",
        json={"status": "BLOCKED"},
        headers=_auth(operator_token),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "BLOCKED"

    filtered = await api_client.get(
        "/api/v1/accounts?status=BLOCKED",
        headers=_auth(tokens["access_token"]),
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
