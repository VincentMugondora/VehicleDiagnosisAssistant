from datetime import datetime, timedelta
from supabase import Client
from app.core.config import settings


class MessageLogRepository:
    """Repository for message audit logs and rate limiting"""

    def __init__(self, client: Client | None):
        self.client = client
        self._processed_messages = set()  # In-memory fallback for idempotency

    def count_recent(self, phone_hash: str, days: int) -> int:
        """
        Count messages from a phone number within a time window.

        Args:
            phone_hash: SHA-256 hash of phone number
            days: Number of days to look back

        Returns:
            Count of messages
        """
        if not settings.supabase_enabled or self.client is None:
            return 0  # No rate limiting in fallback mode

        window_start = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = self.client.table("message_logs")\
            .select("*", count="exact")\
            .eq("phone_hash", phone_hash)\
            .gte("created_at", window_start)\
            .execute()
        return result.count or 0

    def insert_audit(
        self,
        message_id: str,
        phone_hash: str,
        request_id: str,
        session_id: str | None,
        request_text: str,
        response_text: str,
        code: str | None
    ):
        """
        Insert message audit log entry.

        Args:
            message_id: WhatsApp message ID
            phone_hash: SHA-256 hash of phone number
            request_id: Request tracing ID
            session_id: Session ID (if session exists)
            request_text: User message
            response_text: Bot response
            code: OBD code (if extracted)
        """
        if not settings.supabase_enabled or self.client is None:
            self._processed_messages.add(message_id)
            return  # Skip audit logging in fallback mode

        self.client.table("message_logs").insert({
            "message_id": message_id,
            "phone_hash": phone_hash,
            "request_id": request_id,
            "session_id": session_id,
            "request_text": request_text,
            "response_text": response_text,
            "code": code
        }).execute()

    def message_exists(self, message_id: str) -> bool:
        """
        Check if message has already been processed (idempotency check).

        Args:
            message_id: WhatsApp message ID

        Returns:
            True if message exists in logs
        """
        if not settings.supabase_enabled or self.client is None:
            # Use in-memory set for idempotency in fallback mode
            return message_id in self._processed_messages

        result = self.client.table("message_logs")\
            .select("id")\
            .eq("message_id", message_id)\
            .execute()
        return len(result.data) > 0
