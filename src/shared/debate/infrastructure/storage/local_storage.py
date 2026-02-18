"""
Local file storage adapter with non-blocking I/O.

This adapter provides async file operations using asyncio.to_thread
to prevent blocking the event loop during file operations.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

from ...domain.value_objects import RunId
from ...domain.entities import DebateRoom
from ...application.ports import FileStorage


logger = logging.getLogger(__name__)


class LocalFileStorage:
    """File storage adapter using asyncio.to_thread for non-blocking I/O."""

    async def create_run_directory(
        self,
        base_dir: Path,
        run_id: RunId
    ) -> Path:
        """Create output directory for a run."""
        run_dir = base_dir / run_id.value
        await asyncio.to_thread(run_dir.mkdir, parents=True, exist_ok=True)
        return run_dir

    async def save_dialogue_json(
        self,
        output_dir: Path,
        room: DebateRoom
    ) -> None:
        """Save debate room dialogue as JSON."""
        dialogue_path = output_dir / f"{room.room_id.value}_dialogue.json"
        content = room.to_json()
        await asyncio.to_thread(
            dialogue_path.write_text,
            content,
            encoding="utf-8"
        )

    async def save_report(
        self,
        output_dir: Path,
        report_name: str,
        content: str
    ) -> None:
        """Save markdown report."""
        report_path = output_dir / report_name
        await asyncio.to_thread(
            report_path.write_text,
            content,
            encoding="utf-8"
        )

    async def save_metadata(
        self,
        output_dir: Path,
        metadata: Dict[str, Any]
    ) -> None:
        """Save run metadata as JSON."""
        metadata_path = output_dir / "metadata.json"
        content = json.dumps(metadata, indent=2)
        await asyncio.to_thread(
            metadata_path.write_text,
            content,
            encoding="utf-8"
        )
