"""Unit tests for file operations."""

import tempfile
from pathlib import Path

import pytest

from src.orchestrator.domain.models import OrchestratorConfig, OverwriteOutputMode
from src.orchestrator.infrastructure.filesystem import FileOperations


@pytest.fixture
def config():
    """Create test configuration."""
    return OrchestratorConfig(
        output_suffix=".corrected.",
        timestamp_output=False,
        overwrite_output=OverwriteOutputMode.ERROR,
    )


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files."""
    source = tmp_path / "source.md"
    corrections = tmp_path / "corrections.md"
    source.write_text("# Source\nContent with special chars: éàü")
    corrections.write_text("# Corrections\nFix items")
    return source, corrections


class TestFileReading:
    """Tests for file reading with encoding detection."""

    def test_read_source_file(self, config, temp_files):
        """Test reading source file."""
        source, _ = temp_files
        ops = FileOperations(config)

        content = ops.read_source(source)

        assert "# Source" in content
        assert "éàü" in content

    def test_read_corrections_file(self, config, temp_files):
        """Test reading corrections file."""
        _, corrections = temp_files
        ops = FileOperations(config)

        content = ops.read_corrections(corrections)

        assert "# Corrections" in content

    def test_read_nonexistent_file_raises_error(self, config, tmp_path):
        """Test that reading nonexistent file raises FileNotFoundError."""
        ops = FileOperations(config)

        with pytest.raises(FileNotFoundError, match="not found"):
            ops.read_source(tmp_path / "nonexistent.md")

    def test_read_with_encoding_fallback(self, config, tmp_path):
        """Test encoding fallback for non-UTF8 files."""
        # Create a file with latin-1 encoding
        test_file = tmp_path / "latin1.txt"
        with open(test_file, "w", encoding="latin-1") as f:
            f.write("Special chars: éàüç")

        ops = FileOperations(config)
        content = ops.read_source(test_file)

        assert "Special chars" in content


class TestOutputPathGeneration:
    """Tests for output path generation."""

    def test_generate_output_path_with_suffix(self, config, temp_files):
        """Test output path generation with suffix."""
        source, _ = temp_files
        ops = FileOperations(config)

        output_path = ops.generate_output_path(source)

        assert "corrected" in output_path.name
        assert output_path.suffix == ".md"

    def test_generate_output_path_with_timestamp(self, tmp_path):
        """Test output path generation with timestamp."""
        config = OrchestratorConfig(
            timestamp_output=True,
        )
        source = tmp_path / "source.md"
        source.write_text("# Test")

        ops = FileOperations(config)
        output_path = ops.generate_output_path(source)

        # Timestamp format: YYYYMMDD-HHMMSS
        import re
        assert re.search(r"\.\d{8}-\d{6}\.", output_path.name)

    def test_generate_output_path_preserves_extension(self, config, temp_files):
        """Test that output path preserves file extension."""
        source, _ = temp_files
        ops = FileOperations(config)

        output_path = ops.generate_output_path(source)

        assert output_path.suffix == source.suffix


class TestOutputWriting:
    """Tests for output file writing."""

    def test_write_output_creates_new_file(self, config, temp_files):
        """Test writing output creates new file."""
        source, _ = temp_files
        ops = FileOperations(config)

        output_path = ops.write_output(source, "# Corrected content")

        assert output_path.exists()
        assert output_path.read_text() == "# Corrected content"

    def test_write_output_preserves_original(self, config, temp_files):
        """Test that writing output doesn't modify original."""
        source, _ = temp_files
        original_content = source.read_text()
        ops = FileOperations(config)

        ops.write_output(source, "# Modified content")

        assert source.read_text() == original_content

    def test_write_output_atomic(self, config, temp_files):
        """Test that output writing is atomic (via temp file)."""
        source, _ = temp_files
        ops = FileOperations(config)

        # Write should create final file, not leave temp
        output_path = ops.write_output(source, "# Atomic write")

        assert output_path.exists()
        assert not output_path.with_suffix(".tmp").exists()

    def test_write_output_error_on_exists(self, config, temp_files):
        """Test that writing to existing path raises error in ERROR mode."""
        source, _ = temp_files
        ops = FileOperations(config)

        # Create first output
        ops.write_output(source, "# First write")

        # Second write should fail
        with pytest.raises(FileExistsError, match="already exists"):
            ops.write_output(source, "# Second write")

    def test_write_output_overwrite_mode(self, temp_files):
        """Test OVERWRITE mode overwrites existing file."""
        config = OrchestratorConfig(
            overwrite_output=OverwriteOutputMode.OVERWRITE,
        )
        source, _ = temp_files
        ops = FileOperations(config)

        # Create first output
        first_path = ops.write_output(source, "# First write")

        # Second write should succeed
        second_path = ops.write_output(source, "# Second write")

        assert first_path == second_path
        assert second_path.read_text() == "# Second write"

    def test_write_output_timestamp_mode(self, temp_files):
        """Test TIMESTAMP mode creates unique file."""
        config = OrchestratorConfig(
            overwrite_output=OverwriteOutputMode.TIMESTAMP,
        )
        source, _ = temp_files
        ops = FileOperations(config)

        # Create first output
        first_path = ops.write_output(source, "# First write")

        # Second write should create new file with timestamp
        second_path = ops.write_output(source, "# Second write")

        assert first_path != second_path
        assert first_path.exists()
        assert second_path.exists()


class TestFileValidation:
    """Tests for file validation."""

    def test_validate_source_readable(self, config, temp_files):
        """Test validation of readable source file."""
        source, _ = temp_files
        ops = FileOperations(config)

        # Should not raise
        ops.validate_source_readable(source)

    def test_validate_source_not_found(self, config, tmp_path):
        """Test validation fails for nonexistent source."""
        ops = FileOperations(config)
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError, match="not found"):
            ops.validate_source_readable(nonexistent)

    def test_validate_corrections_readable(self, config, temp_files):
        """Test validation of readable corrections file."""
        _, corrections = temp_files
        ops = FileOperations(config)

        # Should not raise
        ops.validate_corrections_readable(corrections)

    def test_validate_not_a_file(self, config, tmp_path):
        """Test validation fails for directory."""
        ops = FileOperations(config)

        with pytest.raises(ValueError, match="not a file"):
            ops.validate_source_readable(tmp_path)
