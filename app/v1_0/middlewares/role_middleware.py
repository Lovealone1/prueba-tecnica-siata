from typing import Callable, Sequence
from functools import wraps

from fastapi import Depends, HTTPException, status

from app.infraestructure.models.user import User, GlobalRole
from .auth_middleware import require_authenticated


def require_roles(*allowed_roles: GlobalRole) -> Callable:
    """
    Dependency factory – returns a FastAPI dependency that enforces role-based
    access control.

    Parameters
    ----------
    *allowed_roles : GlobalRole
        One or more ``GlobalRole`` values that are permitted to access the
        endpoint.  At least one role must be provided.

    Returns
    -------
    Callable
        An async FastAPI dependency function.

    Raises
    ------
    ValueError
        If no roles are supplied (programming error, caught at start-up).
    HTTPException(403)
        At request time, when the authenticated user's role is not in
        ``allowed_roles``.

    Example
    -------
    ::

        @router.delete(
            "/users/{user_id}",
            dependencies=[Depends(require_roles(GlobalRole.ADMIN))],
        )
        async def delete_user(user_id: str, ...):
            ...
    """
    if not allowed_roles:
        raise ValueError("require_roles() requires at least one GlobalRole argument.")

    allowed: Sequence[GlobalRole] = allowed_roles

    async def _check_role(current_user: User = Depends(require_authenticated)) -> User:
        """
        Inner dependency – validates that ``current_user.global_role`` is one
        of the roles declared in the enclosing ``require_roles`` call.

        Returns
        -------
        User
            The same user instance so it can be re-used by the route handler.

        Raises
        ------
        HTTPException(403)
            If the user's role is not in the allowed set.
        """
        user_role: GlobalRole = current_user.global_role

        # Normalize: compare enum member to enum member
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
