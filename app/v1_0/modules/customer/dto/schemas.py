import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateDTO(BaseModel):
    """Payload to create a customer."""

    name: str = Field(..., min_length=1, max_length=255, description="Customer full name")
    identifier: str = Field(..., min_length=1, max_length=255, description="Unique identifier (NIT, CC, etc.)")
    email: EmailStr = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, max_length=255, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")


class CustomerUpdateDTO(BaseModel):
    """Partial payload to update a customer (PATCH)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None


class CustomerResponseDTO(BaseModel):
    """Customer representation returned to the HTTP client."""

    id: uuid.UUID
    name: str
    identifier: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponseDTO(BaseModel):
    """Paginated response for customer listing."""

    data: list[CustomerResponseDTO]
    total: int
    skip: int
    limit: int
