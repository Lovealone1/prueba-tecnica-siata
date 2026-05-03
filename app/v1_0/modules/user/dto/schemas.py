import uuid
from datetime import datetime
from pydantic import BaseModel
from app.infraestructure.models.user import GlobalRole

class UserResponseDTO(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone_number: str | None
    is_active: bool
    global_role: GlobalRole
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class UserListResponseDTO(BaseModel):
    data: list[UserResponseDTO]
    total: int
    skip: int
    limit: int

class UserUpdateRoleDTO(BaseModel):
    global_role: GlobalRole
