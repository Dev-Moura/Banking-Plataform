"""Contratos de dependências reutilizáveis por todos os módulos."""

from __future__ import annotations

from banking.modules.identity.presentation.api.dependencies import (
    get_current_principal,
    require_roles,
)

__all__ = ["get_current_principal", "require_roles"]
