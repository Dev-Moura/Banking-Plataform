"""Rotas HTTP do módulo de transações."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status

from banking.api.dependencies import get_current_principal
from banking.modules.transaction.application.dto import (
    TransactionOutput,
    TransferInput,
)
from banking.modules.transaction.application.use_cases.get_transaction import (
    GetTransactionUseCase,
)
from banking.modules.transaction.application.use_cases.list_transactions import (
    ListTransactionsUseCase,
)
from banking.modules.transaction.application.use_cases.transfer import TransferUseCase
from banking.modules.transaction.domain.value_objects import TransactionStatus
from banking.modules.transaction.presentation.api.dependencies import (
    get_list_transactions_use_case,
    get_transaction_use_case,
    get_transfer_use_case,
)
from banking.modules.transaction.presentation.api.schemas import (
    TransactionPageResponse,
    TransactionResponse,
    TransferRequest,
)
from banking.shared.contracts.security import Principal

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _to_response(transaction: TransactionOutput) -> TransactionResponse:
    return TransactionResponse(
        id=transaction.id,
        source_account_id=transaction.source_account_id,
        destination_account_id=transaction.destination_account_id,
        amount=f"{transaction.amount:.2f}",
        currency=transaction.currency,
        status=transaction.status,
        description=transaction.description,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
    )


@router.post(
    "/transfers",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionResponse,
    summary="Transferir entre contas",
)
async def transfer(
    payload: TransferRequest,
    response: Response,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=128),
    ],
    principal: Principal = Depends(get_current_principal),
    use_case: TransferUseCase = Depends(get_transfer_use_case),
) -> TransactionResponse:
    """Executa transferência idempotente entre contas."""
    result = await use_case.execute(
        principal,
        TransferInput(
            source_account_id=payload.source_account_id,
            destination_account_id=payload.destination_account_id,
            amount=payload.amount,
            idempotency_key=idempotency_key,
            description=payload.description,
        ),
    )
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return _to_response(result.transaction)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Consultar transação",
)
async def get_transaction(
    transaction_id: UUID,
    principal: Principal = Depends(get_current_principal),
    use_case: GetTransactionUseCase = Depends(get_transaction_use_case),
) -> TransactionResponse:
    """Consulta uma transação autorizada."""
    return _to_response(await use_case.execute(principal, transaction_id))


@router.get(
    "",
    response_model=TransactionPageResponse,
    summary="Listar transações",
)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: TransactionStatus | None = Query(default=None, alias="status"),
    account_id: UUID | None = Query(default=None),
    principal: Principal = Depends(get_current_principal),
    use_case: ListTransactionsUseCase = Depends(get_list_transactions_use_case),
) -> TransactionPageResponse:
    """Lista transações do cliente ou todas para staff."""
    status = status_filter.value if status_filter is not None else None
    result = await use_case.execute(principal, status, account_id, page, page_size)
    return TransactionPageResponse(
        items=[_to_response(item) for item in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        pages=result.pages,
    )
