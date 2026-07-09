from pydantic import BaseModel
from typing import Optional
from app.models.enrichment import EnrichmentMetadata


class VehicleContext(BaseModel):
    """Vehicle information extracted from user message"""
    make: str | None = None
    model: str | None = None
    year: str | None = None
    engine: str | None = None


class DiagnosticRequest(BaseModel):
    """Request for OBD code diagnosis"""
    code: str
    vehicle: VehicleContext
    phone_hash: str
    request_id: str


class DiagnosticResult(BaseModel):
    """
    Result of OBD code diagnosis.

    All fields should be populated from database or AI generation.
    Formatter should not infer any of these fields - it only presents them.

    NOTE: Lists are stored as JSON arrays in database, not comma-separated strings.
    """
    code: str
    description: str
    causes: list[str]  # JSON array in database
    checks: list[str]  # JSON array in database
    confidence: float
    source: str  # "local_db" | "vehicle_override" | "external" | "ai_learned" | "enriched"
    system: str | None = None  # Vehicle system (e.g., "Emissions", "Fuel System")

    # Enriched fields (from database/AI, not inferred)
    symptoms: list[str] | None = None  # JSON array in database
    severity: str | None = None  # "Critical" | "High" | "Moderate" | "Low"
    severity_explanation: str | None = None  # Why this severity level
    technician_tip: str | None = None  # Practical diagnostic tip
    pre_replacement_checks: list[str] | None = None  # JSON array in database

    # Enrichment metadata (tracks provenance and quality)
    enrichment_meta: Optional[EnrichmentMetadata] = None


class SymptomDiagnosisResult(BaseModel):
    """Result of symptom-based diagnosis"""
    probable_codes: list[str]
    likely_systems: list[str]
    recommended_checks: list[str]
