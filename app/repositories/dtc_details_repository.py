"""
Repository for DTC detail tables (vehicles, repair_steps, parts,
common_symptoms, related_codes).

Provides read-only access to enriched diagnostic data keyed to obd_codes.
"""
from typing import Optional
from supabase import Client
from app.core.logging import logger


class DTCDetailsRepository:
    """Repository for DTC detail lookups"""

    def __init__(self, client: Client):
        self.client = client

    # ========================================================================
    # VEHICLES - Which vehicles does a code apply to?
    # ========================================================================

    def get_vehicles_for_code(self, code: str) -> list[dict]:
        """
        Get vehicle fitment data for a DTC code.

        Args:
            code: DTC code (e.g., "P0420")

        Returns:
            List of vehicle dicts with make, model, year_start, year_end, engine
            Empty list if code not found or no vehicles defined
        """
        try:
            response = (
                self.client.table("vehicles")
                .select("*")
                .eq("code_id", code.upper())
                .order("make, model, year_start")
                .execute()
            )

            logger.info(
                "vehicles_retrieved",
                code=code,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_vehicles_failed",
                code=code,
                error=str(e)
            )
            return []

    def get_vehicles_for_code_filtered(
        self,
        code: str,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None
    ) -> list[dict]:
        """
        Get vehicle fitment data with optional filters.

        Args:
            code: DTC code
            make: Optional make filter (case-insensitive)
            model: Optional model filter (case-insensitive)
            year: Optional year (checks if year is within year_start..year_end)

        Returns:
            Filtered list of vehicle dicts
        """
        try:
            query = (
                self.client.table("vehicles")
                .select("*")
                .eq("code_id", code.upper())
            )

            if make:
                query = query.ilike("make", make)
            if model:
                query = query.ilike("model", model)
            if year:
                # Year must be within the range [year_start, year_end]
                query = query.lte("year_start", year).gte("year_end", year)

            response = query.order("make, model, year_start").execute()

            logger.info(
                "vehicles_filtered_retrieved",
                code=code,
                make=make,
                model=model,
                year=year,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_vehicles_filtered_failed",
                code=code,
                error=str(e)
            )
            return []

    # ========================================================================
    # REPAIR STEPS - Step-by-step repair instructions
    # ========================================================================

    def get_repair_steps_for_code(self, code: str) -> list[dict]:
        """
        Get repair steps for a DTC code, ordered by step_number.

        Args:
            code: DTC code (e.g., "P0420")

        Returns:
            List of repair step dicts with step_number and instruction
            Empty list if code not found or no steps defined
        """
        try:
            response = (
                self.client.table("repair_steps")
                .select("*")
                .eq("code_id", code.upper())
                .order("step_number")
                .execute()
            )

            logger.info(
                "repair_steps_retrieved",
                code=code,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_repair_steps_failed",
                code=code,
                error=str(e)
            )
            return []

    # ========================================================================
    # PARTS - Required parts for repair
    # ========================================================================

    def get_parts_for_code(self, code: str) -> list[dict]:
        """
        Get parts required for repairing a DTC code.

        Args:
            code: DTC code (e.g., "P0420")

        Returns:
            List of part dicts with part_name and part_number
            Empty list if code not found or no parts defined
        """
        try:
            response = (
                self.client.table("parts")
                .select("*")
                .eq("code_id", code.upper())
                .order("part_name")
                .execute()
            )

            logger.info(
                "parts_retrieved",
                code=code,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_parts_failed",
                code=code,
                error=str(e)
            )
            return []

    # ========================================================================
    # COMMON SYMPTOMS - What drivers experience
    # ========================================================================

    def get_symptoms_for_code(self, code: str) -> list[dict]:
        """
        Get common symptoms for a DTC code.

        Args:
            code: DTC code (e.g., "P0420")

        Returns:
            List of symptom dicts with symptom text
            Empty list if code not found or no symptoms defined
        """
        try:
            response = (
                self.client.table("common_symptoms")
                .select("*")
                .eq("code_id", code.upper())
                .order("symptom")
                .execute()
            )

            logger.info(
                "symptoms_retrieved",
                code=code,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_symptoms_failed",
                code=code,
                error=str(e)
            )
            return []

    # ========================================================================
    # RELATED CODES - Codes that often appear together
    # ========================================================================

    def get_related_codes_for_code(self, code: str) -> list[dict]:
        """
        Get related DTC codes that often appear with this code.

        Args:
            code: DTC code (e.g., "P0420")

        Returns:
            List of related code dicts with related_code text
            Empty list if code not found or no related codes defined
        """
        try:
            response = (
                self.client.table("related_codes")
                .select("*")
                .eq("code_id", code.upper())
                .order("related_code")
                .execute()
            )

            logger.info(
                "related_codes_retrieved",
                code=code,
                count=len(response.data) if response.data else 0
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(
                "get_related_codes_failed",
                code=code,
                error=str(e)
            )
            return []

    # ========================================================================
    # AGGREGATE - Get all details for a code in one call
    # ========================================================================

    def get_all_details_for_code(
        self,
        code: str,
        vehicle_filter: Optional[dict] = None
    ) -> dict:
        """
        Get all enriched details for a DTC code in a single call.

        Args:
            code: DTC code (e.g., "P0420")
            vehicle_filter: Optional dict with 'make', 'model', 'year'
                          to filter vehicles

        Returns:
            Dict with keys:
                - vehicles: list[dict]
                - repair_steps: list[dict]
                - parts: list[dict]
                - symptoms: list[dict]
                - related_codes: list[dict]
        """
        code_upper = code.upper()

        # Get vehicles with optional filter
        if vehicle_filter:
            vehicles = self.get_vehicles_for_code_filtered(
                code_upper,
                make=vehicle_filter.get('make'),
                model=vehicle_filter.get('model'),
                year=vehicle_filter.get('year')
            )
        else:
            vehicles = self.get_vehicles_for_code(code_upper)

        # Get all other details
        result = {
            'code': code_upper,
            'vehicles': vehicles,
            'repair_steps': self.get_repair_steps_for_code(code_upper),
            'parts': self.get_parts_for_code(code_upper),
            'symptoms': self.get_symptoms_for_code(code_upper),
            'related_codes': self.get_related_codes_for_code(code_upper)
        }

        logger.info(
            "all_details_retrieved",
            code=code,
            vehicles_count=len(result['vehicles']),
            steps_count=len(result['repair_steps']),
            parts_count=len(result['parts']),
            symptoms_count=len(result['symptoms']),
            related_count=len(result['related_codes'])
        )

        return result

    # ========================================================================
    # UTILITY - Check if code has any enriched data
    # ========================================================================

    def has_enriched_data(self, code: str) -> dict:
        """
        Quick check if a code has any enriched data without fetching it all.

        Args:
            code: DTC code

        Returns:
            Dict with boolean flags:
                - has_vehicles
                - has_repair_steps
                - has_parts
                - has_symptoms
                - has_related_codes
        """
        code_upper = code.upper()

        try:
            # Quick count queries (limit 1 for efficiency)
            has_vehicles = len(
                self.client.table("vehicles")
                .select("id", count="exact")
                .eq("code_id", code_upper)
                .limit(1)
                .execute()
                .data
            ) > 0

            has_repair_steps = len(
                self.client.table("repair_steps")
                .select("id", count="exact")
                .eq("code_id", code_upper)
                .limit(1)
                .execute()
                .data
            ) > 0

            has_parts = len(
                self.client.table("parts")
                .select("id", count="exact")
                .eq("code_id", code_upper)
                .limit(1)
                .execute()
                .data
            ) > 0

            has_symptoms = len(
                self.client.table("common_symptoms")
                .select("id", count="exact")
                .eq("code_id", code_upper)
                .limit(1)
                .execute()
                .data
            ) > 0

            has_related_codes = len(
                self.client.table("related_codes")
                .select("id", count="exact")
                .eq("code_id", code_upper)
                .limit(1)
                .execute()
                .data
            ) > 0

            result = {
                'has_vehicles': has_vehicles,
                'has_repair_steps': has_repair_steps,
                'has_parts': has_parts,
                'has_symptoms': has_symptoms,
                'has_related_codes': has_related_codes,
                'has_any': any([
                    has_vehicles,
                    has_repair_steps,
                    has_parts,
                    has_symptoms,
                    has_related_codes
                ])
            }

            logger.debug(
                "enriched_data_check",
                code=code,
                **result
            )

            return result

        except Exception as e:
            logger.error(
                "has_enriched_data_failed",
                code=code,
                error=str(e)
            )
            return {
                'has_vehicles': False,
                'has_repair_steps': False,
                'has_parts': False,
                'has_symptoms': False,
                'has_related_codes': False,
                'has_any': False
            }
