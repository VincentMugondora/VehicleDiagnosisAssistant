import hashlib
import re


def normalize_phone(phone: str) -> str:
    """
    Remove formatting from phone number, keeping only digits and +.

    Args:
        phone: Raw phone number (e.g., "whatsapp:+1 (234) 567-8900")

    Returns:
        Normalized phone number (e.g., "+12345678900")
    """
    # Remove everything except digits and +
    return re.sub(r"[^\d+]", "", phone)


def hash_phone_number(phone: str) -> str:
    """
    SHA-256 hash phone number for privacy compliance.
    Never store raw phone numbers in logs or database.

    Args:
        phone: Raw phone number

    Returns:
        SHA-256 hex digest (64 characters)
    """
    normalized = normalize_phone(phone)
    return hashlib.sha256(normalized.encode()).hexdigest()
