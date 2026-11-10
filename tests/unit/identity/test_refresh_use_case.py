"""Testes de rotação e detecção de reuso de refresh token."""

from __future__ import annotations

from uuid import uuid4

import pytest

from banking.modules.identity.application.exceptions import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
)
from banking.modules.identity.application.use_cases.refresh import RefreshTokenUseCase
from banking.modules.identity.domain.entities import RefreshSession, User
from banking.modules.identity.domain.services import RefreshTokenPolicy
from banking.shared.contracts.security import Role
from tests.unit.identity.fakes import (
    FakeClock,
    FakeRefreshSessionRepository,
    FakeTokenService,
    FakeUnitOfWork,
    FakeUserRepository,
)

pytestmark = pytest.mark.unit


async def _build() -> tuple[
    RefreshTokenUseCase,
    FakeRefreshSessionRepository,
    str,
    User,
]:
    clock = FakeClock()
    users = FakeUserRepository()
    sessions = FakeRefreshSessionRepository()
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash="hashed::x",
        role=Role.CUSTOMER,
        status="ACTIVE",
        failed_login_attempts=0,
        locked_until=None,
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    await users.add(user)
    token = RefreshTokenPolicy.generate()
    await sessions.add(
        RefreshSession(
            id=uuid4(),
            user_id=user.id,
            token_hash=RefreshTokenPolicy.hash(token),
            family_id=uuid4(),
            expires_at=RefreshTokenPolicy.expiry(clock.now(), 7),
            revoked_at=None,
            replaced_by_id=None,
            created_at=clock.now(),
        )
    )
    use_case = RefreshTokenUseCase(
        user_repository=users,
        session_repository=sessions,
        token_service=FakeTokenService(),
        unit_of_work=FakeUnitOfWork(),
        clock=clock,
        refresh_expire_days=7,
    )
    return use_case, sessions, token, user


async def test_rotation_revokes_old_and_issues_new() -> None:
    use_case, sessions, token, user = await _build()

    tokens = await use_case.execute(token)

    assert tokens.refresh_token != token
    old = sessions.sessions[RefreshTokenPolicy.hash(token)]
    new = sessions.sessions[RefreshTokenPolicy.hash(tokens.refresh_token)]
    assert old.revoked_at is not None
    assert old.replaced_by_id == new.id
    assert new.family_id == old.family_id
    assert new.user_id == user.id


async def test_reuse_revokes_entire_family() -> None:
    use_case, sessions, token, _ = await _build()
    tokens = await use_case.execute(token)

    with pytest.raises(RefreshTokenReuseError):
        await use_case.execute(token)

    family_id = next(iter(sessions.sessions.values())).family_id
    family = [s for s in sessions.sessions.values() if s.family_id == family_id]
    assert all(s.revoked_at is not None for s in family)
    assert tokens.refresh_token


async def test_unknown_token_is_rejected() -> None:
    use_case, _, _, _ = await _build()

    with pytest.raises(InvalidRefreshTokenError):
        await use_case.execute("token-that-does-not-exist")
