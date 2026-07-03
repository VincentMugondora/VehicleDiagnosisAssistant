"""
Payment-related Pydantic models for Paynow integration.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class PaymentInitRequest(BaseModel):
    """Request to initiate a payment"""
    user_phone: str = Field(..., description="Zimbabwe phone number (e.g., '0771234567')")
    user_email: str = Field(..., description="User email (required by Paynow)")
    subscription_type: str = Field(default="monthly", description="Subscription type")

    @field_validator('user_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate Zimbabwe phone format"""
        # Remove spaces and dashes
        cleaned = v.replace(' ', '').replace('-', '')

        # Check basic format (starts with 0, 10 digits)
        if not cleaned.startswith('0') or len(cleaned) != 10:
            raise ValueError(
                "Phone must be Zimbabwe format: 10 digits starting with 0 "
                "(e.g., '0771234567')"
            )

        # Check if it's a valid mobile prefix
        valid_prefixes = ['071', '073', '077', '078']  # EcoCash-compatible prefixes
        if not any(cleaned.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"Phone must start with valid mobile prefix: {', '.join(valid_prefixes)}"
            )

        return cleaned

    @field_validator('user_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError("Invalid email format")
        return v.lower()


class PaymentInitResponse(BaseModel):
    """Response from payment initiation"""
    success: bool
    order_reference: str
    poll_url: Optional[str] = None
    instructions: Optional[str] = None
    error: Optional[str] = None
    transaction_id: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response from payment status check"""
    status: str  # 'pending', 'paid', 'failed', 'cancelled', 'expired'
    amount: Optional[Decimal] = None
    order_reference: str
    paynow_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None


class Transaction(BaseModel):
    """Transaction record (matches database schema)"""
    id: str
    phone_hash: str
    amount: Decimal
    currency: str
    description: str
    status: str
    order_reference: str
    paynow_reference: Optional[str] = None
    poll_url: Optional[str] = None
    user_email: str
    user_phone: str
    subscription_type: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    related_diagnosis_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Subscription(BaseModel):
    """Subscription record (matches database schema)"""
    id: str
    phone_hash: str
    subscription_type: str
    amount: Decimal
    currency: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    transaction_id: Optional[str] = None
    auto_renew: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUsage(BaseModel):
    """User usage tracking (matches database schema)"""
    id: str
    phone_hash: str
    diagnostics_count: int
    period_start: datetime
    period_end: datetime
    was_subscribed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UsageCheckResponse(BaseModel):
    """Response for checking if user can access diagnostic"""
    can_access: bool
    reason: str  # 'subscribed', 'within_free_limit', 'limit_exceeded'
    diagnostics_used: int
    diagnostics_remaining: int
    subscription_end_date: Optional[datetime] = None
