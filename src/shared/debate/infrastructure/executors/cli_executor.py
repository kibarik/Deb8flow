"""
CLI executor adapter for debate rooms.

This adapter calls scripts/document_debate_cli.py as a subprocess to execute debates.
"""

import asyncio
import json
import logging
import sys
from typing import Optional
from pathlib import Path

from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ...domain.services import categorize_error
from ...application.ports import DebateExecutor
from ..retry import retry_with_backoff


logger = logging.getLogger(__name__)


class CliDebateExecutor:
    """Executes debates by calling document_debate_cli.py as subprocess."""

    DEFAULT_TIMEOUT = 300  # 5 minutes

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
        """Execute debate room with retry logic."""
        opponent = room_id.value.split("_vs_")[-1]

        async def _execute_once():
            return await self._execute_room(
                room_id, pro_prompt_path, con_prompt_path,
                question, prd_content, model, language,
                json_output_path, opponent
            )

        try:
            return await retry_with_backoff(_execute_once, max_retries)
        except Exception as e:
            logger.error(f"Failed room: TPM vs {opponent} - {e}")
            return DebateRoom(
                room_id=room_id,
                pro_participant="TPM",
                con_participant=opponent,
                status=RoomStatus.FAILED,
                messages=[],
                error=str(e)
            )

    async def _execute_room(
        self,
        room_id: RoomId,
        pro_prompt_path: Path,
        con_prompt_path: Path,
        question: str,
        prd_content: str,
        model: Optional[str],
        language: Optional[str],
        json_output_path: Optional[Path],
        opponent: str
    ) -> DebateRoom:
        """Execute single debate attempt."""
        logger.info(f"Starting room: TPM vs {opponent}")

        # Build command
        cmd = [
            sys.executable,
            "scripts/document_debate_cli.py",
            "--text", prd_content,
            "--pro-prompt", str(pro_prompt_path),
            "--con-prompt", str(con_prompt_path)
        ]

        if model:
            cmd.extend(["--model", model])
        if language:
            cmd.extend(["--language", language])
        if json_output_path:
            cmd.extend(["--json-output", str(json_output_path)])

        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.DEFAULT_TIMEOUT
            )
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError(f"Debate room {room_id.value} timed out")

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Debate failed: {error_msg}")

        # Load JSON output if available
        if json_output_path and json_output_path.exists():
            return await self._parse_json_output(json_output_path, room_id, opponent)

        # Fallback: parse from stdout
        return self._parse_stdout_output(stdout.decode(), room_id, opponent)

    async def _parse_json_output(
        self,
        json_path: Path,
        room_id: RoomId,
        opponent: str
    ) -> DebateRoom:
        """Parse debate results from JSON file."""
        content = await asyncio.to_thread(json_path.read_text, encoding='utf-8')
        dialogue = json.loads(content)

        messages = [
            DebateMessage(
                speaker=Speaker(msg["speaker"]),
                content=msg["content"],
                stage=msg.get("stage", ""),
                timestamp=msg.get("timestamp", ""),
                validated=msg.get("validated", False)
            )
            for msg in dialogue
        ]

        # Find verdict
        verdict = self._extract_verdict(messages)

        if verdict:
            logger.info(f"Completed room: TPM vs {opponent} - WINNER: {verdict.winner.value}")
        else:
            logger.warning(f"Completed room: TPM vs {opponent} - NO VERDICT")

        return DebateRoom(
            room_id=room_id,
            pro_participant="TPM",
            con_participant=opponent,
            status=RoomStatus.SUCCESS if verdict else RoomStatus.FAILED,
            messages=messages,
            verdict=verdict
        )

    def _parse_stdout_output(
        self,
        stdout: str,
        room_id: RoomId,
        opponent: str
    ) -> DebateRoom:
        """Parse debate results from stdout (fallback)."""
        verdict = self._extract_verdict_from_text(stdout)

        if verdict:
            logger.info(f"Completed room: TPM vs {opponent} - WINNER: {verdict.winner.value}")
        else:
            logger.warning(f"Completed room: TPM vs {opponent} - NO VERDICT")

        return DebateRoom(
            room_id=room_id,
            pro_participant="TPM",
            con_participant=opponent,
            status=RoomStatus.SUCCESS if verdict else RoomStatus.FAILED,
            messages=[],
            verdict=verdict
        )

    def _extract_verdict(self, messages: list) -> Optional[Verdict]:
        """Extract verdict from dialogue messages."""
        import re
        verdict_pattern = r"WINNER:\s*\*{0,2}(PRO|CON)\*{0,2}"

        for msg in reversed(messages):
            if "verdict" in msg.content.lower() or "winner" in msg.content.lower():
                content = msg.content
                match = re.search(verdict_pattern, content, re.IGNORECASE)
                if match:
                    winner_str = match.group(1)
                    winner = Speaker.PRO if winner_str.upper() == "PRO" else Speaker.CON
                    return Verdict(winner=winner, explanation=content[-500:] if len(content) > 500 else content)
        return None

    def _extract_verdict_from_text(self, text: str) -> Optional[Verdict]:
        """Extract verdict from plain text output."""
        import re
        verdict_pattern = r"WINNER:\s*(PRO|CON)"
        match = re.search(verdict_pattern, text, re.IGNORECASE)

        if match:
            winner_str = match.group(1)
            winner = Speaker.PRO if winner_str.upper() == "PRO" else Speaker.CON
            return Verdict(winner=winner, explanation=text[-500:] if len(text) > 500 else text)

        return None
