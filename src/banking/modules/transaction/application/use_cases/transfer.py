"""Caso de uso de transferência idempotente entre contas."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from banking.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.account.domain.entities import Account
from banking.modules.account.domain.value_objects import AccountStatus
from banking.modules.customer.application.interfaces import CustomerRepository
from banking.modules.identity.application.interfaces import Clock, UnitOfWorkPort
from banking.modules.ledger.application.interfaces import LedgerEntryRepository
from banking.modules.ledger.domain.entities import LedgerEntry
from banking.modules.ledger.domain.value_objects import EntryType
from banking.modules.transaction.application.dto import (
    TransactionOutput,
    TransferInput,
    TransferResult,
)
from banking.modules.transaction.application.interfaces import TransactionRepository
from banking.modules.transaction.domain.entities import Transaction
from banking.modules.transaction.domain.value_objects import TransactionStatus
from banking.shared.contracts.security import Principal
from banking.shared.domain.errors import InvalidMoneyError
from banking.shared.domain.value_objects import MONEY_QUANT, Money


def _request_hash(principal: Principal, data: TransferInput) -> str:
    payload = "|".join(
        (
            str(principal.user_id),
            str(data.source_account_id),
            str(data.destination_account_id),
            f"{data.amount.quantize(MONEY_QUANT):.2f}",
            data.description or "",
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def to_output(transaction: Transaction) -> TransactionOutput:
    """Converte transação em DTO."""
    return TransactionOutput(
        id=transaction.id,
        source_account_id=transaction.source_account_id,
        destination_account_id=transaction.destination_account_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        description=transaction.description,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
    )


class TransferUseCase:
    """Executa transferências com idempotência e bloqueio de contas."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        ledger_repository: LedgerEntryRepository,
        account_repository: AccountRepository,
        customer_repository: CustomerRepository,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._transactions = transaction_repository
        self._ledger = ledger_repository
        self._accounts = account_repository
        self._customers = customer_repository
        self._uow = unit_of_work
        self._clock = clock

    async def execute(
        self, principal: Principal, data: TransferInput
    ) -> TransferResult:
        """Transfere valor entre contas de forma atômica e idempotente."""
        if data.source_account_id == data.destination_account_id:
            raise ValidationError("Conta de origem e destino devem ser distintas.")

        request_hash = _request_hash(principal, data)
        existing = await self._transactions.get_by_idempotency_key(data.idempotency_key)
        if existing is not None:
            return self._replay(principal, existing, request_hash)

        customer = await self._customers.get_by_user_id(principal.user_id)
        if customer is None:
            raise ForbiddenError("Usuário sem cadastro de cliente.")

        locked = await self._accounts.get_many_for_update(
            sorted({data.source_account_id, data.destination_account_id})
        )
        source = locked.get(data.source_account_id)
        destination = locked.get(data.destination_account_id)
        if source is None:
            raise NotFoundError("Conta de origem não encontrada.")
        if destination is None:
            raise NotFoundError("Conta de destino não encontrada.")
        if not source.belongs_to(customer.id):
            raise ForbiddenError("A conta de origem não pertence ao usuário.")

        existing = await self._transactions.get_by_idempotency_key(data.idempotency_key)
        if existing is not None:
            return self._replay(principal, existing, request_hash)

        money = self._validate_transfer(source, destination, data.amount)
        now = self._clock.now()
        source.balance = (source.balance - money.amount).quantize(MONEY_QUANT)
        destination.balance = (destination.balance + money.amount).quantize(MONEY_QUANT)
        source.updated_at = now
        destination.updated_at = now

        transaction = Transaction(
            id=uuid4(),
            source_account_id=source.id,
            destination_account_id=destination.id,
            amount=money.amount,
            currency=source.currency,
            status=TransactionStatus.COMPLETED.value,
            idempotency_key=data.idempotency_key,
            request_hash=request_hash,
            description=data.description,
            created_by_user_id=principal.user_id,
            completed_at=now,
            created_at=now,
            updated_at=now,
        )
        entries = [
            LedgerEntry(
                id=uuid4(),
                transaction_id=transaction.id,
                account_id=source.id,
                entry_type=EntryType.DEBIT.value,
                amount=money.amount,
                balance_after=source.balance,
                currency=source.currency,
                created_at=now,
            ),
            LedgerEntry(
                id=uuid4(),
                transaction_id=transaction.id,
                account_id=destination.id,
                entry_type=EntryType.CREDIT.value,
                amount=money.amount,
                balance_after=destination.balance,
                currency=destination.currency,
                created_at=now,
            ),
        ]

        try:
            await self._transactions.add(transaction)
            await self._ledger.add_many(entries)
            await self._accounts.update_balances([source, destination])
            await self._uow.commit()
        except IntegrityError as exc:
            await self._uow.rollback()
            existing = await self._transactions.get_by_idempotency_key(
                data.idempotency_key
            )
            if existing is not None:
                return self._replay(principal, existing, request_hash)
            raise ConflictError("Não foi possível concluir a transferência.") from exc

        return TransferResult(transaction=to_output(transaction), created=True)

    def _validate_transfer(
        self,
        source: Account,
        destination: Account,
        amount: Decimal,
    ) -> Money:
        if source.status != AccountStatus.ACTIVE.value:
            raise ValidationError("Conta de origem não está ativa.")
        if destination.status != AccountStatus.ACTIVE.value:
            raise ValidationError("Conta de destino não está ativa.")
        if source.currency != destination.currency:
            raise ValidationError("As contas possuem moedas diferentes.")
        try:
            money = Money(amount, source.currency)
        except InvalidMoneyError as exc:
            raise ValidationError("Valor da transferência inválido.") from exc
        if not money.is_positive():
            raise ValidationError("O valor da transferência deve ser positivo.")
        if source.balance < money.amount:
            raise ValidationError("Saldo insuficiente para a transferência.")
        return money

    def _replay(
        self,
        principal: Principal,
        existing: Transaction,
        request_hash: str,
    ) -> TransferResult:
        if (
            existing.created_by_user_id != principal.user_id
            or existing.request_hash != request_hash
        ):
            raise ConflictError(
                "Chave de idempotência reutilizada com dados diferentes."
            )
        return TransferResult(transaction=to_output(existing), created=False)
