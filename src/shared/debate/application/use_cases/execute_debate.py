"""
Use case for executing a single debate room.

This module contains the ExecuteDebate use case which coordinates
the execution of a debate room via the DebateExecutor port.
"""

from typing import Optional
from pathlib import Path
from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ..ports import DebateExecutor


class ExecuteDebate:
    """Use case for executing a single debate room."""

    def __init__(self, executor: DebateExecutor):
        """
        Initialize the use case with a debate executor.

        Args:
            executor: An implementation of the DebateExecutor port
        """
        self.executor = executor

    async def execute(
        self,
        room_id: str,
        pro_prompt_path: Path,
        con_prompt_path: Path,
        question: str,
        prd_content: str,
        model: Optional[str],
        language: Optional[str],
        max_retries: int,
        json_output_path: Optional[Path]
    ) -> DebateRoom:
        """
        Execute debate room with retry logic.

        Args:
            room_id: The identifier for this debate room
            pro_prompt_path: Path to the PRO debater prompt file
            con_prompt_path: Path to the CON debater prompt file
            question: The debate topic/question
            prd_content: The PRD document content for context
            model: Optional LLM model override
            language: Optional language/style setting
            max_retries: Maximum number of retry attempts
            json_output_path: Optional path to save JSON output

        Returns:
            A DebateRoom with the execution results
        """
        room_id_vo = RoomId(room_id)

        # Initial status
        result = DebateRoom(
            room_id=room_id_vo,
            pro_participant=Path(pro_prompt_path).stem.upper(),
            con_participant=Path(con_prompt_path).stem.upper(),
            status=RoomStatus.IN_PROGRESS,
            messages=[]
        )

        # Execute via executor
        result = await self.executor.execute(
            room_id=room_id_vo,
            pro_prompt_path=pro_prompt_path,
            con_prompt_path=con_prompt_path,
            question=question,
            prd_content=prd_content,
            model=model,
            language=language,
            max_retries=max_retries,
            json_output_path=json_output_path
        )

        return result
