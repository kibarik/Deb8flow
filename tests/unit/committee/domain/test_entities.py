"""
Unit tests for committee domain entities.
"""

import pytest
from src.committee.domain.entities import CommitteeRun, CommitteeMetadata, CommitteeReport
from src.shared.debate.domain.entities import DebateRoom, Verdict
from src.shared.debate.domain.value_objects import RoomId, RunId, Speaker, RoomStatus


def test_committee_run_tpm_wins():
    """Test CommitteeRun.tpm_wins counts correctly."""
    rooms = [
        DebateRoom(
            room_id=RoomId("TPM_vs_CPO"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.PRO, explanation="TPM wins")
        ),
        DebateRoom(
            room_id=RoomId("TPM_vs_CFO"),
            pro_participant="TPM",
            con_participant="CFO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.CON, explanation="CFO wins")
        )
    ]

    run = CommitteeRun(
        run_id=RunId("test"),
        question="test question",
        prd_path="test.txt",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=2,
        rooms=rooms,
        start_time="2025-01-01T00:00:00Z"
    )
    assert run.tpm_wins == 1
    assert run.opponent_wins == 1


def test_committee_run_validation():
    """Test CommitteeRun validates configuration."""
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        CommitteeRun(
            run_id=RunId("test"),
            question="test",
            prd_path="test.txt",
            model=None,
            language=None,
            max_retries=-1,  # Invalid
            max_concurrency=2,
            rooms=[],
            start_time="2025-01-01T00:00:00Z"
        )

    with pytest.raises(ValueError, match="max_concurrency must be 0-4"):
        CommitteeRun(
            run_id=RunId("test"),
            question="test",
            prd_path="test.txt",
            model=None,
            language=None,
            max_retries=2,
            max_concurrency=5,  # Invalid
            rooms=[],
            start_time="2025-01-01T00:00:00Z"
        )


def test_committee_metadata_from_run():
    """Test CommitteeMetadata.from_run creates correct metadata."""
    rooms = [
        DebateRoom(
            room_id=RoomId("TPM_vs_CPO"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.PRO, explanation="Test")
        )
    ]

    run = CommitteeRun(
        run_id=RunId("test_run"),
        question="Test question",
        prd_path="test.txt",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=2,
        rooms=rooms,
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T01:00:00Z"
    )

    metadata = CommitteeMetadata.from_run(run, [])

    assert metadata.run_id == "test_run"
    assert metadata.prd_path == "test.txt"
    assert metadata.question == "Test question"
    assert metadata.room_statuses == {"tpm_cpo": "success"}
    assert metadata.max_retries == 2
    assert metadata.max_concurrency == 2


def test_committee_metadata_to_json():
    """Test CommitteeMetadata.to_json produces valid JSON."""
    metadata = CommitteeMetadata(
        run_id="test",
        prd_path="test.txt",
        question="test",
        model="default",
        language=None,
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T01:00:00Z",
        room_statuses={},
        max_retries=2,
        max_concurrency=2,
        warning_flags={},
        errors=[]
    )

    json_str = metadata.to_json()
    assert '"run_id": "test"' in json_str
    assert '"question": "test"' in json_str


def test_committee_run_successful_and_failed_rooms():
    """Test CommitteeRun filters rooms correctly."""
    successful_room = DebateRoom(
        room_id=RoomId("TPM_vs_CPO"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=Verdict(winner=Speaker.PRO, explanation="Test")
    )

    failed_room = DebateRoom(
        room_id=RoomId("TPM_vs_CFO"),
        pro_participant="TPM",
        con_participant="CFO",
        status=RoomStatus.FAILED,
        messages=[],
        error="Timeout"
    )

    run = CommitteeRun(
        run_id=RunId("test"),
        question="test",
        prd_path="test.txt",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=2,
        rooms=[successful_room, failed_room],
        start_time="2025-01-01T00:00:00Z"
    )

    assert len(run.successful_rooms) == 1
    assert len(run.failed_rooms) == 1
    assert run.successful_rooms[0].room_id.value == "TPM_vs_CPO"
    assert run.failed_rooms[0].room_id.value == "TPM_vs_CFO"
