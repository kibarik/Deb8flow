# Data Model: Product Committee Orchestrator

**Feature**: 007-product-committee-orchestrator
**Date**: 2026-02-14
**Status**: Complete

## Overview

This document defines the data entities, their attributes, relationships, and state transitions for the Product Committee Orchestrator feature.

## Entity Definitions

### CommitteeRun

**Description**: Represents a single execution of the product committee orchestrator with a specific PRD and question.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string | Yes | Unique identifier (timestamp-based or user-provided via --run-id) |
| `prd_path` | string | Yes | Path to the PRD document (absolute or relative) |
| `question` | string | Yes | The committee question posed to all rooms |
| `model` | string | No | LLM model name (if specified via --model) |
| `start_time` | datetime | Yes | Orchestrator start timestamp |
| `end_time` | datetime | Yes | Orchestrator completion timestamp |
| `max_retries` | integer | Yes | Maximum retry attempts per room (default: 2) |
| `roles_dir` | string | Yes | Directory where role prompt files were loaded |
| `output_dir` | string | Yes | Directory where run artifacts were saved |

**Relationships**:
- Has 4 `DebateRoom` entities (one per role matchup)
- Has 1 `TPMReflection` entity
- Has 1 `RunMetadata` entity

**State Transitions**: None (immutable record of execution)

---

### DebateRoom

**Description**: Represents one perspective matchup (TPM vs CPO/CFO/CTO/BDM) with execution status and results.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `room_id` | string | Yes | Room identifier (e.g., "TPM_vs_CPO", "TPM_vs_CFO") |
| `status` | enum | Yes | Execution status: `success`, `failed`, `skipped_missing_prompt` |
| `timestamp` | datetime | Yes | Room completion timestamp |
| `tpm_position` | string | Yes | Summary of TPM's position |
| `opponent_position` | string | Yes | Summary of opponent's position |
| `opponent_role` | string | Yes | Opponent role name (CPO, CFO, CTO, or BDM) |
| `judge_verdict` | object | Yes | Judge's assessment (winner + explanation) |
| `takeaways` | array[string] | Yes | 3-5 key insights for TPM |
| `error` | string | No | Error message if status is `failed` |

**Relationships**:
- Belongs to 1 `CommitteeRun`
- Produces 1 `RoomResult` (JSON output)

**State Transitions**:

```
[start] → [running] → [success] ✓
               ↓            ↓
               [failed]     [skipped_missing_prompt] ✓
```

**State Transition Rules**:
- `running` → `success`: Room completes successfully, all data captured
- `running` → `failed`: Room fails after max retries exhausted
- `[start]` → `skipped_missing_prompt`: Prompt file missing, room never runs

---

### TPMReflection

**Description**: The synthesized analysis produced after all rooms complete. Contains learned insights, updated potential assessment, and recommendations.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `timestamp` | datetime | Yes | Reflection completion timestamp |
| `learned_insights` | object | Yes | What TPM learned from each participating role |
| `potential_assessment` | object | Yes | Updated view on project potential (overall + confidence) |
| `recommendations` | array[object] | Yes | Concrete recommendations for PRD author |
| `argument_decisions` | array[object] | Yes | Which arguments TPM accepts/rejects and why |
| `missing_perspectives` | array[object] | No | Notes on missing perspectives (if any rooms failed) |
| `hypotheses_to_test` | array[string] | No | Suggested hypotheses to validate |
| `risks_prioritized` | array[object] | No | Key risks identified, prioritized |

**Relationships**:
- Belongs to 1 `CommitteeRun`
- Consumes all successful `DebateRoom` results as input
- Produces 1 `ReflectionResult` (JSON output)

**State Transitions**: None (immutable result)

---

### RoomStatus (Enum)

**Description**: The execution state of a debate room.

**Values**:

| Value | Description |
|-------|-------------|
| `success` | Room completed successfully, all data captured |
| `failed` | Room failed after exhausting retry attempts |
| `skipped_missing_prompt` | Room never ran due to missing role prompt file |

**Usage**: Stored in `DebateRoom.status` and `RunMetadata.room_statuses`

---

### RunMetadata

**Description**: Administrative data about a committee run. Contains input paths, timestamps, model info, room statuses, and warning flags.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string | Yes | Same as CommitteeRun.run_id |
| `prd_path` | string | Yes | Same as CommitteeRun.prd_path |
| `question` | string | Yes | Same as CommitteeRun.question |
| `model` | string | No | Same as CommitteeRun.model |
| `start_time` | string | Yes | ISO 8601 format |
| `end_time` | string | Yes | ISO 8601 format |
| `room_statuses` | object | Yes | Status of each room (tpm_cpo, tpm_cfo, tpm_cto, tpm_bdm) |
| `roles_dir` | string | Yes | Same as CommitteeRun.roles_dir |
| `output_dir` | string | No | Same as CommitteeRun.output_dir |
| `max_retries` | integer | No | Same as CommitteeRun.max_retries |
| `warning_flags` | object | No | Flags: prd_too_short, question_too_short, some_rooms_failed |
| `errors` | array[object] | No | Non-fatal errors encountered |
| `version` | string | No | Orchestrator version |

**Relationships**:
- Describes 1 `CommitteeRun`
- Aggregates statuses of 4 `DebateRoom` entities

---

## Entity Relationships

```
CommitteeRun (1)
    ├── DebateRoom (4) ──→ RoomResult (4 JSON files)
    ├── TPMReflection (1) ──→ ReflectionResult (1 JSON file)
    └── RunMetadata (1) ──→ metadata.json
```

**Cardinality Notes**:
- CommitteeRun has exactly 4 DebateRoom instances (one per role)
- CommitteeRun has exactly 1 TPMReflection (always runs, even with 0 successful rooms)
- CommitteeRun has exactly 1 RunMetadata
- Each DebateRoom produces exactly 1 RoomResult JSON file
- TPMReflection produces exactly 1 ReflectionResult JSON file
- RunMetadata produces exactly 1 metadata.json file

## Data Flow

```
[User Input]
    │
    ├── PRD document
    ├── Question
    └── CLI flags (--model, --max-retries, etc.)
    ↓
[CommitteeRun Orchestrator]
    │
    ├── [Validate Input]
    │     ├── PRD exists/readable?
    │     ├── Question non-empty?
    │     └── TPM prompt exists?
    │
    ├── [Room 1: TPM vs CPO] ──→ DebateRoom(status=...)
    ├── [Room 2: TPM vs CFO] ──→ DebateRoom(status=...)
    ├── [Room 3: TPM vs CTO] ──→ DebateRoom(status=...)
    └── [Room 4: TPM vs BDM] ──→ DebateRoom(status=...)
    │
    ├── [Collect Successful Room Results]
    │     └── Filter rooms where status == "success"
    │
    └── [TPM Self-Reflection] ──→ TPMReflection
    │
    ├── [Generate Artifacts]
    │     ├── tpm_cpo.json, tpm_cfo.json, tpm_cto.json, tpm_bdm.json
    │     ├── tpm_reflection.json
    │     ├── metadata.json
    │     └── final_report.md
    │
    └── [Output]
          └── RUN_<timestamp>_<slug>/
```

## Validation Rules

### CommitteeRun
- `prd_path` must exist and be readable
- `question` must be non-empty string
- `tpm.txt` must exist in `roles_dir`
- `max_retries` must be >= 0

### DebateRoom
- `room_id` must match pattern `^TPM_vs_(CPO|CFO|CTO|BDM)$`
- `status` must be one of: `success`, `failed`, `skipped_missing_prompt`
- If `status == "success"`, all result fields required
- If `status == "failed"`, `error` field required
- `takeaways` array must have 3-5 items (if status == success)

### TPMReflection
- `learned_insights` only includes rooms that succeeded
- `recommendations` array must have >= 1 item
- `potential_assessment.overall` required
- `potential_assessment.confidence` must be: high, moderate, or low

### RunMetadata
- `room_statuses` must include all 4 rooms
- Each room status must be valid enum value
- `warning_flags` are optional, default to false if omitted

## JSON Schema References

See [contracts/](contracts/) directory for detailed JSON schemas:

- `room_result_schema.json`: DebateRoom output format
- `reflection_schema.json`: TPMReflection output format
- `metadata_schema.json`: RunMetadata output format

All JSON outputs must validate against their respective schemas.
