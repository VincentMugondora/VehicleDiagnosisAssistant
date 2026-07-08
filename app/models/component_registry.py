"""
Component Registry - Single Source of Truth for Component-to-Image Mapping

This module defines all supported automotive components with their:
- Canonical names
- Aliases and synonyms
- Image mappings
- Confidence scoring rules

Design Principles:
1. Accuracy over coverage - only send images for high-confidence matches
2. Easy extensibility - adding new components requires no code changes
3. Maintainability - all component metadata in one place
"""
from typing import Optional, List, Dict, NamedTuple
from dataclasses import dataclass
from enum import Enum


class MatchConfidence(Enum):
    """Confidence levels for component matches"""
    EXACT = 100          # Exact canonical name match
    HIGH_SYNONYM = 95    # Approved high-confidence synonym
    MEDIUM_SYNONYM = 85  # Common alternative name
    LOW_SYNONYM = 80     # Less common but valid synonym
    NO_MATCH = 0         # No match found


@dataclass
class ComponentDefinition:
    """
    Definition of a supported automotive component.

    Attributes:
        canonical_name: Official component name (lowercase, used as key)
        display_name: Human-readable display name
        aliases: List of synonyms/alternative names with confidence scores
        image_filename: Filename in app/static/images/ (None if no image)
        category: Component category (exhaust, ignition, sensors, etc.)
        description: Brief description for documentation
    """
    canonical_name: str
    display_name: str
    aliases: List[tuple[str, int]]  # (alias, confidence_score)
    image_filename: Optional[str]
    category: str
    description: str

    def get_confidence_for_match(self, matched_text: str) -> int:
        """
        Get confidence score for a matched text.

        Args:
            matched_text: The text that was matched (lowercase)

        Returns:
            Confidence score (0-100)
        """
        # Exact match with canonical name
        if matched_text == self.canonical_name:
            return MatchConfidence.EXACT.value

        # Check aliases
        for alias, confidence in self.aliases:
            if matched_text == alias:
                return confidence

        return MatchConfidence.NO_MATCH.value


class ComponentMatch(NamedTuple):
    """Result of a component matching operation"""
    component: ComponentDefinition
    confidence: int
    matched_text: str


# =============================================================================
# COMPONENT REGISTRY
# =============================================================================
#
# To add a new component:
# 1. Add a new ComponentDefinition below
# 2. Place the image file in app/static/images/
# 3. That's it - no code changes needed!
#
# Confidence Scoring Guide:
#   100: Exact canonical name
#   95:  Official technical term (e.g., "MAF" for "mass air flow sensor")
#   85:  Common industry synonym (e.g., "cat" for "catalytic converter")
#   80:  Valid but less common name
#   <80: DO NOT ADD - will not trigger image send
# =============================================================================

COMPONENT_REGISTRY: List[ComponentDefinition] = [
    # -------------------------------------------------------------------------
    # EXHAUST & EMISSIONS
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="catalytic converter",
        display_name="Catalytic Converter",
        aliases=[
            ("catalyst", 95),
            ("cat converter", 90),
            ("cat", 85),
            ("catalytic conv", 85),
        ],
        image_filename="catalytic-converter.svg",
        category="exhaust_emissions",
        description="Reduces harmful exhaust emissions by converting pollutants"
    ),

    ComponentDefinition(
        canonical_name="oxygen sensor",
        display_name="Oxygen Sensor",
        aliases=[
            ("o2 sensor", 95),
            ("lambda sensor", 95),
            ("o2", 90),
            ("lambda", 85),
            ("air fuel sensor", 80),
        ],
        image_filename="oxygen-sensor.svg",
        category="exhaust_emissions",
        description="Measures oxygen content in exhaust to optimize air-fuel ratio"
    ),

    ComponentDefinition(
        canonical_name="egr valve",
        display_name="EGR Valve",
        aliases=[
            ("egr", 95),
            ("exhaust gas recirculation valve", 95),
            ("exhaust gas recirculation", 90),
        ],
        image_filename="egr-valve.svg",
        category="exhaust_emissions",
        description="Recirculates exhaust gases to reduce NOx emissions"
    ),

    ComponentDefinition(
        canonical_name="evap system",
        display_name="EVAP System",
        aliases=[
            ("evap", 95),
            ("evaporative emission system", 95),
            ("evaporative emission", 90),
            ("purge valve", 85),
            ("canister purge valve", 85),
        ],
        image_filename="evap-system.svg",
        category="exhaust_emissions",
        description="Prevents fuel vapors from escaping to atmosphere"
    ),

    # -------------------------------------------------------------------------
    # AIR INTAKE
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="mass air flow sensor",
        display_name="MAF Sensor",
        aliases=[
            ("maf sensor", 95),
            ("maf", 95),
            ("mass airflow sensor", 95),
            ("air flow sensor", 85),
            ("airflow sensor", 85),
        ],
        image_filename="maf-sensor.svg",
        category="air_intake",
        description="Measures volume of air entering engine"
    ),

    ComponentDefinition(
        canonical_name="throttle body",
        display_name="Throttle Body",
        aliases=[
            ("throttle", 90),
            ("throttle position sensor", 85),
            ("tps", 85),
            ("throttle actuator", 80),
        ],
        image_filename="throttle-body.svg",
        category="air_intake",
        description="Controls air flow into engine based on accelerator pedal position"
    ),

    # -------------------------------------------------------------------------
    # IGNITION SYSTEM
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="ignition coil",
        display_name="Ignition Coil",
        aliases=[
            ("coil pack", 90),
            ("coil", 85),
            ("spark coil", 80),
        ],
        image_filename="ignition-coil.svg",
        category="ignition",
        description="Converts battery voltage to high voltage needed for spark plugs"
    ),

    # -------------------------------------------------------------------------
    # FUEL SYSTEM
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="fuel injector",
        display_name="Fuel Injector",
        aliases=[
            ("injector", 95),
            ("fuel injection", 85),
        ],
        image_filename="fuel-injector.svg",
        category="fuel",
        description="Sprays atomized fuel into combustion chamber"
    ),

    # -------------------------------------------------------------------------
    # SENSORS
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="camshaft position sensor",
        display_name="Camshaft Position Sensor",
        aliases=[
            ("cam sensor", 95),
            ("cmp sensor", 95),
            ("camshaft sensor", 95),
            ("cam position sensor", 90),
        ],
        image_filename="camshaft-sensor.svg",
        category="sensors",
        description="Monitors camshaft position for fuel injection and ignition timing"
    ),

    ComponentDefinition(
        canonical_name="crankshaft position sensor",
        display_name="Crankshaft Position Sensor",
        aliases=[
            ("crank sensor", 95),
            ("ckp sensor", 95),
            ("crankshaft sensor", 95),
            ("crank position sensor", 90),
        ],
        image_filename="crankshaft-sensor.svg",
        category="sensors",
        description="Monitors crankshaft position and RPM"
    ),

    ComponentDefinition(
        canonical_name="wheel speed sensor",
        display_name="Wheel Speed Sensor",
        aliases=[
            ("abs sensor", 90),
            ("speed sensor", 80),
        ],
        image_filename="wheel_speed_sensor_optimized.jpg",
        category="sensors",
        description="Monitors wheel rotation speed for ABS and traction control"
    ),

    # -------------------------------------------------------------------------
    # ELECTRICAL
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="battery",
        display_name="Battery",
        aliases=[
            ("car battery", 90),
            ("12v battery", 85),
        ],
        image_filename="battery_optimized.jpg",
        category="electrical",
        description="Stores electrical energy to start engine and power accessories"
    ),

    # -------------------------------------------------------------------------
    # TRANSMISSION
    # -------------------------------------------------------------------------
    ComponentDefinition(
        canonical_name="transmission",
        display_name="Transmission",
        aliases=[
            ("gearbox", 95),
            ("trans", 85),
            ("automatic transmission", 90),
            ("manual transmission", 90),
        ],
        image_filename="transmission_optimized.jpg",
        category="transmission",
        description="Transmits engine power to wheels with gear ratio control"
    ),
]


# Build lookup index for fast access
_REGISTRY_BY_CANONICAL_NAME: Dict[str, ComponentDefinition] = {
    comp.canonical_name: comp for comp in COMPONENT_REGISTRY
}


def get_component_by_name(canonical_name: str) -> Optional[ComponentDefinition]:
    """
    Get component definition by canonical name.

    Args:
        canonical_name: Component canonical name (lowercase)

    Returns:
        ComponentDefinition if found, None otherwise
    """
    return _REGISTRY_BY_CANONICAL_NAME.get(canonical_name.lower())


def get_all_components() -> List[ComponentDefinition]:
    """
    Get all registered components.

    Returns:
        List of all ComponentDefinition objects
    """
    return COMPONENT_REGISTRY.copy()


def get_components_by_category(category: str) -> List[ComponentDefinition]:
    """
    Get all components in a category.

    Args:
        category: Category name (e.g., "sensors", "ignition")

    Returns:
        List of ComponentDefinition objects in that category
    """
    return [comp for comp in COMPONENT_REGISTRY if comp.category == category]


def get_components_with_images() -> List[ComponentDefinition]:
    """
    Get all components that have images available.

    Returns:
        List of ComponentDefinition objects with image_filename set
    """
    return [comp for comp in COMPONENT_REGISTRY if comp.image_filename]


def get_components_without_images() -> List[ComponentDefinition]:
    """
    Get all components that need images.

    Returns:
        List of ComponentDefinition objects with image_filename=None
    """
    return [comp for comp in COMPONENT_REGISTRY if not comp.image_filename]
