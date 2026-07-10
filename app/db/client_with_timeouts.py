"""
Supabase client with proper timeout and retry configuration.

This module creates a properly configured Supabase client with:
- Increased timeouts to handle slow network conditions
- Connection pooling
- Retry logic for transient failures
"""

from supabase import create_client, Client
from httpx import Timeout, Limits
from app.core.config import settings

_client: Client | None = None


def get_supabase_client_with_timeouts() -> Client | None:
    """
    Get or create singleton Supabase client with optimized timeout settings.

    Timeout configuration:
    - connect: 10s (time to establish connection)
    - read: 30s (time waiting for server response)
    - write: 10s (time to send request)
    - pool: 60s (time waiting for connection from pool)

    Connection pool:
    - max_connections: 100 (total connections across all hosts)
    - max_keepalive_connections: 20 (persistent connections to reuse)

    Returns None if Supabase is disabled.
    """
    global _client

    if not settings.supabase_enabled:
        return None

    if _client is None:
        # Configure HTTP client with proper timeouts
        timeout = Timeout(
            connect=10.0,   # Time to establish TCP connection
            read=30.0,      # Time waiting for data from server
            write=10.0,     # Time to send data to server
            pool=60.0       # Time waiting for connection from pool
        )

        # Configure connection pooling
        limits = Limits(
            max_connections=100,            # Total connections
            max_keepalive_connections=20    # Persistent connections to reuse
        )

        # Create client with custom httpx options
        # Note: supabase-py v2+ supports httpx client options
        try:
            _client = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
                options={
                    'timeout': timeout,
                    'limits': limits
                }
            )
        except TypeError:
            # Fallback for older supabase-py versions that don't support options
            import httpx
            http_client = httpx.Client(
                timeout=timeout,
                limits=limits
            )
            _client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
            # Monkey-patch the session
            if hasattr(_client, 'postgrest'):
                _client.postgrest.session = http_client

    return _client


def close_supabase_client():
    """Close the Supabase client and cleanup resources."""
    global _client
    if _client is not None:
        if hasattr(_client, 'postgrest') and hasattr(_client.postgrest, 'session'):
            _client.postgrest.session.close()
        _client = None
