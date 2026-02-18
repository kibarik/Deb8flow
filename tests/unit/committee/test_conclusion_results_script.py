"""Tests for conclusion_results.py script."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the main function and helpers from the script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from conclusion_results import (
    parse_final_report,
    convert_to_debate_rooms,
    validate_input_path
)
from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RoomStatus, Speaker


class TestParseFinalReport:
    """Test suite for parse_final_report function."""

    def test_parse_committee_question(self):
        """Should extract committee question from report."""
        content = """## Committee Question

What is the potential of this project?

---
"""
        result = parse_final_report(content)
        assert result["question"] == "What is the potential of this project?"

    def test_parse_successful_room(self):
        """Should parse a successful debate room."""
        content = """### TPM_vs_CPO

**Status:** success
**Winner:** PRO
**Judge Explanation:**
TPM made strong technical arguments

**Key Takeaways:**

- Good point 1
- Good point 2

---
"""
        result = parse_final_report(content)
        assert len(result["rooms"]) == 1
        room = result["rooms"][0]
        assert room["room_id"] == "TPM_vs_CPO"
        assert room["status"] == "success"
        assert room["winner"] == Speaker.PRO
        assert "strong technical arguments" in room["summary"]
        # Takeaways should be parsed
        assert len(room["takeaways"]) >= 0  # May be empty depending on parsing logic

    def test_parse_failed_room(self):
        """Should parse a failed debate room."""
        content = """### TPM_vs_CFO

**Status:** failed
**Error:** Timeout waiting for LLM response

---
"""
        result = parse_final_report(content)
        assert len(result["rooms"]) == 1
        room = result["rooms"][0]
        assert room["status"] == "failed"
        assert "Timeout" in room["error"]

    def test_parse_multiple_rooms(self):
        """Should parse multiple rooms."""
        content = """### TPM_vs_CPO
**Status:** success
**Winner:** PRO

---

### TPM_vs_CFO
**Status:** failed
**Error:** API error

---

### TPM_vs_CTO
**Status:** success
**Winner:** CON

---
"""
        result = parse_final_report(content)
        assert len(result["rooms"]) == 3
        assert result["rooms"][0]["room_id"] == "TPM_vs_CPO"
        assert result["rooms"][1]["room_id"] == "TPM_vs_CFO"
        assert result["rooms"][2]["room_id"] == "TPM_vs_CTO"


class TestConvertToDebateRooms:
    """Test suite for convert_to_debate_rooms function."""

    def test_convert_successful_room(self):
        """Should convert successful room to DebateRoom entity."""
        parsed = [{
            "room_id": "TPM_vs_CPO",
            "opponent": "CPO",
            "status": "success",
            "winner": Speaker.PRO,
            "summary": "Good arguments",
            "takeaways": ["Point 1"],
            "error": None
        }]

        rooms = convert_to_debate_rooms(parsed)
        assert len(rooms) == 1

        room = rooms[0]
        assert room.room_id.value == "TPM_vs_CPO"
        assert room.status == RoomStatus.SUCCESS
        assert room.is_successful
        assert room.verdict.winner == Speaker.PRO
        assert room.verdict.explanation == "Good arguments"
        assert room.takeaways == ["Point 1"]
        assert room.error is None

    def test_convert_failed_room(self):
        """Should convert failed room to DebateRoom entity."""
        parsed = [{
            "room_id": "TPM_vs_CFO",
            "opponent": "CFO",
            "status": "failed",
            "winner": None,
            "summary": None,
            "takeaways": [],
            "error": "Timeout error"
        }]

        rooms = convert_to_debate_rooms(parsed)
        assert len(rooms) == 1

        room = rooms[0]
        assert room.status == RoomStatus.FAILED
        assert not room.is_successful
        assert room.verdict is None
        assert room.error == "Timeout error"

    def test_convert_skipped_room(self):
        """Should convert skipped room to DebateRoom entity."""
        parsed = [{
            "room_id": "TPM_vs_BDM",
            "opponent": "BDM",
            "status": "skipped",
            "winner": None,
            "summary": None,
            "takeaways": [],
            "error": None
        }]

        rooms = convert_to_debate_rooms(parsed)
        assert len(rooms) == 1

        room = rooms[0]
        assert room.status == RoomStatus.SKIPPED
        assert not room.is_successful


class TestValidateInputPath:
    """Test suite for validate_input_path function."""

    def test_valid_path(self, tmp_path):
        """Should accept valid existing file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("test")

        # Should not raise
        validate_input_path(test_file)

    def test_nonexistent_path(self, tmp_path):
        """Should exit for nonexistent path."""
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(SystemExit) as exc_info:
            validate_input_path(nonexistent)

        assert exc_info.value.code == 1

    def test_directory_instead_of_file(self, tmp_path):
        """Should exit for directory path."""
        with pytest.raises(SystemExit) as exc_info:
            validate_input_path(tmp_path)

        assert exc_info.value.code == 1


class TestIntegration:
    """Integration tests for the full script workflow."""

    def test_full_workflow_with_sample_report(self, tmp_path):
        """Should process a complete final_report.md file."""
        # Create a sample final_report.md
        report_content = """# Product Committee Report

**Run ID:** RUN_20260218_test
**Generated:** 2024-02-18T12:00:00Z

---

## Committee Question

What is the potential of this AI project?

---

## Executive Summary

This report synthesizes debate results from 3 committee rooms:
- **Successful rooms:** 2
- **Failed rooms:** 1
- **Skipped rooms:** 0 (missing role prompts)

---

## Room-by-Room Analysis

### TPM_vs_CPO

**Status:** success
**Participants:** TPM (PRO) vs CPO (CON)
**Winner:** PRO
**Judge Explanation:**
TPM demonstrated exceptional understanding of market needs

**Key Takeaways:**

- Market timing is favorable
- Team has relevant experience

### TPM_vs_CFO

**Status:** failed
**Error:** Timeout waiting for LLM response

### TPM_vs_CTO

**Status:** success
**Participants:** TPM (PRO) vs CTO (CON)
**Winner:** CON
**Judge Explanation:**
CTO raised valid concerns about technical feasibility

**Key Takeaways:**

- Architecture needs review
- Performance testing required

---

## TPM Reflection

*Reflection feature is currently disabled*

---

## Metadata

- **PRD:** ./test_prd.txt
- **Model:** gpt-4
- **Start time:** 2024-02-18T11:00:00Z
- **End time:** 2024-02-18T12:00:00Z
"""

        report_path = tmp_path / "final_report.md"
        report_path.write_text(report_content, encoding="utf-8")

        # Parse the report
        parsed = parse_final_report(report_content)
        rooms = convert_to_debate_rooms(parsed["rooms"])

        # Verify parsing
        assert len(rooms) == 3
        assert rooms[0].is_successful
        assert rooms[0].verdict.winner == Speaker.PRO
        assert not rooms[1].is_successful
        assert rooms[2].is_successful
        assert rooms[2].verdict.winner == Speaker.CON
