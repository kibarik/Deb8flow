"""File operations for orchestrator document processing.

This module handles file reading with encoding detection, output path
generation, and atomic file writing while preserving originals.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.orchestrator.domain.models import OrchestratorConfig, OverwriteOutputMode


class FileOperations:
    """File operations for document processing.

    Handles reading source and corrections files with encoding detection,
    generating output paths, and writing corrected files atomically.
    """

    def __init__(self, config: OrchestratorConfig):
        """Initialize file operations.

        Args:
            config: Orchestrator configuration
        """
        self.config = config

    def read_source(self, source_path: Path) -> str:
        """Read source document with encoding detection.

        Args:
            source_path: Path to source document

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        return self._read_with_encoding_detection(source_path)

    def read_corrections(self, corrections_path: Path) -> str:
        """Read corrections document with encoding detection.

        Args:
            corrections_path: Path to corrections document

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        return self._read_with_encoding_detection(corrections_path)

    def _read_with_encoding_detection(self, file_path: Path) -> str:
        """Read file with automatic encoding detection.

        Tries common encodings in order: utf-8, latin-1, cp1252.

        Args:
            file_path: Path to file

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue

        # If all encodings fail, try with errors='replace' as last resort
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def generate_output_path(self, source_path: Path) -> Path:
        """Generate output path for corrected file.

        Args:
            source_path: Path to source file

        Returns:
            Path for corrected output file
        """
        # Get file extension
        stem = source_path.stem
        suffix = source_path.suffix

        # Build output filename
        output_name = stem
        if self.config.output_suffix:
            output_name += self.config.output_suffix

        if self.config.timestamp_output:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_name += f".{timestamp}"

        output_name += suffix

        # Determine output directory
        output_dir = source_path.parent
        # Note: In real usage, output_dir would come from args or config

        return output_dir / output_name

    def write_output(self, source_path: Path, content: str) -> Path:
        """Write corrected file atomically.

        Writes to a temporary file first, then renames atomically.
        Original file is never modified.

        Args:
            source_path: Path to original source file
            content: Corrected content to write

        Returns:
            Path to written output file

        Raises:
            FileExistsError: If output exists and overwrite mode is "error"
        """
        output_path = self.generate_output_path(source_path)

        # Handle conflicts
        if output_path.exists():
            if self.config.overwrite_output == OverwriteOutputMode.ERROR:
                raise FileExistsError(
                    f"Output file already exists: {output_path}\n"
                    f"Use --overwrite flag or remove the existing file."
                )
            elif self.config.overwrite_output == OverwriteOutputMode.TIMESTAMP:
                # Generate new path with timestamp
                stem = output_path.stem
                suffix = output_path.suffix
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                output_path = output_path.parent / f"{stem}.{timestamp}{suffix}"

        # Write atomically via temp file
        temp_path = output_path.with_suffix(".tmp")

        try:
            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Atomic rename
            shutil.move(str(temp_path), str(output_path))

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e

        return output_path

    def validate_source_readable(self, source_path: Path) -> None:
        """Validate that source file is readable.

        Args:
            source_path: Path to source file

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Source path is not a file: {source_path}")

        try:
            with open(source_path, "r") as f:
                f.read(1)
        except PermissionError:
            raise PermissionError(f"Source file is not readable: {source_path}")

    def validate_corrections_readable(self, corrections_path: Path) -> None:
        """Validate that corrections file is readable.

        Args:
            corrections_path: Path to corrections file

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
        """
        if not corrections_path.exists():
            raise FileNotFoundError(f"Corrections file not found: {corrections_path}")

        if not corrections_path.is_file():
            raise ValueError(f"Corrections path is not a file: {corrections_path}")

        try:
            with open(corrections_path, "r") as f:
                f.read(1)
        except PermissionError:
            raise PermissionError(f"Corrections file is not readable: {corrections_path}")
