"""Contratos de segurança compartilhados entre módulos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    """Papéis de acesso suportados pela plataforma."""

    CUSTOMER = "CUSTOMER"
    BANK_OPERATOR = "BANK_OPERATOR"
    BANK_ADMIN = "BANK_ADMIN"
    AUDITOR = "AUDITOR"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True, slots=True)
class Principal:
    """Identidade autenticada e autorizada de uma requisição."""

    user_id: UUID
    email: str
    role: Role
