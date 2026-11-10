"""Fluxo de integração do módulo de clientes com PostgreSQL real."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration

PASSWORD = "Correct@Pass123"


async def _authenticate(client: httpx.AsyncClient, email: str) -> dict[str, str]:
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
    return login.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_create_read_and_update_customer(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _authenticate(api_client, "customer@example.com")

    created = await api_client.post(
        "/api/v1/customers",
        json={
            "full_name": "  Maria Silva  ",
            "document_reference": "DOC-001",
            "birth_date": "1990-05-10",
        },
        headers=_auth(tokens["access_token"]),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["full_name"] == "Maria Silva"
    assert body["status"] == "ACTIVE"
    customer_id = body["id"]

    me = await api_client.get(
        "/api/v1/customers/me", headers=_auth(tokens["access_token"])
    )
    assert me.status_code == 200
    assert me.json()["id"] == customer_id

    by_id = await api_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=_auth(tokens["access_token"]),
    )
    assert by_id.status_code == 200

    updated = await api_client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"full_name": "Maria Souza"},
        headers=_auth(tokens["access_token"]),
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Maria Souza"


async def test_duplicate_customer_is_conflict(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _authenticate(api_client, "dup@example.com")
    payload = {
        "full_name": "Duplicate User",
        "document_reference": "DOC-DUP",
    }
    first = await api_client.post(
        "/api/v1/customers", json=payload, headers=_auth(tokens["access_token"])
    )
    assert first.status_code == 201

    second = await api_client.post(
        "/api/v1/customers", json=payload, headers=_auth(tokens["access_token"])
    )
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")


async def test_duplicate_document_is_conflict(
    api_client: httpx.AsyncClient,
) -> None:
    first_tokens = await _authenticate(api_client, "first@example.com")
    second_tokens = await _authenticate(api_client, "second@example.com")

    payload = {
        "full_name": "First Owner",
        "document_reference": "DOC-SHARED",
    }
    first = await api_client.post(
        "/api/v1/customers",
        json=payload,
        headers=_auth(first_tokens["access_token"]),
    )
    assert first.status_code == 201

    second = await api_client.post(
        "/api/v1/customers",
        json={**payload, "full_name": "Second Owner"},
        headers=_auth(second_tokens["access_token"]),
    )
    assert second.status_code == 409


async def test_customer_requires_authentication(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/customers/me")
    assert response.status_code == 401


async def test_customer_is_not_visible_to_other_user(
    api_client: httpx.AsyncClient,
) -> None:
    owner = await _authenticate(api_client, "owner@example.com")
    intruder = await _authenticate(api_client, "intruder@example.com")

    created = await api_client.post(
        "/api/v1/customers",
        json={"full_name": "Owner Name", "document_reference": "DOC-OWNER"},
        headers=_auth(owner["access_token"]),
    )
    assert created.status_code == 201

    response = await api_client.get(
        f"/api/v1/customers/{created.json()['id']}",
        headers=_auth(intruder["access_token"]),
    )
    assert response.status_code == 403
