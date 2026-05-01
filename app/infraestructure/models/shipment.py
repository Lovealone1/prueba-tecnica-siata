from datetime import datetime
import uuid
import enum

from sqlalchemy import String, DateTime, func, Integer, Numeric, Float, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.infraestructure.models.base import Base


class ShippingStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"


class ShippingType(str, enum.Enum):
    LAND = "LAND"
    MARITIME = "MARITIME"


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)
    seaport_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seaports.id", ondelete="SET NULL"), nullable=True)
    
    product_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    shipping_type: Mapped[ShippingType] = mapped_column(Enum(ShippingType, name="shipping_type_enum"), nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    dispatch_location: Mapped[str] = mapped_column(String(100), server_default='USA', default='USA', nullable=False)
    dispatch_continent: Mapped[str] = mapped_column(String(100), server_default='North America', default='North America', nullable=False)
    
    guide_number: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    vehicle_plate: Mapped[str | None] = mapped_column(String(6), nullable=True)
    fleet_number: Mapped[str | None] = mapped_column(String(8), nullable=True)
    
    registry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    shipping_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shipping_status: Mapped[ShippingStatus] = mapped_column(Enum(ShippingStatus, name="shipping_status_enum"), default=ShippingStatus.PENDING, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
