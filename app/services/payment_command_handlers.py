"""
Payment command handlers with state machine integration.

Commands: SUBSCRIBE, RENEW, CANCEL, STATUS, HELP
"""
from typing import Optional, Tuple
from datetime import datetime
from app.services.user_state_machine import (
    UserStateMachine,
    UserState,
    StateTransitionTrigger
)
from app.services.payment_service import PaymentService
from app.core.logging import logger


class PaymentCommandHandler:
    """
    Handles payment commands with clean state machine integration.

    All commands receive resolved state and work with it,
    ensuring single source of truth.
    """

    def __init__(
        self,
        state_machine: UserStateMachine,
        payment_service: PaymentService
    ):
        self.state_machine = state_machine
        self.payment_service = payment_service

    # ==================== COMMAND PARSERS ====================

    @staticmethod
    def parse_subscribe_or_renew(text: str) -> Optional[Tuple[str, str, bool]]:
        """
        Parse SUBSCRIBE or RENEW command.

        Format: SUBSCRIBE|RENEW <email> <phone>
        Example: SUBSCRIBE john@example.com 0771234567

        Returns:
            Tuple of (email, phone, is_renew) if valid, None otherwise
        """
        text = text.strip()
        upper = text.upper()

        is_renew = upper.startswith('RENEW')
        is_subscribe = upper.startswith('SUBSCRIBE')

        if not (is_subscribe or is_renew):
            return None

        # Extract parts
        parts = text.split()
        if len(parts) < 3:
            return None

        email = parts[1]
        phone = parts[2]

        # Validate email
        if '@' not in email or '.' not in email.split('@')[1]:
            return None

        # Clean and validate phone
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('0') or len(phone) != 10:
            return None

        # Check EcoCash-compatible prefix
        valid_prefixes = ['071', '073', '077', '078']
        if not any(phone.startswith(prefix) for prefix in valid_prefixes):
            return None

        return (email, phone, is_renew)

    @staticmethod
    def parse_cancel(text: str) -> bool:
        """Check if message is CANCEL command"""
        return text.strip().upper() == 'CANCEL'

    @staticmethod
    def parse_status(text: str) -> bool:
        """Check if message is STATUS command"""
        return text.strip().upper() == 'STATUS'

    @staticmethod
    def parse_help(text: str) -> bool:
        """Check if message is HELP command"""
        return text.strip().upper() == 'HELP'

    # ==================== COMMAND HANDLERS ====================

    async def handle_subscribe_or_renew(
        self,
        phone_hash: str,
        email: str,
        phone: str,
        is_renew: bool
    ) -> str:
        """
        Handle SUBSCRIBE or RENEW command.

        Both commands do the same thing: initiate a payment.
        Transitions: free_tier|expired -> pending_payment

        Args:
            phone_hash: User's hashed phone
            email: User email for Paynow
            phone: User phone for EcoCash
            is_renew: True if RENEW, False if SUBSCRIBE

        Returns:
            Response message for user
        """
        command_name = "RENEW" if is_renew else "SUBSCRIBE"

        # Resolve current state
        state = self.state_machine.resolve_state(phone_hash)

        logger.info(
            f"{command_name.lower()}_command_received",
            phone_hash=phone_hash,
            current_state=state.state.value,
            email=email
        )

        # Check if already in pending_payment
        if state.state == UserState.PENDING_PAYMENT:
            order_ref = state.pending_order_reference
            return (
                f"⏳ You already have a payment in progress.\n\n"
                f"Order: {order_ref}\n\n"
                f"📱 Check your phone for EcoCash prompt.\n\n"
                f"⏱️ Expires in {self._minutes_remaining(state)} minutes.\n\n"
                f"Reply STATUS to check payment progress."
            )

        # Check if already active subscriber
        if state.state == UserState.ACTIVE_SUBSCRIBER:
            expiry = state.subscription_end_date.strftime("%Y-%m-%d")
            return (
                f"✅ You already have an active subscription!\n\n"
                f"📅 Expires: {expiry}\n\n"
                f"Your plan will auto-renew unless you send CANCEL.\n\n"
                f"Reply STATUS for details."
            )

        # Initiate payment
        try:
            result = await self.payment_service.initiate_subscription_payment(
                user_phone=phone,
                user_email=email,
                subscription_type="monthly"
            )

            if not result.get("success"):
                error = result.get("error", "Unknown error")
                logger.error(
                    f"{command_name.lower()}_payment_failed",
                    phone_hash=phone_hash,
                    error=error
                )

                return (
                    f"❌ Payment initiation failed:\n{error}\n\n"
                    f"Please check:\n"
                    f"• Phone number: {phone}\n"
                    f"• Email: {email}\n"
                    f"• EcoCash account is active\n\n"
                    f"Try again with:\n"
                    f"{command_name} <email> <phone>"
                )

            # Payment initiated successfully
            order_ref = result["order_reference"]
            tx_id = result["transaction_id"]

            # Transition to pending_payment
            trigger = (
                StateTransitionTrigger.RENEW_COMMAND
                if is_renew
                else StateTransitionTrigger.SUBSCRIBE_COMMAND
            )

            self.state_machine.transition_to_pending_payment(
                phone_hash=phone_hash,
                transaction_id=tx_id,
                order_reference=order_ref,
                trigger=trigger
            )

            instructions = result.get("instructions", "")

            return (
                f"✅ {command_name} initiated!\n\n"
                f"📱 Check your phone ({phone}) for EcoCash prompt\n"
                f"💰 Amount: $2.00 USD\n"
                f"🎯 Plan: Monthly Unlimited\n\n"
                f"{instructions}\n\n"
                f"⏱️ You have 15 minutes to approve.\n\n"
                f"Order: {order_ref}\n\n"
                f"Reply STATUS to check payment progress."
            )

        except Exception as e:
            logger.error(
                f"{command_name.lower()}_command_error",
                phone_hash=phone_hash,
                error=str(e)
            )

            return (
                f"❌ Error processing {command_name}:\n{str(e)}\n\n"
                f"Please try again later or contact support."
            )

    async def handle_cancel(self, phone_hash: str) -> str:
        """
        Handle CANCEL command.

        Cancels auto-renewal (sets auto_renew=false).
        Does NOT revoke access - subscription stays active until expiry.

        Args:
            phone_hash: User's hashed phone

        Returns:
            Response message for user
        """
        # Resolve current state
        state = self.state_machine.resolve_state(phone_hash)

        logger.info(
            "cancel_command_received",
            phone_hash=phone_hash,
            current_state=state.state.value
        )

        # Only active subscribers can cancel
        if state.state != UserState.ACTIVE_SUBSCRIBER:
            if state.state == UserState.EXPIRED:
                return (
                    "❌ Your subscription has already expired.\n\n"
                    "You're currently on free tier (5 diagnostics/week).\n\n"
                    "To re-subscribe:\n"
                    "RENEW <email> <phone>\n\n"
                    "Example:\n"
                    "RENEW john@example.com 0771234567"
                )
            else:
                return (
                    "❌ You don't have an active subscription to cancel.\n\n"
                    "To subscribe:\n"
                    "SUBSCRIBE <email> <phone>\n\n"
                    "Example:\n"
                    "SUBSCRIBE john@example.com 0771234567"
                )

        # Cancel auto-renewal
        result = self.payment_service.cancel_subscription(phone_hash)

        if not result["success"]:
            error = result.get("error", "Unknown error")
            logger.error(
                "cancel_command_failed",
                phone_hash=phone_hash,
                error=error
            )

            return (
                f"❌ Cancellation failed:\n{error}\n\n"
                f"Please try again or contact support."
            )

        expiry = result["expires_at"]

        logger.info(
            "auto_renewal_cancelled",
            phone_hash=phone_hash,
            expires_at=expiry
        )

        return (
            f"✅ Auto-renewal cancelled.\n\n"
            f"📅 You'll keep unlimited access until:\n"
            f"{expiry}\n\n"
            f"After that, you'll return to free tier (5 diagnostics/week).\n\n"
            f"💳 No further charges will be made.\n\n"
            f"To re-subscribe anytime:\n"
            f"SUBSCRIBE <email> <phone>"
        )

    async def handle_status(self, phone_hash: str) -> str:
        """
        Handle STATUS command.

        Shows current state, plan details, and expiry if applicable.

        Args:
            phone_hash: User's hashed phone

        Returns:
            Status message for user
        """
        # Resolve current state
        state = self.state_machine.resolve_state(phone_hash)

        logger.info(
            "status_command_received",
            phone_hash=phone_hash,
            current_state=state.state.value
        )

        if state.state == UserState.ACTIVE_SUBSCRIBER:
            expiry = state.subscription_end_date.strftime("%Y-%m-%d %H:%M UTC")
            auto_renew_text = (
                "✅ Will auto-renew"
                if state.auto_renew
                else "❌ Auto-renew cancelled (send SUBSCRIBE to re-enable)"
            )

            return (
                f"✅ Active Subscription\n\n"
                f"📱 Plan: Monthly Unlimited\n"
                f"🎯 Status: Active\n"
                f"📅 Expires: {expiry}\n"
                f"🔄 Renewal: {auto_renew_text}\n\n"
                f"You have unlimited diagnostics until expiration.\n\n"
                f"To cancel auto-renewal: CANCEL"
            )

        elif state.state == UserState.PENDING_PAYMENT:
            order_ref = state.pending_order_reference
            minutes_left = self._minutes_remaining(state)

            return (
                f"⏳ Payment Pending\n\n"
                f"Order: {order_ref}\n\n"
                f"📱 Check your phone for EcoCash prompt.\n\n"
                f"⏱️ Expires in {minutes_left} minutes.\n\n"
                f"Current access: Free tier\n"
                f"Used: {state.diagnostics_used}/{state.diagnostics_used + state.diagnostics_remaining} this week"
            )

        elif state.state == UserState.EXPIRED:
            return (
                f"⚠️ Subscription Expired\n\n"
                f"You're now on free tier:\n"
                f"✅ Used: {state.diagnostics_used}/5 this week\n"
                f"🎯 Remaining: {state.diagnostics_remaining}\n\n"
                f"To renew unlimited access:\n"
                f"RENEW <email> <phone>\n\n"
                f"Example:\n"
                f"RENEW john@example.com 0771234567\n\n"
                f"💵 Only $2/month"
            )

        elif state.state == UserState.FREE_TIER:
            return (
                f"📊 Free Tier Status\n\n"
                f"✅ Used: {state.diagnostics_used}/5 this week\n"
                f"🎯 Remaining: {state.diagnostics_remaining}\n\n"
                f"Upgrade to unlimited:\n"
                f"SUBSCRIBE <email> <phone>\n\n"
                f"Example:\n"
                f"SUBSCRIBE john@example.com 0771234567\n\n"
                f"💵 Only $2/month"
            )

        else:  # NEW_USER
            return (
                f"👋 Welcome!\n\n"
                f"You have 5 free diagnostics per week.\n\n"
                f"Send an OBD code to get started:\n"
                f"Example: P0420\n\n"
                f"For unlimited diagnostics ($2/month):\n"
                f"SUBSCRIBE <email> <phone>\n\n"
                f"Need help? Send: HELP"
            )

    async def handle_help(self, phone_hash: str) -> str:
        """
        Handle HELP command.

        Shows available commands based on current state.

        Args:
            phone_hash: User's hashed phone

        Returns:
            Help message with available commands
        """
        # Resolve current state to show relevant commands
        state = self.state_machine.resolve_state(phone_hash)

        base_help = (
            "🔧 Vehicle Diagnosis Assistant\n\n"
            "📋 Available Commands:\n\n"
        )

        # Diagnostic commands (always available)
        commands = [
            "🔍 Diagnostics:",
            "  • Send OBD code: P0420",
            "  • Follow-up: explain further",
            "",
            "💳 Payment:",
        ]

        # State-specific commands
        if state.state == UserState.ACTIVE_SUBSCRIBER:
            commands.extend([
                "  • STATUS - Check subscription",
                "  • CANCEL - Stop auto-renewal",
            ])
        elif state.state == UserState.EXPIRED:
            commands.extend([
                "  • RENEW <email> <phone> - Restart plan",
                "  • STATUS - Check usage",
            ])
        elif state.state == UserState.PENDING_PAYMENT:
            commands.extend([
                "  • STATUS - Check payment",
            ])
        else:  # FREE_TIER or NEW_USER
            commands.extend([
                "  • SUBSCRIBE <email> <phone> - Unlimited access",
                "  • STATUS - Check free tier usage",
            ])

        # General commands
        commands.extend([
            "",
            "ℹ️ Info:",
            "  • HELP - Show this message",
            "",
            "📧 Example:",
            "  SUBSCRIBE john@example.com 0771234567",
        ])

        return base_help + "\n".join(commands)

    # ==================== HELPER METHODS ====================

    def _minutes_remaining(self, state) -> int:
        """Calculate minutes remaining for pending payment"""
        if not state.transaction_created_at:
            return 0

        elapsed = datetime.utcnow() - state.transaction_created_at
        remaining = 15 - int(elapsed.total_seconds() / 60)
        return max(0, remaining)
