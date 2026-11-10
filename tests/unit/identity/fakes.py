"""Dublês em memória para testes de casos de uso de identidade."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from banking.modules.identity.domain.entities import RefreshSession, User
from banking.shared.contracts.security import Principal, Role


class FakeClock:
    """Relógio controlável."""

    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime.now(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class FakeUnitOfWork:
    """Unidade de trabalho em memória."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakePasswordHasher:
    """Hasher determinístico."""

    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed::{password}"

    def needs_rehash(self, password_hash: str) -> bool:
        return False


class FakeUserRepository:
    """Repositório de usuários em memória."""

    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def add(self, user: User) -> None:
        self.users[user.id] = user

    async def update(self, user: User) -> None:
        self.users[user.id] = user


class FakeRefreshSessionRepository:
    """Repositório de sessões em memória."""

    def __init__(self) -> None:
        self.sessions: dict[str, RefreshSession] = {}

    async def add(self, session: RefreshSession) -> None:
        self.sessions[session.token_hash] = session

    async def get_by_token_hash(self, token_hash: str) -> RefreshSession | None:
        return self.sessions.get(token_hash)

    async def update(self, session: RefreshSession) -> None:
        self.sessions[session.token_hash] = session

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        for session in self.sessions.values():
            if session.family_id == family_id and session.revoked_at is None:
                session.revoked_at = revoked_at


class FakeTokenService:
    """Serviço de tokens determinístico."""

    def create_access_token(
        self, user_id: UUID, email: str, role: Role
    ) -> tuple[str, int]:
        return f"access::{user_id}", 900

    def decode_access_token(self, token: str) -> Principal:
        raise NotImplementedError
