"""
Port interfaces for the shared debate framework.

This module defines protocol interfaces that define the contracts between
the application layer and infrastructure adapters. All ports use typing.Protocol
for structural subtyping (duck typing).
"""

from typing import Protocol, Dict, Any, List, Optional
from pathlib import Path
from ..domain.entities import DebateRoom, Verdict
from ..domain.value_objects import RoomId, RunId, Speaker


class DebateExecutor(Protocol):
    """Executes a single debate room."""

    async def execute(
        self,
        room_id: RoomId,
        pro_prompt_path: Path,
        con_prompt_path: Path,
        question: str,
        prd_content: str,
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        json_output_path: Optional[Path]
    ) -> DebateRoom:
        """Execute debate room and return result."""
        ...


class ReportGenerator(Protocol):
    """Generates markdown reports from debate results."""

    def generate_final_report(
        self,
        run_id: str,
        prd_path: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate comprehensive final report."""
        ...

    def generate_conclusion(
        self,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate executive summary conclusion."""
        ...

    def generate_intermediate_report(
        self,
        run_id: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate intermediate report during execution."""
        ...


class FileStorage(Protocol):
    """Persists artifacts to the file system."""

    async def create_run_directory(
        self,
        base_dir: Path,
        run_id: RunId
    ) -> Path:
        """Create output directory for a run."""
        ...

    async def save_dialogue_json(
        self,
        output_dir: Path,
        room: DebateRoom
    ) -> None:
        """Save debate room dialogue as JSON."""
        ...

    async def save_report(
        self,
        output_dir: Path,
        report_name: str,
        content: str
    ) -> None:
        """Save markdown report."""
        ...

    async def save_metadata(
        self,
        output_dir: Path,
        metadata: Dict[str, Any]
    ) -> None:
        """Save run metadata as JSON."""
        ...
