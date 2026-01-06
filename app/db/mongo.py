import os
from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(uri)
    return _client


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    client = _get_client()
    db_name = os.getenv("MONGODB_DB", "vehicle_diag")
    db = client[db_name]
    try:
        yield db
    finally:
        # Do not close client per request; reuse globally
        pass


async def init_db() -> None:
    """Create indexes for collections used by the app."""
    db_name = os.getenv("MONGODB_DB", "vehicle_diag")
    db = _get_client()[db_name]
    # obd_codes: unique code
    await db["obd_codes"].create_index("code", unique=True)
    # message_logs: phone_number + created_at
    await db["message_logs"].create_index("phone_number")
    await db["message_logs"].create_index("created_at")
