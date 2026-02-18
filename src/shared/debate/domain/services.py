"""
Domain services for the shared debate framework.

This module contains domain validation rules and business logic services.
"""

from typing import List
from .entities import DebateRoom
from .value_objects import RoomStatus


def validate_room_configuration(
    pro_participant: str,
    con_participant: str,
    max_retries: int,
    max_concurrency: int
) -> None:
    """
    Validate debate room configuration.

    Args:
        pro_participant: PRO participant name
        con_participant: CON participant name
        max_retries: Maximum retry attempts
        max_concurrency: Maximum concurrent rooms (0-4)

    Raises:
        ValueError: If configuration is invalid
    """
    if not pro_participant or not isinstance(pro_participant, str):
        raise ValueError("pro_participant must be a non-empty string")
    if not con_participant or not isinstance(con_participant, str):
        raise ValueError("con_participant must be a non-empty string")
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if not (0 <= max_concurrency <= 4):
        raise ValueError("max_concurrency must be 0-4")


def categorize_error(error_message: str) -> str:
    """
    Categorize error type for reporting.

    Args:
        error_message: The error message to categorize

    Returns:
        A human-readable error category
    """
    error_lower = error_message.lower()
    if "regex" in error_lower or "re.error" in error_lower:
        return "Regex/Pattern Error"
    elif "timeout" in error_lower or "timed out" in error_lower:
        return "Timeout"
    elif "json" in error_lower or "parse" in error_lower:
        return "JSON Parsing Error"
    elif "llm" in error_lower or "api" in error_lower:
        return "LLM/API Error"
    else:
        return "Other Error"
