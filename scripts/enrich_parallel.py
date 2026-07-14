#!/usr/bin/env python3
"""
Parallel AI Enrichment Script (Cohere)

Enriches ALL OBD codes with knowledge_score < 80% using concurrent Cohere AI calls.
Processes 10 codes in parallel to dramatically reduce total enrichment time.

Usage:
    # Enrich all codes (10 parallel workers)
    python scripts/enrich_parallel.py

    # Custom concurrency
    python scripts/enrich_parallel.py --workers 15

    # Limit to N codes
    python scripts/enrich_parallel.py --limit 500

    # Dry run
    python scripts/enrich_parallel.py --dry-run --limit 20
"""

import sys
import json
import time
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import cohere
from supabase import create_client, Client
from app.core.config import settings


VALID_DIFFICULTIES = ["Easy", "Moderate", "Advanced", "Professional Required"]


def build_enrichment_prompt(code: str, description: str, existing_causes: str = "", existing_symptoms: str = "") -> str:
    return f"""You are an expert automotive diagnostic technician. Generate comprehensive diagnostic information for OBD code {code}.

Code: {code}
Description: {description}
Existing Causes: {existing_causes}
Existing Symptoms: {existing_symptoms}

Generate the following fields in JSON format:

1. **symptoms**: Array of 4-6 common symptoms the driver will notice
2. **common_causes**: Array of 4-6 likely causes
3. **severity_explanation**: One paragraph explaining severity and consequences
4. **technician_tip**: Professional diagnostic tip (2-3 sentences)
5. **pre_replacement_checks**: Array of 3-5 checks to do before replacing parts
6. **typical_repair_time**: Estimated time range (e.g., "1-3 hours")
7. **typical_cost_range**: Cost range with breakdown (e.g., "$200-$800 (Parts: $100-$500, Labor: $100-$300)")
8. **diy_difficulty**: One of: "Easy", "Moderate", "Advanced", "Professional Required"
9. **related_codes**: Array of 3-5 related OBD codes
10. **common_misdiagnoses**: Paragraph warning about common diagnostic mistakes
11. **freeze_frame_data_to_check**: Array of 4-6 scanner data points to review
12. **cause_likelihoods**: Array of causes with likelihood percentages that sum to 100
    Format: [{{"cause": "description", "likelihood": 60}}, ...]
13. **emissions_impact**: One of: "Will Fail", "May Fail", "Monitor Not Ready", "No Impact"

Return ONLY valid JSON. Be specific, practical, and accurate."""


class ParallelEnrichment:
    def __init__(self, client: Client, workers: int = 10, dry_run: bool = False):
        self.client = client
        self.semaphore = asyncio.Semaphore(workers)
        self.dry_run = dry_run
        self.workers = workers

        # Stats
        self.enriched = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.start_time = time.time()
        self.lock = asyncio.Lock()

        # Cohere client (sync, called from thread pool)
        self.cohere_client = cohere.Client(api_key=settings.cohere_api_key)
        self.cohere_model = settings.cohere_model

    async def generate_with_ai(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call Cohere AI with retry logic, running sync client in thread pool."""
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.cohere_client.chat(
                        model=self.cohere_model,
                        message=prompt,
                        temperature=0.3,
                        max_tokens=2000
                    )
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                is_retryable = any(x in error_str.lower() for x in ["429", "503", "rate limit", "too many", "timeout"])

                if attempt < max_retries - 1 and is_retryable:
                    wait = 15 * (attempt + 1)  # 15s, 30s, 45s for rate limits
                    print(f"    [RATE-LIMIT] Waiting {wait}s before retry...")
                    await asyncio.sleep(wait)
                    continue
                elif attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
                else:
                    return None

    def parse_ai_response(self, response: str) -> Optional[dict]:
        """Parse JSON from AI response."""
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    return None
            return None

    def prepare_update_data(self, enriched_data: dict) -> dict:
        """Prepare data for database update."""
        # Normalize diy_difficulty
        if "diy_difficulty" in enriched_data:
            raw = enriched_data["diy_difficulty"]
            normalized = None
            for valid in VALID_DIFFICULTIES:
                if valid.lower() in raw.lower():
                    normalized = valid
                    break
            enriched_data["diy_difficulty"] = normalized or "Moderate"

        # Convert cause_likelihoods to JSON string
        if "cause_likelihoods" in enriched_data and isinstance(enriched_data["cause_likelihoods"], list):
            enriched_data["cause_likelihoods"] = json.dumps(enriched_data["cause_likelihoods"])

        # Convert list fields to proper format for DB
        for field in ["symptoms", "common_causes", "pre_replacement_checks", "related_codes", "freeze_frame_data_to_check"]:
            if field in enriched_data and isinstance(enriched_data[field], list):
                enriched_data[field] = enriched_data[field]

        # Add metadata
        enriched_data["enrichment_status"] = "ai_enriched"
        enriched_data["last_enriched"] = datetime.now().isoformat()
        enriched_data["knowledge_score"] = 75.0

        return enriched_data

    async def enrich_single_code(self, code_record: dict) -> bool:
        """Enrich a single code with semaphore-controlled concurrency and rate limiting."""
        async with self.semaphore:
            # Rate limit: wait between calls to avoid hitting trial key limits
            await asyncio.sleep(2)
            code = code_record.get("code")
            description = code_record.get("description", "")
            existing_causes = code_record.get("common_causes", "") or ""
            existing_symptoms = code_record.get("symptoms", "") or ""

            # Generate prompt
            prompt = build_enrichment_prompt(code, description, existing_causes, existing_symptoms)

            # Call AI
            response = await self.generate_with_ai(prompt)
            if not response:
                async with self.lock:
                    self.failed += 1
                    self._print_progress(code, "FAIL", "AI generation failed")
                return False

            # Parse response
            enriched_data = self.parse_ai_response(response)
            if not enriched_data:
                async with self.lock:
                    self.failed += 1
                    self._print_progress(code, "FAIL", "JSON parse failed")
                return False

            # Prepare update
            update_data = self.prepare_update_data(enriched_data)

            if self.dry_run:
                async with self.lock:
                    self.enriched += 1
                    self._print_progress(code, "DRY-RUN", "Would update")
                return True

            # Update database
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.table("obd_codes").update(update_data).eq("code", code).execute()
                )
                if result.data:
                    async with self.lock:
                        self.enriched += 1
                        self._print_progress(code, "OK", "Enriched")
                    return True
                else:
                    async with self.lock:
                        self.failed += 1
                        self._print_progress(code, "FAIL", "DB update empty")
                    return False
            except Exception as e:
                async with self.lock:
                    self.failed += 1
                    self._print_progress(code, "FAIL", f"DB error: {str(e)[:50]}")
                return False

    def _print_progress(self, code: str, status: str, message: str):
        """Print progress update."""
        done = self.enriched + self.failed + self.skipped
        elapsed = time.time() - self.start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (self.total - done) / rate if rate > 0 else 0

        print(f"  [{done}/{self.total}] {code}: [{status}] {message} "
              f"(rate: {rate:.1f}/s, ETA: {eta/60:.0f}min)")

    async def run(self, limit: Optional[int] = None, offset: int = 0):
        """Fetch all unenriched codes and process them in parallel batches."""
        print("\n" + "=" * 70)
        print("PARALLEL AI ENRICHMENT")
        print("=" * 70)
        print(f"Workers: {self.workers}")
        print(f"Dry-run: {self.dry_run}")
        print(f"Offset: {offset}")
        print()

        # Fetch codes needing enrichment
        print("[*] Fetching codes needing enrichment...")
        query = self.client.table("obd_codes").select(
            "code, description, symptoms, common_causes, knowledge_score"
        ).lt("knowledge_score", 80.0).order("code")

        if offset > 0:
            query = query.range(offset, offset + (limit or 10000) - 1)
        elif limit:
            query = query.limit(limit)

        result = query.execute()
        codes = result.data

        if not codes:
            print("[OK] No codes need enrichment!")
            return

        self.total = len(codes)
        print(f"[OK] Found {self.total} codes to enrich")
        print(f"[*] Starting parallel enrichment with {self.workers} workers...")
        print()

        # Process all codes concurrently (semaphore controls parallelism)
        tasks = [self.enrich_single_code(record) for record in codes]
        await asyncio.gather(*tasks)

        # Final stats
        self._print_final_stats()

    def _print_final_stats(self):
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("ENRICHMENT COMPLETE")
        print("=" * 70)
        print(f"Total processed: {self.enriched + self.failed + self.skipped}")
        print(f"Enriched:        {self.enriched}")
        print(f"Failed:          {self.failed}")
        print(f"Skipped:         {self.skipped}")
        print(f"Duration:        {elapsed:.0f}s ({elapsed/60:.1f} min)")
        if self.enriched > 0:
            print(f"Avg per code:    {elapsed/self.enriched:.1f}s")
            print(f"Effective rate:  {self.enriched/elapsed:.2f} codes/s")
        print("=" * 70)

        remaining = self.total - self.enriched
        if remaining > 0 and self.enriched > 0:
            rate = self.enriched / elapsed
            print(f"\nEstimated time for remaining {remaining} codes: {remaining/rate/60:.0f} min")
            print(f"Re-run with: python scripts/enrich_parallel.py")


async def main():
    parser = argparse.ArgumentParser(description="Parallel AI Enrichment for all OBD codes")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers (default: 10)")
    parser.add_argument("--limit", type=int, help="Limit number of codes to process")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N codes")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    args = parser.parse_args()

    if not settings.supabase_enabled:
        print("[ERROR] Supabase not enabled in .env")
        return 1

    if not settings.cohere_api_key:
        print("[ERROR] COHERE_API_KEY not set in .env")
        return 1

    client = create_client(settings.supabase_url, settings.supabase_service_key)
    print(f"[OK] Supabase connected")
    print(f"[OK] Cohere AI ready (model: {settings.cohere_model})")

    enricher = ParallelEnrichment(
        client=client,
        workers=args.workers,
        dry_run=args.dry_run
    )

    await enricher.run(limit=args.limit, offset=args.offset)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
