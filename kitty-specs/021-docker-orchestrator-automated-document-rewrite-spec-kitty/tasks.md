# Tasks: Docker Orchestrator for Automated Document Rewrite via Claude Code + Spec-Kitty

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Branch**: `021-docker-orchestrator-automated-document-rewrite-spec-kitty`
**Status**: Draft
**Created**: 2026-02-21

## Overview

This document defines work packages for implementing the Docker Orchestrator feature. The orchestrator automatically processes text documents through the complete Spec-Kitty workflow using Docker containers and a stateful AI agent.

## Work Package Summary

| WP | Title | Priority | Subtasks | Dependencies | Est. Lines |
|----|-------|----------|----------|--------------|------------|
| WP01 | Foundation & Configuration | P0 | 5 | None | ~300 |
| WP02 | Domain Models & State Machine | P0 | 6 | WP01 | ~350 |
| WP03 | Docker Container Management | P0 | 7 | WP01, WP02 | ~420 |
| WP04 | Claude Code Agent Communication | P0 | 8 | WP02 | ~480 |
| WP05 | Workflow Orchestration Core | P0 | 7 | WP02, WP03, WP04 | ~450 |
| WP06 | Phase Execution & Validation | P0 | 7 | WP05 | ~420 |
| WP07 | CLI Interface & Progress Reporting | P1 | 6 | WP01, WP05 | ~380 |
| WP08 | File Operations & Output Management | P1 | 5 | WP01 | ~320 |
| WP09 | Logging & Observability | P1 | 5 | WP01 | ~300 |
| WP10 | Error Handling & Signal Management | P1 | 6 | WP03, WP04, WP05 | ~380 |
| WP11 | Integration Testing & Fixtures | P2 | 5 | WP01-WP10 | ~350 |

**Total**: 11 work packages, 67 subtasks, estimated ~4,450 prompt lines

## Phase Breakdown

### Phase 0: Foundation (WP01-WP02)
Core domain models, configuration system, and state machine foundation.

### Phase 1: Infrastructure (WP03-WP04)
Docker container management and Claude Code subprocess communication.

### Phase 2: Core Workflow (WP05-WP06)
Main orchestration loop and phase execution with validation.

### Phase 3: User Interface (WP07-WP09)
CLI, progress reporting, file operations, and logging.

### Phase 4: Quality (WP10-WP11)
Error handling, signal management, and integration testing.

## Work Packages

---

## WP01 – Foundation & Configuration (Priority: P0)

**Goal**: Establish project structure, configuration loading, and shared utilities.

**Success Criteria**:
- Project structure created matching plan.md
- Configuration loads from debate_config.yaml with defaults
- Configuration validates against schema
- Docker dependency added to pyproject.toml

**Included Subtasks**:
- [x] T001 – Create project structure and module hierarchy
- [x] T002 – Add Docker dependency to pyproject.toml
- [x] T003 – Implement OrchestratorConfig domain model
- [x] T004 – Create configuration loader adapter
- [x] T005 – Add configuration schema validation

**Implementation Sketch**:
1. Create `src/orchestrator/` directory with clean architecture subdirs
2. Update `pyproject.toml` with `docker` dependency
3. Implement `OrchestratorConfig` as Pydantic/dataclass model
4. Create `ConfigLoader` adapter extending existing config system
5. Add validation logic for all config fields

**Parallel Opportunities**: T001 and T002 can run in parallel (different files)

**Dependencies**: None

**Risks**:
- Config system integration may require updates to `src/shared/config`
- Pydantic vs dataclass decision affects validation approach

---

## WP02 – Domain Models & State Machine (Priority: P0)

**Goal**: Implement core domain entities and workflow state machine.

**Success Criteria**:
- All domain models (WorkflowPhase, OrchestratorResult, ArtifactMetadata) implemented
- State machine enforces valid transitions
- Thread-safe phase state updates
- Result aggregation from phases works correctly

**Included Subtasks**:
- [x] T006 – Implement WorkflowPhase domain model
- [x] T007 – Implement PhaseStatus and ValidationStatus enums
- [x] T008 – Implement state transition logic with validation
- [x] T009 – Implement OrchestratorResult domain model
- [x] T010 – Implement ArtifactMetadata domain model
- [x] T011 – Add thread-safety to phase state updates

**Implementation Sketch**:
1. Create enum classes for PhaseStatus and ValidationStatus
2. Implement WorkflowPhase with transition_to() method and validation
3. Use threading.Lock for thread-safe state updates
4. Implement OrchestratorResult with from_phases() factory method
5. Implement ArtifactMetadata with frontmatter parsing

**Parallel Opportunities**: T006-T010 can run in parallel (different model files)

**Dependencies**: WP01 (uses config validation patterns)

**Risks**:
- Thread-safety adds complexity; may need threading.Lock
- State machine transitions must be exhaustive

---

## WP03 – Docker Container Management (Priority: P0)

**Goal**: Implement Docker container lifecycle management using Docker SDK.

**Success Criteria**:
- Containers start with correct volumes and environment
- Container health checks work
- Log streaming captures output in real-time
- Containers stop and remove cleanly on all exit paths
- Pre-flight Docker validation works

**Included Subtasks**:
- [x] T012 – Create DockerClient wrapper adapter
- [x] T013 – Implement container start with volume mounts
- [x] T014 – Implement container health check
- [x] T015 – Implement real-time log streaming
- [x] T016 – Implement container stop and cleanup
- [x] T017 – Add pre-flight Docker availability validation
- [x] T018 – Handle container resource limits and timeouts

**Implementation Sketch**:
1. Create `DockerClient` wrapping docker.from_env()
2. Implement start() with volumes, environment, and resource limits
3. Implement health_check() polling container status
4. Use ThreadPoolExecutor for log streaming in background thread
5. Ensure cleanup in finally block or context manager
6. Test with docker ps, docker images commands

**Parallel Opportunities**: T012-T016 can run in parallel (different concerns)

**Dependencies**: WP01 (uses config values for docker_image, timeouts)

**Risks**:
- Docker SDK version compatibility
- Container name collisions on concurrent runs
- Log streaming thread may not terminate cleanly

---

## WP04 – Claude Code Agent Communication (Priority: P0)

**Goal**: Implement subprocess communication with Claude Code CLI using JSON protocol.

**Success Criteria**:
- Claude Code subprocess starts and communicates via stdin/stdout
- JSON commands sent and responses parsed correctly
- UUID-based request/response matching works
- Timeout handling terminates hung subprocess
- Subprocess cleanup works on all exit paths

**Included Subtasks**:
- [ ] T019 – Create ClaudeCodeAgent infrastructure class
- [ ] T020 – Implement subprocess start with stdin/stdout pipes
- [ ] T021 – Implement JSON command sending with UUID
- [ ] T022 – Implement response parsing and UUID matching
- [ ] T023 – Implement timeout handling with SIGTERM/SIGKILL
- [ ] T024 – Implement subprocess cleanup and termination
- [ ] T025 – Add retry logic for transient subprocess failures
- [ ] T026 – Implement Spec-Kitty command helpers

**Implementation Sketch**:
1. Create subprocess.Popen with text mode and line buffering
2. Generate UUID v4 for each request
3. Send JSON commands with trailing newline
4. Read responses line-by-line, parse JSON
5. Use threading.Timer for timeout, then send SIGTERM, wait 5s, SIGKILL
6. Implement send_command() with timeout and retry

**Parallel Opportunities**: T019-T024 can run in parallel (different methods)

**Dependencies**: WP02 (uses WorkflowPhase for state tracking)

**Risks**:
- Claude Code CLI may not support stdin/stdout protocol as assumed
- Subprocess may buffer output causing delays
- Race conditions in timeout handling

---

## WP05 – Workflow Orchestration Core (Priority: P0)

**Goal**: Implement main orchestration loop that drives Spec-Kitty workflow phases.

**Success Criteria**:
- Orchestrator executes all 7 phases sequentially
- Phase state tracked correctly throughout workflow
- Workflow aborts on critical failures
- Partial results preserved on abort
- Progress callbacks fire for each phase transition

**Included Subtasks**:
- [ ] T027 – Create Orchestrator application class
- [ ] T028 – Implement main workflow execution loop
- [ ] T029 – Implement phase transition logic
- [ ] T030 – Implement workflow abort and cleanup
- [ ] T031 – Add progress callback hooks
- [ ] T032 – Implement OrchestratorResult aggregation
- [ ] T033 – Handle workflow pause/resume (if feasible)

**Implementation Sketch**:
1. Create Orchestrator class with dependencies (container_manager, agent, config)
2. Implement execute() running phases sequentially
3. For each phase: start, await completion, validate if needed, retry or continue
4. On failure: stop container, save partial results, exit with appropriate code
5. Call progress_reporter for each phase transition

**Parallel Opportunities**: T027-T032 are sequential (orchestration logic)

**Dependencies**: WP02 (state machine), WP03 (containers), WP04 (agent)

**Risks**:
- Complex state management across phases
- Error handling may swallow important failures
- Phase timeouts need careful tuning

---

## WP06 – Phase Execution & Validation (Priority: P0)

**Goal**: Implement individual phase execution and artifact validation logic.

**Success Criteria**:
- Each Spec-Kitty phase executes via Claude Code agent
- Artifact validation runs after enabled phases
- Validation failures trigger retries up to limit
- Invalid artifacts cause workflow abort after max retries
- Validation prompts use configurable templates

**Included Subtasks**:
- [ ] T034 – Create PhaseRunner application class
- [ ] T035 – Implement phase execution for each Spec-Kitty command
- [ ] T036 – Implement ArtifactValidator for spec/plan/tasks
- [ ] T037 – Create validation prompt templates
- [ ] T038 – Implement retry logic with context accumulation
- [ ] T039 – Add artifact completeness detection
- [ ] T040 – Implement validation timeout handling

**Implementation Sketch**:
1. Create PhaseRunner with execute_phase(phase_name) method
2. For each phase, send appropriate Spec-Kitty command via agent
3. After phase, parse artifact from kitty-specs directory
4. Run validation: load prompt, send to Claude Code, parse response
5. On validation fail: accumulate feedback, retry if attempts < max_retries
6. Use ArtifactMetadata to detect [NEEDS CLARIFICATION] markers

**Parallel Opportunities**: T035-T037 can run in parallel (different phases)

**Dependencies**: WP04 (agent communication), WP05 (orchestrator integration)

**Risks**:
- Spec-Kitty command interface may differ from assumptions
- Artifact parsing may fail on malformed markdown
- Validation quality depends on prompt quality

---

## WP07 – CLI Interface & Progress Reporting (Priority: P1)

**Goal**: Implement CLI argument parsing and console progress reporting.

**Success Criteria**:
- CLI accepts source/corrections file paths and options
- Help message displays correctly
- Console output shows real-time progress
- Verbose mode provides additional detail
- Progress reporter formats output consistently

**Included Subtasks**:
- [x] T041 – Create CLI argument parser adapter
- [x] T042 – Implement argument validation
- [x] T043 – Create ProgressReporter adapter
- [x] T044 – Implement phase progress display
- [x] T045 – Implement summary and result display
- [x] T046 – Add Ctrl+C signal handler

**Implementation Sketch**:
1. Use argparse following patterns from scripts/rewrite
2. Add arguments: source, corrections, --output, --config, --verbose, --dry-run
3. Validate file paths exist and are readable
4. ProgressReporter prints [ORCHESTRATOR] prefixed messages
5. Format: "Phase: <name> → <status>" with progress indicators
6. Signal handler sets flag,优雅地 shutdown after current phase

**Parallel Opportunities**: T041-T043 can run in parallel (different adapters)

**Dependencies**: WP01 (config), WP05 (orchestrator interface)

**Risks**:
- Argument parsing complexity with many options
- Progress output may conflict with subprocess output

---

## WP08 – File Operations & Output Management (Priority: P1)

**Goal**: Implement file reading, output generation, and preservation of originals.

**Success Criteria**:
- Source and corrections files read correctly
- Multiple file format support (markdown, text, code)
- Output file written with correct suffix
- Original files never modified
- Output file conflicts handled per config

**Included Subtasks**:
- [ ] T047 – Create FileOperations infrastructure class
- [ ] T048 – Implement file reading with encoding detection
- [ ] T049 – Implement output path generation
- [ ] T050 – Implement corrected file writing
- [ ] T051 – Add output file conflict handling

**Implementation Sketch**:
1. Create FileOperations class in infrastructure/
2. Read files trying multiple encodings (utf-8, latin-1, cp1252)
3. Generate output path: source.with_suffix(config.output_suffix + ext)
4. Write output atomically (write to temp, then rename)
5. Handle conflict: error, overwrite, or timestamp per config

**Parallel Opportunities**: T047-T051 are sequential (file ops)

**Dependencies**: WP01 (config values)

**Risks**:
- Binary files may slip through text detection
- File encoding issues on non-UTF-8 content
- Atomic write may fail on some filesystems

---

## WP09 – Logging & Observability (Priority: P1)

**Goal**: Implement structured logging to files and optional verbose console output.

**Success Criteria**:
- Log files written to .orchestrator/logs/
- Logs contain sufficient debugging information
- Log rotation prevents disk space issues
- Verbose mode provides additional detail
- Log format matches existing patterns

**Included Subtasks**:
- [ ] T052 – Create LoggingSetup infrastructure
- [ ] T053 – Implement structured log formatting
- [ ] T054 – Add file logging with rotation
- [ ] T055 – Implement verbose mode logging
- [ ] T056 – Add log cleanup on startup

**Implementation Sketch**:
1. Create logging setup in infrastructure/logging.py
2. Use Python logging with custom formatter
3. FileHandler with RotatingFileLogger (10MB max, 3 backups)
4. ConsoleHandler respects verbose flag
5. On startup: clean logs older than 7 days

**Parallel Opportunities**: T052-T055 can run in parallel (different aspects)

**Dependencies**: WP01 (config log_level, log_dir)

**Risks**:
- Log directory may not exist or be unwritable
- Log rotation may conflict with multiple processes

---

## WP10 – Error Handling & Signal Management (Priority: P1)

**Goal**: Implement comprehensive error handling and graceful signal management.

**Success Criteria**:
- All error paths exit with appropriate codes
- Docker containers cleaned up on all exits
- Ctrl+C handled gracefully with partial results
- Error messages are actionable
- No resource leaks on any exit path

**Included Subtasks**:
- [ ] T057 – Create OrchestratorError exception hierarchy
- [ ] T058 – Implement error code mapping
- [ ] T059 – Add container cleanup on error paths
- [ ] T060 – Implement graceful shutdown on signals
- [ ] T061 – Add partial result preservation on abort
- [ ] T062 – Create error message templates

**Implementation Sketch**:
1. Create exception classes: DockerError, AgentError, ValidationError, ConfigError
2. Map exception types to exit codes (0=success, 1=partial, 2=failed, etc.)
3. Use try/finally to ensure container cleanup
4. Signal handler sets shutdown_flag, waits for current phase
5. On abort: write partial output, save state, exit with code 130

**Parallel Opportunities**: T057-T062 can run in parallel (different error types)

**Dependencies**: WP03 (containers), WP04 (agent), WP05 (orchestrator)

**Risks**:
- Signal handling in Python can be tricky
- Finally blocks may not execute on SIGKILL
- Error recovery may leave resources leaked

---

## WP11 – Integration Testing & Fixtures (Priority: P2)

**Goal**: Create integration tests and test fixtures for end-to-end validation.

**Success Criteria**:
- Integration tests cover main workflow
- Mock Docker and Claude Code for testing
- Test fixtures provide sample artifacts
- Tests validate error handling paths
- Test suite runs in CI environment

**Included Subtasks**:
- [ ] T063 – Create test fixtures directory and sample files
- [ ] T064 – Mock Docker client for testing
- [ ] T065 – Mock Claude Code agent for testing
- [ ] T066 – Write integration test for happy path
- [ ] T067 – Write integration tests for error paths

**Implementation Sketch**:
1. Create tests/orchestrator/fixtures/ with sample .md files
2. Mock docker.from_env() returning fake containers
3. Mock subprocess.Popen returning fake responses
4. Test: successful workflow with all phases
5. Tests: Docker unavailable, agent crash, validation failure, Ctrl+C

**Parallel Opportunities**: T063-T065 can run in parallel (different fixtures)

**Dependencies**: All WP01-WP10 (tests the integrated system)

**Risks**:
- Mocking Docker subprocess is complex
- Integration tests may be slow
- CI environment may not have Docker

---

## Dependency Graph

```
WP01 (Foundation)
├── WP02 (Domain Models)
│   ├── WP03 (Docker Containers)
│   │   └── WP05 (Orchestration Core) ──┐
│   │       └── WP06 (Phase Execution)  │
│   └── WP04 (Agent Communication) ──────┤
│                                       │
└── WP07 (CLI Interface) ────────────────┘
    │
    └── WP08 (File Operations)

WP01 ─────────────────────────────────────────┐
    │                                         │
    └── WP09 (Logging)                        │
                                             │
WP03, WP04, WP05 ──── WP10 (Error Handling)  │
                                             │
All WP01-WP10 ─────────── WP11 (Integration Tests)
```

## Parallelization Strategy

**Wave 1** (Can run in parallel immediately):
- WP01: Foundation & Configuration
- WP07: CLI Interface (after WP01 starts)
- WP08: File Operations (after WP01 starts)
- WP09: Logging & Observability (after WP01 starts)

**Wave 2** (After WP01 completes):
- WP02: Domain Models & State Machine
- WP03: Docker Container Management
- WP04: Claude Code Agent Communication

**Wave 3** (After WP02, WP03, WP04 complete):
- WP05: Workflow Orchestration Core
- WP10: Error Handling & Signal Management

**Wave 4** (After WP05 completes):
- WP06: Phase Execution & Validation
- WP11: Integration Testing & Fixtures

## MVP Scope Recommendation

**Minimum Viable Product**: WP01 through WP06

This provides:
- Complete infrastructure (Docker + Agent communication)
- Working orchestration core
- All 7 phases executing sequentially
- Artifact validation and retry logic
- File I/O and configuration

**Post-MVP additions**:
- WP07-WP09: Polish and user experience
- WP10-WP11: Quality and testing

## Notes

- Each work package targets 200-500 lines in the prompt file
- All WPs follow clean architecture (adapters/application/domain/infrastructure)
- Tests are optional unless explicitly required (per constitution)
- Thread-safety is critical due to ThreadPoolExecutor usage
- Resource cleanup is paramount (containers, subprocesses, files)
