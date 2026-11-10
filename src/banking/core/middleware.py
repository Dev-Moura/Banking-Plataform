"""Middlewares transversais: correlação, headers de segurança e payload."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from banking.core.config import get_settings

RequestHandler = Callable[[Request], Awaitable[Response]]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propaga ou gera identificadores de requisição e correlação."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Aplica headers defensivos em todas as respostas."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path.startswith(("/api/v1/identity", "/api/v1/auth")):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Rejeita corpos maiores que o limite configurado."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = 0
            if size > settings.max_payload_bytes:
                return JSONResponse(
                    status_code=413,
                    media_type="application/problem+json",
                    content={
                        "type": "https://moura-banking.local/problems/payload-too-large",
                        "title": "Payload Too Large",
                        "status": 413,
                        "detail": "O corpo da requisição excede o limite permitido.",
                    },
                )
        return await call_next(request)
