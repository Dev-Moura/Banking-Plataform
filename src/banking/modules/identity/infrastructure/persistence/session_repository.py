"""Repositório SQLAlchemy de sessões de refresh."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.identity.domain.entities import RefreshSession
from banking.modules.identity.infrastructure.persistence.models import (
    RefreshSession as RefreshSessionModel,
)


def _to_domain(row: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        family_id=row.family_id,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        replaced_by_id=row.replaced_by_id,
        created_at=row.created_at,
    )


class SqlAlchemyRefreshSessionRepository:
    """Implementação de RefreshSessionRepository com SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session: RefreshSession) -> None:
        """Persiste uma nova sessão de refresh."""
        self._session.add(
            RefreshSessionModel(
                id=session.id,
                user_id=session.user_id,
                token_hash=session.token_hash,
                family_id=session.family_id,
                expires_at=session.expires_at,
                revoked_at=session.revoked_at,
                replaced_by_id=session.replaced_by_id,
                created_at=session.created_at,
            )
        )
        await self._session.flush()

    async def get_by_token_hash(self, token_hash: str) -> RefreshSession | None:
        """Busca sessão pelo hash do token."""
        result = await self._session.execute(
            select(RefreshSessionModel).where(
                RefreshSessionModel.token_hash == token_hash
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def update(self, session: RefreshSession) -> None:
        """Atualiza revogação e substituição de uma sessão."""
        row = await self._session.get(RefreshSessionModel, session.id)
        if row is None:
            return
        row.revoked_at = session.revoked_at
        row.replaced_by_id = session.replaced_by_id
        await self._session.flush()

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        """Revoga todas as sessões ativas de uma família."""
        await self._session.execute(
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.family_id == family_id,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self._session.flush()
