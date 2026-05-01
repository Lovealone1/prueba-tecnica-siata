import time
import uuid
from typing import Optional, Any

from fastapi import Depends, Request

from app.core.logger import logger
from app.infraestructure.models.user import User
from .auth_middleware import require_authenticated


def audit_log(action: Optional[str] = None, metadata: Optional[dict[str, Any]] = None):
    """
    FastAPI dependency factory for audit logging on protected endpoints.

    Logs a structured audit entry that includes the authenticated user's
    identity alongside the request context. Designed to be bound to a
    monitoring/observability tool in the future.

    Parameters
    ----------
    action : str, optional
        Human-readable description of the business action being performed,
        e.g. ``"user.session.revoke"`` or ``"report.export"``.
        When omitted the entry is logged with action ``"unspecified"``.
    metadata : dict, optional
        Arbitrary key-value pairs that add domain context to the audit entry,
        e.g. ``{"target_session_id": sid}`` or ``{"report_type": "csv"}``.

    Returns
    -------
    Callable
        An async FastAPI dependency that resolves to the authenticated ``User``
        so it can optionally be re-used in the route handler.

    Usage
    -----
    Minimal — just audit who hit the endpoint::

        @router.post("/logout")
        async def logout(
            user: User = Depends(audit_log(action="user.session.logout"))
        ):
            ...

    With extra metadata::

        @router.delete("/sessions/{sid}")
        async def revoke_session(
            sid: str,
            user: User = Depends(
                audit_log(
                    action="user.session.revoke",
                    metadata={"target_sid": sid},
                )
            ),
        ):
            ...

    As a route-level guard (user not needed in handler body)::

        @router.get(
            "/admin/users",
            dependencies=[Depends(audit_log(action="admin.users.list"))],
        )
        async def list_users(): ...

    Log format
    ----------
    Each invocation produces one INFO line::

        [AUDIT] user.session.revoke | user_id=<uuid> role=ADMIN
                | IP: 192.168.1.10 | UA: Mozilla/5.0 | 3ms
                | meta: {"target_sid": "abc-123"}
    """
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
