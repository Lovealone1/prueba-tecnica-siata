import uuid
from typing import Optional, List

from fastapi import HTTPException, status

from app.core.logger import logger
from app.core.context import audit_context
from app.infraestructure.models.product import Product, TransportMode, ProductSize
from .domain import IProductRepository
from .dto.schemas import (
    ProductCreateDTO,
    ProductUpdateDTO,
    ProductListResponseDTO,
    ProductResponseDTO,
)


class ProductService:
    """
    Domain service for Product.

    Business rules:
    - The `name` must be unique in the system; duplicates are rejected with 409.
    - All mutation side-effects (audit diff) are stored in `audit_context` so the
      middleware can persist them without coupling the service to the HTTP layer.
    """

    def __init__(self, product_repository: IProductRepository) -> None:
        """
        Initializes the service with the product repository.

        Args:
            product_repository: Data access layer for product entities.
        """
        self.repo = product_repository

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> ProductListResponseDTO:
        """
        Retrieves a paginated and filtered list of products.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            transport_mode: Optional filter by transport mode (LAND, MARITIME).
            size: Optional filter by product size.

        Returns:
            ProductListResponseDTO containing the list of products and the total count.
        """
        products = await self.repo.get_all(
            skip=skip, limit=limit, transport_mode=transport_mode, size=size
        )
        total = await self.repo.count_all(transport_mode=transport_mode, size=size)
        return ProductListResponseDTO(
            data=[ProductResponseDTO.model_validate(p) for p in products],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_product(self, product_id: uuid.UUID) -> ProductResponseDTO:
        """
        Retrieves a specific product by its unique identifier.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductResponseDTO containing the product details.

        Raises:
            HTTPException: 404 if the product is not found.
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )
        return ProductResponseDTO.model_validate(product)

    async def create_product(self, payload: ProductCreateDTO) -> ProductResponseDTO:
        """
        Creates a new product in the system.

        Workflow:
        1. Validates that the product name is globally unique.
        2. Initializes a new Product entity with the provided data.
        3. Persists the product and logs the creation event.

        Args:
            payload: Data transfer object containing the new product's details.

        Returns:
            ProductResponseDTO with the created product data.

        Raises:
            HTTPException: 409 if a product with the same name already exists.
        """
        if await self.repo.get_by_name(payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A product with name '{payload.name}' already exists",
            )

        product = Product(
            name=payload.name,
            description=payload.description,
            product_type=payload.product_type,
            transport_mode=payload.transport_mode,
            size=payload.size,
        )
        created = await self.repo.create(product)
        logger.info(f"[PRODUCT] Created product id={created.id} name='{created.name}'")
        return ProductResponseDTO.model_validate(created)

    async def update_product(
        self,
        product_id: uuid.UUID,
        payload: ProductUpdateDTO,
    ) -> ProductResponseDTO:
        """
        Updates an existing product's attributes partially.

        Workflow:
        1. Retrieves the existing product and verifies its existence.
        2. Captures the current state of modified fields for the audit trail.
        3. If renaming, ensures the new name is not already in use by another product.
        4. Applies the updates and persists the changed entity.
        5. Calculates the diff and stores it in the global audit context for the middleware.

        Args:
            product_id: The unique identifier of the product to update.
            payload: Data transfer object with the fields to update.

        Returns:
            ProductResponseDTO with the updated product details.

        Raises:
            HTTPException:
                - 404: If the product is not found.
                - 409: If the new name is already taken.
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        before_state = {field: getattr(product, field) for field in update_data}

        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != product_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A product with name '{update_data['name']}' already exists",
                )

        for field, value in update_data.items():
            setattr(product, field, value)

        updated = await self.repo.update(product)

        diff = {}
        for field, old_val in before_state.items():
            new_val = getattr(updated, field)
            if old_val != new_val:
                diff[field] = {"old": str(old_val), "new": str(new_val)}

        if diff:
            ctx = audit_context.get().copy()
            ctx["diff"] = diff
            audit_context.set(ctx)

        return ProductResponseDTO.model_validate(updated)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """
        Permanently removes a product from the catalog.

        Workflow:
        1. Retrieves the product and verifies it exists.
        2. Invokes the repository to delete the record.

        Args:
            product_id: The unique identifier of the product to delete.

        Raises:
            HTTPException: 404 if the product is not found.
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )
        await self.repo.delete(product)
