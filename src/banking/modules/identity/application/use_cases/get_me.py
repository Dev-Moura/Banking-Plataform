"""Caso de uso de consulta do próprio usuário."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import UnauthorizedError
from banking.modules.identity.application.dto import UserOutput
from banking.modules.identity.application.interfaces import UserRepository


class GetMeUseCase:
    """Retorna os dados públicos do usuário autenticado."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def execute(self, user_id: UUID) -> UserOutput:
        """Consulta o usuário por identificador."""
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active():
            raise UnauthorizedError("Usuário não encontrado ou inativo.")
        return UserOutput(
            id=user.id,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
        )
