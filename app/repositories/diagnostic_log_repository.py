from supabase import Client
from app.core.config import settings


class DiagnosticLogRepository:
    """Repository for diagnostic audit logs (append-only)"""

    def __init__(self, client: Client | None):
        self.client = client

    def insert_diagnostic(
        self,
        code: str,
        vehicle: str,
        source: str,
        confidence: float
    ):
        """
        Insert diagnostic audit log entry.

        Args:
            code: OBD code
            vehicle: Concatenated vehicle string (make model year engine)
            source: Source of diagnosis ("local_db", "vehicle_override", "external")
            confidence: Confidence score (0.0-1.0)
        """
        # Skip logging in fallback mode
        if not settings.supabase_enabled or self.client is None:
            return

        self.client.table("diagnostic_logs").insert({
            "code": code,
            "vehicle": vehicle,
            "source": source,
            "confidence": confidence
        }).execute()
