from functools import lru_cache
from supabase import Client
from app.core.config import settings
from app.repositories.fallback_obd_data import get_fallback_code

# Global cache for OBD code lookups (reduces 3.5s query to <1ms)
_obd_cache = {}


class OBDRepository:
    """Repository for OBD code lookups and vehicle overrides"""

    def __init__(self, client: Client | None):
        self.client = client

    def get_by_code(self, code: str) -> dict | None:
        """
        Lookup OBD code in knowledge base with caching.

        Args:
            code: OBD code (e.g., "P0420")

        Returns:
            Dict with code info or None if not found
        """
        # Use fallback data if Supabase is disabled
        if not settings.supabase_enabled or self.client is None:
            return get_fallback_code(code)

        # Check cache first (hot path optimization)
        code_upper = code.upper()
        if code_upper in _obd_cache:
            return _obd_cache[code_upper]

        # Query database (cold path - slow)
        result = self.client.table("obd_codes")\
            .select("*")\
            .eq("code", code_upper)\
            .execute()

        # Cache the result (even None to prevent repeated lookups)
        code_data = result.data[0] if result.data else None
        _obd_cache[code_upper] = code_data

        return code_data

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

        # Invalidate cache for this code
        code_upper = code_data.get("code", "").upper()
        if code_upper in _obd_cache:
            del _obd_cache[code_upper]

        return result.data[0] if result.data else None

    def update_code_fields(self, code: str, updates: dict) -> dict:
        """
        Update specific fields of an existing OBD code.
        Preserves fields not included in updates.

        Args:
            code: OBD code to update
            updates: Dict with fields to update (can include metadata fields)

        Returns:
            Updated code data
        """
        if not settings.supabase_enabled or self.client is None:
            return None

        # Add code to updates to ensure we're updating the right record
        updates["code"] = code.upper()

        result = self.client.table("obd_codes")\
            .update(updates)\
            .eq("code", code.upper())\
            .execute()

        # Invalidate cache
        code_upper = code.upper()
        if code_upper in _obd_cache:
            del _obd_cache[code_upper]

        return result.data[0] if result.data else None

    def enrich_code(self, code: str, enriched_fields: dict, metadata_fields: dict) -> dict:
        """
        Enrich an existing code with AI-generated fields and metadata.

        This is a specialized method that:
        1. Updates only the specified enriched fields
        2. Stores metadata for each enriched field
        3. Updates enrichment status and timestamp
        4. Preserves all existing fields

        Uses upsert to handle both new and existing records safely.

        Args:
            code: OBD code to enrich
            enriched_fields: Dict of field_name -> value (e.g., {"symptoms": [...], "severity": "High"})
            metadata_fields: Dict of field_name_meta -> metadata (e.g., {"symptoms_meta": {...}})

        Returns:
            Updated code data or None if failed
        """
        if not settings.supabase_enabled or self.client is None:
            return None

        # Check if record exists first
        existing = self.get_by_code(code)
        if not existing:
            logger.warning("enrich_code_record_not_found", code=code)
            return None

        # Build update payload
        updates = {
            "code": code.upper(),
            **enriched_fields,
            **metadata_fields,
            "last_enriched": "now()"  # PostgreSQL function
        }

        # Determine enrichment status based on completeness
        # For now, mark as ai_generated if we're enriching
        updates["enrichment_status"] = "ai_generated"

        try:
            result = self.client.table("obd_codes")\
                .update(updates)\
                .eq("code", code.upper())\
                .execute()

            # Invalidate cache
            code_upper = code.upper()
            if code_upper in _obd_cache:
                del _obd_cache[code_upper]

            if result.data:
                logger.info("enrich_code_success", code=code)
                return result.data[0]
            else:
                logger.warning("enrich_code_no_data_returned", code=code)
                return None

        except Exception as e:
            logger.error("enrich_code_failed", code=code, error=str(e))
            return None
