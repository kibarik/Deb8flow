# WP02: Port Interfaces and Application Layer

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP02
**Status**: TODO
**Dependencies**: WP01

## Overview

Define port interfaces using `typing.Protocol` and create use case orchestrators. This layer coordinates domain logic without knowing implementation details.

## Context

Ports define "what" the application needs, not "how" it's implemented. Adapters (WP03) will provide the implementations.

## Implementation Requirements

### 1. Port Interfaces (`src/shared/debate/application/ports.py`)

Define protocol interfaces for the application layer:

```python
from typing import Protocol, Dict, Any, List, Optional
from pathlib import Path
from ..domain.entities import DebateRoom, Verdict
from ..domain.value_objects import RoomId, RunId, Speaker

class DebateExecutor(Protocol):
    """Executes a single debate room."""

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
        """Execute debate room and return result."""
        ...

class ReportGenerator(Protocol):
    """Generates markdown reports from debate results."""

    def generate_final_report(
        self,
        run_id: str,
        prd_path: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate comprehensive final report."""
        ...

    def generate_conclusion(
        self,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate executive summary conclusion."""
        ...

    def generate_intermediate_report(
        self,
        run_id: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate intermediate report during execution."""
        ...

class FileStorage(Protocol):
    """Persists artifacts to the file system."""

    async def create_run_directory(
        self,
        base_dir: Path,
        run_id: RunId
    ) -> Path:
        """Create output directory for a run."""
        ...

    async def save_dialogue_json(
        self,
        output_dir: Path,
        room: DebateRoom
    ) -> None:
        """Save debate room dialogue as JSON."""
        ...

    async def save_report(
        self,
        output_dir: Path,
        report_name: str,
        content: str
    ) -> None:
        """Save markdown report."""
        ...

    async def save_metadata(
        self,
        output_dir: Path,
        metadata: Dict[str, Any]
    ) -> None:
        """Save run metadata as JSON."""
        ...
```

### 2. Execute Debate Use Case (`src/shared/debate/application/use_cases/execute_debate.py`)

Implement use case that coordinates debate execution:

```python
from typing import Optional
from pathlib import Path
from ...domain.entities import DebateRoom, DebateMessage, Verdict
from ...domain.value_objects import RoomId, Speaker, RoomStatus
from ..ports import DebateExecutor

class ExecuteDebate:
    """Use case for executing a single debate room."""

    def __init__(self, executor: DebateExecutor):
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
        """Execute debate room with retry logic."""
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
```

### 3. Package Structure

```python
# src/shared/debate/application/__init__.py
"""Application layer - use cases and port interfaces."""
from .ports import DebateExecutor, ReportGenerator, FileStorage

__all__ = ["DebateExecutor", "ReportGenerator", "FileStorage"]

# src/shared/debate/application/use_cases/__init__.py
"""Use case implementations."""
from .execute_debate import ExecuteDebate

__all__ = ["ExecuteDebate"]
```

## Testing Requirements

Test use cases with mock adapters:

```python
# tests/unit/shared/debate/application/test_ports.py
from src.shared.debate.application.ports import DebateExecutor
from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus

class MockDebateExecutor:
    async def execute(self, **kwargs):
        return DebateRoom(
            room_id=RoomId("test"),
            pro_participant="TPM",
            con_participant="CPO",
            status=RoomStatus.SUCCESS,
            messages=[],
            verdict=Verdict(winner=Speaker.PRO, explanation="Test")
        )

async def test_debate_executor_protocol():
    executor: DebateExecutor = MockDebateExecutor()
    result = await executor.execute(
        room_id=RoomId("test"),
        pro_prompt_path=Path("test.txt"),
        con_prompt_path=Path("test.txt"),
        question="test",
        prd_content="test",
        model=None,
        language=None,
        max_retries=2,
        json_output_path=None
    )
    assert result.is_successful

# tests/integration/test_execute_debate_use_case.py
import pytest
from src.shared.debate.application.use_cases import ExecuteDebate

@pytest.mark.asyncio
async def test_execute_debate_use_case():
    mock_executor = MockDebateExecutor()
    use_case = ExecuteDebate(mock_executor)

    result = await use_case.execute(
        room_id="test_room",
        pro_prompt_path=Path("test.txt"),
        con_prompt_path=Path("test.txt"),
        question="test question",
        prd_content="test prd",
        model=None,
        language=None,
        max_retries=2,
        json_output_path=None
    )

    assert result.room_id.value == "test_room"
```

## Acceptance Criteria

- [ ] All ports use `typing.Protocol` (not ABC)
- [ ] Use cases depend only on ports, not implementations
- [ ] Integration tests use mock adapters
- [ ] Clear separation between application and infrastructure
- [ ] `DebateExecutor` protocol defined
- [ ] `ReportGenerator` protocol defined
- [ ] `FileStorage` protocol defined
- [ ] `ExecuteDebate` use case implemented
- [ ] All tests pass with mock adapters

## Files to Create

1. `src/shared/debate/application/__init__.py`
2. `src/shared/debate/application/ports.py`
3. `src/shared/debate/application/use_cases/__init__.py`
4. `src/shared/debate/application/use_cases/execute_debate.py`
5. `tests/unit/shared/debate/application/test_ports.py`
6. `tests/integration/test_execute_debate_use_case.py`

## Notes

- Use `typing.Protocol` for structural subtyping (duck typing)
- Ports should NOT import from infrastructure layer
- Use cases orchestrate domain logic via ports
- Mock adapters for testing - don't use real implementations
- Keep use cases focused on single responsibility

## Next Steps

After completing this work package:
1. Run `pytest tests/unit/shared/debate/application/` to verify tests pass
2. Verify no infrastructure layer imports in ports/use_cases
3. Commit changes with message "feat: implement port interfaces and use cases (WP02)"
4. Move to WP03 (Infrastructure Adapters)
