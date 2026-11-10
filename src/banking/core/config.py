"""Configuração centralizada baseada em variáveis de ambiente."""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = False
    app_name: str = "Moura Banking Platform"
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://banking:banking@localhost:5432/banking"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = ""

    jwt_secret_key: str = ""
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    jwt_issuer: str = "moura-banking-platform"
    jwt_audience: str = "moura-banking-api"
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)

    password_hash_scheme: str = "argon2id"  # noqa: S105
    max_payload_bytes: int = Field(default=1_048_576, ge=1024)
    rate_limit_enabled: bool = True

    @property
    def is_production(self) -> bool:
        """Indica se o ambiente é de produção."""
        return self.app_env == "production"

    @property
    def docs_enabled(self) -> bool:
        """Swagger/OpenAPI habilitados apenas fora de produção."""
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    """Retorna a configuração singleton, gerando segredo efêmero em dev."""
    settings = Settings()
    if not settings.jwt_secret_key:
        if settings.is_production:
            msg = "JWT_SECRET_KEY é obrigatório em produção."
            raise RuntimeError(msg)
        settings.jwt_secret_key = secrets.token_urlsafe(48)
    return settings
