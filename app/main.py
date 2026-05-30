from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import RequestContextMiddleware
from app.db.client import get_supabase_client
from app.api.routes import webhook

# Setup structured logging
setup_logging()

app = FastAPI(
    title="Vehicle Diagnosis Assistant API",
    version="2.0.0",
    description="WhatsApp-based OBD-II diagnostic assistant with PostgreSQL/Supabase backend"
)

# Register middleware
app.add_middleware(RequestContextMiddleware)

# Register routes
app.include_router(webhook.router)


# Global exception handler to catch and log all errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and log them"""
    import traceback
    with open("error.log", "a") as f:
        f.write(f"Exception for path {request.url.path}:\n")
        f.write(traceback.format_exc())
        f.write("\n")

    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    logger.info(
        "app_starting",
        env=settings.app_env,
        supabase_url=settings.supabase_url
    )

    # Initialize Supabase client (validates connection)
    try:
        get_supabase_client()
        logger.info("supabase_connected")
    except Exception as e:
        logger.error("supabase_connection_failed", error=str(e))
        raise


@app.get("/healthz")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "env": settings.app_env
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Vehicle Diagnosis Assistant",
        "version": "2.0.0",
        "docs": "/docs"
    }
