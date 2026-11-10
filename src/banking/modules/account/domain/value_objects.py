"""Value objects do módulo de contas."""

from __future__ import annotations

from enum import StrEnum


class AccountType(StrEnum):
    """Tipos de conta suportados."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class AccountStatus(StrEnum):
    """Estados possíveis de uma conta."""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


class Currency(StrEnum):
    """Moedas suportadas."""

    BRL = "BRL"
