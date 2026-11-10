"""Caso de uso de consulta do ledger de uma transação."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.ledger.application.dto import LedgerEntryOutput
from banking.modules.ledger.application.interfaces import LedgerEntryRepository
from banking.modules.ledger.application.use_cases.get_account_statement import (
    to_output,
)
from banking.modules.transaction.application.access import ensure_transaction_access
from banking.modules.transaction.application.interfaces import TransactionRepository
from banking.shared.contracts.security import Principal


class GetTransactionLedgerUseCase:
    """Retorna os lançamentos contábeis de uma transação."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
        ledger_repository: LedgerEntryRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._accounts = account_repository
        self._customers = customer_repository
        self._ledger = ledger_repository

    async def execute(
        self, principal: Principal, transaction_id: UUID
    ) -> list[LedgerEntryOutput]:
        """Lista os lançamentos da transação autorizada."""
        transaction = await self._transactions.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError("Transação não encontrada.")
        await ensure_transaction_access(
            principal, transaction, self._accounts, self._customers
        )
        entries = await self._ledger.list_by_transaction(transaction_id)
        return [to_output(entry) for entry in entries]
