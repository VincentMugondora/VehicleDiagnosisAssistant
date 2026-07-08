"""
Component name extraction from OBD code descriptions with confidence scoring.

Maps OBD code descriptions to component registry entries with accuracy scores.
Only returns high-confidence matches (≥80%) to prevent misleading images.
"""
import re
from typing import Optional
from app.core.logging import logger
from app.models.component_registry import (
    ComponentDefinition,
    ComponentMatch,
    get_component_by_name,
    get_all_components,
    MatchConfidence
)


# Minimum confidence threshold for image sending
CONFIDENCE_THRESHOLD = 80


# =============================================================================
# COMPONENT EXTRACTION PATTERNS
# =============================================================================
# These patterns extract component names from OBD descriptions
# Pattern -> canonical_name mapping
# =============================================================================

COMPONENT_PATTERNS = [
    # Exhaust & Emissions
    (r'\bcatalyst\b|\bcatalytic converter\b', 'catalytic converter'),
    (r'\bo2\s*sensor\b|\boxygen sensor\b|\blambda\s*sensor\b', 'oxygen sensor'),
    (r'\begr\b|\bexhaust gas recirculation\b', 'egr valve'),
    (r'\bevap\b|\bevaporative\s*emission|\bpurge\s*valve', 'evap system'),

    # Air Intake
    (r'\bmaf\b|\bmass.*air\s*flow|\bair\s*flow\s*sensor', 'mass air flow sensor'),
    (r'\bthrottle\s*body\b|\bthrottle\s*position|\bthrottle\s*actuator', 'throttle body'),

    # Ignition & Fuel
    (r'\bignition\s*coil\b', 'ignition coil'),
    (r'\bfuel\s*injector|\binjector\b|\binjection\b', 'fuel injector'),

    # Sensors
    (r'\bcamshaft\s*position', 'camshaft position sensor'),
    (r'\bcrankshaft\s*position', 'crankshaft position sensor'),
    (r'\bwheel\s*speed', 'wheel speed sensor'),
    (r'\bcoolant.*temp|\bect\s*sensor|\bcoolant\s*sensor', 'engine coolant temperature sensor'),

    # Electrical
    (r'\bbattery\b', 'battery'),

    # Transmission
    (r'\btransmission\b|\bgearbox\b', 'transmission'),
]


def extract_component_from_description(
    description: str,
    code: Optional[str] = None
) -> Optional[ComponentMatch]:
    """
    Extract component name from OBD code description with confidence score.

    Args:
        description: OBD code description (e.g., "Catalyst System Efficiency Below Threshold")
        code: Optional OBD code for logging

    Returns:
        ComponentMatch with component definition and confidence, or None if no match

    Examples:
        >>> match = extract_component_from_description("Catalyst System Efficiency Below Threshold")
        >>> match.component.canonical_name
        'catalytic converter'
        >>> match.confidence
        100

        >>> match = extract_component_from_description("O2 Sensor Circuit Bank 1 Sensor 1")
        >>> match.component.canonical_name
        'oxygen sensor'
        >>> match.confidence
        95
    """
    if not description:
        return None

    # Normalize: lowercase for pattern matching
    desc_lower = description.lower()

    # Try each pattern
    for pattern, canonical_name in COMPONENT_PATTERNS:
        if re.search(pattern, desc_lower, re.IGNORECASE):
            # Get component from registry
            component = get_component_by_name(canonical_name)
            if not component:
                logger.warning(
                    "component_in_pattern_but_not_in_registry",
                    canonical_name=canonical_name,
                    code=code
                )
                continue

            # Determine confidence based on what matched
            # Extract the actual matched text
            match_obj = re.search(pattern, desc_lower, re.IGNORECASE)
            if match_obj:
                matched_text = match_obj.group(0).strip()
                confidence = component.get_confidence_for_match(matched_text)

                # If exact pattern match from our list, use EXACT confidence
                if confidence == 0:
                    confidence = MatchConfidence.EXACT.value

                result = ComponentMatch(
                    component=component,
                    confidence=confidence,
                    matched_text=matched_text
                )

                logger.debug(
                    "component_extracted_from_description",
                    code=code,
                    description=description[:50],
                    component=canonical_name,
                    confidence=confidence,
                    matched_text=matched_text
                )

                return result

    # No match found
    logger.debug(
        "no_component_match",
        code=code,
        description=description[:50]
    )
    return None


def extract_component_from_code_prefix(code: str) -> Optional[ComponentMatch]:
    """
    Extract component from DTC code prefix patterns with confidence.

    Some codes have predictable ranges for specific components.

    Args:
        code: OBD code (e.g., "P0420")

    Returns:
        ComponentMatch if pattern matches, None otherwise

    Examples:
        >>> match = extract_component_from_code_prefix("P0420")
        >>> match.component.canonical_name
        'catalytic converter'
        >>> match.confidence
        100
    """
    if not code:
        return None

    code_upper = code.upper()
    canonical_name = None
    confidence = MatchConfidence.EXACT.value  # Code ranges are exact

    # Catalyst system codes
    if code_upper in ['P0420', 'P0421', 'P0422', 'P0423', 'P0424',
                       'P0430', 'P0431', 'P0432', 'P0433', 'P0434']:
        canonical_name = 'catalytic converter'

    # O2 sensor codes (P0130-P0167)
    elif code_upper.startswith('P013') or code_upper.startswith('P014') or \
         code_upper.startswith('P015') or code_upper.startswith('P016'):
        canonical_name = 'oxygen sensor'

    # EGR codes (P0400-P0409)
    elif code_upper.startswith('P040'):
        canonical_name = 'egr valve'

    # EVAP codes (P0440-P0459)
    elif code_upper.startswith('P044') or code_upper.startswith('P045'):
        canonical_name = 'evap system'

    # MAF codes (P0100-P0104)
    elif code_upper in ['P0100', 'P0101', 'P0102', 'P0103', 'P0104']:
        canonical_name = 'mass air flow sensor'

    # Throttle codes (P0120-P0124)
    elif code_upper in ['P0120', 'P0121', 'P0122', 'P0123', 'P0124']:
        canonical_name = 'throttle body'

    # Misfire codes (P0300-P0312) - ignition coil
    elif code_upper.startswith('P030'):
        canonical_name = 'ignition coil'

    # Fuel injector codes (P0200-P0212)
    elif code_upper.startswith('P020') or code_upper.startswith('P021'):
        canonical_name = 'fuel injector'

    if canonical_name:
        component = get_component_by_name(canonical_name)
        if component:
            return ComponentMatch(
                component=component,
                confidence=confidence,
                matched_text=code_upper
            )

    return None


def should_send_image(match: Optional[ComponentMatch]) -> bool:
    """
    Determine if an image should be sent based on match confidence.

    Args:
        match: ComponentMatch or None

    Returns:
        True if confidence ≥ 80% and image exists, False otherwise

    Decision Logic:
        - No match: False
        - Confidence < 80%: False (too uncertain)
        - Confidence ≥ 80% AND image exists: True
        - Confidence ≥ 80% AND no image: False (no image available)
    """
    if not match:
        return False

    if match.confidence < CONFIDENCE_THRESHOLD:
        logger.info(
            "image_skipped_low_confidence",
            component=match.component.canonical_name,
            confidence=match.confidence,
            threshold=CONFIDENCE_THRESHOLD
        )
        return False

    if not match.component.image_filename:
        logger.info(
            "image_skipped_no_file",
            component=match.component.canonical_name,
            confidence=match.confidence
        )
        return False

    return True


def extract_best_component_match(
    description: str,
    code: Optional[str] = None
) -> Optional[ComponentMatch]:
    """
    Extract the best component match from description and code.

    Tries multiple extraction methods and returns highest confidence match.

    Priority order:
    1. Description pattern match (most specific)
    2. Code prefix pattern match (fallback)

    Args:
        description: OBD code description
        code: OBD code

    Returns:
        Best ComponentMatch or None
    """
    # Try description first (most specific)
    if description:
        match = extract_component_from_description(description, code)
        if match:
            return match

    # Fallback to code prefix patterns
    if code:
        match = extract_component_from_code_prefix(code)
        if match:
            logger.debug(
                "component_extracted_from_code_prefix",
                code=code,
                component=match.component.canonical_name,
                confidence=match.confidence
            )
            return match

    return None


# =============================================================================
# STATISTICS & MONITORING
# =============================================================================

def get_component_coverage_stats() -> dict:
    """
    Get statistics about component coverage.

    Returns:
        Dict with coverage statistics:
        - total_components: Total components in registry
        - components_with_images: Components that have images
        - components_without_images: Components needing images
        - coverage_percentage: Percentage with images
    """
    all_components = get_all_components()
    with_images = [c for c in all_components if c.image_filename]
    without_images = [c for c in all_components if not c.image_filename]

    return {
        "total_components": len(all_components),
        "components_with_images": len(with_images),
        "components_without_images": len(without_images),
        "coverage_percentage": round(len(with_images) / len(all_components) * 100, 1) if all_components else 0,
        "components_needing_images": [c.canonical_name for c in without_images]
    }
