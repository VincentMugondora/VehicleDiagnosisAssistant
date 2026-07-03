from pydantic import BaseModel


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
    """Result of OBD code diagnosis"""
    code: str
    description: str
    causes: list[str]
    checks: list[str]
    confidence: float
    source: str  # "local_db" | "vehicle_override" | "external"
    system: str | None = None  # Vehicle system (e.g., "Emissions", "Fuel System")


class SymptomDiagnosisResult(BaseModel):
    """Result of symptom-based diagnosis"""
    probable_codes: list[str]
    likely_systems: list[str]
    recommended_checks: list[str]
