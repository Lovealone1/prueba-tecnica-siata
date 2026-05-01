import uuid
from typing import Optional, List
from datetime import date
from abc import ABC, abstractmethod

from app.infraestructure.models.shipment import Shipment, ShippingType, ShippingStatus, ShipmentStatusLog

__all__ = ["Shipment", "IShipmentRepository", "ShipmentStatusLog"]


class IShipmentRepository(ABC):
    """Port: contract that any persistence adapter must implement."""

    @abstractmethod
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        guide_number: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Shipment]:
        ...

    @abstractmethod
    async def count_all(
        self,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        guide_number: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
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

    @abstractmethod
    async def create_status_log(self, log: ShipmentStatusLog) -> ShipmentStatusLog:
        ...

    @abstractmethod
    async def get_status_history(self, shipment_id: uuid.UUID) -> List[ShipmentStatusLog]:
        ...

    @abstractmethod
    async def get_admin_stats(self) -> dict:
        ...
