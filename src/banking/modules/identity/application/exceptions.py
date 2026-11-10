"""Mapeamento das exceções de identidade para erros HTTP."""

from __future__ import annotations

from banking.core.exceptions import ConflictError, UnauthorizedError


class EmailAlreadyExistsError(ConflictError):
    """E-mail já cadastrado."""

    type_slug = "email-already-exists"

    def __init__(self) -> None:
        super().__init__("Já existe uma conta com este e-mail.")


class InvalidCredentialsError(UnauthorizedError):
    """Credenciais inválidas."""

    type_slug = "invalid-credentials"

    def __init__(self) -> None:
        super().__init__("Credenciais inválidas.")


class AccountLockedError(UnauthorizedError):
    """Conta temporariamente bloqueada."""

    type_slug = "account-locked"

    def __init__(self) -> None:
        super().__init__("Credenciais inválidas.")


class InvalidRefreshTokenError(UnauthorizedError):
    """Refresh token inválido."""

    type_slug = "invalid-refresh-token"

    def __init__(self) -> None:
        super().__init__("Refresh token inválido ou expirado.")


class RefreshTokenReuseError(UnauthorizedError):
    """Reuso de refresh token detectado."""

    type_slug = "refresh-token-reuse"

    def __init__(self) -> None:
        super().__init__("Sessão revogada por suspeita de reuso de token.")
