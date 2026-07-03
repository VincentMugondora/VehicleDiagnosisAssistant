"""
Handler for payment-related WhatsApp commands.
"""
import re
from typing import Optional, Tuple
from app.services.payment_service import PaymentService
from app.core.logging import logger


def parse_subscribe_command(raw_text: str) -> Optional[Tuple[str, str]]:
    """
    Parse SUBSCRIBE command from WhatsApp message.

    Format: SUBSCRIBE <email> <phone>
    Example: SUBSCRIBE john@example.com 0771234567

    Returns:
        Tuple of (email, phone) if valid, None otherwise
    """
    # Normalize text
    text = raw_text.strip()

    # Check if it's a subscribe command
    if not text.upper().startswith('SUBSCRIBE'):
        return None

    # Extract parts after SUBSCRIBE
    parts = text.split()

    if len(parts) < 3:
        return None

    email = parts[1]
    phone = parts[2]

    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None

    # Clean phone number
    phone = phone.replace(' ', '').replace('-', '')

    if not phone.startswith('0') or len(phone) != 10:
        return None

    # Check if it's a valid EcoCash-compatible prefix
    valid_prefixes = ['071', '073', '077', '078']
    if not any(phone.startswith(prefix) for prefix in valid_prefixes):
        return None

    return (email, phone)


async def handle_subscribe_command(
    raw_text: str,
    payment_service: PaymentService
) -> str:
    """
    Handle SUBSCRIBE command from user.

    Args:
        raw_text: User's message text
        payment_service: PaymentService instance

    Returns:
        Response message to send back to user
    """
    parsed = parse_subscribe_command(raw_text)

    if not parsed:
        return (
            "❌ Invalid SUBSCRIBE command format.\n\n"
            "Correct format:\n"
            "SUBSCRIBE <email> <phone>\n\n"
            "Example:\n"
            "SUBSCRIBE john@example.com 0771234567\n\n"
            "Make sure:\n"
            "• Email has @ and domain\n"
            "• Phone is 10 digits starting with 0\n"
            "• Phone supports EcoCash (071, 073, 077, 078)"
        )

    email, phone = parsed

    try:
        # Initiate payment
        result = await payment_service.initiate_subscription_payment(
            user_phone=phone,
            user_email=email,
            subscription_type="monthly"
        )

        if result["success"]:
            instructions = result.get("instructions", "")
            order_ref = result["order_reference"]

            return (
                f"✅ Payment initiated!\n\n"
                f"📱 Check your phone for EcoCash prompt\n"
                f"💰 Amount: $2.00 USD\n"
                f"🎯 Plan: Monthly Unlimited\n\n"
                f"{instructions}\n\n"
                f"⏱️ You have 5 minutes to approve the payment.\n\n"
                f"Order: {order_ref}\n\n"
                f"Reply STATUS to check payment progress."
            )
        else:
            error = result.get("error", "Unknown error")
            logger.error("subscription_initiation_failed", error=error)

            return (
                f"❌ Payment initiation failed:\n{error}\n\n"
                f"Please try again or contact support."
            )

    except Exception as e:
        logger.error("subscribe_command_error", error=str(e))

        return (
            f"❌ Error processing subscription:\n{str(e)}\n\n"
            f"Please try again later."
        )


def parse_status_command(raw_text: str) -> bool:
    """Check if message is a STATUS command"""
    return raw_text.strip().upper() == 'STATUS'


async def handle_status_command(
    phone_hash: str,
    payment_service: PaymentService
) -> str:
    """
    Handle STATUS command - show user their subscription/usage status.

    Args:
        phone_hash: User's phone hash
        payment_service: PaymentService instance

    Returns:
        Status message
    """
    try:
        # Check access info
        access_info = payment_service.check_user_access(phone_hash)

        if access_info["reason"] == "subscribed":
            end_date = access_info["subscription_end_date"]

            # Parse datetime string if needed
            if isinstance(end_date, str):
                from datetime import datetime
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            return (
                f"✅ Active Subscription\n\n"
                f"📱 Plan: Monthly Unlimited\n"
                f"🎯 Status: Active\n"
                f"📅 Expires: {end_date.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"You have unlimited diagnostics until expiration."
            )
        elif access_info["reason"] == "within_free_limit":
            used = access_info["diagnostics_used"]
            remaining = access_info["diagnostics_remaining"]

            return (
                f"📊 Free Tier Status\n\n"
                f"✅ Used: {used}/5 this week\n"
                f"🎯 Remaining: {remaining}\n\n"
                f"Upgrade to unlimited:\n"
                f"SUBSCRIBE <email> <phone>\n\n"
                f"Only $2/month!"
            )
        else:
            used = access_info["diagnostics_used"]

            return (
                f"⚠️ Free Tier Limit Reached\n\n"
                f"Used: {used}/5 this week\n\n"
                f"Subscribe for unlimited:\n"
                f"SUBSCRIBE <email> <phone>\n\n"
                f"Example:\n"
                f"SUBSCRIBE john@example.com 0771234567\n\n"
                f"💵 Only $2/month"
            )

    except Exception as e:
        logger.error("status_command_error", error=str(e))

        return (
            f"❌ Error retrieving status:\n{str(e)}\n\n"
            f"Please try again later."
        )


def parse_cancel_command(raw_text: str) -> bool:
    """Check if message is a CANCEL command"""
    return raw_text.strip().upper() == 'CANCEL'


async def handle_cancel_command(
    phone_hash: str,
    payment_service: PaymentService
) -> str:
    """
    Handle CANCEL command - disable auto-renewal.

    Subscription remains active until expiry date.

    Args:
        phone_hash: User's phone hash
        payment_service: PaymentService instance

    Returns:
        Response message
    """
    try:
        # Check if user has active subscription
        access_info = payment_service.check_user_access(phone_hash)

        if not access_info["has_subscription"]:
            return (
                "❌ You don't have an active subscription.\n\n"
                "To subscribe:\n"
                "SUBSCRIBE <email> <phone>\n\n"
                "Example:\n"
                "SUBSCRIBE john@example.com 0771234567"
            )

        # Cancel auto-renewal
        result = payment_service.cancel_subscription(phone_hash)

        if result["success"]:
            expiry = result["expires_at"]

            return (
                f"✅ Auto-renewal cancelled.\n\n"
                f"Your subscription remains active until:\n"
                f"📅 {expiry}\n\n"
                f"After that, you'll return to free tier (5 diagnostics/week).\n\n"
                f"To re-subscribe anytime, send:\n"
                f"SUBSCRIBE <email> <phone>"
            )
        else:
            error = result.get("error", "Unknown error")
            logger.error("cancel_command_failed", error=error)

            return (
                f"❌ Cancellation failed:\n{error}\n\n"
                f"Please try again or contact support."
            )

    except Exception as e:
        logger.error("cancel_command_error", error=str(e))

        return (
            f"❌ Error processing cancellation:\n{str(e)}\n\n"
            f"Please try again later."
        )


def parse_renew_command(raw_text: str) -> Optional[Tuple[str, str]]:
    """
    Parse RENEW command from WhatsApp message.

    Format: RENEW <email> <phone>
    Example: RENEW john@example.com 0771234567

    Returns:
        Tuple of (email, phone) if valid, None otherwise
    """
    # Normalize text
    text = raw_text.strip()

    # Check if it's a renew command
    if not text.upper().startswith('RENEW'):
        return None

    # Extract parts after RENEW
    parts = text.split()

    if len(parts) < 3:
        return None

    email = parts[1]
    phone = parts[2]

    # Basic validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return None

    # Clean phone number
    phone = phone.replace(' ', '').replace('-', '')

    if not phone.startswith('0') or len(phone) != 10:
        return None

    # Check if it's a valid EcoCash-compatible prefix
    valid_prefixes = ['071', '073', '077', '078']
    if not any(phone.startswith(prefix) for prefix in valid_prefixes):
        return None

    return (email, phone)


async def handle_renew_command(
    raw_text: str,
    payment_service: PaymentService
) -> str:
    """
    Handle RENEW command - restart expired subscription.

    Essentially same as SUBSCRIBE but for expired users.

    Args:
        raw_text: User's message text
        payment_service: PaymentService instance

    Returns:
        Response message
    """
    parsed = parse_renew_command(raw_text)

    if not parsed:
        return (
            "❌ Invalid RENEW command format.\n\n"
            "Correct format:\n"
            "RENEW <email> <phone>\n\n"
            "Example:\n"
            "RENEW john@example.com 0771234567\n\n"
            "Make sure:\n"
            "• Email has @ and domain\n"
            "• Phone is 10 digits starting with 0\n"
            "• Phone supports EcoCash (071, 073, 077, 078)"
        )

    email, phone = parsed

    try:
        # Initiate payment (same as SUBSCRIBE)
        result = await payment_service.initiate_subscription_payment(
            user_phone=phone,
            user_email=email,
            subscription_type="monthly"
        )

        if result["success"]:
            instructions = result.get("instructions", "")
            order_ref = result["order_reference"]

            return (
                f"✅ Renewal initiated!\n\n"
                f"📱 Check your phone for EcoCash prompt\n"
                f"💰 Amount: $2.00 USD\n"
                f"🎯 Plan: Monthly Unlimited\n\n"
                f"{instructions}\n\n"
                f"⏱️ You have 5 minutes to approve the payment.\n\n"
                f"Order: {order_ref}\n\n"
                f"Reply STATUS to check payment progress."
            )
        else:
            error = result.get("error", "Unknown error")
            logger.error("renewal_initiation_failed", error=error)

            return (
                f"❌ Renewal initiation failed:\n{error}\n\n"
                f"Please check:\n"
                f"• Phone number is correct ({phone})\n"
                f"• EcoCash account is active\n"
                f"• You have sufficient balance ($2)\n\n"
                f"Try again with RENEW command."
            )

    except Exception as e:
        logger.error("renew_command_error", error=str(e))

        return (
            f"❌ Error processing renewal:\n{str(e)}\n\n"
            f"Please try again later."
        )
