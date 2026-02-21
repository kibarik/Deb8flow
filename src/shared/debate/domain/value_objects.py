"""
Value objects for the shared debate framework.

This module contains immutable value objects used throughout the debate system.
All value objects use frozen dataclasses to ensure immutability.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import re
from datetime import datetime, timezone


@dataclass(frozen=True)
class RoomId:
    """Immutable identifier for a debate room."""

    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("RoomId must be a non-empty string")


@dataclass(frozen=True)
class RunId:
    """Immutable identifier for a committee run."""

    value: str

    @classmethod
    def generate(cls, question: str, manual_id: Optional[str] = None) -> "RunId":
        """
        Generate a RunId from a question.

        Args:
            question: The committee question
            manual_id: Optional manual run ID (overrides generation)

        Returns:
            A new RunId instance
        """
        if manual_id:
            return cls(manual_id)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return cls(timestamp)


class Speaker(Enum):
    """Participant roles in a debate."""

    PRO = "PRO"
    CON = "CON"
    JUDGE = "JUDGE"


class RoomStatus(Enum):
    """Execution status of a debate room."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"  # Debate timed out but partial results are available
