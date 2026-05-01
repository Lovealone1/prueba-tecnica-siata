import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject

from app.infraestructure.models.user import User, GlobalRole
from app.middlewares import require_roles, audit_log
from .dto.schemas import (
    CustomerCreateDTO,
    CustomerUpdateDTO,
    CustomerResponseDTO,
    CustomerListResponseDTO,
)
from .service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])

_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))

@router.get(
    "/",
    response_model=CustomerListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="List customers",
)
@inject
async def list_customers(
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of records")] = 100,
    _current_user: User = _allowed_roles,
    customer_service: CustomerService = Depends(Provide["customer_service"]),
) -> CustomerListResponseDTO:
    return await customer_service.list_customers(skip=skip, limit=limit)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get customer by ID",
)
@inject
async def get_customer(
    customer_id: uuid.UUID,
    _current_user: User = _allowed_roles,
    customer_service: CustomerService = Depends(Provide["customer_service"]),
) -> CustomerResponseDTO:
    return await customer_service.get_customer(customer_id)


@router.post(
    "/",
    response_model=CustomerResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
)
@inject
async def create_customer(
    payload: CustomerCreateDTO,
    _current_user: User = _allowed_roles,
    customer_service: CustomerService = Depends(Provide["customer_service"]),
) -> CustomerResponseDTO:
    return await customer_service.create_customer(payload)


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Partially update a customer",
)
@inject
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdateDTO,
    _audit_user: User = Depends(
        audit_log(
            action="customer.update",
            metadata={"entity": "Customer"},
            capture_body=True,
        )
    ),
    customer_service: CustomerService = Depends(Provide["customer_service"]),
) -> CustomerResponseDTO:
    return await customer_service.update_customer(customer_id, payload)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer",
)
@inject
async def delete_customer(
    customer_id: uuid.UUID,
    _audit_user: User = Depends(
        audit_log(action="customer.delete", metadata={"entity": "Customer"})
    ),
    customer_service: CustomerService = Depends(Provide["customer_service"]),
) -> None:
    await customer_service.delete_customer(customer_id)
