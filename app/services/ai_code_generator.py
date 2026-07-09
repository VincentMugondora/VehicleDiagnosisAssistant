"""
AI Code Generator Service
Uses LLM to generate OBD code information from its training data.
More reliable than web scraping (no Cloudflare blocks).
"""

from typing import Dict, Any, Optional
from app.services.ai_client import AIClient
from app.core.logging import logger
import json


class AICodeGenerator:
    """Uses AI to generate OBD code information"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def generate_code_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to generate complete OBD code information.

        Args:
            code: OBD code (e.g., "P3499")

        Returns:
            Complete code data or None if generation fails
        """

        logger.info("ai_code_generation_started", code=code)

        # Build prompt for LLM
        prompt = self._build_generation_prompt(code)

        try:
            # Call AI to generate the data
            response = await self.ai_client.complete(
                prompt=prompt,
                temperature=0.2  # Lower temperature for factual generation
            )

            # Parse JSON response
            code_data = self._parse_ai_response(response, code)

            if code_data:
                logger.info("ai_code_generation_success", code=code)
                return code_data
            else:
                logger.warning("ai_code_generation_failed_parse", code=code)
                return None

        except Exception as e:
            logger.error("ai_code_generation_error", code=code, error=str(e))
            return None

    def _build_generation_prompt(self, code: str) -> str:
        """Build prompt for LLM to generate code information"""

        # Determine system from code prefix
        prefix = code[0].upper()
        system_map = {
            'P': 'Powertrain',
            'C': 'Chassis',
            'B': 'Body',
            'U': 'Network'
        }
        expected_system = system_map.get(prefix, 'Powertrain')

        return f"""You are an automotive diagnostic expert with knowledge of OBD-II diagnostic trouble codes.

Generate complete, accurate diagnostic information for OBD code **{code}**.

**Return ONLY a valid JSON object with this structure:**

{{
  "code": "{code}",
  "description": "Clear, technical description (30-70 chars)",
  "symptoms": "What the driver experiences (comma-separated, 4-8 items)",
  "common_causes": "Most likely causes (comma-separated, 4-6 items, ordered by likelihood)",
  "generic_fixes": "Diagnostic steps to identify the problem (comma-separated, 5-8 steps)",
  "system": "{expected_system}",
  "severity": "Critical|High|Moderate|Low",
  "severity_explanation": "Brief explanation of why this severity level (1-2 sentences)",
  "technician_tip": "One practical diagnostic tip that helps avoid unnecessary part replacement (1-2 sentences)",
  "pre_replacement_checks": "What to verify before replacing parts (comma-separated, 3-5 items)"
}}

**Guidelines:**

1. **Description**: Precise technical meaning of the code (30-70 chars)

2. **Symptoms**: What the DRIVER sees/feels
   - Always include "Check Engine Light illuminated" as first symptom
   - Add 3-7 more symptoms specific to this code
   - Be specific: "Engine hesitation during acceleration" not just "poor performance"

3. **Causes**: Root causes, most to least likely
   - Be specific: "Faulty knock sensor Bank 2" not "sensor failure"
   - Order by actual likelihood for this specific code
   - Avoid generic phrases

4. **Generic Fixes**: Diagnostic workflow, not just "replace X"
   - Start with inspection/testing steps
   - Include what to measure and verify
   - End with repair/replacement only after diagnosis
   - Example: "Test sensor resistance with multimeter" before "Replace sensor if out of spec"

5. **Severity**:
   - **Critical**: Safety systems (airbag, ABS, steering, brakes) - immediate attention required
   - **High**: Engine damage potential (misfire, knock sensor, overheating, oil pressure)
   - **Moderate**: Performance/emissions issues, drivable but should be fixed soon
   - **Low**: Minor issues that can wait (EVAP small leak, pending codes)

6. **Severity Explanation**: Why this level?
   - Explain the risk: "Can lead to engine damage" or "Minor issue, no immediate risk"
   - Mention driveability: "Vehicle usually drivable" or "May enter limp mode"

7. **Technician Tip**: Practical advice to save time/money
   - Focus on common mistakes: "Many X codes are caused by Y, not Z"
   - Highlight what to check first: "Before replacing sensor, check wiring"
   - Mention known issues: "Common on [vehicle type] due to [reason]"

8. **Pre-replacement Checks**: What to verify BEFORE buying parts
   - Wiring/connector inspection
   - Voltage/resistance testing
   - Live scanner data verification
   - Related component testing

**Important:**
- DO NOT include markdown, code blocks, or explanations
- Return ONLY the JSON object
- Use professional but accessible language
- Be specific and actionable
- If this is a rare code, provide best available information

Generate the JSON now:"""

    def _parse_ai_response(
        self,
        response: str,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """Parse AI response and validate structure"""

        try:
            # Extract JSON from response
            json_match = response.strip()

            # Remove markdown code blocks if present
            if '```' in json_match:
                parts = json_match.split('```')
                for part in parts:
                    if part.strip().startswith('{'):
                        json_match = part.strip()
                        break
                    elif 'json' in part.lower():
                        continue
                    elif part.strip().startswith('{'):
                        json_match = part.strip()
                        break

            # Parse JSON
            data = json.loads(json_match)

            # Validate required fields
            required_fields = [
                'code', 'description', 'symptoms',
                'common_causes', 'generic_fixes', 'system', 'severity',
                'severity_explanation', 'technician_tip', 'pre_replacement_checks'
            ]

            for field in required_fields:
                if field not in data or not data[field]:
                    logger.warning(
                        "ai_response_missing_field",
                        code=code,
                        field=field
                    )
                    # Don't fail completely - just log and continue
                    # Allow partial data to be saved
                    if field in ['code', 'description', 'system']:
                        # Critical fields - must have
                        return None
                    else:
                        # Optional enrichment fields - set defaults
                        if field == 'severity':
                            data[field] = 'Moderate'
                        elif field == 'severity_explanation':
                            data[field] = 'Should be diagnosed and repaired to maintain vehicle performance.'
                        elif field == 'technician_tip':
                            data[field] = 'Always verify diagnosis with live scanner data before replacing parts.'
                        elif field == 'symptoms':
                            data[field] = 'Check Engine Light illuminated'
                        elif field == 'pre_replacement_checks':
                            data[field] = 'Wiring and connectors inspected, Live scanner data verified'

            # Validate system
            valid_systems = ['Powertrain', 'Chassis', 'Body', 'Network']
            if data['system'] not in valid_systems:
                # Fix common variations
                system_lower = data['system'].lower()
                if 'power' in system_lower or 'engine' in system_lower:
                    data['system'] = 'Powertrain'
                elif 'chassis' in system_lower or 'brake' in system_lower:
                    data['system'] = 'Chassis'
                elif 'body' in system_lower or 'airbag' in system_lower:
                    data['system'] = 'Body'
                elif 'network' in system_lower or 'communication' in system_lower:
                    data['system'] = 'Network'
                else:
                    logger.warning("ai_response_invalid_system", code=code)
                    data['system'] = 'Powertrain'  # Default fallback

            # Validate severity
            if data['severity'] not in ['Critical', 'High', 'Moderate', 'Low']:
                logger.warning("ai_response_invalid_severity", code=code, got=data['severity'])
                # Try to map common variations
                severity_lower = data['severity'].lower()
                if severity_lower in ['medium', 'moderate']:
                    data['severity'] = 'Moderate'
                elif severity_lower in ['high', 'severe']:
                    data['severity'] = 'High'
                elif severity_lower in ['low', 'minor']:
                    data['severity'] = 'Low'
                elif severity_lower in ['critical', 'severe', 'urgent']:
                    data['severity'] = 'Critical'
                else:
                    data['severity'] = 'Moderate'  # Default fallback

            # Ensure code matches (uppercase)
            data['code'] = code.upper()

            # Add metadata
            data['source'] = 'ai_generated'
            data['auto_added'] = True

            return data

        except json.JSONDecodeError as e:
            logger.error("ai_response_invalid_json", code=code, error=str(e), response=response[:200])
            return None
        except Exception as e:
            logger.error("ai_response_parse_error", code=code, error=str(e))
            return None
