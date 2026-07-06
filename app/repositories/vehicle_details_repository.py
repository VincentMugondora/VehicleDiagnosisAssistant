"""
Repository for accessing vehicle-specific OBD code details.
Handles vehicles, repair steps, parts, symptoms, and related codes.
"""
from typing import List, Dict, Optional, Any
from uuid import UUID
from app.db.supabase_client import get_supabase_client
import structlog

logger = structlog.get_logger(__name__)


class VehicleDetailsRepository:
    """Repository for vehicle-specific OBD code information."""

    def __init__(self):
        self.client = get_supabase_client()

    # =========================================================================
    # VEHICLES
    # =========================================================================

    def find_vehicle(
        self,
        make: str,
        model: str,
        year: int,
        engine: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a vehicle by make, model, year, and optional engine.

        Args:
            make: Vehicle make (e.g., 'Toyota')
            model: Vehicle model (e.g., 'Camry')
            year: Vehicle year (e.g., 2015)
            engine: Optional engine specification (e.g., '2.5L 4-cylinder')

        Returns:
            Vehicle dict or None if not found
        """
        try:
            query = self.client.table("vehicles").select("*").ilike("make", make).ilike("model", model).eq("year", year)

            if engine:
                query = query.ilike("engine", engine)

            response = query.limit(1).execute()

            if response.data and len(response.data) > 0:
                logger.info("vehicle_found", make=make, model=model, year=year, engine=engine)
                return response.data[0]

            logger.debug("vehicle_not_found", make=make, model=model, year=year, engine=engine)
            return None

        except Exception as e:
            logger.error("find_vehicle_error", error=str(e), make=make, model=model, year=year)
            return None

    def get_vehicle_by_id(self, vehicle_id: UUID) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID."""
        try:
            response = self.client.table("vehicles").select("*").eq("id", str(vehicle_id)).single().execute()
            return response.data
        except Exception as e:
            logger.error("get_vehicle_error", error=str(e), vehicle_id=str(vehicle_id))
            return None

    def list_vehicles(self, make: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List vehicles, optionally filtered by make.

        Args:
            make: Optional make to filter by
            limit: Maximum number of results (default: 50)

        Returns:
            List of vehicle dicts
        """
        try:
            query = self.client.table("vehicles").select("*")

            if make:
                query = query.ilike("make", make)

            response = query.limit(limit).order("make, model, year").execute()
            return response.data or []

        except Exception as e:
            logger.error("list_vehicles_error", error=str(e))
            return []

    # =========================================================================
    # REPAIR STEPS
    # =========================================================================

    def get_repair_steps(
        self,
        code: str,
        vehicle_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get repair steps for an OBD code, optionally filtered by vehicle.

        Args:
            code: OBD code (e.g., 'P0420')
            vehicle_id: Optional vehicle ID for vehicle-specific steps

        Returns:
            List of repair step dicts, ordered by step_number
        """
        try:
            # First get the code_id
            code_response = self.client.table("obd_codes").select("id").eq("code", code.upper()).single().execute()

            if not code_response.data:
                logger.warning("code_not_found_for_steps", code=code)
                return []

            code_id = code_response.data["id"]

            # Get repair steps
            query = self.client.table("repair_steps").select("*").eq("code_id", code_id)

            # Filter by vehicle: get vehicle-specific OR generic (vehicle_id IS NULL)
            if vehicle_id:
                # Use OR filter: vehicle_id = X OR vehicle_id IS NULL
                query = query.or_(f"vehicle_id.eq.{vehicle_id},vehicle_id.is.null")
            else:
                # Only generic steps
                query = query.is_("vehicle_id", "null")

            response = query.order("step_number").execute()

            logger.info(
                "repair_steps_retrieved",
                code=code,
                vehicle_id=str(vehicle_id) if vehicle_id else None,
                count=len(response.data or [])
            )

            return response.data or []

        except Exception as e:
            logger.error("get_repair_steps_error", error=str(e), code=code)
            return []

    # =========================================================================
    # PARTS
    # =========================================================================

    def get_parts(
        self,
        code: str,
        vehicle_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get parts needed for an OBD code repair.

        Args:
            code: OBD code (e.g., 'P0420')
            vehicle_id: Optional vehicle ID for vehicle-specific parts

        Returns:
            List of part dicts, ordered by OEM status and price
        """
        try:
            # Get code_id
            code_response = self.client.table("obd_codes").select("id").eq("code", code.upper()).single().execute()

            if not code_response.data:
                logger.warning("code_not_found_for_parts", code=code)
                return []

            code_id = code_response.data["id"]

            # Get parts
            query = self.client.table("parts").select("*").eq("code_id", code_id)

            if vehicle_id:
                query = query.or_(f"vehicle_id.eq.{vehicle_id},vehicle_id.is.null")
            else:
                query = query.is_("vehicle_id", "null")

            response = query.order("is_oem.desc, price_estimate_usd.asc.nullslast").execute()

            logger.info(
                "parts_retrieved",
                code=code,
                vehicle_id=str(vehicle_id) if vehicle_id else None,
                count=len(response.data or [])
            )

            return response.data or []

        except Exception as e:
            logger.error("get_parts_error", error=str(e), code=code)
            return []

    # =========================================================================
    # SYMPTOMS
    # =========================================================================

    def get_symptoms(self, code: str) -> List[Dict[str, Any]]:
        """
        Get common symptoms for an OBD code.

        Args:
            code: OBD code (e.g., 'P0420')

        Returns:
            List of symptom dicts, ordered by severity
        """
        try:
            # Get code_id
            code_response = self.client.table("obd_codes").select("id").eq("code", code.upper()).single().execute()

            if not code_response.data:
                logger.warning("code_not_found_for_symptoms", code=code)
                return []

            code_id = code_response.data["id"]

            # Get symptoms
            response = (
                self.client.table("common_symptoms")
                .select("*")
                .eq("code_id", code_id)
                .order("severity.desc, symptom")
                .execute()
            )

            logger.info("symptoms_retrieved", code=code, count=len(response.data or []))

            return response.data or []

        except Exception as e:
            logger.error("get_symptoms_error", error=str(e), code=code)
            return []

    # =========================================================================
    # RELATED CODES
    # =========================================================================

    def get_related_codes(self, code: str) -> List[Dict[str, Any]]:
        """
        Get codes related to the given OBD code.

        Args:
            code: OBD code (e.g., 'P0420')

        Returns:
            List of related code dicts
        """
        try:
            # Get code_id
            code_response = self.client.table("obd_codes").select("id").eq("code", code.upper()).single().execute()

            if not code_response.data:
                logger.warning("code_not_found_for_related", code=code)
                return []

            code_id = code_response.data["id"]

            # Get related codes
            response = (
                self.client.table("related_codes")
                .select("*")
                .eq("code_id", code_id)
                .order("related_code")
                .execute()
            )

            logger.info("related_codes_retrieved", code=code, count=len(response.data or []))

            return response.data or []

        except Exception as e:
            logger.error("get_related_codes_error", error=str(e), code=code)
            return []

    # =========================================================================
    # COMPLETE CODE DETAILS
    # =========================================================================

    def get_complete_code_details(
        self,
        code: str,
        vehicle_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get complete information for an OBD code including symptoms, steps, parts, and related codes.

        Args:
            code: OBD code (e.g., 'P0420')
            vehicle_context: Optional dict with keys: make, model, year, engine

        Returns:
            Dict containing all code details:
            {
                'code': str,
                'vehicle': Optional[Dict],
                'symptoms': List[Dict],
                'repair_steps': List[Dict],
                'parts': List[Dict],
                'related_codes': List[Dict]
            }
        """
        try:
            vehicle_id = None
            vehicle = None

            # Find vehicle if context provided
            if vehicle_context:
                make = vehicle_context.get("make")
                model = vehicle_context.get("model")
                year = vehicle_context.get("year")
                engine = vehicle_context.get("engine")

                if make and model and year:
                    vehicle = self.find_vehicle(make, model, year, engine)
                    if vehicle:
                        vehicle_id = UUID(vehicle["id"])

            # Get all details
            result = {
                "code": code.upper(),
                "vehicle": vehicle,
                "symptoms": self.get_symptoms(code),
                "repair_steps": self.get_repair_steps(code, vehicle_id),
                "parts": self.get_parts(code, vehicle_id),
                "related_codes": self.get_related_codes(code)
            }

            logger.info(
                "complete_details_retrieved",
                code=code,
                vehicle_matched=vehicle is not None,
                symptoms_count=len(result["symptoms"]),
                steps_count=len(result["repair_steps"]),
                parts_count=len(result["parts"]),
                related_count=len(result["related_codes"])
            )

            return result

        except Exception as e:
            logger.error("get_complete_details_error", error=str(e), code=code)
            return {
                "code": code.upper(),
                "vehicle": None,
                "symptoms": [],
                "repair_steps": [],
                "parts": [],
                "related_codes": []
            }

    # =========================================================================
    # FORMATTING HELPERS
    # =========================================================================

    def format_repair_steps_text(self, steps: List[Dict[str, Any]]) -> str:
        """
        Format repair steps as numbered text for WhatsApp messages.

        Args:
            steps: List of repair step dicts

        Returns:
            Formatted string with numbered steps
        """
        if not steps:
            return "No repair steps available for this code."

        lines = ["*Repair Steps:*\n"]

        for step in steps:
            step_num = step.get("step_number", "?")
            instruction = step.get("instruction", "No instruction")
            difficulty = step.get("difficulty_level")
            time = step.get("estimated_time_minutes")

            line = f"{step_num}. {instruction}"

            # Add metadata if available
            meta = []
            if difficulty:
                meta.append(f"Difficulty: {difficulty}")
            if time:
                meta.append(f"Time: ~{time} min")

            if meta:
                line += f"\n   _{' | '.join(meta)}_"

            # Add tools if available
            tools = step.get("tools_required")
            if tools and len(tools) > 0:
                line += f"\n   🔧 Tools: {', '.join(tools)}"

            # Add safety warnings if present
            safety = step.get("safety_warnings")
            if safety:
                line += f"\n   ⚠️ {safety}"

            lines.append(line)

        return "\n\n".join(lines)

    def format_parts_text(self, parts: List[Dict[str, Any]]) -> str:
        """
        Format parts as text for WhatsApp messages.

        Args:
            parts: List of part dicts

        Returns:
            Formatted string with parts list
        """
        if not parts:
            return "No parts information available."

        lines = ["*Parts Needed:*\n"]

        for part in parts:
            name = part.get("part_name", "Unknown part")
            part_num = part.get("part_number")
            manufacturer = part.get("manufacturer")
            price = part.get("price_estimate_usd")
            is_oem = part.get("is_oem", False)

            line = f"• {name}"

            if part_num:
                line += f"\n  Part #: {part_num}"

            meta = []
            if manufacturer:
                meta.append(manufacturer)
            if is_oem:
                meta.append("OEM")
            if price:
                meta.append(f"~${price:.2f}")

            if meta:
                line += f"\n  {' | '.join(meta)}"

            lines.append(line)

        return "\n\n".join(lines)

    def format_symptoms_text(self, symptoms: List[Dict[str, Any]]) -> str:
        """
        Format symptoms as text for WhatsApp messages.

        Args:
            symptoms: List of symptom dicts

        Returns:
            Formatted string with symptoms
        """
        if not symptoms:
            return "No symptoms information available."

        lines = ["*Common Symptoms:*\n"]

        for symptom in symptoms:
            text = symptom.get("symptom", "Unknown symptom")
            severity = symptom.get("severity")
            frequency = symptom.get("frequency")

            # Choose emoji based on severity
            emoji = "ℹ️"
            if severity == "Critical":
                emoji = "🚨"
            elif severity == "High":
                emoji = "⚠️"
            elif severity == "Medium":
                emoji = "⚡"

            line = f"{emoji} {text}"

            if severity or frequency:
                meta = []
                if severity:
                    meta.append(severity)
                if frequency:
                    meta.append(frequency)
                line += f" _({', '.join(meta)})_"

            lines.append(line)

        return "\n".join(lines)

    def format_related_codes_text(self, related: List[Dict[str, Any]]) -> str:
        """
        Format related codes as text for WhatsApp messages.

        Args:
            related: List of related code dicts

        Returns:
            Formatted string with related codes
        """
        if not related:
            return "No related codes found."

        lines = ["*Related Codes:*\n"]

        for item in related:
            code = item.get("related_code", "?")
            relationship = item.get("relationship_type", "Related")
            description = item.get("description", "")

            line = f"• *{code}* ({relationship})"
            if description:
                line += f"\n  {description}"

            lines.append(line)

        return "\n\n".join(lines)


# Singleton instance
_repository_instance = None


def get_vehicle_details_repository() -> VehicleDetailsRepository:
    """Get singleton instance of VehicleDetailsRepository."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = VehicleDetailsRepository()
    return _repository_instance
