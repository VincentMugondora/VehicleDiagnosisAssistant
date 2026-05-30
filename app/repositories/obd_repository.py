from supabase import Client


class OBDRepository:
    """Repository for OBD code lookups and vehicle overrides"""

    def __init__(self, client: Client):
        self.client = client

    def get_by_code(self, code: str) -> dict | None:
        """
        Lookup OBD code in knowledge base.

        Args:
            code: OBD code (e.g., "P0420")

        Returns:
            Dict with code info or None if not found
        """
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
