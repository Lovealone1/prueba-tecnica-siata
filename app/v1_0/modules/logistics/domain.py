import uuid
from typing import Optional, List, TypeVar, Generic
from abc import ABC, abstractmethod

from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport

T = TypeVar("T", Warehouse, Seaport)

__all__ = [
    "T",
    "ILogisticsNodeRepository",
    "IWarehouseRepository",
    "ISeaportRepository",
]


class ILogisticsNodeRepository(ABC, Generic[T]):
    """
    Generic port for any logistics node (Warehouse, Seaport).
    The service layer only depends on this contract.
    """

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        continent: Optional[str] = None,
        country: Optional[str] = None,
    ) -> List[T]:
        ...

    @abstractmethod
    async def count_all(
        self, continent: Optional[str] = None, country: Optional[str] = None
    ) -> int:
        ...

    @abstractmethod
    async def get_by_id(self, node_id: uuid.UUID) -> Optional[T]:
        ...

    @abstractmethod
    async def create(self, node: T) -> T:
        ...

    @abstractmethod
    async def update(self, node: T) -> T:
        ...

    @abstractmethod
    async def delete(self, node: T) -> None:
        ...


# Typed aliases for DI wiring clarity
IWarehouseRepository = ILogisticsNodeRepository[Warehouse]
ISeaportRepository = ILogisticsNodeRepository[Seaport]
