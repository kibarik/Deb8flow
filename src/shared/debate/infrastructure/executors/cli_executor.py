"""
CLI executor adapter for debate rooms.

This adapter calls scripts/document_debate_cli.py as a subprocess to execute debates.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional
from pathlib import Path

from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ...domain.services import categorize_error
from ...application.ports import DebateExecutor
from ...application.analyzers import TakeawayAnalyzer, TakeawayConfig
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
            # Clean up JSON file on timeout
            await self._cleanup_json_file(json_output_path)
            raise TimeoutError(f"Debate room {room_id.value} timed out")

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            # Clean up JSON file on error
            await self._cleanup_json_file(json_output_path)
            raise RuntimeError(f"Debate failed: {error_msg}")

        # Load JSON output if available
        if json_output_path and json_output_path.exists():
            return await self._parse_json_output(json_output_path, room_id, opponent, question)

        # Fallback: parse from stdout
        return self._parse_stdout_output(stdout.decode(), room_id, opponent)

    async def _cleanup_json_file(self, json_path: Optional[Path]) -> None:
        """Remove JSON file if it exists."""
        if json_path and json_path.exists():
            try:
                await asyncio.to_thread(json_path.unlink)
                logger.debug(f"Cleaned up JSON file: {json_path.name}")
            except Exception as e:
                logger.warning(f"Failed to clean up JSON file {json_path}: {e}")

    async def _parse_json_output(
        self,
        json_path: Path,
        room_id: RoomId,
        opponent: str,
        question: Optional[str] = None,
        generate_takeaways: bool = True
    ) -> DebateRoom:
        """Parse debate results from JSON file."""
        content = await asyncio.to_thread(json_path.read_text, encoding='utf-8')
        dialogue_json = json.loads(content)

        messages = [
            DebateMessage(
                speaker=Speaker(msg["speaker"]),
                content=msg["content"],
                stage=msg.get("stage", ""),
                timestamp=msg.get("timestamp", ""),
                validated=msg.get("validated", False)
            )
            for msg in dialogue_json.get("messages", dialogue_json)
        ]

        # Find verdict
        verdict = self._extract_verdict(messages)

        if verdict:
            logger.info(f"Completed room: TPM vs {opponent} - WINNER: {verdict.winner.value}")
        else:
            logger.warning(f"Completed room: TPM vs {opponent} - NO VERDICT")
            # Remove JSON file for failed room
            try:
                await asyncio.to_thread(json_path.unlink)
                logger.info(f"Removed JSON file for failed room: {json_path.name}")
            except Exception as e:
                logger.warning(f"Failed to remove JSON file {json_path}: {e}")

        # Generate takeaways if requested and verdict exists
        takeaways = []
        if generate_takeaways and verdict:
            try:
                takeaways = await self._generate_takeaways(
                    dialogue_json=dialogue_json,
                    question=question,
                    verdict=verdict
                )
                logger.info(f"Generated {len(takeaways)} takeaways for TPM vs {opponent}")
            except Exception as e:
                logger.warning(f"Failed to generate takeaways: {e}")

        return DebateRoom(
            room_id=room_id,
            pro_participant="TPM",
            con_participant=opponent,
            status=RoomStatus.SUCCESS if verdict else RoomStatus.FAILED,
            messages=messages,
            verdict=verdict,
            takeaways=takeaways
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

    async def _generate_takeaways(
        self,
        dialogue_json: dict,
        question: Optional[str],
        verdict: Verdict
    ) -> list:
        """
        Generate takeaways from the debate dialogue.

        Args:
            dialogue_json: The full dialogue JSON with messages and verdict
            question: The committee question (optional)
            verdict: The verdict object

        Returns:
            List of takeaway strings
        """
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEBATE_API_KEY") or os.environ.get("LLM_API_KEY")
        base_url = os.environ.get("OPENAI_API_BASE") or os.environ.get("API_BASE_URL")

        if not api_key:
            logger.warning("No API key found for takeaway generation, skipping")
            return []

        # Configure analyzer
        config = TakeawayConfig(
            min_takeaways=3,
            max_takeaways=10,
            api_key=api_key,
            base_url=base_url if base_url else None,
        )

        analyzer = TakeawayAnalyzer(config)

        # Extract dialogue data
        messages = dialogue_json.get("messages", dialogue_json)
        verdict_data = dialogue_json.get("verdict", {})

        # Use question from verdict or parameter
        if not question:
            question = "Анализ документа продукта комитета"

        # Generate takeaways
        return await analyzer.generate_takeaways(
            dialogue=messages,
            question=question,
            verdict_explanation=verdict_data.get("explanation") or verdict.explanation,
            winner=verdict_data.get("winner") or verdict.winner.value
        )
