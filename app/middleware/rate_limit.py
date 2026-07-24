"""
IP-based rate limiting middleware for public API endpoints.

Prevents abuse of the /chat endpoint by limiting requests per IP.
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.logging import logger

RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMITED_PATHS = {"/chat"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS

        timestamps = self._requests[client_ip]
        self._requests[client_ip] = [t for t in timestamps if t > window_start]

        if len(self._requests[client_ip]) >= RATE_LIMIT_REQUESTS:
            return True

        self._requests[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        if request.url.path in RATE_LIMITED_PATHS and request.method == "POST":
            client_ip = self._get_client_ip(request)
            if self._is_rate_limited(client_ip):
                logger.warning(
                    "rate_limit_exceeded",
                    client_ip=client_ip,
                    path=request.url.path
                )
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)}
                )

        return await call_next(request)
