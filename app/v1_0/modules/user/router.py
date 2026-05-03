import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject
from app.infraestructure.models.user import User, GlobalRole
from app.middlewares import require_roles, audit_log
from .dto.schemas import UserUpdateRoleDTO, UserResponseDTO, UserListResponseDTO
from .service import AdminUserService

router = APIRouter(prefix="/users", tags=["Users Admin"])
_allowed_roles = Depends(require_roles(GlobalRole.ADMIN))

@router.get("/", response_model=UserListResponseDTO)
@inject
async def list_users(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    _u: User = _allowed_roles,
    service: AdminUserService = Depends(Provide["admin_user_service"]),
):
    return await service.list(skip=skip, limit=limit)

@router.patch("/{user_id}/role", response_model=UserResponseDTO)
@inject
async def update_user_role(
    user_id: uuid.UUID,
    payload: UserUpdateRoleDTO,
    _u: User = Depends(audit_log(action="user.update_role", metadata={"entity": "User"})),
    service: AdminUserService = Depends(Provide["admin_user_service"]),
):
    return await service.update_role(user_id, payload)
