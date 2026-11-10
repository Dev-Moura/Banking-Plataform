"""Schemas Pydantic do módulo de identidade."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from banking.shared.contracts.security import Role


class RegisterRequest(BaseModel):
    """Payload de cadastro."""

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    """Payload de login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """Payload de renovação de tokens."""

    refresh_token: str = Field(min_length=16, max_length=512)


class UserResponse(BaseModel):
    """Representação pública do usuário."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: Role
    status: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Par de tokens emitido pela autenticação."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
