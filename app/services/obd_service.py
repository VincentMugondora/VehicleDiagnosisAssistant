import re
from typing import Optional
from app.repositories.obd_repository import OBDRepository
from app.models.diagnostic import DiagnosticResult, VehicleContext
from app.core.errors import OBDCodeNotFound
from app.core.logging import logger
from app.services.ai_code_generator import AICodeGenerator
from app.services.ai_client import AIClient
from app.services.selective_enrichment import SelectiveEnrichment

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

        # Initialize AI services if AI client provided
        self.code_generator = None
        self.selective_enrichment = None
        if self.ai_client:
            self.code_generator = AICodeGenerator(self.ai_client)
            self.selective_enrichment = SelectiveEnrichment(self.ai_client)

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
        logger.info("obd_lookup_started", code=code)

        # Lookup base code
        base = self.obd_repo.get_by_code(code)

        if base:
            logger.info("obd_code_found_in_db", code=code, has_symptoms=bool(base.get("symptoms")))

        if not base:
            logger.warning("obd_code_not_found", code=code)

            # Try to fetch from web if auto-learn is enabled
            if self.auto_learn:
                web_result = await self._fetch_and_learn(code)
                if web_result:
                    return web_result

            # Return minimal unknown code response
            # Do not provide generic suggestions - accuracy over coverage
            return DiagnosticResult(
                code=code.upper(),
                description=f"Code {code.upper()} is not in our database yet.",
                causes=[
                    "This code may be vehicle-specific",
                    "Check your vehicle's service manual for details"
                ],
                checks=[
                    f"Search online: '{code.upper()} [your vehicle make/model]'",
                    "Visit a qualified mechanic for professional diagnosis",
                    "Clear code and monitor if problem recurs"
                ],
                confidence=0.10,  # Very low - we don't know what this code means
                source="unknown",
                system=None,  # Unknown system
                symptoms=None  # No symptoms for unknown codes
            )

        # Parse all fields from database
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
        base_symptoms = [
            s.strip()
            for s in (base.get("symptoms") or "").split(",")
            if s.strip()
        ]
        base_severity = base.get("severity")  # e.g., "High", "Moderate", "Low"
        base_severity_explanation = base.get("severity_explanation")
        base_technician_tip = base.get("technician_tip")
        base_pre_replacement_checks = [
            c.strip()
            for c in (base.get("pre_replacement_checks") or "").split(",")
            if c.strip()
        ]

        # Check if we need AI enrichment
        needs_enrichment = (
            not base_causes or
            not base_checks or
            not base_symptoms or
            not base_severity or
            not base_technician_tip or
            not base_pre_replacement_checks
        )

        if needs_enrichment:
            logger.info(
                "enrichment_needed",
                code=code,
                missing_symptoms=not base_symptoms,
                missing_causes=not base_causes,
                missing_checks=not base_checks,
                missing_severity=not base_severity,
                missing_tip=not base_technician_tip,
                missing_pre_checks=not base_pre_replacement_checks
            )

        # If missing any enrichment data and AI is available, enrich and save
        if needs_enrichment and self.auto_learn and self.code_generator:
            enriched = await self._enrich_and_save(code, base)
            if enriched:
                # Use enriched data
                base_causes = enriched.get("causes") or base_causes
                base_checks = enriched.get("checks") or base_checks
                base_symptoms = enriched.get("symptoms") or base_symptoms
                base_severity = enriched.get("severity") or base_severity
                base_severity_explanation = enriched.get("severity_explanation") or base_severity_explanation
                base_technician_tip = enriched.get("technician_tip") or base_technician_tip
                base_pre_replacement_checks = enriched.get("pre_replacement_checks") or base_pre_replacement_checks
        else:
            if needs_enrichment:
                logger.info("enrichment_skipped", code=code, reason="ai_not_available")

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

                # Build enrichment metadata for vehicle override case
                enrichment_meta = self._build_enrichment_metadata(base)

                return DiagnosticResult(
                    code=code.upper(),
                    description=base.get("description", ""),
                    causes=merged_causes,
                    checks=merged_checks,
                    confidence=0.98,
                    source="vehicle_override",
                    system=base.get("system"),
                    symptoms=base_symptoms or None,
                    severity=base_severity,
                    severity_explanation=base_severity_explanation,
                    technician_tip=base_technician_tip,
                    pre_replacement_checks=base_pre_replacement_checks or None,
                    enrichment_meta=enrichment_meta
                )

        # Return base code without override
        source = "enriched" if needs_enrichment and base_symptoms else "local_db"
        logger.info("obd_lookup_success", code=code, source=source)

        # Build enrichment metadata from database
        enrichment_meta = self._build_enrichment_metadata(base)

        return DiagnosticResult(
            code=code.upper(),
            description=base.get("description", ""),
            causes=base_causes,
            checks=base_checks,
            confidence=0.90 if source == "enriched" else 0.85,
            source=source,
            system=base.get("system"),
            symptoms=base_symptoms or None,
            severity=base_severity,
            severity_explanation=base_severity_explanation,
            technician_tip=base_technician_tip,
            pre_replacement_checks=base_pre_replacement_checks or None,
            enrichment_meta=enrichment_meta
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
                    "severity": generated_data.get("severity", "Moderate"),
                    "severity_explanation": generated_data.get("severity_explanation", ""),
                    "technician_tip": generated_data.get("technician_tip", ""),
                    "pre_replacement_checks": generated_data.get("pre_replacement_checks", "")
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
            symptoms = [
                s.strip()
                for s in (generated_data.get("symptoms") or "").split(",")
                if s.strip()
            ]
            pre_replacement_checks = [
                c.strip()
                for c in (generated_data.get("pre_replacement_checks") or "").split(",")
                if c.strip()
            ]

            return DiagnosticResult(
                code=code.upper(),
                description=generated_data.get("description", ""),
                causes=causes or ["Component malfunction"],
                checks=checks or ["Diagnose with scanner"],
                confidence=0.75,  # Good confidence for AI-generated
                source="ai_learned",
                system=generated_data.get("system"),
                symptoms=symptoms or None,
                severity=generated_data.get("severity"),
                severity_explanation=generated_data.get("severity_explanation"),
                technician_tip=generated_data.get("technician_tip"),
                pre_replacement_checks=pre_replacement_checks or None
            )

        except Exception as e:
            logger.error("fetch_and_learn_error", code=code, error=str(e))
            return None

    async def _enrich_and_save_selective(
        self,
        code: str,
        base_data: dict,
        missing_fields: list[str]
    ) -> Optional[dict]:
        """
        Selectively enrich ONLY the missing fields using AI.
        More efficient and accurate than regenerating everything.

        Args:
            code: OBD code
            base_data: Existing database entry
            missing_fields: List of field names that need generation

        Returns:
            Dict with enriched fields or None if enrichment fails
        """
        if not self.selective_enrichment:
            logger.warning("selective_enrichment_not_available", code=code)
            return None

        try:
            enrichment_start = __import__('time').time()
            logger.info("enrichment_started", code=code, fields=missing_fields)

            # Generate only missing fields (returns both data and metadata)
            generated_fields = await self.selective_enrichment.enrich_missing_fields(
                code=code,
                existing_data=base_data,
                missing_fields=missing_fields
            )

            if not generated_fields:
                logger.warning("enrichment_failed", code=code)
                return None

            # Separate data fields from metadata fields
            enriched_fields = {}
            metadata_fields = {}

            # Map internal field names to database column names
            # NOTE: technician_tip and pre_replacement_checks have NO data columns,
            # only metadata columns where the actual value is stored
            field_map = {
                "symptoms": "symptoms",
                "common_causes": "common_causes",
                "generic_fixes": "generic_fixes",
                "severity": "severity",
                "severity_explanation": "severity_explanation"
                # technician_tip and pre_replacement_checks are stored in metadata only
            }

            # Map metadata field names (internal -> database)
            metadata_field_map = {
                "symptoms_meta": "symptoms_meta",
                "common_causes_meta": "common_causes_meta",
                "generic_fixes_meta": "diagnostic_steps_meta",  # Database uses different name!
                "severity_explanation_meta": "severity_explanation_meta",
                "technician_tip_meta": "technician_tip_meta",
                "pre_replacement_checks_meta": "pre_replacement_checks_meta"
            }

            # Fields that are stored IN the metadata (no separate data column)
            metadata_only_fields = {"technician_tip", "pre_replacement_checks"}

            # Process data fields (those with data columns)
            for internal_field, db_field in field_map.items():
                if internal_field in generated_fields:
                    value = generated_fields[internal_field]
                    # Convert lists to comma-separated strings for database
                    if isinstance(value, list):
                        enriched_fields[db_field] = ", ".join(value)
                    else:
                        enriched_fields[db_field] = value

                # Copy metadata if present
                meta_key = f"{internal_field}_meta"
                if meta_key in generated_fields:
                    # Use metadata field map for correct column names
                    db_meta_key = metadata_field_map.get(meta_key, meta_key)
                    metadata_fields[db_meta_key] = generated_fields[meta_key]

            # Process metadata-only fields (no data column, value stored in metadata.value)
            for field in metadata_only_fields:
                if field in generated_fields:
                    meta_key = f"{field}_meta"
                    db_meta_key = metadata_field_map.get(meta_key, meta_key)
                    # Store the actual value in the metadata's "value" key
                    metadata_value = generated_fields.get(meta_key, {})
                    if isinstance(metadata_value, dict):
                        metadata_value["value"] = generated_fields[field]
                    else:
                        # If metadata doesn't exist, create it with just the value
                        metadata_value = {"value": generated_fields[field]}
                    metadata_fields[db_meta_key] = metadata_value

            # Update database with enriched fields and metadata
            try:
                self.obd_repo.enrich_code(code, enriched_fields, metadata_fields)
                enrichment_duration = __import__('time').time() - enrichment_start
                logger.info(
                    "enrichment_completed",
                    code=code,
                    fields_enriched=list(enriched_fields.keys()),
                    duration_ms=int(enrichment_duration * 1000)
                )
            except Exception as e:
                logger.error("enrichment_save_failed", code=code, error=str(e))
                # Continue anyway - we can still return the data to user

            # Return in format expected by get_obd_info
            result = {}
            if "symptoms" in generated_fields:
                result["symptoms"] = generated_fields["symptoms"]
            if "common_causes" in generated_fields:
                result["causes"] = generated_fields["common_causes"]
            if "generic_fixes" in generated_fields:
                result["checks"] = generated_fields["generic_fixes"]
            if "severity" in generated_fields:
                result["severity"] = generated_fields["severity"]
            if "severity_explanation" in generated_fields:
                result["severity_explanation"] = generated_fields["severity_explanation"]
            if "technician_tip" in generated_fields:
                result["technician_tip"] = generated_fields["technician_tip"]
            if "pre_replacement_checks" in generated_fields:
                result["pre_replacement_checks"] = generated_fields["pre_replacement_checks"]

            return result

        except Exception as e:
            logger.error("enrichment_error", code=code, error=str(e))
            return None

    async def _enrich_and_save(self, code: str, base_data: dict) -> Optional[dict]:
        """
        Enrich existing database entry with missing fields using AI.
        Now uses selective enrichment for better accuracy and efficiency.

        Args:
            code: OBD code
            base_data: Existing database entry

        Returns:
            Dict with enriched fields or None if enrichment fails
        """
        # Determine which fields are missing
        missing_fields = []

        if not base_data.get("symptoms"):
            missing_fields.append("symptoms")
        if not base_data.get("common_causes"):
            missing_fields.append("common_causes")
        if not base_data.get("generic_fixes"):
            missing_fields.append("generic_fixes")
        if not base_data.get("severity"):
            missing_fields.append("severity")
        if not base_data.get("severity_explanation"):
            missing_fields.append("severity_explanation")
        if not base_data.get("technician_tip"):
            missing_fields.append("technician_tip")
        if not base_data.get("pre_replacement_checks"):
            missing_fields.append("pre_replacement_checks")

        if not missing_fields:
            logger.info("no_enrichment_needed", code=code)
            return None

        # Use selective enrichment (smarter and more efficient)
        return await self._enrich_and_save_selective(code, base_data, missing_fields)

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

    def _build_enrichment_metadata(self, base_data: dict):
        """
        Build EnrichmentMetadata from database metadata columns.

        Args:
            base_data: Database record with metadata columns

        Returns:
            EnrichmentMetadata or None if no metadata present
        """
        from app.models.enrichment import EnrichmentMetadata, FieldMetadata

        # Check if any metadata fields are present
        has_metadata = any([
            base_data.get("symptoms_meta"),
            base_data.get("causes_meta"),
            base_data.get("severity_meta"),
            base_data.get("technician_tip_meta"),
            base_data.get("pre_replacement_checks_meta")
        ])

        if not has_metadata:
            return None

        # Build FieldMetadata objects from JSONB fields
        def parse_field_meta(meta_dict):
            if not meta_dict:
                return None
            try:
                return FieldMetadata(**meta_dict)
            except:
                return None

        symptoms_meta = parse_field_meta(base_data.get("symptoms_meta"))
        causes_meta = parse_field_meta(base_data.get("causes_meta"))
        severity_meta = parse_field_meta(base_data.get("severity_meta"))
        technician_tip_meta = parse_field_meta(base_data.get("technician_tip_meta"))
        pre_replacement_checks_meta = parse_field_meta(base_data.get("pre_replacement_checks_meta"))

        # Determine overall enrichment status
        from app.models.enrichment import EnrichmentStatus, calculate_knowledge_score

        knowledge_score = calculate_knowledge_score(
            has_description=bool(base_data.get("description")),
            has_symptoms=bool(base_data.get("symptoms")),
            has_causes=bool(base_data.get("common_causes")),
            has_checks=bool(base_data.get("generic_fixes")),
            has_severity=bool(base_data.get("severity")),
            has_severity_explanation=bool(base_data.get("severity_explanation")),
            has_technician_tip=bool(base_data.get("technician_tip")),
            has_pre_replacement_checks=bool(base_data.get("pre_replacement_checks")),
            has_system=bool(base_data.get("system"))
        )

        enrichment_status = base_data.get("enrichment_status", "not_enriched")
        if enrichment_status == "not_enriched" and knowledge_score >= 80:
            enrichment_status = "ai_generated"  # Auto-upgrade if complete

        return EnrichmentMetadata(
            symptoms_meta=symptoms_meta,
            causes_meta=causes_meta,
            severity_meta=severity_meta,
            technician_tip_meta=technician_tip_meta,
            pre_replacement_checks_meta=pre_replacement_checks_meta,
            enrichment_status=EnrichmentStatus(enrichment_status) if enrichment_status else EnrichmentStatus.NOT_ENRICHED,
            knowledge_score=knowledge_score,
            last_enriched=base_data.get("last_enriched"),
            enrichment_version=base_data.get("schema_version", 1)
        )
