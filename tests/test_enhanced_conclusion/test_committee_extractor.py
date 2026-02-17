"""
Unit tests for CommitteeReportExtractor.

Tests verify:
- CommitteeReportExtractor class creation (T046)
- Room section parsing (T047)
- Room outcome extraction (T048)
- Transcript data extraction with turn indices (T049)
- UTF-8 encoding support for Russian/English
- Error handling for missing files
"""

import pytest
from pathlib import Path
import tempfile
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.extractors.committee_report_extractor import (
    CommitteeReportExtractor,
    CommitteeReportData,
    RoomData,
    TranscriptEntry,
)


@pytest.fixture
def sample_final_report():
    """Sample final_report.md content for testing."""
    return """# Product Committee Report

**Run ID:** RUN_20260215_202208_test
**Generated:** 2026-02-15T20:22:08Z

---

## Committee Question

Should we approve the PRD for the new AI-powered feature?

---

## Executive Summary

This report synthesizes debate results from 4 committee rooms.

---

## Room-by-Room Analysis

### TPM_vs_CPO

**Status:** success

**Winner:** TPM

**Judge Explanation:** TPM demonstrated clear product vision and user value.

**Key Takeaways:**
- User value proposition is strong
- Market timing is favorable

**Full Dialogue:**

**PRO** (opening) ✓:
The PRD presents a compelling vision for AI-powered features that address real user needs.

**CON** (rebuttal) ✗:
While the vision is compelling, the implementation timeline seems overly aggressive.

**PRO** (counter) ✓:
The timeline is realistic based on similar past projects.

---

### TPM_vs_CFO

**Status:** success

**Winner:** CFO

**Judge Explanation:** Financial concerns are significant and require additional planning.

**Key Takeaways:**
- Financial model lacks conservative scenarios
- Implementation costs are underestimated

**Full Dialogue:**

**PRO** (opening) ✓:
The financial projections show strong ROI within 18 months.

**CON** (rebuttal) ✗:
The financial model is overly optimistic with no downside analysis.

**PRO** (counter) ✓:
We have conducted sensitivity analysis for various scenarios.

---

### TPM_vs_CTO

**Status:** success

**Winner:** TPM

**Judge Rationale:** Technical approach is sound and feasible.

**Key Takeaways:**
- Architecture is well-designed
- Implementation approach is pragmatic

---

### TPM_vs_BDM

**Status:** failed

**Winner:** Unknown

---

## TPM Reflection

### Learnings

TPM learned that financial modeling needs more detail.

### Recommendations

1. Add detailed financial analysis
2. Provide conservative scenarios
"""


@pytest.fixture
def extractor():
    """Create CommitteeReportExtractor instance."""
    return CommitteeReportExtractor()


class TestCommitteeReportExtractorCreation:
    """Test CommitteeReportExtractor class creation (T046)."""

    def test_extractor_initialization(self, extractor):
        """Test extractor can be initialized."""
        assert extractor is not None
        assert hasattr(extractor, "logger")
        assert hasattr(extractor, "parse")

    def test_parse_method_exists(self, extractor):
        """Test parse method exists and is callable."""
        assert callable(extractor.parse)


class TestRoomSectionParsing:
    """Test room section parsing (T047)."""

    def test_parse_all_rooms(self, extractor, sample_final_report):
        """Test parsing all room sections from report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary report file
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            # Parse report
            report_data = extractor.parse(str(report_path))

            # Verify all rooms were parsed
            assert len(report_data.rooms) == 4

            # Verify room IDs
            room_ids = [room.room_id for room in report_data.rooms]
            assert "TPM_vs_CPO" in room_ids
            assert "TPM_vs_CFO" in room_ids
            assert "TPM_vs_CTO" in room_ids
            assert "TPM_vs_BDM" in room_ids

    def test_parse_room_opponent_roles(self, extractor, sample_final_report):
        """Test extracting opponent roles from room IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify opponent roles
            opponent_roles = {room.room_id: room.opponent_role for room in report_data.rooms}
            assert opponent_roles["TPM_vs_CPO"] == "CPO"
            assert opponent_roles["TPM_vs_CFO"] == "CFO"
            assert opponent_roles["TPM_vs_CTO"] == "CTO"
            assert opponent_roles["TPM_vs_BDM"] == "BDM"

    def test_parse_varying_header_formats(self, extractor):
        """Test handling varying header formats."""
        # Test with different header formats
        report_with_headers = """
## Committee Question

Test question?

---

## Room-by-Room Analysis

### TPM_vs_CPO
**Status:** success
**Winner:** TPM

### TPM_vs_CFO
**Status:** success
**Winner:** CFO
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(report_with_headers, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Should still parse correctly
            assert len(report_data.rooms) == 2


class TestRoomOutcomeExtraction:
    """Test room outcome extraction (T048)."""

    def test_extract_winners(self, extractor, sample_final_report):
        """Test extracting winners from each room."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify winners
            winners = {room.room_id: room.winner for room in report_data.rooms}
            assert winners["TPM_vs_CPO"] == "TPM"
            assert winners["TPM_vs_CFO"] == "CFO"
            assert winners["TPM_vs_CTO"] == "TPM"
            assert winners["TPM_vs_BDM"] == "Unknown"

    def test_extract_room_status(self, extractor, sample_final_report):
        """Test extracting room status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify status
            statuses = {room.room_id: room.status for room in report_data.rooms}
            assert statuses["TPM_vs_CPO"] == "success"
            assert statuses["TPM_vs_CFO"] == "success"
            assert statuses["TPM_vs_BDM"] == "failed"

    def test_extract_judge_rationale(self, extractor, sample_final_report):
        """Test extracting judge rationales."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify rationales
            rationale_cpo = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")
            assert "clear product vision" in rationale_cpo.judge_rationale.lower()

            rationale_cfo = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CFO")
            assert "financial concerns" in rationale_cfo.judge_rationale.lower()

    def test_extract_key_takeaways(self, extractor, sample_final_report):
        """Test extracting key takeaways."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify takeaways
            cpo_room = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")
            assert len(cpo_room.key_takeaways) == 2
            assert "User value proposition" in cpo_room.key_takeaways[0]


class TestTranscriptDataExtraction:
    """Test transcript data extraction with turn indices (T049)."""

    def test_extract_transcript_with_turn_indices(self, extractor, sample_final_report):
        """Test extracting transcript with turn indices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Find room with transcript (CPO room)
            cpo_room = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")

            # Verify transcript entries
            assert len(cpo_room.transcript) == 3

            # Verify first entry
            first_entry = cpo_room.transcript[0]
            assert first_entry.speaker == "PRO"
            assert first_entry.stage == "opening"
            assert first_entry.validated == True
            assert first_entry.turn_index == 0

            # Verify second entry
            second_entry = cpo_room.transcript[1]
            assert second_entry.speaker == "CON"
            assert second_entry.stage == "rebuttal"
            assert second_entry.validated == False
            assert second_entry.turn_index == 1

    def test_transcript_entry_structure(self, extractor, sample_final_report):
        """Test TranscriptEntry data structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            cpo_room = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")
            entry = cpo_room.transcript[0]

            # Verify all attributes
            assert hasattr(entry, "speaker")
            assert hasattr(entry, "stage")
            assert hasattr(entry, "content")
            assert hasattr(entry, "validated")
            assert hasattr(entry, "turn_index")

    def test_handle_missing_transcript(self, extractor):
        """Test handling rooms without transcript data."""
        report_without_transcript = """
## Committee Question

Test question?

---

## Room-by-Room Analysis

### TPM_vs_CPO
**Status:** success
**Winner:** TPM
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(report_without_transcript, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Room should exist but have no transcript
            cpo_room = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")
            assert len(cpo_room.transcript) == 0


class TestMetadataExtraction:
    """Test metadata extraction."""

    def test_extract_run_id(self, extractor, sample_final_report):
        """Test extracting run ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            assert report_data.run_id == "RUN_20260215_202208_test"

    def test_extract_question(self, extractor, sample_final_report):
        """Test extracting committee question."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            assert "Should we approve the PRD" in report_data.question

    def test_extract_timestamp(self, extractor, sample_final_report):
        """Test extracting timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            assert "2026-02-15" in report_data.generated_at

    def test_extract_tpm_reflection(self, extractor, sample_final_report):
        """Test extracting TPM reflection section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(sample_final_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            assert "financial modeling" in report_data.tpm_reflection.lower()


class TestErrorHandling:
    """Test error handling."""

    def test_file_not_found(self, extractor):
        """Test handling of missing file."""
        with pytest.raises(FileNotFoundError, match="Final report not found"):
            extractor.parse("/nonexistent/path/final_report.md")

    def test_missing_committee_question(self, extractor):
        """Test handling of missing Committee Question section."""
        invalid_report = """
# Product Committee Report

**Run ID:** RUN_test

## Room-by-Room Analysis

### TPM_vs_CPO
**Status:** success
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(invalid_report, encoding="utf-8")

            with pytest.raises(ValueError, match="Missing required section: Committee Question"):
                extractor.parse(str(report_path))


class TestUTF8EncodingSupport:
    """Test UTF-8 encoding support."""

    def test_russian_text_support(self, extractor):
        """Test UTF-8 encoding support for Russian text."""
        russian_report = """
# Product Committee Report

**Run ID:** RUN_test
**Generated:** 2026-02-15T20:22:08Z

---

## Committee Question

Следует ли нам одобрить PRD для новой функции на основе ИИ?

---

## Room-by-Room Analysis

### TPM_vs_CPO

**Status:** success

**Winner:** TPM

**Judge Explanation:** Техническое решение обосновано и выполнимо.

**Key Takeaways:**
- Архитектура хорошо спроектирована
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "final_report.md"
            report_path.write_text(russian_report, encoding="utf-8")

            report_data = extractor.parse(str(report_path))

            # Verify Russian text is preserved
            assert "ИИ" in report_data.question
            cpo_room = next(r for r in report_data.rooms if r.room_id == "TPM_vs_CPO")
            assert "Техническое решение" in cpo_room.judge_rationale
            assert "Архитектура" in cpo_room.key_takeaways[0]
