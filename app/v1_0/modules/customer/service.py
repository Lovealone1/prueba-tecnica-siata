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
        """
        Initializes the service with the customer repository.

        Args:
            customer_repository: Data access layer for customer entities.
        """
        self.repo = customer_repository

    async def list_customers(self, skip: int = 0, limit: int = 100) -> CustomerListResponseDTO:
        """
        Retrieves a paginated list of customers from the system.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            CustomerListResponseDTO containing the list of customers and total count.
        """
        customers = await self.repo.get_all(skip=skip, limit=limit)
        total = await self.repo.count_all()
        return CustomerListResponseDTO(
            data=[CustomerResponseDTO.model_validate(c) for c in customers],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_customer(self, customer_id: uuid.UUID) -> CustomerResponseDTO:
        """
        Retrieves a specific customer by its unique identifier.

        Args:
            customer_id: The unique identifier of the customer.

        Returns:
            CustomerResponseDTO containing the customer details.

        Raises:
            HTTPException: 404 if the customer is not found.
        """
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )
        return CustomerResponseDTO.model_validate(customer)

    async def create_customer(self, payload: CustomerCreateDTO) -> CustomerResponseDTO:
        """
        Registers a new customer in the system.

        Workflow:
        1. Validates that the unique identifier (e.g., tax ID) is not already registered.
        2. Validates that the provided email address is unique.
        3. Persists the new customer entity and logs the creation event.

        Args:
            payload: Data transfer object containing the new customer's details.

        Returns:
            CustomerResponseDTO with the created customer data.

        Raises:
            HTTPException: 409 if the identifier or email already exists.
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
        Updates an existing customer's contact and location details.

        Workflow:
        1. Retrieves the customer and verifies its existence.
        2. Captures the current state of modified fields for audit logging.
        3. If email is updated, ensures the new address is not taken by another customer.
        4. Applies the updates and persists the entity.
        5. Calculates the state diff and stores it in the global audit context for middleware.

        Args:
            customer_id: The unique identifier of the customer to update.
            payload: Data transfer object with the fields to update.

        Returns:
            CustomerResponseDTO with the updated customer details.

        Raises:
            HTTPException:
                - 404: If the customer is not found.
                - 409: If the new email address is already in use.
        """
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

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
        """
        Permanently removes a customer from the system.

        Workflow:
        1. Retrieves the customer and verifies it exists.
        2. Invokes the repository to delete the record.

        Args:
            customer_id: The unique identifier of the customer to delete.

        Raises:
            HTTPException: 404 if the customer is not found.
        """
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found",
            )
        await self.repo.delete(customer)
