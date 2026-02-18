# WP01: Shared Domain Layer

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP01
**Status**: FOR_REVIEW
**Dependencies**: None

## Overview

Create the shared debate framework domain layer with pure dataclasses and value objects. This is the foundation for all other work packages.

## Context

You are implementing a clean architecture refactoring of the product committee system. The domain layer must have **zero external dependencies** - only Python standard library.

## Implementation Requirements

### 1. Value Objects (`src/shared/debate/domain/value_objects.py`)

Create immutable value objects using `@dataclass(frozen=True)`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import re
from datetime import datetime, timezone

@dataclass(frozen=True)
class RoomId:
    """Immutable identifier for a debate room."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("RoomId must be a non-empty string")

@dataclass(frozen=True)
class RunId:
    """Immutable identifier for a committee run."""
    value: str

    @classmethod
    def generate(cls, question: str, manual_id: Optional[str] = None) -> "RunId":
        if manual_id:
            return cls(manual_id)

        words = question.strip().split()[:5]
        slug = "-".join(words).lower()
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return cls(f"RUN_{timestamp}_{slug}")

class Speaker(Enum):
    """Participant roles in a debate."""
    PRO = "PRO"
    CON = "CON"
    JUDGE = "JUDGE"

class RoomStatus(Enum):
    """Execution status of a debate room."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### 2. Domain Entities (`src/shared/debate/domain/entities.py`)

Create domain entities with business logic:

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
from .value_objects import RoomId, Speaker, RoomStatus

@dataclass
class DebateMessage:
    """A single message in a debate dialogue."""
    speaker: Speaker
    content: str
    stage: str
    timestamp: str
    validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker.value,
            "content": self.content,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "validated": self.validated
        }

@dataclass
class Verdict:
    """Judge's decision for a debate room."""
    winner: Speaker
    explanation: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "winner": self.winner.value,
            "explanation": self.explanation,
            "confidence": self.confidence
        }

@dataclass
class DebateRoom:
    """A single debate room between two participants."""
    room_id: RoomId
    pro_participant: str
    con_participant: str
    status: RoomStatus
    messages: List[DebateMessage]
    verdict: Optional[Verdict] = None
    takeaways: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        return self.status == RoomStatus.SUCCESS and self.verdict is not None

    @property
    def dialogue(self) -> List[Dict[str, Any]]:
        return [msg.to_dict() for msg in self.messages]

    def to_json(self) -> str:
        data = {
            "room_id": self.room_id.value,
            "pro_participant": self.pro_participant,
            "con_participant": self.con_participant,
            "status": self.status.value,
            "messages": self.dialogue,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "takeaways": self.takeaways,
            "error": self.error
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
```

### 3. Domain Services (`src/shared/debate/domain/services.py`)

Add domain validation rules:

```python
from typing import List
from .entities import DebateRoom
from .value_objects import RoomStatus, RoomId

def validate_room_configuration(
    pro_participant: str,
    con_participant: str,
    max_retries: int,
    max_concurrency: int
) -> None:
    """Validate debate room configuration."""
    if not pro_participant or not isinstance(pro_participant, str):
        raise ValueError("pro_participant must be a non-empty string")
    if not con_participant or not isinstance(con_participant, str):
        raise ValueError("con_participant must be a non-empty string")
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if not (0 <= max_concurrency <= 4):
        raise ValueError("max_concurrency must be 0-4")

def categorize_error(error_message: str) -> str:
    """Categorize error type for reporting."""
    error_lower = error_message.lower()
    if "regex" in error_lower or "re.error" in error_lower:
        return "Regex/Pattern Error"
    elif "timeout" in error_lower or "timed out" in error_lower:
        return "Timeout"
    elif "json" in error_lower or "parse" in error_lower:
        return "JSON Parsing Error"
    elif "llm" in error_lower or "api" in error_lower:
        return "LLM/API Error"
    else:
        return "Other Error"
```

### 4. Package Structure

Create proper package structure with `__init__.py` files:

```python
# src/shared/debate/__init__.py
"""Shared debate framework for product committee and document debate."""

# src/shared/debate/domain/__init__.py
"""Domain layer - pure business logic with no external dependencies."""
from .value_objects import RoomId, RunId, Speaker, RoomStatus
from .entities import DebateMessage, Verdict, DebateRoom
from .services import validate_room_configuration, categorize_error

__all__ = [
    "RoomId", "RunId", "Speaker", "RoomStatus",
    "DebateMessage", "Verdict", "DebateRoom",
    "validate_room_configuration", "categorize_error"
]
```

## Testing Requirements

Create comprehensive unit tests:

```python
# tests/unit/shared/debate/domain/test_value_objects.py
import pytest
from src.shared.debate.domain.value_objects import RoomId, RunId, Speaker, RoomStatus

def test_room_id_validation():
    with pytest.raises(ValueError):
        RoomId("")
    with pytest.raises(ValueError):
        RoomId(123)

def test_run_id_generation():
    run_id = RunId.generate("test question")
    assert run_id.value.startswith("RUN_")
    assert "test-question" in run_id.value

# tests/unit/shared/debate/domain/test_entities.py
import pytest
from src.shared.debate.domain.entities import DebateRoom, DebateMessage, Verdict
from src.shared.debate.domain.value_objects import RoomId, Speaker, RoomStatus

def test_debate_room_is_successful():
    room = DebateRoom(
        room_id=RoomId("test"),
        pro_participant="TPM",
        con_participant="CPO",
        status=RoomStatus.SUCCESS,
        messages=[],
        verdict=Verdict(winner=Speaker.PRO, explanation="Test")
    )
    assert room.is_successful is True
```

## Acceptance Criteria

- [ ] All domain entities use `@dataclass` (no Pydantic)
- [ ] Zero external dependencies in domain layer (only `typing`, `dataclasses`, `enum`, `json`, `re`, `datetime`)
- [ ] All unit tests pass without mocks
- [ ] Domain logic is testable in isolation
- [ ] `RoomId`, `RunId`, `Speaker`, `RoomStatus` value objects implemented
- [ ] `DebateMessage`, `Verdict`, `DebateRoom` entities implemented
- [ ] Domain validation rules implemented

## Files to Create

1. `src/shared/debate/__init__.py`
2. `src/shared/debate/domain/__init__.py`
3. `src/shared/debate/domain/value_objects.py`
4. `src/shared/debate/domain/entities.py`
5. `src/shared/debate/domain/services.py`
6. `tests/unit/shared/debate/domain/test_value_objects.py`
7. `tests/unit/shared/debate/domain/test_entities.py`

## Notes

- **DO NOT use Pydantic** in the domain layer
- **DO NOT import from other layers** - domain must be self-contained
- Use `frozen=True` for value objects to ensure immutability
- Keep business logic in entities (properties, methods)
- Domain services should only contain validation/rules that don't naturally fit in entities

## Next Steps

After completing this work package:
1. Run `pytest tests/unit/shared/debate/domain/` to verify all tests pass
2. Review code for any external dependencies
3. Commit changes with message "feat: implement shared debate domain layer (WP01)"
4. Move to WP02 (Port Interfaces and Application Layer)
