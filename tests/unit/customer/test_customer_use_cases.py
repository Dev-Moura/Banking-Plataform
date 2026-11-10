"""Testes unitários dos casos de uso de clientes."""

from __future__ import annotations

from uuid import uuid4

import pytest

from banking.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from banking.modules.customer.application.dto import (
    CreateCustomerInput,
    UpdateCustomerInput,
)
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
from banking.shared.contracts.security import Principal, Role
from tests.unit.account.fakes import (
    FakeClock,
    FakeCustomerRepository,
    FakeUnitOfWork,
    make_customer,
)


def _principal(role: Role = Role.CUSTOMER) -> Principal:
    return Principal(user_id=uuid4(), email="user@example.com", role=role)


async def test_create_customer_strips_fields() -> None:
    use_case = CreateCustomerUseCase(
        FakeCustomerRepository(), FakeUnitOfWork(), FakeClock()
    )
    principal = _principal()

    result = await use_case.execute(
        principal,
        CreateCustomerInput(
            full_name="  Ana Lima  ",
            document_reference="  DOC-1  ",
            birth_date=None,
        ),
    )

    assert result.full_name == "Ana Lima"
    assert result.document_reference == "DOC-1"
    assert result.user_id == principal.user_id
    assert result.status == "ACTIVE"


async def test_create_customer_twice_conflicts() -> None:
    customers = FakeCustomerRepository()
    use_case = CreateCustomerUseCase(customers, FakeUnitOfWork(), FakeClock())
    principal = _principal()
    data = CreateCustomerInput(
        full_name="Ana Lima", document_reference="DOC-1", birth_date=None
    )

    await use_case.execute(principal, data)

    with pytest.raises(ConflictError):
        await use_case.execute(principal, data)


async def test_create_customer_with_duplicate_document_conflicts() -> None:
    customers = FakeCustomerRepository()
    existing = make_customer(uuid4())
    existing.document_reference = "DOC-1"
    customers.customers[existing.id] = existing
    use_case = CreateCustomerUseCase(customers, FakeUnitOfWork(), FakeClock())

    with pytest.raises(ConflictError):
        await use_case.execute(
            _principal(),
            CreateCustomerInput(
                full_name="Other Name",
                document_reference="DOC-1",
                birth_date=None,
            ),
        )


async def test_get_my_customer_requires_profile() -> None:
    with pytest.raises(NotFoundError):
        await GetMyCustomerUseCase(FakeCustomerRepository()).execute(_principal())


async def test_get_customer_checks_ownership() -> None:
    customers = FakeCustomerRepository()
    owner = make_customer(uuid4())
    customers.customers[owner.id] = owner
    use_case = GetCustomerUseCase(customers)

    with pytest.raises(ForbiddenError):
        await use_case.execute(_principal(), owner.id)

    allowed = await use_case.execute(_principal(Role.AUDITOR), owner.id)
    assert allowed.id == owner.id


async def test_update_customer_by_owner_and_admin() -> None:
    customers = FakeCustomerRepository()
    owner_principal = _principal(Role.CUSTOMER)
    owner = make_customer(owner_principal.user_id)
    customers.customers[owner.id] = owner
    use_case = UpdateCustomerUseCase(customers, FakeUnitOfWork(), FakeClock())

    updated = await use_case.execute(
        owner_principal,
        owner.id,
        UpdateCustomerInput(full_name="New Name"),
    )
    assert updated.full_name == "New Name"

    admin_update = await use_case.execute(
        _principal(Role.BANK_ADMIN),
        owner.id,
        UpdateCustomerInput(full_name="Admin Name"),
    )
    assert admin_update.full_name == "Admin Name"


async def test_update_customer_rejects_other_customer() -> None:
    customers = FakeCustomerRepository()
    owner = make_customer(uuid4())
    customers.customers[owner.id] = owner
    use_case = UpdateCustomerUseCase(customers, FakeUnitOfWork(), FakeClock())

    with pytest.raises(ForbiddenError):
        await use_case.execute(
            _principal(),
            owner.id,
            UpdateCustomerInput(full_name="Hijack"),
        )
