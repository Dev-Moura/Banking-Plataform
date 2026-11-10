"""Cliente Redis assíncrono com fallback em memória para testes."""

from __future__ import annotations

import time
from functools import lru_cache

from redis.asyncio import Redis

from banking.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    """Retorna o cliente Redis singleton."""
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Encerra o cliente Redis."""
    client = get_redis()
    await client.aclose()
    get_redis.cache_clear()


class InMemoryRateLimiter:
    """Rate limiter em memória para ambientes de teste."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        hits = [t for t in self._hits.get(key, []) if now - t < window_seconds]
        if len(hits) >= limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True

    def reset(self) -> None:
        self._hits.clear()


class RedisRateLimiter:
    """Rate limiter de janela fixa usando INCR + EXPIRE."""

    def __init__(self, client: Redis) -> None:
        self.client = client

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        redis_key = f"ratelimit:{key}"
        current = await self.client.incr(redis_key)
        if current == 1:
            await self.client.expire(redis_key, window_seconds)
        return int(current) <= limit
