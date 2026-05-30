import asyncio
import httpx
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import structlog
import threading
import time

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.get("/error")
async def root():
    raise ValueError("Test error")

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

if __name__ == "__main__":
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(1)
    try:
        response = httpx.get("http://127.0.0.1:8001/error")
        print(response.status_code)
        print(response.json())
    except Exception as e:
        print("HTTPX Error:", e)
    time.sleep(1)
