import uuid
from fastapi import HTTPException, status
from app.core.logger import logger
from app.infraestructure.models.user import User
from .domain import IUserRepository
from .dto.schemas import UserUpdateRoleDTO, UserListResponseDTO, UserResponseDTO
from app.infraestructure.redis.redis_cache_service import RedisCacheService

class AdminUserService:
    def __init__(
        self, 
        user_repository: IUserRepository,
        redis_cache: RedisCacheService
    ) -> None:
        self.repo = user_repository
        self.redis = redis_cache

    async def list(self, skip=0, limit=100) -> UserListResponseDTO:
        items = await self.repo.get_all(skip=skip, limit=limit)
        total = await self.repo.count_all()
        return UserListResponseDTO(
            data=[UserResponseDTO.model_validate(i) for i in items],
            total=total, skip=skip, limit=limit,
        )

    async def update_role(self, entity_id: uuid.UUID, payload: UserUpdateRoleDTO) -> UserResponseDTO:
        item = await self.repo.get_by_id(entity_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        
        item.global_role = payload.global_role
        updated = await self.repo.update(item)
        
        # Invalidate the user profile cache in Redis so the role change is applied on next request
        await self.redis.delete(f"user:profile:{item.id}")
        logger.info(f"[USER_ADMIN] Updated role for user {item.id} to {item.global_role}")
        
        return UserResponseDTO.model_validate(updated)
