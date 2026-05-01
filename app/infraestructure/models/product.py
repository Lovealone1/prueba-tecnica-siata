from datetime import datetime
import enum
import uuid

from sqlalchemy import String, DateTime, func, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.infraestructure.models.base import Base


class TransportMode(str, enum.Enum):
    LAND = "LAND"
    MARITIME = "MARITIME"


class ProductSize(str, enum.Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    EXTRA_LARGE = "EXTRA_LARGE"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transport_mode: Mapped[TransportMode] = mapped_column(
        Enum(TransportMode, name="transport_mode_enum", create_type=False), 
        nullable=False
    )
    size: Mapped[ProductSize] = mapped_column(
        Enum(ProductSize, name="product_size_enum", create_type=False), 
        default=ProductSize.MEDIUM, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
