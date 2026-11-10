"""Dublês em memória para testes de contas e clientes."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from banking.modules.account.domain.entities import Account
from banking.modules.customer.domain.entities import Customer

FIXED_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class FakeClock:
    """Relógio fixo."""

    def now(self) -> datetime:
        return FIXED_NOW


class FakeUnitOfWork:
    """Unidade de trabalho em memória."""

    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


class FakeCustomerRepository:
    """Repositório de clientes em memória."""

    def __init__(self) -> None:
        self.customers: dict[UUID, Customer] = {}

    async def get_by_user_id(self, user_id: UUID) -> Customer | None:
        return next(
            (c for c in self.customers.values() if c.user_id == user_id),
            None,
        )

    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        return self.customers.get(customer_id)

    async def get_by_document(self, document_reference: str) -> Customer | None:
        return next(
            (
                c
                for c in self.customers.values()
                if c.document_reference == document_reference
            ),
            None,
        )

    async def add(self, customer: Customer) -> None:
        self.customers[customer.id] = customer

    async def update(self, customer: Customer) -> None:
        self.customers[customer.id] = customer


class FakeAccountRepository:
    """Repositório de contas em memória com numeração sequencial."""

    def __init__(self) -> None:
        self.accounts: dict[UUID, Account] = {}
        self._next_number = 10_000_001

    async def add(self, account: Account) -> Account:
        account.account_number = self._next_number
        self._next_number += 1
        self.accounts[account.id] = account
        return account

    async def get_by_id(self, account_id: UUID) -> Account | None:
        return self.accounts.get(account_id)

    async def list_by_customer(
        self,
        customer_id: UUID,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]:
        items = [
            a
            for a in self.accounts.values()
            if a.customer_id == customer_id
            and not a.is_system
            and (status is None or a.status == status)
        ]
        return items[offset : offset + limit], len(items)

    async def list_all(
        self,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Account], int]:
        items = [
            a
            for a in self.accounts.values()
            if not a.is_system and (status is None or a.status == status)
        ]
        return items[offset : offset + limit], len(items)

    async def update_status(self, account: Account) -> None:
        self.accounts[account.id] = account


def make_customer(user_id: UUID) -> Customer:
    """Cria um cliente de teste."""
    return Customer(
        id=uuid4(),
        user_id=user_id,
        full_name="Test Customer",
        document_reference=f"DOC-{user_id}",
        birth_date=None,
        status="ACTIVE",
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_account(
    customer_id: UUID, *, is_system: bool = False, status: str = "ACTIVE"
) -> Account:
    """Cria uma conta de teste."""
    return Account(
        id=uuid4(),
        customer_id=customer_id,
        account_number=10_000_001,
        account_type="CHECKING",
        status=status,
        currency="BRL",
        balance=Decimal("0.00"),
        is_system=is_system,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )
