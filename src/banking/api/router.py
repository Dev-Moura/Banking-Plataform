"""Roteador agregador da API versionada."""

from __future__ import annotations

from fastapi import APIRouter

from banking.api.health import router as health_router
from banking.api.versioning import API_V1_PREFIX

api_router = APIRouter()
api_router.include_router(health_router)


def include_module_routers() -> None:
    """Inclui os roteadores dos módulos de domínio sob /api/v1.

    Importações locais evitam ciclos de importação durante o bootstrap.
    """
    from banking.modules.account.presentation.api.routes import router as accounts
    from banking.modules.audit.presentation.api.routes import router as audit
    from banking.modules.customer.presentation.api.routes import router as customers
    from banking.modules.identity.presentation.api.routes import router as identity
    from banking.modules.ledger.presentation.api.routes import router as ledger
    from banking.modules.transaction.presentation.api.routes import (
        router as transactions,
    )

    for module_router in (
        identity,
        customers,
        accounts,
        transactions,
        ledger,
        audit,
    ):
        api_router.include_router(module_router, prefix=API_V1_PREFIX)


include_module_routers()
