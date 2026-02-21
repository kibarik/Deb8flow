# Data Model: Docker Orchestrator

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Date**: 2026-02-21
**Phase**: Phase 1 - Design

## Overview

This document defines the data model for the Docker Orchestrator feature, including all entities, their attributes, relationships, and state transitions.

## Entities

### OrchestratorConfig

Configuration loaded from `config/debate_config.yaml` under the `orchestrator:` section.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_retries` | int | No | 3 | Maximum retry attempts per phase |
| `validation_timeout` | int | No | 30 | Seconds to wait for validation |
| `auto_accept` | bool | No | false | Skip final acceptance prompt |
| `keep_containers` | bool | No | false | Don't stop containers after completion |
| `output_suffix` | str | No | ".corrected." | Suffix for output files |
| `timestamp_output` | bool | No | false | Add timestamp to output filename |
| `docker_image` | str | No | "claude-code:latest" | Container image to use |
| `container_timeout` | int | No | 3600 | Max seconds for container execution |
| `log_dir` | str | No | ".orchestrator/logs" | Directory for logs |
| `log_level` | str | No | "INFO" | Logging level |
| `verbose` | bool | No | false | Enable verbose output |
| `claude_cli_path` | str \| None | No | null | Optional path to Claude Code CLI binary |
| `phases` | list[PhaseConfig] | No | All enabled | Phase-specific configuration |

**Validation Rules**:
- `max_retries` must be >= 0
- `validation_timeout` must be > 0
- `container_timeout` must be > 0
- `log_level` must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL

### PhaseConfig

Configuration for individual workflow phases.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | - | Phase identifier (specify, research, plan, tasks, implement, review, accept) |
| `enabled` | bool | No | true | Whether phase is executed |
| `validate` | bool | No | false | Whether to validate artifact after phase |

**Validation Rules**:
- `name` must be one of the 7 valid phase names

### WorkflowPhase

Represents the state of a single workflow phase.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Phase identifier (enum) |
| `status` | PhaseStatus | Yes | Current status of the phase |
| `attempts` | int | Yes | Number of execution attempts |
| `artifact_path` | Path \| None | Yes | Path to generated artifact (if any) |
| `validation_result` | ValidationStatus \| None | Yes | Result of artifact validation |
| `started_at` | datetime \| None | Yes | When phase execution started |
| `completed_at` | datetime \| None | Yes | When phase execution completed |
| `error_message` | str \| None | Yes | Error message if failed |

**PhaseStatus Enum**:
```
pending -> running -> (completed | failed | retrying)
```

**Values**:
- `pending`: Phase not yet started
- `running`: Phase currently executing
- `completed`: Phase finished successfully
- `failed`: Phase failed after max retries
- `retrying`: Phase being retried after validation failure

**ValidationStatus Enum**:
- `passed`: Artifact validation passed
- `failed`: Artifact validation failed
- `skipped`: Validation not configured for this phase

**State Transitions**:
```
pending
  ↓ (start_phase)
running
  ↓ (artifact_generated)
  ├─→ completed (if validation passed or skipped)
  ├─→ retrying (if validation failed and retries remaining)
  └─→ failed (if validation failed and no retries remaining)

retrying
  ↓ (retry_attempt)
running (again)
```

### OrchestratorResult

Final result of orchestrator execution.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | ResultStatus | Yes | Overall execution status |
| `phases_completed` | int | Yes | Number of phases successfully completed |
| `total_phases` | int | Yes | Total number of phases configured |
| `total_retries` | int | Yes | Total retry attempts across all phases |
| `duration_seconds` | int | Yes | Total execution time |
| `output_path` | Path \| None | Yes | Path to corrected output file |
| `failed_phase` | str \| None | Yes | Name of phase that failed (if any) |
| `container_id` | str \| None | Yes | Docker container ID for debugging |
| `error_summary` | list[str] | Yes | List of errors encountered |

**ResultStatus Enum**:
- `success`: All phases completed successfully
- `partial`: Some phases completed but workflow stopped
- `failed`: Workflow failed before completion

### ArtifactMetadata

Metadata extracted from Spec-Kitty artifacts.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `artifact_type` | str | Yes | Type of artifact (spec, plan, tasks) |
| `path` | Path | Yes | Path to artifact file |
| `frontmatter` | dict | Yes | YAML frontmatter content |
| `mandatory_sections` | list[str] | Yes | List of mandatory section names |
| `present_sections` | list[str] | Yes | List of present section names |
| `clarifications_needed` | int | Yes | Count of [NEEDS CLARIFICATION] markers |
| `is_complete` | bool | Yes | Whether artifact is complete |

## Relationships

```
OrchestratorConfig
  ├── 1..* PhaseConfig
  └── used by → Orchestrator

WorkflowPhase
  ├── 0..1 ArtifactMetadata (after phase completion)
  └── managed by → Orchestrator

OrchestratorResult
  ├── references → 0..* WorkflowPhase (all phases)
  └── produced by → Orchestrator
```

## State Machine: Workflow Orchestration

```
                        ┌─────────────────┐
                        │   INITIALIZE    │
                        │  (load config,  │
                        │   validate      │
                        │   docker)       │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │ START_CONTAINER │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │  RUN_PHASE_LOOP │◄──────────────┐
                        └────────┬────────┘               │
                                 │                        │
              ┌──────────────────┼──────────────────┐    │
              │                  │                  │    │
              ↓                  ↓                  ↓    │
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  SPECIFY    │    │  RESEARCH   │    │    PLAN     │───│
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                  │                  │
           └──────────────────┴──────────────────┘
                                 │
                                 ↓
    ┌─────────────────────────────────────────┐
    │         VALIDATE_IF_REQUIRED            │
    │  (if validation fails and retries > 0)  │
    └──────────────┬──────────────────────────┘
                   │ (retry)
                   └──────────────────────────┘
                                 │ (pass)
                                 ↓
    ┌─────────────────────────────────────────┐
    │         NEXT_PHASE_OR_COMPLETE          │
    └─────────────────────────────────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ↓                           ↓
            ┌─────────────┐           ┌─────────────┐
            │    TASKS    │           │  IMPLEMENT  │
            └──────┬──────┘           └──────┬──────┘
                   │                         │
                   └─────────────┬───────────┘
                                 ↓
                        ┌─────────────────┐
                        │    REVIEW       │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │    ACCEPT       │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │ COPY_OUTPUT     │
                        │ (generate       │
                        │  .corrected)    │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │ STOP_CONTAINER  │
                        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │     RETURN      │
                        │  (Orchestrator  │
                        │   Result)       │
                        └─────────────────┘
```

## Validation Rules Summary

### Config Validation
- All integer values must be non-negative where applicable
- Enum values must match allowed values
- Paths must be valid directory/file paths

### Phase Validation
- Phase names must be valid Spec-Kitty phases
- Phase transitions must follow state machine rules
- Cannot transition from `completed` back to `running`

### Artifact Validation
- `is_complete` = true only if:
  - All mandatory sections present
  - No `[NEEDS CLARIFICATION]` markers
  - Frontmatter contains required fields

## Data Access Patterns

### Configuration Loading
```python
# Single source of truth
config = OrchestratorConfig.from_yaml('config/debate_config.yaml')

# Validation on load
if not config.is_valid():
    raise ConfigValidationError(config.errors)
```

### Phase State Management
```python
# Thread-safe phase updates
phase = WorkflowPhase(name='specify')
phase.transition_to('running')

# State validation
if not phase.can_transition_to('completed'):
    raise InvalidStateTransitionError(phase.status, 'completed')
```

### Result Aggregation
```python
# Build result from phase states
result = OrchestratorResult.from_phases(phases)
result.status = determine_result_status(phases)
```
