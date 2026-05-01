import uuid
from typing import List, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport
from .domain import ILogisticsNodeRepository

T = TypeVar("T", Warehouse, Seaport)


class LogisticsNodeRepository(ILogisticsNodeRepository[T]):
    """
    Generic repository for logistics nodes.
    Both WarehouseRepository and SeaportRepository are aliases of this class
    instantiated with their respective ORM model.
    """

    def __init__(self, db_maker: async_sessionmaker, model_class: Type[T]) -> None:
        self.db_maker = db_maker
        self.model_class = model_class

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        continent: Optional[str] = None,
        country: Optional[str] = None,
    ) -> List[T]:
        async with self.db_maker() as session:
            query = select(self.model_class)

            if continent:
                query = query.where(self.model_class.continent == continent.strip().upper())
            if country:
                query = query.where(self.model_class.country == country.strip().title())

            result = await session.execute(
                query.offset(skip)
                .limit(limit)
                .order_by(self.model_class.created_at.desc())
            )
            return list(result.scalars().all())

    async def count_all(
        self, continent: Optional[str] = None, country: Optional[str] = None
    ) -> int:
        async with self.db_maker() as session:
            query = select(func.count()).select_from(self.model_class)

            if continent:
                query = query.where(self.model_class.continent == continent.strip().upper())
            if country:
                query = query.where(self.model_class.country == country.strip().title())

            result = await session.execute(query)
            return result.scalar_one()

    async def get_by_id(self, node_id: uuid.UUID) -> Optional[T]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == node_id)
            )
            return result.scalar_one_or_none()

    async def create(self, node: T) -> T:
        async with self.db_maker() as session:
            session.add(node)
            await session.commit()
            await session.refresh(node)
            return node

    async def update(self, node: T) -> T:
        async with self.db_maker() as session:
            merged = await session.merge(node)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, node: T) -> None:
        async with self.db_maker() as session:
            existing = await session.get(self.model_class, node.id)
            if existing:
                await session.delete(existing)
                await session.commit()


# Concrete aliases — instantiated by the DI container with the correct model_class
WarehouseRepository = LogisticsNodeRepository
SeaportRepository = LogisticsNodeRepository
