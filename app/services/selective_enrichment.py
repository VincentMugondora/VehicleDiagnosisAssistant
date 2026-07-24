"""
Selective AI Enrichment Service

Generates ONLY missing fields for a diagnostic code.
Reduces hallucination and token usage by providing existing context.
"""

from typing import Dict, Any, Optional, List
from datetime import UTC, datetime
from app.services.ai_client import AIClient
from app.core.logging import logger
from app.models.enrichment import FieldMetadata, DataSource
import json


CURRENT_PROMPT_VERSION = "v6"
CURRENT_AI_MODEL = "claude-sonnet-4"  # Updated when model changes


class SelectiveEnrichment:
    """
    Generates only the missing fields for a diagnostic code.

    Benefits:
    - Reduces hallucination (AI has context)
    - Lower token usage (smaller prompts)
    - Preserves existing data
    - Explicit about what needs generation
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def enrich_missing_fields(
        self,
        code: str,
        existing_data: Dict[str, Any],
        missing_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Generate only the specified missing fields.

        Args:
            code: OBD code (e.g., "P0420")
            existing_data: Current database entry
            missing_fields: List of fields to generate (e.g., ["symptoms", "technician_tip"])

        Returns:
            Dict with only the generated fields + metadata
        """
        if not missing_fields:
            logger.warning("enrich_called_with_no_missing_fields", code=code)
            return {}

        logger.info(
            "selective_enrichment_started",
            code=code,
            missing_fields=missing_fields
        )

        # Build selective prompt
        prompt = self._build_selective_prompt(code, existing_data, missing_fields)

        try:
            # Call AI
            response = await self.ai_client.complete(
                prompt=prompt,
                temperature=0.2  # Lower temperature for factual generation
            )

            # Parse response
            generated = self._parse_ai_response(response, code, missing_fields)

            if not generated:
                logger.warning("selective_enrichment_failed_parse", code=code)
                return {}

            # Add metadata to each generated field
            now = datetime.now(UTC)
            result = {}

            for field in missing_fields:
                if field in generated and generated[field]:
                    result[field] = generated[field]
                    # Store metadata with proper field mapping
                    result[f"{field}_meta"] = FieldMetadata(
                        source=DataSource.AI_GENERATED,
                        generated_at=now,
                        ai_model=CURRENT_AI_MODEL,
                        prompt_version=CURRENT_PROMPT_VERSION
                    ).model_dump(mode='json')

            logger.info(
                "selective_enrichment_success",
                code=code,
                generated_fields=list(result.keys()),
                metadata_fields=[k for k in result.keys() if k.endswith("_meta")]
            )

            return result

        except Exception as e:
            logger.error("selective_enrichment_error", code=code, error=str(e))
            return {}

    def _build_selective_prompt(
        self,
        code: str,
        existing_data: Dict[str, Any],
        missing_fields: List[str]
    ) -> str:
        """
        Build prompt that provides context and requests only missing fields.

        This reduces hallucination because the AI sees what we already know.
        """
        # Determine system from code prefix
        prefix = code[0].upper()
        system_map = {
            'P': 'Powertrain',
            'C': 'Chassis',
            'B': 'Body',
            'U': 'Network'
        }
        expected_system = system_map.get(prefix, 'Powertrain')

        # Build context section
        context_parts = []
        if existing_data.get("description"):
            context_parts.append(f"**Description:** {existing_data['description']}")
        if existing_data.get("system"):
            context_parts.append(f"**System:** {existing_data['system']}")
        if existing_data.get("common_causes"):
            causes = existing_data['common_causes']
            if isinstance(causes, list):
                context_parts.append(f"**Known Causes:** {', '.join(causes)}")
            else:
                context_parts.append(f"**Known Causes:** {causes}")
        if existing_data.get("generic_fixes"):
            fixes = existing_data['generic_fixes']
            if isinstance(fixes, list):
                context_parts.append(f"**Known Fixes:** {', '.join(fixes)}")
            else:
                context_parts.append(f"**Known Fixes:** {fixes}")

        context_section = "\n".join(context_parts) if context_parts else "No existing context available."

        # Build fields to generate
        field_mapping = {
            "symptoms": {
                "format": "JSON array of strings",
                "guidelines": "4-8 symptoms the driver experiences. Always include 'Check Engine Light illuminated' first. Be specific."
            },
            "severity": {
                "format": "One of: Critical | High | Moderate | Low",
                "guidelines": "Critical=safety systems, High=engine damage risk, Moderate=performance issues, Low=minor issues"
            },
            "severity_explanation": {
                "format": "String (1-2 sentences)",
                "guidelines": "Explain why this severity level, mention driveability and risk"
            },
            "technician_tip": {
                "format": "String (1-2 sentences)",
                "guidelines": "Practical advice to avoid unnecessary part replacement. Focus on common mistakes."
            },
            "pre_replacement_checks": {
                "format": "JSON array of strings",
                "guidelines": "3-5 items. What to verify BEFORE buying parts. Start with wiring/connectors."
            },
            "common_causes": {
                "format": "JSON array of strings",
                "guidelines": "4-6 causes ordered by likelihood. Be specific, not generic."
            },
            "generic_fixes": {
                "format": "JSON array of strings",
                "guidelines": "5-8 diagnostic steps (not just 'replace X'). Start with inspection/testing."
            }
        }

        fields_section = []
        for field in missing_fields:
            if field in field_mapping:
                spec = field_mapping[field]
                fields_section.append(
                    f"- **{field}**: {spec['format']}\n  Guidelines: {spec['guidelines']}"
                )

        fields_to_generate = "\n".join(fields_section)

        # Build complete prompt
        return f"""You are an automotive diagnostic expert. Generate ONLY the missing fields for OBD code **{code}**.

**EXISTING CONTEXT:**

{context_section}

---

**FIELDS TO GENERATE:**

{fields_to_generate}

---

**IMPORTANT:**
- Return ONLY a valid JSON object
- Include ONLY the fields listed above
- Do NOT regenerate existing fields
- Use the existing context to inform your generation
- Be specific and actionable
- For arrays, return actual JSON arrays, not comma-separated strings

**RETURN FORMAT:**

{{
  "field_name": value,
  ...
}}

Generate the JSON now:"""

    def _parse_ai_response(
        self,
        response: str,
        code: str,
        expected_fields: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse AI response and validate structure.

        Args:
            response: AI response text
            code: OBD code (for logging)
            expected_fields: Fields we asked AI to generate

        Returns:
            Dict with generated fields or None if parse fails
        """
        try:
            # Extract JSON from response
            json_match = response.strip()

            # Remove markdown code blocks if present
            if '```' in json_match:
                parts = json_match.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        part = part[4:].strip()
                    if part.startswith('{'):
                        json_match = part
                        break

            # Parse JSON
            data = json.loads(json_match)

            # Validate that only expected fields are present
            for key in data.keys():
                if key not in expected_fields:
                    logger.warning(
                        "ai_generated_unexpected_field",
                        code=code,
                        field=key
                    )

            # Validate severity if generated
            if "severity" in data:
                if data["severity"] not in ["Critical", "High", "Moderate", "Low"]:
                    logger.warning("ai_invalid_severity", code=code, got=data["severity"])
                    # Try to map
                    severity_lower = data["severity"].lower()
                    if severity_lower in ["medium", "moderate"]:
                        data["severity"] = "Moderate"
                    elif severity_lower in ["high", "severe"]:
                        data["severity"] = "High"
                    elif severity_lower in ["low", "minor"]:
                        data["severity"] = "Low"
                    elif severity_lower in ["critical", "urgent"]:
                        data["severity"] = "Critical"
                    else:
                        data["severity"] = "Moderate"

            return data

        except json.JSONDecodeError as e:
            logger.error("ai_response_invalid_json", code=code, error=str(e), response=response[:200])
            return None
        except Exception as e:
            logger.error("ai_response_parse_error", code=code, error=str(e))
            return None
