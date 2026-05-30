from supabase import Client


class DiagnosticLogRepository:
    """Repository for diagnostic audit logs (append-only)"""

    def __init__(self, client: Client):
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
        self.client.table("diagnostic_logs").insert({
            "code": code,
            "vehicle": vehicle,
            "source": source,
            "confidence": confidence
        }).execute()
