import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import logger


class RequestInfoMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that logs a structured summary for every HTTP request.

    Applies globally to all routes regardless of authentication status, making
    it suitable for logging public endpoints (e.g. /auth/otp, /health) where
    no user identity is available yet.

    Log format
    ----------
    Each request produces a single INFO line after the response is sent::

        [POST] /api/v1/auth/otp | 200 | 47ms | IP: 192.168.1.10 | UA: Mozilla/5.0...

    This structured format is intentionally parseable by log aggregators
    (Datadog, Loki, CloudWatch, etc.) for future monitoring integration.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()

        # Resolve real client IP — honour X-Forwarded-For when behind a proxy.
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else "unknown")
        )

        user_agent = request.headers.get("user-agent", "-")
        method = request.method
        path = request.url.path

        response: Response = await call_next(request)

        elapsed_ms = round((time.monotonic() - start) * 1000)
        status = response.status_code

        logger.info(
            f"[{method}] {path} | {status} | {elapsed_ms}ms"
            f" | IP: {client_ip}"
            f" | UA: {user_agent}"
        )

        return response
