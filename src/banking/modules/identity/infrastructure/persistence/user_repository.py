"""Repositório SQLAlchemy de usuários."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from banking.modules.identity.domain.entities import User
from banking.modules.identity.infrastructure.persistence.models import User as UserModel
from banking.shared.contracts.security import Role


def _to_domain(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        role=Role(row.role),
        status=row.status,
        failed_login_attempts=row.failed_login_attempts,
        locked_until=row.locked_until,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyUserRepository:
    """Implementação de UserRepository com SQLAlchemy assíncrono."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Busca usuário por e-mail normalizado."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Busca usuário por identificador."""
        row = await self._session.get(UserModel, user_id)
        return _to_domain(row) if row is not None else None

    async def add(self, user: User) -> None:
        """Persiste um novo usuário."""
        self._session.add(
            UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role.value,
                status=user.status,
                failed_login_attempts=user.failed_login_attempts,
                locked_until=user.locked_until,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )
        await self._session.flush()

    async def update(self, user: User) -> None:
        """Atualiza os campos mutáveis de um usuário."""
        row = await self._session.get(UserModel, user.id)
        if row is None:
            return
        row.email = user.email
        row.password_hash = user.password_hash
        row.role = user.role.value
        row.status = user.status
        row.failed_login_attempts = user.failed_login_attempts
        row.locked_until = user.locked_until
        row.updated_at = user.updated_at
        await self._session.flush()
