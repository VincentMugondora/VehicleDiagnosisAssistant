from datetime import UTC, datetime, timedelta
from app.repositories.session_repository import SessionRepository
from app.repositories.message_log_repository import MessageLogRepository
from app.models.session import SessionState
from app.core.errors import MessageAlreadyProcessed
from app.core.config import settings
from app.core.logging import logger


class SessionManager:
    """
    Manages conversation sessions and message idempotency.

    Per CLAUDE.md requirements:
    - 30-minute session TTL
    - Message deduplication via message_id
    - Session state persistence
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageLogRepository
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo

    def check_message_idempotency(self, message_id: str):
        """
        Check if message has already been processed.

        Args:
            message_id: WhatsApp message ID

        Raises:
            MessageAlreadyProcessed: If message_id exists in logs
        """
        if self.message_repo.message_exists(message_id):
            logger.warning(
                "duplicate_message_detected",
                message_id=message_id
            )
            raise MessageAlreadyProcessed(
                f"Message {message_id} already processed"
            )

    def load_session(self, phone_hash: str) -> SessionState:
        """
        Load or create conversation session for a user.

        Args:
            phone_hash: SHA-256 hash of phone number

        Returns:
            SessionState (existing or new)
        """
        session = self.session_repo.get_by_phone_hash(phone_hash)

        if not session:
            logger.info("session_created", phone_hash=phone_hash)
            return SessionState(
                phone_hash=phone_hash,
                last_active=datetime.now(UTC)
            )

        # Check TTL — ensure last_active is tz-aware for comparison
        ttl_delta = timedelta(seconds=settings.session_ttl_seconds)
        last_active = session.last_active
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=UTC)
        if datetime.now(UTC) - last_active > ttl_delta:
            logger.info(
                "session_expired",
                phone_hash=phone_hash,
                last_active=session.last_active.isoformat()
            )
            # Expired, create new
            return SessionState(
                phone_hash=phone_hash,
                last_active=datetime.now(UTC)
            )

        logger.info(
            "session_loaded",
            phone_hash=phone_hash,
            turn_count=len(session.turns)
        )
        return session

    def save_session(self, session: SessionState):
        """
        Persist session state with updated timestamp.

        Args:
            session: SessionState to save
        """
        session.last_active = datetime.now(UTC)
        self.session_repo.upsert_session(session)
        logger.info(
            "session_saved",
            phone_hash=session.phone_hash,
            turn_count=len(session.turns)
        )
