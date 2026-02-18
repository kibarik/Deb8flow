"""
Unit tests for domain entities.

Tests the DebateMessage, Verdict, and DebateRoom entities.
"""

import pytest
from src.shared.debate.domain.entities import DebateMessage, Verdict, DebateRoom
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


def test_debate_message_to_dict():
    """Test converting DebateMessage to dictionary."""
    message = DebateMessage(
        speaker=Speaker.PRO,
        content="Test argument",
        stage="opening",
        timestamp="2025-01-01T12:00:00Z",
        validated=True
    )

    result = message.to_dict()
    assert result["speaker"] == "PRO"
    assert result["content"] == "Test argument"
    assert result["stage"] == "opening"
    assert result["timestamp"] == "2025-01-01T12:00:00Z"
    assert result["validated"] is True


def test_verdict_to_dict():
    """Test converting Verdict to dictionary."""
    verdict = Verdict(
        winner=Speaker.PRO,
        explanation="PRO presented stronger arguments",
        confidence=0.9
    )

    result = verdict.to_dict()
    assert result["winner"] == "PRO"
    assert result["explanation"] == "PRO presented stronger arguments"
    assert result["confidence"] == 0.9


def test_verdict_default_confidence():
    """Test Verdict has default confidence of 1.0."""
    verdict = Verdict(
        winner=Speaker.CON,
        explanation="Test"
    )
    assert verdict.confidence == 1.0


def test_debate_room_is_successful_true():
    """Test DebateRoom.is_successful returns True when successful."""
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=Verdict(winner=Speaker.PRO, explanation="Test")
    )
    assert room.is_successful is True


def test_debate_room_is_successful_false_no_verdict():
    """Test DebateRoom.is_successful returns False when no verdict."""
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=None
    )
    assert room.is_successful is False


def test_debate_room_is_successful_false_not_success():
    """Test DebateRoom.is_successful returns False when not success."""
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.FAILED,
        messages=[],
        verdict=None
    )
    assert room.is_successful is False


def test_debate_room_dialogue_property():
    """Test DebateRoom.dialogue returns list of message dicts."""
    messages = [
        DebateMessage(Speaker.PRO, "Argument 1", "opening", "2025-01-01T12:00:00Z"),
        DebateMessage(Speaker.CON, "Counter 1", "rebuttal", "2025-01-01T12:01:00Z")
    ]

    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=messages,
        verdict=Verdict(winner=Speaker.PRO, explanation="Test")
    )

    dialogue = room.dialogue
    assert len(dialogue) == 2
    assert dialogue[0]["speaker"] == "PRO"
    assert dialogue[1]["speaker"] == "CON"


def test_debate_room_to_json():
    """Test converting DebateRoom to JSON string."""
    room = DebateRoom(
        room_id=RoomId("TPM_vs_CPO"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=Verdict(winner=Speaker.PRO, explanation="Test"),
        takeaways=["Point 1", "Point 2"]
    )

    json_str = room.to_json()
    assert "TPM_vs_CPO" in json_str
    assert "TPM" in json_str
    assert "CPO" in json_str
    assert "success" in json_str
    assert "Point 1" in json_str


def test_debate_room_default_takeaways_empty_list():
    """Test DebateRoom has default empty takeaways list."""
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.PENDING,
        messages=[]
    )
    assert room.takeaways == []


def test_debate_room_with_error():
    """Test DebateRoom can store error information."""
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.FAILED,
        messages=[],
        error="Connection timeout"
    )
    assert room.error == "Connection timeout"
