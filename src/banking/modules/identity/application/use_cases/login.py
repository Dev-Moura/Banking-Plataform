"""Caso de uso de autenticação."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from banking.modules.identity.application.dto import LoginInput, TokenPair
from banking.modules.identity.application.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
)
from banking.modules.identity.application.interfaces import (
    AccessTokenService,
    Clock,
    PasswordHasher,
    RefreshSessionRepository,
    UnitOfWorkPort,
    UserRepository,
)
from banking.modules.identity.domain.entities import RefreshSession
from banking.modules.identity.domain.services import RefreshTokenPolicy
from banking.modules.identity.domain.value_objects import Email

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15
DUMMY_PASSWORD = "dummy-password-for-timing"  # noqa: S105


class LoginUseCase:
    """Autentica credenciais e emite par de tokens."""

    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: RefreshSessionRepository,
        password_hasher: PasswordHasher,
        token_service: AccessTokenService,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
        refresh_expire_days: int,
    ) -> None:
        self._users = user_repository
        self._sessions = session_repository
        self._hasher = password_hasher
        self._tokens = token_service
        self._uow = unit_of_work
        self._clock = clock
        self._refresh_expire_days = refresh_expire_days

    async def execute(self, data: LoginInput) -> TokenPair:
        """Executa o login com proteção contra brute force."""
        email = Email(data.email).value
        now = self._clock.now()

        user = await self._users.get_by_email(email)
        if user is None:
            self._hasher.verify(self._hasher.hash(DUMMY_PASSWORD), data.password)
            raise InvalidCredentialsError

        if user.is_locked(now):
            raise AccountLockedError

        if not self._hasher.verify(user.password_hash, data.password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCK_DURATION_MINUTES)
            user.updated_at = now
            await self._users.update(user)
            await self._uow.commit()
            raise InvalidCredentialsError

        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = now
        if self._hasher.needs_rehash(user.password_hash):
            user.password_hash = self._hasher.hash(data.password)
        await self._users.update(user)

        refresh_token = RefreshTokenPolicy.generate()
        session = RefreshSession(
            id=uuid4(),
            user_id=user.id,
            token_hash=RefreshTokenPolicy.hash(refresh_token),
            family_id=uuid4(),
            expires_at=RefreshTokenPolicy.expiry(now, self._refresh_expire_days),
            revoked_at=None,
            replaced_by_id=None,
            created_at=now,
        )
        await self._sessions.add(session)
        await self._uow.commit()

        access_token, expires_in = self._tokens.create_access_token(
            user.id, user.email, user.role
        )
        return TokenPair(
            access_token=access_token,
            token_type="bearer",  # noqa: S106
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=self._refresh_expire_days * 86400,
        )
