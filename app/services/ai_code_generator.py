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

Generate complete, accurate information for OBD code **{code}**.

**Task:**
Provide detailed diagnostic information in JSON format. Use your knowledge of automotive systems and OBD-II standards.

**Return ONLY a valid JSON object with this structure:**

{{
  "code": "{code}",
  "description": "Clear, technical description (30-70 chars)",
  "symptoms": "What the driver experiences (comma-separated, 3-5 items)",
  "common_causes": "Most likely causes (comma-separated, 3-5 items, ordered by likelihood)",
  "generic_fixes": "Diagnostic steps to identify the problem (comma-separated, 3-5 steps)",
  "system": "{expected_system}",
  "severity": "High|Medium|Low"
}}

**Guidelines:**
1. **Description**: Precise technical meaning of the code
2. **Symptoms**: What the DRIVER sees/feels (check engine light, rough idle, etc.)
3. **Causes**: List from most to least common, be specific
4. **Fixes**: Diagnostic steps, not just "replace X" - include testing and inspection
5. **Severity**:
   - **High**: Safety risk, engine damage potential, flashing check engine light, no-start
   - **Medium**: Performance/emissions issue, steady check engine light
   - **Low**: Minor issue, can wait until next service
6. Use professional but accessible language
7. Be specific - avoid generic phrases like "component failure"
8. Focus on practical, actionable information

**Important:**
- DO NOT include markdown, code blocks, or explanations
- Return ONLY the JSON object
- If this is a rare or manufacturer-specific code, provide the best general information available
- Use standard automotive terminology

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
                'common_causes', 'generic_fixes', 'system', 'severity'
            ]

            for field in required_fields:
                if field not in data or not data[field]:
                    logger.warning(
                        "ai_response_missing_field",
                        code=code,
                        field=field
                    )
                    return None

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
            if data['severity'] not in ['High', 'Medium', 'Low']:
                logger.warning("ai_response_invalid_severity", code=code)
                data['severity'] = 'Medium'  # Default fallback

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
