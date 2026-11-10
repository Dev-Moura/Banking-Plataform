"""Rotas HTTP do módulo de ledger."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from banking.api.dependencies import get_current_principal
from banking.modules.ledger.application.dto import LedgerEntryOutput
from banking.modules.ledger.application.use_cases.get_account_statement import (
    GetAccountStatementUseCase,
)
from banking.modules.ledger.application.use_cases.get_transaction_ledger import (
    GetTransactionLedgerUseCase,
)
from banking.modules.ledger.domain.value_objects import EntryType
from banking.modules.ledger.presentation.api.dependencies import (
    get_account_statement_use_case,
    get_transaction_ledger_use_case,
)
from banking.modules.ledger.presentation.api.schemas import (
    LedgerEntryPageResponse,
    LedgerEntryResponse,
    TransactionLedgerResponse,
)
from banking.shared.contracts.security import Principal

router = APIRouter(prefix="/ledger", tags=["ledger"])
statement_router = APIRouter(prefix="/accounts", tags=["accounts"])


def _to_response(entry: LedgerEntryOutput) -> LedgerEntryResponse:
    return LedgerEntryResponse(
        id=entry.id,
        transaction_id=entry.transaction_id,
        account_id=entry.account_id,
        entry_type=entry.entry_type,
        amount=f"{entry.amount:.2f}",
        balance_after=f"{entry.balance_after:.2f}",
        currency=entry.currency,
        created_at=entry.created_at,
    )


async def _account_statement(
    account_id: UUID,
    page: int,
    page_size: int,
    principal: Principal,
    use_case: GetAccountStatementUseCase,
) -> LedgerEntryPageResponse:
    result = await use_case.execute(principal, account_id, page, page_size)
    return LedgerEntryPageResponse(
        items=[_to_response(item) for item in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        pages=result.pages,
    )


@router.get(
    "/accounts/{account_id}",
    response_model=LedgerEntryPageResponse,
    summary="Listar lançamentos da conta",
)
async def list_account_entries(
    account_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    use_case: GetAccountStatementUseCase = Depends(get_account_statement_use_case),
) -> LedgerEntryPageResponse:
    """Lista o ledger de uma conta autorizada."""
    return await _account_statement(account_id, page, page_size, principal, use_case)


@statement_router.get(
    "/{account_id}/statement",
    response_model=LedgerEntryPageResponse,
    summary="Consultar extrato da conta",
)
async def get_account_statement(
    account_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_current_principal),
    use_case: GetAccountStatementUseCase = Depends(get_account_statement_use_case),
) -> LedgerEntryPageResponse:
    """Retorna o extrato contábil paginado da conta."""
    return await _account_statement(account_id, page, page_size, principal, use_case)


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionLedgerResponse,
    summary="Listar lançamentos da transação",
)
async def list_transaction_entries(
    transaction_id: UUID,
    principal: Principal = Depends(get_current_principal),
    use_case: GetTransactionLedgerUseCase = Depends(get_transaction_ledger_use_case),
) -> TransactionLedgerResponse:
    """Lista os lançamentos de uma transação autorizada."""
    entries = await use_case.execute(principal, transaction_id)
    debit = sum(
        (entry.amount for entry in entries if entry.entry_type == EntryType.DEBIT),
        Decimal("0.00"),
    )
    credit = sum(
        (entry.amount for entry in entries if entry.entry_type == EntryType.CREDIT),
        Decimal("0.00"),
    )
    return TransactionLedgerResponse(
        transaction_id=transaction_id,
        entries=[_to_response(entry) for entry in entries],
        balanced=debit == credit,
    )
