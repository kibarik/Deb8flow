# Quick Start: Product Committee Refactoring

**Feature**: 017-product-committee-clean-architecture-refactoring
**Last Updated**: 2025-02-18

## Overview

This guide helps developers understand and work with the refactored product committee codebase using Clean Architecture principles.

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  product_committee.py (~200 lines)                          │
│  - Parse arguments (Pydantic validation)                    │
│  - Invoke RunProductCommittee use case                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  src/committee/application/run_committee.py                 │
│  - RunProductCommittee use case                             │
│  - Orchestrates debate rooms                                │
│  - Coordinates via ports (interfaces)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      Domain Layer        │    │   Shared Debate Core     │
│  src/committee/domain/   │    │  src/shared/debate/      │
│  - CommitteeRun          │    │  - DebateRoom            │
│  - CommitteeReport       │    │  - Verdict               │
│  (business rules)        │    │  - DebateMessage         │
└──────────────────────────┘    └──────────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  src/shared/debate/infrastructure/                          │
│  - CliDebateExecutor (calls document_debate_cli.py)        │
│  - LocalFileStorage (saves artifacts)                       │
│  - Retry logic (exponential backoff)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Ports and Adapters (Hexagonal Architecture)

**Ports (Interfaces)**: Define what the application needs
```python
# src/shared/debate/application/ports.py
from typing import Protocol

class DebateExecutor(Protocol):
    async def execute(self, request: DebateRequest) -> DebateRoom:
        """Execute a debate room."""
        ...
```

**Adapters (Implementations)**: Provide what the interface defines
```python
# src/shared/debate/infrastructure/executors/cli_executor.py
class CliDebateExecutor:
    async def execute(self, request: DebateRequest) -> DebateRoom:
        # Calls document_debate_cli.py as subprocess
        ...
```

### 2. Domain Isolation

The domain layer has **zero** external dependencies:
- No Pydantic
- No LLM clients
- No file I/O
- Pure business logic

```python
# src/committee/domain/entities.py
from dataclasses import dataclass

@dataclass
class CommitteeRun:
    run_id: RunId
    question: str
    rooms: List[DebateRoom]

    @property
    def tpm_wins(self) -> int:
        """Business rule: count TPM victories."""
        return sum(1 for r in self.successful_rooms
                   if r.verdict.winner == Speaker.PRO)
```

### 3. Dependency Flow

```
Infrastructure → Application → Domain
    ↓                 ↓              ↓
  I/O files        Use cases    Business rules
```

**Critical Rule**: Domain never depends on Infrastructure!

---

## Module Structure

### Shared Debate Framework (`src/shared/debate/`)

```
src/shared/debate/
├── domain/
│   ├── entities.py      # DebateRoom, Verdict, DebateMessage
│   ├── value_objects.py # RoomId, RunId, Speaker, RoomStatus
│   └── services.py      # Domain rules, validation
│
├── application/
│   ├── ports.py         # DebateExecutor, ReportGenerator, FileStorage
│   └── use_cases/
│       ├── execute_debate.py
│       └── run_session.py
│
└── infrastructure/
    ├── executors/
    │   └── cli_executor.py    # Calls document_debate_cli.py
    ├── storage/
    │   └── local_storage.py   # File I/O operations
    └── retry.py              # Exponential backoff
```

### Committee Module (`src/committee/`)

```
src/committee/
├── domain/
│   └── entities.py      # CommitteeRun, CommitteeReport
│
├── application/
│   └── run_committee.py # RunProductCommittee use case
│
└── adapters/
    ├── cli.py           # CLI argument parsing
    └── reports/
        ├── final_report.py
        └── conclusion.py
```

---

## Common Tasks

### Running the Product Committee

```bash
# Basic usage
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question 'заработает ли этот проект 100 млн за 2 дня' \
  --max-concurrency 0 \
  --language 'русский кратко, в формате буллетлистов'

# With verbose output
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question "Test question" \
  --verbose

# Sequential execution
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question "Test question" \
  --max-concurrency 1
```

### Adding a New Debate Room Type

```python
# 1. Define new role in prompts/roles/{role}.txt
# 2. Add to ROOM_ORDER in src/committee/application/run_committee.py

ROOM_ORDER = ["cpo", "cfo", "cto", "bdm", "legal"]  # Add "legal"
```

### Writing Tests

```python
# Domain tests (no external dependencies)
def test_committee_run_tpm_wins():
    run = CommitteeRun(
        run_id=RunId("test"),
        question="Test",
        rooms=[room_with_tpm_win, room_with_opponent_win]
    )
    assert run.tpm_wins == 1

# Integration tests (with mock adapters)
async def test_execute_committee_room():
    mock_executor = MockDebateExecutor()
    result = await execute_room(mock_executor, request)
    assert result.status == RoomStatus.SUCCESS
```

---

## Migration Progress

### Phase 1A: Domain Layer ✅
- [x] Create `src/shared/debate/domain/` entities
- [x] Define value objects (RoomId, RunId, Speaker, etc.)
- [x] Write domain tests

### Phase 1B: Application Layer ⏳
- [ ] Create port interfaces (`ports.py`)
- [ ] Implement `ExecuteDebate` use case
- [ ] Create CLI executor adapter

### Phase 1C: Committee Module ⏳
- [ ] Create `src/committee/domain/` entities
- [ ] Implement `RunProductCommittee` use case

### Phase 1D: Report Generation ⏳
- [ ] Extract report logic to `src/committee/adapters/reports/`
- [ ] Write snapshot tests

### Phase 1E: CLI Migration ⏳
- [ ] Refactor `product_committee.py`
- [ ] Validate all tests pass

### Phase 1F: Document Debate Migration ⏳
- [ ] Migrate `document_debate_cli.py` to use shared framework

---

## Testing Strategy

### Unit Tests (Domain Layer)
```bash
# Test domain entities in isolation
pytest tests/unit/shared/debate/domain/
pytest tests/unit/committee/domain/
```

### Integration Tests (Use Cases)
```bash
# Test use cases with mock adapters
pytest tests/integration/test_committee_workflow.py
```

### Snapshot Tests (CLI Output)
```bash
# Generate/update snapshots
pytest tests/snapshots/ --snapshot-update

# Verify against snapshots
pytest tests/snapshots/
```

### E2E Tests (Full Workflow)
```bash
# Test complete committee workflow
pytest tests/test_product_committee.py
```

---

## Troubleshooting

### Issue: Import errors after refactoring

**Solution**: Ensure module structure matches plan.md
```bash
# Verify structure
ls -la src/shared/debate/
ls -la src/committee/
```

### Issue: Tests failing

**Solution**: Check test imports and mock adapters
```python
# Update imports
from src.shared.debate.domain.entities import DebateRoom
from src.committee.domain.entities import CommitteeRun
```

### Issue: Snapshot tests mismatch

**Solution**: Update snapshots if output format changed intentionally
```bash
pytest tests/snapshots/ --snapshot-update
```

---

## Further Reading

- [Clean Architecture by Robert C. Martin](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [DDD Shared Kernel](https://martinfowler.com/bliki/SharedKernel.html)
- [Python typing.Protocol](https://peps.python.org/pep-0544/)

---

## Questions?

- Check [plan.md](./plan.md) for detailed architecture
- Check [data-model.md](./data-model.md) for entity definitions
- Check [contracts/](./contracts/) for interface specifications
- Check [research.md](./research.md) for technical decisions
