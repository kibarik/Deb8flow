"""
CLI executor adapter for debate rooms.

This adapter calls scripts/document_debate_cli.py as a subprocess to execute debates.
"""

import asyncio
import json
import logging
import os
import sys
import shutil
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ...domain.services import categorize_error
from ...application.ports import DebateExecutor
from ...application.analyzers import TakeawayAnalyzer, TakeawayConfig
from ..retry import retry_with_backoff, RateLimitError

if TYPE_CHECKING:
    from ....config.config_loader import LLMConfig


logger = logging.getLogger(__name__)


class CliDebateExecutor:
    """Executes debates by calling document_debate_cli.py as subprocess.

    Args:
        llm_config: Optional LLM configuration from debate_config.yaml
                    for API parameters (api_key, model, base_url).
    """

    DEFAULT_TIMEOUT = 900  # 15 minutes - increased for 9-stage debates
    MIN_DISK_MB = 100  # Minimum required disk space in MB

    def __init__(self, llm_config: Optional["LLMConfig"] = None):
        """Initialize executor with LLM configuration.

        Args:
            llm_config: LLM configuration from debate_config.yaml
        """
        self.llm_config = llm_config

    def _check_disk_space(self, output_dir: Optional[Path]) -> bool:
        """Check if there's enough disk space for debate output.

        Args:
            output_dir: Directory to check disk space for

        Returns:
            True if enough space, False otherwise
        """
        try:
            # Check disk space
            stat = shutil.disk_usage(output_dir if output_dir else Path.cwd())
            free_mb = stat.free / (1024 * 1024)

            if free_mb < self.MIN_DISK_MB:
                logger.error(f"Insufficient disk space: {free_mb:.1f}MB free, {self.MIN_DISK_MB}MB required")
                return False

            return True

        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            # Assume OK if we can't check
            return True

    async def _has_valid_result(self, json_path: Optional[Path]) -> bool:
        """Check if a valid debate result already exists.

        Args:
            json_path: Path to JSON result file

        Returns:
            True if valid result exists, False otherwise
        """
        if not json_path or not json_path.exists():
            return False

        try:
            content = await asyncio.to_thread(json_path.read_text, encoding='utf-8')
            data = json.loads(content)

            # Check if debate completed successfully
            # A valid result should have:
            # - 'winner' field (not None or empty)
            # - 'messages' array with at least 9 entries (8 stages + verdict)
            # - 'in_progress' should be False or not present

            if isinstance(data, dict):
                winner = data.get("winner")
                messages = data.get("messages", [])
                in_progress = data.get("in_progress", False)

                if in_progress:
                    # Check if nearly complete (8+ messages) - might be worth using
                    if len(messages) >= 8:
                        logger.info(f"Found nearly complete debate at {json_path.name} ({len(messages)} messages), will reuse")
                        return True
                    logger.info(f"Found incomplete debate at {json_path.name}, will re-run")
                    return False

                if not winner:
                    # No winner but has messages - check if nearly complete
                    if len(messages) >= 8:
                        logger.info(f"Found debate without winner but with {len(messages)} messages at {json_path.name}, will reuse")
                        return True
                    logger.info(f"Found debate result without winner at {json_path.name}, will re-run")
                    return False

                if len(messages) < 9:
                    logger.info(f"Found incomplete debate ({len(messages)} messages) at {json_path.name}, will re-run")
                    return False

                # Found valid result
                logger.info(f"Found valid debate result at {json_path.name}, will reuse")
                return True

        except Exception as e:
            logger.warning(f"Error checking existing result: {e}")

        return False

    def _is_nearly_complete(self, data: dict) -> bool:
        """Check if a debate result is nearly complete (8+ messages).

        Args:
            data: Parsed JSON data

        Returns:
            True if debate has 8 or more messages
        """
        if not isinstance(data, dict):
            return False

        messages = data.get("messages", [])
        return len(messages) >= 8

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

        # Check if we already have a valid result (including nearly complete)
        if await self._has_valid_result(json_output_path):
            logger.info(f"Reusing existing result for TPM vs {opponent}")
            return await self._parse_json_output(json_output_path, room_id, opponent, question)

        # Check disk space before starting
        output_dir = json_output_path.parent if json_output_path else None
        if not self._check_disk_space(output_dir):
            error_msg = f"Insufficient disk space (need {self.MIN_DISK_MB}MB)"
            logger.error(error_msg)
            return DebateRoom(
                room_id=room_id,
                pro_participant="TPM",
                con_participant=opponent,
                status=RoomStatus.FAILED,
                messages=[],
                error=error_msg
            )

        async def _execute_once():
            return await self._execute_room(
                room_id, pro_prompt_path, con_prompt_path,
                question, prd_content, model, language,
                json_output_path, opponent
            )

        try:
            result = await retry_with_backoff(_execute_once, max_retries)

            # After execution, check the result status
            # TIMEOUT: Preserve partial results, don't retry
            if result.status == RoomStatus.TIMEOUT:
                logger.warning(f"Debate TPM vs {opponent} timed out - partial results preserved")
                return result
            # SUCCESS: Valid complete result
            elif result.status == RoomStatus.SUCCESS:
                logger.info(f"Debate TPM vs {opponent} completed successfully")
                return result
            # Has verdict but status might be different - still valid
            elif result.verdict is not None:
                logger.info(f"Debate TPM vs {opponent} completed with verdict")
                return result
            else:
                # Execution returned but no verdict - treat as failure
                error_msg = result.error or "Debate completed without verdict"
                logger.warning(f"Debate TPM vs {opponent} returned invalid result: {error_msg}")

                # Check if we should retry (only if attempts remaining)
                if max_retries > 0:
                    raise RuntimeError(f"Invalid result: {error_msg}")
                else:
                    return result

        except Exception as e:
            logger.error(f"Failed room: TPM vs {opponent} - {e}")
            # Check if we have a partial result to return (including TIMEOUT results)
            if json_output_path and json_output_path.exists():
                try:
                    partial_result = await self._parse_json_output(json_output_path, room_id, opponent, question)
                    if partial_result.status in (RoomStatus.SUCCESS, RoomStatus.TIMEOUT):
                        logger.info(f"Using partial result for TPM vs {opponent} despite error")
                        return partial_result
                except Exception as parse_error:
                    logger.warning(f"Could not parse partial result: {parse_error}")

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
            "--con-prompt", str(con_prompt_path),
            "--room-id", room_id.value  # Pass room_id for progress logging
        ]

        if model:
            cmd.extend(["--model", model])
        if language:
            cmd.extend(["--language", language])
        if json_output_path:
            cmd.extend(["--json-output", str(json_output_path)])

        # Run subprocess with stderr going directly to console for real-time progress
        # For 429 detection, we'll check the JSON file or return code
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=None  # Real-time progress output to console
        )

        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=self.DEFAULT_TIMEOUT
            )
        except asyncio.TimeoutError:
            process.kill()
            # Wait for process to actually terminate
            await process.wait()

            # On timeout, preserve partial progress and return TIMEOUT status
            if json_output_path and json_output_path.exists():
                try:
                    content = await asyncio.to_thread(json_output_path.read_text, encoding='utf-8')
                    data = json.loads(content)
                    messages = data.get("messages", [])
                    stage_info = data.get("stage", "unknown")

                    # Parse partial result and mark as TIMEOUT
                    logger.warning(f"Debate {room_id.value} timed out with {len(messages)} messages at stage {stage_info}, preserving partial result")
                    return await self._parse_json_output(json_output_path, room_id, opponent, question, is_timeout=True)
                except Exception as e:
                    logger.warning(f"Could not parse partial result after timeout: {e}")

            # Even if we can't parse, return a TIMEOUT room with the file path
            logger.warning(f"Debate {room_id.value} timed out after {self.DEFAULT_TIMEOUT}s, partial results saved to {json_output_path}")
            return DebateRoom(
                room_id=room_id,
                pro_participant="TPM",
                con_participant=opponent,
                status=RoomStatus.TIMEOUT,
                messages=[],
                error=f"Debate timed out after {self.DEFAULT_TIMEOUT}s. Partial results available."
            )

        # Check if process failed
        if process.returncode != 0:
            # Try to detect 429 from JSON file if it exists
            is_429_error = False

            if json_output_path and json_output_path.exists():
                try:
                    content = await asyncio.to_thread(json_output_path.read_text, encoding='utf-8')
                    data = json.loads(content)

                    # Check if there are error messages indicating 429
                    messages = data.get("messages", [])
                    for msg in messages:
                        msg_content = msg.get("content", "").lower()
                        if "429" in msg_content or "rate limit" in msg_content or "resource exhausted" in msg_content:
                            is_429_error = True
                            break
                except Exception:
                    pass  # If JSON parsing fails, fall back to other detection

            # Also check stdout for 429 indicators
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            if not is_429_error:
                if "429" in stdout_text.lower() or "rate limit" in stdout_text.lower() or "resource exhausted" in stdout_text.lower():
                    is_429_error = True

            if is_429_error:
                # Raise RateLimitError for retry logic to handle
                raise RateLimitError(f"Rate limit hit for room {room_id.value}")

            # For other errors, clean up and raise RuntimeError
            await self._cleanup_json_file(json_output_path)
            raise RuntimeError(f"Debate failed with return code {process.returncode}")

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
        generate_takeaways: bool = True,
        is_timeout: bool = False
    ) -> DebateRoom:
        """Parse debate results from JSON file.

        Handles both complete and partial results:
        - Complete: has winner field and 9+ messages
        - Partial: has messages but might be missing winner or some stages
        - Timeout: debate timed out but partial results are available

        Args:
            json_path: Path to JSON result file
            room_id: Room identifier
            opponent: Opponent name
            question: Optional committee question
            generate_takeaways: Whether to generate takeaways
            is_timeout: If True, mark result as TIMEOUT status
        """
        content = await asyncio.to_thread(json_path.read_text, encoding='utf-8')
        dialogue_json = json.loads(content)

        # Handle both dict format (with 'messages' key) and list format
        messages_list = dialogue_json.get("messages", []) if isinstance(dialogue_json, dict) else dialogue_json

        messages = [
            DebateMessage(
                speaker=Speaker(msg["speaker"]),
                content=msg["content"],
                stage=msg.get("stage", ""),
                timestamp=msg.get("timestamp", ""),
                validated=msg.get("validated", False)
            )
            for msg in messages_list
        ]

        # Determine if this is a partial or complete result
        is_nearly_complete = self._is_nearly_complete(dialogue_json) if isinstance(dialogue_json, dict) else len(messages_list) >= 8
        in_progress = dialogue_json.get("in_progress", False) if isinstance(dialogue_json, dict) else False

        # Find verdict - first check if winner field exists in JSON (new format)
        verdict = None
        winner_from_json = dialogue_json.get("winner") if isinstance(dialogue_json, dict) else None

        if winner_from_json:
            # Use winner from JSON (new format)
            try:
                winner = Speaker.PRO if winner_from_json.upper() == "PRO" else Speaker.CON
                # Get explanation from JUDGE message if available
                explanation = ""
                for msg in reversed(messages):
                    if msg.speaker == Speaker.JUDGE:
                        explanation = msg.content
                        break
                verdict = Verdict(winner=winner, explanation=explanation)
                logger.info(f"Completed room: TPM vs {opponent} - WINNER: {winner.value} (from JSON)")
            except Exception as e:
                logger.warning(f"Failed to parse winner from JSON: {e}, falling back to extraction")

        # Fallback to extraction from messages if no winner field or parsing failed
        if not verdict:
            verdict = self._extract_verdict(messages)

        # Determine status and error message
        if is_timeout:
            # Timeout case - preserve partial progress
            status = RoomStatus.TIMEOUT
            stage_info = dialogue_json.get("stage", "unknown") if isinstance(dialogue_json, dict) else "unknown"
            error_msg = f"Debate timed out at stage {stage_info} with {len(messages)} messages. Partial results preserved."
            logger.warning(f"Room TPM vs {opponent} marked as TIMEOUT: {error_msg}")
        elif verdict:
            status = RoomStatus.SUCCESS
            error_msg = None
        elif is_nearly_complete:
            # Nearly complete but no verdict - still count as success
            status = RoomStatus.SUCCESS
            error_msg = "Debate completed with most stages but no clear verdict"
        else:
            status = RoomStatus.FAILED
            error_msg = "No verdict found in JUDGE response - expected WINNER: PRO or WINNER: CON format"

        # Generate takeaways only for successful complete results
        takeaways = []
        if generate_takeaways and verdict and not in_progress and not is_timeout:
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
            status=status,
            messages=messages,
            verdict=verdict,
            takeaways=takeaways,
            error=error_msg
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
                    return Verdict(winner=winner, explanation=content)
        return None

    def _extract_verdict_from_text(self, text: str) -> Optional[Verdict]:
        """Extract verdict from plain text output."""
        import re
        verdict_pattern = r"WINNER:\s*(PRO|CON)"
        match = re.search(verdict_pattern, text, re.IGNORECASE)

        if match:
            winner_str = match.group(1)
            winner = Speaker.PRO if winner_str.upper() == "PRO" else Speaker.CON
            return Verdict(winner=winner, explanation=text)

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
        # Get API parameters from config or environment (fallback)
        if self.llm_config:
            api_key = self.llm_config.api_key
            model = self.llm_config.model
            base_url = self.llm_config.get_effective_base_url()
        else:
            # Fallback to environment variables
            api_key = os.environ.get("OPENAI_API_KEY")
            model = os.environ.get("DEBATE_MODEL")
            base_url = os.environ.get("DEBATE_BASE_URL")

        if not api_key:
            logger.warning("No API key found for takeaway generation, skipping")
            return []

        # Configure analyzer
        config = TakeawayConfig(
            min_takeaways=3,
            max_takeaways=10,
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
        )

        analyzer = TakeawayAnalyzer(config)

        # Extract dialogue data
        # dialogue_json can be either a dict with 'messages' key, or a list directly
        if isinstance(dialogue_json, dict):
            messages = dialogue_json.get("messages", [])
            verdict_data = dialogue_json.get("verdict", {})
        else:
            messages = dialogue_json  # It's already a list
            verdict_data = {}

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
