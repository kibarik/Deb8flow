# Data Model: Product Committee Clean Architecture

**Feature**: 017-product-committee-clean-architecture-refactoring
**Date**: 2025-02-18

## Overview

This document defines the data model for the refactored product committee system, including entities, value objects, and their relationships following Clean Architecture principles.

---

## Architecture Layers

### Domain Layer (Pure, No External Dependencies)

All entities use `dataclass` with standard library types only.

### Application Layer (Orchestration)

Use cases and port interfaces using `typing.Protocol`.

### Adapter Layer (External Integration)

Pydantic models for CLI/config validation only.

---

## Shared Debate Framework (src/shared/debate/)

### Value Objects

#### RoomId
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RoomId:
    """Immutable identifier for a debate room."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("RoomId must be a non-empty string")
```

**Usage**: `TPM_vs_CPO`, `TPM_vs_CFO`, `TPM_vs_CTO`, `TPM_vs_BDM`

#### RunId
```python
@dataclass(frozen=True)
class RunId:
    """Immutable identifier for a committee run."""
    value: str

    @classmethod
    def generate(cls, question: str, manual_id: str | None = None) -> "RunId":
        if manual_id:
            return cls(manual_id)

        import re
        from datetime import datetime, timezone

        words = question.strip().split()[:5]
        slug = "-".join(words).lower()
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return cls(f"RUN_{timestamp}_{slug}")
```

#### Speaker
```python
from enum import Enum

class Speaker(Enum):
    """Participant roles in a debate."""
    PRO = "PRO"       # TPM (Technical Project Manager)
    CON = "CON"       # CPO/CFO/CTO/BDM (opponent)
    JUDGE = "JUDGE"   # Judge determines winner
```

#### RoomStatus
```python
class RoomStatus(Enum):
    """Execution status of a debate room."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # Missing role prompt
```

### Domain Entities

#### DebateMessage
```python
from typing import Optional

@dataclass
class DebateMessage:
    """A single message in a debate dialogue."""
    speaker: Speaker
    content: str
    stage: str  # "opening", "rebuttal", "counter", "final", "verdict"
    timestamp: str  # ISO 8601
    validated: bool = False  # Whether fact-checked

    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker.value,
            "content": self.content,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "validated": self.validated
        }
```

#### Verdict
```python
@dataclass
class Verdict:
    """Judge's decision for a debate room."""
    winner: Speaker
    explanation: str
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> dict:
        return {
            "winner": self.winner.value,
            "explanation": self.explanation,
            "confidence": self.confidence
        }
```

#### DebateRoom
```python
from typing import List, Optional

@dataclass
class DebateRoom:
    """A single debate room between two participants."""
    room_id: RoomId
    pro_participant: str  # e.g., "TPM"
    con_participant: str  # e.g., "CPO"
    status: RoomStatus
    messages: List[DebateMessage]
    verdict: Optional[Verdict] = None
    takeaways: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.takeaways is None:
            self.takeaways = []

    @property
    def is_successful(self) -> bool:
        return self.status == RoomStatus.SUCCESS and self.verdict is not None

    @property
    def dialogue(self) -> List[dict]:
        return [msg.to_dict() for msg in self.messages]

    def to_json(self) -> str:
        import json
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

---

## Committee-Specific Entities (src/committee/)

### Domain Entities

#### CommitteeRun
```python
@dataclass
class CommitteeRun:
    """A complete product committee session with multiple debate rooms."""
    run_id: RunId
    question: str
    prd_path: str
    model: Optional[str]
    language: Optional[str]
    max_retries: int
    max_concurrency: int
    rooms: List[DebateRoom]
    start_time: str
    end_time: Optional[str] = None

    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if not (0 <= self.max_concurrency <= 4):
            raise ValueError("max_concurrency must be 0-4")

    @property
    def is_complete(self) -> bool:
        return self.end_time is not None

    @property
    def successful_rooms(self) -> List[DebateRoom]:
        return [r for r in self.rooms if r.is_successful]

    @property
    def failed_rooms(self) -> List[DebateRoom]:
        return [r for r in self.rooms if r.status == RoomStatus.FAILED]

    @property
    def tpm_wins(self) -> int:
        return sum(1 for r in self.successful_rooms
                   if r.verdict and r.verdict.winner == Speaker.PRO)

    @property
    def opponent_wins(self) -> int:
        return len(self.successful_rooms) - self.tpm_wins
```

#### CommitteeReport
```python
@dataclass
class CommitteeReport:
    """Generated report from a committee run."""
    run: CommitteeRun
    final_report_markdown: str
    conclusion_markdown: str

    def save(self, output_dir: Path) -> None:
        """Save report files to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save final report
        final_path = output_dir / "final_report.md"
        final_path.write_text(self.final_report_markdown, encoding="utf-8")

        # Save conclusion
        conclusion_path = output_dir / "conclusion.md"
        conclusion_path.write_text(self.conclusion_markdown, encoding="utf-8")
```

### Metadata Entity

#### CommitteeMetadata
```python
@dataclass
class CommitteeMetadata:
    """Metadata for tracking committee execution."""
    run_id: str
    prd_path: str
    question: str
    model: str
    language: Optional[str]
    start_time: str
    end_time: Optional[str]
    room_statuses: dict  # {"tpm_cpo": "success", ...}
    max_retries: int
    max_concurrency: int
    warning_flags: dict
    errors: List[dict]

    def to_json(self) -> str:
        import json
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_run(cls, run: CommitteeRun, errors: List[dict]) -> "CommitteeMetadata":
        room_statuses = {
            f"tpm_{room.con_participant.lower()}": room.status.value
            for room in run.rooms
        }

        return cls(
            run_id=run.run_id.value,
            prd_path=run.prd_path,
            question=run.question,
            model=run.model or "default",
            language=run.language,
            start_time=run.start_time,
            end_time=run.end_time,
            room_statuses=room_statuses,
            max_retries=run.max_retries,
            max_concurrency=run.max_concurrency,
            warning_flags={
                "prd_too_short": False,
                "question_too_short": False,
                "some_rooms_failed": len(run.failed_rooms) > 0
            },
            errors=errors
        )
```

---

## State Transitions

### Debate Room Lifecycle

```
PENDING → IN_PROGRESS → SUCCESS
                  ↘               ↘
                   FAILED          (has verdict)
```

**Transition Rules:**
- `PENDING → IN_PROGRESS`: Room execution starts
- `IN_PROGRESS → SUCCESS`: Judge verdict received, dialogue captured
- `IN_PROGRESS → FAILED`: Error during execution (timeout, LLM error, etc.)
- `PENDING → SKIPPED`: Role prompt file missing

### Committee Run Lifecycle

```
CREATED → RUNNING → COMPLETED
                ↘
              PARTIAL_FAILURE (some rooms failed)
                ↘
              TOTAL_FAILURE (all rooms failed)
```

---

## Relationships

```
CommitteeRun (1)
    ├── RunId (1)
    ├── DebateRoom (4)
    │   ├── RoomId (1)
    │   ├── DebateMessage (*)
    │   ├── Verdict (0..1)
    │   └── List[str] takeaways
    └── CommitteeReport (1)

CommitteeMetadata (1) ← derived from CommitteeRun
```

---

## Adapter Layer Models (Pydantic)

### CLI Input Models

```python
# src/committee/adapters/cli.py
from pydantic import BaseModel, Field, field_validator

class CommitteeCliInput(BaseModel):
    """Validated CLI input for product committee."""
    prd: str = Field(..., description="Path to PRD document")
    question: str = Field(..., min_length=1, description="Committee question")
    model: str | None = Field(None, description="LLM model name")
    max_retries: int = Field(2, ge=0, description="Max retry attempts")
    max_concurrency: int = Field(2, ge=0, le=4, description="Max parallel rooms")
    output_dir: str = Field("./committee_output", description="Output directory")
    roles_dir: str = Field("prompts/roles/", description="Role prompts directory")
    run_id: str | None = Field(None, description="Manual run ID")
    language: str | None = Field(None, description="Language setting")
    verbose: bool = Field(False, description="Verbose logging")
    quiet: bool = Field(False, description="Quiet mode")

    @field_validator("prd")
    def prd_must_exist(cls, v):
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"PRD file not found: {v}")
        return v

    @field_validator("question")
    def question_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
```

---

## Validation Rules

| Entity | Rule | Error |
|--------|------|-------|
| `RoomId` | Must be non-empty string | ValueError |
| `RunId` | Auto-generated if not provided | N/A |
| `CommitteeRun` | `max_retries >= 0` | ValueError |
| `CommitteeRun` | `0 <= max_concurrency <= 4` | ValueError |
| `CommitteeCliInput` | PRD file must exist | Pydantic ValidationError |
| `CommitteeCliInput` | Question must not be empty | Pydantic ValidationError |

---

## Data Flow

```
CLI Input (Pydantic)
    ↓
CommitteeCliInput.validate()
    ↓
CommitteeRun (domain entity)
    ↓
ExecuteDebateRooms (use case)
    ↓
DebateRoom[] (domain entities)
    ↓
GenerateReport (use case)
    ↓
CommitteeReport (domain entity)
    ↓
Save to disk (infrastructure)
```

---

## Index of Entities

| Entity | Layer | File | Mutable |
|--------|-------|------|---------|
| `RoomId` | Domain (VO) | `shared/debate/domain/value_objects.py` | No |
| `RunId` | Domain (VO) | `shared/debate/domain/value_objects.py` | No |
| `Speaker` | Domain (Enum) | `shared/debate/domain/value_objects.py` | No |
| `RoomStatus` | Domain (Enum) | `shared/debate/domain/value_objects.py` | No |
| `DebateMessage` | Domain | `shared/debate/domain/entities.py` | Yes |
| `Verdict` | Domain | `shared/debate/domain/entities.py` | Yes |
| `DebateRoom` | Domain | `shared/debate/domain/entities.py` | Yes |
| `CommitteeRun` | Domain | `committee/domain/entities.py` | Yes |
| `CommitteeReport` | Domain | `committee/domain/entities.py` | Yes |
| `CommitteeMetadata` | Domain | `committee/domain/entities.py` | Yes |
| `CommitteeCliInput` | Adapter (Pydantic) | `committee/adapters/cli.py` | Yes |

---

## Next Steps

With data model defined:
1. Create port interface contracts
2. Generate quickstart guide for developers
3. Proceed to task generation (`/spec-kitty.tasks`)
