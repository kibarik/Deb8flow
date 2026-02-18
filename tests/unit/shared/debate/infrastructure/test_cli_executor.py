"""Tests for CliDebateExecutor class."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

import pytest

from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor
from src.shared.debate.domain.entities import DebateRoom, DebateMessage, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus


@pytest.fixture
def executor():
    """Create a CliDebateExecutor instance."""
    return CliDebateExecutor()


@pytest.fixture
def mock_pro_prompt_path(tmp_path):
    """Create a mock PRO prompt file."""
    prompt_path = tmp_path / "tpm.txt"
    prompt_path.write_text("You are TPM.", encoding="utf-8")
    return prompt_path


@pytest.fixture
def mock_con_prompt_path(tmp_path):
    """Create a mock CON prompt file."""
    prompt_path = tmp_path / "cpo.txt"
    prompt_path.write_text("You are CPO.", encoding="utf-8")
    return prompt_path


@pytest.fixture
def sample_dialogue_json():
    """Create sample dialogue JSON for testing."""
    return [
        {
            "speaker": "PRO",
            "content": "Opening statement for TPM",
            "stage": "opening",
            "timestamp": "2024-01-01T00:00:00Z",
            "validated": True
        },
        {
            "speaker": "CON",
            "content": "Opening statement for CPO",
            "stage": "opening",
            "timestamp": "2024-01-01T00:01:00Z",
            "validated": True
        },
        {
            "speaker": "JUDGE",
            "content": "WINNER: PRO - TPM made stronger arguments",
            "stage": "verdict",
            "timestamp": "2024-01-01T00:05:00Z",
            "validated": False
        }
    ]


class TestCliDebateExecutor:
    """Test suite for CliDebateExecutor."""

    @pytest.mark.asyncio
    async def test_execute_with_json_output(
        self, executor, tmp_path, mock_pro_prompt_path,
        mock_con_prompt_path, sample_dialogue_json
    ):
        """Should parse debate results from JSON output file."""
        json_output_path = tmp_path / "dialogue.json"
        json_output_path.write_text(json.dumps(sample_dialogue_json), encoding="utf-8")

        room_id = RoomId("TPM_vs_CPO")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock successful subprocess execution
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            result = await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="What is the potential?",
                prd_content="Sample PRD content",
                model=None,
                language=None,
                max_retries=1,
                json_output_path=json_output_path
            )

            assert result.room_id == room_id
            assert result.pro_participant == "TPM"
            assert result.con_participant == "CPO"
            assert result.status == RoomStatus.SUCCESS
            assert len(result.messages) == 3
            assert result.verdict is not None
            assert result.verdict.winner == Speaker.PRO

    @pytest.mark.asyncio
    async def test_execute_fallback_to_stdout_parsing(
        self, executor, mock_pro_prompt_path, mock_con_prompt_path
    ):
        """Should parse verdict from stdout when JSON is unavailable."""
        room_id = RoomId("TPM_vs_CPO")
        stdout_output = "Debate in progress...\nWINNER: CON - CPO wins\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(
                stdout_output.encode(),
                b""
            ))
            mock_subprocess.return_value = mock_process

            result = await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="Test question",
                prd_content="Test PRD",
                model=None,
                language=None,
                max_retries=1,
                json_output_path=None
            )

            assert result.status == RoomStatus.SUCCESS
            assert result.verdict.winner == Speaker.CON

    @pytest.mark.asyncio
    async def test_execute_handles_timeout(
        self, executor, mock_pro_prompt_path, mock_con_prompt_path
    ):
        """Should handle timeout and return failed room."""
        room_id = RoomId("TPM_vs_CPO")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()

            async def raise_timeout(*args, **kwargs):
                await asyncio.sleep(0.1)
                raise asyncio.TimeoutError()

            mock_process.communicate = raise_timeout
            mock_subprocess.return_value = mock_process

            result = await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="Test",
                prd_content="PRD",
                model=None,
                language=None,
                max_retries=1,
                json_output_path=None
            )

            assert result.status == RoomStatus.FAILED
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_non_zero_exit(
        self, executor, mock_pro_prompt_path, mock_con_prompt_path
    ):
        """Should handle subprocess returning non-zero exit code."""
        room_id = RoomId("TPM_vs_CPO")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(
                b"",
                b"Error: LLM API failure"
            ))
            mock_subprocess.return_value = mock_process

            result = await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="Test",
                prd_content="PRD",
                model=None,
                language=None,
                max_retries=1,
                json_output_path=None
            )

            assert result.status == RoomStatus.FAILED

    @pytest.mark.asyncio
    async def test_builds_command_with_model(
        self, executor, mock_pro_prompt_path, mock_con_prompt_path
    ):
        """Should include model parameter in command when provided."""
        room_id = RoomId("TPM_vs_CPO")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="Test",
                prd_content="PRD",
                model="gpt-4",
                language=None,
                max_retries=1,
                json_output_path=None
            )

            # Verify the command includes --model flag
            call_args = mock_subprocess.call_args[0]
            assert "--model" in call_args
            assert "gpt-4" in call_args

    @pytest.mark.asyncio
    async def test_builds_command_with_language(
        self, executor, mock_pro_prompt_path, mock_con_prompt_path
    ):
        """Should include language parameter in command when provided."""
        room_id = RoomId("TPM_vs_CPO")

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_subprocess.return_value = mock_process

            await executor.execute(
                room_id=room_id,
                pro_prompt_path=mock_pro_prompt_path,
                con_prompt_path=mock_con_prompt_path,
                question="Test",
                prd_content="PRD",
                model=None,
                language="русский",
                max_retries=1,
                json_output_path=None
            )

            # Verify the command includes --language flag
            call_args = mock_subprocess.call_args[0]
            assert "--language" in call_args
            assert "русский" in call_args
