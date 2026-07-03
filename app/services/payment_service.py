"""
Payment service for Paynow integration.

Handles payment initiation, status polling, and subscription management.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from paynow import Paynow
from app.repositories.payment_repository import PaymentRepository
from app.core.config import settings
from app.core.logging import logger
from app.utils.phone import hash_phone_number


class PaymentService:
    """
    Service for handling Paynow payments and subscriptions.

    Implements:
    - Payment initiation (EcoCash mobile payments)
    - Status polling
    - Subscription creation
    - Access control (free tier + subscription)
    """

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo

        # Initialize Paynow client
        if not settings.paynow_integration_id or not settings.paynow_integration_key:
            logger.warning(
                "paynow_credentials_missing",
                message="Paynow credentials not configured - payments disabled"
            )
            self.paynow = None
        else:
            self.paynow = Paynow(
                integration_id=settings.paynow_integration_id,
                integration_key=settings.paynow_integration_key,
                return_url=settings.paynow_return_url,
                result_url=settings.paynow_result_url
            )
            logger.info("paynow_client_initialized")

    def _generate_order_reference(self, phone_hash: str) -> str:
        """Generate unique order reference"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"SUB-{timestamp}-{unique_id}"

    async def initiate_subscription_payment(
        self,
        user_phone: str,
        user_email: str,
        subscription_type: str = "monthly"
    ) -> dict:
        """
        Initiate a subscription payment via EcoCash.

        Args:
            user_phone: Zimbabwe phone number (e.g., '0771234567')
            user_email: User email (required by Paynow)
            subscription_type: 'monthly'

        Returns:
            Dict with: success, order_reference, poll_url, instructions, error, transaction_id
        """
        if not self.paynow:
            return {
                "success": False,
                "error": "Payment system not configured"
            }

        # Generate order reference
        phone_hash = hash_phone_number(f"whatsapp:{user_phone}")
        order_reference = self._generate_order_reference(phone_hash)

        # Get subscription price
        amount = float(settings.subscription_price)
        currency = "USD"
        description = f"Monthly Unlimited Diagnostics - {subscription_type.title()}"

        try:
            # Create transaction record (status=pending)
            transaction = self.payment_repo.create_transaction(
                phone_hash=phone_hash,
                amount=amount,
                currency=currency,
                description=description,
                order_reference=order_reference,
                user_email=user_email,
                user_phone=user_phone,
                subscription_type=subscription_type
            )

            # Create Paynow payment
            payment = self.paynow.create_payment(
                reference=order_reference,
                auth_email=user_email
            )

            # Add line item
            payment.add(description, amount)

            # Send mobile payment (EcoCash)
            logger.info(
                "paynow_payment_initiating",
                order_reference=order_reference,
                phone=user_phone,
                amount=amount
            )

            response = self.paynow.send_mobile(
                payment=payment,
                phone=user_phone,
                method='ecocash'
            )

            if response.success:
                # Update transaction with Paynow response
                self.payment_repo.update_transaction_paynow_response(
                    order_reference=order_reference,
                    paynow_reference=response.reference if hasattr(response, 'reference') else None,
                    poll_url=response.poll_url,
                    paynow_response={
                        "success": True,
                        "instructions": response.instructions,
                        "poll_url": response.poll_url
                    }
                )

                logger.info(
                    "paynow_payment_initiated",
                    order_reference=order_reference,
                    poll_url=response.poll_url
                )

                return {
                    "success": True,
                    "order_reference": order_reference,
                    "poll_url": response.poll_url,
                    "instructions": response.instructions,
                    "transaction_id": transaction["id"]
                }
            else:
                # Payment initiation failed
                self.payment_repo.update_transaction_status(
                    order_reference=order_reference,
                    status="failed"
                )

                logger.error(
                    "paynow_payment_failed",
                    order_reference=order_reference,
                    error=response.error if hasattr(response, 'error') else "Unknown error"
                )

                return {
                    "success": False,
                    "error": response.error if hasattr(response, 'error') else "Payment initiation failed"
                }

        except Exception as e:
            logger.error(
                "payment_initiation_error",
                order_reference=order_reference,
                error=str(e)
            )

            # Mark transaction as failed if it was created
            try:
                self.payment_repo.update_transaction_status(
                    order_reference=order_reference,
                    status="failed"
                )
            except:
                pass

            return {
                "success": False,
                "error": f"Payment initiation error: {str(e)}"
            }

    async def check_payment_status(self, order_reference: str) -> dict:
        """
        Check payment status by polling Paynow.

        Args:
            order_reference: Our order reference

        Returns:
            Dict with: status, amount, order_reference, paynow_reference, paid_at, subscription_end_date
        """
        if not self.paynow:
            return {
                "status": "failed",
                "error": "Payment system not configured"
            }

        # Get transaction from database
        transaction = self.payment_repo.get_transaction_by_order_reference(order_reference)

        if not transaction:
            logger.warning("transaction_not_found", order_reference=order_reference)
            return {
                "status": "not_found",
                "order_reference": order_reference
            }

        # If already paid, return cached status
        if transaction["status"] == "paid":
            return {
                "status": "paid",
                "amount": float(transaction["amount"]),
                "order_reference": order_reference,
                "paynow_reference": transaction.get("paynow_reference"),
                "paid_at": transaction.get("paid_at"),
                "subscription_end_date": transaction.get("subscription_end_date")
            }

        # If no poll_url, can't check status
        poll_url = transaction.get("poll_url")
        if not poll_url:
            logger.warning("no_poll_url", order_reference=order_reference)
            return {
                "status": transaction["status"],
                "order_reference": order_reference
            }

        try:
            # Poll Paynow for status
            logger.info("paynow_polling_status", order_reference=order_reference)

            status_response = self.paynow.check_transaction_status(poll_url)

            # Log response for debugging (without sensitive data)
            logger.info(
                "paynow_status_response",
                order_reference=order_reference,
                paid=status_response.paid,
                status=status_response.status if hasattr(status_response, 'status') else None
            )

            # Check if payment is confirmed
            if status_response.paid:
                # Payment confirmed - create subscription
                await self._process_successful_payment(
                    transaction=transaction,
                    paynow_reference=status_response.reference if hasattr(status_response, 'reference') else None
                )

                # Get updated transaction
                updated_transaction = self.payment_repo.get_transaction_by_order_reference(order_reference)

                return {
                    "status": "paid",
                    "amount": float(updated_transaction["amount"]),
                    "order_reference": order_reference,
                    "paynow_reference": updated_transaction.get("paynow_reference"),
                    "paid_at": updated_transaction.get("paid_at"),
                    "subscription_end_date": updated_transaction.get("subscription_end_date")
                }
            else:
                # Payment still pending or failed
                current_status = transaction["status"]

                # Update status if it changed
                new_status = self._map_paynow_status(status_response)
                if new_status != current_status:
                    self.payment_repo.update_transaction_status(
                        order_reference=order_reference,
                        status=new_status
                    )

                return {
                    "status": new_status,
                    "order_reference": order_reference
                }

        except Exception as e:
            logger.error(
                "payment_status_check_error",
                order_reference=order_reference,
                error=str(e)
            )

            return {
                "status": transaction["status"],
                "order_reference": order_reference,
                "error": str(e)
            }

    def _map_paynow_status(self, status_response) -> str:
        """Map Paynow status to our internal status"""
        if status_response.paid:
            return "paid"

        # Get status string if available
        if hasattr(status_response, 'status'):
            paynow_status = status_response.status.lower()

            if "cancel" in paynow_status:
                return "cancelled"
            elif "fail" in paynow_status or "error" in paynow_status:
                return "failed"

        return "pending"

    async def _process_successful_payment(
        self,
        transaction: dict,
        paynow_reference: Optional[str]
    ):
        """
        Process a successful payment: create subscription, update transaction.

        Args:
            transaction: Transaction record
            paynow_reference: Paynow's transaction reference
        """
        order_reference = transaction["order_reference"]

        try:
            # Calculate subscription dates
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30)  # Monthly subscription

            # Update transaction status
            self.payment_repo.update_transaction_status(
                order_reference=order_reference,
                status="paid",
                paynow_reference=paynow_reference
            )

            # Update subscription dates in transaction
            from supabase import Client
            client = self.payment_repo.client
            client.table("transactions").update({
                "subscription_start_date": start_date.isoformat(),
                "subscription_end_date": end_date.isoformat()
            }).eq("order_reference", order_reference).execute()

            # Create subscription record
            self.payment_repo.create_subscription(
                phone_hash=transaction["phone_hash"],
                subscription_type=transaction["subscription_type"],
                amount=float(transaction["amount"]),
                currency=transaction["currency"],
                start_date=start_date,
                end_date=end_date,
                transaction_id=transaction["id"]
            )

            logger.info(
                "payment_processed_subscription_created",
                order_reference=order_reference,
                subscription_end_date=end_date.isoformat()
            )

        except Exception as e:
            logger.error(
                "subscription_creation_error",
                order_reference=order_reference,
                error=str(e)
            )
            raise

    def check_user_access(self, phone_hash: str) -> dict:
        """
        Check if user can access diagnostic service.

        Returns:
            Dict with: can_access, reason, diagnostics_used, diagnostics_remaining, subscription_end_date
        """
        return self.payment_repo.check_access(
            phone_hash=phone_hash,
            free_limit=settings.free_diagnostics_limit
        )

    def increment_user_usage(self, phone_hash: str) -> int:
        """
        Increment user's diagnostic usage counter.

        Args:
            phone_hash: User phone hash

        Returns:
            New usage count
        """
        return self.payment_repo.increment_usage(phone_hash)

    def cancel_subscription(self, phone_hash: str) -> dict:
        """
        Cancel auto-renewal for active subscription.

        The subscription remains active until its expiry date.
        After expiry, user reverts to free tier.

        Args:
            phone_hash: User phone hash

        Returns:
            Dict with success, expires_at, or error
        """
        try:
            subscription = self.payment_repo.get_active_subscription(phone_hash)

            if not subscription:
                return {
                    "success": False,
                    "error": "No active subscription found"
                }

            # Set auto_renew = false
            self.payment_repo.update_subscription_auto_renew(
                subscription_id=subscription["id"],
                auto_renew=False
            )

            # Parse end_date (Supabase returns ISO string)
            end_date = subscription["end_date"]
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            logger.info(
                "subscription_cancelled",
                phone_hash=phone_hash,
                expires_at=end_date
            )

            return {
                "success": True,
                "expires_at": end_date.strftime("%Y-%m-%d")
            }

        except Exception as e:
            logger.error("cancel_subscription_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def poll_pending_transactions(self):
        """
        Background task: Poll all pending transactions.

        This should be called periodically (e.g., every 30 seconds).
        """
        if not self.paynow:
            return

        try:
            pending = self.payment_repo.get_pending_transactions(limit=50)

            logger.info(
                "polling_pending_transactions",
                count=len(pending)
            )

            for transaction in pending:
                order_reference = transaction["order_reference"]

                try:
                    # Check payment status
                    await self.check_payment_status(order_reference)
                except Exception as e:
                    logger.error(
                        "poll_transaction_error",
                        order_reference=order_reference,
                        error=str(e)
                    )

        except Exception as e:
            logger.error("poll_pending_transactions_error", error=str(e))
