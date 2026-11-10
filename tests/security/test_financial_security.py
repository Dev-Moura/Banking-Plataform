"""Regressão de segurança das operações financeiras."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.security, pytest.mark.integration]

PASSWORD = "Correct@Pass123"


def _auth(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


async def _register(client: httpx.AsyncClient, email: str) -> str:
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


async def _account(client: httpx.AsyncClient, token: str, email: str) -> str:
    await client.post(
        "/api/v1/customers",
        json={
            "full_name": f"Secure {email}",
            "document_reference": f"DOC-SEC-{email}",
        },
        headers=_auth(token),
    )
    response = await client.post(
        "/api/v1/accounts",
        json={"account_type": "CHECKING", "currency": "BRL"},
        headers=_auth(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _fund(session: AsyncSession, account_id: str, value: str) -> None:
    await session.execute(
        text("UPDATE accounts SET balance = :value WHERE id = :id"),
        {"value": Decimal(value), "id": account_id},
    )
    await session.commit()
    session.expire_all()


async def test_financial_endpoints_require_authentication(
    api_client: httpx.AsyncClient,
) -> None:
    account_id = "00000000-0000-0000-0000-000000000001"
    responses = [
        await api_client.post(
            "/api/v1/transactions/transfers",
            json={
                "source_account_id": account_id,
                "destination_account_id": account_id,
                "amount": "10.00",
            },
            headers={"Idempotency-Key": "security-key"},
        ),
        await api_client.get("/api/v1/transactions"),
        await api_client.get(f"/api/v1/accounts/{account_id}/statement"),
        await api_client.get(f"/api/v1/ledger/accounts/{account_id}"),
    ]
    assert all(response.status_code == 401 for response in responses)


async def test_financial_endpoints_reject_invalid_token(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/transactions",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


async def test_cannot_transfer_from_account_of_another_customer(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_token = await _register(api_client, "sec-owner@example.com")
    owner_account = await _account(api_client, owner_token, "sec-owner@example.com")
    attacker_token = await _register(api_client, "sec-attacker@example.com")
    attacker_account = await _account(
        api_client, attacker_token, "sec-attacker@example.com"
    )
    await _fund(db_session, owner_account, "100.00")

    response = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": owner_account,
            "destination_account_id": attacker_account,
            "amount": "50.00",
        },
        headers=_auth(attacker_token, "steal-key"),
    )
    assert response.status_code == 403

    balance = await api_client.get(
        f"/api/v1/accounts/{owner_account}/balance",
        headers=_auth(owner_token),
    )
    assert balance.json()["balance"] == "100.00"


async def test_cannot_read_statement_of_another_customer(
    api_client: httpx.AsyncClient,
) -> None:
    owner_token = await _register(api_client, "stmt-owner@example.com")
    owner_account = await _account(api_client, owner_token, "stmt-owner@example.com")
    attacker_token = await _register(api_client, "stmt-attacker@example.com")

    response = await api_client.get(
        f"/api/v1/accounts/{owner_account}/statement",
        headers=_auth(attacker_token),
    )
    assert response.status_code == 403


async def test_idempotency_key_is_not_shared_between_users(
    api_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    first_token = await _register(api_client, "idem-first@example.com")
    first_account = await _account(api_client, first_token, "idem-first@example.com")
    second_token = await _register(api_client, "idem-second@example.com")
    second_account = await _account(api_client, second_token, "idem-second@example.com")
    await _fund(db_session, first_account, "100.00")

    first = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": first_account,
            "destination_account_id": second_account,
            "amount": "10.00",
        },
        headers=_auth(first_token, "shared-key"),
    )
    assert first.status_code == 201

    replay_by_other = await api_client.post(
        "/api/v1/transactions/transfers",
        json={
            "source_account_id": second_account,
            "destination_account_id": first_account,
            "amount": "10.00",
        },
        headers=_auth(second_token, "shared-key"),
    )
    assert replay_by_other.status_code == 409
