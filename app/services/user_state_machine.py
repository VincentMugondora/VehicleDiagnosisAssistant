"""
User state machine for payment lifecycle.

States: new_user -> free_tier -> pending_payment -> active_subscriber -> expired

Identity: Phone number (hashed) is sole identity, no separate auth.
"""
from enum import Enum
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Union
from dataclasses import dataclass
from app.repositories.payment_repository import PaymentRepository
from app.core.logging import logger
from app.core.config import settings


def _parse_datetime(dt: Union[str, datetime]) -> datetime:
    """
    Parse datetime from string or return datetime object as-is.

    Supabase returns ISO format strings, we need datetime objects for comparison.
    """
    if isinstance(dt, str):
        # Parse ISO format: "2026-07-03T11:43:22.595519+00:00"
        return datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt


def _utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


class UserState(Enum):
    """User lifecycle states"""
    NEW_USER = "new_user"
    FREE_TIER = "free_tier"
    PENDING_PAYMENT = "pending_payment"
    ACTIVE_SUBSCRIBER = "active_subscriber"
    EXPIRED = "expired"


class StateTransitionTrigger(Enum):
    """What triggered a state transition"""
    FIRST_MESSAGE = "first_message"
    SUBSCRIBE_COMMAND = "subscribe_command"
    RENEW_COMMAND = "renew_command"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_TIMEOUT = "payment_timeout"
    PAYMENT_DECLINED = "payment_declined"
    SUBSCRIPTION_EXPIRED = "subscription_expired"


@dataclass
class UserStateInfo:
    """Complete user state information"""
    state: UserState
    phone_hash: str

    # Free tier
    diagnostics_used: int = 0
    diagnostics_remaining: int = 5

    # Subscription
    has_active_subscription: bool = False
    subscription_end_date: Optional[datetime] = None
    auto_renew: bool = False

    # Pending payment
    has_pending_transaction: bool = False
    pending_transaction_id: Optional[str] = None
    pending_order_reference: Optional[str] = None
    transaction_created_at: Optional[datetime] = None

    # Access control
    can_access_diagnostic: bool = True
    reason: str = ""


class UserStateMachine:
    """
    State machine for user payment lifecycle.

    Resolves current state based on database records, not stored state field.
    Single source of truth for all access control and command handling.
    """

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo
        self.free_tier_limit = settings.free_diagnostics_limit
        self.payment_timeout_minutes = 15  # Timeout for pending payments

    def resolve_state(self, phone_hash: str) -> UserStateInfo:
        """
        Resolve current user state from database records.

        This is the single source of truth for user state.
        Called at the top of every message before processing.

        State resolution logic:
        1. Check for active subscription (is_active=true, end_date > now)
           -> active_subscriber
        2. Check for pending transaction (status='pending', created < 15min ago)
           -> pending_payment
        3. Check for expired subscription (is_active=false OR end_date <= now)
           -> expired (behaves like free_tier for access)
        4. Check free tier usage (diagnostics_count this week)
           -> free_tier
        5. No records at all
           -> new_user (will become free_tier on first diagnostic)

        Args:
            phone_hash: User's hashed phone number

        Returns:
            UserStateInfo with complete state
        """
        logger.info("resolving_user_state", phone_hash=phone_hash)

        # Check for active subscription first
        subscription = self.payment_repo.get_active_subscription(phone_hash)

        if subscription:
            # Active subscriber
            end_date = _parse_datetime(subscription["end_date"])

            # Double-check expiry (db might not have marked it yet)
            if end_date > _utcnow():
                logger.info(
                    "state_resolved",
                    phone_hash=phone_hash,
                    state="active_subscriber",
                    expires_at=end_date.isoformat()
                )

                return UserStateInfo(
                    state=UserState.ACTIVE_SUBSCRIBER,
                    phone_hash=phone_hash,
                    has_active_subscription=True,
                    subscription_end_date=end_date,
                    auto_renew=subscription.get("auto_renew", False),
                    diagnostics_remaining=-1,  # Unlimited
                    can_access_diagnostic=True,
                    reason="active_subscription"
                )
            else:
                # Subscription just expired, mark it
                logger.info(
                    "subscription_expired_on_check",
                    phone_hash=phone_hash,
                    end_date=end_date.isoformat()
                )
                self._mark_subscription_expired(subscription["id"])
                # Fall through to expired state

        # Check for pending transaction
        pending_tx = self.payment_repo.get_pending_transactions_by_phone(
            phone_hash,
            limit=1
        )

        if pending_tx:
            tx = pending_tx[0]
            created_at = _parse_datetime(tx["created_at"])

            # Check if payment has timed out
            timeout_threshold = _utcnow() - timedelta(
                minutes=self.payment_timeout_minutes
            )

            if created_at < timeout_threshold:
                # Payment timed out
                logger.info(
                    "payment_timeout_detected",
                    phone_hash=phone_hash,
                    order_reference=tx["order_reference"],
                    created_at=created_at.isoformat()
                )

                self._expire_transaction(tx["order_reference"], "timeout")
                # Fall through to check other states
            else:
                # Still pending, within timeout window
                logger.info(
                    "state_resolved",
                    phone_hash=phone_hash,
                    state="pending_payment",
                    order_reference=tx["order_reference"]
                )

                # Get usage for free tier info
                usage = self.payment_repo.get_weekly_usage(phone_hash)

                return UserStateInfo(
                    state=UserState.PENDING_PAYMENT,
                    phone_hash=phone_hash,
                    has_pending_transaction=True,
                    pending_transaction_id=tx["id"],
                    pending_order_reference=tx["order_reference"],
                    transaction_created_at=created_at,
                    diagnostics_used=usage,
                    diagnostics_remaining=max(0, self.free_tier_limit - usage),
                    can_access_diagnostic=(usage < self.free_tier_limit),
                    reason="pending_payment"
                )

        # Check if user has expired subscription (falls back to free tier)
        expired_sub = self.payment_repo.get_expired_subscription(phone_hash)

        if expired_sub:
            usage = self.payment_repo.get_weekly_usage(phone_hash)

            logger.info(
                "state_resolved",
                phone_hash=phone_hash,
                state="expired",
                usage=usage
            )

            return UserStateInfo(
                state=UserState.EXPIRED,
                phone_hash=phone_hash,
                diagnostics_used=usage,
                diagnostics_remaining=max(0, self.free_tier_limit - usage),
                can_access_diagnostic=(usage < self.free_tier_limit),
                reason="expired_subscription"
            )

        # Check free tier usage
        usage = self.payment_repo.get_weekly_usage(phone_hash)

        if usage > 0:
            # User has used diagnostics before -> free_tier
            logger.info(
                "state_resolved",
                phone_hash=phone_hash,
                state="free_tier",
                usage=usage
            )

            return UserStateInfo(
                state=UserState.FREE_TIER,
                phone_hash=phone_hash,
                diagnostics_used=usage,
                diagnostics_remaining=max(0, self.free_tier_limit - usage),
                can_access_diagnostic=(usage < self.free_tier_limit),
                reason="free_tier"
            )

        # No records at all -> new user
        logger.info(
            "state_resolved",
            phone_hash=phone_hash,
            state="new_user"
        )

        return UserStateInfo(
            state=UserState.NEW_USER,
            phone_hash=phone_hash,
            diagnostics_remaining=self.free_tier_limit,
            can_access_diagnostic=True,
            reason="new_user"
        )

    def transition_to_pending_payment(
        self,
        phone_hash: str,
        transaction_id: str,
        order_reference: str,
        trigger: StateTransitionTrigger
    ) -> UserStateInfo:
        """
        Transition user to pending_payment state.

        Called after initiating payment (SUBSCRIBE or RENEW command).

        Args:
            phone_hash: User's hashed phone
            transaction_id: Created transaction ID
            order_reference: Paynow order reference
            trigger: What triggered this transition

        Returns:
            New state info
        """
        current_state = self.resolve_state(phone_hash)

        logger.info(
            "state_transition",
            phone_hash=phone_hash,
            from_state=current_state.state.value,
            to_state="pending_payment",
            trigger=trigger.value,
            transaction_id=transaction_id,
            order_reference=order_reference
        )

        # State is now pending_payment
        # Re-resolve to get fresh state
        return self.resolve_state(phone_hash)

    def transition_to_active_subscriber(
        self,
        phone_hash: str,
        transaction_id: str,
        order_reference: str
    ) -> Tuple[bool, UserStateInfo, str]:
        """
        Transition user to active_subscriber state.

        Called when Paynow webhook confirms payment.
        IDEMPOTENT: Only transitions if transaction status is 'pending'.

        Args:
            phone_hash: User's hashed phone
            transaction_id: Transaction ID being confirmed
            order_reference: Paynow order reference

        Returns:
            Tuple of (success: bool, new_state: UserStateInfo, reason: str)
        """
        current_state = self.resolve_state(phone_hash)

        # Get transaction
        transaction = self.payment_repo.get_transaction_by_order_reference(
            order_reference
        )

        if not transaction:
            logger.error(
                "transaction_not_found",
                order_reference=order_reference,
                phone_hash=phone_hash
            )
            return (False, current_state, "Transaction not found")

        # IDEMPOTENCY CHECK: Only process if currently 'pending'
        if transaction["status"] != "pending":
            logger.warning(
                "duplicate_webhook_ignored",
                phone_hash=phone_hash,
                order_reference=order_reference,
                current_status=transaction["status"],
                message="Transaction already processed, ignoring duplicate webhook"
            )
            # Re-resolve state and return
            new_state = self.resolve_state(phone_hash)
            return (False, new_state, f"Already processed (status={transaction['status']})")

        # Update transaction status to 'paid'
        self.payment_repo.update_transaction_status(
            order_reference=order_reference,
            status="paid"
        )

        # Create or extend subscription
        start_date = _utcnow()
        end_date = start_date + timedelta(days=30)  # 30-day subscription

        # Check if they have an existing subscription (even if expired)
        existing_sub = self.payment_repo.get_subscription_by_phone(phone_hash)

        if existing_sub:
            # Update existing subscription
            self.payment_repo.update_subscription(
                subscription_id=existing_sub["id"],
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                transaction_id=transaction_id
            )
        else:
            # Create new subscription
            self.payment_repo.create_subscription(
                phone_hash=phone_hash,
                amount=transaction["amount"],
                currency=transaction["currency"],
                subscription_type=transaction.get("subscription_type", "monthly"),
                start_date=start_date,
                end_date=end_date,
                transaction_id=transaction_id
            )

        logger.info(
            "state_transition",
            phone_hash=phone_hash,
            from_state=current_state.state.value,
            to_state="active_subscriber",
            trigger="payment_confirmed",
            transaction_id=transaction_id,
            order_reference=order_reference,
            expires_at=end_date.isoformat()
        )

        # Re-resolve state
        new_state = self.resolve_state(phone_hash)
        return (True, new_state, "Payment confirmed, subscription activated")

    def _mark_subscription_expired(self, subscription_id: str):
        """Mark subscription as expired (is_active=false)"""
        self.payment_repo.mark_subscription_expired(subscription_id)

    def _expire_transaction(self, order_reference: str, reason: str):
        """
        Expire a pending transaction.

        Called when payment times out or is declined.
        """
        logger.info(
            "expiring_transaction",
            order_reference=order_reference,
            reason=reason
        )

        self.payment_repo.update_transaction_status(
            order_reference=order_reference,
            status="expired"
        )
