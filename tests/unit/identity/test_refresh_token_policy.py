"""Testes da política de refresh tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from banking.modules.identity.domain.services import RefreshTokenPolicy

pytestmark = pytest.mark.unit


def test_generated_tokens_are_unique_and_opaque() -> None:
    first = RefreshTokenPolicy.generate()
    second = RefreshTokenPolicy.generate()

    assert first != second
    assert len(first) >= 48


def test_hash_is_stable_and_hex() -> None:
    token = RefreshTokenPolicy.generate()
    digest = RefreshTokenPolicy.hash(token)

    assert digest == RefreshTokenPolicy.hash(token)
    assert len(digest) == 64
    int(digest, 16)


def test_expiry_uses_configured_days() -> None:
    now = datetime.now(UTC)
    expiry = RefreshTokenPolicy.expiry(now, 7)

    assert expiry - now == timedelta(days=7)
