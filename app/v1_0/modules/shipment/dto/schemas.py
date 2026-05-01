import uuid
import re
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

class ShippingStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"

class ShippingType(str, Enum):
    LAND = "LAND"
    MARITIME = "MARITIME"

class ShipmentCreateDTO(BaseModel):
    """Payload to create a shipment."""
    customer_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: Optional[uuid.UUID] = None
    seaport_id: Optional[uuid.UUID] = None
    product_quantity: int = Field(..., gt=0)
    discount_percentage: float = Field(0.0, ge=0, le=100)
    dispatch_location: str = Field("USA", max_length=100)
    dispatch_continent: str = Field("North America", max_length=100)
    
    vehicle_plate: Optional[str] = Field(None, description="Manual assignment. Format: AAA123.")
    fleet_number: Optional[str] = Field(None, description="Manual assignment. Format: AAA1234A.")

    @field_validator('vehicle_plate')
    @classmethod
    def validate_vehicle_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[A-Z]{3}\d{3}$", v):
                raise ValueError("vehicle_plate must be in AAA123 format")
        return v

    @field_validator('fleet_number')
    @classmethod
    def validate_fleet_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[A-Z]{3}\d{4}[A-Z]$", v):
                raise ValueError("fleet_number must be in AAA1234A format")
        return v


class ShipmentUpdateDTO(BaseModel):
    """Payload to update a shipment, for tracking lifecycle and manual assignments."""
    shipping_status: Optional[ShippingStatus] = Field(None, description="Allows for tracking the shipment lifecycle.")
    vehicle_plate: Optional[str] = Field(None, description="Manual assignment. Format: AAA123.")
    fleet_number: Optional[str] = Field(None, description="Manual assignment. Format: AAA1234A.")

    @field_validator('vehicle_plate')
    @classmethod
    def validate_vehicle_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[A-Z]{3}\d{3}$", v):
                raise ValueError("vehicle_plate must be in AAA123 format")
        return v

    @field_validator('fleet_number')
    @classmethod
    def validate_fleet_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[A-Z]{3}\d{4}[A-Z]$", v):
                raise ValueError("fleet_number must be in AAA1234A format")
        return v


class ShipmentResponseDTO(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: Optional[uuid.UUID]
    seaport_id: Optional[uuid.UUID]
    product_quantity: int
    shipping_type: ShippingType
    base_price: float
    discount_percentage: float
    total_price: float
    dispatch_location: str
    dispatch_continent: str
    guide_number: str
    vehicle_plate: Optional[str]
    fleet_number: Optional[str]
    registry_date: datetime
    shipping_date: datetime
    shipping_status: ShippingStatus
    applied_extra_fee: Optional[float] = Field(None, description="Bonus fee applied due to quantity thresholds. Calculated on the fly.")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShipmentListResponseDTO(BaseModel):
    data: list[ShipmentResponseDTO]
    total: int
    skip: int
    limit: int
