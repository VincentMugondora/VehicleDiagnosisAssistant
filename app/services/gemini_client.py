import re
import base64
from typing import Dict, List
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger

_VISION_SYSTEM_PROMPT = """You are an expert automotive diagnostic assistant analyzing a photo.
Identify any visible issues: damage, leaks, worn parts, corrosion, loose connections,
fluid stains, or abnormal conditions. Be specific about component names and locations.
If you cannot identify any automotive components or issues, say so clearly.
Keep your response concise and actionable for a mechanic."""


class GeminiClient:
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        model = settings.gemini_model
        if model.startswith("models/"):
            model = model[len("models/"):]
        self.model = model

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
        )
        if response.text:
            return response.text
        raise RuntimeError("Gemini returned empty response")

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        user_context: str = "",
    ) -> str:
        """
        Analyze a vehicle photo for visible issues using Gemini vision.

        Args:
            image_bytes: Raw image data
            mime_type: MIME type of the image (image/jpeg, image/png, etc.)
            user_context: Optional user-provided description or question

        Returns:
            Analysis text describing visible issues
        """
        import asyncio

        prompt_text = _VISION_SYSTEM_PROMPT
        if user_context:
            prompt_text += f"\n\nUser's question/context: {user_context}"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        text_part = types.Part.from_text(text=prompt_text)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=[text_part, image_part],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000,
                )
            )
        )

        if response.text:
            return response.text
        raise RuntimeError("Gemini vision returned empty response")

    def rank_causes_with_retry(
        self,
        base_causes: list[str],
        vehicle_context: Dict[str, str],
        max_retries: int = 3
    ) -> list[str]:
        vehicle_str = " ".join(
            v for v in [
                vehicle_context.get("year"),
                vehicle_context.get("make"),
                vehicle_context.get("model"),
                vehicle_context.get("engine")
            ] if v
        ) or "generic vehicle"

        prompt = f"""Given these possible causes for an OBD-II fault code on a {vehicle_str}, rank the top 5 by likelihood. Return ONLY the causes as a numbered list (1-5), no explanations.

Causes:
{chr(10).join(f'- {c}' for c in base_causes)}"""

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    response = pool.submit(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=500,
                        )
                    ).result(timeout=15)
            else:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=500,
                    )
                )
        except Exception as e:
            logger.error("gemini_rank_failed", error=str(e))
            return base_causes[:5]

        if not response.text:
            return base_causes[:5]

        ranked = []
        for line in response.text.strip().split("\n"):
            line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
            if line:
                for cause in base_causes:
                    if cause.lower() in line.lower() or line.lower() in cause.lower():
                        if cause not in ranked:
                            ranked.append(cause)
                        break

        if len(ranked) < 3:
            return base_causes[:5]

        return ranked[:5]
