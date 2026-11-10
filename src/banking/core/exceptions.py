"""Exceções de aplicação mapeadas para Problem Details (RFC 9457)."""

from __future__ import annotations

from typing import Any

PROBLEM_BASE = "https://moura-banking.local/problems"


class AppError(Exception):
    """Erro base de aplicação com status HTTP e tipo de problema."""

    status_code: int = 500
    title: str = "Internal Server Error"
    type_slug: str = "internal-error"

    def __init__(
        self,
        detail: str | None = None,
        *,
        errors: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.detail = detail or self.title
        self.errors = errors or []
        self.headers = headers or {}
        super().__init__(self.detail)

    @property
    def type_uri(self) -> str:
        """URI identificadora do tipo de problema."""
        return f"{PROBLEM_BASE}/{self.type_slug}"


class ValidationError(AppError):
    """Dados de entrada inválidos."""

    status_code = 422
    title = "Unprocessable Entity"
    type_slug = "validation-error"


class BadRequestError(AppError):
    """Requisição malformada."""

    status_code = 400
    title = "Bad Request"
    type_slug = "bad-request"


class UnauthorizedError(AppError):
    """Credenciais ausentes ou inválidas."""

    status_code = 401
    title = "Unauthorized"
    type_slug = "unauthorized"


class ForbiddenError(AppError):
    """Autenticado, porém sem permissão para o recurso."""

    status_code = 403
    title = "Forbidden"
    type_slug = "forbidden"


class NotFoundError(AppError):
    """Recurso inexistente."""

    status_code = 404
    title = "Not Found"
    type_slug = "not-found"


class ConflictError(AppError):
    """Conflito de estado ou unicidade."""

    status_code = 409
    title = "Conflict"
    type_slug = "conflict"


class RateLimitError(AppError):
    """Limite de requisições excedido."""

    status_code = 429
    title = "Too Many Requests"
    type_slug = "rate-limit-exceeded"


class PayloadTooLargeError(AppError):
    """Corpo da requisição acima do limite permitido."""

    status_code = 413
    title = "Payload Too Large"
    type_slug = "payload-too-large"


class ServiceUnavailableError(AppError):
    """Dependência externa indisponível."""

    status_code = 503
    title = "Service Unavailable"
    type_slug = "service-unavailable"
