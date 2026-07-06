"""
Component name extraction from OBD code descriptions.

Maps OBD code descriptions to system diagram component names.
"""
import re
from typing import Optional
from app.core.logging import logger


# Mapping patterns: regex pattern -> component name
COMPONENT_PATTERNS = [
    # Exhaust & Emissions
    (r'\bcatalyst\b|\bcatalytic converter\b', 'catalytic converter'),
    (r'\bo2\s*sensor\b|\boxygen sensor\b|\blambda\s*sensor\b', 'oxygen sensor'),
    (r'\begr\b|\bexhaust gas recirculation\b', 'egr valve'),
    (r'\bevap\b|\bevaporative\s*emission', 'evap system'),

    # Air Intake
    (r'\bmaf\b|\bmass air flow\b', 'mass air flow sensor'),
    (r'\bmap\b|\bmanifold absolute pressure\b', 'map sensor'),
    (r'\bthrottle\s*body\b|\bthrottle\s*position', 'throttle body'),
    (r'\bintake\s*manifold\b|\bair\s*intake', 'air intake manifold'),

    # Ignition & Fuel
    (r'\bignition\s*coil\b', 'ignition coil'),
    (r'\bspark\s*plug', 'spark plug'),
    (r'\bfuel\s*injector', 'fuel injector'),
    (r'\bfuel\s*pump', 'fuel pump'),

    # Sensors
    (r'\bcamshaft\s*position\s*sensor', 'camshaft position sensor'),
    (r'\bcrankshaft\s*position\s*sensor', 'crankshaft position sensor'),
    (r'\bknock\s*sensor', 'knock sensor'),
    (r'\bcoolant\s*temp', 'coolant temperature sensor'),

    # Cooling System
    (r'\bthermostat\b', 'thermostat'),
    (r'\bradiator\b', 'radiator'),

    # Engine Mechanical
    (r'\btiming\s*belt\b|\btiming\s*chain\b', 'timing belt'),
    (r'\bpcv\s*valve\b|\bpositive\s*crankcase', 'pcv valve'),

    # Electrical
    (r'\balternator\b', 'alternator'),
    (r'\bbattery\b', 'battery'),

    # Brakes
    (r'\bbrake\s*pad', 'brake pads'),
    (r'\bwheel\s*speed\s*sensor', 'wheel speed sensor'),

    # Transmission
    (r'\btransmission\b|\bgearbox\b', 'transmission'),
]


def extract_component_from_description(description: str, code: str = None) -> Optional[str]:
    """
    Extract component name from OBD code description.

    Args:
        description: OBD code description (e.g., "Catalyst System Efficiency Below Threshold")
        code: Optional OBD code for logging

    Returns:
        Component name if found, None otherwise

    Examples:
        >>> extract_component_from_description("Catalyst System Efficiency Below Threshold")
        'catalytic converter'

        >>> extract_component_from_description("O2 Sensor Circuit Bank 1 Sensor 1")
        'oxygen sensor'

        >>> extract_component_from_description("Throttle Position Sensor Range/Performance")
        'throttle body'
    """
    if not description:
        return None

    # Normalize: lowercase for pattern matching
    desc_lower = description.lower()

    # Try each pattern
    for pattern, component in COMPONENT_PATTERNS:
        if re.search(pattern, desc_lower, re.IGNORECASE):
            logger.debug(
                "component_extracted_from_description",
                code=code,
                description=description[:50],
                component=component,
                pattern=pattern
            )
            return component

    # No match found
    logger.debug(
        "no_component_match",
        code=code,
        description=description[:50]
    )
    return None


def extract_component_from_code(code_obj) -> Optional[str]:
    """
    Extract component name from OBD code object.

    Tries multiple fields in priority order:
    1. description field (most specific)
    2. code prefix patterns (fallback)

    Args:
        code_obj: OBD code object with description, code, etc.

    Returns:
        Component name if found, None otherwise
    """
    # Try description first
    if hasattr(code_obj, 'description') and code_obj.description:
        component = extract_component_from_description(
            code_obj.description,
            code=getattr(code_obj, 'code', None)
        )
        if component:
            return component

    # Fallback: try code patterns (e.g., P0420-P0434 = catalyst)
    if hasattr(code_obj, 'code') and code_obj.code:
        component = extract_component_from_code_prefix(code_obj.code)
        if component:
            return component

    return None


def extract_component_from_code_prefix(code: str) -> Optional[str]:
    """
    Extract component from DTC code prefix patterns.

    Some codes have predictable ranges for specific components.

    Args:
        code: OBD code (e.g., "P0420")

    Returns:
        Component name if pattern matches, None otherwise
    """
    if not code:
        return None

    code_upper = code.upper()

    # Catalyst system codes
    if code_upper in ['P0420', 'P0421', 'P0422', 'P0423', 'P0424',
                       'P0430', 'P0431', 'P0432', 'P0433', 'P0434']:
        return 'catalytic converter'

    # O2 sensor codes (P0130-P0167, P0131-P0135, etc.)
    if code_upper.startswith('P013') or code_upper.startswith('P014') or \
       code_upper.startswith('P015') or code_upper.startswith('P016'):
        return 'oxygen sensor'

    # EGR codes (P0400-P0409)
    if code_upper.startswith('P040'):
        return 'egr valve'

    # EVAP codes (P0440-P0459)
    if code_upper.startswith('P044') or code_upper.startswith('P045'):
        return 'evap system'

    # MAF codes (P0100-P0104)
    if code_upper in ['P0100', 'P0101', 'P0102', 'P0103', 'P0104']:
        return 'mass air flow sensor'

    # Throttle codes (P0120-P0124)
    if code_upper in ['P0120', 'P0121', 'P0122', 'P0123', 'P0124']:
        return 'throttle body'

    # Misfire codes (P0300-P0312) - could be ignition coil or spark plug
    if code_upper.startswith('P030'):
        return 'ignition coil'

    # Fuel injector codes (P0200-P0212)
    if code_upper.startswith('P020') or code_upper.startswith('P021'):
        return 'fuel injector'

    # Coolant temp sensor (P0115-P0119)
    if code_upper in ['P0115', 'P0116', 'P0117', 'P0118', 'P0119']:
        return 'coolant temperature sensor'

    # Thermostat (P0125, P0128)
    if code_upper in ['P0125', 'P0128']:
        return 'thermostat'

    return None
