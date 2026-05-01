import time
import uuid
import json
from typing import Optional, Any

from fastapi import Depends, Request

from app.core.logger import logger
from app.core.context import audit_context
from app.infraestructure.models.user import User
from .auth import require_authenticated


def audit_log(action: Optional[str] = None, metadata: Optional[dict[str, Any]] = None, capture_body: bool = False):
    """
    Advanced audit log dependency using yield and ContextVars.
    
    1. Pre-action: Sets up the audit context and captures request metadata.
    2. Endpoint execution: The service layer can enrich audit_context with diffs.
    3. Post-action: Logs everything including the business-level diffs.
    """
    resolved_action = action or "unspecified"
    base_metadata = metadata or {}

    async def _audit(
        request: Request,
        current_user: User = Depends(require_authenticated),
    ):
        start = time.monotonic()
        
        # Initialize context for this request
        ctx = {
            "action": resolved_action,
            "base_meta": base_metadata,
            "path_params": request.path_params,
            "payload": None
        }
        
        # Pre-capture body if requested
        if capture_body and request.method in ["POST", "PATCH", "PUT"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body_json = json.loads(body_bytes)
                    sensitive_fields = {"password", "token", "otp", "secret"}
                    ctx["payload"] = {k: v for k, v in body_json.items() if k not in sensitive_fields}
            except Exception:
                ctx["payload"] = "error_capturing_body"

        # Set context and save token for cleanup
        token = audit_context.set(ctx)

        try:
            # --- ENDPOINT EXECUTION ---
            yield current_user
            # --------------------------

            # Re-fetch context after service might have modified it (e.g., added "diff")
            final_ctx = audit_context.get()
            
            elapsed_ms = round((time.monotonic() - start) * 1000)
            
            # Client info
            forwarded_for = request.headers.get("x-forwarded-for")
            client_ip = (
                forwarded_for.split(",")[0].strip()
                if forwarded_for
                else (request.client.host if request.client else "unknown")
            )
            
            user_id: uuid.UUID = current_user.id
            role = (
                current_user.global_role.value
                if hasattr(current_user.global_role, "value")
                else current_user.global_role
            )

            # Build final metadata string
            log_meta = {
                "action": final_ctx["action"],
                "params": final_ctx["path_params"],
                "static": final_ctx["base_meta"],
            }
            if final_ctx["payload"]:
                log_meta["payload"] = final_ctx["payload"]
            if "diff" in final_ctx:
                log_meta["diff"] = final_ctx["diff"]

            logger.info(
                f"[AUDIT] {final_ctx['action']}"
                f" | user_id={user_id} role={role}"
                f" | IP: {client_ip}"
                f" | {elapsed_ms}ms"
                f" | data: {log_meta}"
            )

        finally:
            # Clean up context
            audit_context.reset(token)

    return _audit
