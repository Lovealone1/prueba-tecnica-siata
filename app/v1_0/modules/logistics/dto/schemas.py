import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LogisticsNodeCreateDTO(BaseModel):
    """
    Payload to create a warehouse or seaport.

    Note: `continent` is NOT accepted from the client.
    It is automatically derived from `country` by the ORM model
    via @validates("country") → LocationHelper.get_continent_by_country().

    `city` and `country` are normalized to Title Case before persistence.
    """

    name: str = Field(..., min_length=1, max_length=150, description="Facility name")
    address: str = Field(..., min_length=1, max_length=255, description="Physical address")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    country: str = Field(..., min_length=1, max_length=100, description="Country name (used to derive continent)")

    @field_validator("city", "country", mode="before")
    @classmethod
    def normalize_to_title_case(cls, value: str) -> str:
        """Strips whitespace and converts to Title Case (e.g. 'COLOMBIA' → 'Colombia')."""
        if isinstance(value, str):
            return value.strip().title()
        return value


class LogisticsNodeUpdateDTO(BaseModel):
    """
    Partial payload to update a warehouse or seaport (PATCH).

    - `country` is allowed: updating it will automatically re-derive `continent`
      via the ORM @validates trigger.
    - `continent` is NOT exposed: it is always derived from `country`,
      never set directly by the client.
    - `city` and `country` are normalized to Title Case when provided.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Changing country re-derives continent automatically",
    )

    @field_validator("city", "country", mode="before")
    @classmethod
    def normalize_to_title_case(cls, value: Optional[str]) -> Optional[str]:
        """Strips whitespace and converts to Title Case when a value is provided."""
        if isinstance(value, str):
            return value.strip().title()
        return value


class LogisticsNodeResponseDTO(BaseModel):
    """
    Logistics node representation returned to the HTTP client.
    Exposes `continent` as a read-only field derived from `country`.
    """

    id: uuid.UUID
    name: str
    address: str
    city: str
    country: str
    continent: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LogisticsNodeListResponseDTO(BaseModel):
    """Paginated response for logistics node listing."""

    data: list[LogisticsNodeResponseDTO]
    total: int
    skip: int
    limit: int

