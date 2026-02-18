# Research: Product Committee Clean Architecture Refactoring

**Feature**: 017-product-committee-clean-architecture-refactoring
**Date**: 2025-02-18
**Status**: Complete

## Overview

This document captures research findings and decisions for implementing Clean Architecture principles in the Deb8flow product committee refactoring.

---

## Research Topic 1: Clean Architecture in Python

### Question
What are the best practices for implementing Clean Architecture/Hexagonal Architecture in Python 3.12+?

### Findings

**Python-Specific Patterns for Clean Architecture:**

1. **Domain Layer (Entities)**
   - Use `@dataclass` for entities (pure Python, no external dependencies)
   - Use `typing.Protocol` for interfaces (lightweight, no inheritance required)
   - Domain services as regular classes with domain logic

2. **Application Layer (Use Cases & Ports)**
   - Use `typing.Protocol` for port interfaces (not ABC)
   - Use simple dependency injection via constructor parameters
   - No need for DI frameworks (injector, dependency_injector) - overkill for CLI tool

3. **Infrastructure Layer (Adapters)**
   - Implement protocol interfaces in concrete classes
   - Keep external dependencies (LLM clients, file I/O) contained here

4. **Key Decision: Protocol vs ABC**
   ```python
   # GOOD: Protocol (preferred)
   from typing import Protocol

   class DebateExecutor(Protocol):
       async def execute(self, request: DebateRequest) -> DebateResult: ...

   # AVOID: ABC (heavier, requires inheritance)
   from abc import ABC, abstractmethod

   class DebateExecutor(ABC):
       @abstractmethod
       async def execute(self, request: DebateRequest) -> DebateResult: ...
   ```

**Decision**: Use `typing.Protocol` for all port interfaces. It's:
- More Pythonic (duck typing)
- Easier to test (any object matching the signature works)
- No inheritance required
- Better IDE support (structural subtyping)

### References
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [Clean Architecture in Python (krzysztofzuraw.com)](https://krzysztofzuraw.com/blog/2020/clean-architecture-in-python.html)

---

## Research Topic 2: Shared Framework Design

### Question
How to structure a shared kernel between `product_committee.py` and `document_debate_cli.py`?

### Findings

**DDD Shared Kernel Pattern:**

The Shared Kernel is the minimal part of the domain model that multiple Bounded Contexts agree on.

**Key Principles:**
1. **Minimize shared code** - only share what truly must be consistent
2. **Explicit boundaries** - clear API contracts between modules
3. **Independent evolution** - changes in one context don't break the other

**Applying to Deb8flow:**

```
Shared Kernel (src/shared/debate/)
├── Domain: Common debate concepts
│   ├── DebateRoom (room_id, participants, status)
│   ├── Verdict (winner, explanation)
│   ├── Speaker (PRO, CON, judge)
│   └── DebateMessage (speaker, content, stage)
│
├── Application Ports: Common interfaces
│   ├── DebateExecutor (execute debate room)
│   ├── ReportGenerator (generate markdown reports)
│   └── FileStorage (save/load artifacts)
│
└── Infrastructure: Shared implementations
    ├── Retry logic (exponential backoff)
    ├── Error handling (error categorization)
    └── Logging configuration
```

**Separate Contexts:**
- `src/committee/` - Product committee orchestration (4 rooms, metadata, final report)
- `src/document_debate/` - Single document debate (2 participants, one debate)

**Decision**: Shared Kernel pattern with these boundaries:
- **Domain entities** in shared kernel (DebateRoom, Verdict, Message)
- **Port interfaces** in shared kernel (DebateExecutor, etc.)
- **Use cases** separate per context (RunCommittee vs RunSingleDebate)
- **Adapters** separate per context (committee CLI vs debate CLI)

### References
- [Domain-Driven Design Shared Kernel (martinfowler.com)](https://martinfowler.com/bliki/SharedKernel.html)

---

## Research Topic 3: Snapshot Testing Strategy

### Question
Which snapshot testing approach is best for Python CLI tools?

### Findings

**Options Evaluated:**

1. **snapshottest**
   - Pros: Mature, pytest plugin, inline snapshots
   - Cons: Requires `_snapshot` fixture, slower for multiple snapshots

2. **syrupy**
   - Pros: Faster, better diff output, pytest plugin
   - Cons: Newer, less adoption

3. **Custom assertion helpers**
   - Pros: Full control, no dependencies
   - Cons: More maintenance, reinventing the wheel

**Decision**: Use **syrupy** for snapshot testing

**Rationale:**
- pytest-native (no special fixtures needed)
- Fast and reliable
- Excellent diff output for debugging
- Easy to update snapshots (`--snapshot-update`)
- No additional dependencies beyond pytest

**Snapshot Strategy:**
```python
# tests/snapshots/test_committee_workflow.py
def test_committee_generates_expected_output(snapshot):
    result = run_committee_cli(
        prd="test_prd.txt",
        question="Test question",
        max_concurrency=0
    )

    # Snapshot entire output directory
    assert snapshot == result.output_dir

    # Or snapshot individual files
    assert snapshot == result.final_report
    assert snapshot == result.conclusion
    assert snapshot == result.metadata
```

**Snapshot Files Structure:**
```
tests/snapshots/test_committee_workflow/
├── test_committee_generates_expected_output/
│   ├── final_report.md
│   ├── conclusion.md
│   └── metadata.json
```

### References
- [syrupy documentation](https://docs.tophat.com/work/topics/syrupy/)

---

## Research Topic 4: Async vs Sync Consolidation

### Question
How to eliminate sync/async duplication in debate execution?

### Findings

**Current Problem:**
- `run_debate_room_with_retry()` - synchronous (subprocess.run)
- `run_debate_room_async()` - asynchronous (asyncio subprocess)
- ~200 lines of duplicated logic

**Best Practices for Python CLI Tools:**

1. **Use asyncio internally, provide sync wrapper externally**
   - Core execution is async (supports concurrency naturally)
   - Entry point (CLI) can be sync wrapper calling `asyncio.run()`

2. **Subprocess execution:**
   ```python
   # Async subprocess (preferred)
   process = await asyncio.create_subprocess_exec(
       *cmd,
       stdout=asyncio.subprocess.PIPE,
       stderr=asyncio.subprocess.PIPE
   )
   stdout, stderr = await process.communicate()
   ```

3. **File I/O:**
   ```python
   # Use asyncio.to_thread for blocking file operations
   content = await asyncio.to_thread(Path.read_text, path)
   await asyncio.to_thread(Path.write_text, path, content)
   ```

**Decision:**
- **Core execution**: Pure asyncio (single code path)
- **CLI entry point**: Sync wrapper using `asyncio.run()`
- **Eliminate**: Separate sync implementation

**Migration Strategy:**
1. Create async-only `execute_debate_room()`
2. Replace sync implementation with `asyncio.run(execute_debate_room(...))`
3. Remove duplicate sync code
4. Update all call sites to use async

### References
- [ asyncio documentation](https://docs.python.org/3/library/asyncio.html)

---

## Research Topic 5: File I/O Best Practices

### Question
How to handle file I/O in a concurrent debate execution system?

### Findings

**Problem:**
- 4 debate rooms running in parallel
- Each room writes JSON output file
- Intermediate reports after each room
- Final report after all rooms complete

**Options:**

1. **Blocking file I/O (current)**
   - Problem: Blocks event loop during write
   - Acceptable for small files, but not ideal

2. **asyncio.to_thread**
   - Offloads blocking I/O to thread pool
   - Keeps event loop unblocked
   - Recommended for file operations

3. **aiofiles**
   - True async file I/O
   - Additional dependency
   - Overkill for this use case

**Decision**: Use `asyncio.to_thread` for file operations

**Implementation Pattern:**
```python
# Save intermediate report (non-blocking)
async def save_intermediate_report(
    output_dir: Path,
    rooms: List[DebateRoom]
) -> None:
    report = generate_markdown(rooms)

    # Non-blocking write
    await asyncio.to_thread(
        output_dir.joinpath("final_report.md").write_text,
        report,
        encoding="utf-8"
    )
```

**Concurrency Considerations:**
- Multiple rooms writing to same directory = OK (different files)
- Multiple processes writing same file = BAD (need file locks)
- Solution: Each room writes unique file, no conflicts

### References
- [asyncio.to_thread documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

---

## Summary of Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Domain layer | Plain `@dataclass` | No external dependencies, testable |
| Port interfaces | `typing.Protocol` | Pythonic, duck typing, no inheritance |
| DI approach | Constructor injection | Simple, no DI framework needed |
| Shared framework | DDD Shared Kernel pattern | Minimal shared code, explicit boundaries |
| Snapshot testing | syrupy pytest plugin | Fast, reliable, excellent diffs |
| Execution model | Pure asyncio, sync wrapper | Single code path, no duplication |
| File I/O | `asyncio.to_thread` | Non-blocking, no new dependencies |
| Validation | Pydantic on boundaries only | Clean domain, validated I/O |

---

## Next Steps

With research complete, proceed to:
1. **Phase 1 Design**: Define data models, contracts, and quickstart guide
2. **Phase 2 Task Generation**: Create work packages for implementation
