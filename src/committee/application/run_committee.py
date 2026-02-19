"""
Use case for running a complete product committee session.

This module contains the RunProductCommittee use case which orchestrates
debate rooms based on configured agents with concurrency control.
"""

import asyncio
import logging
from dataclasses import asdict
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone

from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RunId, RoomId, RoomStatus
from src.shared.debate.application.ports import DebateExecutor, ReportGenerator, FileStorage
from src.shared.config import AgentsConfig
from ..domain.entities import CommitteeRun, CommitteeMetadata, CommitteeReport


logger = logging.getLogger(__name__)


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
        agents_config: AgentsConfig,
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
            agents_config: Configuration for debate agents (main + opponents)
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

        # Validate agent prompts and get paths
        agent_paths = await self._validate_agent_prompts(agents_config)

        # Execute debate rooms
        rooms = await self._execute_rooms(
            run_id=run_id,
            question=question,
            prd_content=prd_content,
            agents_config=agents_config,
            agent_paths=agent_paths,
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

        # Collect errors from failed rooms
        errors = self._collect_errors(committee_run)

        # Generate and save reports (always includes metadata with errors)
        metadata = CommitteeMetadata.from_run(committee_run, errors)
        await self._save_reports(committee_run, metadata, run_output_dir)

        # Note: We no longer delete folders on complete failure
        # metadata.json with error traces is kept for debugging

        return committee_run

    async def _cleanup_failed_run(self, output_dir: Path) -> None:
        """Remove output directory if all rooms failed."""
        import shutil
        try:
            if output_dir.exists():
                await asyncio.to_thread(shutil.rmtree, output_dir)
                logger.info(f"Removed failed run directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to remove directory {output_dir}: {e}")

    def _collect_errors(self, run: CommitteeRun) -> List[Dict[str, Any]]:
        """
        Collect errors from failed rooms.

        Args:
            run: The committee run

        Returns:
            List of error dictionaries with room_id, error, and timestamp
        """
        errors = []
        for room in run.rooms:
            if room.status.value == "failed" and room.error:
                errors.append({
                    "room_id": room.room_id.value,
                    "opponent": room.con_participant,
                    "error": room.error,
                    "timestamp": run.end_time or datetime.now(timezone.utc).isoformat()
                })
        return errors

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

    async def _validate_agent_prompts(self, agents_config: AgentsConfig) -> Dict[str, Path]:
        """
        Validate agent prompt files exist and return their paths.

        Args:
            agents_config: Configuration for agents

        Returns:
            Dict mapping agent names to their prompt file paths

        Raises:
            FileNotFoundError: If main agent prompt is not found
            ValueError: If no agents configured
        """
        if not agents_config.main_agent:
            raise ValueError("Main agent is required in configuration")

        agent_paths = {}

        # Validate main agent prompt
        main_prompt_path = Path(agents_config.main_agent.prompt_path)
        if not main_prompt_path.exists():
            raise FileNotFoundError(f"Main agent prompt not found: {main_prompt_path}")
        agent_paths[agents_config.main_agent.name] = main_prompt_path

        # Validate opponent prompts
        for opponent in agents_config.opponents:
            opp_prompt_path = Path(opponent.prompt_path)
            if not opp_prompt_path.exists():
                logger.warning(f"Opponent prompt not found: {opp_prompt_path}, skipping {opponent.name}")
                continue
            agent_paths[opponent.name] = opp_prompt_path

        logger.info(f"Validated {len(agent_paths)} agent prompts: {', '.join(agent_paths.keys())}")
        return agent_paths

    async def _execute_rooms(
        self,
        run_id: RunId,
        question: str,
        prd_content: str,
        agents_config: AgentsConfig,
        agent_paths: Dict[str, Path],
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        max_concurrency: int,
        output_dir: Path
    ) -> List[DebateRoom]:
        """
        Execute all debate rooms with concurrency control.

        Creates one debate room per opponent, each debating against the main agent.
        """
        rooms = []
        tasks = []
        opponent_names = []

        # Get main agent info
        main_name = agents_config.main_agent.name
        main_prompt = agent_paths[main_name]

        # Create tasks for each opponent
        for opponent in agents_config.opponents:
            opponent_name = opponent.name

            # Skip if opponent prompt file not found
            if opponent_name not in agent_paths:
                rooms.append(DebateRoom(
                    room_id=RoomId(f"{main_name}_vs_{opponent_name}"),
                    pro_participant=main_name,
                    con_participant=opponent_name,
                    status=RoomStatus.SKIPPED,
                    messages=[]
                ))
                continue

            opponent_names.append(opponent_name)

            # Create task
            task = self._execute_single_room(
                run_id=run_id,
                main_name=main_name,
                opponent_name=opponent_name,
                pro_prompt=main_prompt,
                con_prompt=agent_paths[opponent_name],
                question=question,
                prd_content=prd_content,
                model=model,
                language=language,
                max_retries=max_retries,
                output_dir=output_dir
            )
            tasks.append(task)

        logger.info(f"Created {len(tasks)} debate rooms: {main_name} vs {', '.join(opponent_names)}")

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
            opponent_name = opponent_names[i]
            if isinstance(result, Exception):
                # Create failed room
                rooms.append(DebateRoom(
                    room_id=RoomId(f"{main_name}_vs_{opponent_name}"),
                    pro_participant=main_name,
                    con_participant=opponent_name,
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
        main_name: str,
        opponent_name: str,
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
        room_id = RoomId(f"{main_name}_vs_{opponent_name}")
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
        # Save metadata always
        await self.storage.save_metadata(output_dir, asdict(metadata))

        # Skip report generation if all rooms failed
        if not run.successful_rooms:
            logger.warning("All rooms failed - skipping report generation")
            return

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

        # Save dialogue JSONs
        for room in run.rooms:
            if room.is_successful:
                await self.storage.save_dialogue_json(output_dir, room)
