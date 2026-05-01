import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.shipment import Shipment
from app.v1_0.modules.shipment.domain import IShipmentRepository

class ShipmentRepository(IShipmentRepository):
    def __init__(self, db_maker: async_sessionmaker):
        self.db_maker = db_maker

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Shipment]:
        async with self.db_maker() as session:
            query = select(Shipment).order_by(Shipment.created_at.desc()).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def count_all(self) -> int:
        async with self.db_maker() as session:
            query = select(func.count(Shipment.id))
            result = await session.execute(query)
            return result.scalar() or 0

    async def get_by_id(self, shipment_id: uuid.UUID) -> Optional[Shipment]:
        async with self.db_maker() as session:
            return await session.get(Shipment, shipment_id)

    async def get_by_guide_number(self, guide_number: str) -> Optional[Shipment]:
        async with self.db_maker() as session:
            query = select(Shipment).where(Shipment.guide_number == guide_number)
            result = await session.execute(query)
            return result.scalars().first()

    async def create(self, shipment: Shipment) -> Shipment:
        async with self.db_maker() as session:
            session.add(shipment)
            await session.commit()
            await session.refresh(shipment)
            return shipment

    async def update(self, shipment: Shipment) -> Shipment:
        async with self.db_maker() as session:
            merged = await session.merge(shipment)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, shipment: Shipment) -> None:
        async with self.db_maker() as session:
            existing = await session.get(Shipment, shipment.id)
            if existing:
                await session.delete(existing)
                await session.commit()
