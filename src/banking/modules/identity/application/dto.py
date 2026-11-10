"""DTOs de entrada e saída do módulo de identidade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from banking.shared.contracts.security import Role


@dataclass(frozen=True, slots=True)
class RegisterInput:
    """Dados para cadastro de usuário."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginInput:
    """Credenciais de autenticação."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class UserOutput:
    """Representação pública de um usuário."""

    id: UUID
    email: str
    role: Role
    status: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Par de tokens emitido pela autenticação."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
