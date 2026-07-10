"""
Structured Audit Event System

Logs all database changes as structured events with complete context.
Supports rollback, debugging, and compliance auditing.
"""

from datetime import datetime
from typing import Optional
import json


def create_severity_update_event(
    code: str,
    previous_severity: str,
    new_severity: str,
    confidence: float,
    rule: str,
    reasoning: str,
    actor: str = "severity_rules_v1",
    previous_explanation: Optional[str] = None,
    new_explanation: Optional[str] = None
) -> dict:
    """
    Create severity update audit event.

    Args:
        code: OBD-II code
        previous_severity: Original severity
        new_severity: Updated severity
        confidence: Confidence score (0.0-1.0)
        rule: Rule that triggered the change
        reasoning: Why this severity was chosen
        actor: System/user making the change
        previous_explanation: Original explanation
        new_explanation: New explanation

    Returns:
        Structured event dict
    """
    return {
        'event': 'severity_updated',
        'code': code,
        'previous': previous_severity,
        'new': new_severity,
        'confidence': confidence,
        'rule': rule,
        'reasoning': reasoning,
        'actor': actor,
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': {
            'previous_explanation': previous_explanation,
            'new_explanation': new_explanation
        }
    }


def create_enrichment_event(
    code: str,
    fields_enriched: list[str],
    prompt_version: str,
    prompt_hash: str,
    ai_model: str,
    previous_status: str,
    new_status: str,
    actor: str = "enrichment_tool"
) -> dict:
    """
    Create enrichment audit event.

    Args:
        code: OBD-II code
        fields_enriched: List of enriched field names
        prompt_version: Version of enrichment prompt
        prompt_hash: Hash of prompt template
        ai_model: AI model used
        previous_status: Status before enrichment
        new_status: Status after enrichment
        actor: System performing enrichment

    Returns:
        Structured event dict
    """
    return {
        'event': 'code_enriched',
        'code': code,
        'fields_enriched': fields_enriched,
        'prompt_version': prompt_version,
        'prompt_hash': prompt_hash,
        'ai_model': ai_model,
        'previous_status': previous_status,
        'new_status': new_status,
        'actor': actor,
        'timestamp': datetime.utcnow().isoformat()
    }


def create_review_event(
    code: str,
    previous_status: str,
    new_status: str,
    approved: bool,
    reviewer: str,
    review_notes: Optional[str] = None
) -> dict:
    """
    Create review audit event.

    Args:
        code: OBD-II code
        previous_status: Status before review
        new_status: Status after review
        approved: Whether content was approved
        reviewer: User performing review
        review_notes: Optional review notes

    Returns:
        Structured event dict
    """
    return {
        'event': 'content_reviewed',
        'code': code,
        'previous_status': previous_status,
        'new_status': new_status,
        'approved': approved,
        'reviewer': reviewer,
        'review_notes': review_notes,
        'actor': reviewer,
        'timestamp': datetime.utcnow().isoformat()
    }


def create_publication_event(
    code: str,
    previous_status: str,
    publisher: str
) -> dict:
    """
    Create publication audit event.

    Args:
        code: OBD-II code
        previous_status: Status before publication
        publisher: User publishing content

    Returns:
        Structured event dict
    """
    return {
        'event': 'content_published',
        'code': code,
        'previous_status': previous_status,
        'new_status': 'published',
        'publisher': publisher,
        'actor': publisher,
        'timestamp': datetime.utcnow().isoformat()
    }


def create_unpublish_event(
    code: str,
    reason: str,
    requester: str
) -> dict:
    """
    Create unpublish/revision audit event.

    Args:
        code: OBD-II code
        reason: Why content is being unpublished
        requester: User requesting unpublish

    Returns:
        Structured event dict
    """
    return {
        'event': 'content_unpublished',
        'code': code,
        'previous_status': 'published',
        'new_status': 'needs_revision',
        'reason': reason,
        'requester': requester,
        'actor': requester,
        'timestamp': datetime.utcnow().isoformat()
    }


class AuditLogger:
    """Logs structured audit events to database"""

    def __init__(self, db_client):
        self.db_client = db_client

    def log_event(self, event: dict):
        """
        Log an audit event to database.

        Args:
            event: Structured event dict
        """
        # Insert into audit log
        self.db_client.table('enrichment_audit_log').insert({
            'code': event['code'],
            'timestamp': event['timestamp'],
            'action': event['event'],
            'actor': event['actor'],
            'previous_state': event.get('previous') or event.get('previous_status'),
            'new_state': event.get('new') or event.get('new_status'),
            'notes': event.get('reasoning') or event.get('reason') or event.get('review_notes'),
            'metadata': event
        }).execute()

    def log_severity_update(
        self,
        code: str,
        previous_severity: str,
        new_severity: str,
        confidence: float,
        rule: str,
        reasoning: str,
        previous_explanation: Optional[str] = None,
        new_explanation: Optional[str] = None
    ):
        """Log severity correction"""
        event = create_severity_update_event(
            code, previous_severity, new_severity, confidence, rule, reasoning,
            previous_explanation=previous_explanation,
            new_explanation=new_explanation
        )
        self.log_event(event)

    def log_enrichment(
        self,
        code: str,
        fields_enriched: list[str],
        prompt_version: str,
        prompt_hash: str,
        ai_model: str,
        previous_status: str,
        new_status: str
    ):
        """Log code enrichment"""
        event = create_enrichment_event(
            code, fields_enriched, prompt_version, prompt_hash, ai_model,
            previous_status, new_status
        )
        self.log_event(event)

    def log_review(
        self,
        code: str,
        previous_status: str,
        new_status: str,
        approved: bool,
        reviewer: str,
        review_notes: Optional[str] = None
    ):
        """Log content review"""
        event = create_review_event(
            code, previous_status, new_status, approved, reviewer, review_notes
        )
        self.log_event(event)

    def log_publication(
        self,
        code: str,
        previous_status: str,
        publisher: str
    ):
        """Log content publication"""
        event = create_publication_event(code, previous_status, publisher)
        self.log_event(event)

    def log_unpublish(
        self,
        code: str,
        reason: str,
        requester: str
    ):
        """Log content unpublish/revision"""
        event = create_unpublish_event(code, reason, requester)
        self.log_event(event)


# Export
__all__ = [
    'create_severity_update_event',
    'create_enrichment_event',
    'create_review_event',
    'create_publication_event',
    'create_unpublish_event',
    'AuditLogger'
]


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("STRUCTURED AUDIT EVENTS")
    print("=" * 80)
    print()

    # Severity update event
    event = create_severity_update_event(
        code="P0450",
        previous_severity="High",
        new_severity="Moderate",
        confidence=0.92,
        rule="EVAP_SYSTEM",
        reasoning="EVAP system - emissions primarily, rarely drivability"
    )

    print("Severity Update Event:")
    print(json.dumps(event, indent=2))
    print()

    # Enrichment event
    event2 = create_enrichment_event(
        code="P0420",
        fields_enriched=["symptoms", "common_causes", "diagnostic_steps"],
        prompt_version="1.0.0",
        prompt_hash="abc123",
        ai_model="claude-sonnet-4.5",
        previous_status="raw_database",
        new_status="ai_enriched"
    )

    print("Enrichment Event:")
    print(json.dumps(event2, indent=2))
    print()
