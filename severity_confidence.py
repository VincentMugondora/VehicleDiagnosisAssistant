"""
Confidence-Based Severity Correction

Classifies severity corrections by confidence level:
- High confidence (≥90%): Auto-apply
- Medium confidence (60-89%): Queue for review
- Low confidence (<60%): Leave unchanged

Confidence is based on:
- Rule specificity (code-specific > category > pattern > default)
- Description clarity
- System classification
- Known patterns vs unknowns
"""

from dataclasses import dataclass
from typing import Literal
from severity_rules import classify_severity, get_severity_explanation


@dataclass
class SeverityCorrection:
    """Severity correction with confidence assessment"""
    code: str
    description: str
    system: str
    current_severity: str
    recommended_severity: str
    reasoning: str
    confidence: float  # 0.0 to 1.0
    confidence_level: Literal["high", "medium", "low"]
    evidence: str  # Why this confidence level
    action: Literal["auto_apply", "queue_review", "leave_unchanged"]


def assess_confidence(
    code: str,
    description: str,
    system: str,
    current_severity: str,
    recommended_severity: str,
    reasoning: str
) -> tuple[float, str]:
    """
    Assess confidence in severity classification.

    Returns:
        (confidence_score, evidence_explanation)
    """
    confidence = 0.0
    evidence_parts = []

    # Base confidence from rule matching
    from severity_rules import CODE_OVERRIDES, SEVERITY_RULES

    # 1. Code-specific override (highest confidence)
    if code.upper() in CODE_OVERRIDES:
        confidence += 0.50
        evidence_parts.append("Code-specific override defined")

    # 2. Category match in rules
    desc_lower = description.lower() if description else ""
    system_lower = system.lower() if system else ""

    category_matched = False
    for rule in SEVERITY_RULES:
        category_lower = rule.category.lower()
        if category_lower in desc_lower or category_lower in system_lower:
            # Check if code is in rule examples (high confidence)
            if code.upper() in rule.examples:
                confidence += 0.40
                evidence_parts.append(f"Defined in '{rule.category}' rule examples")
            else:
                confidence += 0.35
                evidence_parts.append(f"Matches '{rule.category}' category")
            category_matched = True
            break

    # 3. Pattern-based classification confidence
    if not category_matched:
        # Pattern matches (EVAP, O2, misfire, etc.)
        if 'evap' in desc_lower or 'purge' in desc_lower:
            confidence += 0.25
            evidence_parts.append("EVAP pattern recognized")
        elif 'o2' in desc_lower or 'oxygen' in desc_lower:
            confidence += 0.25
            evidence_parts.append("O2 sensor pattern recognized")
        elif 'misfire' in desc_lower:
            confidence += 0.30
            evidence_parts.append("Misfire pattern recognized")
        elif 'sensor circuit' in desc_lower:
            confidence += 0.20
            evidence_parts.append("Sensor circuit pattern")
        elif 'brake' in desc_lower or 'abs' in desc_lower:
            confidence += 0.35
            evidence_parts.append("Safety system pattern")
        else:
            confidence += 0.10
            evidence_parts.append("Generic pattern match")

    # 4. Description quality
    if description and len(description) > 20:
        confidence += 0.10
        evidence_parts.append("Clear description")
    else:
        confidence -= 0.05
        evidence_parts.append("Vague description")

    # 5. System classification present
    if system and system != "Unknown System":
        confidence += 0.10
        evidence_parts.append("System classified")

    # 6. Well-known code patterns (boost confidence)
    code_prefix = code.upper()[:4] if code else ""
    evidence_str = "; ".join(evidence_parts)

    # EVAP codes (P04xx) are well-documented
    if code_prefix.startswith('P04') and 'evap' in desc_lower:
        confidence = max(confidence, 0.92)
        if "EVAP" not in evidence_str:
            evidence_parts.append("Well-documented EVAP code")

    # O2 sensor codes (P01xx) are well-documented
    if code_prefix.startswith('P01') and ('o2' in desc_lower or 'oxygen' in desc_lower):
        confidence = max(confidence, 0.92)
        if "O2" not in evidence_str:
            evidence_parts.append("Well-documented O2 sensor code")

    # Misfire codes (P030x) are critical and well-documented
    if code_prefix.startswith('P030') and 'misfire' in desc_lower:
        confidence = max(confidence, 0.95)
        if "misfire" not in evidence_str.lower():
            evidence_parts.append("Well-documented misfire code")

    # 7. Standardization vs actual change
    if current_severity == "Medium" and recommended_severity == "Moderate":
        # This is just terminology standardization (high confidence)
        confidence = max(confidence, 0.95)
        evidence_parts.append("Terminology standardization (Medium->Moderate)")
    elif current_severity == recommended_severity:
        # No change needed
        confidence = 1.0
        evidence_parts = ["No change required"]

    # Cap at 1.0
    confidence = min(confidence, 1.0)

    evidence = "; ".join(evidence_parts)
    return confidence, evidence


def classify_correction(
    code: str,
    description: str,
    system: str,
    current_severity: str
) -> SeverityCorrection:
    """
    Classify a severity correction with confidence assessment.

    Args:
        code: OBD-II code
        description: Code description
        system: Vehicle system
        current_severity: Current severity rating

    Returns:
        SeverityCorrection with confidence and recommended action
    """
    # Get recommended severity
    recommended_severity, reasoning = classify_severity(code, description, system)

    # Assess confidence
    confidence, evidence = assess_confidence(
        code, description, system,
        current_severity, recommended_severity, reasoning
    )

    # Determine confidence level and action
    if confidence >= 0.90:
        confidence_level = "high"
        action = "auto_apply"
    elif confidence >= 0.60:
        confidence_level = "medium"
        action = "queue_review"
    else:
        confidence_level = "low"
        action = "leave_unchanged"

    return SeverityCorrection(
        code=code,
        description=description,
        system=system,
        current_severity=current_severity,
        recommended_severity=recommended_severity,
        reasoning=reasoning,
        confidence=confidence,
        confidence_level=confidence_level,
        evidence=evidence,
        action=action
    )


def analyze_corrections(codes: list[dict]) -> dict:
    """
    Analyze all codes and categorize corrections by confidence.

    Args:
        codes: List of code records from database

    Returns:
        Statistics and categorized corrections
    """
    high_confidence = []
    medium_confidence = []
    low_confidence = []
    no_change = []

    for record in codes:
        code = record.get('code')
        description = record.get('description', '')
        system = record.get('system', 'Powertrain')
        current = record.get('severity')

        if not current:
            continue

        correction = classify_correction(code, description, system, current)

        if correction.current_severity == correction.recommended_severity:
            no_change.append(correction)
        elif correction.confidence_level == "high":
            high_confidence.append(correction)
        elif correction.confidence_level == "medium":
            medium_confidence.append(correction)
        else:
            low_confidence.append(correction)

    return {
        "high_confidence": high_confidence,
        "medium_confidence": medium_confidence,
        "low_confidence": low_confidence,
        "no_change": no_change,
        "stats": {
            "total": len(codes),
            "high_confidence": len(high_confidence),
            "medium_confidence": len(medium_confidence),
            "low_confidence": len(low_confidence),
            "no_change": len(no_change)
        }
    }


def generate_review_queue(corrections: list[SeverityCorrection], output_file: str):
    """
    Generate review queue document for medium/low confidence corrections.

    Args:
        corrections: List of corrections needing review
        output_file: Output filename
    """
    lines = [
        "# Severity Corrections Review Queue",
        f"\n**Total Corrections Needing Review:** {len(corrections)}",
        "\n---\n"
    ]

    for corr in corrections:
        lines.extend([
            f"\n## {corr.code} - {corr.description[:60]}...",
            f"\n**Current:** {corr.current_severity}",
            f"**Recommended:** {corr.recommended_severity}",
            f"**Confidence:** {corr.confidence:.0%} ({corr.confidence_level})",
            f"**Evidence:** {corr.evidence}",
            f"**Reasoning:** {corr.reasoning}",
            "\n**Review Decision:**",
            "- [ ] APPROVE (apply correction)",
            "- [ ] REJECT (keep current severity)",
            "- [ ] CUSTOM (specify alternative severity)",
            "\n**Notes:**\n",
            "\n---\n"
        ])

    content = "\n".join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Review queue generated: {output_file}")


if __name__ == "__main__":
    # Test cases
    print("=" * 80)
    print("CONFIDENCE-BASED SEVERITY CORRECTION")
    print("=" * 80)
    print()

    test_cases = [
        # High confidence (code-specific override)
        {
            "code": "P0450",
            "description": "EVAP System Pressure Sensor/Switch A Circuit",
            "system": "Powertrain",
            "current": "High"
        },
        # High confidence (clear EVAP pattern)
        {
            "code": "P0442",
            "description": "EVAP System Leak Detected (small leak)",
            "system": "Powertrain",
            "current": "High"
        },
        # Medium confidence (sensor circuit)
        {
            "code": "P0115",
            "description": "Engine Coolant Temperature Sensor Circuit",
            "system": "Powertrain",
            "current": "High"
        },
        # Low confidence (vague description)
        {
            "code": "P1234",
            "description": "Unknown Code",
            "system": "Unknown",
            "current": "Medium"
        }
    ]

    for test in test_cases:
        correction = classify_correction(
            test["code"],
            test["description"],
            test["system"],
            test["current"]
        )

        print(f"Code: {correction.code}")
        print(f"  Current: {correction.current_severity} -> Recommended: {correction.recommended_severity}")
        print(f"  Confidence: {correction.confidence:.0%} ({correction.confidence_level})")
        print(f"  Action: {correction.action}")
        print(f"  Evidence: {correction.evidence}")
        print()
