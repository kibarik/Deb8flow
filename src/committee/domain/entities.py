"""
Committee-specific domain entities.

This module contains entities specific to the product committee orchestration,
extending the shared debate framework.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RunId, Speaker


@dataclass
class CommitteeRun:
    """A complete product committee session with multiple debate rooms."""

    run_id: RunId
    question: str
    prd_path: str
    model: Optional[str]
    language: Optional[str]
    max_retries: int
    max_concurrency: int
    rooms: List[DebateRoom]
    start_time: str
    end_time: Optional[str] = None

    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if not (0 <= self.max_concurrency <= 4):
            raise ValueError("max_concurrency must be 0-4")

    @property
    def is_complete(self) -> bool:
        """Check if the committee run has completed."""
        return self.end_time is not None

    @property
    def successful_rooms(self) -> List[DebateRoom]:
        """Get all successfully completed debate rooms."""
        return [r for r in self.rooms if r.is_successful]

    @property
    def failed_rooms(self) -> List[DebateRoom]:
        """Get all failed debate rooms."""
        return [r for r in self.rooms if r.status.value == "failed"]

    @property
    def tpm_wins(self) -> int:
        """Count the number of rooms TPM (PRO) won."""
        return sum(1 for r in self.successful_rooms
                   if r.verdict and r.verdict.winner == Speaker.PRO)

    @property
    def opponent_wins(self) -> int:
        """Count the number of rooms opponents (CON) won."""
        return len(self.successful_rooms) - self.tpm_wins

    def mark_complete(self):
        """Mark the committee run as complete."""
        if not self.end_time:
            self.end_time = datetime.now(timezone.utc).isoformat()


@dataclass
class CommitteeMetadata:
    """Metadata for tracking committee execution."""

    run_id: str
    prd_path: str
    question: str
    model: str
    language: Optional[str]
    start_time: str
    end_time: Optional[str]
    room_statuses: Dict[str, str]
    max_retries: int
    max_concurrency: int
    warning_flags: Dict[str, bool]
    errors: List[Dict[str, Any]]

    def to_json(self) -> str:
        """Convert metadata to JSON string."""
        import json
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_run(cls, run: CommitteeRun, errors: List[Dict[str, Any]]) -> "CommitteeMetadata":
        """Create metadata from a CommitteeRun."""
        room_statuses = {
            f"tpm_{room.con_participant.lower()}": room.status.value
            for room in run.rooms
        }

        return cls(
            run_id=run.run_id.value,
            prd_path=run.prd_path,
            question=run.question,
            model=run.model or "default",
            language=run.language,
            start_time=run.start_time,
            end_time=run.end_time,
            room_statuses=room_statuses,
            max_retries=run.max_retries,
            max_concurrency=run.max_concurrency,
            warning_flags={
                "prd_too_short": False,
                "question_too_short": False,
                "some_rooms_failed": len(run.failed_rooms) > 0
            },
            errors=errors
        )


@dataclass
class CommitteeReport:
    """Generated report from a committee run."""

    run: CommitteeRun
    final_report_markdown: str
    conclusion_markdown: str

    def save(self, output_dir: Path) -> None:
        """Save report files to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save final report
        final_path = output_dir / "final_report.md"
        final_path.write_text(self.final_report_markdown, encoding="utf-8")

        # Save conclusion
        conclusion_path = output_dir / "conclusion.md"
        conclusion_path.write_text(self.conclusion_markdown, encoding="utf-8")
