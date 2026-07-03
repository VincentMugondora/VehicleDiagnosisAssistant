from supabase import Client
from app.core.config import settings
from app.repositories.fallback_obd_data import get_fallback_code


class OBDRepository:
    """Repository for OBD code lookups and vehicle overrides"""

    def __init__(self, client: Client | None):
        self.client = client

    def get_by_code(self, code: str) -> dict | None:
        """
        Lookup OBD code in knowledge base.

        Args:
            code: OBD code (e.g., "P0420")

        Returns:
            Dict with code info or None if not found
        """
        # Use fallback data if Supabase is disabled
        if not settings.supabase_enabled or self.client is None:
            return get_fallback_code(code)

        result = self.client.table("obd_codes")\
            .select("*")\
            .eq("code", code.upper())\
            .execute()
        return result.data[0] if result.data else None

    def get_vehicle_override(
        self,
        code: str,
        make: str,
        model: str,
        year: str,
        engine: str
    ) -> dict | None:
        """
        Lookup vehicle-specific override for OBD code.

        Args:
            code: OBD code
            make: Vehicle make (normalized lowercase)
            model: Vehicle model (normalized lowercase)
            year: Vehicle year
            engine: Engine size/type (normalized lowercase)

        Returns:
            Dict with override info or None if not found
        """
        # No vehicle overrides in fallback mode
        if not settings.supabase_enabled or self.client is None:
            return None

        result = self.client.table("vehicle_overrides")\
            .select("*")\
            .eq("code", code.upper())\
            .eq("make", make.lower())\
            .eq("model", model.lower())\
            .eq("year", year)\
            .eq("engine", engine.lower())\
            .execute()
        return result.data[0] if result.data else None

    def list_by_system(self, system: str) -> list[dict]:
        """
        List all OBD codes for a specific system.

        Args:
            system: System name (e.g., "Fuel & Air", "Ignition")

        Returns:
            List of OBD code dicts
        """
        result = self.client.table("obd_codes")\
            .select("*")\
            .eq("system", system)\
            .execute()
        return result.data

    def insert_code(self, code_data: dict) -> dict:
        """
        Insert a new OBD code into the database.
        Uses upsert to avoid duplicates.

        Args:
            code_data: Dict with code information

        Returns:
            Inserted/updated code data
        """
        result = self.client.table("obd_codes")\
            .upsert(code_data, on_conflict="code")\
            .execute()
        return result.data[0] if result.data else None
