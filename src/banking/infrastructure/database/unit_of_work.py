"""Unidade de trabalho transacional sobre AsyncSession."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Coordena commit/rollback de uma unidade de trabalho."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Confirma a transação."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Reverte a transação."""
        await self.session.rollback()

    async def flush(self) -> None:
        """Envia comandos pendentes ao banco sem commitar."""
        await self.session.flush()
