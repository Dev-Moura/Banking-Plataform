"""Value objects do domínio de identidade."""

from __future__ import annotations

import re
from dataclasses import dataclass

from banking.shared.domain.errors import DomainError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidEmailError(DomainError):
    """E-mail em formato inválido."""


class WeakPasswordError(DomainError):
    """Senha não atende à política mínima."""


@dataclass(frozen=True, slots=True)
class Email:
    """E-mail normalizado e validado."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if len(normalized) > 320 or not EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError("E-mail inválido.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
