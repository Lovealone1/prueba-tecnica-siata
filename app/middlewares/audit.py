import time
import uuid
from typing import Optional, Any

from fastapi import Depends, Request

from app.core.logger import logger
from app.infraestructure.models.user import User
from .auth import require_authenticated


def audit_log(action: Optional[str] = None, metadata: Optional[dict[str, Any]] = None):
    resolved_action = action or "unspecified"
    resolved_metadata = metadata or {}

    async def _audit(
        request: Request,
        current_user: User = Depends(require_authenticated),
    ) -> User:
        start = time.monotonic()

        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else "unknown")
        )
        user_agent = request.headers.get("user-agent", "-")

        user_id: uuid.UUID = current_user.id
        role = (
            current_user.global_role.value
            if hasattr(current_user.global_role, "value")
            else current_user.global_role
        )

        elapsed_ms = round((time.monotonic() - start) * 1000)

        meta_str = f" | meta: {resolved_metadata}" if resolved_metadata else ""

        logger.info(
            f"[AUDIT] {resolved_action}"
            f" | user_id={user_id} role={role}"
            f" | IP: {client_ip}"
            f" | UA: {user_agent}"
            f" | {elapsed_ms}ms"
            f"{meta_str}"
        )

        return current_user

    return _audit
