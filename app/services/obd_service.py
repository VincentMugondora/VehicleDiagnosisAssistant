import re
from typing import Optional
from app.repositories.obd_repository import OBDRepository
from app.models.diagnostic import DiagnosticResult, VehicleContext
from app.core.errors import OBDCodeNotFound
from app.core.logging import logger
from app.services.ai_code_generator import AICodeGenerator
from app.services.ai_client import AIClient

_OBD_REGEX = re.compile(r"^[PBCU][0-9]{4}$", re.IGNORECASE)


def validate_obd_code(code: str) -> bool:
    """
    Validate OBD-II code format.

    Args:
        code: OBD code to validate

    Returns:
        True if valid format (e.g., P0420, B1234, C0001, U0100)
    """
    return bool(_OBD_REGEX.match(code or ""))


class OBDService:
    """
    Service for OBD code lookups with vehicle-specific overrides.

    Uses repository pattern for database access.
    Dynamically fetches and learns new codes from the web.
    """

    def __init__(
        self,
        obd_repo: OBDRepository,
        ai_client: Optional[AIClient] = None,
        auto_learn: bool = True
    ):
        self.obd_repo = obd_repo
        self.ai_client = ai_client
        self.auto_learn = auto_learn  # Enable/disable dynamic learning

        # Initialize AI code generator if AI client provided
        self.code_generator = None
        if self.ai_client:
            self.code_generator = AICodeGenerator(self.ai_client)

    async def get_obd_info(
        self,
        code: str,
        vehicle: VehicleContext
    ) -> DiagnosticResult:
        """
        Lookup OBD code with optional vehicle-specific overrides.
        If not found locally, attempts to fetch from web and learn.

        Args:
            code: OBD code (e.g., "P0420")
            vehicle: Vehicle context

        Returns:
            DiagnosticResult with description, causes, checks, confidence

        Raises:
            OBDCodeNotFound: If code not in database and no fallback available
        """
        # Lookup base code
        base = self.obd_repo.get_by_code(code)

        if not base:
            logger.warning("obd_code_not_found", code=code)

            # Try to fetch from web if auto-learn is enabled
            if self.auto_learn:
                web_result = await self._fetch_and_learn(code)
                if web_result:
                    return web_result

            # Return generic fallback
            return DiagnosticResult(
                code=code.upper(),
                description="Generic OBD-II diagnostic trouble code",
                causes=[
                    "Faulty sensor",
                    "Wiring or connector issue",
                    "ECM software fault"
                ],
                checks=[
                    "Inspect wiring",
                    "Check connectors",
                    "Clear code and retest"
                ],
                confidence=0.30,
                source="fallback"
            )

        # Parse base causes and checks
        base_causes = [
            c.strip()
            for c in (base.get("common_causes") or "").split(",")
            if c.strip()
        ]
        base_checks = [
            c.strip()
            for c in re.split(r"[,\n;]+", base.get("generic_fixes") or "")
            if c.strip()
        ]

        # Check for vehicle-specific override
        if (vehicle.make and vehicle.model and
            vehicle.year and vehicle.engine):

            override = self.obd_repo.get_vehicle_override(
                code=code,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                engine=vehicle.engine
            )

            if override:
                logger.info(
                    "vehicle_override_found",
                    code=code,
                    vehicle=f"{vehicle.make} {vehicle.model} {vehicle.year}"
                )

                # Merge causes (override + base, deduplicated)
                override_causes = override.get("known_issues", []) or []
                merged_causes = self._dedupe_list(
                    override_causes + base_causes
                )

                # Merge checks (override + base, deduplicated)
                override_checks = override.get("priority_checks", []) or []
                merged_checks = self._dedupe_list(
                    override_checks + base_checks
                )

                return DiagnosticResult(
                    code=code.upper(),
                    description=base.get("description", ""),
                    causes=merged_causes,
                    checks=merged_checks,
                    confidence=0.98,
                    source="vehicle_override"
                )

        # Return base code without override
        logger.info("obd_lookup_success", code=code, source="local_db")
        return DiagnosticResult(
            code=code.upper(),
            description=base.get("description", ""),
            causes=base_causes,
            checks=base_checks,
            confidence=0.85,
            source="local_db"
        )

    async def _fetch_and_learn(self, code: str) -> Optional[DiagnosticResult]:
        """
        Generate code info using AI, save to database.

        Args:
            code: OBD code to generate info for

        Returns:
            DiagnosticResult if successful, None otherwise
        """
        if not self.code_generator:
            logger.warning("ai_generator_not_available", code=code)
            return None

        try:
            # Step 1: Generate with AI
            logger.info("dynamic_learn_started", code=code)
            generated_data = await self.code_generator.generate_code_info(code)

            if not generated_data:
                logger.warning("ai_generation_failed", code=code)
                return None

            # Step 2: Save to database for future use
            logger.info("auto_save_started", code=code)
            try:
                self.obd_repo.insert_code({
                    "code": generated_data["code"],
                    "description": generated_data["description"],
                    "symptoms": generated_data.get("symptoms", ""),
                    "common_causes": generated_data.get("common_causes", ""),
                    "generic_fixes": generated_data.get("generic_fixes", ""),
                    "system": generated_data.get("system", "Powertrain"),
                    "severity": generated_data.get("severity", "Medium")
                })
                logger.info("auto_save_success", code=code)
            except Exception as e:
                logger.error("auto_save_failed", code=code, error=str(e))
                # Continue anyway - we can still return the data to user

            # Step 3: Return structured result to user
            causes = [
                c.strip()
                for c in (generated_data.get("common_causes") or "").split(",")
                if c.strip()
            ]
            checks = [
                c.strip()
                for c in (generated_data.get("generic_fixes") or "").split(",")
                if c.strip()
            ]

            return DiagnosticResult(
                code=code.upper(),
                description=generated_data.get("description", ""),
                causes=causes or ["Component malfunction"],
                checks=checks or ["Diagnose with scanner"],
                confidence=0.75,  # Good confidence for AI-generated
                source="ai_learned"
            )

        except Exception as e:
            logger.error("fetch_and_learn_error", code=code, error=str(e))
            return None

    def _dedupe_list(self, items: list[str]) -> list[str]:
        """
        Deduplicate list while preserving order (case-insensitive).

        Args:
            items: List of strings

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
