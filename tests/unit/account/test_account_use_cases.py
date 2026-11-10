"""Testes unitários dos casos de uso de contas."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from banking.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from banking.modules.account.application.dto import CreateAccountInput
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
from banking.shared.contracts.security import Principal, Role
from tests.unit.account.fakes import (
    FakeAccountRepository,
    FakeClock,
    FakeCustomerRepository,
    FakeUnitOfWork,
    make_account,
    make_customer,
)


def _principal(role: Role = Role.CUSTOMER) -> Principal:
    return Principal(user_id=uuid4(), email="user@example.com", role=role)


async def test_create_account_for_customer() -> None:
    customers = FakeCustomerRepository()
    accounts = FakeAccountRepository()
    principal = _principal()
    customer = make_customer(principal.user_id)
    customers.customers[customer.id] = customer
    use_case = CreateAccountUseCase(accounts, customers, FakeUnitOfWork(), FakeClock())

    result = await use_case.execute(
        principal, CreateAccountInput(account_type="CHECKING")
    )

    assert result.customer_id == customer.id
    assert result.account_number == 10_000_001
    assert result.balance == Decimal("0.00")
    assert result.status == "ACTIVE"


async def test_create_account_without_customer_profile() -> None:
    use_case = CreateAccountUseCase(
        FakeAccountRepository(),
        FakeCustomerRepository(),
        FakeUnitOfWork(),
        FakeClock(),
    )

    with pytest.raises(NotFoundError):
        await use_case.execute(
            _principal(), CreateAccountInput(account_type="CHECKING")
        )


async def test_owner_can_read_account_and_balance() -> None:
    customers = FakeCustomerRepository()
    accounts = FakeAccountRepository()
    principal = _principal()
    customer = make_customer(principal.user_id)
    customers.customers[customer.id] = customer
    account = make_account(customer.id)
    accounts.accounts[account.id] = account

    fetched = await GetAccountUseCase(accounts, customers).execute(
        principal, account.id
    )
    balance = await GetBalanceUseCase(accounts, customers, FakeClock()).execute(
        principal, account.id
    )

    assert fetched.id == account.id
    assert balance.balance == Decimal("0.00")
    assert balance.currency == "BRL"


async def test_other_customer_cannot_read_account() -> None:
    customers = FakeCustomerRepository()
    accounts = FakeAccountRepository()
    owner = make_customer(uuid4())
    customers.customers[owner.id] = owner
    account = make_account(owner.id)
    accounts.accounts[account.id] = account

    with pytest.raises(ForbiddenError):
        await GetAccountUseCase(accounts, customers).execute(_principal(), account.id)


async def test_staff_can_read_any_account() -> None:
    customers = FakeCustomerRepository()
    accounts = FakeAccountRepository()
    owner = make_customer(uuid4())
    account = make_account(owner.id)
    accounts.accounts[account.id] = account

    result = await GetAccountUseCase(accounts, customers).execute(
        _principal(Role.BANK_OPERATOR), account.id
    )
    assert result.id == account.id


async def test_missing_account_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        await GetAccountUseCase(
            FakeAccountRepository(), FakeCustomerRepository()
        ).execute(_principal(), uuid4())


async def test_list_accounts_is_scoped_for_customer() -> None:
    customers = FakeCustomerRepository()
    accounts = FakeAccountRepository()
    principal = _principal()
    customer = make_customer(principal.user_id)
    customers.customers[customer.id] = customer
    own_account = make_account(customer.id)
    other_account = make_account(uuid4())
    accounts.accounts[own_account.id] = own_account
    accounts.accounts[other_account.id] = other_account
    use_case = ListAccountsUseCase(accounts, customers)

    page = await use_case.execute(principal, None, 1, 20)

    assert page.total == 1
    assert all(item.customer_id == customer.id for item in page.items)


async def test_list_accounts_for_staff_returns_all() -> None:
    accounts = FakeAccountRepository()
    first = make_account(uuid4())
    second = make_account(uuid4())
    accounts.accounts[first.id] = first
    accounts.accounts[second.id] = second

    page = await ListAccountsUseCase(accounts, FakeCustomerRepository()).execute(
        _principal(Role.AUDITOR), None, 1, 20
    )

    assert page.total == 2


async def test_update_status_rejects_invalid_value() -> None:
    use_case = UpdateAccountStatusUseCase(
        FakeAccountRepository(), FakeUnitOfWork(), FakeClock()
    )
    with pytest.raises(BadRequestError):
        await use_case.execute(uuid4(), "UNKNOWN")


async def test_update_status_rejects_system_account() -> None:
    accounts = FakeAccountRepository()
    system_account = make_account(uuid4(), is_system=True)
    accounts.accounts[system_account.id] = system_account
    use_case = UpdateAccountStatusUseCase(accounts, FakeUnitOfWork(), FakeClock())

    with pytest.raises(BadRequestError):
        await use_case.execute(system_account.id, "BLOCKED")


async def test_update_status_success() -> None:
    accounts = FakeAccountRepository()
    account = make_account(uuid4())
    accounts.accounts[account.id] = account
    use_case = UpdateAccountStatusUseCase(accounts, FakeUnitOfWork(), FakeClock())

    result = await use_case.execute(account.id, "BLOCKED")

    assert result.status == "BLOCKED"
    assert accounts.accounts[account.id].status == "BLOCKED"
