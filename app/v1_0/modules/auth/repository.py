from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.infraestructure.models.user import User
import uuid

class UserRepository:
    def __init__(self, db_maker: async_sessionmaker):
        self.db_maker = db_maker

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.db_maker() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        async with self.db_maker() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        async with self.db_maker() as session:
            session.add(user)
            await session.commit() 
            await session.refresh(user)
            return user

    async def commit_user(self, user: User):
        async with self.db_maker() as session:
            await session.merge(user)
            await session.commit()

