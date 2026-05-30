"""
Code Enhancer Service
Uses LLM to parse, enhance, and structure scraped OBD code data.
"""

from typing import Dict, Any, Optional
from app.services.ai_client import AIClient
from app.core.logging import logger
import json


class CodeEnhancer:
    """Uses AI to enhance and structure scraped OBD code data"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def enhance_code_data(
        self,
        raw_data: Dict[str, Any],
        code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to parse and enhance scraped code data.

        Args:
            raw_data: Raw scraped data from web
            code: OBD code (e.g., "P3499")

        Returns:
            Enhanced, structured code data ready for database
        """

        logger.info("llm_enhance_started", code=code)

        # Build prompt for LLM
        prompt = self._build_enhancement_prompt(raw_data, code)

        try:
            # Call AI to structure the data
            response = await self.ai_client.complete(
                prompt=prompt,
                temperature=0.3  # Lower temperature for factual extraction
            )

            # Parse JSON response
            enhanced_data = self._parse_llm_response(response, code)

            if enhanced_data:
                logger.info("llm_enhance_success", code=code)
                return enhanced_data
            else:
                logger.warning("llm_enhance_failed_parse", code=code)
                return None

        except Exception as e:
            logger.error("llm_enhance_error", code=code, error=str(e))
            return None

    def _build_enhancement_prompt(
        self,
        raw_data: Dict[str, Any],
        code: str
    ) -> str:
        """Build prompt for LLM to structure the code data"""

        return f"""You are an automotive diagnostic expert. I have scraped OBD code information from a website.
Please parse and structure this data into a clean, standardized format.

**OBD Code:** {code}

**Raw Scraped Data:**
- Description: {raw_data.get('description', 'N/A')}
- Symptoms: {raw_data.get('symptoms', 'N/A')}
- Common Causes: {raw_data.get('common_causes', 'N/A')}
- Generic Fixes: {raw_data.get('generic_fixes', 'N/A')}
- Source: {raw_data.get('source', 'N/A')}

**Task:**
Clean, structure, and enhance this data. Return ONLY a valid JSON object with this exact structure:

{{
  "code": "{code}",
  "description": "Clear, concise description (30-60 chars)",
  "symptoms": "User-facing symptoms they would notice (comma-separated)",
  "common_causes": "Most likely causes (comma-separated, 3-5 items)",
  "generic_fixes": "Step-by-step diagnostic steps (comma-separated)",
  "system": "Powertrain|Chassis|Body|Network",
  "severity": "High|Medium|Low"
}}

**Guidelines:**
1. Description should be clear and specific to this code
2. Symptoms should describe what the DRIVER experiences
3. Causes should be listed from most to least common
4. Fixes should be diagnostic steps, not just "replace X"
5. System: Determine from code prefix (P=Powertrain, C=Chassis, B=Body, U=Network)
6. Severity:
   - High = Safety issue, engine damage risk, no-start, flashing check engine light
   - Medium = Performance/emissions issue, steady check engine light
   - Low = Minor issue, can wait until next service
7. Use professional but user-friendly language
8. DO NOT include markdown, explanations, or anything outside the JSON object

Return ONLY the JSON object, nothing else."""

    def _parse_llm_response(
        self,
        response: str,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM response and validate structure"""

        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_match = response.strip()

            # Remove markdown code blocks if present
            if json_match.startswith('```'):
                json_match = json_match.split('```')[1]
                if json_match.startswith('json'):
                    json_match = json_match[4:]
                json_match = json_match.strip()

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
                        "llm_response_missing_field",
                        code=code,
                        field=field
                    )
                    return None

            # Validate system
            if data['system'] not in ['Powertrain', 'Chassis', 'Body', 'Network']:
                logger.warning("llm_response_invalid_system", code=code)
                return None

            # Validate severity
            if data['severity'] not in ['High', 'Medium', 'Low']:
                logger.warning("llm_response_invalid_severity", code=code)
                return None

            # Ensure code matches
            if data['code'].upper() != code.upper():
                data['code'] = code.upper()

            return data

        except json.JSONDecodeError as e:
            logger.error("llm_response_invalid_json", code=code, error=str(e))
            return None
        except Exception as e:
            logger.error("llm_response_parse_error", code=code, error=str(e))
            return None

    def validate_and_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Final validation and cleaning before saving to database"""

        # Ensure all text fields are trimmed
        for field in ['description', 'symptoms', 'common_causes', 'generic_fixes']:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()

        # Ensure description isn't too long
        if len(data.get('description', '')) > 200:
            data['description'] = data['description'][:197] + '...'

        # Add metadata
        data['source'] = 'web_enhanced'
        data['auto_added'] = True

        return data
