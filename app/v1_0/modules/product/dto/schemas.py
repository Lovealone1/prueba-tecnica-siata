import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.infraestructure.models.product import TransportMode, ProductSize


class ProductCreateDTO(BaseModel):
    """Payload required to create a new product."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Commercial name of the product",
    )
    description: Optional[str] = Field(
        None,
        description="Optional extended description of the product",
    )
    product_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the product (e.g. 'Electronics', 'Chemicals')",
    )
    transport_mode: TransportMode = Field(
        ...,
        description="Transport mode required for this product: LAND or MARITIME",
    )
    size: ProductSize = Field(
        ProductSize.MEDIUM,
        description="Physical size classification of the product",
    )


class ProductUpdateDTO(BaseModel):
    """Partial payload for updating an existing product (PATCH semantics)."""

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    product_type: Optional[str] = Field(None, min_length=1, max_length=50)
    transport_mode: Optional[TransportMode] = None
    size: Optional[ProductSize] = None


class ProductResponseDTO(BaseModel):
    """Product representation returned to the HTTP client."""

    id: uuid.UUID
    name: str
    description: Optional[str]
    product_type: str
    transport_mode: TransportMode
    size: ProductSize
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponseDTO(BaseModel):
    """Paginated response for the product listing endpoint."""

    data: list[ProductResponseDTO]
    total: int
    skip: int
    limit: int
