# Tasks: Product Committee Clean Architecture Refactoring

**Feature**: 017-product-committee-clean-architecture-refactoring
**Status**: Ready for Implementation
**Generated**: 2025-02-18

## Overview

This document contains grouped work packages (WP) for implementing the product committee clean architecture refactoring. Each work package represents a coherent, deliverable unit of work that can be implemented in a git worktree.

**Migration Strategy**: Core-to-edges incremental extraction
- WP01-WP03: Shared debate framework foundation
- WP04-WP05: Committee-specific implementation
- WP06-WP07: CLI integration and validation
- WP08-WP09: Documentation and testing

**Total Work Packages**: 9

---

## 📦 WP01: Shared Domain Layer

**Description**: Create the shared debate framework domain layer with pure dataclasses and value objects.

**Dependencies**: None

**Files to Create**:
- `src/shared/debate/__init__.py`
- `src/shared/debate/domain/__init__.py`
- `src/shared/debate/domain/value_objects.py` - RoomId, RunId, Speaker, RoomStatus enums
- `src/shared/debate/domain/entities.py` - DebateMessage, Verdict, DebateRoom
- `src/shared/debate/domain/services.py` - Domain validation rules

**Tasks**:
1. Create directory structure `src/shared/debate/domain/`
2. Implement `RoomId` value object (frozen dataclass with validation)
3. Implement `RunId` value object with `generate()` factory method
4. Implement `Speaker` enum (PRO, CON, JUDGE)
5. Implement `RoomStatus` enum (PENDING, IN_PROGRESS, SUCCESS, FAILED, SKIPPED)
6. Implement `DebateMessage` entity (speaker, content, stage, timestamp, validated)
7. Implement `Verdict` entity (winner, explanation, confidence)
8. Implement `DebateRoom` entity with `is_successful` property and `to_json()` method
9. Add domain validation rules in `services.py`
10. Write comprehensive unit tests for all domain entities

**Acceptance Criteria**:
- All domain entities use `@dataclass` (no Pydantic)
- Zero external dependencies in domain layer
- All unit tests pass without mocks
- Domain logic is testable in isolation

**Tests to Write**:
- `tests/unit/shared/debate/domain/test_value_objects.py`
- `tests/unit/shared/debate/domain/test_entities.py`

**Estimated Complexity**: Medium

---

## 📦 WP02: Port Interfaces and Application Layer

**Description**: Define port interfaces using `typing.Protocol` and create use case orchestrators.

**Dependencies**: WP01

**Files to Create**:
- `src/shared/debate/application/__init__.py`
- `src/shared/debate/application/ports.py` - DebateExecutor, ReportGenerator, FileStorage protocols
- `src/shared/debate/application/use_cases/__init__.py`
- `src/shared/debate/application/use_cases/execute_debate.py` - ExecuteDebate use case

**Tasks**:
1. Create directory structure `src/shared/debate/application/`
2. Define `DebateExecutor` protocol with `execute()` async method
3. Define `ReportGenerator` protocol with `generate_final_report()`, `generate_conclusion()`, `generate_intermediate_report()` methods
4. Define `FileStorage` protocol with `create_run_directory()`, `save_dialogue_json()`, `save_report()`, `save_metadata()` async methods
5. Implement `ExecuteDebate` use case that coordinates debate execution via DebateExecutor port
6. Create request/response dataclasses for use case inputs/outputs
7. Write integration tests with mock adapters

**Acceptance Criteria**:
- All ports use `typing.Protocol` (not ABC)
- Use cases depend only on ports, not implementations
- Integration tests use mock adapters
- Clear separation between application and infrastructure

**Tests to Write**:
- `tests/unit/shared/debate/application/test_ports.py`
- `tests/integration/test_execute_debate_use_case.py`

**Estimated Complexity**: Medium

---

## 📦 WP03: Infrastructure Adapters (Debate Executor & Storage)

**Description**: Implement concrete adapters for debate execution (subprocess) and file storage.

**Dependencies**: WP02

**Files to Create**:
- `src/shared/debate/infrastructure/__init__.py`
- `src/shared/debate/infrastructure/executors/__init__.py`
- `src/shared/debate/infrastructure/executors/cli_executor.py` - CliDebateExecutor adapter
- `src/shared/debate/infrastructure/storage/__init__.py`
- `src/shared/debate/infrastructure/storage/local_storage.py` - LocalFileStorage adapter
- `src/shared/debate/infrastructure/retry.py` - Retry logic with exponential backoff

**Tasks**:
1. Create directory structure `src/shared/debate/infrastructure/`
2. Implement `CliDebateExecutor` that calls `document_debate_cli.py` as subprocess
3. Implement async subprocess execution using `asyncio.create_subprocess_exec`
4. Implement JSON output parsing from subprocess results
5. Implement `LocalFileStorage` using `asyncio.to_thread` for non-blocking I/O
6. Implement retry logic with exponential backoff in `retry.py`
7. Add error categorization (Regex, Timeout, JSON, LLM/API)
8. Write integration tests for both adapters

**Acceptance Criteria**:
- `CliDebateExecutor` successfully calls `document_debate_cli.py` with correct arguments
- `LocalFileStorage` uses non-blocking I/O via `asyncio.to_thread`
- Retry logic implements exponential backoff (2^attempt seconds)
- All adapters implement their respective protocols
- Integration tests validate end-to-end behavior

**Tests to Write**:
- `tests/integration/test_cli_executor.py`
- `tests/integration/test_local_storage.py`

**Estimated Complexity**: High

---

## 📦 WP04: Committee Domain and Use Cases

**Description**: Create committee-specific domain entities and use cases extending the shared framework.

**Dependencies**: WP01, WP02

**Files to Create**:
- `src/committee/__init__.py`
- `src/committee/domain/__init__.py`
- `src/committee/domain/entities.py` - CommitteeRun, CommitteeReport, CommitteeMetadata
- `src/committee/application/__init__.py`
- `src/committee/application/run_committee.py` - RunProductCommittee use case

**Tasks**:
1. Create directory structure `src/committee/`
2. Implement `CommitteeRun` entity extending shared framework
3. Implement `CommitteeReport` entity with `save()` method
4. Implement `CommitteeMetadata` entity with `from_run()` factory
5. Add committee-specific business rules (tpm_wins, opponent_wins counts)
6. Implement `RunProductCommittee` use case
7. Orchestrate 4 debate rooms (TPM vs CPO/CFO/CTO/BDM)
8. Support parallel/sequential execution based on `max_concurrency` parameter
9. Implement intermediate report generation after each room
10. Write integration tests for committee workflow

**Acceptance Criteria**:
- `CommitteeRun` correctly tracks 4 debate rooms
- Parallel execution completes faster than sequential
- Intermediate reports saved after each room completes
- Use case coordinates debate execution via shared ports
- All committee tests pass

**Tests to Write**:
- `tests/unit/committee/domain/test_entities.py`
- `tests/integration/test_committee_workflow.py`

**Estimated Complexity**: High

---

## 📦 WP05: Report Generation System

**Description**: Extract report generation logic into modular adapter classes.

**Dependencies**: WP04

**Files to Create**:
- `src/committee/adapters/__init__.py`
- `src/committee/adapters/reports/__init__.py`
- `src/committee/adapters/reports/final_report.py` - FinalReportGenerator
- `src/committee/adapters/reports/conclusion.py` - ConclusionGenerator

**Tasks**:
1. Create directory structure `src/committee/adapters/reports/`
2. Extract report generation logic from `product_committee.py`
3. Implement `FinalReportGenerator` class implementing `ReportGenerator` port
4. Implement `ConclusionGenerator` class with error categorization
5. Generate markdown with room-by-room analysis, verdicts, dialogue transcripts
6. Handle all-room-failure case with specific recommendations
7. Write snapshot tests for report output
8. Validate snapshot output matches current implementation

**Acceptance Criteria**:
- Report generators produce identical output to current implementation
- Snapshot tests pass for all report types
- Error categorization matches spec (Regex, Timeout, JSON, LLM/API)
- Reports handle partial failures gracefully

**Tests to Write**:
- `tests/snapshots/test_committee_reports/` - Snapshot files for final_report.md, conclusion.md
- `tests/unit/committee/adapters/reports/test_generators.py`

**Estimated Complexity**: Medium

---

## 📦 WP06: CLI Argument Parsing and Validation

**Description**: Create Pydantic models for CLI validation and argument parsing.

**Dependencies**: WP04

**Files to Create**:
- `src/committee/adapters/cli.py` - CLI argument parsing with Pydantic
- `src/committee/adapters/validators.py` - Custom validators

**Tasks**:
1. Create `CommitteeCliInput` Pydantic model for validation
2. Add field validators for PRD file existence, question non-empty
3. Validate `max_retries >= 0` and `0 <= max_concurrency <= 4`
4. Preserve all existing CLI arguments (--prd, --question, --model, etc.)
5. Create `main()` entry point that uses Pydantic validation
6. Add clear error messages for validation failures
7. Write CLI validation tests

**Acceptance Criteria**:
- All existing CLI arguments preserved
- Pydantic validation provides clear error messages
- Invalid inputs rejected before execution starts
- CLI tests validate all argument combinations

**Tests to Write**:
- `tests/unit/committee/adapters/test_cli_validation.py`

**Estimated Complexity**: Low

---

## 📦 WP07: Product Committee CLI Refactoring

**Description**: Refactor `product_committee.py` to use new architecture, preserving all functionality.

**Dependencies**: WP04, WP05, WP06

**Files to Modify**:
- `product_committee.py` - Reduce from ~1970 lines to ~200 lines

**Tasks**:
1. Create new `product_committee.py` using shared framework
2. Import from `src/committee/` and `src/shared/debate/`
3. Preserve all CLI arguments and behavior
4. Wire up RunProductCommittee use case
5. Remove TPM reflection feature (per spec FR11)
6. Remove duplicate sync/async execution paths
7. Ensure backward compatibility with all existing use cases
8. Run full test suite and fix any failures
9. Verify snapshot tests match old output
10. Performance benchmark: parallel <= 60% of sequential time

**Acceptance Criteria**:
- All existing CLI arguments work identically
- All existing tests pass without modification
- Snapshot tests match old implementation exactly
- Code reduced to <500 lines
- Zero duplicate code blocks >10 lines
- Performance: parallel execution completes in ≤60% of sequential time

**Tests to Run**:
- All existing tests: `pytest tests/test_product_committee.py`
- Snapshot tests: `pytest tests/snapshots/`
- Performance benchmarks

**Estimated Complexity**: High

---

## 📦 WP08: Documentation

**Description**: Create comprehensive documentation for the refactored architecture.

**Dependencies**: WP07

**Files to Create**:
- `docs/product-committee-refactoring.md` - Feature documentation
- Update `README.md` with new architecture overview

**Tasks**:
1. Create feature documentation following constitution requirements
2. Document Modular Hexagonal Hybrid architecture approach
3. Include architecture diagrams and data flow
4. Provide usage examples and command reference
5. Explain shared debate framework structure
6. Update README.md with new module structure
7. Add migration notes for users
8. Document testing approach and snapshot testing

**Acceptance Criteria**:
- Documentation follows constitution standards
- Clear explanation of architecture for new developers
- Usage examples match actual CLI behavior
- Architecture diagrams accurate to implementation

**Estimated Complexity**: Low

---

## 📦 WP09: Final Validation and Cleanup

**Description**: Final validation, performance testing, and code cleanup.

**Dependencies**: WP07, WP08

**Tasks**:
1. Run complete test suite and verify 100% pass rate
2. Validate functional equivalence with old implementation
3. Performance benchmark: parallel vs sequential execution
4. Check code quality metrics (cyclomatic complexity, coupling)
5. Remove any remaining dead code or comments
6. Update CLAUDE.md with new architecture
7. Verify all constitution requirements met
8. Create PR with comprehensive description
9. Address any code review feedback

**Acceptance Criteria**:
- All tests pass (existing + new)
- Functional equivalence verified
- Performance: parallel <= 60% of sequential time
- Code quality metrics acceptable
- Constitution requirements satisfied
- PR ready for review

**Tests to Run**:
- Full test suite: `pytest`
- Coverage report: `pytest --cov=src/shared --cov=src/committee`
- Performance benchmarks

**Estimated Complexity**: Medium

---

## Task Status Tracking

| WP | Description | Status | Blocked By |
|----|-------------|--------|------------|
| WP01 | Shared Domain Layer | TODO | None |
| WP02 | Port Interfaces and Application Layer | TODO | WP01 |
| WP03 | Infrastructure Adapters | TODO | WP02 |
| WP04 | Committee Domain and Use Cases | TODO | WP01, WP02 |
| WP05 | Report Generation System | TODO | WP04 |
| WP06 | CLI Argument Parsing and Validation | TODO | WP04 |
| WP07 | Product Committee CLI Refactoring | TODO | WP04, WP05, WP06 |
| WP08 | Documentation | TODO | WP07 |
| WP09 | Final Validation and Cleanup | TODO | WP07, WP08 |

---

## Success Criteria Validation

| Criterion | Validation Method | Target |
|-----------|-------------------|--------|
| Functional Equivalence | All existing tests pass | 100% |
| Code Quality Reduction | Line count per module | <500 lines |
| Duplication Elimination | Code analysis tools | 0 blocks >10 lines |
| Architecture Compliance | Layer dependency analysis | Clear separation |
| Test Coverage | Domain logic testability | 100% without external deps |
| Performance | Benchmark parallel vs sequential | ≤60% time |
| Test Suite | All tests pass | 100% |

---

## Next Steps

1. Start with WP01 (Shared Domain Layer) - foundation for all other work
2. Use `/spec-kitty.implement WP01` to create a worktree for WP01
3. Follow migration order: WP01 → WP02 → WP03 → WP04 → WP05 → WP06 → WP07 → WP08 → WP09
4. Each WP should be completed and tested before starting dependent WPs
