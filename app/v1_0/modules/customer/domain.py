import uuid
from typing import Optional, List
from abc import ABC, abstractmethod

from app.infraestructure.models.customer import Customer

__all__ = ["Customer", "ICustomerRepository"]


class ICustomerRepository(ABC):
    """Port: contract that any persistence adapter must implement."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        ...

    @abstractmethod
    async def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        ...

    @abstractmethod
    async def get_by_identifier(self, identifier: str) -> Optional[Customer]:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Customer]:
        ...

    @abstractmethod
    async def create(self, customer: Customer) -> Customer:
        ...

    @abstractmethod
    async def update(self, customer: Customer) -> Customer:
        ...

    @abstractmethod
    async def delete(self, customer: Customer) -> None:
        ...
