"""Fluxo de integração do módulo de identidade com PostgreSQL real."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration

EMAIL = "user@example.com"
PASSWORD = "Correct@Pass123"


async def test_register_login_me_refresh_logout(
    api_client: httpx.AsyncClient,
) -> None:
    register = await api_client.post(
        "/api/v1/identity/register",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert register.status_code == 201
    assert register.json()["email"] == EMAIL
    assert "password" not in register.text

    login = await api_client.post(
        "/api/v1/identity/login",
        json={"email": EMAIL.upper(), "password": PASSWORD},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"
    access = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    me = await api_client.get(
        "/api/v1/identity/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL
    assert me.json()["role"] == "CUSTOMER"

    refreshed = await api_client.post(
        "/api/v1/identity/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != refresh_token

    logout = await api_client.post(
        "/api/v1/identity/logout",
        json={"refresh_token": refreshed.json()["refresh_token"]},
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert logout.status_code == 204


async def test_duplicate_email_is_conflict(api_client: httpx.AsyncClient) -> None:
    first = await api_client.post(
        "/api/v1/identity/register",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert first.status_code == 201

    second = await api_client.post(
        "/api/v1/identity/register",
        json={"email": EMAIL.upper(), "password": PASSWORD},
    )
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")


async def test_weak_password_is_rejected(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/identity/register",
        json={"email": "weak@example.com", "password": "weakpass"},
    )
    assert response.status_code == 422
