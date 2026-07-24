"""
Repository for payment-related database operations.
"""
from typing import Optional, List
from datetime import UTC, datetime, timedelta
from supabase import Client
from app.core.logging import logger


class PaymentRepository:
    """Handle payment-related database operations"""

    def __init__(self, client: Client):
        self.client = client

    def create_transaction(
        self,
        phone_hash: str,
        amount: float,
        currency: str,
        description: str,
        order_reference: str,
        user_email: str,
        user_phone: str,
        subscription_type: Optional[str] = None
    ) -> dict:
        """
        Create a new transaction record.

        Args:
            phone_hash: SHA-256 hash of user phone
            amount: Payment amount
            currency: Currency code (USD)
            description: Payment description
            order_reference: Unique order reference
            user_email: User email
            user_phone: User phone (Zimbabwe format)
            subscription_type: 'monthly' or None

        Returns:
            Created transaction record
        """
        data = {
            "phone_hash": phone_hash,
            "amount": amount,
            "currency": currency,
            "description": description,
            "status": "pending",
            "order_reference": order_reference,
            "user_email": user_email,
            "user_phone": user_phone,
            "subscription_type": subscription_type
        }

        response = self.client.table("transactions").insert(data).execute()

        if response.data:
            logger.info(
                "transaction_created",
                order_reference=order_reference,
                amount=amount
            )
            return response.data[0]

        raise Exception("Failed to create transaction")

    def update_transaction_paynow_response(
        self,
        order_reference: str,
        paynow_reference: Optional[str],
        poll_url: Optional[str],
        paynow_response: dict
    ) -> dict:
        """
        Update transaction with Paynow API response.

        Args:
            order_reference: Our order reference
            paynow_reference: Paynow's transaction reference
            poll_url: URL for polling payment status
            paynow_response: Full Paynow response (for debugging)

        Returns:
            Updated transaction
        """
        update_data = {
            "paynow_reference": paynow_reference,
            "poll_url": poll_url,
            "paynow_response": paynow_response,
            "updated_at": datetime.now(UTC).isoformat()
        }

        response = self.client.table("transactions").update(update_data).eq(
            "order_reference", order_reference
        ).execute()

        if response.data:
            return response.data[0]

        raise Exception(f"Failed to update transaction {order_reference}")

    def update_transaction_status(
        self,
        order_reference: str,
        status: str,
        paynow_reference: Optional[str] = None
    ) -> dict:
        """
        Update transaction status.

        Args:
            order_reference: Our order reference
            status: New status ('pending', 'paid', 'failed', 'cancelled', 'expired')
            paynow_reference: Paynow reference (if available)

        Returns:
            Updated transaction
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now(UTC).isoformat()
        }

        if paynow_reference:
            update_data["paynow_reference"] = paynow_reference

        if status == "paid":
            update_data["paid_at"] = datetime.now(UTC).isoformat()

        response = self.client.table("transactions").update(update_data).eq(
            "order_reference", order_reference
        ).execute()

        if response.data:
            logger.info(
                "transaction_status_updated",
                order_reference=order_reference,
                status=status
            )
            return response.data[0]

        raise Exception(f"Failed to update transaction status {order_reference}")

    def get_transaction_by_order_reference(self, order_reference: str) -> Optional[dict]:
        """Get transaction by our order reference"""
        response = self.client.table("transactions").select("*").eq(
            "order_reference", order_reference
        ).execute()

        return response.data[0] if response.data else None

    def get_pending_transactions(self, limit: int = 100) -> List[dict]:
        """
        Get pending transactions for polling.

        Args:
            limit: Max number of records to return

        Returns:
            List of pending transactions
        """
        # Only get transactions from last hour (older ones are likely expired)
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        response = self.client.table("transactions").select("*").eq(
            "status", "pending"
        ).gte(
            "created_at", one_hour_ago
        ).limit(limit).execute()

        return response.data if response.data else []

    def create_subscription(
        self,
        phone_hash: str,
        subscription_type: str,
        amount: float,
        currency: str,
        start_date: datetime,
        end_date: datetime,
        transaction_id: str
    ) -> dict:
        """
        Create a new subscription after successful payment.

        Args:
            phone_hash: User phone hash
            subscription_type: 'monthly'
            amount: Subscription price
            currency: Currency code
            start_date: Subscription start
            end_date: Subscription end
            transaction_id: Related transaction ID

        Returns:
            Created subscription
        """
        # Deactivate any existing subscriptions for this user
        self.client.table("subscriptions").update({
            "is_active": False,
            "updated_at": datetime.now(UTC).isoformat()
        }).eq("phone_hash", phone_hash).eq("is_active", True).execute()

        # Create new subscription
        data = {
            "phone_hash": phone_hash,
            "subscription_type": subscription_type,
            "amount": amount,
            "currency": currency,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "is_active": True,
            "transaction_id": transaction_id,
            "auto_renew": False
        }

        response = self.client.table("subscriptions").insert(data).execute()

        if response.data:
            logger.info(
                "subscription_created",
                phone_hash=phone_hash,
                end_date=end_date.isoformat()
            )
            return response.data[0]

        raise Exception("Failed to create subscription")

    def get_active_subscription(self, phone_hash: str) -> Optional[dict]:
        """
        Get user's active subscription.

        Args:
            phone_hash: User phone hash

        Returns:
            Active subscription or None
        """
        response = self.client.table("subscriptions").select("*").eq(
            "phone_hash", phone_hash
        ).eq(
            "is_active", True
        ).gt(
            "end_date", datetime.now(UTC).isoformat()
        ).execute()

        return response.data[0] if response.data else None

    def has_active_subscription(self, phone_hash: str) -> bool:
        """Check if user has an active subscription"""
        return self.get_active_subscription(phone_hash) is not None

    def get_weekly_usage(self, phone_hash: str) -> int:
        """
        Get user's diagnostic count for current week.

        Args:
            phone_hash: User phone hash

        Returns:
            Number of diagnostics used this week
        """
        # Calculate current week boundaries (Monday to Sunday)
        now = datetime.now(UTC)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        response = self.client.table("user_usage").select("diagnostics_count").eq(
            "phone_hash", phone_hash
        ).eq(
            "period_start", week_start.isoformat()
        ).execute()

        if response.data:
            return response.data[0]["diagnostics_count"]

        return 0

    def increment_usage(self, phone_hash: str) -> int:
        """
        Increment user's diagnostic usage for current week.

        Args:
            phone_hash: User phone hash

        Returns:
            New usage count
        """
        # Calculate current week boundaries
        now = datetime.now(UTC)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        # Check if record exists
        existing = self.client.table("user_usage").select("*").eq(
            "phone_hash", phone_hash
        ).eq(
            "period_start", week_start.isoformat()
        ).execute()

        if existing.data:
            # Update existing record
            new_count = existing.data[0]["diagnostics_count"] + 1
            self.client.table("user_usage").update({
                "diagnostics_count": new_count,
                "updated_at": datetime.now(UTC).isoformat()
            }).eq(
                "phone_hash", phone_hash
            ).eq(
                "period_start", week_start.isoformat()
            ).execute()

            return new_count
        else:
            # Create new record
            data = {
                "phone_hash": phone_hash,
                "diagnostics_count": 1,
                "period_start": week_start.isoformat(),
                "period_end": week_end.isoformat(),
                "was_subscribed": self.has_active_subscription(phone_hash)
            }

            response = self.client.table("user_usage").insert(data).execute()

            if response.data:
                return 1

        raise Exception("Failed to increment usage")

    def update_subscription_auto_renew(
        self,
        subscription_id: str,
        auto_renew: bool
    ) -> bool:
        """
        Update auto_renew setting for a subscription.

        Args:
            subscription_id: Subscription UUID
            auto_renew: New auto_renew value

        Returns:
            True if successful
        """
        response = (
            self.client.table("subscriptions")
            .update({"auto_renew": auto_renew})
            .eq("id", subscription_id)
            .execute()
        )

        return len(response.data) > 0

    def get_pending_transactions_by_phone(
        self,
        phone_hash: str,
        limit: int = 1
    ) -> list[dict]:
        """
        Get pending transactions for a specific user.

        Args:
            phone_hash: User phone hash
            limit: Max number to return

        Returns:
            List of pending transaction dicts
        """
        response = (
            self.client.table("transactions")
            .select("*")
            .eq("phone_hash", phone_hash)
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data

    def get_expired_subscription(self, phone_hash: str) -> Optional[dict]:
        """
        Get most recent expired subscription for user.

        Args:
            phone_hash: User phone hash

        Returns:
            Expired subscription dict or None
        """
        response = (
            self.client.table("subscriptions")
            .select("*")
            .eq("phone_hash", phone_hash)
            .eq("is_active", False)
            .order("end_date", desc=True)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    def get_subscription_by_phone(self, phone_hash: str) -> Optional[dict]:
        """
        Get any subscription (active or not) for user.

        Args:
            phone_hash: User phone hash

        Returns:
            Most recent subscription dict or None
        """
        response = (
            self.client.table("subscriptions")
            .select("*")
            .eq("phone_hash", phone_hash)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    def update_subscription(
        self,
        subscription_id: str,
        start_date,
        end_date,
        is_active: bool,
        transaction_id: str
    ) -> bool:
        """
        Update existing subscription with new dates.

        Args:
            subscription_id: Subscription UUID
            start_date: New start date
            end_date: New end date
            is_active: Active status
            transaction_id: New transaction ID

        Returns:
            True if successful
        """
        response = (
            self.client.table("subscriptions")
            .update({
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "is_active": is_active,
                "transaction_id": transaction_id
            })
            .eq("id", subscription_id)
            .execute()
        )

        return len(response.data) > 0

    def mark_subscription_expired(self, subscription_id: str) -> bool:
        """
        Mark subscription as expired (is_active=false).

        Args:
            subscription_id: Subscription UUID

        Returns:
            True if successful
        """
        response = (
            self.client.table("subscriptions")
            .update({"is_active": False})
            .eq("id", subscription_id)
            .execute()
        )

        return len(response.data) > 0

    def check_access(self, phone_hash: str, free_limit: int = 5) -> dict:
        """
        Check if user can access diagnostic service.

        Args:
            phone_hash: User phone hash
            free_limit: Free diagnostics per week

        Returns:
            Dict with: can_access, reason, diagnostics_used, diagnostics_remaining, subscription_end_date
        """
        # Check subscription first
        subscription = self.get_active_subscription(phone_hash)
        if subscription:
            return {
                "can_access": True,
                "reason": "subscribed",
                "diagnostics_used": 0,
                "diagnostics_remaining": -1,  # -1 means unlimited
                "subscription_end_date": subscription["end_date"]
            }

        # Check free tier usage
        usage_count = self.get_weekly_usage(phone_hash)

        if usage_count < free_limit:
            return {
                "can_access": True,
                "reason": "within_free_limit",
                "diagnostics_used": usage_count,
                "diagnostics_remaining": free_limit - usage_count,
                "subscription_end_date": None
            }

        # Free limit exceeded
        return {
            "can_access": False,
            "reason": "limit_exceeded",
            "diagnostics_used": usage_count,
            "diagnostics_remaining": 0,
            "subscription_end_date": None
        }
