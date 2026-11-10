"""Hash de senhas com Argon2id."""

from __future__ import annotations

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


class Argon2PasswordHasher:
    """Implementação de PasswordHasher usando Argon2id."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    def hash(self, password: str) -> str:
        """Gera hash Argon2id."""
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        """Verifica senha contra hash, sem propagar detalhes."""
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Indica se o hash precisa ser atualizado."""
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except InvalidHashError:
            return True
