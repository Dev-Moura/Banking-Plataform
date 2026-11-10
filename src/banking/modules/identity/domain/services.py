"""Serviços e políticas puras do domínio de identidade."""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import UTC, datetime, timedelta

from banking.modules.identity.domain.value_objects import WeakPasswordError

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_SPECIALS = set(string.punctuation)


class PasswordPolicy:
    """Política de complexidade de senha."""

    @staticmethod
    def validate(password: str) -> None:
        """Valida a senha ou lança WeakPasswordError."""
        if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
            raise WeakPasswordError(
                f"A senha deve ter entre {PASSWORD_MIN_LENGTH} e "
                f"{PASSWORD_MAX_LENGTH} caracteres."
            )
        if not any(char.isupper() for char in password):
            raise WeakPasswordError("A senha deve conter letra maiúscula.")
        if not any(char.islower() for char in password):
            raise WeakPasswordError("A senha deve conter letra minúscula.")
        if not any(char.isdigit() for char in password):
            raise WeakPasswordError("A senha deve conter dígito.")
        if not any(char in PASSWORD_SPECIALS for char in password):
            raise WeakPasswordError("A senha deve conter caractere especial.")


class RefreshTokenPolicy:
    """Geração, hash e expiração de refresh tokens opacos."""

    @staticmethod
    def generate() -> str:
        """Gera um token opaco com alta entropia."""
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash(token: str) -> str:
        """Retorna SHA-256 hexadecimal do token."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def expiry(now: datetime, days: int) -> datetime:
        """Calcula a expiração do refresh token."""
        return now + timedelta(days=days)


def utc_now() -> datetime:
    """Retorna o instante atual em UTC com timezone."""
    return datetime.now(UTC)
