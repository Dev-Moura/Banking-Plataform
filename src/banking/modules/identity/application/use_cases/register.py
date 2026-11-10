"""Caso de uso de cadastro de usuário."""

from __future__ import annotations

from uuid import uuid4

from banking.modules.identity.application.dto import RegisterInput, UserOutput
from banking.modules.identity.application.exceptions import EmailAlreadyExistsError
from banking.modules.identity.application.interfaces import (
    Clock,
    PasswordHasher,
    UnitOfWorkPort,
    UserRepository,
)
from banking.modules.identity.domain.entities import User
from banking.modules.identity.domain.services import PasswordPolicy
from banking.modules.identity.domain.value_objects import Email
from banking.shared.contracts.security import Role


class RegisterUserUseCase:
    """Cadastra um novo usuário com senha protegida por Argon2id."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._users = user_repository
        self._hasher = password_hasher
        self._uow = unit_of_work
        self._clock = clock

    async def execute(self, data: RegisterInput) -> UserOutput:
        """Executa o cadastro."""
        email = Email(data.email).value
        PasswordPolicy.validate(data.password)

        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyExistsError

        now = self._clock.now()
        user = User(
            id=uuid4(),
            email=email,
            password_hash=self._hasher.hash(data.password),
            role=Role.CUSTOMER,
            status="ACTIVE",
            failed_login_attempts=0,
            locked_until=None,
            created_at=now,
            updated_at=now,
        )
        await self._users.add(user)
        await self._uow.commit()

        return UserOutput(
            id=user.id,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
        )
