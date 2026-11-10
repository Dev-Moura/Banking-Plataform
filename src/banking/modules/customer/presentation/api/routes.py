"""Rotas HTTP do módulo de clientes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from banking.api.dependencies import get_current_principal
from banking.modules.customer.application.dto import (
    CreateCustomerInput,
    CustomerOutput,
    UpdateCustomerInput,
)
from banking.modules.customer.application.use_cases.create_customer import (
    CreateCustomerUseCase,
)
from banking.modules.customer.application.use_cases.get_customer import (
    GetCustomerUseCase,
    GetMyCustomerUseCase,
)
from banking.modules.customer.application.use_cases.update_customer import (
    UpdateCustomerUseCase,
)
from banking.modules.customer.presentation.api.dependencies import (
    get_create_customer_use_case,
    get_customer_use_case,
    get_my_customer_use_case,
    get_update_customer_use_case,
)
from banking.modules.customer.presentation.api.schemas import (
    CreateCustomerRequest,
    CustomerResponse,
    UpdateCustomerRequest,
)
from banking.shared.contracts.security import Principal

router = APIRouter(prefix="/customers", tags=["customers"])


def _to_response(customer: CustomerOutput) -> CustomerResponse:
    return CustomerResponse(
        id=customer.id,
        user_id=customer.user_id,
        full_name=customer.full_name,
        document_reference=customer.document_reference,
        birth_date=customer.birth_date,
        status=customer.status,
        created_at=customer.created_at,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CustomerResponse,
    summary="Cadastrar cliente",
)
async def create_customer(
    payload: CreateCustomerRequest,
    principal: Principal = Depends(get_current_principal),
    use_case: CreateCustomerUseCase = Depends(get_create_customer_use_case),
) -> CustomerResponse:
    """Cria o cliente vinculado ao usuário autenticado."""
    result = await use_case.execute(
        principal,
        CreateCustomerInput(
            full_name=payload.full_name,
            document_reference=payload.document_reference,
            birth_date=payload.birth_date,
        ),
    )
    return _to_response(result)


@router.get(
    "/me",
    response_model=CustomerResponse,
    summary="Consultar meu cadastro",
)
async def get_my_customer(
    principal: Principal = Depends(get_current_principal),
    use_case: GetMyCustomerUseCase = Depends(get_my_customer_use_case),
) -> CustomerResponse:
    """Retorna o cliente do usuário autenticado."""
    return _to_response(await use_case.execute(principal))


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Consultar cliente por id",
)
async def get_customer(
    customer_id: UUID,
    principal: Principal = Depends(get_current_principal),
    use_case: GetCustomerUseCase = Depends(get_customer_use_case),
) -> CustomerResponse:
    """Consulta cliente com verificação de propriedade/RBAC."""
    return _to_response(await use_case.execute(principal, customer_id))


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Atualizar cliente",
)
async def update_customer(
    customer_id: UUID,
    payload: UpdateCustomerRequest,
    principal: Principal = Depends(get_current_principal),
    use_case: UpdateCustomerUseCase = Depends(get_update_customer_use_case),
) -> CustomerResponse:
    """Atualiza dados cadastrais do cliente."""
    result = await use_case.execute(
        principal,
        customer_id,
        UpdateCustomerInput(
            full_name=payload.full_name,
            birth_date=payload.birth_date,
        ),
    )
    return _to_response(result)
