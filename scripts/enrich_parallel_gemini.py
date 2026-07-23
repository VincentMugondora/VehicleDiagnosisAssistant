#!/usr/bin/env python3
"""
Parallel AI Enrichment Script (Gemini)

Enriches OBD codes using Google Gemini AI with concurrent requests.
Targets codes with knowledge_score < 80 (or upgrades local-enriched codes with score == 70).

Usage:
    # Enrich all codes needing AI upgrade
    python scripts/enrich_parallel_gemini.py

    # Custom concurrency (Gemini free tier: use 5-10 workers)
    python scripts/enrich_parallel_gemini.py --workers 5

    # Only upgrade local-enriched codes (score == 70)
    python scripts/enrich_parallel_gemini.py --upgrade-local

    # Limit to N codes
    python scripts/enrich_parallel_gemini.py --limit 100

    # Dry run
    python scripts/enrich_parallel_gemini.py --dry-run --limit 10
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

from google import genai
from google.genai import types
from supabase import create_client, Client
from app.core.config import settings


VALID_DIFFICULTIES = ["Easy", "Moderate", "Advanced", "Professional Required"]


def build_enrichment_prompt(code: str, description: str, existing_causes: str = "", existing_symptoms: str = "") -> str:
    return f"""You are an expert automotive diagnostic technician with 20+ years of experience. Generate comprehensive, accurate diagnostic information for OBD-II code {code}.

Code: {code}
Description: {description}
{f'Known Causes: {existing_causes}' if existing_causes else ''}
{f'Known Symptoms: {existing_symptoms}' if existing_symptoms else ''}

Generate the following fields in valid JSON format. Be specific to this exact code - do NOT give generic answers:

{{
  "symptoms": ["array of 4-6 specific symptoms the driver will notice"],
  "common_causes": ["array of 4-6 likely causes, ordered by probability"],
  "severity_explanation": "One paragraph explaining why this code matters and consequences of ignoring it",
  "technician_tip": "Professional diagnostic tip from experience (2-3 sentences)",
  "pre_replacement_checks": ["array of 3-5 checks before replacing parts"],
  "typical_repair_time": "Estimated time range (e.g., '1-3 hours')",
  "typical_cost_range": "Cost with breakdown (e.g., '$200-$800 (Parts: $100-$500, Labor: $100-$300)')",
  "diy_difficulty": "One of: Easy, Moderate, Advanced, Professional Required",
  "related_codes": ["array of 3-5 related OBD codes that often appear alongside this one"],
  "common_misdiagnoses": "Paragraph about common diagnostic mistakes for this specific code",
  "freeze_frame_data_to_check": ["array of 4-6 specific scanner data points to review"],
  "cause_likelihoods": [{{"cause": "most likely cause", "likelihood": 40}}, {{"cause": "second cause", "likelihood": 25}}, {{"cause": "third cause", "likelihood": 20}}, {{"cause": "fourth cause", "likelihood": 15}}],
  "emissions_impact": "One of: Will Fail, May Fail, Monitor Not Ready, No Impact"
}}

Return ONLY valid JSON. No markdown formatting, no code blocks, just the JSON object."""


class GeminiParallelEnrichment:
    def __init__(self, client: Client, workers: int = 5, dry_run: bool = False):
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

        # Gemini setup
        self.genai_client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model

    async def generate_with_ai(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call Gemini AI with retry logic."""
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.genai_client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=2000,
                        )
                    )
                )
                if response.text:
                    return response.text
                return None
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = any(x in error_str for x in [
                    "429", "503", "rate", "quota", "resource_exhausted", "timeout", "deadline"
                ])

                if attempt < max_retries - 1 and is_retryable:
                    wait = 20 * (attempt + 1)
                    print(f"    [RATE-LIMIT] {str(e)[:60]}... Waiting {wait}s")
                    await asyncio.sleep(wait)
                    continue
                elif attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    continue
                else:
                    print(f"    [ERROR] {str(e)[:80]}")
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
        if "diy_difficulty" in enriched_data:
            raw = str(enriched_data["diy_difficulty"])
            normalized = None
            for valid in VALID_DIFFICULTIES:
                if valid.lower() in raw.lower():
                    normalized = valid
                    break
            enriched_data["diy_difficulty"] = normalized or "Moderate"

        if "cause_likelihoods" in enriched_data and isinstance(enriched_data["cause_likelihoods"], list):
            enriched_data["cause_likelihoods"] = json.dumps(enriched_data["cause_likelihoods"])

        enriched_data["enrichment_status"] = "ai_enriched"
        enriched_data["last_enriched"] = datetime.now().isoformat()
        enriched_data["knowledge_score"] = 85.0

        return enriched_data

    async def enrich_single_code(self, code_record: dict) -> bool:
        """Enrich a single code with semaphore-controlled concurrency."""
        async with self.semaphore:
            await asyncio.sleep(1.5)  # Rate limit spacing

            code = code_record.get("code")
            description = code_record.get("description", "")
            existing_causes = code_record.get("common_causes", "") or ""
            existing_symptoms = code_record.get("symptoms", "") or ""

            if isinstance(existing_causes, list):
                existing_causes = ", ".join(existing_causes)
            if isinstance(existing_symptoms, list):
                existing_symptoms = ", ".join(existing_symptoms)

            prompt = build_enrichment_prompt(code, description, existing_causes, existing_symptoms)

            response = await self.generate_with_ai(prompt)
            if not response:
                async with self.lock:
                    self.failed += 1
                    self._print_progress(code, "FAIL", "AI generation failed")
                return False

            enriched_data = self.parse_ai_response(response)
            if not enriched_data:
                async with self.lock:
                    self.failed += 1
                    self._print_progress(code, "FAIL", "JSON parse failed")
                return False

            update_data = self.prepare_update_data(enriched_data)

            if self.dry_run:
                async with self.lock:
                    self.enriched += 1
                    self._print_progress(code, "DRY-RUN", "Would update")
                return True

            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda ud=update_data, c=code: self.client.table("obd_codes").update(ud).eq("code", c).execute()
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
                    self._print_progress(code, "FAIL", f"DB: {str(e)[:50]}")
                return False

    def _print_progress(self, code: str, status: str, message: str):
        """Print progress update."""
        done = self.enriched + self.failed + self.skipped
        elapsed = time.time() - self.start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (self.total - done) / rate if rate > 0 else 0

        print(f"  [{done}/{self.total}] {code}: [{status}] {message} "
              f"(rate: {rate:.2f}/s, ETA: {eta/60:.0f}min)")

    async def run(self, limit: Optional[int] = None, offset: int = 0, upgrade_local: bool = False):
        """Fetch codes and process them in parallel."""
        print("\n" + "=" * 70)
        print("PARALLEL AI ENRICHMENT (Gemini)")
        print("=" * 70)
        print(f"Model:    {settings.gemini_model}")
        print(f"Workers:  {self.workers}")
        print(f"Dry-run:  {self.dry_run}")
        print(f"Mode:     {'Upgrade local-enriched (score=70)' if upgrade_local else 'All unenriched (score<80)'}")
        print()

        print("[*] Fetching codes needing enrichment...")

        all_codes = []
        page_offset = offset
        page_size = 1000

        while True:
            query = self.client.table("obd_codes").select(
                "code, description, symptoms, common_causes, knowledge_score"
            ).order("code")

            if upgrade_local:
                query = query.eq("knowledge_score", 70.0)
            else:
                query = query.lt("knowledge_score", 80.0)

            query = query.range(page_offset, page_offset + page_size - 1)
            result = query.execute()

            if not result.data:
                break

            all_codes.extend(result.data)
            page_offset += page_size

            if limit and len(all_codes) >= limit:
                all_codes = all_codes[:limit]
                break

            if len(result.data) < page_size:
                break

            print(f"  Fetched {len(all_codes)} codes so far...")

        if not all_codes:
            print("[OK] No codes need enrichment!")
            return

        self.total = len(all_codes)
        print(f"[OK] Found {self.total} codes to enrich")
        print(f"[*] Starting parallel enrichment with {self.workers} workers...")
        print()

        tasks = [self.enrich_single_code(record) for record in all_codes]
        await asyncio.gather(*tasks)

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


async def main():
    parser = argparse.ArgumentParser(description="Parallel AI Enrichment using Gemini")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers (default: 5, Gemini free tier safe)")
    parser.add_argument("--limit", type=int, help="Limit number of codes to process")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N codes")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--upgrade-local", action="store_true", help="Only upgrade local-enriched codes (score=70)")
    args = parser.parse_args()

    if not settings.supabase_enabled:
        print("[ERROR] Supabase not enabled in .env")
        return 1

    if not settings.gemini_api_key:
        print("[ERROR] GEMINI_API_KEY not set in .env")
        return 1

    client = create_client(settings.supabase_url, settings.supabase_service_key)
    print(f"[OK] Supabase connected")
    print(f"[OK] Gemini AI ready (model: {settings.gemini_model})")

    enricher = GeminiParallelEnrichment(
        client=client,
        workers=args.workers,
        dry_run=args.dry_run
    )

    await enricher.run(limit=args.limit, offset=args.offset, upgrade_local=args.upgrade_local)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
