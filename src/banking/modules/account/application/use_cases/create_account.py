"""Caso de uso de abertura de conta."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from banking.core.exceptions import NotFoundError
from banking.modules.account.application.dto import AccountOutput, CreateAccountInput
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.account.domain.entities import Account
from banking.modules.account.domain.value_objects import (
    AccountStatus,
    AccountType,
    Currency,
)
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.identity.application.interfaces import Clock, UnitOfWorkPort
from banking.shared.contracts.security import Principal


class CreateAccountUseCase:
    """Abre uma conta ativa com saldo inicial zero."""

    def __init__(
        self,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository
        self._uow = unit_of_work
        self._clock = clock

    async def execute(
        self, principal: Principal, data: CreateAccountInput
    ) -> AccountOutput:
        """Cria a conta para o cliente do usuário autenticado."""
        customer = await self._customers.get_by_user_id(principal.user_id)
        if customer is None:
            raise NotFoundError("Cadastre-se como cliente antes de abrir uma conta.")

        now = self._clock.now()
        account = Account(
            id=uuid4(),
            customer_id=customer.id,
            account_number=0,
            account_type=AccountType(data.account_type).value,
            status=AccountStatus.ACTIVE.value,
            currency=Currency(data.currency).value,
            balance=Decimal("0.00"),
            is_system=False,
            created_at=now,
            updated_at=now,
        )
        persisted = await self._accounts.add(account)
        await self._uow.commit()
        return AccountOutput(
            id=persisted.id,
            customer_id=persisted.customer_id,
            account_number=persisted.account_number,
            account_type=persisted.account_type,
            status=persisted.status,
            currency=persisted.currency,
            balance=persisted.balance,
            created_at=persisted.created_at,
        )
