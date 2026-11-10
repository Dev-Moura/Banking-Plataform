"""Value objects compartilhados de domínio."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from banking.shared.domain.errors import InvalidMoneyError

MONEY_QUANT = Decimal("0.01")
SUPPORTED_CURRENCIES = frozenset({"BRL"})


@dataclass(frozen=True, slots=True)
class Money:
    """Valor monetário com precisão decimal fixa."""

    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, ValueError) as exc:
                raise InvalidMoneyError("Valor monetário inválido.") from exc
        if self.currency not in SUPPORTED_CURRENCIES:
            raise InvalidMoneyError(f"Moeda não suportada: {self.currency}.")
        object.__setattr__(self, "amount", self.amount.quantize(MONEY_QUANT))

    @classmethod
    def from_str(cls, value: str, currency: str = "BRL") -> Money:
        """Cria Money a partir de string decimal, evitando float."""
        try:
            return cls(Decimal(value), currency)
        except (InvalidOperation, ValueError) as exc:
            raise InvalidMoneyError("Valor monetário inválido.") from exc

    def is_positive(self) -> bool:
        """Indica se o valor é estritamente positivo."""
        return self.amount > 0

    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise InvalidMoneyError("Moedas divergentes.")

    def __str__(self) -> str:
        return f"{self.amount:.2f}"
