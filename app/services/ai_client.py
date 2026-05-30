"""
Unified AI client that supports multiple providers (Cohere, Gemini).

Automatically selects provider based on AI_PROVIDER environment variable.
"""
from typing import Dict
from app.core.config import settings
from app.core.logging import logger


class AIClient:
    """
    Unified AI client with automatic provider selection.

    Supports:
    - Cohere (default)
    - Gemini (legacy)
    """

    def __init__(self):
        """Initialize AI client based on configured provider"""
        self.provider = settings.ai_provider.lower()
        self._client = None

        if self.provider == "cohere":
            from app.services.cohere_client import CohereClient
            self._client = CohereClient()
            logger.info("ai_client_initialized", provider="cohere")
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
        Rank OBD causes using configured AI provider.

        Args:
            base_causes: List of possible causes
            vehicle_context: Dict with make, model, year, engine
            max_retries: Maximum retry attempts

        Returns:
            Ranked list of causes (top 5)
        """
        return self._client.rank_causes_with_retry(
            base_causes=base_causes,
            vehicle_context=vehicle_context,
            max_retries=max_retries
        )

    async def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text completion using configured AI provider.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        return await self._client.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )


# Factory function for easy import
def get_ai_client() -> AIClient:
    """Get AI client instance (singleton pattern recommended)"""
    return AIClient()
