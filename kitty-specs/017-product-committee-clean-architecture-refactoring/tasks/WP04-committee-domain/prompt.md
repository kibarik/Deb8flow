# WP04: Committee Domain and Use Cases

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP04
**Status**: FOR_REVIEW
**Dependencies**: WP01, WP02

## Overview

Create committee-specific domain entities and use cases extending the shared framework. This implements the product committee orchestration logic.

## Implementation Requirements

### 1. Committee Domain Entities (`src/committee/domain/entities.py`)

Extend shared framework with committee-specific entities:

```python
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RunId, Speaker
from pathlib import Path

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
        return self.end_time is not None

    @property
    def successful_rooms(self) -> List[DebateRoom]:
        return [r for r in self.rooms if r.is_successful]

    @property
    def failed_rooms(self) -> List[DebateRoom]:
        return [r for r in self.rooms if r.status.value == "failed"]

    @property
    def tpm_wins(self) -> int:
        return sum(1 for r in self.successful_rooms
                   if r.verdict and r.verdict.winner == Speaker.PRO)

    @property
    def opponent_wins(self) -> int:
        return len(self.successful_rooms) - self.tpm_wins

    def mark_complete(self):
        """Mark run as complete."""
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
        import json
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_run(cls, run: CommitteeRun, errors: List[Dict[str, Any]]) -> "CommitteeMetadata":
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
        import asyncio

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save final report
        final_path = output_dir / "final_report.md"
        final_path.write_text(self.final_report_markdown, encoding="utf-8")

        # Save conclusion
        conclusion_path = output_dir / "conclusion.md"
        conclusion_path.write_text(self.conclusion_markdown, encoding="utf-8")
```

### 2. Run Product Committee Use Case (`src/committee/application/run_committee.py`)

Implement the main committee orchestration use case:

```python
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone

from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RunId, RoomId, RoomStatus
from src.shared.debate.application.ports import DebateExecutor, ReportGenerator, FileStorage
from ..domain.entities import CommitteeRun, CommitteeMetadata, CommitteeReport

ROOM_ORDER = ["cpo", "cfo", "cto", "bdm"]

class RunProductCommittee:
    """Use case for running a complete product committee session."""

    def __init__(
        self,
        executor: DebateExecutor,
        generator: ReportGenerator,
        storage: FileStorage
    ):
        self.executor = executor
        self.generator = generator
        self.storage = storage

    async def execute(
        self,
        prd_path: str,
        question: str,
        roles_dir: str,
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        max_concurrency: int,
        output_dir: Path,
        manual_run_id: Optional[str]
    ) -> CommitteeRun:
        """Execute complete product committee session."""
        # Initialize
        run_id = RunId.generate(question, manual_run_id)
        start_time = datetime.now(timezone.utc).isoformat()

        # Create output directory
        run_output_dir = await self.storage.create_run_directory(output_dir, run_id)

        # Read PRD content
        prd_content = await self._read_prd_content(prd_path)

        # Validate role prompts
        role_files = await self._validate_role_prompts(Path(roles_dir))

        # Execute debate rooms
        rooms = await self._execute_rooms(
            run_id=run_id,
            question=question,
            prd_content=prd_content,
            role_files=role_files,
            model=model,
            language=language,
            max_retries=max_retries,
            max_concurrency=max_concurrency,
            output_dir=run_output_dir
        )

        # Create committee run
        committee_run = CommitteeRun(
            run_id=run_id,
            question=question,
            prd_path=prd_path,
            model=model,
            language=language,
            max_retries=max_retries,
            max_concurrency=max_concurrency,
            rooms=rooms,
            start_time=start_time
        )

        # Mark complete and generate reports
        committee_run.mark_complete()

        # Generate and save reports
        metadata = CommitteeMetadata.from_run(committee_run, [])
        await self._save_reports(committee_run, metadata, run_output_dir)

        return committee_run

    async def _read_prd_content(self, prd_path: str) -> str:
        """Read PRD document content."""
        path = Path(prd_path)

        if path.suffix.lower() == ".docx":
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)

        # Try multiple encodings for text files
        encodings = ['utf-8', 'cp1251', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                return await asyncio.to_thread(path.read_text, encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise RuntimeError(f"Could not decode PRD file: {prd_path}")

    async def _validate_role_prompts(self, roles_dir: Path) -> Dict[str, Optional[Path]]:
        """Validate role prompt files exist."""
        role_files = {}

        # TPM is required
        tpm_path = roles_dir / "tpm.txt"
        if not tpm_path.exists():
            raise FileNotFoundError(f"TPM prompt not found: {tpm_path}")
        role_files["tpm"] = tpm_path

        # Other roles are optional
        for role in ROOM_ORDER:
            role_path = roles_dir / f"{role}.txt"
            role_files[role] = role_path if role_path.exists() else None

        return role_files

    async def _execute_rooms(
        self,
        run_id: RunId,
        question: str,
        prd_content: str,
        role_files: Dict[str, Optional[Path]],
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        max_concurrency: int,
        output_dir: Path
    ) -> List[DebateRoom]:
        """Execute all debate rooms with concurrency control."""
        rooms = []
        tasks = []

        for role in ROOM_ORDER:
            opponent_file = role_files[role]

            # Skip if opponent prompt is missing
            if opponent_file is None:
                rooms.append(DebateRoom(
                    room_id=RoomId(f"TPM_vs_{role.upper()}"),
                    pro_participant="TPM",
                    con_participant=role.upper(),
                    status=RoomStatus.SKIPPED,
                    messages=[]
                ))
                continue

            # Create task
            task = self._execute_single_room(
                run_id=run_id,
                role=role,
                pro_prompt=role_files["tpm"],
                con_prompt=opponent_file,
                question=question,
                prd_content=prd_content,
                model=model,
                language=language,
                max_retries=max_retries,
                output_dir=output_dir
            )
            tasks.append(task)

        # Execute with concurrency control
        if max_concurrency == 0:
            # Run all at once
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run with semaphore
            semaphore = asyncio.Semaphore(max_concurrency)

            async def bounded_task(task):
                async with semaphore:
                    return await task

            bounded_tasks = [bounded_task(t) for t in tasks]
            results = await asyncio.gather(*bounded_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create failed room
                role = ROOM_ORDER[i]
                rooms.append(DebateRoom(
                    room_id=RoomId(f"TPM_vs_{role.upper()}"),
                    pro_participant="TPM",
                    con_participant=role.upper(),
                    status=RoomStatus.FAILED,
                    messages=[],
                    error=str(result)
                ))
            else:
                rooms.append(result)

        return rooms

    async def _execute_single_room(
        self,
        run_id: RunId,
        role: str,
        pro_prompt: Path,
        con_prompt: Path,
        question: str,
        prd_content: str,
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        output_dir: Path
    ) -> DebateRoom:
        """Execute a single debate room."""
        room_id = RoomId(f"TPM_vs_{role.upper()}")
        json_output_path = output_dir / f"{room_id.value}_dialogue.json"

        return await self.executor.execute(
            room_id=room_id,
            pro_prompt_path=pro_prompt,
            con_prompt_path=con_prompt,
            question=question,
            prd_content=prd_content,
            model=model,
            language=language,
            max_retries=max_retries,
            json_output_path=json_output_path
        )

    async def _save_reports(
        self,
        run: CommitteeRun,
        metadata: CommitteeMetadata,
        output_dir: Path
    ) -> None:
        """Generate and save all reports."""
        # Generate reports
        final_report = self.generator.generate_final_report(
            run_id=run.run_id.value,
            prd_path=run.prd_path,
            question=run.question,
            rooms=run.rooms,
            metadata=asdict(metadata)
        )

        conclusion = self.generator.generate_conclusion(
            question=run.question,
            rooms=run.rooms,
            metadata=asdict(metadata)
        )

        # Save via storage
        await self.storage.save_report(output_dir, "final_report.md", final_report)
        await self.storage.save_report(output_dir, "conclusion.md", conclusion)
        await self.storage.save_metadata(output_dir, asdict(metadata))

        # Save dialogue JSONs
        for room in run.rooms:
            if room.is_successful:
                await self.storage.save_dialogue_json(output_dir, room)
```

## Testing Requirements

```python
# tests/unit/committee/domain/test_entities.py
from src.committee.domain.entities import CommitteeRun

def test_committee_run_tpm_wins():
    rooms = [room_with_tpm_win, room_with_opponent_win]
    run = CommitteeRun(
        run_id=RunId("test"),
        question="test",
        prd_path="test.txt",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=2,
        rooms=rooms,
        start_time="2025-01-01T00:00:00Z"
    )
    assert run.tpm_wins == 1
    assert run.opponent_wins == 1

# tests/integration/test_committee_workflow.py
@pytest.mark.asyncio
async def test_run_product_committee_use_case():
    use_case = RunProductCommittee(mock_executor, mock_generator, mock_storage)
    result = await use_case.execute(...)
    assert len(result.rooms) == 4
```

## Acceptance Criteria

- [ ] `CommitteeRun` correctly tracks 4 debate rooms
- [ ] Parallel execution completes faster than sequential
- [ ] Intermediate reports saved after each room completes
- [ ] Use case coordinates debate execution via shared ports
- [ ] All committee tests pass
- [ ] Concurrency control works (max_concurrency parameter)
- [ ] Missing role prompts handled gracefully (SKIPPED status)

## Files to Create

1. `src/committee/__init__.py`
2. `src/committee/domain/__init__.py`
3. `src/committee/domain/entities.py`
4. `src/committee/application/__init__.py`
5. `src/committee/application/run_committee.py`
6. `tests/unit/committee/domain/test_entities.py`
7. `tests/integration/test_committee_workflow.py`

## Notes

- Extend shared framework, don't modify it
- Use shared ports (DebateExecutor, ReportGenerator, FileStorage)
- Support both parallel (max_concurrency=0) and sequential execution
- Handle missing role prompts gracefully
- Save intermediate reports after each room

## Next Steps

After completing this work package:
1. Run `pytest tests/unit/committee/ tests/integration/test_committee_workflow.py`
2. Test with real PRD file and role prompts
3. Commit changes with message "feat: implement committee domain and use cases (WP04)"
4. Move to WP05 (Report Generation System)
