"""Dependências HTTP do módulo de ledger."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from banking.infrastructure.database.session import get_session
from banking.modules.account.infrastructure.persistence.account_repository import (
    SqlAlchemyAccountRepository,
)
from banking.modules.customer.infrastructure.persistence.customer_repository import (
    SqlAlchemyCustomerRepository,
)
from banking.modules.ledger.application.use_cases.get_account_statement import (
    GetAccountStatementUseCase,
)
from banking.modules.ledger.application.use_cases.get_transaction_ledger import (
    GetTransactionLedgerUseCase,
)
from banking.modules.ledger.infrastructure.persistence.ledger_repository import (
    SqlAlchemyLedgerEntryRepository,
)
from banking.modules.transaction.infrastructure.persistence import (
    transaction_repository,
)


def get_account_statement_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetAccountStatementUseCase:
    """Monta o caso de uso de extrato por conta."""
    return GetAccountStatementUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
        ledger_repository=SqlAlchemyLedgerEntryRepository(session),
    )


def get_transaction_ledger_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetTransactionLedgerUseCase:
    """Monta o caso de uso de ledger por transação."""
    return GetTransactionLedgerUseCase(
        transaction_repository=transaction_repository.SqlAlchemyTransactionRepository(
            session
        ),
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
        ledger_repository=SqlAlchemyLedgerEntryRepository(session),
    )
