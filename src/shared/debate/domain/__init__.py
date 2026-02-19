"""
Domain layer - pure business logic with no external dependencies.

This module contains the core domain entities, value objects, and services
for the shared debate framework. All code in this layer uses only Python
standard library - no external dependencies.
"""

from .value_objects import RoomId, RunId, Speaker, RoomStatus
from .entities import DebateMessage, Verdict, DebateRoom, DebateMode
from .services import validate_room_configuration, categorize_error

__all__ = [
    "RoomId", "RunId", "Speaker", "RoomStatus",
    "DebateMessage", "Verdict", "DebateRoom", "DebateMode",
    "validate_room_configuration", "categorize_error"
]
