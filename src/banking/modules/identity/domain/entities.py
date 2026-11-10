"""Entidades de domínio do módulo de identidade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from banking.shared.contracts.security import Role


@dataclass(slots=True)
class User:
    """Usuário autenticável."""

    id: UUID
    email: str
    password_hash: str
    role: Role
    status: str
    failed_login_attempts: int
    locked_until: datetime | None
    created_at: datetime
    updated_at: datetime

    def is_locked(self, now: datetime) -> bool:
        """Indica se a conta está temporariamente bloqueada."""
        return self.locked_until is not None and self.locked_until > now

    def is_active(self) -> bool:
        """Indica se a conta pode autenticar."""
        return self.status == "ACTIVE"


@dataclass(slots=True)
class RefreshSession:
    """Sessão opaca de renovação de token."""

    id: UUID
    user_id: UUID
    token_hash: str
    family_id: UUID
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_id: UUID | None
    created_at: datetime

    def is_expired(self, now: datetime) -> bool:
        """Indica se a sessão expirou."""
        return self.expires_at <= now

    def is_revoked(self) -> bool:
        """Indica se a sessão foi revogada."""
        return self.revoked_at is not None
