import time
import re
from typing import Dict, List
import cohere
from app.core.config import settings
from app.core.errors import GeminiUnavailable
from app.core.logging import logger


class CohereClient:
    """
    Cohere API client with retry logic and exponential backoff.

    Implements CLAUDE.md requirements:
    - Retry on 429/503 errors
    - Exponential backoff (1s, 2s, 4s)
    - Graceful degradation
    """

    def __init__(self):
        """Initialize Cohere client with API key from config"""
        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY not set in environment")
        self.client = cohere.Client(api_key=settings.cohere_api_key)

    def rank_causes_with_retry(
        self,
        base_causes: list[str],
        vehicle_context: Dict[str, str],
        max_retries: int = 3
    ) -> list[str]:
        """
        Rank OBD causes using Cohere with retry logic.

        Args:
            base_causes: List of possible causes
            vehicle_context: Dict with make, model, year, engine
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Ranked list of causes (top 5)

        Raises:
            GeminiUnavailable: If all retries fail (named for compatibility)
        """
        prompt = self._build_prompt(base_causes, vehicle_context)

        for attempt in range(max_retries):
            try:
                logger.info(
                    "cohere_request",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )

                response = self.client.chat(
                    model=settings.cohere_model,
                    message=prompt,
                    temperature=0.3,
                    max_tokens=500
                )

                ranked = self._parse_response(response.text, base_causes)

                logger.info(
                    "cohere_success",
                    ranked_count=len(ranked)
                )

                return ranked

            except Exception as e:
                error_str = str(e)
                is_retryable = (
                    "429" in error_str or
                    "503" in error_str or
                    "rate limit" in error_str.lower() or
                    "too many requests" in error_str.lower()
                )

                if attempt < max_retries - 1 and is_retryable:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "cohere_retry",
                        attempt=attempt + 1,
                        wait_seconds=wait,
                        error=error_str
                    )
                    time.sleep(wait)
                    continue

                # Final attempt failed or non-retryable error
                logger.error(
                    "cohere_failed",
                    attempt=attempt + 1,
                    error=error_str
                )

                # Graceful degradation: return original causes
                return base_causes[:5]

        # Should never reach here, but return fallback
        return base_causes[:5]

    def _build_prompt(
        self,
        causes: list[str],
        vehicle: Dict[str, str]
    ) -> str:
        """
        Build prompt for Cohere.

        Args:
            causes: List of possible causes
            vehicle: Vehicle context dict

        Returns:
            Formatted prompt string
        """
        make = vehicle.get("make", "")
        model = vehicle.get("model", "")
        year = vehicle.get("year", "")
        engine = vehicle.get("engine", "")

        return (
            "You are an automotive diagnostics assistant for mechanics. "
            "Only rephrase and rank the provided list of causes. "
            "Do not invent any new items. "
            "Return only the top 5 causes as a plain list, one per line, "
            "no numbering.\n\n"
            f"Vehicle: {make} {model} {year} {engine}\n"
            f"Causes to rank: {', '.join(causes)}\n\n"
            "Ranked causes (most likely first):"
        )

    def _parse_response(
        self,
        text: str,
        original_causes: list[str]
    ) -> list[str]:
        """
        Parse Cohere response and validate against original causes.

        Args:
            text: Cohere response text
            original_causes: Original cause list for validation

        Returns:
            Parsed and validated list of causes
        """
        if not text:
            return original_causes[:5]

        lines = text.splitlines()
        normalized = self._normalize_items(lines)

        # Filter: only keep causes that match original list
        allowed_set = {c.lower(): c for c in original_causes}
        filtered = []

        for item in normalized:
            key = item.lower()
            # Fuzzy match against allowed causes
            match = next(
                (
                    allowed_set[a.lower()]
                    for a in allowed_set
                    if key.startswith(a.lower()) or a.lower() in key
                ),
                None
            )
            if match and match not in filtered:
                filtered.append(match)

        # If no valid matches, return original
        if not filtered:
            logger.warning("cohere_parse_failed_no_matches")
            return original_causes[:5]

        return filtered[:5]

    def _normalize_items(self, lines: list[str]) -> list[str]:
        """
        Clean and normalize Cohere output lines.

        Args:
            lines: Raw output lines

        Returns:
            Cleaned list of strings
        """
        cleaned = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            # Remove leading bullets, numbers, dashes
            s = re.sub(r"^[\-•\d\.)\s]+", "", s)
            s = s.strip()
            if s:
                cleaned.append(s)
        return cleaned
