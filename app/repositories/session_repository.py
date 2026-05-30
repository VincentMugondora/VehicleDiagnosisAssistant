from datetime import datetime
from supabase import Client
from app.models.session import SessionState


class SessionRepository:
    """Repository for conversation session state"""

    def __init__(self, client: Client):
        self.client = client

    def get_by_phone_hash(self, phone_hash: str) -> SessionState | None:
        """
        Load session state by phone hash.

        Args:
            phone_hash: SHA-256 hash of phone number

        Returns:
            SessionState or None if not found
        """
        result = self.client.table("conversation_sessions")\
            .select("*")\
            .eq("phone_hash", phone_hash)\
            .execute()

        if not result.data:
            return None

        # Extract state JSONB and reconstruct SessionState
        return SessionState(**result.data[0]["state"])

    def upsert_session(self, session: SessionState):
        """
        Save or update session state.

        Args:
            session: SessionState to persist
        """
        # Serialize datetime objects to ISO format strings
        session_dict = session.model_dump(mode='json')

        self.client.table("conversation_sessions")\
            .upsert({
                "phone_hash": session.phone_hash,
                "state": session_dict,
                "last_active": datetime.utcnow().isoformat()
            }, on_conflict="phone_hash")\
            .execute()
