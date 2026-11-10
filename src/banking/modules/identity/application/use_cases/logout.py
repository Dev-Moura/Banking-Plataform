"""Caso de uso de encerramento de sessão."""

from __future__ import annotations

from banking.modules.identity.application.exceptions import InvalidRefreshTokenError
from banking.modules.identity.application.interfaces import (
    Clock,
    RefreshSessionRepository,
    UnitOfWorkPort,
)
from banking.modules.identity.domain.services import RefreshTokenPolicy


class LogoutUseCase:
    """Revoga o refresh token informado."""

    def __init__(
        self,
        session_repository: RefreshSessionRepository,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._sessions = session_repository
        self._uow = unit_of_work
        self._clock = clock

    async def execute(self, refresh_token: str) -> None:
        """Revoga a sessão; tokens desconhecidos são rejeitados."""
        token_hash = RefreshTokenPolicy.hash(refresh_token)
        session = await self._sessions.get_by_token_hash(token_hash)
        if session is None:
            raise InvalidRefreshTokenError
        if not session.is_revoked():
            session.revoked_at = self._clock.now()
            await self._sessions.update(session)
            await self._uow.commit()
