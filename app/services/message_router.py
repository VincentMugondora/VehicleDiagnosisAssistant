from datetime import datetime
from app.services.obd_service import OBDService, validate_obd_code
from app.services.vin_decoder import validate_vin, decode_vin
from app.services.diagnose import diagnose
from app.services.normalize import normalize_symptoms
from app.utils.obd_parser import parse_message
from app.models.diagnostic import DiagnosticResult, VehicleContext, SymptomDiagnosisResult
from app.models.session import LastDiagnosis, SessionState
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

    def _find_vin_token(self, raw_text: str) -> str | None:
        """Extract a VIN-shaped token from the message text."""
        for t in raw_text.strip().split():
            cleaned = t.strip(".,;:!?\"'")
            if len(cleaned) == 17 and validate_vin(cleaned):
                return cleaned
        return None

    async def _try_vin_decode(
        self,
        raw_text: str,
        vehicle: VehicleContext,
        session: SessionState | None
    ) -> VehicleContext | None:
        """
        If raw_text contains a 17-char VIN-shaped token, decode it and
        return an updated VehicleContext. Returns None if no VIN found
        or decode is not useful.
        """
        vin_token = self._find_vin_token(raw_text)
        if not vin_token:
            return None

        decoded = await decode_vin(vin_token)
        if not decoded or not decoded.is_useful():
            logger.info("vin_decode_not_useful", vin=vin_token)
            return None

        logger.info(
            "vin_decoded_vehicle_context",
            vin=vin_token,
            make=decoded.make,
            model=decoded.model,
            year=decoded.year,
        )

        # Store decoded vehicle on session for future messages
        if session:
            session.vehicle = VehicleContext(
                make=decoded.make,
                model=decoded.model,
                year=decoded.year,
                engine=decoded.engine_summary,
            )

        return VehicleContext(
            make=decoded.make,
            model=decoded.model,
            year=decoded.year,
            engine=decoded.engine_summary,
        )

    async def route_message(
        self,
        raw_text: str,
        phone_hash: str,
        request_id: str,
        session: SessionState | None = None
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

        # Check for VIN in the message and use it to fill vehicle context
        vin_result = await self._try_vin_decode(raw_text, vehicle, session)
        if vin_result:
            vehicle = vin_result

        logger.info(
            "message_parsed",
            code=code,
            vehicle_detected=bool(vehicle.make)
        )

        # Route 0: VIN-only message (no code, no symptoms) — acknowledge vehicle
        vin_token = self._find_vin_token(raw_text)
        if vin_token and not code:
            if vin_result:
                vehicle_str = " ".join(filter(None, [
                    vehicle.make, vehicle.model, vehicle.year
                ]))
                engine_str = f" ({vehicle.engine})" if vehicle.engine else ""
                return {
                    "reply": (
                        f"Vehicle identified: {vehicle_str}{engine_str}. "
                        f"Now send an OBD-II fault code (e.g. P0420) and "
                        f"I'll diagnose it for your specific vehicle."
                    )
                }
            else:
                return {
                    "reply": (
                        "I received your VIN but couldn't identify the vehicle "
                        "(this is common for imports not sold in the US market). "
                        "Please tell me your vehicle make, model, and year instead "
                        "(e.g. Toyota Hilux 2015 2.5L)."
                    )
                }

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

                # Store diagnosis in session for followup context
                if session:
                    vehicle_str = " ".join(filter(None, [
                        vehicle.make,
                        vehicle.model,
                        vehicle.year,
                        vehicle.engine
                    ])) or None

                    session.last_diagnosis = LastDiagnosis(
                        code=result.code,
                        description=result.description,
                        timestamp=datetime.utcnow(),
                        vehicle_context=vehicle_str
                    )
                    logger.info("last_diagnosis_stored", code=result.code)

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

        # Route 2: Free-text followup with context
        # If user is asking a followup question about their last diagnosis
        if session and session.last_diagnosis and self.ai_client:
            logger.info(
                "routing_to_followup_with_context",
                last_code=session.last_diagnosis.code
            )
            try:
                # Build context from last diagnosis
                context = f"""Previous diagnosis context:
- OBD Code: {session.last_diagnosis.code}
- Issue: {session.last_diagnosis.description}
- Vehicle: {session.last_diagnosis.vehicle_context or 'Not specified'}

User's followup question: {raw_text}

Provide a helpful response based on the previous diagnosis context."""

                response = await self.ai_client.complete(
                    prompt=context,
                    temperature=0.3,
                    max_tokens=500
                )

                # Return dict with reply key
                return {
                    "reply": response
                }
            except Exception as e:
                logger.error(
                    "followup_with_context_failed",
                    error=str(e)
                )
                # Fall through to symptom diagnosis

        # Route 3: Symptom-based diagnosis
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
