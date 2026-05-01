import uuid
from typing import Optional, List
from abc import ABC, abstractmethod

from app.infraestructure.models.product import Product, TransportMode, ProductSize

__all__ = ["Product", "IProductRepository"]


class IProductRepository(ABC):
    """
    Port: abstract contract that any persistence adapter for Product must implement.

    The service layer depends exclusively on this interface, guaranteeing that
    the business logic remains isolated from any infrastructure detail.
    """

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> List[Product]:
        """Returns a paginated, ordered and optionally filtered list of products."""
        ...

    @abstractmethod
    async def count_all(
        self,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> int:
        """Returns the total number of products (optionally filtered)."""
        ...

    @abstractmethod
    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Retrieves a single product by its UUID. Returns None if not found."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Product]:
        """Retrieves a single product by its exact name. Returns None if not found."""
        ...

    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Persists a new product and returns the created instance with server-generated fields."""
        ...

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Merges and persists changes to an existing product. Returns the refreshed instance."""
        ...

    @abstractmethod
    async def delete(self, product: Product) -> None:
        """Deletes the given product from the persistence layer."""
        ...
