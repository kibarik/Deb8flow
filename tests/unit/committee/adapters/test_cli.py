"""Tests for CommitteeCliInput and related CLI validation functions."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from src.committee.adapters.cli import (
    CommitteeCliInput,
    parse_arguments_to_input,
    sanitize_run_id
)


class TestCommitteeCliInput:
    """Test suite for CommitteeCliInput Pydantic model."""

    def test_valid_minimal_input(self, tmp_path):
        """Should accept valid minimal input with required fields only."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD content")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM prompt")

        input_data = {
            "prd_path": str(prd_file),
            "question": "What is the potential?"
        }

        result = CommitteeCliInput(**input_data)
        assert result.prd_path == prd_file
        assert result.question == "What is the potential?"
        assert result.max_retries == 2  # Default value

    def test_valid_full_input(self, tmp_path):
        """Should accept valid input with all optional fields."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD content")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM prompt")

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test question?",
            "model": "gpt-4",
            "max_retries": 3,
            "max_concurrency": 0,
            "output_dir": "./custom_output",
            "roles_dir": str(roles_dir),
            "run_id": "custom_run",
            "language": "русский",
            "verbose": True,
            "quiet": False
        }

        result = CommitteeCliInput(**input_data)
        assert result.model == "gpt-4"
        assert result.max_retries == 3
        assert result.max_concurrency == 0
        assert result.language == "русский"
        assert result.verbose is True

    def test_validate_prd_path_exists(self, tmp_path):
        """Should reject if PRD file doesn't exist."""
        prd_file = tmp_path / "nonexistent.txt"
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM prompt")

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?"
        }

        with pytest.raises(ValidationError, match="PRD file not found"):
            CommitteeCliInput(**input_data)

    def test_validate_prd_path_is_file(self, tmp_path):
        """Should reject if PRD path is a directory."""
        prd_dir = tmp_path / "prd"
        prd_dir.mkdir()
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM prompt")

        input_data = {
            "prd_path": str(prd_dir),
            "question": "Test?"
        }

        with pytest.raises(ValidationError, match="not a file"):
            CommitteeCliInput(**input_data)

    def test_validate_roles_dir_exists(self, tmp_path):
        """Should reject if roles directory doesn't exist."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?",
            "roles_dir": "/nonexistent/roles"
        }

        with pytest.raises(ValidationError, match="Roles directory not found"):
            CommitteeCliInput(**input_data)

    def test_validate_tpm_prompt_required(self, tmp_path):
        """Should require TPM prompt file in roles directory."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        # No tpm.txt created

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?",
            "roles_dir": str(roles_dir)
        }

        with pytest.raises(ValidationError, match="TPM prompt file not found"):
            CommitteeCliInput(**input_data)

    def test_validate_question_not_empty(self, tmp_path):
        """Should reject empty question."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        with pytest.raises(ValidationError):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": ""
            })

        with pytest.raises(ValidationError, match="cannot be empty"):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": "   "
            })

    def test_validate_max_retries_positive(self, tmp_path):
        """Should reject negative max_retries."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        with pytest.raises(ValidationError):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": "Test?",
                "max_retries": -1
            })

    def test_validate_max_concurrency_range(self, tmp_path):
        """Should reject max_concurrency outside valid range."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        with pytest.raises(ValidationError):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": "Test?",
                "max_concurrency": -1
            })

        with pytest.raises(ValidationError):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": "Test?",
                "max_concurrency": 5
            })

    def test_validate_mutually_exclusive_verbose_quiet(self, tmp_path):
        """Should reject both verbose and quiet being True."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")
        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        with pytest.raises(ValidationError, match="mutually exclusive"):
            CommitteeCliInput(**{
                "prd_path": str(prd_file),
                "question": "Test?",
                "verbose": True,
                "quiet": True
            })

    def test_get_available_roles(self, tmp_path):
        """Should return list of available roles based on prompt files."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")
        (roles_dir / "cpo.txt").write_text("CPO")
        (roles_dir / "cto.txt").write_text("CTO")
        # CFO and BDM missing

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?",
            "roles_dir": str(roles_dir)
        }

        cli_input = CommitteeCliInput(**input_data)
        available = cli_input.get_available_roles()

        assert "tpm" in available
        assert "cpo" in available
        assert "cto" in available
        assert "cfo" not in available
        assert "bdm" not in available

    def test_get_role_prompt_path(self, tmp_path):
        """Should return correct path for role prompt file."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?",
            "roles_dir": str(roles_dir)
        }

        cli_input = CommitteeCliInput(**input_data)
        path = cli_input.get_role_prompt_path("tpm")

        assert path == roles_dir / "tpm.txt"

    def test_get_role_prompt_path_missing(self, tmp_path):
        """Should raise error for missing role prompt."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        input_data = {
            "prd_path": str(prd_file),
            "question": "Test?",
            "roles_dir": str(roles_dir)
        }

        cli_input = CommitteeCliInput(**input_data)

        with pytest.raises(ValueError, match="Role prompt file not found"):
            cli_input.get_role_prompt_path("cfo")


class TestParseArgumentsToInput:
    """Test suite for parse_arguments_to_input function."""

    def test_parse_valid_arguments(self, tmp_path):
        """Should parse valid arguments dict to CommitteeCliInput."""
        prd_file = tmp_path / "test.txt"
        prd_file.write_text("Test PRD")

        roles_dir = tmp_path / "roles"
        roles_dir.mkdir()
        (roles_dir / "tpm.txt").write_text("TPM")

        args = {
            "prd_path": str(prd_file),
            "question": "Test question?",
            "max_retries": 3,
            "verbose": True
        }

        result = parse_arguments_to_input(args)

        assert isinstance(result, CommitteeCliInput)
        assert result.max_retries == 3
        assert result.verbose is True

    def test_parse_invalid_arguments_raises_error(self, tmp_path):
        """Should raise error for invalid arguments."""
        args = {
            "prd_path": "/nonexistent/prd.txt",
            "question": "Test?"
        }

        with pytest.raises(ValueError):
            parse_arguments_to_input(args)


class TestSanitizeRunId:
    """Test suite for sanitize_run_id function."""

    def test_sanitize_manual_run_id(self):
        """Should sanitize manual run ID by removing invalid chars."""
        result = sanitize_run_id("Test?", manual_id="my-run_ID.123!")
        assert result == "my-run_ID123"

    def test_sanitize_manual_run_id_empty_after_sanitize(self):
        """Should raise error if manual ID becomes empty after sanitization."""
        with pytest.raises(ValueError, match="no valid characters"):
            sanitize_run_id("Test?", manual_id="!!!...$$$")

    def test_generate_run_id_from_question(self):
        """Should generate run ID from question when manual ID not provided."""
        result = sanitize_run_id("What is the potential of this amazing project?")

        assert result.startswith("RUN_")
        # Slug is truncated to ~50 chars, so check for prefix
        assert "what-is-the-potential-of" in result.lower()
        # Should have timestamp
        assert "_" in result

    def test_generate_run_id_limits_slug_length(self):
        """Should limit slug length to 50 characters."""
        long_question = "What is the potential " + "x" * 100 + " project?"
        result = sanitize_run_id(long_question)

        # Should truncate long slug
        assert len(result) < 100  # RUN_<timestamp>_<truncated_slug>

    def test_generate_run_id_removes_special_chars(self):
        """Should remove special characters from slug."""
        result = sanitize_run_id("Is GitHub useful for developers? @#$%")

        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result
        assert "github-useful-for-developers" in result.lower()
