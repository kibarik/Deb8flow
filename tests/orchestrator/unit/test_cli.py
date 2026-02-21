"""Unit tests for CLI argument parsing and validation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.orchestrator.adapters.cli import (
    is_shutdown_requested,
    parse_args,
    signal_handler,
)


@pytest.fixture
def sample_files(tmp_path):
    """Create sample source and corrections files."""
    source = tmp_path / "source.md"
    corrections = tmp_path / "corrections.md"
    source.write_text("# Sample\nContent")
    corrections.write_text("# Corrections\nFix typos")
    return source, corrections


class TestArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_parse_positional_arguments(self, sample_files):
        """Test parsing positional source and corrections arguments."""
        source, corrections = sample_files
        args = parse_args([str(source), str(corrections)])

        assert args["source"] == source
        assert args["corrections"] == corrections

    def test_parse_with_output_option(self, sample_files, tmp_path):
        """Test parsing --output option."""
        source, corrections = sample_files
        output_dir = tmp_path / "output"

        args = parse_args([str(source), str(corrections), "--output", str(output_dir)])

        assert args["output"] == output_dir

    def test_parse_with_config_option(self, sample_files):
        """Test parsing --config option."""
        source, corrections = sample_files
        config = Path("/test/config.yaml")

        args = parse_args([str(source), str(corrections), "--config", str(config)])

        assert args["config"] == config

    def test_parse_with_max_retries(self, sample_files):
        """Test parsing --max-retries option."""
        source, corrections = sample_files

        args = parse_args([str(source), str(corrections), "--max-retries", "5"])

        assert args["max_retries"] == 5

    def test_parse_with_timeout(self, sample_files):
        """Test parsing --timeout option."""
        source, corrections = sample_files

        args = parse_args([str(source), str(corrections), "--timeout", "1800"])

        assert args["timeout"] == 1800

    def test_parse_with_keep_containers_flag(self, sample_files):
        """Test parsing --keep-containers flag."""
        source, corrections = sample_files

        args = parse_args([str(source), str(corrections), "--keep-containers"])

        assert args["keep_containers"] is True

    def test_parse_with_verbose_flag(self, sample_files):
        """Test parsing --verbose flag."""
        source, corrections = sample_files

        args = parse_args([str(source), str(corrections), "--verbose"])

        assert args["verbose"] is True

    def test_parse_with_dry_run_flag(self, sample_files):
        """Test parsing --dry-run flag."""
        source, corrections = sample_files

        args = parse_args([str(source), str(corrections), "--dry-run"])

        assert args["dry_run"] is True


class TestArgumentValidation:
    """Tests for argument validation."""

    def test_validate_source_file_not_found(self):
        """Test that missing source file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            parse_args(["nonexistent.md", "corrections.md"])

    def test_validate_corrections_file_not_found(self, sample_files):
        """Test that missing corrections file raises FileNotFoundError."""
        source, _ = sample_files

        with pytest.raises(FileNotFoundError, match="Corrections file not found"):
            parse_args([str(source), "nonexistent.md"])

    def test_validate_source_not_a_file(self, tmp_path):
        """Test that non-file source path raises ValueError."""
        source = tmp_path  # Directory, not file
        corrections = tmp_path / "corrections.md"
        corrections.write_text("# Corrections")

        with pytest.raises(ValueError, match="not a file"):
            parse_args([str(source), str(corrections)])

    def test_validate_corrections_not_a_file(self, tmp_path):
        """Test that non-file corrections path raises ValueError."""
        source = tmp_path / "source.md"
        source.write_text("# Source")
        corrections = tmp_path  # Directory, not file

        with pytest.raises(ValueError, match="not a file"):
            parse_args([str(source), str(corrections)])

    def test_validate_max_retries_negative(self, sample_files):
        """Test that negative max-retries raises ValueError."""
        source, corrections = sample_files

        with pytest.raises(ValueError, match="max-retries must be >= 0"):
            parse_args([str(source), str(corrections), "--max-retries", "-1"])

    def test_validate_timeout_less_than_one(self, sample_files):
        """Test that timeout < 1 raises ValueError."""
        source, corrections = sample_files

        with pytest.raises(ValueError, match="timeout must be >= 1"):
            parse_args([str(source), str(corrections), "--timeout", "0"])

    def test_validate_creates_output_directory(self, sample_files, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        source, corrections = sample_files
        output = tmp_path / "new_output_dir"

        assert not output.exists()

        args = parse_args([str(source), str(corrections), "--output", str(output)])

        assert output.exists()
        assert output.is_dir()


class TestSignalHandling:
    """Tests for signal handling."""

    def test_signal_handler_sets_shutdown_flag(self):
        """Test that signal handler sets shutdown flag."""
        global _shutdown_requested
        import importlib
        import src.orchestrator.adapters.cli as cli_module

        # Reset flag
        cli_module._shutdown_requested = False

        # Call signal handler
        cli_module.signal_handler(2, None)  # SIGINT

        assert cli_module._shutdown_requested is True

    def test_is_shutdown_requested_returns_flag(self):
        """Test is_shutdown_requested returns current flag state."""
        assert is_shutdown_requested() in (True, False)


class TestProgressReporter:
    """Tests for ProgressReporter class."""

    def test_phase_start_prints_message(self, capsys, sample_files):
        """Test that phase_start prints formatted message."""
        from src.orchestrator.adapters.progress_reporter import ProgressReporter

        reporter = ProgressReporter(verbose=False)
        reporter.phase_start("specify", "/spec-kitty.specify")

        captured = capsys.readouterr()
        assert "[ORCHESTRATOR]" in captured.out
        assert "specify" in captured.out
        assert "Running" in captured.out

    def test_phase_complete_prints_success(self, capsys):
        """Test that phase_complete prints success message."""
        from src.orchestrator.adapters.progress_reporter import ProgressReporter

        reporter = ProgressReporter(verbose=False)
        reporter.phase_complete("specify", attempts=1, validated=True)

        captured = capsys.readouterr()
        assert "[ORCHESTRATOR]" in captured.out
        assert "specify" in captured.out
        assert "Validation passed" in captured.out

    def test_phase_error_prints_error(self, capsys):
        """Test that phase_error prints error message."""
        from src.orchestrator.adapters.progress_reporter import ProgressReporter

        reporter = ProgressReporter(verbose=False)
        reporter.phase_error("specify", "Command failed")

        captured = capsys.readouterr()
        assert "[ORCHESTRATOR]" in captured.out
        assert "specify" in captured.out
        assert "ERROR" in captured.out
        assert "Command failed" in captured.out

    def test_summary_prints_result(self, capsys):
        """Test that summary prints workflow result."""
        from src.orchestrator.adapters.progress_reporter import ProgressReporter
        from src.orchestrator.domain.models import OrchestratorResult, ResultStatus

        result = OrchestratorResult(
            status=ResultStatus.SUCCESS,
            phases_completed=3,
            total_phases=3,
            duration_seconds=123,
        )

        reporter = ProgressReporter(verbose=False)

        with pytest.raises(SystemExit):
            reporter.summary(result)

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out
        assert "3/3" in captured.out
        assert "2m 3s" in captured.out
