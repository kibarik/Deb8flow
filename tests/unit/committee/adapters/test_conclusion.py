"""Tests for ConclusionGenerator class."""

import pytest

from src.committee.adapters.reports.conclusion import ConclusionGenerator
from src.shared.debate.domain.entities import DebateRoom, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


@pytest.fixture
def generator():
    """Create a ConclusionGenerator instance."""
    return ConclusionGenerator()


class TestConclusionGenerator:
    """Test suite for ConclusionGenerator."""

    def test_generate_conclusion_tpm_wins_majority(self, generator):
        """Should show TPM prevails when winning majority of rooms."""
        rooms = [
            self._create_successful_room("TPM_vs_CPO", Speaker.PRO),
            self._create_successful_room("TPM_vs_CFO", Speaker.PRO),
            self._create_successful_room("TPM_vs_CTO", Speaker.CON),
            self._create_successful_room("TPM_vs_BDM", Speaker.PRO)
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="What is the potential?",
            rooms=rooms,
            metadata=metadata
        )

        assert "TPM victories:** 3/4" in conclusion
        assert "Opponent victories:** 1/4" in conclusion
        assert "TPM (PRO) position prevails" in conclusion

    def test_generate_conclusion_opponents_win_majority(self, generator):
        """Should show opponents prevail when winning majority."""
        rooms = [
            self._create_successful_room("TPM_vs_CPO", Speaker.CON),
            self._create_successful_room("TPM_vs_CFO", Speaker.CON),
            self._create_successful_room("TPM_vs_CTO", Speaker.PRO),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test question?",
            rooms=rooms,
            metadata=metadata
        )

        assert "Opponents (CON) positions prevail" in conclusion

    def test_generate_conclusion_tie(self, generator):
        """Should show no clear consensus on tie."""
        rooms = [
            self._create_successful_room("TPM_vs_CPO", Speaker.PRO),
            self._create_successful_room("TPM_vs_CFO", Speaker.CON),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "No clear consensus" in conclusion

    def test_generate_conclusion_all_rooms_failed(self, generator):
        """Should generate error analysis when all rooms fail."""
        rooms = [
            self._create_failed_room("TPM_vs_CPO", "Timeout error"),
            self._create_failed_room("TPM_vs_CFO", "LLM API error"),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "All debate rooms failed to complete" in conclusion
        assert "## Error Analysis" in conclusion
        assert "## Next Steps" in conclusion

    def test_error_categorization_timeout(self, generator):
        """Should categorize timeout errors correctly."""
        rooms = [
            self._create_failed_room("TPM_vs_CPO", "Debate timed out after 300s"),
            self._create_failed_room("TPM_vs_CFO", "Timeout waiting for response"),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "### Timeout" in conclusion
        assert "Affected rooms: TPM_vs_CPO, TPM_vs_CFO" in conclusion
        assert "Consider increasing timeout" in conclusion

    def test_error_categorization_regex(self, generator):
        """Should categorize regex errors correctly."""
        rooms = [
            self._create_failed_room("TPM_vs_CPO", "re.error: bad escape in pattern"),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "### Regex/Pattern Error" in conclusion
        assert "Check regular expressions" in conclusion

    def test_error_categorization_json(self, generator):
        """Should categorize JSON parsing errors correctly."""
        rooms = [
            self._create_failed_room("TPM_vs_CPO", "JSON decode error: Expecting value"),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "### JSON Parsing Error" in conclusion
        assert "LLM responses are not valid JSON" in conclusion

    def test_error_categorization_llm_api(self, generator):
        """Should categorize LLM/API errors correctly."""
        rooms = [
            self._create_failed_room("TPM_vs_CPO", "OpenAI API error: rate limit exceeded"),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "### LLM/API Error" in conclusion
        assert "Check API key is valid" in conclusion

    def test_conclusion_includes_room_summaries(self, generator):
        """Should include one-sentence summaries for each room."""
        explanation = "TPM demonstrated exceptional technical depth with well-researched market analysis."
        rooms = [
            self._create_successful_room(
                "TPM_vs_CPO",
                Speaker.PRO,
                explanation=explanation
            ),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        assert "## Room Results Summary" in conclusion
        assert "### TPM_vs_CPO" in conclusion
        assert "**Summary:**" in conclusion
        # Should truncate long explanation
        assert "TPM demonstrated exceptional technical depth" in conclusion

    def test_conclusion_handles_mixed_results(self, generator):
        """Should handle mix of successful and failed rooms."""
        rooms = [
            self._create_successful_room("TPM_vs_CPO", Speaker.PRO),
            self._create_failed_room("TPM_vs_CFO", "Timeout"),
            self._create_successful_room("TPM_vs_CTO", Speaker.CON),
        ]

        metadata = {"end_time": "2024-01-01T12:00:00Z"}
        conclusion = generator.generate_conclusion(
            question="Test?",
            rooms=rooms,
            metadata=metadata
        )

        # Should show successful rooms in summary
        assert "After 2 successful debate rooms" in conclusion
        assert "### TPM_vs_CPO" in conclusion
        assert "### TPM_vs_CTO" in conclusion
        # Failed rooms shouldn't appear in Room Results Summary
        assert "TPM_vs_CFO" not in conclusion.split("## Room Results Summary")[1].split("##")[0]

    def test_extract_first_sentence_truncates_long_text(self, generator):
        """Should truncate long sentences to max length."""
        long_text = "A" * 300 + ". " + "B" * 100
        result = generator._extract_first_sentence(long_text, max_length=200)

        assert len(result) <= 203  # 200 + "..."
        assert "..." in result

    def test_extract_first_sentence_handles_empty_text(self, generator):
        """Should handle empty text gracefully."""
        result = generator._extract_first_sentence("")
        assert result == "No explanation provided"

    def test_extract_first_sentence_handles_no_period(self, generator):
        """Should handle text without sentence terminators."""
        result = generator._extract_first_sentence("This is a single sentence")
        assert result == "This is a single sentence"

    def _create_successful_room(self, room_id: str, winner: Speaker, explanation: str = "Good argument") -> DebateRoom:
        """Helper to create a successful debate room."""
        return DebateRoom(
            room_id=RoomId(room_id),
            pro_participant="TPM",
            con_participant=room_id.split("_vs_")[-1],
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=winner, explanation=explanation),
            takeaways=["Point 1", "Point 2"]
        )

    def _create_failed_room(self, room_id: str, error: str) -> DebateRoom:
        """Helper to create a failed debate room."""
        return DebateRoom(
            room_id=RoomId(room_id),
            pro_participant="TPM",
            con_participant=room_id.split("_vs_")[-1],
            status=RoomStatus.FAILED,
            messages=[],
            error=error
        )
