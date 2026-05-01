import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infraestructure.models.customer import Customer
from .domain import ICustomerRepository


class CustomerRepository(ICustomerRepository):
    """Concrete implementation of ICustomerRepository over PostgreSQL / SQLAlchemy."""

    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Customer).offset(skip).limit(limit).order_by(Customer.created_at.desc())
            )
            return list(result.scalars().all())

    async def count_all(self) -> int:
        async with self.db_maker() as session:
            result = await session.execute(select(func.count()).select_from(Customer))
            return result.scalar_one()

    async def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> Optional[Customer]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Customer).where(Customer.identifier == identifier)
            )
            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Customer]:
        async with self.db_maker() as session:
            result = await session.execute(
                select(Customer).where(Customer.email == email)
            )
            return result.scalar_one_or_none()

    async def create(self, customer: Customer) -> Customer:
        async with self.db_maker() as session:
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
            return customer

    async def update(self, customer: Customer) -> Customer:
        async with self.db_maker() as session:
            merged = await session.merge(customer)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, customer: Customer) -> None:
        async with self.db_maker() as session:
            existing = await session.get(Customer, customer.id)
            if existing:
                await session.delete(existing)
                await session.commit()
