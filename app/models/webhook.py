from pydantic import BaseModel, Field


class TwilioWebhookPayload(BaseModel):
    """Twilio WhatsApp webhook payload"""
    From: str = Field(alias="From")
    Body: str = Field(alias="Body")
    MessageSid: str = Field(alias="MessageSid")

    class Config:
        populate_by_name = True


class BaileysWebhookPayload(BaseModel):
    """Baileys WhatsApp webhook payload with fallback fields"""
    from_: str | None = Field(None, alias="from")
    sender: str | None = None
    text: str | None = None
    message: str | None = None
    message_id: str | None = None

    class Config:
        populate_by_name = True

    def get_sender(self) -> str:
        """Get sender with fallback logic"""
        return self.from_ or self.sender or ""

    def get_text(self) -> str:
        """Get message text with fallback logic"""
        return self.text if self.text is not None else (self.message or "")
