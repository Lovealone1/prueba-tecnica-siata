import uuid
from typing import Optional, List
from abc import ABC, abstractmethod

from app.infraestructure.models.shipment import Shipment

__all__ = ["Shipment", "IShipmentRepository"]


class IShipmentRepository(ABC):
    """Port: contract that any persistence adapter must implement."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Shipment]:
        ...

    @abstractmethod
    async def count_all(self) -> int:
        ...

    @abstractmethod
    async def get_by_id(self, shipment_id: uuid.UUID) -> Optional[Shipment]:
        ...

    @abstractmethod
    async def get_by_guide_number(self, guide_number: str) -> Optional[Shipment]:
        ...

    @abstractmethod
    async def create(self, shipment: Shipment) -> Shipment:
        ...

    @abstractmethod
    async def update(self, shipment: Shipment) -> Shipment:
        ...

    @abstractmethod
    async def delete(self, shipment: Shipment) -> None:
        ...
