"""Caso de uso de consulta de transação."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.transaction.application.access import ensure_transaction_access
from banking.modules.transaction.application.dto import TransactionOutput
from banking.modules.transaction.application.interfaces import TransactionRepository
from banking.modules.transaction.application.use_cases.transfer import to_output
from banking.shared.contracts.security import Principal


class GetTransactionUseCase:
    """Consulta uma transação com verificação de participação."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._accounts = account_repository
        self._customers = customer_repository

    async def execute(
        self, principal: Principal, transaction_id: UUID
    ) -> TransactionOutput:
        """Retorna a transação autorizada."""
        transaction = await self._transactions.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError("Transação não encontrada.")
        await ensure_transaction_access(
            principal, transaction, self._accounts, self._customers
        )
        return to_output(transaction)
