# WP03: Infrastructure Adapters (Debate Executor & Storage)

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP03
**Status**: TODO
**Dependencies**: WP02

## Overview

Implement concrete adapters for debate execution (subprocess) and file storage. These adapters implement the port interfaces defined in WP02.

## Context

Adapters provide the "how" - the actual implementation of calling subprocesses, writing files, etc. They must implement the protocols from WP02.

## Implementation Requirements

### 1. CLI Debate Executor (`src/shared/debate/infrastructure/executors/cli_executor.py`)

Implement subprocess call to document_debate_cli.py:

```python
import asyncio
import subprocess
import sys
import logging
from typing import Optional
from pathlib import Path
from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ...domain.services import categorize_error
from ...application.ports import DebateExecutor

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

        for attempt in range(max_retries + 1):
            try:
                return await self._execute_once(
                    room_id, pro_prompt_path, con_prompt_path,
                    question, prd_content, model, language,
                    json_output_path, opponent
                )
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {room_id.value}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Room {room_id.value} failed after {max_retries + 1} attempts")
                    return DebateRoom(
                        room_id=room_id,
                        pro_participant="TPM",
                        con_participant=opponent,
                        status=RoomStatus.FAILED,
                        messages=[],
                        error=str(e)
                    )

    async def _execute_once(
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
        # Build command
        cmd = [
            sys.executable,
            "document_debate_cli.py",
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
        import json

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
        verdict = None
        for msg in reversed(dialogue):
            if "verdict" in msg.get("content", "").lower():
                content = msg["content"]
                if "WINNER: PRO" in content:
                    verdict = Verdict(winner=Speaker.PRO, explanation=content)
                    break
                elif "WINNER: CON" in content:
                    verdict = Verdict(winner=Speaker.CON, explanation=content)
                    break

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
        import re

        verdict_pattern = r"WINNER:\s*(PRO|CON)"
        match = re.search(verdict_pattern, stdout)

        verdict = None
        if match:
            winner_str = match.group(1)
            winner = Speaker.PRO if winner_str == "PRO" else Speaker.CON
            verdict = Verdict(winner=winner, explanation=stdout[-500:])

        return DebateRoom(
            room_id=room_id,
            pro_participant="TPM",
            con_participant=opponent,
            status=RoomStatus.SUCCESS if verdict else RoomStatus.FAILED,
            messages=[],
            verdict=verdict
        )
```

### 2. Local File Storage (`src/shared/debate/infrastructure/storage/local_storage.py`)

Implement file storage with non-blocking I/O:

```python
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from ...domain.value_objects import RunId
from ...domain.entities import DebateRoom
from ...application.ports import FileStorage

class LocalFileStorage:
    """File storage adapter using asyncio.to_thread for non-blocking I/O."""

    async def create_run_directory(
        self,
        base_dir: Path,
        run_id: RunId
    ) -> Path:
        """Create output directory for a run."""
        run_dir = base_dir / run_id.value
        await asyncio.to_thread(run_dir.mkdir, parents=True, exist_ok=True)
        return run_dir

    async def save_dialogue_json(
        self,
        output_dir: Path,
        room: DebateRoom
    ) -> None:
        """Save debate room dialogue as JSON."""
        dialogue_path = output_dir / f"{room.room_id.value}_dialogue.json"
        content = room.to_json()
        await asyncio.to_thread(
            dialogue_path.write_text,
            content,
            encoding="utf-8"
        )

    async def save_report(
        self,
        output_dir: Path,
        report_name: str,
        content: str
    ) -> None:
        """Save markdown report."""
        report_path = output_dir / report_name
        await asyncio.to_thread(
            report_path.write_text,
            content,
            encoding="utf-8"
        )

    async def save_metadata(
        self,
        output_dir: Path,
        metadata: Dict[str, Any]
    ) -> None:
        """Save run metadata as JSON."""
        metadata_path = output_dir / "metadata.json"
        content = json.dumps(metadata, indent=2)
        await asyncio.to_thread(
            metadata_path.write_text,
            content,
            encoding="utf-8"
        )
```

### 3. Retry Logic (`src/shared/debate/infrastructure/retry.py`)

Extract retry logic for reuse:

```python
import asyncio
import logging
from typing import Callable, TypeVar, Optional

T = TypeVar('T')

logger = logging.getLogger(__name__)

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int,
    *args,
    **kwargs
) -> T:
    """Execute function with exponential backoff retry."""
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries + 1} attempts")

    raise last_exception or Exception("Retry failed")
```

## Testing Requirements

Test adapters with real subprocess/file operations:

```python
# tests/integration/test_cli_executor.py
import pytest
from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor

@pytest.mark.asyncio
async def test_cli_executor_calls_subprocess():
    executor = CliDebateExecutor()
    # Test with real subprocess (requires document_debate_cli.py)

@pytest.mark.asyncio
async def test_local_storage_non_blocking():
    from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage
    storage = LocalFileStorage()

    # Test non-blocking file operations
    await storage.save_report(
        Path("/tmp/test"),
        "test.md",
        "# Test"
    )
```

## Acceptance Criteria

- [ ] `CliDebateExecutor` successfully calls `document_debate_cli.py`
- [ ] `LocalFileStorage` uses non-blocking I/O via `asyncio.to_thread`
- [ ] Retry logic implements exponential backoff (2^attempt seconds)
- [ ] All adapters implement their respective protocols
- [ ] Integration tests validate end-to-end behavior
- [ ] Error categorization matches spec requirements

## Files to Create

1. `src/shared/debate/infrastructure/__init__.py`
2. `src/shared/debate/infrastructure/executors/__init__.py`
3. `src/shared/debate/infrastructure/executors/cli_executor.py`
4. `src/shared/debate/infrastructure/storage/__init__.py`
5. `src/shared/debate/infrastructure/storage/local_storage.py`
6. `src/shared/debate/infrastructure/retry.py`
7. `tests/integration/test_cli_executor.py`
8. `tests/integration/test_local_storage.py`

## Notes

- Use `asyncio.create_subprocess_exec` for subprocess execution
- Use `asyncio.to_thread` for file I/O (non-blocking)
- Implement timeout handling (DEFAULT_TIMEOUT = 300s)
- Parse JSON output when available, fallback to stdout parsing
- Retry logic: 2^attempt seconds delay (exponential backoff)

## Next Steps

After completing this work package:
1. Run `pytest tests/integration/` to verify adapter behavior
2. Test with real `document_debate_cli.py` subprocess
3. Commit changes with message "feat: implement infrastructure adapters (WP03)"
4. Move to WP04 (Committee Domain and Use Cases)
