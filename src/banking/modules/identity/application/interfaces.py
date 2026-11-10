"""Portas (interfaces) da camada de aplicação de identidade."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from banking.modules.identity.domain.entities import RefreshSession, User
from banking.shared.contracts.security import Principal, Role


class UserRepository(Protocol):
    """Abstração de persistência de usuários."""

    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def add(self, user: User) -> None: ...

    async def update(self, user: User) -> None: ...


class RefreshSessionRepository(Protocol):
    """Abstração de persistência de sessões de refresh."""

    async def add(self, session: RefreshSession) -> None: ...

    async def get_by_token_hash(self, token_hash: str) -> RefreshSession | None: ...

    async def update(self, session: RefreshSession) -> None: ...

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None: ...


class PasswordHasher(Protocol):
    """Abstração de hash de senhas."""

    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...

    def needs_rehash(self, password_hash: str) -> bool: ...


class AccessTokenService(Protocol):
    """Abstração de emissão e validação de access tokens."""

    def create_access_token(
        self, user_id: UUID, email: str, role: Role
    ) -> tuple[str, int]: ...

    def decode_access_token(self, token: str) -> Principal: ...


class UnitOfWorkPort(Protocol):
    """Abstração de unidade de trabalho transacional."""

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class Clock(Protocol):
    """Abstração de relógio para testes determinísticos."""

    def now(self) -> datetime: ...
