"""Paginação padronizada para listagens da API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Page[T]:
    """Página de resultados com metadados."""

    items: list[T]
    page: int
    page_size: int
    total: int

    @property
    def pages(self) -> int:
        """Quantidade total de páginas."""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    def to_dict(self, serialize: Callable[[T], dict[str, Any]]) -> dict[str, Any]:
        """Serializa a página usando um callable de item."""
        return {
            "items": [serialize(item) for item in self.items],
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "pages": self.pages,
        }


def normalize_pagination(page: int, page_size: int) -> tuple[int, int, int]:
    """Normaliza parâmetros de paginação e retorna (page, size, offset)."""
    safe_page = max(page, 1)
    safe_size = min(max(page_size, 1), 100)
    return safe_page, safe_size, (safe_page - 1) * safe_size
