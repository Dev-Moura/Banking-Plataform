"""Testes do caso de uso de login e lockout."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from banking.modules.identity.application.dto import LoginInput
from banking.modules.identity.application.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
)
from banking.modules.identity.application.use_cases.login import LoginUseCase
from banking.modules.identity.domain.entities import User
from banking.modules.identity.domain.value_objects import Email
from banking.shared.contracts.security import Role
from tests.unit.identity.fakes import (
    FakeClock,
    FakePasswordHasher,
    FakeRefreshSessionRepository,
    FakeTokenService,
    FakeUnitOfWork,
    FakeUserRepository,
)

pytestmark = pytest.mark.unit

PASSWORD = "Correct@Pass123"


async def _build() -> tuple[
    LoginUseCase,
    FakeUserRepository,
    FakeRefreshSessionRepository,
    FakeClock,
    User,
]:
    clock = FakeClock()
    users = FakeUserRepository()
    sessions = FakeRefreshSessionRepository()
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash=f"hashed::{PASSWORD}",
        role=Role.CUSTOMER,
        status="ACTIVE",
        failed_login_attempts=0,
        locked_until=None,
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    await users.add(user)
    use_case = LoginUseCase(
        user_repository=users,
        session_repository=sessions,
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
        unit_of_work=FakeUnitOfWork(),
        clock=clock,
        refresh_expire_days=7,
    )
    return use_case, users, sessions, clock, user


async def test_login_emits_tokens_and_persists_session() -> None:
    use_case, _, sessions, _, user = await _build()

    tokens = await use_case.execute(
        LoginInput(email="USER@example.com", password=PASSWORD)
    )

    assert tokens.access_token.startswith("access::")
    assert tokens.refresh_token
    assert len(sessions.sessions) == 1
    stored = next(iter(sessions.sessions.values()))
    assert stored.user_id == user.id
    assert stored.revoked_at is None


async def test_login_rejects_wrong_password() -> None:
    use_case, _, _, _, _ = await _build()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginInput(email="user@example.com", password="Wrong@Pass123")
        )


async def test_login_locks_after_five_failures() -> None:
    use_case, users, _, clock, user = await _build()

    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(
                LoginInput(email=user.email, password="Wrong@Pass123")
            )

    stored = users.users[user.id]
    assert stored.failed_login_attempts == 5
    assert stored.locked_until is not None

    with pytest.raises(AccountLockedError):
        await use_case.execute(LoginInput(email=user.email, password=PASSWORD))

    clock.advance(timedelta(minutes=16))
    tokens = await use_case.execute(LoginInput(email=user.email, password=PASSWORD))
    assert tokens.access_token
    assert users.users[user.id].failed_login_attempts == 0
    assert users.users[user.id].locked_until is None


async def test_login_rejects_unknown_email_without_leaking() -> None:
    use_case, _, _, _, _ = await _build()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(LoginInput(email="ghost@example.com", password=PASSWORD))


def test_email_is_normalized() -> None:
    assert Email("User@Example.com").value == "user@example.com"
