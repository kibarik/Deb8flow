"""
Retry logic with exponential backoff.

This module provides retry functionality for operations that may fail transiently.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int,
    *args,
    **kwargs
) -> T:
    """
    Execute function with exponential backoff retry.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries + 1} attempts")

    raise last_exception or Exception("Retry failed")
