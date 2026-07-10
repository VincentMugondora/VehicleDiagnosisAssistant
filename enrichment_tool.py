"""
Incremental DTC Enrichment Tool

Features:
- Batch processing (25, 50, 100 codes)
- Resume after interruption
- Skip already reviewed records
- Review workflow: RAW_DATABASE -> AI_ENRICHED -> REVIEWED -> PUBLISHED
- Improved AI prompt with OEM-style guidance
- Generate review reports after each batch
"""

import asyncio
import json
from datetime import datetime
from supabase import create_client
from app.core.config import settings
from app.services.ai_client import AIClient
from severity_rules import classify_severity, get_severity_explanation
from priority_codes import get_priority_tier, TIER_1_PRIORITY, TIER_2_PRIORITY, TIER_3_PRIORITY


# Enrichment workflow states
class EnrichmentStatus:
    RAW_DATABASE = "raw_database"        # Basic info only (description, system)
    AI_ENRICHED = "ai_enriched"          # AI-generated content, needs review
    REVIEWED = "reviewed"                # Human-reviewed, approved
    PUBLISHED = "published"              # Published to production
    NEEDS_REVISION = "needs_revision"    # Reviewed but needs changes


# Improved AI enrichment prompt
ENRICHMENT_PROMPT_TEMPLATE = """You are an automotive diagnostic expert creating structured diagnostic information for OBD-II fault codes.

Generate comprehensive diagnostic information following OEM diagnostic practices.

**Code:** {code}

**Official Definition:** {description}

**Vehicle System:** {system}

**Guidelines:**
- Use OEM-style diagnostic language (professional, technical, precise)
- Prioritize testing and verification over part replacement
- Do NOT exaggerate severity or create urgency for non-critical issues
- Base recommendations on proven diagnostic procedures
- Include electrical testing before condemning sensors
- Mention TSBs or known issues if applicable

**Required Output (JSON format only):**

```json
{{
  "symptoms": [
    "List 5-8 specific observable symptoms",
    "Focus on what driver/technician would notice",
    "Be specific (e.g., 'rough idle below 1000 RPM' not just 'rough idle')",
    "Include 'Check Engine Light illuminated' as first symptom"
  ],
  "common_causes": [
    "List 5-8 most common root causes",
    "Order by frequency (most common first)",
    "Be specific about components/conditions",
    "Include both mechanical and electrical causes",
    "Example: 'Faulty MAF sensor element (contaminated or failed)' not just 'Bad MAF'"
  ],
  "diagnostic_steps": [
    "List 6-10 systematic diagnostic steps",
    "Follow OEM diagnostic flow: scan -> inspect -> test -> verify",
    "Start with free/easy checks (visual inspection, wiring)",
    "Include specific tests with expected values",
    "Use multimeter/scope readings where applicable",
    "Example: 'Check MAF sensor voltage at idle (should be 0.6-1.0V)' not just 'Test MAF'"
  ],
  "technician_tip": "Single practical tip from experience. Focus on: (1) common mistake to avoid, (2) diagnostic shortcut, (3) known pattern for this code, or (4) money-saving advice. Example: 'Before replacing the MAF sensor, try cleaning it with MAF cleaner - contamination causes 70% of MAF faults.'",
  "pre_replacement_checks": [
    "List 3-5 verification steps before replacing parts",
    "Include electrical tests (continuity, voltage, resistance)",
    "Check for TSBs or software updates",
    "Verify problem with known-good component if possible",
    "Example: 'Verify 5V reference voltage at sensor connector'"
  ]
}}
```

**Important:**
- Return ONLY valid JSON (no markdown, no explanations)
- Do NOT include severity in output (handled separately)
- Focus on accuracy over quantity
- Use professional diagnostic terminology
- Be specific and actionable
"""


class EnrichmentTool:
    """Tool for incremental DTC enrichment with review workflow"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.client = create_client(settings.supabase_url, settings.supabase_service_key)

    async def enrich_code(self, code: str, description: str, system: str) -> dict | None:
        """
        Enrich a single code using AI.

        Args:
            code: OBD-II code
            description: Code description
            system: Vehicle system

        Returns:
            Enriched data dict or None if failed
        """
        prompt = ENRICHMENT_PROMPT_TEMPLATE.format(
            code=code,
            description=description,
            system=system
        )

        try:
            response = await self.ai_client.generate(prompt)

            # Parse JSON response
            # Try to extract JSON if wrapped in markdown
            content = response.strip()
            if content.startswith("```"):
                # Extract content between ```json and ```
                lines = content.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```json"):
                        in_json = True
                        continue
                    elif line.strip().startswith("```"):
                        break
                    elif in_json:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            enriched = json.loads(content)

            # Validate required fields
            required = ["symptoms", "common_causes", "diagnostic_steps", "technician_tip", "pre_replacement_checks"]
            for field in required:
                if field not in enriched:
                    raise ValueError(f"Missing required field: {field}")

            return enriched

        except Exception as e:
            print(f"ERROR enriching {code}: {e}")
            return None

    def get_codes_to_enrich(
        self,
        batch_size: int,
        tier: int = 1,
        skip_statuses: list[str] = None
    ) -> list[dict]:
        """
        Get next batch of codes to enrich.

        Args:
            batch_size: Number of codes to retrieve
            tier: Priority tier (1, 2, 3, or 0 for all)
            skip_statuses: List of enrichment statuses to skip

        Returns:
            List of code records
        """
        if skip_statuses is None:
            skip_statuses = [
                EnrichmentStatus.AI_ENRICHED,
                EnrichmentStatus.REVIEWED,
                EnrichmentStatus.PUBLISHED
            ]

        # Get priority codes for tier
        if tier == 1:
            priority_codes = TIER_1_PRIORITY
        elif tier == 2:
            priority_codes = TIER_2_PRIORITY
        elif tier == 3:
            priority_codes = TIER_3_PRIORITY
        else:
            priority_codes = TIER_1_PRIORITY + TIER_2_PRIORITY + TIER_3_PRIORITY

        # Fetch from database
        query = self.client.table("obd_codes").select("*")

        # Filter by priority codes
        query = query.in_("code", priority_codes[:batch_size * 2])  # Fetch extra in case some are already enriched

        # Exclude already enriched codes
        if skip_statuses:
            query = query.not_.in_("enrichment_status", skip_statuses)

        result = query.limit(batch_size).execute()

        return result.data

    async def enrich_batch(
        self,
        batch_size: int = 25,
        tier: int = 1,
        resume: bool = True
    ) -> dict:
        """
        Enrich a batch of codes.

        Args:
            batch_size: Number of codes to enrich
            tier: Priority tier
            resume: Skip already enriched codes

        Returns:
            Statistics dict
        """
        print("=" * 80)
        print(f"ENRICHMENT BATCH - Tier {tier}, Size {batch_size}")
        print("=" * 80)
        print()

        # Get codes to enrich
        skip_statuses = [
            EnrichmentStatus.AI_ENRICHED,
            EnrichmentStatus.REVIEWED,
            EnrichmentStatus.PUBLISHED
        ] if resume else []

        codes = self.get_codes_to_enrich(batch_size, tier, skip_statuses)

        if not codes:
            print("No codes found to enrich")
            return {"success": 0, "failed": 0, "skipped": 0}

        print(f"Found {len(codes)} codes to enrich")
        print()

        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "codes_enriched": [],
            "codes_failed": []
        }

        for i, code_record in enumerate(codes, 1):
            code = code_record["code"]
            description = code_record.get("description", "")
            system = code_record.get("system", "Powertrain")

            print(f"[{i}/{len(codes)}] Enriching {code}...")

            # Check if already enriched (shouldn't happen with skip_statuses, but double-check)
            current_status = code_record.get("enrichment_status")
            if current_status in skip_statuses:
                print(f"  SKIPPED (already {current_status})")
                stats["skipped"] += 1
                continue

            # Enrich with AI
            enriched = await self.enrich_code(code, description, system)

            if not enriched:
                print(f"  FAILED")
                stats["failed"] += 1
                stats["codes_failed"].append(code)
                continue

            # Apply deterministic severity
            severity, severity_reasoning = classify_severity(code, description, system)
            severity_explanation = get_severity_explanation(severity, severity_reasoning)

            # Prepare database update
            update_data = {
                "symptoms": ", ".join(enriched["symptoms"]),
                "common_causes": ", ".join(enriched["common_causes"]),
                "generic_fixes": ", ".join(enriched["diagnostic_steps"]),
                "technician_tip": enriched["technician_tip"],
                "pre_replacement_checks": ", ".join(enriched["pre_replacement_checks"]),
                "severity": severity,
                "severity_explanation": severity_explanation,
                "enrichment_status": EnrichmentStatus.AI_ENRICHED,
                "last_enriched": datetime.utcnow().isoformat()
            }

            # Save to database
            try:
                self.client.table("obd_codes").update(update_data).eq("code", code).execute()
                print(f"  SUCCESS - Severity: {severity}")
                stats["success"] += 1
                stats["codes_enriched"].append(code)
            except Exception as e:
                print(f"  FAILED to save: {e}")
                stats["failed"] += 1
                stats["codes_failed"].append(code)

            # Rate limiting (avoid overwhelming API)
            await asyncio.sleep(1)

        print()
        print("=" * 80)
        print("BATCH COMPLETE")
        print("=" * 80)
        print(f"Success: {stats['success']}")
        print(f"Failed:  {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        print()

        return stats

    def generate_review_report(self, codes: list[str], output_file: str = None):
        """
        Generate review report for enriched codes.

        Args:
            codes: List of codes to review
            output_file: Output filename (default: enrichment_review_TIMESTAMP.md)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"enrichment_review_{timestamp}.md"

        # Fetch enriched codes
        result = self.client.table("obd_codes").select("*").in_("code", codes).execute()

        if not result.data:
            print("No codes found for review")
            return

        # Generate markdown report
        report_lines = [
            "# Enrichment Review Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Codes to Review:** {len(result.data)}",
            "\n---\n"
        ]

        for code_data in result.data:
            code = code_data["code"]
            report_lines.extend([
                f"\n## {code} - {code_data.get('description', 'N/A')}",
                f"\n**System:** {code_data.get('system', 'N/A')}",
                f"**Severity:** {code_data.get('severity', 'N/A')}",
                f"**Status:** {code_data.get('enrichment_status', 'N/A')}",
                "\n### Symptoms",
                code_data.get('symptoms', 'N/A'),
                "\n### Common Causes",
                code_data.get('common_causes', 'N/A'),
                "\n### Diagnostic Steps",
                code_data.get('generic_fixes', 'N/A'),
                "\n### Technician Tip",
                code_data.get('technician_tip', 'N/A'),
                "\n### Pre-Replacement Checks",
                code_data.get('pre_replacement_checks', 'N/A'),
                "\n### Severity Explanation",
                code_data.get('severity_explanation', 'N/A'),
                "\n### Review Notes",
                "[ ] Symptoms accurate and specific",
                "[ ] Causes complete and ordered correctly",
                "[ ] Diagnostic steps follow OEM procedures",
                "[ ] Technician tip is practical and valuable",
                "[ ] Pre-replacement checks are thorough",
                "[ ] Severity rating is appropriate",
                "\n**Review Decision:**",
                "- [ ] APPROVED (mark as REVIEWED)",
                "- [ ] NEEDS_REVISION (specify changes needed)",
                "\n---\n"
            ])

        report = "\n".join(report_lines)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Review report generated: {output_file}")

        return output_file


async def main():
    """Main entry point for enrichment tool"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python enrichment_tool.py <batch_size> [tier] [--no-resume]")
        print()
        print("Examples:")
        print("  python enrichment_tool.py 25           # Enrich 25 Tier 1 codes (resume)")
        print("  python enrichment_tool.py 50 2         # Enrich 50 Tier 2 codes")
        print("  python enrichment_tool.py 100 1 --no-resume  # Re-enrich Tier 1 codes")
        return

    batch_size = int(sys.argv[1])
    tier = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    resume = "--no-resume" not in sys.argv

    # Initialize AI client
    ai_client = AIClient()

    # Create enrichment tool
    tool = EnrichmentTool(ai_client)

    # Run enrichment
    stats = await tool.enrich_batch(batch_size, tier, resume)

    # Generate review report
    if stats["codes_enriched"]:
        print("Generating review report...")
        report_file = tool.generate_review_report(stats["codes_enriched"])
        print(f"\nReview enriched codes in: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
