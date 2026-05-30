from datetime import datetime
from pydantic import BaseModel
from app.models.diagnostic import VehicleContext


class ConversationTurn(BaseModel):
    """Single turn in a conversation"""
    request: str
    response: str
    timestamp: datetime


class SessionState(BaseModel):
    """Conversation session state for multi-turn interactions"""
    phone_hash: str
    persona: str = "unknown"  # "customer" | "provider" | "unknown"
    current_step: str = "awaiting_input"
    vehicle: VehicleContext | None = None
    pending_obd_codes: list[str] = []
    turns: list[ConversationTurn] = []
    last_active: datetime
