"""Exceções de domínio do módulo de identidade."""

from __future__ import annotations

from banking.shared.domain.errors import DomainError


class EmailAlreadyExistsError(DomainError):
    """E-mail já cadastrado."""


class InvalidCredentialsError(DomainError):
    """Credenciais inválidas."""


class AccountLockedError(DomainError):
    """Conta temporariamente bloqueada por tentativas inválidas."""


class InvalidRefreshTokenError(DomainError):
    """Refresh token inexistente, expirado ou revogado."""


class RefreshTokenReuseError(DomainError):
    """Reuso de refresh token já rotacionado."""
