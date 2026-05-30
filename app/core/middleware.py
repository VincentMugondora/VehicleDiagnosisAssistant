from uuid import uuid4
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject request_id into every request and bind it to
    structured logging context for tracing.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id

        # Bind request_id to structlog context for all logs in this request
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context after request
            structlog.contextvars.clear_contextvars()
