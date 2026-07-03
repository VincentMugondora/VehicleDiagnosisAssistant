"""
FastAPI routes for payment handling.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.models.payment import (
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentStatusResponse,
    UsageCheckResponse
)
from app.services.payment_service import PaymentService
from app.services.user_state_machine import UserStateMachine
from app.repositories.payment_repository import PaymentRepository
from app.db.client import get_supabase_client
from app.utils.phone import hash_phone_number
from app.core.logging import logger

router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service() -> PaymentService:
    """Dependency: Get payment service instance"""
    client = get_supabase_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    payment_repo = PaymentRepository(client)
    return PaymentService(payment_repo)


@router.post("/initiate", response_model=PaymentInitResponse)
async def initiate_payment(
    payment_request: PaymentInitRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Initiate a subscription payment via EcoCash.

    This will:
    1. Create a pending transaction record
    2. Call Paynow API to initiate mobile payment
    3. Return instructions for user to complete payment on their phone
    """
    logger.info(
        "payment_initiation_requested",
        phone=payment_request.user_phone,
        subscription_type=payment_request.subscription_type
    )

    result = await payment_service.initiate_subscription_payment(
        user_phone=payment_request.user_phone,
        user_email=payment_request.user_email,
        subscription_type=payment_request.subscription_type
    )

    if result["success"]:
        return PaymentInitResponse(**result)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Payment initiation failed")
        )


@router.get("/status/{order_reference}", response_model=PaymentStatusResponse)
async def check_payment_status(
    order_reference: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Check payment status by order reference.

    Polls Paynow API and returns current payment status.
    """
    result = await payment_service.check_payment_status(order_reference)

    if result.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return PaymentStatusResponse(
        status=result["status"],
        amount=result.get("amount"),
        order_reference=result["order_reference"],
        paynow_reference=result.get("paynow_reference"),
        paid_at=result.get("paid_at"),
        subscription_end_date=result.get("subscription_end_date")
    )


@router.get("/access-check/{phone}", response_model=UsageCheckResponse)
async def check_user_access(
    phone: str,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Check if a user can access diagnostic service.

    Returns:
    - can_access: True if user has subscription or is within free limit
    - reason: 'subscribed', 'within_free_limit', or 'limit_exceeded'
    - diagnostics_used: Number of diagnostics used this week
    - diagnostics_remaining: Number remaining (or -1 for unlimited)
    - subscription_end_date: When subscription expires (if subscribed)
    """
    phone_hash = hash_phone_number(f"whatsapp:{phone}")

    access_info = payment_service.check_user_access(phone_hash)

    return UsageCheckResponse(**access_info)


@router.post("/webhook/paynow")
async def paynow_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Paynow result URL webhook.

    Paynow posts payment status updates to this endpoint.
    This provides definitive payment confirmation (polling is for real-time updates).

    Uses state machine for idempotent transition to ACTIVE_SUBSCRIBER.
    """
    try:
        # Get POST form data
        form_data = await request.form()
        data = dict(form_data)

        logger.info(
            "paynow_webhook_received",
            reference=data.get("reference"),
            status=data.get("status")
        )

        # Process webhook using Paynow SDK validation
        if payment_service.paynow:
            status_response = payment_service.paynow.process_status_update(data)

            if status_response.paid:
                # Payment confirmed via webhook
                order_reference = status_response.reference if hasattr(status_response, 'reference') else data.get("reference")

                if order_reference:
                    # Get transaction and phone_hash
                    client = get_supabase_client()
                    payment_repo = PaymentRepository(client)
                    state_machine = UserStateMachine(payment_repo)

                    transaction = payment_repo.get_transaction_by_order_reference(order_reference)

                    if transaction:
                        phone_hash = transaction["phone_hash"]
                        transaction_id = transaction["id"]

                        # Use state machine for idempotent transition
                        success, new_state, reason = state_machine.transition_to_active_subscriber(
                            phone_hash=phone_hash,
                            transaction_id=transaction_id,
                            order_reference=order_reference
                        )

                        if success:
                            logger.info(
                                "paynow_webhook_payment_confirmed",
                                reference=order_reference,
                                phone_hash=phone_hash,
                                new_state=new_state.state.value,
                                expires_at=new_state.subscription_end_date.isoformat() if new_state.subscription_end_date else None
                            )
                        else:
                            logger.info(
                                "paynow_webhook_already_processed",
                                reference=order_reference,
                                reason=reason
                            )
                    else:
                        logger.warning(
                            "paynow_webhook_transaction_not_found",
                            reference=order_reference
                        )

        return {"status": "ok"}

    except Exception as e:
        logger.error(
            "paynow_webhook_error",
            error=str(e)
        )

        # Return 200 anyway to prevent Paynow retries
        return {"status": "error", "message": str(e)}


@router.get("/test")
async def test_payments():
    """Test endpoint to verify payments API is working"""
    return {
        "status": "ok",
        "message": "Payments API is running",
        "paynow_configured": bool(get_payment_service().paynow)
    }
