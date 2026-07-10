"""
Enrichment Metadata and Provenance Tracking

Tracks the complete provenance of AI-generated diagnostic content:
- Prompt version and hash
- AI model used
- Generation timestamp
- Review status and reviewer
- Publication timestamp
- Evidence sources

This enables:
- Selective regeneration when prompts improve
- Audit trail for all content
- Replacement of AI content with OEM references
- Quality control and accountability
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
import hashlib
import json


# Current prompt version (increment when prompt changes significantly)
ENRICHMENT_PROMPT_VERSION = "1.0.0"


def compute_prompt_hash(prompt_template: str) -> str:
    """
    Compute deterministic hash of enrichment prompt.

    Args:
        prompt_template: The prompt template string

    Returns:
        SHA-256 hash of prompt (first 16 chars)
    """
    return hashlib.sha256(prompt_template.encode()).hexdigest()[:16]


@dataclass
class EvidenceSource:
    """Source of diagnostic information"""
    type: Literal["ai_generated", "oem_service_manual", "tsb", "repair_database", "human_expert"]
    confidence: float  # 0.0 to 1.0
    model: Optional[str] = None  # For AI: "claude-sonnet-4.5", "cohere-command-r-plus"
    reference: Optional[str] = None  # For OEM: TSB number, manual reference
    date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: Optional[str] = None


@dataclass
class FieldProvenance:
    """Provenance tracking for a single enriched field"""
    field_name: str  # "symptoms", "common_causes", etc.
    value: str | list[str]  # The actual content
    evidence: list[EvidenceSource]

    # Generation metadata
    prompt_version: str
    prompt_hash: str
    generated_at: str

    # Review metadata
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None

    # Publication metadata
    published_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "field_name": self.field_name,
            "value": self.value,
            "evidence": [
                {
                    "type": e.type,
                    "confidence": e.confidence,
                    "model": e.model,
                    "reference": e.reference,
                    "date": e.date,
                    "notes": e.notes
                }
                for e in self.evidence
            ],
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "generated_at": self.generated_at,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "review_notes": self.review_notes,
            "published_at": self.published_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FieldProvenance":
        """Create from dictionary"""
        evidence = [
            EvidenceSource(
                type=e["type"],
                confidence=e["confidence"],
                model=e.get("model"),
                reference=e.get("reference"),
                date=e["date"],
                notes=e.get("notes")
            )
            for e in data["evidence"]
        ]

        return cls(
            field_name=data["field_name"],
            value=data["value"],
            evidence=evidence,
            prompt_version=data["prompt_version"],
            prompt_hash=data["prompt_hash"],
            generated_at=data["generated_at"],
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=data.get("reviewed_at"),
            review_notes=data.get("review_notes"),
            published_at=data.get("published_at")
        )


@dataclass
class EnrichmentRecord:
    """Complete enrichment record with provenance for all fields"""
    code: str

    # Enriched fields with provenance
    symptoms: Optional[FieldProvenance] = None
    common_causes: Optional[FieldProvenance] = None
    diagnostic_steps: Optional[FieldProvenance] = None
    technician_tip: Optional[FieldProvenance] = None
    pre_replacement_checks: Optional[FieldProvenance] = None
    severity_explanation: Optional[FieldProvenance] = None

    # Overall enrichment status
    enrichment_status: str = "raw_database"

    def is_published(self) -> bool:
        """Check if any field is published"""
        fields = [
            self.symptoms,
            self.common_causes,
            self.diagnostic_steps,
            self.technician_tip,
            self.pre_replacement_checks,
            self.severity_explanation
        ]
        return any(
            f and f.published_at is not None
            for f in fields
        )

    def can_overwrite(self) -> bool:
        """
        Check if this record can be overwritten by AI enrichment.

        Published content is immutable - requires explicit review action.
        """
        return not self.is_published()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "code": self.code,
            "symptoms": self.symptoms.to_dict() if self.symptoms else None,
            "common_causes": self.common_causes.to_dict() if self.common_causes else None,
            "diagnostic_steps": self.diagnostic_steps.to_dict() if self.diagnostic_steps else None,
            "technician_tip": self.technician_tip.to_dict() if self.technician_tip else None,
            "pre_replacement_checks": self.pre_replacement_checks.to_dict() if self.pre_replacement_checks else None,
            "severity_explanation": self.severity_explanation.to_dict() if self.severity_explanation else None,
            "enrichment_status": self.enrichment_status
        }


def create_ai_evidence(
    model: str,
    confidence: float,
    notes: Optional[str] = None
) -> EvidenceSource:
    """
    Create evidence source for AI-generated content.

    Args:
        model: AI model name (e.g., "claude-sonnet-4.5")
        confidence: Confidence score (0.0-1.0)
        notes: Optional notes about generation

    Returns:
        EvidenceSource for AI generation
    """
    return EvidenceSource(
        type="ai_generated",
        confidence=confidence,
        model=model,
        notes=notes
    )


def create_field_provenance(
    field_name: str,
    value: str | list[str],
    prompt_version: str,
    prompt_hash: str,
    evidence: list[EvidenceSource]
) -> FieldProvenance:
    """
    Create field provenance for newly generated content.

    Args:
        field_name: Name of field
        value: Field content
        prompt_version: Version of prompt used
        prompt_hash: Hash of prompt template
        evidence: List of evidence sources

    Returns:
        FieldProvenance record
    """
    return FieldProvenance(
        field_name=field_name,
        value=value,
        evidence=evidence,
        prompt_version=prompt_version,
        prompt_hash=prompt_hash,
        generated_at=datetime.utcnow().isoformat()
    )


def mark_reviewed(
    provenance: FieldProvenance,
    reviewer: str,
    notes: Optional[str] = None
) -> FieldProvenance:
    """
    Mark field as reviewed.

    Args:
        provenance: Field provenance to update
        reviewer: Name/ID of reviewer
        notes: Review notes

    Returns:
        Updated provenance
    """
    provenance.reviewed_by = reviewer
    provenance.reviewed_at = datetime.utcnow().isoformat()
    provenance.review_notes = notes
    return provenance


def mark_published(provenance: FieldProvenance) -> FieldProvenance:
    """
    Mark field as published (immutable).

    Args:
        provenance: Field provenance to update

    Returns:
        Updated provenance
    """
    if not provenance.reviewed_by:
        raise ValueError("Cannot publish unreviewed content")

    provenance.published_at = datetime.utcnow().isoformat()
    return provenance


# Export current prompt version and hash function
__all__ = [
    "ENRICHMENT_PROMPT_VERSION",
    "compute_prompt_hash",
    "EvidenceSource",
    "FieldProvenance",
    "EnrichmentRecord",
    "create_ai_evidence",
    "create_field_provenance",
    "mark_reviewed",
    "mark_published"
]


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("ENRICHMENT METADATA SYSTEM")
    print("=" * 80)
    print()

    # Create AI evidence
    evidence = create_ai_evidence(
        model="claude-sonnet-4.5",
        confidence=0.85,
        notes="Generated with improved OEM-style prompt"
    )

    print("Evidence Source:")
    print(f"  Type: {evidence.type}")
    print(f"  Model: {evidence.model}")
    print(f"  Confidence: {evidence.confidence}")
    print(f"  Date: {evidence.date}")
    print()

    # Create field provenance
    provenance = create_field_provenance(
        field_name="symptoms",
        value=["Check Engine Light illuminated", "Rough idle", "Poor fuel economy"],
        prompt_version=ENRICHMENT_PROMPT_VERSION,
        prompt_hash="abc123def456",
        evidence=[evidence]
    )

    print("Field Provenance:")
    print(f"  Field: {provenance.field_name}")
    print(f"  Prompt Version: {provenance.prompt_version}")
    print(f"  Generated: {provenance.generated_at}")
    print(f"  Reviewed: {provenance.reviewed_by or 'No'}")
    print(f"  Published: {provenance.published_at or 'No'}")
    print()

    # Mark as reviewed
    provenance = mark_reviewed(provenance, "technician_001", "Symptoms accurate")
    print("After Review:")
    print(f"  Reviewed By: {provenance.reviewed_by}")
    print(f"  Review Notes: {provenance.review_notes}")
    print()

    # Mark as published
    provenance = mark_published(provenance)
    print("After Publication:")
    print(f"  Published: {provenance.published_at}")
    print()

    # Serialize to JSON
    json_data = provenance.to_dict()
    print("JSON Serialization:")
    print(json.dumps(json_data, indent=2))
    print()
