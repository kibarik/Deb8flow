"""
Retry logic with exponential backoff.

This module provides retry functionality for operations that may fail transiently.
"""

import asyncio
import logging
import errno
import sys
from typing import TypeVar, Callable, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimitError(Exception):
    """Rate limit error (429) that should be retried."""
    pass


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception is retryable (transient) or permanent.

    Permanent errors that should NOT be retried:
    - 401 Authentication errors (retries won't fix bad credentials)
    - Disk space errors (ENOSPC)
    - Permission errors (EACCES, EPERM)
    - File not found errors (ENOENT)
    - TimeoutError (preserve partial progress instead of restarting)

    Transient errors that CAN be retried:
    - 429 Rate limit errors
    - RateLimitError (custom exception)
    - 503 Service unavailable
    - Connection errors
    - 5xx server errors (except timeouts)

    Args:
        exception: The exception to check

    Returns:
        True if the error is transient and should be retried
    """
    # Check for RateLimitError - always retryable
    if isinstance(exception, RateLimitError):
        return True

    # Check for TimeoutError - NOT retryable (preserve progress)
    if isinstance(exception, (TimeoutError, asyncio.TimeoutError)):
        logger.error("TimeoutError - will NOT retry (preserving partial progress)")
        return False

    # Check for timeout in error message - also NOT retryable
    error_str = str(exception).lower()
    if "timed out" in error_str and "debate room" in error_str:
        # This is our debate timeout, not a network timeout
        logger.error("Debate timeout - will NOT retry (preserving partial progress)")
        return False

    # Check for authentication errors (401)
    if "401" in error_str or "authentication" in error_str or "unauthorized" in error_str:
        logger.error("Authentication error (401) - will NOT retry")
        return False

    # Check for specific OpenAI authentication error
    if hasattr(exception, 'status') and exception.status == 401:
        logger.error("Authentication error (401) - will NOT retry")
        return False

    # Check for disk space errors (errno 28 - ENOSPC)
    if isinstance(exception, OSError):
        if exception.errno == errno.ENOSPC:  # No space left on device
            logger.error("Disk space error (ENOSPC) - will NOT retry")
            return False
        if exception.errno in (errno.EACCES, errno.EPERM):
            logger.error("Permission error - will NOT retry")
            return False
        if exception.errno == errno.ENOENT:
            logger.error("File not found error - will NOT retry")
            return False
    if "no space left on device" in error_str:
        logger.error("Disk space error - will NOT retry")
        return False

    # Check for rate limit errors (429) - these ARE retryable
    if "429" in error_str or "rate limit" in error_str or "resource exhausted" in error_str:
        return True

    # Check for server errors (5xx) - these ARE retryable
    if any(code in error_str for code in ["500", "502", "503", "504"]):
        return True

    # Check for connection errors - these ARE retryable
    if "connection" in error_str or "network" in error_str:
        return True

    # Default: don't retry unknown errors
    logger.warning(f"Unknown error type: {type(exception).__name__} - will NOT retry")
    return False


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int,
    *args,
    is_retryable_check: Optional[Callable[[Exception], bool]] = None,
    **kwargs
) -> T:
    """
    Execute function with exponential backoff retry.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        *args: Positional arguments for func
        is_retryable_check: Optional function to check if error is retryable.
                           If not provided, uses default is_retryable_error().
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution

    Raises:
        Last exception if all retries fail or error is not retryable
    """
    last_exception = None
    retry_check = is_retryable_check or is_retryable_error

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Simple console output for 429 rate limit errors
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str or "resource exhausted" in error_str:
                print(f"⚠️ Rate limit hit, retrying...", file=sys.stderr, flush=True)

            # Check if this error is retryable
            if not retry_check(e):
                logger.error(f"Non-retryable error on attempt {attempt + 1}: {e}")
                raise

            # Only retry if we have attempts left
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries + 1} attempts: {e}")

    raise last_exception or Exception("Retry failed")
