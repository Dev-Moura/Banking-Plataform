"""Adapter de rate limiting para a camada de aplicação."""

from __future__ import annotations

from banking.core.config import get_settings
from banking.infrastructure.cache.redis import (
    InMemoryRateLimiter,
    RedisRateLimiter,
    get_redis,
)


class RedisRateLimiterAdapter:
    """Rate limiter Redis que respeita a configuração de ambiente."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._limiter = RedisRateLimiter(get_redis())
        self._fallback = InMemoryRateLimiter()

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        """Retorna True quando a requisição é permitida."""
        if not self._settings.rate_limit_enabled:
            return True
        try:
            return await self._limiter.allow(key, limit, window_seconds)
        except Exception:
            return self._fallback.allow(key, limit, window_seconds)
