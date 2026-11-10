"""Caso de uso de alteração de status de conta."""

from __future__ import annotations

from uuid import UUID

from banking.core.exceptions import BadRequestError, NotFoundError
from banking.modules.account.application.dto import AccountOutput
from banking.modules.account.application.interfaces import AccountRepository
from banking.modules.account.application.use_cases.list_accounts import to_output
from banking.modules.account.domain.value_objects import AccountStatus
from banking.modules.identity.application.interfaces import Clock, UnitOfWorkPort


class UpdateAccountStatusUseCase:
    """Ativa, bloqueia ou encerra uma conta (operação administrativa)."""

    def __init__(
        self,
        account_repository: AccountRepository,
        unit_of_work: UnitOfWorkPort,
        clock: Clock,
    ) -> None:
        self._accounts = account_repository
        self._uow = unit_of_work
        self._clock = clock

    async def execute(self, account_id: UUID, new_status: str) -> AccountOutput:
        """Altera o status validando o valor informado."""
        try:
            status = AccountStatus(new_status)
        except ValueError as exc:
            raise BadRequestError("Status de conta inválido.") from exc

        account = await self._accounts.get_by_id(account_id)
        if account is None:
            raise NotFoundError("Conta não encontrada.")
        if account.is_system:
            raise BadRequestError("Contas sistêmicas não podem ser alteradas.")

        account.status = status.value
        account.updated_at = self._clock.now()
        await self._accounts.update_status(account)
        await self._uow.commit()
        return to_output(account)
