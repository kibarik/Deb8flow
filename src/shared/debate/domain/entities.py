"""
Domain entities for the shared debate framework.

This module contains core domain entities with business logic.
All entities use plain dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from .value_objects import RoomId, Speaker, RoomStatus


class DebateMode(str, Enum):
    """Debate execution mode."""

    STANDARD = "standard"  # Multi-turn, separate LLM calls per stage
    SIMPLE = "simple"      # Single LLM call for entire debate

    @classmethod
    def from_string(cls, value: str) -> "DebateMode":
        """Parse string to DebateMode, with validation."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = [m.value for m in cls]
            raise ValueError(
                f"Invalid debate mode: {value}. "
                f"Must be one of: {valid}"
            )

    def is_standard(self) -> bool:
        """Check if this is standard mode."""
        return self == DebateMode.STANDARD

    def is_simple(self) -> bool:
        """Check if this is simple mode."""
        return self == DebateMode.SIMPLE


@dataclass
class DebateMessage:
    """A single message in a debate dialogue."""

    speaker: Speaker
    content: str
    stage: str
    timestamp: str
    validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            "speaker": self.speaker.value,
            "content": self.content,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "validated": self.validated
        }


@dataclass
class Verdict:
    """Judge's decision for a debate room."""

    winner: Speaker
    explanation: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert verdict to dictionary representation."""
        return {
            "winner": self.winner.value,
            "explanation": self.explanation,
            "confidence": self.confidence
        }


@dataclass
class DebateRoom:
    """A single debate room between two participants."""

    room_id: RoomId
    pro_participant: str
    con_participant: str
    status: RoomStatus
    messages: List[DebateMessage]
    verdict: Optional[Verdict] = None
    takeaways: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        """Check if the room completed successfully with a verdict."""
        return self.status == RoomStatus.SUCCESS and self.verdict is not None

    @property
    def dialogue(self) -> List[Dict[str, Any]]:
        """Get the full dialogue as a list of dictionaries."""
        return [msg.to_dict() for msg in self.messages]

    def to_json(self) -> str:
        """Convert room to JSON string."""
        data = {
            "room_id": self.room_id.value,
            "pro_participant": self.pro_participant,
            "con_participant": self.con_participant,
            "status": self.status.value,
            "messages": self.dialogue,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "takeaways": self.takeaways,
            "error": self.error
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
