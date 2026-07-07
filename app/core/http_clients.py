"""
HTTP client utilities with connection pooling and retry logic.
"""
import httpx
from functools import lru_cache
from app.core.logging import logger


@lru_cache(maxsize=1)
def get_twilio_client() -> httpx.AsyncClient:
    """
    Get or create a persistent Twilio HTTP client with connection pooling.

    Benefits:
    - Reuses TCP connections (faster)
    - Handles connection drops gracefully
    - Automatic retries on transient errors

    Returns:
        Configured httpx.AsyncClient instance
    """
    transport = httpx.AsyncHTTPTransport(
        retries=2,
        http2=False
    )

    client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(30.0, connect=5.0),
        limits=httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        ),
        follow_redirects=True
    )

    logger.info("twilio_http_client_created")
    return client


@lru_cache(maxsize=1)
def get_baileys_client() -> httpx.AsyncClient:
    """
    Get or create a persistent Baileys HTTP client for outbound messaging.

    Returns:
        Configured httpx.AsyncClient instance
    """
    transport = httpx.AsyncHTTPTransport(
        retries=1,
        http2=False
    )

    client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(20.0, connect=3.0),
        limits=httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        ),
        follow_redirects=False
    )

    logger.info("baileys_http_client_created")
    return client
