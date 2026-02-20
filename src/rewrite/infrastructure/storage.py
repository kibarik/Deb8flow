"""
File storage operations for rewrite feature.

Provides safe file operations with backup and rollback support.
"""
import shutil
import logging
from pathlib import Path
from typing import Optional
import tempfile
import os
import datetime

from ..domain.value_objects import RewriteConfig


logger = logging.getLogger(__name__)


class RewriteStorage:
    """
    Handles file storage operations for rewrite feature.

    Provides safe file operations with automatic backup and
    atomic write capabilities.
    """

    def __init__(self, config: RewriteConfig):
        """
        Initialize storage with configuration.

        Args:
            config: Rewrite configuration containing backup settings
        """
        self.config = config
        self.backup_created = False

    def create_backup(self, source_path: Path) -> Path:
        """
        Create a backup of the source file.

        Args:
            source_path: Path to source file

        Returns:
            Path to backup file

        Raises:
            FileNotFoundError: If source file doesn't exist
            FileExistsError: If backup file already exists
            IOError: If backup creation fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        backup_path = self._get_backup_path(source_path)

        if backup_path.exists():
            raise FileExistsError(
                f"Backup file already exists: {backup_path}\n"
                f"Please remove the existing backup or specify --no-backup to skip"
            )

        try:
            shutil.copy2(source_path, backup_path)
            self.backup_created = True
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            raise IOError(f"Failed to create backup: {e}")

    def _get_backup_path(self, source_path: Path) -> Path:
        """Get the backup file path for a source file."""
        # Add suffix before extension
        stem = source_path.stem
        suffix = source_path.suffix
        backup_suffix = self.config.backup_suffix

        # For files with multiple extensions (e.g., .tar.gz), handle correctly
        if suffix:
            backup_path = source_path.with_name(f"{stem}{backup_suffix}{suffix}")
        else:
            backup_path = source_path.with_name(f"{stem}{backup_suffix}")

        return backup_path

    def backup_exists(self, source_path: Path) -> bool:
        """Check if a backup file already exists."""
        backup_path = self._get_backup_path(source_path)
        return backup_path.exists()

    def prompt_backup_overwrite(self, source_path: Path) -> bool:
        """
        Prompt user to confirm backup overwrite.

        Args:
            source_path: Path to source file

        Returns:
            True if user confirms overwrite, False otherwise
        """
        backup_path = self._get_backup_path(source_path)

        print(f"\n⚠️  Backup file already exists: {backup_path}")
        print(f"Created: {self._get_backup_mtime(backup_path)}")
        print(f"Size: {backup_path.stat().st_size} bytes")

        response = input("Overwrite existing backup? [y/N]: ").strip().lower()
        return response in ['y', 'yes']

    def _get_backup_mtime(self, backup_path: Path) -> str:
        """Get backup modification time as string."""
        mtime = backup_path.stat().st_mtime
        return datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

    def atomic_write(self, target_path: Path, content: str, source_encoding: str = "utf-8") -> None:
        """
        Write content to file atomically.

        Writes to a temporary file first, then renames to target.
        This prevents corruption if write is interrupted.

        Args:
            target_path: Final file path to write to
            content: Content to write
            source_encoding: Text encoding (default: utf-8)

        Raises:
            IOError: If write operation fails
        """
        # Get directory for temp file
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory (ensures same filesystem)
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding=source_encoding,
            dir=target_dir,
            prefix=f".{target_path.name}.",
            delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

            try:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk

                # Atomic rename (overwrites target if exists)
                temp_path.replace(target_path)

                logger.info(f"Atomic write complete: {target_path}")

            except Exception as e:
                # Clean up temp file on failure
                try:
                    temp_path.unlink()
                except:
                    pass
                raise IOError(f"Atomic write failed: {e}")

    def atomic_write_bytes(self, target_path: Path, content: bytes) -> None:
        """
        Write binary content to file atomically.

        Args:
            target_path: Final file path to write to
            content: Binary content to write

        Raises:
            IOError: If write operation fails
        """
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode='wb',
            dir=target_dir,
            prefix=f".{target_path.name}.",
            delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

            try:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

                temp_path.replace(target_path)

                logger.info(f"Atomic write complete: {target_path}")

            except Exception as e:
                try:
                    temp_path.unlink()
                except:
                    pass
                raise IOError(f"Atomic write failed: {e}")

    def safe_backup(self, source_path: Path, skip_backup: bool = False) -> Optional[Path]:
        """
        Create backup with conflict handling.

        Args:
            source_path: Path to source file
            skip_backup: If True, skip backup creation

        Returns:
            Backup path if created, None if skipped

        Raises:
            FileExistsError: If backup exists and user declines overwrite
        """
        if skip_backup:
            logger.info("Backup creation skipped (--no-backup flag)")
            return None

        if self.backup_exists(source_path):
            if not self.prompt_backup_overwrite(source_path):
                raise FileExistsError(
                    f"Backup exists and overwrite declined: {self._get_backup_path(source_path)}\n"
                    f"Remove existing backup or use --no-backup to skip"
                )

        return self.create_backup(source_path)

    def restore_from_backup(self, source_path: Path) -> None:
        """
        Restore source file from backup.

        Args:
            source_path: Path to source file (backup path derived from this)

        Raises:
            FileNotFoundError: If backup doesn't exist
            IOError: If restore operation fails
        """
        backup_path = self._get_backup_path(source_path)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            shutil.copy2(backup_path, source_path)
            logger.info(f"Restored from backup: {source_path}")
        except Exception as e:
            raise IOError(f"Failed to restore from backup: {e}")

    def remove_backup(self, source_path: Path) -> None:
        """
        Remove backup file.

        Args:
            source_path: Path to source file (backup path derived from this)
        """
        backup_path = self._get_backup_path(source_path)

        if backup_path.exists():
            backup_path.unlink()
            logger.info(f"Backup removed: {backup_path}")
