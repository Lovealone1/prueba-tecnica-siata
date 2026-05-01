import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.product import Product, TransportMode, ProductSize
from .domain import IProductRepository


class ProductRepository(IProductRepository):
    """
    Concrete implementation of IProductRepository over PostgreSQL / SQLAlchemy.

    Each method opens its own async session via the factory, commits the unit of
    work, and closes the session automatically through the context manager.
    """

    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> List[Product]:
        """Returns products ordered from newest to oldest with optional filtering."""
        async with self.db_maker() as session:
            query = select(Product)
            if transport_mode:
                query = query.where(Product.transport_mode == transport_mode)
            if size:
                query = query.where(Product.size == size)

            result = await session.execute(
                query.offset(skip).limit(limit).order_by(Product.created_at.desc())
            )
            return list(result.scalars().all())

    async def count_all(
        self,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> int:
        """Returns the total count of products with optional filtering."""
        async with self.db_maker() as session:
            query = select(func.count()).select_from(Product)
            if transport_mode:
                query = query.where(Product.transport_mode == transport_mode)
            if size:
                query = query.where(Product.size == size)

            result = await session.execute(query)
            return result.scalar_one()

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Retrieves a product by its primary UUID key."""
        async with self.db_maker() as session:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Product]:
        """Retrieves a product by its exact name (case-sensitive)."""
        async with self.db_maker() as session:
            result = await session.execute(
                select(Product).where(Product.name == name)
            )
            return result.scalar_one_or_none()

    async def create(self, product: Product) -> Product:
        """Inserts a new product row and returns the refreshed ORM instance."""
        async with self.db_maker() as session:
            session.add(product)
            await session.commit()
            await session.refresh(product)
            return product

    async def update(self, product: Product) -> Product:
        """Merges a detached product instance into the session and commits."""
        async with self.db_maker() as session:
            merged = await session.merge(product)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, product: Product) -> None:
        """Re-fetches the product by PK and deletes it within a single transaction."""
        async with self.db_maker() as session:
            existing = await session.get(Product, product.id)
            if existing:
                await session.delete(existing)
                await session.commit()
