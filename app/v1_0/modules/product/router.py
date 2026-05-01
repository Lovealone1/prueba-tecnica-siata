import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject

from app.infraestructure.models.user import User, GlobalRole
from app.infraestructure.models.product import TransportMode, ProductSize
from app.middlewares import require_roles, audit_log
from .dto.schemas import (
    ProductCreateDTO,
    ProductUpdateDTO,
    ProductResponseDTO,
    ProductListResponseDTO,
)
from .service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

# Shared dependency: requires an authenticated user with USER or ADMIN role.
_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))


@router.get(
    "/",
    response_model=ProductListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="List products",
)
@inject
async def list_products(
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of records to return")] = 100,
    transport_mode: Annotated[Optional[TransportMode], Query(description="Filter by transport mode")] = None,
    size: Annotated[Optional[ProductSize], Query(description="Filter by product size")] = None,
    _current_user: User = _allowed_roles,
    product_service: ProductService = Depends(Provide["product_service"]),
) -> ProductListResponseDTO:
    return await product_service.list_products(
        skip=skip, limit=limit, transport_mode=transport_mode, size=size
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
@inject
async def get_product(
    product_id: uuid.UUID,
    _current_user: User = _allowed_roles,
    product_service: ProductService = Depends(Provide["product_service"]),
) -> ProductResponseDTO:
    return await product_service.get_product(product_id)


@router.post(
    "/",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
@inject
async def create_product(
    payload: ProductCreateDTO,
    _current_user: User = _allowed_roles,
    product_service: ProductService = Depends(Provide["product_service"]),
) -> ProductResponseDTO:
    return await product_service.create_product(payload)


@router.patch(
    "/{product_id}",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Partially update a product",
)
@inject
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdateDTO,
    _audit_user: User = Depends(
        audit_log(
            action="product.update",
            metadata={"entity": "Product"},
            capture_body=True,
        )
    ),
    product_service: ProductService = Depends(Provide["product_service"]),
) -> ProductResponseDTO:
    return await product_service.update_product(product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
@inject
async def delete_product(
    product_id: uuid.UUID,
    _audit_user: User = Depends(
        audit_log(action="product.delete", metadata={"entity": "Product"})
    ),
    product_service: ProductService = Depends(Provide["product_service"]),
) -> None:
    await product_service.delete_product(product_id)
