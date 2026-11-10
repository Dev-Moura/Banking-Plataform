"""Regressão de segurança do módulo de identidade."""

from __future__ import annotations

import httpx
import pytest

pytestmark = [pytest.mark.security, pytest.mark.integration]

EMAIL = "security@example.com"
PASSWORD = "Correct@Pass123"


async def _register_and_login(client: httpx.AsyncClient) -> dict[str, str]:
    await client.post(
        "/api/v1/identity/register",
        json={"email": EMAIL, "password": PASSWORD},
    )
    response = await client.post(
        "/api/v1/identity/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()


async def test_me_requires_authentication(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/identity/me")
    assert response.status_code == 401


async def test_me_rejects_invalid_token(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/identity/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


async def test_me_does_not_leak_password_hash(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _register_and_login(api_client)
    response = await api_client.get(
        "/api/v1/identity/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    body = response.text.lower()
    assert "password" not in body
    assert "argon2" not in body


async def test_refresh_reuse_revokes_family(
    api_client: httpx.AsyncClient,
) -> None:
    tokens = await _register_and_login(api_client)
    first_refresh = tokens["refresh_token"]

    rotated = await api_client.post(
        "/api/v1/identity/refresh",
        json={"refresh_token": first_refresh},
    )
    assert rotated.status_code == 200

    reuse = await api_client.post(
        "/api/v1/identity/refresh",
        json={"refresh_token": first_refresh},
    )
    assert reuse.status_code == 401

    after_reuse = await api_client.post(
        "/api/v1/identity/refresh",
        json={"refresh_token": rotated.json()["refresh_token"]},
    )
    assert after_reuse.status_code == 401


async def test_login_uses_generic_error_message(
    api_client: httpx.AsyncClient,
) -> None:
    await api_client.post(
        "/api/v1/identity/register",
        json={"email": EMAIL, "password": PASSWORD},
    )
    wrong_password = await api_client.post(
        "/api/v1/identity/login",
        json={"email": EMAIL, "password": "Wrong@Pass123"},
    )
    unknown_user = await api_client.post(
        "/api/v1/identity/login",
        json={"email": "ghost@example.com", "password": PASSWORD},
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["detail"] == unknown_user.json()["detail"]
