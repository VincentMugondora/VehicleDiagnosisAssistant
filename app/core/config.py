from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str

    # AI Provider
    ai_provider: str = "cohere"  # "cohere" or "gemini"

    # Cohere AI
    cohere_api_key: str | None = None
    cohere_model: str = "command-r"

    # Gemini AI (legacy, optional)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    # WhatsApp (Twilio)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None
    twilio_validate_signature: bool = True
    twilio_send_reply: bool = False

    # WhatsApp (Baileys)
    baileys_api_key: str | None = None

    # App behavior
    app_env: str = "development"
    log_level: str = "INFO"
    session_ttl_seconds: int = 1800
    max_conversation_turns: int = 10

    # Reply formatting
    reply_max_causes: int = 5
    reply_max_checks: int = 5
    reply_max_codes: int = 3

    # Feature flags
    ai_enrich_enabled: bool = False
    internet_fallback_enabled: bool = True

    # Usage limits
    usage_limit_per_number: int = 20
    usage_limit_window_days: int = 30
    allowed_numbers: str = ""

    # External search
    search_provider: str = "brave"
    brave_api_key: str | None = None
    serpapi_key: str | None = None
    trusted_sites: str = "obd-codes.com,autocodes.com,obdii.com"
    external_cache_ttl_seconds: int = 2592000  # 30 days
    external_enrich_always: bool = True
    external_save_per_vehicle: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
