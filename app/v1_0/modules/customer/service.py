import uuid
from typing import Optional

from fastapi import HTTPException, status

from app.core.logger import logger
from app.infraestructure.models.customer import Customer
from .domain import ICustomerRepository
from app.core.context import audit_context
from .dto.schemas import CustomerCreateDTO, CustomerUpdateDTO, CustomerListResponseDTO, CustomerResponseDTO


class CustomerService:
    """
    Domain service for Customer.

    Business rules:
    - The `identifier` must be unique in the system.
    - The `email` must be unique in the system.
    - The `identifier` cannot be updated once created (immutable field).
    """

    def __init__(self, customer_repository: ICustomerRepository) -> None:
        self.repo = customer_repository

    async def list_customers(self, skip: int = 0, limit: int = 100) -> CustomerListResponseDTO:
        """Returns a paginated list of customers."""
        customers = await self.repo.get_all(skip=skip, limit=limit)
        total = await self.repo.count_all()
        return CustomerListResponseDTO(
            data=[CustomerResponseDTO.model_validate(c) for c in customers],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_customer(self, customer_id: uuid.UUID) -> CustomerResponseDTO:
        """Retrieves a customer by its UUID. Raises 404 if it does not exist."""
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )
        return CustomerResponseDTO.model_validate(customer)

    async def create_customer(self, payload: CustomerCreateDTO) -> CustomerResponseDTO:
        """
        Creates a new customer.

        Validations:
        - unique identifier
        - unique email
        """
        if await self.repo.get_by_identifier(payload.identifier):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A customer with identifier '{payload.identifier}' already exists",
            )
        if await self.repo.get_by_email(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A customer with email '{payload.email}' already exists",
            )

        customer = Customer(
            name=payload.name,
            identifier=payload.identifier,
            email=str(payload.email),
            phone=payload.phone,
            address=payload.address,
        )
        created = await self.repo.create(customer)
        logger.info(f"[CUSTOMER] Created customer id={created.id} identifier={created.identifier}")
        return CustomerResponseDTO.model_validate(created)

    async def update_customer(
        self,
        customer_id: uuid.UUID,
        payload: CustomerUpdateDTO,
    ) -> CustomerResponseDTO:
        """
        Partially updates a customer (PATCH).

        - The `identifier` is immutable and cannot be modified here.
        - Validates email uniqueness if attempting to change it.
        """
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # 1. Capture 'before' state for auditing
        before_state = {field: getattr(customer, field) for field in update_data}

        if "email" in update_data:
            new_email = str(update_data["email"])
            existing = await self.repo.get_by_email(new_email)
            if existing and existing.id != customer_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{new_email}' is already in use by another customer",
                )
            update_data["email"] = new_email

        for field, value in update_data.items():
            setattr(customer, field, value)

        updated = await self.repo.update(customer)

        # 2. Compare with 'after' state and save diff in context
        diff = {}
        for field, old_val in before_state.items():
            new_val = getattr(updated, field)
            if old_val != new_val:
                diff[field] = {"old": old_val, "new": new_val}

        if diff:
            ctx = audit_context.get().copy()
            ctx["diff"] = diff
            audit_context.set(ctx)

        return CustomerResponseDTO.model_validate(updated)

    async def delete_customer(self, customer_id: uuid.UUID) -> None:
        """Deletes a customer. Raises 404 if it does not exist."""
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )
        await self.repo.delete(customer)
