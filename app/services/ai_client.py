"""
Unified AI client that supports multiple providers (Cohere, Gemini).

Automatically selects provider based on AI_PROVIDER environment variable.
Supports Gemini as automatic fallback when primary provider fails.
"""
from typing import Dict
from app.core.config import settings
from app.core.logging import logger


class AIClient:
    """
    Unified AI client with automatic provider selection and fallback.

    Supports:
    - Cohere (default)
    - Gemini (legacy/fallback)

    When Cohere is the primary provider, Gemini will be used as backup
    if Cohere fails or is unavailable.
    """

    def __init__(self):
        """Initialize AI client based on configured provider"""
        self.provider = settings.ai_provider.lower()
        self._client = None
        self._backup_client = None

        if self.provider == "cohere":
            from app.services.cohere_client import CohereClient
            self._client = CohereClient()
            logger.info("ai_client_initialized", provider="cohere")

            # Initialize Gemini as backup if API key is available
            if settings.gemini_api_key:
                try:
                    from app.services.gemini_client import GeminiClient
                    self._backup_client = GeminiClient()
                    logger.info("ai_backup_initialized", backup_provider="gemini")
                except Exception as e:
                    logger.warning("ai_backup_init_failed", error=str(e))

        elif self.provider == "gemini":
            from app.services.gemini_client import GeminiClient
            self._client = GeminiClient()
            logger.info("ai_client_initialized", provider="gemini")
        else:
            raise ValueError(
                f"Unsupported AI provider: {self.provider}. "
                f"Supported: cohere, gemini"
            )

    def rank_causes_with_retry(
        self,
        base_causes: list[str],
        vehicle_context: Dict[str, str],
        max_retries: int = 3
    ) -> list[str]:
        """
        Rank OBD causes using configured AI provider with fallback.

        Args:
            base_causes: List of possible causes
            vehicle_context: Dict with make, model, year, engine
            max_retries: Maximum retry attempts

        Returns:
            Ranked list of causes (top 5)
        """
        try:
            # Try primary provider
            result = self._client.rank_causes_with_retry(
                base_causes=base_causes,
                vehicle_context=vehicle_context,
                max_retries=max_retries
            )

            # If result is unchanged (fallback to original), try backup
            if result == base_causes[:5] and self._backup_client:
                logger.info("ai_attempting_backup", reason="primary_returned_unchanged")
                return self._try_backup_rank(base_causes, vehicle_context, max_retries)

            return result

        except Exception as e:
            logger.error("ai_primary_failed", error=str(e))

            # Try backup provider if available
            if self._backup_client:
                return self._try_backup_rank(base_causes, vehicle_context, max_retries)

            # No backup available, return original
            logger.warning("ai_no_backup_available")
            return base_causes[:5]

    def _try_backup_rank(
        self,
        base_causes: list[str],
        vehicle_context: Dict[str, str],
        max_retries: int
    ) -> list[str]:
        """
        Try ranking with backup provider (Gemini).

        Returns:
            Ranked causes or original list if backup fails
        """
        try:
            logger.info("ai_using_backup", provider="gemini")
            result = self._backup_client.rank_causes_with_retry(
                base_causes=base_causes,
                vehicle_context=vehicle_context,
                max_retries=max_retries
            )
            logger.info("ai_backup_success")
            return result
        except Exception as e:
            logger.error("ai_backup_failed", error=str(e))
            return base_causes[:5]

    async def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text completion using configured AI provider with fallback.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            # Try primary provider
            return await self._client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error("ai_complete_primary_failed", error=str(e))

            # Try backup provider if available
            if self._backup_client:
                try:
                    logger.info("ai_complete_using_backup", provider="gemini")
                    result = await self._backup_client.generate(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    logger.info("ai_complete_backup_success")
                    return result
                except Exception as backup_error:
                    logger.error("ai_complete_backup_failed", error=str(backup_error))
                    raise

            # No backup available, re-raise original error
            raise


# Factory function for easy import
def get_ai_client() -> AIClient:
    """Get AI client instance (singleton pattern recommended)"""
    return AIClient()
