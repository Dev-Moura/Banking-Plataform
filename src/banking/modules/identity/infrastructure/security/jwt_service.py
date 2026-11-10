"""Emissão e validação de access tokens JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from banking.core.exceptions import UnauthorizedError
from banking.shared.contracts.security import Principal, Role


class JwtAccessTokenService:
    """Serviço JWT com algoritmo fixo e validação de claims."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        expire_minutes: int,
        issuer: str,
        audience: str,
    ) -> None:
        if algorithm != "HS256":
            msg = "Somente HS256 é permitido para access tokens."
            raise ValueError(msg)
        self._secret = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes
        self._issuer = issuer
        self._audience = audience

    def create_access_token(
        self, user_id: UUID, email: str, role: Role
    ) -> tuple[str, int]:
        """Cria access token e retorna (token, expires_in segundos)."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
            "jti": str(uuid4()),
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, self._expire_minutes * 60

    def decode_access_token(self, token: str) -> Principal:
        """Valida o token e retorna o principal autenticado."""
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={
                    "require": ["exp", "iat", "sub", "iss", "aud"],
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Token inválido ou expirado.") from exc

        if payload.get("type") != "access":
            raise UnauthorizedError("Token inválido.")
        try:
            principal = Principal(
                user_id=UUID(payload["sub"]),
                email=str(payload["email"]),
                role=Role(payload["role"]),
            )
        except (KeyError, ValueError) as exc:
            raise UnauthorizedError("Token inválido.") from exc
        return principal
