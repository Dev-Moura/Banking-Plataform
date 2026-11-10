"""Testes unitários do caso de uso de transferência."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from banking.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from banking.modules.transaction.application.dto import TransferInput
from banking.modules.transaction.application.use_cases.transfer import TransferUseCase
from banking.modules.transaction.domain.value_objects import TransactionStatus
from banking.shared.contracts.security import Principal, Role
from tests.unit.account.fakes import (
    FakeAccountRepository,
    FakeClock,
    FakeCustomerRepository,
    FakeUnitOfWork,
    make_account,
    make_customer,
)
from tests.unit.transaction.fakes import (
    FakeLedgerEntryRepository,
    FakeTransactionRepository,
)


class Scenario:
    """Agrega as dependências de um cenário de transferência."""

    def __init__(self, source_balance: str = "100.00") -> None:
        self.principal = Principal(
            user_id=uuid4(), email="owner@example.com", role=Role.CUSTOMER
        )
        self.customers = FakeCustomerRepository()
        self.customer = make_customer(self.principal.user_id)
        self.customers.customers[self.customer.id] = self.customer
        self.accounts = FakeAccountRepository()
        self.source = make_account(self.customer.id)
        self.source.balance = Decimal(source_balance)
        self.destination = make_account(uuid4())
        self.destination.balance = Decimal("0.00")
        self.accounts.accounts[self.source.id] = self.source
        self.accounts.accounts[self.destination.id] = self.destination
        self.transactions = FakeTransactionRepository()
        self.ledger = FakeLedgerEntryRepository()
        self.uow = FakeUnitOfWork()
        self.use_case = TransferUseCase(
            transaction_repository=self.transactions,
            ledger_repository=self.ledger,
            account_repository=self.accounts,
            customer_repository=self.customers,
            unit_of_work=self.uow,
            clock=FakeClock(),
        )

    def input(
        self,
        amount: str = "40.00",
        key: str = "key-1",
        description: str | None = None,
    ) -> TransferInput:
        return TransferInput(
            source_account_id=self.source.id,
            destination_account_id=self.destination.id,
            amount=Decimal(amount),
            idempotency_key=key,
            description=description,
        )


async def test_transfer_updates_balances_and_writes_balanced_ledger() -> None:
    scenario = Scenario()

    result = await scenario.use_case.execute(scenario.principal, scenario.input())

    assert result.created is True
    assert result.transaction.status == TransactionStatus.COMPLETED.value
    assert scenario.source.balance == Decimal("60.00")
    assert scenario.destination.balance == Decimal("40.00")
    assert len(scenario.ledger.entries) == 2
    assert {entry.entry_type for entry in scenario.ledger.entries} == {
        "DEBIT",
        "CREDIT",
    }
    assert scenario.uow.commits == 1


async def test_replay_with_same_payload_returns_original_transaction() -> None:
    scenario = Scenario()
    data = scenario.input()

    first = await scenario.use_case.execute(scenario.principal, data)
    second = await scenario.use_case.execute(scenario.principal, data)

    assert second.created is False
    assert second.transaction.id == first.transaction.id
    assert scenario.source.balance == Decimal("60.00")
    assert len(scenario.transactions.transactions) == 1


async def test_same_key_with_different_payload_conflicts() -> None:
    scenario = Scenario()
    await scenario.use_case.execute(scenario.principal, scenario.input())

    with pytest.raises(ConflictError):
        await scenario.use_case.execute(
            scenario.principal, scenario.input(amount="10.00")
        )


async def test_insufficient_funds_has_no_side_effects() -> None:
    scenario = Scenario(source_balance="10.00")

    with pytest.raises(ValidationError):
        await scenario.use_case.execute(
            scenario.principal, scenario.input(amount="20.00")
        )

    assert scenario.source.balance == Decimal("10.00")
    assert scenario.destination.balance == Decimal("0.00")
    assert scenario.transactions.transactions == {}
    assert scenario.ledger.entries == []
    assert scenario.uow.commits == 0


async def test_source_must_belong_to_authenticated_customer() -> None:
    scenario = Scenario()
    scenario.source.customer_id = uuid4()

    with pytest.raises(ForbiddenError):
        await scenario.use_case.execute(scenario.principal, scenario.input())


async def test_missing_accounts_are_reported() -> None:
    scenario = Scenario()
    scenario.destination.id = uuid4()

    with pytest.raises(NotFoundError):
        await scenario.use_case.execute(scenario.principal, scenario.input())


async def test_inactive_accounts_are_rejected() -> None:
    scenario = Scenario()
    scenario.destination.status = "BLOCKED"

    with pytest.raises(ValidationError):
        await scenario.use_case.execute(scenario.principal, scenario.input())


async def test_currency_mismatch_is_rejected() -> None:
    scenario = Scenario()
    scenario.destination.currency = "USD"

    with pytest.raises(ValidationError):
        await scenario.use_case.execute(scenario.principal, scenario.input())


async def test_user_without_customer_profile_is_forbidden() -> None:
    scenario = Scenario()
    scenario.customers.customers.clear()

    with pytest.raises(ForbiddenError):
        await scenario.use_case.execute(scenario.principal, scenario.input())
