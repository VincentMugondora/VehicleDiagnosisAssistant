"""
Request size limit middleware.

Prevents memory exhaustion attacks from oversized payloads.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.logging import logger

# Maximum request body size (10 MB)
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce maximum request body size.

    Prevents memory exhaustion from maliciously large payloads.
    """

    async def dispatch(self, request: Request, call_next):
        """Check Content-Length header before processing request."""
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > MAX_BODY_SIZE:
                    logger.warning(
                        "request_too_large",
                        path=request.url.path,
                        size=size,
                        max_size=MAX_BODY_SIZE
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request body too large",
                            "max_size_mb": MAX_BODY_SIZE // (1024 * 1024)
                        }
                    )
            except ValueError:
                pass  # Invalid Content-Length, let request proceed

        response = await call_next(request)
        return response
