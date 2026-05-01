import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.product import Product, TransportMode, ProductSize
from .domain import IProductRepository


class ProductRepository(IProductRepository):

    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        transport_mode: Optional[TransportMode] = None,
        size: Optional[ProductSize] = None,
    ) -> List[Product]:
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
        async with self.db_maker() as session:
            query = select(func.count()).select_from(Product)
            if transport_mode:
                query = query.where(Product.transport_mode == transport_mode)
            if size:
                query = query.where(Product.size == size)

            result = await session.execute(query)
            return result.scalar_one()

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Product]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Product).where(Product.name == name)
            )
            return result.scalar_one_or_none()

    async def create(self, product: Product) -> Product:
        async with self.db_maker() as session:
            session.add(product)
            await session.commit()
            await session.refresh(product)
            return product

    async def update(self, product: Product) -> Product:
        async with self.db_maker() as session:
            merged = await session.merge(product)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, product: Product) -> None:
        async with self.db_maker() as session:
            existing = await session.get(Product, product.id)
            if existing:
                await session.delete(existing)
                await session.commit()
