"""
Unit tests for file storage operations.
"""
import pytest
from pathlib import Path
from src.rewrite.infrastructure.storage import RewriteStorage
from src.rewrite.domain.value_objects import RewriteConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return RewriteConfig(backup_suffix=".backup")


@pytest.fixture
def storage(config):
    """Create storage instance."""
    return RewriteStorage(config)


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample file for testing."""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Test\n\nOriginal content")
    return file_path


class TestRewriteStorage:
    """Test suite for RewriteStorage."""

    def test_create_backup(self, storage, sample_file):
        """Test basic backup creation."""
        backup_path = storage.create_backup(sample_file)

        assert backup_path.exists()
        assert backup_path.name == "test.backup.md"
        assert backup_path.read_text() == sample_file.read_text()
        assert storage.backup_created is True

    def test_backup_path_format(self, storage, sample_file):
        """Test backup path format with suffix."""
        backup_path = storage._get_backup_path(sample_file)

        assert backup_path.name == "test.backup.md"
        assert ".backup" in backup_path.name

    def test_backup_file_exists(self, storage, sample_file):
        """Test backup_exists detection."""
        storage.create_backup(sample_file)

        assert storage.backup_exists(sample_file)

    def test_backup_already_exists_error(self, storage, sample_file):
        """Test error when backup already exists."""
        storage.create_backup(sample_file)

        with pytest.raises(FileExistsError, match="already exists"):
            storage.create_backup(sample_file)

    def test_source_file_not_found(self, storage, tmp_path):
        """Test error when source file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            storage.create_backup(nonexistent)

    def test_atomic_write(self, storage, tmp_path):
        """Test atomic write operation."""
        target_path = tmp_path / "output.md"
        content = "# New Content\n\nTest content"

        storage.atomic_write(target_path, content)

        assert target_path.exists()
        assert target_path.read_text() == content

    def test_atomic_write_overwrites(self, storage, tmp_path):
        """Test atomic write overwrites existing file."""
        target_path = tmp_path / "output.md"
        target_path.write_text("Old content")

        storage.atomic_write(target_path, "New content")

        assert target_path.read_text() == "New content"

    def test_restore_from_backup(self, storage, sample_file):
        """Test restoring from backup."""
        backup_path = storage.create_backup(sample_file)

        # Modify original
        sample_file.write_text("Modified content")

        # Restore
        storage.restore_from_backup(sample_file)

        assert sample_file.read_text() == "# Test\n\nOriginal content"

    def test_restore_no_backup(self, storage, sample_file):
        """Test error when backup doesn't exist."""
        with pytest.raises(FileNotFoundError):
            storage.restore_from_backup(sample_file)

    def test_remove_backup(self, storage, sample_file):
        """Test removing backup file."""
        storage.create_backup(sample_file)
        storage.remove_backup(sample_file)

        assert not storage.backup_exists(sample_file)
