"""
Retry utilities for Supabase database operations.

Handles transient network failures with exponential backoff.
"""

import time
import structlog
from typing import TypeVar, Callable
from httpx import ConnectTimeout, ReadTimeout, RemoteProtocolError, ConnectError

logger = structlog.get_logger()

T = TypeVar('T')

# Transient errors that should be retried
RETRYABLE_EXCEPTIONS = (
    ConnectTimeout,
    ReadTimeout,
    RemoteProtocolError,
    ConnectError,
    ConnectionError,
    TimeoutError
)


def with_retry(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_multiplier: float = 2.0,
    operation_name: str = "database_operation"
) -> T:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Function to execute (should be a lambda or callable with no args)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 0.5s)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
        operation_name: Name of operation for logging

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail

    Example:
        result = with_retry(
            lambda: supabase.table('users').select('*').execute(),
            operation_name="fetch_users"
        )
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    "database_operation_retry",
                    operation=operation_name,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                    retry_delay=delay
                )
                time.sleep(delay)
                delay *= backoff_multiplier
            else:
                logger.error(
                    "database_operation_failed_after_retries",
                    operation=operation_name,
                    attempts=max_retries + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )
        except Exception as e:
            # Non-retryable exception - fail immediately
            logger.error(
                "database_operation_non_retryable_error",
                operation=operation_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    # All retries exhausted
    raise last_exception


def with_retry_default_none(
    func: Callable[[], T],
    max_retries: int = 2,
    operation_name: str = "database_operation"
) -> T | None:
    """
    Execute a function with retry logic, returning None on failure.

    Useful for non-critical operations where graceful degradation is acceptable.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts (default: 2, faster fail)
        operation_name: Name of operation for logging

    Returns:
        Result of the function call, or None if all retries fail

    Example:
        count = with_retry_default_none(
            lambda: supabase.table('users').select('*', count='exact').execute().count,
            operation_name="count_users"
        ) or 0
    """
    try:
        return with_retry(func, max_retries=max_retries, operation_name=operation_name)
    except Exception as e:
        logger.warning(
            "database_operation_degraded",
            operation=operation_name,
            error=str(e),
            error_type=type(e).__name__,
            returning="None"
        )
        return None
