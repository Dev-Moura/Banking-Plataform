"""Testes do serviço de access tokens JWT."""

from __future__ import annotations

from uuid import uuid4

import jwt
import pytest

from banking.core.exceptions import UnauthorizedError
from banking.modules.identity.infrastructure.security.jwt_service import (
    JwtAccessTokenService,
)
from banking.shared.contracts.security import Role

pytestmark = pytest.mark.unit


def _service(minutes: int = 15) -> JwtAccessTokenService:
    return JwtAccessTokenService(
        secret_key="unit-test-secret-key-with-more-than-sixty-four-bytes-for-hs512-tests!!",
        algorithm="HS256",
        expire_minutes=minutes,
        issuer="moura-banking-platform",
        audience="moura-banking-api",
    )


def test_creates_and_decodes_token() -> None:
    user_id = uuid4()
    token, expires_in = _service().create_access_token(
        user_id, "user@example.com", Role.CUSTOMER
    )
    principal = _service().decode_access_token(token)

    assert expires_in == 900
    assert principal.user_id == user_id
    assert principal.email == "user@example.com"
    assert principal.role is Role.CUSTOMER


def test_rejects_expired_token() -> None:
    token, _ = _service(minutes=-1).create_access_token(
        uuid4(), "user@example.com", Role.CUSTOMER
    )
    with pytest.raises(UnauthorizedError):
        _service().decode_access_token(token)


def test_rejects_wrong_audience() -> None:
    token, _ = _service().create_access_token(
        uuid4(), "user@example.com", Role.CUSTOMER
    )
    other = JwtAccessTokenService(
        secret_key="unit-test-secret-key-with-more-than-sixty-four-bytes-for-hs512-tests!!",
        algorithm="HS256",
        expire_minutes=15,
        issuer="moura-banking-platform",
        audience="another-api",
    )
    with pytest.raises(UnauthorizedError):
        other.decode_access_token(token)


def test_rejects_algorithm_confusion() -> None:
    payload = {
        "sub": str(uuid4()),
        "email": "user@example.com",
        "role": "CUSTOMER",
        "type": "access",
        "iss": "moura-banking-platform",
        "aud": "moura-banking-api",
    }
    token = jwt.encode(
        payload,
        "unit-test-secret-key-with-more-than-sixty-four-bytes-for-hs512-tests!!",
        algorithm="HS512",
    )
    with pytest.raises(UnauthorizedError):
        _service().decode_access_token(token)


def test_rejects_non_access_token_type() -> None:
    payload = {
        "sub": str(uuid4()),
        "email": "user@example.com",
        "role": "CUSTOMER",
        "type": "refresh",
        "iss": "moura-banking-platform",
        "aud": "moura-banking-api",
        "exp": 9999999999,
        "iat": 1,
    }
    token = jwt.encode(
        payload,
        "unit-test-secret-key-with-more-than-sixty-four-bytes-for-hs512-tests!!",
        algorithm="HS256",
    )
    with pytest.raises(UnauthorizedError):
        _service().decode_access_token(token)


def test_rejects_unsupported_algorithm_configuration() -> None:
    with pytest.raises(ValueError):
        JwtAccessTokenService(
            secret_key="x",
            algorithm="RS256",
            expire_minutes=15,
            issuer="i",
            audience="a",
        )
