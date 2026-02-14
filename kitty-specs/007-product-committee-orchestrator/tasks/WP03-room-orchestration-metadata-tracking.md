---
work_package_id: WP03
title: Room Orchestration & Metadata Tracking
lane: "doing"
dependencies: []
subtasks:
- T015
- T016
- T017
- T018
- T019
- T020
phase: Foundation
---

## Work Package Prompt: WP03 – Room Orchestration & Metadata Tracking

**Summary**: Implement sequential room execution logic, role prompt validation, status tracking, and metadata generation. This WP manages the core orchestration flow that runs all four debate rooms and collects results for downstream processing.

**Priority**: P1 (Orchestration - core feature)

**Independent Test**: Can run orchestrator with mock subprocess calls to verify all four rooms execute sequentially, statuses are tracked correctly, and metadata.json is generated.

## Context & Constraints

**Reference Documents**:
- [spec.md](spec.md) - Functional requirements FR-001 through FR-005 (room execution), FR-020 through FR-025 (metadata generation)
- [plan.md](plan.md) - Section 0.3 "Retry Logic Research", Section 1.2 "API/CLI Contracts", Section 1.5 "Error Handling Strategy"
- [data-model.md](data-model.md) - CommitteeRun, DebateRoom, RoomStatus entities
- [contracts/metadata_schema.json](contracts/metadata_schema.json) - Target metadata structure

**Architectural Decisions**:
- **Sequential execution**: Rooms run one at a time (CPO → CFO → CTO → BDM)
- **Status tracking**: Each room's status tracked in dict for metadata.json
- **Graceful degradation**: Missing non-TPM prompts skip rooms; TPM prompt missing is fatal
- **File creation**: Output directory created before any rooms run

**Constraints**:
- Must not modify existing `document_debate_cli.py`
- Room execution order is fixed (CPO, CFO, CTO, BDM)
- Status tracking must handle success/failed/skipped states

## Subtasks & Detailed Guidance

### Subtask T015 – Validate role prompt files exist

**Purpose**: Ensure all required role prompt files are present before starting any room executions, providing clear errors if missing.

**Steps**:
1. Create validation function `validate_role_prompts(roles_dir)` that:
   - Checks `tpm.txt` exists in roles_dir
   - Checks for `cpo.txt`, `cfo.txt`, `cto.txt`, `bdm.txt` (optional)
   - Returns tuple: (all_present, missing_files)
2. If `tpm.txt` missing: raise SystemExit with message "TPM prompt file not found at {roles_dir}/tpm.txt. Aborting."
3. If other role prompts missing: log warning for each, return list of missing roles

**Files**:
- `product_committee.py` (add validation function, ~40 lines)
  - Add `validate_role_prompts()` function
  - Add import: `sys`, `os.path`
  - Add docstring explaining validation behavior

**Validation**:
- [ ] `tpm.txt` present → validation passes
- [ ] `tpm.txt` missing → SystemExit with clear error message
- [ ] Other role prompts missing → warnings logged, returned in missing list
- [ ] All prompts exist → empty missing list returned

**Parallel?**: No (validation must complete before any rooms run)

**Notes**:
- Fatal error for TPM is required per spec FR-020
- Warnings for other roles allow graceful degradation per spec edge cases

---

### Subtask T016 – Implement sequential room execution (TPM vs CPO/CFO/CTO/BDM)

**Purpose**: Execute all four debate rooms in fixed sequence using the subprocess wrapper from WP02, collecting results for downstream processing.

**Steps**:
1. Define room configurations list:
   ```python
   ROOMS = [
       {"id": "TPM_vs_CPO", "opponent": "CPO"},
       {"id": "TPM_vs_CFO", "opponent": "CFO"},
       {"id": "TPM_vs_CTO", "opponent": "CTO"},
       {"id": "TPM_vs_BDM", "opponent": "BDM"},
   ]
   ```
2. Create `execute_rooms(prd_path, question, rooms_dir, max_retries, verbose)` function:
   - Validates role prompts (call T015)
   - For each room in ROOMS:
     - Load pro_prompt (tpm.txt) and con_prompt (role-specific)
     - Call `run_debate_room()` from WP02
     - Track result in room_results dict
   - Return list of DebateRoom objects in execution order
3. Ensure sequential execution: rooms run one at a time (not parallel)
4. Return both room_results list and successful_rooms list

**Files**:
- `product_committee.py` (add orchestration logic, ~100 lines)
  - Add `execute_rooms()` function with above logic
  - Add ROOMS configuration constant
  - Add from product_committee.wp02 import run_debate_room, DebateRoom
  - Add exception handling for orchestration-level failures

**Validation**:
- [ ] All four rooms execute in sequence: CPO → CFO → CTO → BDM
- [ ] Each room returns DebateRoom with status populated
- [ ] Room IDs match format: TPM_vs_CPO, TPM_vs_CFO, etc.
- [ ] Successful rooms filtered into separate list for reflection step
- [ ] Room execution is sequential (no parallel calls)

**Parallel?**: No (sequential by spec requirement FR-003)

**Notes**:
- Sequential execution is mandatory for MVP (parallel is future enhancement)
- Room results must be preserved in order for metadata.json
- This is the core orchestration logic that drives the entire feature

---

### Subtask T017 – Track and aggregate room statuses

**Purpose**: Maintain status tracking across all room executions, collecting successful results for reflection step and populating metadata.json room_statuses field.

**Steps**:
1. In `execute_rooms()`, initialize `room_statuses = {}` dict
2. For each room execution:
   - Store result in room_results list by room_id
   - Update room_statuses[room_id.lower()] = result.status
3. Separate rooms into:
   - successful_rooms: list where status == "success"
   - failed_rooms: list where status == "failed"
   - skipped_rooms: list where status == "skipped_missing_prompt"
4. Return tuple: (room_results, room_statuses, successful_rooms, failed_rooms, skipped_rooms)

**Files**:
- `product_committee.py` (add status tracking, ~60 lines)
  - Modify `execute_rooms()` to return status information
  - Add status separation logic
  - Add type hints for return values

**Validation**:
- [ ] room_statuses dict contains all 4 room IDs as keys
- [ ] Each status value is valid: "success", "failed", "skipped_missing_prompt"
- [ ] successful_rooms list contains only rooms with status == "success"
- [ ] failed_rooms and skipped_rooms populated correctly
- [ ] Room order preserved in all lists

**Parallel?**: No (single function's return value)

**Notes**:
- Status tracking is critical for metadata.json generation
- Successful rooms needed for TPM reflection step
- Skipped rooms due to missing prompts should not prevent reflection

---

### Subtask T018 – Collect metadata for run

**Purpose**: Gather all metadata needed for metadata.json including run info, timestamps, warning flags, and error tracking.

**Steps**:
1. Create `CommitteeMetadata` TypedDict with fields:
   - run_id: str (generated or user-provided)
   - prd_path: str
   - question: str
   - model: str (optional)
   - start_time: str (ISO 8601)
   - roles_dir: str
   - max_retries: int
   - room_statuses: dict
   - warning_flags: dict
   - errors: list
2. In `execute_rooms()`, initialize metadata object at start:
   - Set start_time = datetime.utcnow().isoformat()
   - Copy input parameters (prd_path, question, model, etc.)
3. During execution, update metadata:
   - Add room statuses as they complete
   - Append to errors list if any rooms fail
   - Set warning flags for prd_too_short, question_too_short, some_rooms_failed
4. Set end_time when all rooms complete

**Files**:
- `product_committee.py` (add metadata collection, ~70 lines)
  - Add CommitteeMetadata TypedDict at top of file
  - Add metadata initialization in execute_rooms()
  - Add end_time setting after room loop
  - Import datetime for timestamps

**Validation**:
- [ ] run_id is non-empty string
- [ ] start_time and end_time are valid ISO 8601 formats
- [ ] room_statuses matches all executed rooms
- [ ] warning_flags only set when conditions met
- [ ] errors list contains failure details

**Parallel?**: No (metadata is single object)

**Notes**:
- Metadata must be complete before reflection step
- Timestamps must use UTC for consistency
- Warning flags help users identify data quality issues

---

### Subtask T019 – Generate metadata.json output

**Purpose**: Write metadata.json file to output directory with all run information, room statuses, and any warning flags or errors.

**Steps**:
1. Create output directory if not exists:
   ```python
   os.makedirs(output_dir, exist_ok=True)
   ```
2. Generate run_id if not provided via --run-id:
   - Extract first 3-5 words from question
   - Lowercase and hyphenate (e.g., "what is potential" → "what-is-potential")
   - Append to timestamp: RUN_YYYY-MM-DD_HHMMSS_slug
3. Create metadata.json from CommitteeMetadata TypedDict:
   - Include all fields from metadata_schema.json
   - Format room_statuses with all four rooms
   - Include warning_flags and errors if present
4. Write to <output_dir>/RUN_<timestamp>_<slug>/metadata.json with proper formatting

**Files**:
- `product_committee.py` (add metadata generation, ~80 lines)
  - Add `generate_metadata()` function
  - Add slug generation logic
  - Add JSON writing with proper encoding
  - Add from product_committee.wp03 import CommitteeMetadata
  - Add from datetime import datetime

**Validation**:
- [ ] metadata.json created in correct output subdirectory
- [ ] Filename matches format: metadata.json
- [ ] JSON validates against contracts/metadata_schema.json
- [ ] All required fields present (run_id, prd_path, question, etc.)
- [ ] room_statuses contains all four rooms
- [ ] warning_flags populated when conditions met
- [ ] errors list populated when rooms failed

**Parallel?**: No (single file write)

**Notes**:
- metadata.json is critical for debugging and run tracking
- Must be created before reflection step starts
- Schema validation ensures data quality

---

### Subtask T020 – Implement graceful degradation for missing prompts

**Purpose**: Handle missing non-TPM role prompt files gracefully by skipping corresponding rooms and logging warnings, per spec edge cases.

**Steps**:
1. In `validate_role_prompts()` from T015, return list of missing role files
2. In `execute_rooms()` from T016:
   - For each room in ROOMS:
     - Check if opponent prompt file exists
     - If missing: set room status to "skipped_missing_prompt"
     - Log warning: "Role prompt missing: {role}. Skipping {room_id}"
     - Do not execute room (no subprocess call)
3. Ensure skipped rooms don't prevent other rooms from running
4. Ensure skipped rooms are tracked in room_statuses with correct status

**Files**:
- `product_committee.py` (add graceful degradation, ~40 lines)
  - Modify `execute_rooms()` to check opponent prompt existence
  - Add skip logic before subprocess call
  - Add warning logs for skipped rooms
  - Update status tracking to use "skipped_missing_prompt"

**Validation**:
- [ ] Missing tpm.txt → fatal error (no rooms run)
- [ ] Missing cpo.txt → room skipped, warning logged
- [ ] Missing cfo.txt → room skipped, warning logged
- [ ] Missing cto.txt → room skipped, warning logged
- [ ] Missing bdm.txt → room skipped, warning logged
- [ ] Skipped rooms don't crash orchestrator
- [ ] Skipped rooms tracked in metadata with correct status

**Parallel?**: No (sequential room execution)

**Notes**:
- Graceful degradation is key spec requirement
- Only TPM prompt is fatal; others are optional
- This allows partial committee results when some roles are undefined

---

## Test Strategy

Not applicable for this WP (tested in WP06).

## Risks & Mitigations

**Risk**: Room execution order is fixed, may not match user expectations.
- **Mitigation**: Document fixed order in help text; consider adding --room-order flag in future.

**Risk**: Sequential execution may be slow for long PRDs.
- **Mitigation**: Set reasonable timeout per room; log progress timestamps.

**Risk**: Subprocess dependency may be fragile if debate CLI output format changes.
- **Mitigation**: Use robust regex parsing; add examples in comments; monitor exit codes.

## Review Guidance

**Acceptance Criteria**:
- [ ] All four rooms can execute sequentially with mock subprocess
- [ ] Room statuses tracked correctly in metadata
- [ ] Missing non-TPM prompts skip rooms with warnings
- [ ] Missing TPM prompt is fatal error
- [ ] metadata.json generated with all required fields

**Key Checkpoints**:
- Sequential room execution is enforced (no parallel calls)
- Status tracking covers all three states: success, failed, skipped
- Graceful degradation works for optional role prompts
- Metadata generation happens before reflection step

## Activity Log

- 2026-02-14T08:38:48Z – unknown – lane=doing – Starting implementation
