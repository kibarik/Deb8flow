"""Tests for FinalReportGenerator class."""

import pytest

from src.committee.adapters.reports.final_report import FinalReportGenerator
from src.shared.debate.domain.entities import DebateRoom, DebateMessage, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


@pytest.fixture
def generator():
    """Create a FinalReportGenerator instance."""
    return FinalReportGenerator()


@pytest.fixture
def sample_rooms():
    """Create sample debate rooms for testing."""
    return [
        DebateRoom(
            room_id=RoomId("TPM_vs_CPO"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[
                DebateMessage(
                    speaker=Speaker.PRO,
                    content="TPM opening statement",
                    stage="opening",
                    timestamp="2024-01-01T00:00:00Z",
                    validated=True
                ),
                DebateMessage(
                    speaker=Speaker.CON,
                    content="CPO opening statement",
                    stage="opening",
                    timestamp="2024-01-01T00:01:00Z",
                    validated=True
                ),
            ],
            verdict=Verdict(
                winner=Speaker.PRO,
                explanation="TPM presented compelling technical arguments"
            ),
            takeaways=["Technical feasibility is high", "Team has relevant experience"]
        ),
        DebateRoom(
            room_id=RoomId("TPM_vs_CFO"),
            pro_participant="TPM",
            con_participant="CFO",
            status=RoomStatus.FAILED,
            messages=[],
            error="Timeout waiting for LLM response"
        )
    ]


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T10:30:00Z",
        "model": "gpt-4",
        "max_retries": 2,
        "roles_dir": "prompts/roles/"
    }


class TestFinalReportGenerator:
    """Test suite for FinalReportGenerator."""

    def test_generate_final_report_basic_structure(self, generator, sample_rooms, sample_metadata):
        """Should generate report with all required sections."""
        report = generator.generate_final_report(
            run_id="RUN_20240101_test",
            prd_path="./test_prd.txt",
            question="What is the potential of this project?",
            rooms=sample_rooms,
            metadata=sample_metadata
        )

        assert "# Product Committee Report" in report
        assert "## Committee Question" in report
        assert "## Executive Summary" in report
        assert "## Room-by-Room Analysis" in report
        assert "## TPM Reflection" in report
        assert "## Metadata" in report

    def test_generate_final_report_includes_room_details(self, generator, sample_rooms, sample_metadata):
        """Should include detailed information for each room."""
        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test_prd.txt",
            question="Test question?",
            rooms=sample_rooms,
            metadata=sample_metadata
        )

        # Successful room details
        assert "### TPM_vs_CPO" in report
        assert "**Winner:** PRO" in report
        assert "Technical feasibility is high" in report
        assert "TPM opening statement" in report

        # Failed room details
        assert "### TPM_vs_CFO" in report
        assert "**Error:**" in report
        assert "Timeout waiting for LLM response" in report

    def test_generate_final_report_shows_statistics(self, generator, sample_rooms, sample_metadata):
        """Should show summary statistics in executive summary."""
        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test_prd.txt",
            question="Test?",
            rooms=sample_rooms,
            metadata=sample_metadata
        )

        assert "Successful rooms:** 1" in report
        assert "Failed rooms:** 1" in report
        assert "Skipped rooms:** 0" in report

    def test_generate_final_report_includes_metadata_footer(self, generator, sample_rooms, sample_metadata):
        """Should include run metadata in footer."""
        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test_prd.txt",
            question="Test?",
            rooms=sample_rooms,
            metadata=sample_metadata
        )

        assert "**PRD:** ./test_prd.txt" in report
        assert "**Model:** gpt-4" in report
        assert "**Max retries:** 2" in report
        assert "**Start time:** 2024-01-01T10:00:00Z" in report

    def test_generate_final_report_handles_empty_rooms(self, generator, sample_metadata):
        """Should handle empty rooms list gracefully."""
        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test.txt",
            question="Test?",
            rooms=[],
            metadata=sample_metadata
        )

        assert "Successful rooms:** 0" in report
        assert "Failed rooms:** 0" in report

    def test_generate_final_report_truncates_long_dialogue(self, generator, sample_metadata):
        """Should show only first 10 messages in dialogue excerpt."""
        # Create room with many messages
        messages = [
            DebateMessage(
                speaker=Speaker.PRO if i % 2 == 0 else Speaker.CON,
                content=f"Message {i}",
                stage="rebuttal",
                timestamp=f"2024-01-01T00:{i:02d}:00Z",
                validated=True
            )
            for i in range(20)
        ]

        room = DebateRoom(
            room_id=RoomId("TPM_vs_CTO"),
            pro_participant="TPM",
            con_participant="CTO",
            status=RoomStatus.SUCCESS,
            messages=messages,
            verdict=Verdict(winner=Speaker.PRO, explanation="Test"),
            takeaways=[]
        )

        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test.txt",
            question="Test?",
            rooms=[room],
            metadata=sample_metadata
        )

        # Should mention "and 10 more messages"
        assert "and 10 more messages" in report

    def test_generate_intermediate_report(self, generator):
        """Should generate progress report during execution."""
        completed_rooms = [
            DebateRoom(
                room_id=RoomId("TPM_vs_CPO"),
                pro_participant="TPM",
                con_participant="CPO",
                status=RoomStatus.SUCCESS,
                messages=[],
                verdict=Verdict(winner=Speaker.PRO, explanation=""),
                takeaways=[]
            ),
            DebateRoom(
                room_id=RoomId("TPM_vs_CFO"),
                pro_participant="TPM",
                con_participant="CFO",
                status=RoomStatus.FAILED,
                messages=[],
                error="Test error"
            )
        ]

        report = generator.generate_intermediate_report(
            run_id="RUN_test",
            completed_rooms=completed_rooms,
            total_rooms=4
        )

        assert "# Committee Progress Report" in report
        assert "Progress:** 2/4" in report
        assert "Successful:** 1" in report
        assert "Failed:** 1" in report
        assert "In progress:** 2" in report

    def test_generate_intermediate_report_lists_rooms(self, generator):
        """Should list all completed rooms with status icons."""
        rooms = [
            DebateRoom(
                room_id=RoomId("TPM_vs_CPO"),
                pro_participant="TPM",
                con_participant="CPO",
                status=RoomStatus.SUCCESS,
                messages=[],
                verdict=Verdict(winner=Speaker.PRO, explanation=""),
                takeaways=[]
            )
        ]

        report = generator.generate_intermediate_report(
            run_id="RUN_test",
            completed_rooms=rooms,
            total_rooms=1
        )

        assert "✓" in report  # Checkmark for success
        assert "TPM_vs_CPO" in report

    def test_room_section_with_no_takeaways(self, generator, sample_metadata):
        """Should handle successful room with no takeaways."""
        room = DebateRoom(
            room_id=RoomId("TPM_vs_CPO"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.PRO, explanation=""),
            takeaways=[]  # No takeaways
        )

        report = generator.generate_final_report(
            run_id="RUN_test",
            prd_path="./test.txt",
            question="Test?",
            rooms=[room],
            metadata=sample_metadata
        )

        assert "No takeaways extracted" in report
