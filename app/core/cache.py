"""
Simple in-memory cache for frequently accessed data.

Reduces database queries for hot paths like OBD code lookups.
"""
from functools import lru_cache
from typing import Optional, Dict, Any

# LRU cache for OBD codes (500 most recent)
@lru_cache(maxsize=500)
def cached_obd_lookup(code: str, _cache_key: str = "v1") -> Optional[Dict[str, Any]]:
    """
    Cached OBD code lookup.

    Note: This is a placeholder - actual implementation should be in repository.
    The _cache_key parameter allows cache invalidation by changing the key.
    """
    return None  # Actual lookup happens in repository


def clear_obd_cache():
    """Clear the OBD code cache."""
    cached_obd_lookup.cache_clear()
