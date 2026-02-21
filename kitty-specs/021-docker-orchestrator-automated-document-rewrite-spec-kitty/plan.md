# Implementation Plan: Docker Orchestrator for Automated Document Rewrite via Claude Code + Spec-Kitty

**Branch**: `021-docker-orchestrator-automated-document-rewrite-spec-kitty` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/spec.md`

## Summary

Create a Docker-based orchestration system that automatically processes text documents through the complete Spec-Kitty workflow (specify → research → plan → tasks → implement → review → accept). The system runs as a one-shot CLI tool using a threaded Python architecture with `concurrent.futures.ThreadPoolExecutor` for concurrent operations. The AI "vibe-coder" agent is implemented as a Python orchestrator that manages a Claude Code CLI subprocess, driving it via Spec-Kitty slash commands rather than direct API calls.

## Technical Context

**Language/Version**: Python 3.12+ (per constitution)
**Primary Dependencies**:
- `docker` (Docker Python SDK) for container management
- `concurrent.futures` (stdlib) for threading
- `subprocess` (stdlib) for Claude Code CLI management
- `pyyaml` (existing) for configuration loading
- Existing `src/shared/config` and `src/shared/debate` infrastructure

**Storage**: File system for source files, corrections, output files, and logs at `.orchestrator/logs/`
**Testing**: pytest (per constitution requirement)
**Target Platform**: Cross-platform (Linux, macOS, Windows) with Docker Engine required
**Project Type**: Single project (CLI utility)
**Performance Goals**:
- Process 10-page markdown with 20 corrections in under 15 minutes (SC-001)
- Complete full workflow without manual intervention in 95%+ of cases (SC-002)

**Constraints**:
- Requires Docker Engine running on host
- Requires network connectivity for Claude Code API calls
- One-shot execution only (no daemon mode)
- Must preserve original files unchanged (SC-008)

**Scale/Scope**:
- Single document per invocation
- Sequential workflow phases (no parallel execution)
- State machine tracking 7 Spec-Kitty phases
- Maximum 3 retries per phase (configurable)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Status

| Requirement | Status | Notes |
|-------------|--------|-------|
| Python 3.12+ | ✅ PASS | Using Python 3.12+ per constitution |
| pytest required | ✅ PASS | Tests will use pytest |
| Spec-driven development | ✅ PASS | Working from written specification |
| TDD approach | ✅ PASS | Tests written before implementation |
| Doc-driven features | ✅ PASS | Feature documentation in `docs/orchestrator.md` planned |
| pip installable | ✅ PASS | Follows existing package structure |
| Cross-platform | ✅ PASS | Works on Linux, macOS, Windows with Docker |

### Architecture Considerations

**Decision: Threaded architecture with Claude Code subprocess**

*Rationale*: This approach:
- Aligns with constitution's emphasis on simplicity and minimal dependencies
- Leverages existing Claude Code + Spec-Kitty ecosystem without custom agent kernels
- Uses standard library (`concurrent.futures`, `subprocess`) avoiding complex async runtime
- Integrates cleanly with existing synchronous CLI/SDK patterns in the codebase

*Constitution alignment*: The constitution prioritizes rapid development and hypothesis testing over optimization. Threaded architecture provides sufficient concurrency for this use case while maintaining code simplicity.

## Project Structure

### Documentation (this feature)

```
kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/
├── plan.md              # This file (/spec-kitty.plan command output)
├── research.md          # Phase 0 output (/spec-kitty.plan command)
├── data-model.md        # Phase 1 output (/spec-kitty.plan command)
├── quickstart.md        # Phase 1 output (/spec-kitty.plan command)
├── contracts/           # Phase 1 output (/spec-kitty.plan command)
└── tasks.md             # Phase 2 output (/spec-kitty.tasks command - NOT created by /spec-kitty.plan)
```

### Source Code (repository root)

```
src/
├── orchestrator/
│   ├── __init__.py
│   ├── __main__.py                 # Entry point for poetry run
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── cli.py                  # CLI argument parsing
│   │   ├── progress_reporter.py    # Console progress display
│   │   ├── config_loader.py        # Load orchestrator config from debate_config.yaml
│   │   └── docker_client.py        # Docker SDK wrapper
│   ├── application/
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Main workflow orchestration
│   │   ├── workflow_state.py       # State machine for Spec-Kitty phases
│   │   ├── phase_runner.py         # Execute individual phases
│   │   └── artifact_validator.py   # Validate spec/plan/tasks artifacts
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py               # OrchestratorConfig, WorkflowPhase, OrchestratorResult
│   │   ├── phase.py                # Phase enum and state transitions
│   │   └── validation_result.py    # Validation result types
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── container_manager.py    # Docker container lifecycle
│   │   ├── claude_code_agent.py    # Claude Code subprocess management
│   │   ├── filesystem.py           # File operations for source/corrections/output
│   │   └── logging.py              # Structured logging to .orchestrator/logs/
│   └── prompts/
│       ├── __init__.py
│       ├── validation.md           # Prompt for artifact validation
│       └── phase_context.md        # Prompt template for phase-specific context
│
tests/
├── orchestrator/
│   ├── unit/
│   │   ├── test_config_loader.py
│   │   ├── test_workflow_state.py
│   │   ├── test_artifact_validator.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_container_manager.py
│   │   ├── test_claude_code_agent.py
│   │   └── test_orchestrator.py
│   └── fixtures/
│       ├── sample_source.md
│       ├── sample_corrections.md
│       └── mock_spec_kitty_artifacts/

scripts/
└── orchestrator                       # CLI entry point (chmod +x)

docs/
└── orchestrator.md                     # Feature documentation (per constitution)

config/
└── debate_config.yaml                  # Extended with orchestrator: section

.orchestrator/
└── logs/                               # Runtime logs (gitignored)
```

**Structure Decision**: Single project structure following existing `src/rewrite` pattern with clean architecture (adapters/application/domain/infrastructure). This aligns with constitution's preference for simplicity and maintains consistency with the codebase.

## Phase 0: Research

### Outstanding Technical Questions

1. **Docker SDK best practices for Python**
   - Question: What are the recommended patterns for container lifecycle management, log streaming, and error handling with the Docker Python SDK?
   - Impact: Core to container management functionality
   - Deliverable: Best practices summary for `infrastructure/container_manager.py`

2. **Claude Code CLI subprocess communication**
   - Question: How to properly communicate with Claude Code CLI subprocess - stdin/stdout vs socket API, command format, response parsing?
   - Impact: Core to agent implementation
   - Deliverable: Communication protocol specification for `infrastructure/claude_code_agent.py`

3. **Spec-Kitty artifact parsing**
   - Question: What is the structure of spec.md, plan.md, and tasks.md artifacts? How to detect completion status and extract validation criteria?
   - Impact: Required for state machine and validation
   - Deliverable: Artifact parser specification

4. **Artifact validation prompts**
   - Question: What prompts effectively validate Spec-Kitty artifacts for completeness and quality?
   - Impact: Core to retry mechanism
   - Deliverable: Validation prompt templates for `src/orchestrator/prompts/`

5. **Threading patterns for CLI tools**
   - Question: What are the recommended patterns for using `concurrent.futures.ThreadPoolExecutor` in CLI applications?
   - Impact: Core to concurrent operations
   - Deliverable: Threading architecture guidelines

### Research Plan

Dispatch research tasks to resolve each outstanding question. Results will be consolidated in `research.md`.

**Output**: `research.md` with decisions, rationales, and alternatives for each question.

## Phase 1: Design & Contracts

### Data Model

**Output**: `data-model.md` containing:
- Entity definitions (OrchestratorConfig, WorkflowPhase, OrchestratorResult)
- Field types and validation rules
- State transition diagrams for workflow phases
- Relationships between entities

### Configuration Contract

**Output**: `contracts/config-schema.yaml` containing:
- YAML schema for `orchestrator:` section in `config/debate_config.yaml`
- Default values and validation rules
- Configuration loading contract

### CLI Contract

**Output**: `contracts/cli-interface.md` containing:
- Command syntax: `poetry run python scripts/orchestrator <source> <corrections> [options]`
- Argument specifications and defaults
- Exit codes and their meanings
- Console output format specification

### Agent Communication Contract

**Output**: `contracts/agent-protocol.md` containing:
- Claude Code subprocess communication protocol
- Command format for Spec-Kitty slash commands
- Response parsing and error handling
- State synchronization patterns

### Quickstart Guide

**Output**: `quickstart.md` containing:
- Prerequisites (Docker, Claude Code CLI, Spec-Kitty CLI)
- Installation steps
- Basic usage example
- Configuration guide
- Troubleshooting common issues

### Agent Context Update

Update appropriate agent-specific context file with:
- Docker Python SDK (`docker` package)
- concurrent.futures threading patterns
- Subprocess management for CLI tools

## Phase Gates

### Pre-Phase 0 Gate

- [x] Spec reviewed and understood
- [x] Engineering alignment confirmed (threaded architecture, Claude Code subprocess)
- [x] Constitution check passed
- [x] Research questions defined
- [x] Research tasks dispatched

### Pre-Phase 1 Gate

- [x] `research.md` complete with all questions resolved
- [x] Constitution re-check passed (post-design)
- [x] Data model defined
- [x] Contracts specified
- [x] Quickstart drafted

### Pre-Implementation Gate

- [x] All design artifacts complete
- [ ] `tasks.md` generated via `/spec-kitty.tasks`
- [ ] Work packages (WP) created for implementation

## Implementation Notes

### Key Integration Points

1. **Configuration System**: Extend `src/shared/config` to load `orchestrator:` section
2. **Logging**: Use existing logging patterns from `src/rewrite`
3. **CLI Pattern**: Follow `scripts/rewrite` as reference for entry point structure
4. **Error Handling**: Use existing error handling patterns from rewrite implementation

### Critical Success Factors

1. **Docker availability validation**: Pre-flight check before starting workflow
2. **State machine correctness**: Accurate tracking of Spec-Kitty phase transitions
3. **Graceful degradation**: Handle Claude Code CLI failures, API errors, network issues
4. **Resource cleanup**: Ensure containers are stopped even on failure
5. **File preservation**: Never modify original source files

### Testing Strategy

Per constitution (TDD approach):
1. Write unit tests for models, state machine, validation logic
2. Write integration tests for container manager, Claude Code agent
3. Write end-to-end tests for full orchestrator workflow
4. Mock external dependencies (Docker, Claude Code CLI) in tests
