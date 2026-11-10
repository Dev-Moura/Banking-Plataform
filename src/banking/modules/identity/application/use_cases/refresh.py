"""Caso de uso de renovação de tokens com rotação e detecção de reuso."""

from __future__ import annotations

from uuid import uuid4

from banking.modules.identity.application.dto import TokenPair
from banking.modules.identity.application.exceptions import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
)
from banking.modules.identity.application.interfaces import (
    AccessTokenService,
    Clock,
    RefreshSessionRepository,
    UnitOfWorkPort,
    UserRepository,
)
from banking.modules.identity.domain.entities import RefreshSession
from banking.modules.identity.domain.services import RefreshTokenPolicy


class RefreshTokenUseCase:
    """Rotaciona refresh tokens e revoga famílias comprometidas."""

    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: RefreshSessionRepository,
        token_service: AccessTokenService,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
        refresh_expire_days: int,
    ) -> None:
        self._users = user_repository
        self._sessions = session_repository
        self._tokens = token_service
        self._uow = unit_of_work
        self._clock = clock
        self._refresh_expire_days = refresh_expire_days

    async def execute(self, refresh_token: str) -> TokenPair:
        """Executa a rotação do refresh token."""
        now = self._clock.now()
        token_hash = RefreshTokenPolicy.hash(refresh_token)
        session = await self._sessions.get_by_token_hash(token_hash)

        if session is None:
            raise InvalidRefreshTokenError

        if session.is_revoked():
            if session.replaced_by_id is not None:
                await self._sessions.revoke_family(session.family_id, now)
                await self._uow.commit()
                raise RefreshTokenReuseError
            raise InvalidRefreshTokenError

        if session.is_expired(now):
            raise InvalidRefreshTokenError

        user = await self._users.get_by_id(session.user_id)
        if user is None or not user.is_active():
            raise InvalidRefreshTokenError

        new_token = RefreshTokenPolicy.generate()
        new_session = RefreshSession(
            id=uuid4(),
            user_id=user.id,
            token_hash=RefreshTokenPolicy.hash(new_token),
            family_id=session.family_id,
            expires_at=RefreshTokenPolicy.expiry(now, self._refresh_expire_days),
            revoked_at=None,
            replaced_by_id=None,
            created_at=now,
        )

        session.revoked_at = now
        session.replaced_by_id = new_session.id
        await self._sessions.add(new_session)
        await self._sessions.update(session)
        await self._uow.commit()

        access_token, expires_in = self._tokens.create_access_token(
            user.id, user.email, user.role
        )
        return TokenPair(
            access_token=access_token,
            token_type="bearer",  # noqa: S106
            expires_in=expires_in,
            refresh_token=new_token,
            refresh_expires_in=self._refresh_expire_days * 86400,
        )
