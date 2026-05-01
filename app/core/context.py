import contextvars
from typing import Any, Dict

# Context variable to store audit information during the request lifecycle.
# This allows the Service layer to add business-level details (like diffs) 
# that the Middleware/Interceptor will later log.
audit_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("audit_context", default={})
