import uuid
from typing import Optional, List
from datetime import datetime, time, date, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.shipment import Shipment, ShippingType, ShippingStatus
from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport
from app.v1_0.modules.shipment.domain import IShipmentRepository

class ShipmentRepository(IShipmentRepository):
    def __init__(self, db_maker: async_sessionmaker):
        self.db_maker = db_maker

    def _apply_filters(
        self,
        query,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        if customer_id:
            query = query.where(Shipment.customer_id == customer_id)
        if dispatch_location:
            query = query.where(Shipment.dispatch_location.ilike(f"%{dispatch_location}%"))
        if shipping_type:
            query = query.where(Shipment.shipping_type == shipping_type)
        if shipping_status:
            query = query.where(Shipment.shipping_status == shipping_status)
        
        if destination_country:
            # We need to join with Warehouse and Seaport to filter by their country
            query = query.outerjoin(Warehouse, Shipment.warehouse_id == Warehouse.id)
            query = query.outerjoin(Seaport, Shipment.seaport_id == Seaport.id)
            query = query.where(
                or_(
                    Warehouse.country.ilike(f"%{destination_country}%"),
                    Seaport.country.ilike(f"%{destination_country}%")
                )
            )

        if start_date:
            # Normalize to beginning of day in UTC (or the system TZ if not specified)
            # Since our DB stores UTC datetimes
            start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
            query = query.where(Shipment.registry_date >= start_dt)
            
        if end_date:
            # Normalize to end of day in UTC
            end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
            query = query.where(Shipment.registry_date <= end_dt)
        
        return query

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Shipment]:
        async with self.db_maker() as session:
            query = select(Shipment)
            query = self._apply_filters(
                query, customer_id, dispatch_location, destination_country, 
                shipping_type, shipping_status, start_date, end_date
            )
            query = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def count_all(
        self,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        async with self.db_maker() as session:
            query = select(func.count(Shipment.id))
            query = self._apply_filters(
                query, customer_id, dispatch_location, destination_country, 
                shipping_type, shipping_status, start_date, end_date
            )
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
