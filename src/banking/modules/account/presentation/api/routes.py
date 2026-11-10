"""Rotas HTTP do módulo de contas."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from banking.api.dependencies import get_current_principal, require_roles
from banking.modules.account.application.dto import AccountOutput, CreateAccountInput
from banking.modules.account.application.use_cases.create_account import (
    CreateAccountUseCase,
)
from banking.modules.account.application.use_cases.get_account import GetAccountUseCase
from banking.modules.account.application.use_cases.get_balance import GetBalanceUseCase
from banking.modules.account.application.use_cases.list_accounts import (
    ListAccountsUseCase,
)
from banking.modules.account.application.use_cases.update_account_status import (
    UpdateAccountStatusUseCase,
)
from banking.modules.account.domain.value_objects import AccountStatus
from banking.modules.account.presentation.api.dependencies import (
    get_balance_use_case,
    get_create_account_use_case,
    get_get_account_use_case,
    get_list_accounts_use_case,
    get_update_status_use_case,
)
from banking.modules.account.presentation.api.schemas import (
    AccountPageResponse,
    AccountResponse,
    BalanceResponse,
    CreateAccountRequest,
    UpdateAccountStatusRequest,
)
from banking.shared.contracts.security import Principal, Role

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _to_response(account: AccountOutput) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        customer_id=account.customer_id,
        account_number=account.account_number,
        account_type=account.account_type,
        status=account.status,
        currency=account.currency,
        balance=f"{account.balance:.2f}",
        created_at=account.created_at,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountResponse,
    summary="Abrir conta",
)
async def create_account(
    payload: CreateAccountRequest,
    principal: Principal = Depends(get_current_principal),
    use_case: CreateAccountUseCase = Depends(get_create_account_use_case),
) -> AccountResponse:
    """Abre uma conta para o cliente autenticado."""
    result = await use_case.execute(
        principal,
        CreateAccountInput(
            account_type=payload.account_type.value,
            currency=payload.currency.value,
        ),
    )
    return _to_response(result)


@router.get(
    "",
    response_model=AccountPageResponse,
    summary="Listar contas",
)
async def list_accounts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: AccountStatus | None = Query(default=None, alias="status"),
    principal: Principal = Depends(get_current_principal),
    use_case: ListAccountsUseCase = Depends(get_list_accounts_use_case),
) -> AccountPageResponse:
    """Lista contas do cliente ou todas para staff."""
    status = status_filter.value if status_filter is not None else None
    result = await use_case.execute(principal, status, page, page_size)
    return AccountPageResponse(
        items=[_to_response(item) for item in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        pages=result.pages,
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Consultar conta",
)
async def get_account(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    use_case: GetAccountUseCase = Depends(get_get_account_use_case),
) -> AccountResponse:
    """Consulta uma conta autorizada."""
    return _to_response(await use_case.execute(principal, account_id))


@router.get(
    "/{account_id}/balance",
    response_model=BalanceResponse,
    summary="Consultar saldo",
)
async def get_balance(
    account_id: UUID,
    principal: Principal = Depends(get_current_principal),
    use_case: GetBalanceUseCase = Depends(get_balance_use_case),
) -> BalanceResponse:
    """Consulta o saldo de uma conta autorizada."""
    result = await use_case.execute(principal, account_id)
    return BalanceResponse(
        account_id=result.account_id,
        balance=f"{result.balance:.2f}",
        currency=result.currency,
        as_of=result.as_of,
    )


@router.patch(
    "/{account_id}/status",
    response_model=AccountResponse,
    summary="Alterar status da conta",
)
async def update_account_status(
    account_id: UUID,
    payload: UpdateAccountStatusRequest,
    _: Principal = Depends(require_roles(Role.BANK_OPERATOR, Role.BANK_ADMIN)),
    use_case: UpdateAccountStatusUseCase = Depends(get_update_status_use_case),
) -> AccountResponse:
    """Ativa, bloqueia ou encerra uma conta."""
    result = await use_case.execute(account_id, payload.status.value)
    return _to_response(result)
