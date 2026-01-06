import os
from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL", "mongodb://localhost:27017")
_DB_NAME = os.getenv("MONGODB_DB", "vehicle_diag")

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(_MONGODB_URI)
    return _client


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    client = _get_client()
    db = client[_DB_NAME]
    try:
        yield db
    finally:
        # Do not close client per request; reuse globally
        pass


async def init_db() -> None:
    """Create indexes for collections used by the app."""
    db = _get_client()[_DB_NAME]
    # obd_codes: unique code
    await db["obd_codes"].create_index("code", unique=True)
    # message_logs: phone_number + created_at
    await db["message_logs"].create_index("phone_number")
    await db["message_logs"].create_index("created_at")
