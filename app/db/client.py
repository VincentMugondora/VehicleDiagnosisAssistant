from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase_client() -> Client | None:
    """Get or create singleton Supabase client. Returns None if Supabase is disabled."""
    global _client

    if not settings.supabase_enabled:
        return None

    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _client
