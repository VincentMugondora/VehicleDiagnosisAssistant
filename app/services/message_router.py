from app.services.obd_service import OBDService, validate_obd_code
from app.services.diagnose import diagnose
from app.services.normalize import normalize_symptoms
from app.utils.obd_parser import parse_message
from app.models.diagnostic import DiagnosticResult, VehicleContext, SymptomDiagnosisResult
from app.core.config import settings
from app.core.logging import logger


class MessageRouter:
    """
    Routes incoming messages to appropriate diagnosis flow.

    Two flows:
    1. Code-based: User provides OBD code -> lookup in database
    2. Symptom-based: User describes symptoms -> suggest probable codes
    """

    def __init__(self, obd_service: OBDService):
        self.obd_service = obd_service
        self.ai_client = None

        # Initialize AI client if enrichment enabled
        if settings.ai_enrich_enabled:
            try:
                from app.services.ai_client import AIClient
                self.ai_client = AIClient()
            except Exception as e:
                logger.warning(
                    "ai_client_initialization_failed",
                    error=str(e)
                )

    async def route_message(
        self,
        raw_text: str,
        phone_hash: str,
        request_id: str
    ) -> DiagnosticResult | SymptomDiagnosisResult | dict:
        """
        Parse message and route to appropriate diagnosis flow.

        Args:
            raw_text: Raw user message
            phone_hash: SHA-256 hash of phone number
            request_id: Request tracing ID

        Returns:
            DiagnosticResult, SymptomDiagnosisResult, or error dict
        """
        # Parse message to extract code and vehicle
        parsed = parse_message(raw_text)
        code = parsed.get("code")

        vehicle = VehicleContext(
            make=parsed.get("make"),
            model=parsed.get("model"),
            year=parsed.get("year"),
            engine=parsed.get("engine")
        )

        logger.info(
            "message_parsed",
            code=code,
            vehicle_detected=bool(vehicle.make)
        )

        # Route 1: Code-based diagnosis
        if code and validate_obd_code(code):
            logger.info("routing_to_code_diagnosis", code=code)
            try:
                result = await self.obd_service.get_obd_info(code, vehicle)

                # Enrich with AI if enabled
                if self.ai_client and result.causes:
                    try:
                        vehicle_context = {
                            "make": vehicle.make or "",
                            "model": vehicle.model or "",
                            "year": vehicle.year or "",
                            "engine": vehicle.engine or ""
                        }
                        ranked_causes = self.ai_client.rank_causes_with_retry(
                            base_causes=result.causes,
                            vehicle_context=vehicle_context
                        )
                        # Update result with ranked causes
                        result.causes = ranked_causes
                        logger.info(
                            "ai_enrichment_applied",
                            code=code,
                            provider=settings.ai_provider
                        )
                    except Exception as e:
                        logger.warning(
                            "ai_enrichment_failed",
                            code=code,
                            error=str(e)
                        )
                        # Continue with original causes

                return result
            except Exception as e:
                logger.error(
                    "code_diagnosis_failed",
                    code=code,
                    error=str(e)
                )
                return {
                    "error": "Unable to diagnose code. Please try again."
                }

        # Route 2: Symptom-based diagnosis
        symptoms = normalize_symptoms(raw_text)
        if symptoms:
            logger.info(
                "routing_to_symptom_diagnosis",
                symptoms=symptoms
            )
            result = diagnose(symptoms)
            return SymptomDiagnosisResult(**result)

        # Route 3: No valid input
        logger.info("no_valid_input_detected")
        return {
            "error": (
                "Send an OBD-II code like P0171. "
                "Optional: add symptoms (e.g., car shaking) "
                "and vehicle (e.g., Corolla 2015 1.6L)."
            )
        }
