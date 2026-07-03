"""
Background payment poller for checking pending Paynow transactions.

This runs periodically to check payment status without relying solely on webhooks.
"""
import asyncio
from datetime import datetime
from app.services.payment_service import PaymentService
from app.repositories.payment_repository import PaymentRepository
from app.db.client import get_supabase_client
from app.core.logging import logger


class PaymentPoller:
    """Background task for polling pending payments"""

    def __init__(self, poll_interval: int = 30):
        """
        Initialize payment poller.

        Args:
            poll_interval: Seconds between poll cycles (default: 30)
        """
        self.poll_interval = poll_interval
        self.running = False

    async def start(self):
        """Start the payment poller background task"""
        self.running = True

        logger.info(
            "payment_poller_started",
            poll_interval=self.poll_interval
        )

        while self.running:
            try:
                await self.poll_pending_payments()
            except Exception as e:
                logger.error(
                    "payment_poller_error",
                    error=str(e)
                )

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """Stop the payment poller"""
        self.running = False
        logger.info("payment_poller_stopped")

    async def poll_pending_payments(self):
        """Poll all pending transactions"""
        client = get_supabase_client()

        if not client:
            logger.warning("payment_poller_skipped_no_db")
            return

        try:
            payment_repo = PaymentRepository(client)
            payment_service = PaymentService(payment_repo)

            # Get pending transactions
            pending = payment_repo.get_pending_transactions(limit=50)

            if not pending:
                logger.debug("no_pending_transactions")
                return

            logger.info(
                "polling_pending_transactions",
                count=len(pending)
            )

            # Check each transaction
            for transaction in pending:
                order_reference = transaction["order_reference"]

                try:
                    # Check payment status
                    result = await payment_service.check_payment_status(order_reference)

                    # Log if status changed
                    if result["status"] != transaction["status"]:
                        logger.info(
                            "payment_status_changed",
                            order_reference=order_reference,
                            old_status=transaction["status"],
                            new_status=result["status"]
                        )

                except Exception as e:
                    logger.error(
                        "poll_transaction_error",
                        order_reference=order_reference,
                        error=str(e)
                    )

                # Small delay between checks to avoid rate limiting
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error("poll_pending_payments_error", error=str(e))


# Global poller instance
_poller: PaymentPoller | None = None


def get_payment_poller() -> PaymentPoller:
    """Get or create global payment poller instance"""
    global _poller

    if _poller is None:
        _poller = PaymentPoller(poll_interval=30)

    return _poller


async def start_payment_poller():
    """Start the global payment poller"""
    poller = get_payment_poller()

    if not poller.running:
        # Run in background task
        asyncio.create_task(poller.start())
        logger.info("payment_poller_background_task_started")


def stop_payment_poller():
    """Stop the global payment poller"""
    poller = get_payment_poller()
    poller.stop()
