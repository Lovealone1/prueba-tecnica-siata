from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import validates

from app.utils.location_helper import LocationHelper
from .base import Base

class Seaport(Base):
    """
    SQLAlchemy model for the 'seaports' table.
    Represents a maritime node in the logistics network.
    """
    __tablename__ = "seaports"

    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("uuid_generate_v4()")
    )
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    continent = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    @validates("country")
    def validate_country_and_set_continent(self, key: str, value: str) -> str:
        """
        Triggered whenever 'country' is set.
        Automatically assigns the continent using the LocationHelper.
        """
        self.continent = LocationHelper.get_continent_by_country(value)
        return value

    def __repr__(self) -> str:
        return f"<Seaport(id={self.id}, name='{self.name}', continent='{self.continent}')>"
