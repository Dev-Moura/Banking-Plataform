"""Dependências HTTP do módulo de transações."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from banking.infrastructure.database.session import get_session
from banking.infrastructure.database.unit_of_work import UnitOfWork
from banking.modules.account.infrastructure.persistence.account_repository import (
    SqlAlchemyAccountRepository,
)
from banking.modules.customer.infrastructure.persistence.customer_repository import (
    SqlAlchemyCustomerRepository,
)
from banking.modules.identity.presentation.api.dependencies import get_clock
from banking.modules.ledger.infrastructure.persistence.ledger_repository import (
    SqlAlchemyLedgerEntryRepository,
)
from banking.modules.transaction.application.use_cases.get_transaction import (
    GetTransactionUseCase,
)
from banking.modules.transaction.application.use_cases.list_transactions import (
    ListTransactionsUseCase,
)
from banking.modules.transaction.application.use_cases.transfer import TransferUseCase
from banking.modules.transaction.infrastructure.persistence import (
    transaction_repository,
)


def get_transfer_use_case(
    session: AsyncSession = Depends(get_session),
) -> TransferUseCase:
    """Monta o caso de uso de transferência."""
    return TransferUseCase(
        transaction_repository=transaction_repository.SqlAlchemyTransactionRepository(
            session
        ),
        ledger_repository=SqlAlchemyLedgerEntryRepository(session),
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )


def get_transaction_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetTransactionUseCase:
    """Monta o caso de uso de consulta de transação."""
    return GetTransactionUseCase(
        transaction_repository=transaction_repository.SqlAlchemyTransactionRepository(
            session
        ),
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
    )


def get_list_transactions_use_case(
    session: AsyncSession = Depends(get_session),
) -> ListTransactionsUseCase:
    """Monta o caso de uso de listagem de transações."""
    return ListTransactionsUseCase(
        transaction_repository=transaction_repository.SqlAlchemyTransactionRepository(
            session
        ),
        customer_repository=SqlAlchemyCustomerRepository(session),
    )
