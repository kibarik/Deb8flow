# Implementation Plan: Product Committee Clean Architecture Refactoring

**Branch**: `017-product-committee-clean-architecture-refactoring` | **Date**: 2025-02-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/017-product-committee-clean-architecture-refactoring/spec.md`

## Summary

Refactor the 1970-line `product_committee.py` monolith into a clean, maintainable architecture using **Modular Hexagonal Hybrid** design. Extract shared debate framework (`src/shared/debate/`) that both `product_committee.py` and `document_debate_cli.py` can use. Migrate incrementally from core-to-edges: domain entities → debate execution abstraction → report generation → CLI/orchestration. Maintain 100% functional equivalence with parallel testing approach using snapshot tests for CLI validation.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- Existing: `python-docx`, `langgraph`, `langchain` (no changes)
- New: `pydantic` (for CLI/config/IO validation only, NOT in domain layer)
- No DI framework (use simple dependency injection)
- Domain layer uses plain dataclasses (no external dependencies)

**Storage**: File system (JSON logs, markdown reports)
- Output directory: `committee_output/{run-id}/`
- Files: `metadata.json`, `{room_id}.json`, `{room_id}_dialogue.json`, `final_report.md`, `conclusion.md`

**Testing**:
- Framework: `pytest` (existing)
- Approach: Parallel test & refactor with snapshot testing
- Test types: Unit tests for domain, integration tests for use cases, snapshot tests for CLI output
- Focus: Functional equivalence validation

**Target Platform**: Cross-platform (Linux, macOS, Windows) - CLI utility
**Project Type**: Single project with modular architecture (refactoring existing codebase)

**Performance Goals**:
- Parallel execution (max-concurrency=0) completes in ≤60% of sequential time
- No performance degradation from abstraction layers
- File I/O must not block debate execution

**Constraints**:
- Must preserve all existing CLI arguments and behavior
- Output file structure must remain unchanged
- All existing tests must pass without modification
- Code reduction: from ~1970 lines to <500 lines per module
- Zero code duplication >10 lines

**Scale/Scope**:
- Current: 1 monolithic file (~1970 lines)
- Target: ~10-15 modules across 3 layers (domain, application, adapter)
- Files: 4 debate rooms × 2 JSON files + 2 markdown reports + metadata
- Integration points: 2 CLI tools (product_committee, document_debate)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Technical Standards Compliance

| Standard | Status | Notes |
|----------|--------|-------|
| Python 3.12+ | ✅ PASS | Project already uses Python 3.12+ |
| pytest required | ✅ PASS | Existing test suite uses pytest; will add tests during refactoring |
| Cross-platform | ✅ PASS | No platform-specific changes; CLI remains portable |
| pip installable | ✅ PASS | No changes to package structure |

### Code Quality Compliance

| Standard | Status | Notes |
|----------|--------|-------|
| Spec-driven development | ✅ PASS | Working from spec.md |
| TDD | ✅ PASS | Parallel test & refactor approach |
| Minimal dependencies | ✅ PASS | Only adding Pydantic for boundaries (not domain) |
| Self-documenting code | ✅ PASS | Clean architecture with clear module responsibilities |

### Documentation Requirements

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Feature documentation in `docs/` | ⚠️ TODO | Create `docs/product-committee-refactoring.md` during implementation |
| Architecture documentation | ⚠️ TODO | Document Modular Hexagonal Hybrid approach |

**GATE STATUS**: ✅ PASS - All constitution requirements met or planned

**Re-check after Phase 1**: Verify architecture documentation and clean abstractions don't violate "minimal dependencies" principle

## Project Structure

### Documentation (this feature)

```
kitty-specs/017-product-committee-clean-architecture-refactoring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── debate-executor-port.yaml
│   ├── report-generator-port.yaml
│   └── file-storage-port.yaml
└── tasks.md             # Phase 2 output (created by /spec-kitty.tasks)
```

### Source Code (repository root)

```
src/
├── shared/
│   └── debate/                    # Shared debate framework (NEW)
│       ├── __init__.py
│       ├── domain/                # Domain layer (no external deps)
│       │   ├── __init__.py
│       │   ├── entities.py        # DebateSession, DebateRoom, Verdict, etc.
│       │   ├── value_objects.py   # RoomId, RunId, Speaker, etc.
│       │   └── services.py        # Domain rules, validation logic
│       ├── application/           # Application layer
│       │   ├── __init__.py
│       │   ├── ports.py           # Interfaces: DebateExecutor, ReportGenerator, FileStorage
│       │   └── use_cases/         # Use case implementations
│       │       ├── __init__.py
│       │       ├── execute_debate.py
│       │       ├── generate_report.py
│       │       └── run_session.py
│       └── infrastructure/        # Infrastructure (implementation details)
│           ├── __init__.py
│           ├── executors/         # Debate execution adapters
│           │   ├── __init__.py
│           │   └── cli_executor.py  # Calls document_debate_cli.py
│           ├── storage/           # File storage adapters
│           │   ├── __init__.py
│           │   └── local_storage.py
│           └── retry.py           # Retry logic with exponential backoff
│
├── committee/                     # Product committee specific (NEW)
│   ├── __init__.py
│   ├── domain/                    # Committee-specific entities
│   │   ├── __init__.py
│   │   └── entities.py           # CommitteeRun, CommitteeRoom, CommitteeReport
│   ├── application/              # Committee use cases
│   │   ├── __init__.py
│   │   └── run_committee.py      # RunProductCommittee use case
│   └── adapters/                 # Committee adapters
│       ├── __init__.py
│       ├── cli.py                # CLI argument parsing and orchestration
│       └── reports/              # Report generation
│           ├── __init__.py
│           ├── final_report.py
│           └── conclusion.py
│
└── document_debate/               # Document debate refactoring (MINIMAL)
    └── adapters/
        └── cli.py                # Migrate to use shared framework

# Refactored CLI entry points (minimal changes)
product_committee.py               # Reduced to ~200 lines (CLI + orchestration)
document_debate_cli.py             # Reduced to use shared framework

# Tests
tests/
├── unit/
│   ├── shared/
│   │   └── debate/
│   │       ├── domain/
│   │       │   ├── test_entities.py
│   │       │   └── test_services.py
│   │       └── application/
│   │           └── test_use_cases.py
│   └── committee/
│       ├── domain/
│       └── application/
├── integration/
│   ├── test_committee_workflow.py
│   └── test_debate_workflow.py
└── snapshots/
    ├── test_committee_output/
    │   ├── final_report.md
    │   ├── conclusion.md
    │   └── metadata.json
    └── test_debate_output/
        └── ...
```

**Structure Decision**: **Modular monolith with shared core**

Rationale:
- **Shared debate framework** (`src/shared/debate/`) eliminates duplication between product_committee and document_debate
- **Domain layer** uses plain dataclasses (no Pydantic) for purity and testability
- **Application layer** contains use cases and port interfaces
- **Adapter layer** implements ports (CLI executor, file storage, report generators)
- **Committee-specific** logic extends shared framework without modifying core
- **Clear boundaries**: Domain → Application → Infrastructure → CLI

Migration order:
1. Create `src/shared/debate/` domain entities
2. Implement debate execution abstraction
3. Build report generation system
4. Refactor CLI and orchestration layer

## Complexity Tracking

*No violations - refactoring reduces complexity*

| Before | After | Improvement |
|--------|-------|-------------|
| 1 file, ~1970 lines | ~10 modules, <500 lines each | Clear responsibilities |
| Sync/async code duplication | Single execution path | Zero duplication |
| Mixed concerns | Layered architecture | Clear boundaries |
| Untestable domain logic | Pure domain with dataclasses | 100% testable |

## Phase 0: Research & Decision Making

### Research Tasks

1. **Clean Architecture in Python**
   - Research: Best practices for implementing Clean Architecture/Hexagonal in Python
   - Decision: Use plain dataclasses for domain, protocol classes for ports
   - Output: Pattern reference for `src/shared/debate/`

2. **Shared Framework Design**
   - Research: How to structure shared kernel between product_committee and document_debate
   - Decision: Shared Kernel pattern with explicit boundaries
   - Output: Interface contracts in `contracts/`

3. **Snapshot Testing Strategy**
   - Research: Snapshot testing tools for Python (snapshottest, syrupy, or custom)
   - Decision: Evaluate and choose snapshot testing approach
   - Output: Snapshot test configuration

4. **Async vs Sync Consolidation**
   - Research: Best practice for eliminating sync/async duplication
   - Decision: Use asyncio for everything, provide sync wrapper if needed
   - Output: Execution model design

5. **File I/O Best Practices**
   - Research: Async file I/O in Python for concurrent report writing
   - Decision: Use asyncio.to_thread for file operations to avoid blocking
   - Output: I/O patterns for infrastructure layer

### Research Output

See [research.md](./research.md) for detailed findings and decisions.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and state transitions.

### API Contracts

See [contracts/](./contracts/) for interface definitions:
- `debate-executor-port.yaml` - Debate execution interface
- `report-generator-port.yaml` - Report generation interface
- `file-storage-port.yaml` - File storage interface

### Quick Start

See [quickstart.md](./quickstart.md) for developer onboarding guide.

## Migration Strategy

### Incremental Module Extraction

**Phase 1A: Domain Layer (Shared Core)**
1. Create `src/shared/debate/domain/` entities
2. Extract data structures from product_committee.py
3. Write unit tests for all domain entities
4. Validate: All domain tests pass

**Phase 1B: Application Layer (Use Cases)**
1. Create `src/shared/debate/application/ports.py` with interfaces
2. Implement `ExecuteDebate` use case
3. Create `src/shared/debate/infrastructure/executors/cli_executor.py`
4. Write integration tests
5. Validate: Use case tests pass with mock adapters

**Phase 1C: Committee Module**
1. Create `src/committee/domain/` entities extending shared framework
2. Implement `RunProductCommittee` use case
3. Create committee-specific adapters
4. Write integration tests
5. Validate: Committee workflow tests pass

**Phase 1D: Report Generation**
1. Extract report logic into `src/committee/adapters/reports/`
2. Create report generator classes
3. Write snapshot tests for output
4. Validate: Snapshot tests match current output

**Phase 1E: CLI Migration**
1. Refactor `product_committee.py` to use new architecture
2. Preserve all CLI arguments
3. Write end-to-end CLI tests
4. Validate: All existing tests pass, snapshot tests match

**Phase 1F: Document Debate Migration**
1. Migrate `document_debate_cli.py` to use shared framework
2. Validate: No functional changes, tests pass

### Rollback Strategy

Each phase is independently revertable:
- Git commits per phase
- Old code remains until new code is validated
- Feature flags available if needed

## Constitution Check (Post-Design)

*Re-validating after Phase 1 design*

| Standard | Status | Notes |
|----------|--------|-------|
| Minimal dependencies | ✅ PASS | Only Pydantic on boundaries, domain is pure |
| Self-documenting code | ✅ PASS | Clear module names, typed entities |
| Spec-driven | ✅ PASS | All design from spec.md |

**GATE STATUS**: ✅ PASS - Architecture aligns with constitution principles

---

## Next Steps

After Phase 0 (research) and Phase 1 (design) are complete, run `/spec-kitty.tasks` to generate work packages for implementation.
