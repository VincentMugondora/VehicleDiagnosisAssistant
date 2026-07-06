"""
Service for sending images via WhatsApp (Baileys).

Handles system diagram images with timeouts and error recovery.
"""
import asyncio
from typing import Optional
import httpx
from app.models.system_diagram import SystemDiagram
from app.core.logging import logger
from app.core.config import settings


class ImageSendError(Exception):
    """Error sending image via WhatsApp"""
    pass


class ImageSender:
    """
    Send images via Baileys WhatsApp backend.

    Images are sent as separate messages before text diagnosis.
    Failures are logged but never block the text diagnosis.
    """

    def __init__(self, baileys_webhook_url: Optional[str] = None, timeout: float = 10.0):
        """
        Initialize image sender.

        Args:
            baileys_webhook_url: Optional Baileys outbound webhook URL
            timeout: Max seconds to wait for image send (default: 10s)
        """
        self.baileys_webhook_url = baileys_webhook_url or getattr(
            settings, 'baileys_outbound_url', None
        )
        self.timeout = timeout

    async def send_system_diagram(
        self,
        to_number: str,
        diagram: SystemDiagram
    ) -> bool:
        """
        Send system diagram image to WhatsApp user.

        This is a fire-and-forget operation with timeout protection.
        Errors are logged but never propagate to caller.

        Args:
            to_number: Recipient WhatsApp number (e.g., "263771234567")
            diagram: System diagram to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.baileys_webhook_url:
            logger.warning(
                "image_send_skipped",
                reason="baileys_outbound_url_not_configured"
            )
            return False

        try:
            # Wrap in timeout to prevent stalling
            result = await asyncio.wait_for(
                self._send_image_internal(to_number, diagram),
                timeout=self.timeout
            )
            return result

        except asyncio.TimeoutError:
            logger.warning(
                "image_send_timeout",
                to=to_number,
                system=diagram.system,
                timeout=self.timeout
            )
            return False

        except Exception as e:
            logger.error(
                "image_send_failed",
                to=to_number,
                system=diagram.system,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    async def _send_image_internal(
        self,
        to_number: str,
        diagram: SystemDiagram
    ) -> bool:
        """
        Internal method to send image via Baileys webhook.

        Args:
            to_number: Recipient number
            diagram: System diagram

        Returns:
            True if successful

        Raises:
            ImageSendError: If send fails
        """
        # Prepare payload for Baileys
        # Format: {to: "number", image: {url: "..."}, caption: "..."}
        payload = {
            "to": to_number,
            "image": {
                "url": diagram.image_url
            }
        }

        # Add caption if present (keep short for WhatsApp)
        if diagram.caption:
            # Truncate to 60 chars for WhatsApp compatibility
            caption = diagram.caption[:60]
            payload["caption"] = caption

        logger.info(
            "sending_system_diagram",
            to=to_number,
            system=diagram.system,
            image_url=diagram.image_url
        )

        # Send via HTTP POST to Baileys webhook
        headers = {"Content-Type": "application/json"}

        # Add API key if configured
        baileys_api_key = getattr(settings, 'baileys_api_key', None)
        if baileys_api_key:
            headers["X-API-Key"] = baileys_api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.baileys_webhook_url,
                json=payload,
                headers=headers
            )

            # Check response
            if response.status_code == 200:
                logger.info(
                    "system_diagram_sent",
                    to=to_number,
                    system=diagram.system
                )
                return True
            else:
                logger.warning(
                    "system_diagram_send_failed",
                    to=to_number,
                    system=diagram.system,
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False


def format_attribution(diagram: SystemDiagram) -> Optional[str]:
    """
    Format attribution text for appending to text diagnosis.

    Args:
        diagram: System diagram with optional attribution

    Returns:
        Formatted attribution line or None
    """
    if not diagram.attribution_text:
        return None

    # Format as small line at end of diagnosis
    return f"\n\n📷 Diagram: {diagram.attribution_text}"
