"""Dependências HTTP do módulo de clientes."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from banking.infrastructure.database.session import get_session
from banking.infrastructure.database.unit_of_work import UnitOfWork
from banking.modules.customer.application.use_cases.create_customer import (
    CreateCustomerUseCase,
)
from banking.modules.customer.application.use_cases.get_customer import (
    GetCustomerUseCase,
    GetMyCustomerUseCase,
)
from banking.modules.customer.application.use_cases.update_customer import (
    UpdateCustomerUseCase,
)
from banking.modules.customer.infrastructure.persistence.customer_repository import (
    SqlAlchemyCustomerRepository,
)
from banking.modules.identity.presentation.api.dependencies import get_clock


def get_create_customer_use_case(
    session: AsyncSession = Depends(get_session),
) -> CreateCustomerUseCase:
    """Monta o caso de uso de criação de cliente."""
    return CreateCustomerUseCase(
        customer_repository=SqlAlchemyCustomerRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )


def get_my_customer_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetMyCustomerUseCase:
    """Monta o caso de uso de consulta do próprio cliente."""
    return GetMyCustomerUseCase(SqlAlchemyCustomerRepository(session))


def get_customer_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetCustomerUseCase:
    """Monta o caso de uso de consulta por id."""
    return GetCustomerUseCase(SqlAlchemyCustomerRepository(session))


def get_update_customer_use_case(
    session: AsyncSession = Depends(get_session),
) -> UpdateCustomerUseCase:
    """Monta o caso de uso de atualização cadastral."""
    return UpdateCustomerUseCase(
        customer_repository=SqlAlchemyCustomerRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )
