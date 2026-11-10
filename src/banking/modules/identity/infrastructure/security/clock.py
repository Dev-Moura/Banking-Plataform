"""Relógio de sistema para a camada de aplicação."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Implementação de Clock baseada no relógio do sistema em UTC."""

    def now(self) -> datetime:
        """Retorna o instante atual em UTC."""
        return datetime.now(UTC)
