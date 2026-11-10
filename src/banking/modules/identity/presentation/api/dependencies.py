"""Dependências HTTP do módulo de identidade."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from banking.core.config import get_settings
from banking.core.exceptions import ForbiddenError, UnauthorizedError
from banking.infrastructure.database.session import get_session
from banking.infrastructure.database.unit_of_work import UnitOfWork
from banking.modules.identity.application.use_cases.get_me import GetMeUseCase
from banking.modules.identity.application.use_cases.login import LoginUseCase
from banking.modules.identity.application.use_cases.logout import LogoutUseCase
from banking.modules.identity.application.use_cases.refresh import RefreshTokenUseCase
from banking.modules.identity.application.use_cases.register import RegisterUserUseCase
from banking.modules.identity.infrastructure.persistence.session_repository import (
    SqlAlchemyRefreshSessionRepository,
)
from banking.modules.identity.infrastructure.persistence.user_repository import (
    SqlAlchemyUserRepository,
)
from banking.modules.identity.infrastructure.security.argon2_hasher import (
    Argon2PasswordHasher,
)
from banking.modules.identity.infrastructure.security.clock import SystemClock
from banking.modules.identity.infrastructure.security.jwt_service import (
    JwtAccessTokenService,
)
from banking.shared.contracts.security import Principal, Role

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_password_hasher() -> Argon2PasswordHasher:
    """Hasher Argon2id singleton."""
    return Argon2PasswordHasher()


@lru_cache
def get_token_service() -> JwtAccessTokenService:
    """Serviço JWT singleton configurado por ambiente."""
    settings = get_settings()
    return JwtAccessTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )


def get_clock() -> SystemClock:
    """Relógio do sistema."""
    return SystemClock()


def get_register_use_case(
    session: AsyncSession = Depends(get_session),
) -> RegisterUserUseCase:
    """Monta o caso de uso de cadastro."""
    return RegisterUserUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        password_hasher=get_password_hasher(),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )


def get_login_use_case(
    session: AsyncSession = Depends(get_session),
) -> LoginUseCase:
    """Monta o caso de uso de login."""
    settings = get_settings()
    return LoginUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        session_repository=SqlAlchemyRefreshSessionRepository(session),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
        refresh_expire_days=settings.refresh_token_expire_days,
    )


def get_refresh_use_case(
    session: AsyncSession = Depends(get_session),
) -> RefreshTokenUseCase:
    """Monta o caso de uso de refresh."""
    settings = get_settings()
    return RefreshTokenUseCase(
        user_repository=SqlAlchemyUserRepository(session),
        session_repository=SqlAlchemyRefreshSessionRepository(session),
        token_service=get_token_service(),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
        refresh_expire_days=settings.refresh_token_expire_days,
    )


def get_logout_use_case(
    session: AsyncSession = Depends(get_session),
) -> LogoutUseCase:
    """Monta o caso de uso de logout."""
    return LogoutUseCase(
        session_repository=SqlAlchemyRefreshSessionRepository(session),
        unit_of_work=UnitOfWork(session),
        clock=get_clock(),
    )


def get_me_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetMeUseCase:
    """Monta o caso de uso de consulta do usuário autenticado."""
    return GetMeUseCase(user_repository=SqlAlchemyUserRepository(session))


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    """Valida o Bearer token e retorna o principal autenticado."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Autenticação necessária.")
    return get_token_service().decode_access_token(credentials.credentials)


def require_roles(*roles: Role) -> Callable[..., Principal]:
    """Cria dependência que exige um dos papéis informados."""

    async def _dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if principal.role not in roles:
            raise ForbiddenError("Acesso negado para este recurso.")
        return principal

    return _dependency
