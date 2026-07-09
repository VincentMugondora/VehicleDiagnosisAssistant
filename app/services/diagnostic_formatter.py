"""
Diagnostic Report Formatter

Pure presentation layer for diagnostic results.
No automotive knowledge - only formatting structured data.

All diagnostic intelligence (symptoms, severity, tips, checks) comes from:
1. Database (preferred)
2. AI generation (when database incomplete)
3. Minimal generic fallback (only when both unavailable)
"""

from typing import Optional
from app.models.diagnostic import DiagnosticResult


class DiagnosticReportFormatter:
    """
    Formats diagnostic results into standardized professional reports.

    DESIGN PRINCIPLE: Presentation only, no inference.
    This formatter should NOT contain automotive knowledge.
    All diagnostic intelligence should come from the DiagnosticResult model.
    """

    def __init__(self, result: DiagnosticResult):
        self.result = result

    def format_full_report(self) -> str:
        """
        Generate complete diagnostic report with all sections.

        Returns:
            Formatted markdown report string
        """
        sections = []

        # Header
        sections.append(self._format_header())

        # What it means
        sections.append(self._format_description())

        # Common symptoms (from database/AI)
        if self.result.symptoms:
            sections.append(self._format_symptoms())

        # Likely causes (from database/AI)
        if self.result.causes:
            sections.append(self._format_causes())

        # Recommended diagnostic steps (from database/AI)
        if self.result.checks:
            sections.append(self._format_diagnostic_steps())

        # Severity (from database/AI)
        if self.result.severity:
            sections.append(self._format_severity())

        # Pre-replacement checks (from database/AI)
        if self.result.pre_replacement_checks:
            sections.append(self._format_pre_replacement_checks())

        # Technician tip (from database/AI)
        if self.result.technician_tip:
            sections.append(self._format_technician_tip())

        # Footer disclaimer
        sections.append(self._format_footer())

        return "\n\n".join(filter(None, sections))

    def _format_header(self) -> str:
        """Format fault code header"""
        system = self.result.system or "Unknown System"
        return f"""🔧 *Fault Code: {self.result.code}*

*System:* {system}"""

    def _format_description(self) -> str:
        """Format 'What it means' section"""
        return f"""📖 *What it means*

{self.result.description}"""

    def _format_symptoms(self) -> str:
        """Format common symptoms section (from database/AI)"""
        symptoms = self.result.symptoms[:8]  # Limit to 8
        symptom_list = "\n".join(f"• {s}" for s in symptoms)
        return f"""🚗 *Common symptoms*

{symptom_list}"""

    def _format_causes(self) -> str:
        """Format likely causes section (from database/AI)"""
        causes_list = "\n".join(
            f"• {cause}"
            for cause in self.result.causes[:6]
        )

        return f"""🔍 *Likely causes*

{causes_list}"""

    def _format_diagnostic_steps(self) -> str:
        """Format recommended diagnostic steps section (from database/AI)"""
        steps_list = "\n".join(
            f"{i+1}. {step}"
            for i, step in enumerate(self.result.checks[:8])
        )

        return f"""🛠️ *Recommended diagnostic steps*

{steps_list}"""

    def _format_severity(self) -> str:
        """Format severity section (from database/AI)"""
        severity = self.result.severity
        explanation = self.result.severity_explanation or self._get_fallback_severity_explanation(severity)

        return f"""⚠️ *Severity*

*{severity}*

{explanation}"""

    def _format_pre_replacement_checks(self) -> str:
        """Format pre-replacement checks section (from database/AI)"""
        checks_list = "\n".join(
            f"• {check}"
            for check in self.result.pre_replacement_checks[:5]
        )

        return f"""❌ *Do NOT replace parts until*

{checks_list}"""

    def _format_technician_tip(self) -> str:
        """Format technician tip section (from database/AI)"""
        return f"""💡 *Technician Tip*

{self.result.technician_tip}"""

    def _format_footer(self) -> str:
        """Format footer disclaimer"""
        return "> _Always confirm the diagnosis using live scanner data and manufacturer service information before replacing parts._"

    def _get_fallback_severity_explanation(self, severity: str) -> str:
        """
        Minimal generic fallback for severity explanation.
        Only used when database/AI don't provide one.

        Args:
            severity: Severity level

        Returns:
            Generic explanation string
        """
        fallbacks = {
            "Critical": "This code indicates a safety-critical system failure. Have the vehicle diagnosed and repaired immediately by a qualified technician.",
            "High": "This code can lead to engine damage if left unaddressed. Avoid prolonged driving and have the vehicle diagnosed soon.",
            "Moderate": "This code should be diagnosed and repaired to prevent potential damage and restore proper vehicle performance. The vehicle is usually drivable, but prolonged operation may reduce efficiency or cause further issues.",
            "Low": "This code indicates a minor issue that is unlikely to cause immediate damage. Address it at your next scheduled service to prevent future problems."
        }

        return fallbacks.get(severity, fallbacks["Moderate"])


def format_diagnostic_report(result: DiagnosticResult) -> str:
    """
    Format a diagnostic result into a standardized professional report.

    This is a pure presentation function.
    All diagnostic intelligence should already be in the DiagnosticResult.

    Args:
        result: DiagnosticResult with all fields populated

    Returns:
        Formatted diagnostic report string
    """
    formatter = DiagnosticReportFormatter(result)
    return formatter.format_full_report()
