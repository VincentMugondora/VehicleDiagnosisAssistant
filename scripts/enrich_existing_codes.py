#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Enrichment Backfill Script (Migration 003)

This script enriches existing OBD codes with Migration 003 fields using AI.

Features:
- Finds codes with low knowledge_score (< 80%)
- Generates missing fields using AI
- Updates database with enriched data
- Tracks provenance in metadata
- Batch processing with progress tracking
- Dry-run mode for testing

Usage:
    # Enrich 10 codes (dry-run)
    python scripts/enrich_existing_codes.py --limit 10 --dry-run

    # Enrich 50 codes (live)
    python scripts/enrich_existing_codes.py --batch-size 50

    # Enrich all codes with score < 80%
    python scripts/enrich_existing_codes.py --all

    # Enrich specific code
    python scripts/enrich_existing_codes.py --code P0420
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger
from app.services.ai_client import AIClient
from app.services.cohere_client import CohereClient


class EnrichmentBackfill:
    """AI-powered enrichment backfill for OBD codes"""

    def __init__(self, client: Client, ai_client: AIClient, dry_run: bool = False):
        self.client = client
        self.ai_client = ai_client
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            "total_found": 0,
            "enriched": 0,
            "skipped": 0,
            "failed": 0,
            "start_time": time.time()
        }

    def find_codes_needing_enrichment(self, limit: Optional[int] = None) -> list[dict]:
        """
        Find codes with knowledge_score < 80% (needing enrichment)

        Args:
            limit: Maximum number of codes to return

        Returns:
            List of code records needing enrichment
        """
        print("\n[*] Finding codes needing enrichment...")

        try:
            query = self.client.table("obd_codes").select(
                "code, description, system, symptoms, common_causes, generic_fixes, "
                "severity, severity_explanation, technician_tip, pre_replacement_checks, "
                "knowledge_score, enrichment_status"
            ).lt("knowledge_score", 80.0).order("knowledge_score", desc=False)

            if limit:
                query = query.limit(limit)

            result = query.execute()

            codes = result.data
            self.stats["total_found"] = len(codes)

            print(f"[OK] Found {len(codes)} codes needing enrichment")

            if codes:
                print("\nTop 5 codes with lowest scores:")
                for code_record in codes[:5]:
                    code = code_record.get('code')
                    score = code_record.get('knowledge_score', 0)
                    desc = code_record.get('description', 'N/A')[:50]
                    print(f"  - {code}: {score:.1f}% - {desc}...")

            return codes

        except Exception as e:
            print(f"[ERROR] Failed to fetch codes: {e}")
            return []

    def get_specific_code(self, code: str) -> Optional[dict]:
        """Get specific code for enrichment"""
        try:
            result = self.client.table("obd_codes").select("*").eq("code", code.upper()).execute()

            if result.data:
                return result.data[0]
            else:
                print(f"[ERROR] Code {code} not found in database")
                return None

        except Exception as e:
            print(f"[ERROR] Failed to fetch code {code}: {e}")
            return None

    async def generate_enrichment_fields(self, code_record: dict) -> Optional[dict]:
        """
        Generate enrichment fields using AI

        Args:
            code_record: Existing code record from database

        Returns:
            Dict with enriched fields or None if generation fails
        """
        code = code_record.get('code')
        description = code_record.get('description', '')
        existing_causes = code_record.get('common_causes', '')
        existing_symptoms = code_record.get('symptoms', '')

        # Build comprehensive prompt for AI
        prompt = f"""You are an expert automotive diagnostic technician. Generate comprehensive diagnostic information for OBD code {code}.

Code: {code}
Description: {description}
Existing Causes: {existing_causes}
Existing Symptoms: {existing_symptoms}

Generate the following fields in JSON format:

1. **typical_repair_time**: Estimated time range (e.g., "1-3 hours", "30 minutes", "Full day")
2. **typical_cost_range**: Cost range with breakdown (e.g., "$200-$800 (Sensor: $200-$300, Labor: $100-$200)")
3. **diy_difficulty**: One of: "Easy", "Moderate", "Advanced", "Professional Required"
4. **related_codes**: Array of 3-5 related OBD codes to check (e.g., ["P0430", "P0171", "P0174"])
5. **common_misdiagnoses**: Paragraph warning about common diagnostic mistakes (what NOT to do)
6. **freeze_frame_data_to_check**: Array of 4-6 scanner data points to review with expected values
7. **cause_likelihoods**: Array of causes with likelihood percentages that sum to 100
   Format: [{{"cause": "Worn catalytic converter", "likelihood": 60}}, ...]
8. **emissions_impact**: One of: "Will Fail", "May Fail", "Monitor Not Ready", "No Impact"

Return ONLY valid JSON in this exact format:
{{
    "typical_repair_time": "1-3 hours",
    "typical_cost_range": "$200-$2,500",
    "diy_difficulty": "Moderate",
    "related_codes": ["P0430", "P0300", "P0171"],
    "common_misdiagnoses": "Do not immediately replace...",
    "freeze_frame_data_to_check": [
        "Short Term Fuel Trim: -10% to +10%",
        "Long Term Fuel Trim: -10% to +10%"
    ],
    "cause_likelihoods": [
        {{"cause": "Worn catalytic converter", "likelihood": 60}},
        {{"cause": "Faulty O2 sensor", "likelihood": 25}},
        {{"cause": "Engine running rich/lean", "likelihood": 10}},
        {{"cause": "Exhaust leak", "likelihood": 5}}
    ],
    "emissions_impact": "Will Fail"
}}

Be specific, practical, and accurate. Focus on real-world diagnostic scenarios."""

        try:
            response = await self.ai_client.generate(prompt, max_tokens=2000)

            # Try to extract JSON from response
            response_text = response.strip()

            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            enriched_data = json.loads(response_text)

            # Validate required fields
            required_fields = [
                "typical_repair_time", "typical_cost_range", "diy_difficulty",
                "related_codes", "common_misdiagnoses", "freeze_frame_data_to_check",
                "cause_likelihoods", "emissions_impact"
            ]

            missing = [f for f in required_fields if f not in enriched_data]
            if missing:
                print(f"[WARN] AI response missing fields: {missing}")

            return enriched_data

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse AI response as JSON: {e}")
            print(f"Response: {response[:200]}...")
            return None
        except Exception as e:
            print(f"[ERROR] AI generation failed: {e}")
            return None

    def update_code_in_database(self, code: str, enriched_data: dict) -> bool:
        """
        Update code in database with enriched fields

        Args:
            code: OBD code to update
            enriched_data: Dict with enriched fields

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert cause_likelihoods to JSON string for JSONB column
            if "cause_likelihoods" in enriched_data and isinstance(enriched_data["cause_likelihoods"], list):
                enriched_data["cause_likelihoods"] = json.dumps(enriched_data["cause_likelihoods"])

            # Add enrichment metadata
            enriched_data["enrichment_status"] = "ai_enriched"
            enriched_data["last_enriched"] = datetime.now().isoformat()

            # Create metadata for provenance tracking
            metadata = {
                "source": "ai_generated",
                "generated_at": datetime.now().isoformat(),
                "ai_model": settings.cohere_model if settings.ai_provider == "cohere" else settings.gemini_model,
                "prompt_version": "v1_migration_003",
                "script": "enrich_existing_codes.py"
            }

            # Add metadata only to fields that have metadata columns
            # Based on migration 003: symptoms_meta, common_causes_meta, diagnostic_steps_meta,
            # severity_explanation_meta, technician_tip_meta, pre_replacement_checks_meta
            # Note: typical_repair_time, typical_cost_range, related_codes, etc. don't have meta columns
            metadata_fields = {
                # No metadata columns for Migration 003 basic fields
                # They're tracked at the enrichment_status level
            }

            # Metadata is tracked at record level via enrichment_status and last_enriched

            if self.dry_run:
                print(f"[DRY-RUN] Would update code {code} with:")
                print(f"  - typical_repair_time: {enriched_data.get('typical_repair_time')}")
                print(f"  - typical_cost_range: {enriched_data.get('typical_cost_range')}")
                print(f"  - diy_difficulty: {enriched_data.get('diy_difficulty')}")
                print(f"  - related_codes: {enriched_data.get('related_codes')}")
                return True

            # Update database
            result = self.client.table("obd_codes").update(enriched_data).eq("code", code).execute()

            if result.data:
                return True
            else:
                print(f"[ERROR] Update returned no data for {code}")
                return False

        except Exception as e:
            print(f"[ERROR] Database update failed for {code}: {e}")
            return False

    async def enrich_code(self, code_record: dict) -> bool:
        """
        Enrich a single code

        Args:
            code_record: Code record from database

        Returns:
            True if successful, False otherwise
        """
        code = code_record.get('code')
        score = code_record.get('knowledge_score', 0)

        print(f"\n{'='*70}")
        print(f"Enriching: {code} (Current score: {score:.1f}%)")
        print(f"{'='*70}")

        # Check if already well-enriched
        if score >= 80:
            print(f"[SKIP] Code {code} already well-enriched (score: {score:.1f}%)")
            self.stats["skipped"] += 1
            return False

        # Generate enrichment fields
        print("[*] Generating enrichment fields with AI...")
        start_time = time.time()

        enriched_data = await self.generate_enrichment_fields(code_record)

        if not enriched_data:
            print(f"[FAIL] AI generation failed for {code}")
            self.stats["failed"] += 1
            return False

        duration = time.time() - start_time
        print(f"[OK] Generated in {duration:.1f}s")

        # Update database
        print("[*] Updating database...")
        success = self.update_code_in_database(code, enriched_data)

        if success:
            print(f"[OK] Successfully enriched {code}")
            self.stats["enriched"] += 1
            return True
        else:
            print(f"[FAIL] Database update failed for {code}")
            self.stats["failed"] += 1
            return False

    async def run_backfill(self, codes: list[dict], batch_size: int = 10):
        """
        Run backfill process for multiple codes

        Args:
            codes: List of code records to enrich
            batch_size: Pause after this many codes (rate limiting)
        """
        total = len(codes)

        print(f"\n{'='*70}")
        print(f"Starting Enrichment Backfill")
        print(f"{'='*70}")
        print(f"Total codes: {total}")
        print(f"Batch size: {batch_size}")
        print(f"Dry-run: {self.dry_run}")
        print(f"{'='*70}\n")

        for i, code_record in enumerate(codes, 1):
            print(f"\n[{i}/{total}] Processing {code_record.get('code')}...")

            await self.enrich_code(code_record)

            # Rate limiting: pause every batch_size codes
            if i % batch_size == 0 and i < total:
                print(f"\n[*] Completed batch ({i}/{total}). Pausing 2 seconds...")
                time.sleep(2)

        # Print final statistics
        self.print_statistics()

    def print_statistics(self):
        """Print enrichment statistics"""
        duration = time.time() - self.stats["start_time"]

        print(f"\n{'='*70}")
        print("ENRICHMENT STATISTICS")
        print(f"{'='*70}")
        print(f"Total found:     {self.stats['total_found']}")
        print(f"Enriched:        {self.stats['enriched']}")
        print(f"Skipped:         {self.stats['skipped']}")
        print(f"Failed:          {self.stats['failed']}")
        print(f"Duration:        {duration:.1f}s")

        if self.stats["enriched"] > 0:
            avg_time = duration / self.stats["enriched"]
            print(f"Avg per code:    {avg_time:.1f}s")

        print(f"{'='*70}")

        if not self.dry_run and self.stats["enriched"] > 0:
            print("\n[*] Enrichment complete! Run verification:")
            print("    python scripts/run_migration_via_supabase_api.py --verify-only")


async def main():
    parser = argparse.ArgumentParser(description="AI Enrichment Backfill (Migration 003)")
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of codes to enrich"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size (pause after N codes for rate limiting)"
    )
    parser.add_argument(
        "--code",
        type=str,
        help="Enrich specific code (e.g., P0420)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enrich all codes with score < 80%"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (no database updates)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum knowledge_score to enrich (default: 0.0)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("AI ENRICHMENT BACKFILL (Migration 003)")
    print("="*70)

    # Initialize clients
    print("\n[*] Initializing clients...")

    if not settings.supabase_enabled:
        print("[ERROR] Supabase not enabled in .env")
        return 1

    supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    print("[OK] Supabase connected")

    # Initialize AI client based on provider
    if settings.ai_provider == "cohere":
        ai_client = CohereClient()
        print(f"[OK] Cohere AI initialized (model: {settings.cohere_model})")
    else:
        print("[ERROR] Unsupported AI provider. Use 'cohere' in .env")
        return 1

    # Initialize backfill service
    backfill = EnrichmentBackfill(
        client=supabase_client,
        ai_client=ai_client,
        dry_run=args.dry_run
    )

    # Find codes to enrich
    if args.code:
        # Enrich specific code
        code_record = backfill.get_specific_code(args.code)
        if not code_record:
            return 1
        codes = [code_record]
    else:
        # Find codes needing enrichment
        limit = None if args.all else (args.limit or 10)
        codes = backfill.find_codes_needing_enrichment(limit=limit)

        if not codes:
            print("\n[OK] No codes need enrichment!")
            return 0

    # Confirm before proceeding
    if not args.dry_run:
        print(f"\n[!] About to enrich {len(codes)} codes with AI.")
        print("[!] This will update your database.")
        confirmation = input("\nType 'YES' to proceed: ")

        if confirmation != "YES":
            print("\n[!] Cancelled by user")
            return 0

    # Run backfill
    await backfill.run_backfill(codes, batch_size=args.batch_size)

    return 0


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
