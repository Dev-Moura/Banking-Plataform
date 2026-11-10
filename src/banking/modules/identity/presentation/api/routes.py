"""Rotas HTTP do módulo de identidade."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from banking.core.problem_details import problem_response
from banking.modules.identity.application.dto import LoginInput, RegisterInput
from banking.modules.identity.application.use_cases.get_me import GetMeUseCase
from banking.modules.identity.application.use_cases.login import LoginUseCase
from banking.modules.identity.application.use_cases.logout import LogoutUseCase
from banking.modules.identity.application.use_cases.refresh import RefreshTokenUseCase
from banking.modules.identity.application.use_cases.register import RegisterUserUseCase
from banking.modules.identity.infrastructure.security.rate_limiter import (
    RedisRateLimiterAdapter,
)
from banking.modules.identity.presentation.api.dependencies import (
    get_current_principal,
    get_login_use_case,
    get_logout_use_case,
    get_me_use_case,
    get_refresh_use_case,
    get_register_use_case,
)
from banking.modules.identity.presentation.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from banking.shared.contracts.security import Principal

router = APIRouter(prefix="/identity", tags=["identity"])

_rate_limiter = RedisRateLimiterAdapter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


async def _enforce(
    request: Request,
    key: str,
    limit: int,
    window: int = 60,
) -> JSONResponse | None:
    allowed = await _rate_limiter.allow(key, limit, window)
    if allowed:
        return None
    return problem_response(
        request,
        status=429,
        title="Too Many Requests",
        type_uri="https://moura-banking.local/problems/rate-limit-exceeded",
        detail="Limite de requisições excedido. Tente novamente mais tarde.",
        headers={"Retry-After": str(window)},
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Cadastrar usuário",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> UserResponse | JSONResponse:
    """Cadastra um novo usuário."""
    limited = await _enforce(request, f"register:{_client_ip(request)}", 10)
    if limited is not None:
        return limited
    result = await use_case.execute(
        RegisterInput(email=str(payload.email), password=payload.password)
    )
    return UserResponse(
        id=result.id,
        email=result.email,
        role=result.role,
        status=result.status,
        created_at=result.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário",
)
async def login(
    payload: LoginRequest,
    request: Request,
    use_case: LoginUseCase = Depends(get_login_use_case),
) -> TokenResponse | JSONResponse:
    """Autentica credenciais e emite tokens."""
    ip = _client_ip(request)
    limited = await _enforce(request, f"login:{ip}:{payload.email.lower()}", 5)
    if limited is None:
        limited = await _enforce(request, f"login-ip:{ip}", 20)
    if limited is not None:
        return limited
    tokens = await use_case.execute(
        LoginInput(email=str(payload.email), password=payload.password)
    )
    return TokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens",
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    use_case: RefreshTokenUseCase = Depends(get_refresh_use_case),
) -> TokenResponse | JSONResponse:
    """Rotaciona o refresh token e emite novo par."""
    limited = await _enforce(request, f"refresh:{_client_ip(request)}", 30)
    if limited is not None:
        return limited
    tokens = await use_case.execute(payload.refresh_token)
    return TokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar sessão",
)
async def logout(
    payload: RefreshRequest,
    _: Principal = Depends(get_current_principal),
    use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> Response:
    """Revoga o refresh token informado."""
    await use_case.execute(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuário autenticado",
)
async def me(
    principal: Principal = Depends(get_current_principal),
    use_case: GetMeUseCase = Depends(get_me_use_case),
) -> UserResponse:
    """Retorna o usuário autenticado."""
    result = await use_case.execute(principal.user_id)
    return UserResponse(
        id=result.id,
        email=result.email,
        role=result.role,
        status=result.status,
        created_at=result.created_at,
    )
