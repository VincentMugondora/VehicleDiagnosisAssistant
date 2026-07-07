"""
Shared HTTP clients for connection pooling.

Reusing clients across requests enables connection pooling,
reduces TLS handshake overhead, and prevents file descriptor exhaustion.
"""
import httpx
from app.core.logging import logger

# Global HTTP clients (lazily initialized)
_twilio_client: httpx.AsyncClient | None = None
_image_client: httpx.AsyncClient | None = None
_web_client: httpx.AsyncClient | None = None


def get_twilio_client() -> httpx.AsyncClient:
    """
    Get shared Twilio HTTP client.

    Reuses connections for Twilio API calls.
    """
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
        logger.info("twilio_client_initialized")
    return _twilio_client


def get_image_client() -> httpx.AsyncClient:
    """
    Get shared image download HTTP client.

    Reuses connections for image downloads.
    """
    global _image_client
    if _image_client is None:
        _image_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=10
            ),
            follow_redirects=True
        )
        logger.info("image_client_initialized")
    return _image_client


def get_web_client() -> httpx.AsyncClient:
    """
    Get shared web search/scraping HTTP client.

    Reuses connections for web searches and page fetches.
    """
    global _web_client
    if _web_client is None:
        _web_client = httpx.AsyncClient(
            timeout=15.0,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=10
            ),
            follow_redirects=True
        )
        logger.info("web_client_initialized")
    return _web_client


async def close_all_clients():
    """Close all HTTP clients on shutdown."""
    global _twilio_client, _image_client, _web_client

    if _twilio_client:
        await _twilio_client.aclose()
        _twilio_client = None
        logger.info("twilio_client_closed")

    if _image_client:
        await _image_client.aclose()
        _image_client = None
        logger.info("image_client_closed")

    if _web_client:
        await _web_client.aclose()
        _web_client = None
        logger.info("web_client_closed")
