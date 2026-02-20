"""
Unit tests for CLI adapter.
"""
import pytest
from pathlib import Path
from pydantic import ValidationError
from src.rewrite.adapters.cli import RewriteCliInput, parse_arguments


class TestRewriteCliInput:
    """Test suite for RewriteCliInput validation."""

    def test_valid_input(self, tmp_path):
        """Test validation with valid input."""
        source = tmp_path / "test.md"
        source.write_text("# Test")
        conclusion = tmp_path / "conclusion.md"
        conclusion.write_text("## Рекомендации\n\n1. Item")

        input_data = {
            "file_path": source,
            "conclusion_path": conclusion,
            "max_rounds": 10,
            "output_path": None,
            "no_backup": False,
            "verbose": False
        }

        result = RewriteCliInput(**input_data)

        assert result.file_path == source
        assert result.max_rounds == 10

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(ValidationError, match="File not found"):
            RewriteCliInput(
                file_path=Path("/nonexistent.md"),
                conclusion_path=Path("/nonexistent2.md")
            )

    def test_invalid_max_rounds(self, tmp_path):
        """Test error when max_rounds < 0."""
        source = tmp_path / "test.md"
        source.write_text("# Test")
        conclusion = tmp_path / "conclusion.md"
        conclusion.write_text("## Рекомендации\n\n1. Item")

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            RewriteCliInput(
                file_path=source,
                conclusion_path=conclusion,
                max_rounds=-1
            )
