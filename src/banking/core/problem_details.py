"""Handlers de exceção no formato Problem Details (RFC 9457)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from banking.core.exceptions import AppError

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    type_uri: str,
    detail: str,
    errors: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Monta uma resposta Problem Details consistente."""
    body: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "correlation_id": _correlation_id(request),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
        content=body,
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers globais de exceção."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status_code,
            title=exc.title,
            type_uri=exc.type_uri,
            detail=exc.detail,
            errors=exc.errors,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(part) for part in err.get("loc", [])),
                "message": err.get("msg", "valor inválido"),
                "type": err.get("type", "validation_error"),
            }
            for err in exc.errors()
        ]
        return problem_response(
            request,
            status=422,
            title="Unprocessable Entity",
            type_uri="https://moura-banking.local/problems/validation-error",
            detail="Um ou mais campos da requisição são inválidos.",
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status_code,
            title=str(exc.detail) or "HTTP Error",
            type_uri=f"https://moura-banking.local/problems/http-{exc.status_code}",
            detail=str(exc.detail),
            headers=dict(exc.headers or {}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Erro não tratado", extra={"correlation_id": _correlation_id(request)}
        )
        return problem_response(
            request,
            status=500,
            title="Internal Server Error",
            type_uri="https://moura-banking.local/problems/internal-error",
            detail="Ocorreu um erro interno. Tente novamente mais tarde.",
        )
