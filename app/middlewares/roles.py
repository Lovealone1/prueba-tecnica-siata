from typing import Callable, Sequence

from fastapi import Depends, HTTPException, status

from app.infraestructure.models.user import User, GlobalRole
from .auth import require_authenticated


def require_roles(*allowed_roles: GlobalRole) -> Callable:
    if not allowed_roles:
        raise ValueError("require_roles() requires at least one GlobalRole argument.")

    allowed: Sequence[GlobalRole] = allowed_roles

    async def _check_role(current_user: User = Depends(require_authenticated)) -> User:
        user_role: GlobalRole = current_user.global_role

        if isinstance(user_role, str):
            try:
                user_role = GlobalRole(user_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unknown user role",
                )

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{', '.join(r.value for r in allowed)}."
                ),
            )

        return current_user

    return _check_role
