"""Dependências HTTP do módulo de contas."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from banking.infrastructure.database.session import get_session
from banking.infrastructure.database.unit_of_work import UnitOfWork
from banking.modules.account.application.use_cases.create_account import (
    CreateAccountUseCase,
)
from banking.modules.account.application.use_cases.get_account import GetAccountUseCase
from banking.modules.account.application.use_cases.get_balance import GetBalanceUseCase
from banking.modules.account.application.use_cases.list_accounts import (
    ListAccountsUseCase,
)
from banking.modules.account.application.use_cases.update_account_status import (
    UpdateAccountStatusUseCase,
)
from banking.modules.account.infrastructure.persistence.account_repository import (
    SqlAlchemyAccountRepository,
)
from banking.modules.customer.infrastructure.persistence.customer_repository import (
    SqlAlchemyCustomerRepository,
)
from banking.modules.identity.presentation.api.dependencies import get_clock


def get_create_account_use_case(
    session: AsyncSession = Depends(get_session),
) -> CreateAccountUseCase:
    """Monta o caso de uso de abertura de conta."""
    return CreateAccountUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )


def get_list_accounts_use_case(
    session: AsyncSession = Depends(get_session),
) -> ListAccountsUseCase:
    """Monta o caso de uso de listagem."""
    return ListAccountsUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
    )


def get_get_account_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetAccountUseCase:
    """Monta o caso de uso de consulta por id."""
    return GetAccountUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
    )


def get_balance_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetBalanceUseCase:
    """Monta o caso de uso de consulta de saldo."""
    return GetBalanceUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        customer_repository=SqlAlchemyCustomerRepository(session),
        clock=get_clock(),
    )


def get_update_status_use_case(
    session: AsyncSession = Depends(get_session),
) -> UpdateAccountStatusUseCase:
    """Monta o caso de uso de alteração de status."""
    return UpdateAccountStatusUseCase(
        account_repository=SqlAlchemyAccountRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )
