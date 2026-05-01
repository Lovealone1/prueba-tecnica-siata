import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import logger


class RequestInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()

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
