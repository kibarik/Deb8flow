"""
Use case for running a complete product committee session.

This module contains the RunProductCommittee use case which orchestrates
four debate rooms (TPM vs CPO/CFO/CTO/BDM) with concurrency control.
"""

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
        """
        Initialize the use case with required adapters.

        Args:
            executor: Debate executor implementation
            generator: Report generator implementation
            storage: File storage implementation
        """
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
        """
        Execute complete product committee session.

        Args:
            prd_path: Path to PRD document
            question: Committee question
            roles_dir: Directory containing role prompt files
            model: Optional LLM model name
            language: Optional language setting
            max_retries: Maximum retry attempts per room
            max_concurrency: Maximum parallel rooms (0=all, 1=sequential)
            output_dir: Output directory for results
            manual_run_id: Optional manual run identifier

        Returns:
            CommitteeRun with all room results
        """
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
