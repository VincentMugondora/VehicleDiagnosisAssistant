from datetime import datetime, timedelta
from supabase import Client
from app.core.config import settings
from app.db.retry_utils import with_retry, with_retry_default_none


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
            Count of messages (0 if DB unavailable)
        """
        if not settings.supabase_enabled or self.client is None:
            return 0  # No rate limiting in fallback mode

        window_start = (datetime.utcnow() - timedelta(days=days)).isoformat()

        result = with_retry_default_none(
            lambda: self.client.table("message_logs")
                .select("*", count="exact")
                .eq("phone_hash", phone_hash)
                .gte("created_at", window_start)
                .execute(),
            operation_name=f"count_recent_messages_{phone_hash[:8]}"
        )

        return result.count if result else 0

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

        try:
            with_retry(
                lambda: self.client.table("message_logs").insert({
                    "message_id": message_id,
                    "phone_hash": phone_hash,
                    "request_id": request_id,
                    "session_id": session_id,
                    "request_text": request_text,
                    "response_text": response_text,
                    "code": code
                }).execute(),
                operation_name="insert_message_audit"
            )
        except Exception:
            # Fallback to in-memory tracking if audit insert fails
            self._processed_messages.add(message_id)

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

        result = with_retry_default_none(
            lambda: self.client.table("message_logs")
                .select("id")
                .eq("message_id", message_id)
                .execute(),
            operation_name="check_message_exists"
        )

        if result is None:
            # DB unavailable - fall back to in-memory check
            return message_id in self._processed_messages

        return len(result.data) > 0
