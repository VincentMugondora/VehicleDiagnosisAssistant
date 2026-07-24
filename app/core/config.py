from pydantic_settings import BaseSettings, SettingsConfigDict
import socket


def check_supabase_connectivity(url: str) -> bool:
    """Check if Supabase URL is reachable"""
    try:
        hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
        socket.gethostbyname(hostname)
        return True
    except (socket.gaierror, socket.error):
        return False


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str

    # AI Provider (primary provider to use)
    ai_provider: str = "cohere"  # "cohere" or "gemini"

    # Cohere AI (primary provider)
    cohere_api_key: str | None = None
    cohere_model: str = "command-r-plus-08-2024"

    # Gemini AI (automatic fallback when AI_PROVIDER=cohere)
    # If Cohere fails, Gemini will be used automatically
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"

    # WhatsApp (Twilio)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None
    twilio_validate_signature: bool = True
    twilio_send_reply: bool = False

    # WhatsApp (Baileys)
    baileys_api_key: str | None = None
    baileys_outbound_url: str | None = None  # URL to send images back to Baileys

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
    auto_learn_codes: bool = True  # Enable dynamic code learning from web
    supabase_enabled: bool = True  # Disable if Supabase is unreachable

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

    # Paynow payments (client credentials)
    paynow_integration_id: str | None = None
    paynow_integration_key: str | None = None
    paynow_return_url: str = ""
    paynow_result_url: str = ""

    # Payment config
    subscription_price: float = 2.0  # Monthly subscription price in USD
    free_diagnostics_limit: int = 5  # Free diagnostics per week
    free_diagnostics_window_days: int = 7  # Weekly window

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
