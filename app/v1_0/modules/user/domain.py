import uuid
from typing import Optional, List
from abc import ABC, abstractmethod
from app.infraestructure.models.user import User

class IUserRepository(ABC):
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]: ...
    @abstractmethod
    async def count_all(self) -> int: ...
    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[User]: ...
    @abstractmethod
    async def update(self, entity: User) -> User: ...
