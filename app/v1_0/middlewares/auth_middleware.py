import jwt
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.settings import settings
from app.core.database import get_db
from app.infraestructure.redis.redis_cache_service import RedisCacheService
from app.infraestructure.models.user import User

_bearer_scheme = HTTPBearer()


@inject
async def require_authenticated(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis_cache: RedisCacheService = Depends(
        Provide["redis_cache_service"]
    ),
) -> User:
    """
    FastAPI dependency – resolves the currently authenticated user.

    Returns
    -------
    User
        The active, authenticated ``User`` ORM instance.

    Raises
    ------
    HTTPException(401)
        If the token is missing, malformed, expired, or the session has been
        revoked.
    HTTPException(403)
        If the user account is deactivated.
    """
    token = credentials.credentials

    # --- 1. Decode and validate JWT -------------------------------------------
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id_str: str | None = payload.get("sub")
        sid: str | None = payload.get("sid")

        if user_id_str is None or sid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user_id = uuid.UUID(user_id_str)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # --- 2. Validate Redis session ---------------------------------------------
    session_key = f"session:{user_id}:{sid}"
    session_data = await redis_cache.get(session_key)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked or expired",
        )

    # --- 3. Load and validate user record -------------------------------------
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user
