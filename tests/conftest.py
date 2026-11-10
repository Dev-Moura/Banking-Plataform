"""Configuração global de testes."""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "testing-secret-key-not-for-production")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://banking:banking@localhost:5432/banking_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
