from supabase import create_client, Client, ClientOptions
from app.core.config import settings

_client: Client | None = None


def get_supabase_client() -> Client | None:
    """
    Get or create singleton Supabase client with optimized timeout settings.

    Timeout configuration:
    - connect: 10s (time to establish connection)
    - read: 30s (time waiting for server response - increased from default 5s)
    - write: 10s (time to send request)
    - pool: 60s (time waiting for connection from pool)

    Returns None if Supabase is disabled.
    """
    global _client

    if not settings.supabase_enabled:
        return None

    if _client is None:
        # Configure client with increased timeouts to handle intermittent connectivity
        options = ClientOptions(
            postgrest_client_timeout=30,  # 30s read timeout (up from default 5s)
            storage_client_timeout=30,
            schema="public"
        )

        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
            options=options
        )
    return _client
