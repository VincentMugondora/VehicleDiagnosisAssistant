"""
Deterministic Severity Classification Rules

Replaces AI-based severity inference with expert-defined rules.
Based on automotive diagnostic standards and OEM practices.

Severity Levels:
- Critical: Safety systems, immediate danger, vehicle inoperable
- High: Engine damage risk, significant performance loss, urgent repair
- Moderate: Performance impact, emissions issues, moderate urgency
- Low: Minor issues, informational, low urgency
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SeverityRule:
    """Severity classification rule"""
    category: str
    default_severity: str
    reasoning: str
    examples: list[str]


# Expert-defined severity rules by diagnostic category
SEVERITY_RULES = [
    # CRITICAL - Safety systems, immediate danger
    SeverityRule(
        category="Brake System",
        default_severity="Critical",
        reasoning="Brake system failure poses immediate safety risk",
        examples=["C0035", "C0040", "C0045"]
    ),
    SeverityRule(
        category="ABS",
        default_severity="Critical",
        reasoning="Anti-lock brake system affects vehicle control",
        examples=["C0041", "C0050", "C0060"]
    ),
    SeverityRule(
        category="Airbag/SRS",
        default_severity="Critical",
        reasoning="Safety restraint system failure in crash",
        examples=["B0001", "B0010", "B0020"]
    ),
    SeverityRule(
        category="Steering",
        default_severity="Critical",
        reasoning="Steering system failure affects vehicle control",
        examples=["C0460", "C0461", "C0899"]
    ),
    SeverityRule(
        category="Oil Pressure",
        default_severity="Critical",
        reasoning="Low oil pressure can cause immediate engine damage",
        examples=["P0520", "P0521", "P0522"]
    ),
    SeverityRule(
        category="Coolant Overheating",
        default_severity="Critical",
        reasoning="Engine overheating can cause immediate damage",
        examples=["P0217", "P0218", "P0219"]
    ),

    # HIGH - Engine damage risk, urgent repair
    SeverityRule(
        category="Misfire Detected",
        default_severity="High",
        reasoning="Misfires can damage catalytic converter and engine",
        examples=["P0300", "P0301", "P0302", "P0303", "P0304"]
    ),
    SeverityRule(
        category="Knock Sensor",
        default_severity="High",
        reasoning="Undetected knock can cause engine damage",
        examples=["P0325", "P0326", "P0327", "P0328"]
    ),
    SeverityRule(
        category="Timing System",
        default_severity="High",
        reasoning="Timing issues can cause valve/piston damage",
        examples=["P0016", "P0017", "P0018"]
    ),
    SeverityRule(
        category="Turbo/Supercharger",
        default_severity="High",
        reasoning="Forced induction failure can damage engine",
        examples=["P0234", "P0235", "P0236", "P0237", "P0238"]
    ),
    SeverityRule(
        category="Fuel Pressure Low",
        default_severity="High",
        reasoning="Low fuel pressure can cause lean condition and damage",
        examples=["P0087", "P0088", "P0089"]
    ),
    SeverityRule(
        category="Head Gasket",
        default_severity="High",
        reasoning="Head gasket failure causes major engine damage",
        examples=["P0300", "P1316"]  # Often diagnosed with misfires
    ),
    SeverityRule(
        category="Transmission Failure",
        default_severity="High",
        reasoning="Transmission failure causes major repair expense",
        examples=["P0700", "P0735", "P0740"]
    ),

    # MODERATE - Performance impact, emissions, moderate urgency
    SeverityRule(
        category="EVAP System",
        default_severity="Moderate",
        reasoning="Emissions system, rarely affects drivability",
        examples=["P0440", "P0441", "P0442", "P0443", "P0446", "P0450", "P0451", "P0452", "P0453", "P0455", "P0456", "P0457"]
    ),
    SeverityRule(
        category="O2 Sensor",
        default_severity="Moderate",
        reasoning="Affects fuel trim and emissions, not immediate damage",
        examples=["P0130", "P0131", "P0132", "P0133", "P0134", "P0135", "P0136", "P0137", "P0138"]
    ),
    SeverityRule(
        category="Catalyst Efficiency",
        default_severity="Moderate",
        reasoning="Emissions issue, catalyst already damaged",
        examples=["P0420", "P0430", "P0421", "P0431"]
    ),
    SeverityRule(
        category="MAF/MAP Sensor",
        default_severity="Moderate",
        reasoning="Sensor issue affects performance, not critical",
        examples=["P0100", "P0101", "P0102", "P0103", "P0104", "P0105", "P0106"]
    ),
    SeverityRule(
        category="Fuel Trim",
        default_severity="Moderate",
        reasoning="Indicates lean/rich condition needing diagnosis",
        examples=["P0171", "P0172", "P0174", "P0175"]
    ),
    SeverityRule(
        category="EGR System",
        default_severity="Moderate",
        reasoning="Emissions system, moderate performance impact",
        examples=["P0400", "P0401", "P0402", "P0403", "P0404", "P0405"]
    ),
    SeverityRule(
        category="Thermostat",
        default_severity="Moderate",
        reasoning="Affects engine warmup and efficiency",
        examples=["P0125", "P0128", "P0126"]
    ),
    SeverityRule(
        category="Idle Control",
        default_severity="Moderate",
        reasoning="Idle quality issue, not critical",
        examples=["P0505", "P0506", "P0507", "P0508", "P0509"]
    ),
    SeverityRule(
        category="VVT/Cam Timing",
        default_severity="Moderate",
        reasoning="Variable valve timing performance issue",
        examples=["P0010", "P0011", "P0012", "P0013", "P0014", "P0015", "P0016", "P0017", "P0018", "P0019"]
    ),
    SeverityRule(
        category="Sensor Circuit",
        default_severity="Moderate",
        reasoning="Sensor circuit issue, not actual component failure",
        examples=[]  # Pattern-based, not specific codes
    ),

    # LOW - Minor issues, informational
    SeverityRule(
        category="Monitor Not Ready",
        default_severity="Low",
        reasoning="Informational, not actual malfunction",
        examples=["P1000"]
    ),
    SeverityRule(
        category="Fuel Cap",
        default_severity="Low",
        reasoning="Usually just loose fuel cap",
        examples=["P0457", "P0458"]
    ),
]


# Code-specific overrides (when specific DTC differs from category default)
CODE_OVERRIDES = {
    # EVAP large leaks may be more urgent than small leaks
    "P0455": ("Moderate", "Large EVAP leak may affect drivability"),

    # Catalyst damage codes (already failed, not failing)
    "P0420": ("Moderate", "Catalyst efficiency below threshold - already damaged"),
    "P0430": ("Moderate", "Catalyst efficiency below threshold - already damaged"),

    # Coolant temp below thermostat (low severity)
    "P0128": ("Moderate", "Thermostat issue affects warmup time"),

    # Random misfire is higher priority than single cylinder
    "P0300": ("High", "Random/multiple cylinder misfire - diagnose urgently"),

    # Specific critical codes
    "P0217": ("Critical", "Engine coolant over-temperature - stop immediately"),
    "P0218": ("Critical", "Transmission fluid over-temperature - stop immediately"),
    "P0522": ("Critical", "Engine oil pressure sensor low - verify actual pressure"),
}


def classify_severity(code: str, description: str, system: str) -> tuple[str, str]:
    """
    Classify severity using deterministic rules.

    Args:
        code: OBD-II code (e.g., "P0420")
        description: Code description
        system: Vehicle system

    Returns:
        (severity_level, reasoning)
    """
    code_upper = code.upper()
    desc_lower = description.lower() if description else ""
    system_lower = system.lower() if system else ""

    # Check code-specific overrides first
    if code_upper in CODE_OVERRIDES:
        return CODE_OVERRIDES[code_upper]

    # Check category-based rules
    for rule in SEVERITY_RULES:
        category_lower = rule.category.lower()

        # Check if code matches category examples
        if code_upper in rule.examples:
            return rule.default_severity, rule.reasoning

        # Check if description/system matches category
        if category_lower in desc_lower or category_lower in system_lower:
            return rule.default_severity, rule.reasoning

    # Pattern-based classification

    # Brake system codes (C00xx, C04xx range)
    if code_upper.startswith('C') and 'brake' in desc_lower:
        return "Critical", "Brake system failure poses immediate safety risk"

    # ABS codes
    if 'abs' in desc_lower or 'anti-lock' in desc_lower:
        return "Critical", "Anti-lock brake system affects vehicle control"

    # Airbag/SRS codes (B-codes related to restraints)
    if code_upper.startswith('B') and ('airbag' in desc_lower or 'srs' in desc_lower or 'restraint' in desc_lower):
        return "Critical", "Safety restraint system failure in crash"

    # EVAP codes (P04xx range)
    if code_upper.startswith('P04') and ('evap' in desc_lower or 'purge' in desc_lower or 'vent' in desc_lower):
        return "Moderate", "EVAP system - emissions primarily, rarely drivability"

    # O2 sensor codes (P01xx range)
    if code_upper.startswith('P01') and ('o2' in desc_lower or 'oxygen' in desc_lower or 'sensor' in desc_lower):
        return "Moderate", "O2 sensor issue - affects fuel trim and emissions"

    # Misfire codes (P030x)
    if code_upper.startswith('P030') and 'misfire' in desc_lower:
        if 'detected' in desc_lower:
            return "High", "Misfire can damage catalytic converter"
        else:
            return "Moderate", "Misfire detection circuit issue"

    # Sensor circuit codes (typically moderate)
    if 'sensor circuit' in desc_lower or 'circuit range' in desc_lower:
        return "Moderate", "Sensor circuit issue - electrical/sensor problem"

    # Default to Moderate for unknown codes
    return "Moderate", "Standard diagnostic code - diagnose to determine urgency"


def get_severity_explanation(severity: str, reasoning: str) -> str:
    """
    Generate human-readable severity explanation.

    Args:
        severity: Severity level
        reasoning: Rule reasoning

    Returns:
        User-facing explanation
    """
    templates = {
        "Critical": (
            f"{reasoning}. Have the vehicle towed to a qualified technician "
            "immediately. Do not drive the vehicle."
        ),
        "High": (
            f"{reasoning}. Have the vehicle diagnosed by a qualified technician "
            "as soon as possible. Continued driving may cause expensive damage."
        ),
        "Moderate": (
            f"{reasoning}. Have the vehicle diagnosed at your earliest convenience. "
            "The vehicle is usually drivable, but the issue should be addressed "
            "to prevent further problems and restore proper operation."
        ),
        "Low": (
            f"{reasoning}. This code indicates a minor issue that is unlikely "
            "to cause immediate problems. Address it at your next scheduled service."
        )
    }

    return templates.get(severity, templates["Moderate"])


def validate_severity_classification():
    """
    Validate severity rules against test cases.
    Returns list of validation results.
    """
    test_cases = [
        # Critical
        ("C0035", "ABS System Malfunction", "Brakes", "Critical"),
        ("B0001", "Airbag Deployment Control", "SRS", "Critical"),
        ("P0522", "Engine Oil Pressure Sensor Low", "Powertrain", "Critical"),

        # High
        ("P0300", "Random/Multiple Cylinder Misfire Detected", "Powertrain", "High"),
        ("P0301", "Cylinder 1 Misfire Detected", "Powertrain", "High"),
        ("P0325", "Knock Sensor 1 Circuit Bank 1", "Powertrain", "High"),

        # Moderate
        ("P0420", "Catalyst System Efficiency Below Threshold Bank 1", "Powertrain", "Moderate"),
        ("P0450", "EVAP System Pressure Sensor/Switch A Circuit", "Powertrain", "Moderate"),
        ("P0171", "System Too Lean Bank 1", "Powertrain", "Moderate"),
        ("P0130", "O2 Sensor Circuit Bank 1 Sensor 1", "Powertrain", "Moderate"),
        ("P0128", "Coolant Thermostat Temperature Below Thermostat", "Powertrain", "Moderate"),

        # Low
        ("P1000", "OBD System Readiness Test Not Complete", "Powertrain", "Low"),
    ]

    results = []
    for code, desc, system, expected in test_cases:
        severity, reasoning = classify_severity(code, desc, system)
        passed = severity == expected
        results.append({
            'code': code,
            'expected': expected,
            'actual': severity,
            'passed': passed,
            'reasoning': reasoning
        })

    return results


if __name__ == "__main__":
    print("=" * 80)
    print("SEVERITY CLASSIFICATION RULE VALIDATION")
    print("=" * 80)
    print()

    results = validate_severity_classification()

    passed = sum(1 for r in results if r['passed'])
    total = len(results)

    for r in results:
        status = "PASS" if r['passed'] else "FAIL"
        print(f"[{status}] {r['code']:8} Expected: {r['expected']:10} Got: {r['actual']:10}")
        if not r['passed']:
            print(f"        Reasoning: {r['reasoning']}")

    print()
    print(f"Validation: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print()
