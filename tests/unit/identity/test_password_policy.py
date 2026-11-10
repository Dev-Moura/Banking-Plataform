"""Testes da política de senha e normalização de e-mail."""

from __future__ import annotations

import pytest

from banking.modules.identity.domain.services import PasswordPolicy
from banking.modules.identity.domain.value_objects import (
    Email,
    InvalidEmailError,
    WeakPasswordError,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "password",
    [
        "short1!A",
        "alllowercase1!",
        "ALLUPPERCASE1!",
        "NoDigitsHere!",
        "NoSpecial12345",
    ],
)
def test_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(WeakPasswordError):
        PasswordPolicy.validate(password)


def test_accepts_strong_password() -> None:
    PasswordPolicy.validate("Correct@Pass123")


def test_email_is_normalized_to_lowercase() -> None:
    assert Email("  User@Example.COM ").value == "user@example.com"


@pytest.mark.parametrize("value", ["invalid", "a@b", "@example.com", "a b@c.com"])
def test_rejects_invalid_email(value: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(value)
