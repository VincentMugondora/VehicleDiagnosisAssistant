from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import RequestContextMiddleware
from app.middleware.size_limit import RequestSizeLimitMiddleware
from app.db.client import get_supabase_client
from app.api.routes import webhook, payments, chat

# Setup structured logging
setup_logging()

app = FastAPI(
    title="Vehicle Diagnosis Assistant API",
    version="2.0.0",
    description="WhatsApp-based OBD-II diagnostic assistant with PostgreSQL/Supabase backend and Paynow payments"
)

# Mount static files for local image hosting
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info("static_files_mounted", path=str(static_path))

# Register middleware (order matters: first added = outermost = runs first)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

# Register routes
app.include_router(webhook.router)
app.include_router(payments.router)
app.include_router(chat.router)


# Global exception handler to catch and log all errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and log them"""
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
        content={"error": "Internal server error"}
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
    from app.core.config import check_supabase_connectivity

    # Check if Supabase is reachable
    if not check_supabase_connectivity(settings.supabase_url):
        logger.warning(
            "supabase_unreachable",
            url=settings.supabase_url,
            message="Supabase is not reachable. Running in fallback mode without database."
        )
        settings.supabase_enabled = False
        return

    try:
        get_supabase_client()
        logger.info("supabase_connected")
        settings.supabase_enabled = True

        # Start payment poller (only if Paynow configured)
        if settings.paynow_integration_id and settings.paynow_integration_key:
            from app.services.payment_poller import start_payment_poller
            await start_payment_poller()
            logger.info("payment_poller_enabled")
        else:
            logger.info("payment_poller_disabled_no_credentials")

    except Exception as e:
        logger.error("supabase_connection_failed", error=str(e))
        logger.warning("running_without_supabase", message="Continuing in fallback mode")
        settings.supabase_enabled = False


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    try:
        from app.services.payment_poller import stop_payment_poller
        stop_payment_poller()
        logger.info("payment_poller_stopped")
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    # Close shared HTTP clients
    try:
        from app.core.http_clients import close_all_clients
        await close_all_clients()
        logger.info("http_clients_closed")
    except Exception:  # pylint: disable=broad-exception-caught
        pass


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
    """Serve the chat UI"""
    return FileResponse(str(static_path / "chat.html"))
