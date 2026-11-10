"""Erros de domínio puros, independentes de framework."""

from __future__ import annotations


class DomainError(Exception):
    """Violação de regra de negócio."""


class InvalidMoneyError(DomainError):
    """Valor monetário inválido."""


class InsufficientFundsError(DomainError):
    """Saldo insuficiente para a operação."""


class InvalidTransferError(DomainError):
    """Transferência inválida (mesma conta, moeda divergente etc.)."""
