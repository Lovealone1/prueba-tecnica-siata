import uuid
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, func
from .domain import IUserRepository
from app.infraestructure.models.user import User

class AdminUserRepository(IUserRepository):
    def __init__(self, db_maker: async_sessionmaker) -> None:
        self.db_maker = db_maker

    async def get_all(self, skip=0, limit=100):
        async with self.db_maker() as session:
            result = await session.execute(
                select(User).offset(skip).limit(limit)
                           .order_by(User.created_at.desc())
            )
            return list(result.scalars().all())

    async def count_all(self) -> int:
        async with self.db_maker() as session:
            result = await session.execute(
                select(func.count()).select_from(User)
            )
            return result.scalar_one()

    async def get_by_id(self, entity_id: uuid.UUID):
        async with self.db_maker() as session:
            result = await session.execute(
                select(User).where(User.id == entity_id)
            )
            return result.scalar_one_or_none()

    async def update(self, entity: User):
        async with self.db_maker() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged
