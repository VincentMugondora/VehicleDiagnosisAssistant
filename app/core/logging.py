import structlog


from app.core.config import settings

def setup_logging():
    """Configure structlog with JSON output for production observability"""
    if settings.app_env == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            renderer
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )


logger = structlog.get_logger()
