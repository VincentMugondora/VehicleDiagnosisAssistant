class AppError(Exception):
    """Base exception for all application errors"""
    pass


class OBDCodeNotFound(AppError):
    """Raised when an OBD code is not found in the database"""
    pass


class SessionExpired(AppError):
    """Raised when a user session has expired"""
    pass


class GeminiUnavailable(AppError):
    """Raised when Gemini API is unavailable or returns an error"""
    pass


class InvalidVehicleData(AppError):
    """Raised when vehicle data cannot be parsed or is invalid"""
    pass


class MessageAlreadyProcessed(AppError):
    """Raised when attempting to process a duplicate message"""
    pass


class ExternalProviderError(AppError):
    """Raised when an external search provider fails"""
    pass


class ValidationError(AppError):
    """Raised when input validation fails"""
    pass
