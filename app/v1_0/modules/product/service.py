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
        self.repo = product_repository

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> ProductListResponseDTO:
        """Returns a paginated and optionally filtered list of products."""
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
        """Retrieves a product by its UUID. Raises 404 if it does not exist."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )
        return ProductResponseDTO.model_validate(product)

    async def create_product(self, payload: ProductCreateDTO) -> ProductResponseDTO:
        """
        Creates a new product.

        Validations:
        - Name must be unique across all products.
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
        Partially updates a product (PATCH).

        - Validates name uniqueness if attempting to rename.
        - Captures a before/after diff and stores it in `audit_context` for
          the audit log middleware to persist.
        """
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # 1. Capture 'before' state for auditing
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

        # 2. Compare 'after' state and store diff in audit context
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
        """Deletes a product. Raises 404 if it does not exist."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )
        await self.repo.delete(product)
