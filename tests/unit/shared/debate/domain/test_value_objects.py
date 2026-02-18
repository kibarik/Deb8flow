"""
Unit tests for value objects.

Tests the RoomId, RunId, Speaker, and RoomStatus value objects.
"""

import pytest
from src.shared.debate.domain.value_objects import RoomId, RunId, Speaker, RoomStatus


def test_room_id_valid():
    """Test creating a valid RoomId."""
    room_id = RoomId("TPM_vs_CPO")
    assert room_id.value == "TPM_vs_CPO"


def test_room_id_empty_string_raises_error():
    """Test that empty string raises ValueError."""
    with pytest.raises(ValueError, match="RoomId must be a non-empty string"):
        RoomId("")


def test_room_id_non_string_raises_error():
    """Test that non-string raises ValueError."""
    with pytest.raises(ValueError, match="RoomId must be a non-empty string"):
        RoomId(123)


def test_room_id_is_immutable():
    """Test that RoomId is immutable (frozen)."""
    room_id = RoomId("test")
    with pytest.raises(Exception):  # FrozenInstanceError
        room_id.value = "modified"


def test_run_id_valid():
    """Test creating a valid RunId."""
    run_id = RunId("manual_id")
    assert run_id.value == "manual_id"


def test_run_id_generate_with_question():
    """Test generating RunId from question."""
    run_id = RunId.generate("test question here")
    assert run_id.value.startswith("RUN_")
    assert "test-question-here" in run_id.value


def test_run_id_generate_with_manual_id():
    """Test generating RunId with manual ID override."""
    run_id = RunId.generate("test question", manual_id="custom_id")
    assert run_id.value == "custom_id"


def test_run_id_generate_sanitizes_question():
    """Test that question is properly sanitized."""
    run_id = RunId.generate("What is   the   potential?!")
    # Should remove special chars and extra spaces
    assert "what-is-the-potential" in run_id.value


def test_run_id_is_immutable():
    """Test that RunId is immutable (frozen)."""
    run_id = RunId("test")
    with pytest.raises(Exception):  # FrozenInstanceError
        run_id.value = "modified"


def test_speaker_enum_values():
    """Test Speaker enum has correct values."""
    assert Speaker.PRO.value == "PRO"
    assert Speaker.CON.value == "CON"
    assert Speaker.JUDGE.value == "JUDGE"


def test_room_status_enum_values():
    """Test RoomStatus enum has correct values."""
    assert RoomStatus.PENDING.value == "pending"
    assert RoomStatus.IN_PROGRESS.value == "in_progress"
    assert RoomStatus.SUCCESS.value == "success"
    assert RoomStatus.FAILED.value == "failed"
    assert RoomStatus.SKIPPED.value == "skipped"
