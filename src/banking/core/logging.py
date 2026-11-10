"""Configuração de logging estruturado com redação de dados sensíveis."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "jwt_secret_key",
    "document_reference",
    "cpf",
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("***" if key.lower() in SENSITIVE_KEYS else _redact(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    """Formata registros como JSON de uma linha."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("correlation_id", "request_id", "user_id", "method", "path"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if isinstance(record.args, dict):
            payload["context"] = _redact(record.args)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configura o logging raiz para saída JSON estruturada."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
