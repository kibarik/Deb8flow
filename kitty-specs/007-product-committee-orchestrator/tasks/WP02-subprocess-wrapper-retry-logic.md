---
work_package_id: WP02
title: Subprocess Wrapper & Retry Logic
lane: "doing"
dependencies: []
subtasks:
- T008
- T009
- T010
- T011
- T012
- T013
- T014
phase: Foundation
agent: "claude"
shell_pid: "73239"
---

## Work Package Prompt: WP02 – Subprocess Wrapper & Retry Logic

**Summary**: Implement subprocess wrapper that invokes `document_debate_cli.py`, parses its output, and handles retries with exponential backoff. This WP enables the orchestrator to run individual debate rooms and recover from transient failures.

**Priority**: P1 (Core Logic - required before orchestration)

**Phase**: Foundation

**Independent Test**: Subprocess wrapper can invoke a mock command and handle timeout/failure, retrying with backoff, and return structured `DebateRoom` result.

## Context & Constraints

**Reference Documents**:
- [spec.md](spec.md) - Functional requirements FR-001 through FR-005 (retry logic), FR-006 (room JSON structure)
- [plan.md](plan.md) - Section 0.3 "Retry Logic Research", Section 1.2 "API/CLI Contracts"
- [data-model.md](data-model.md) - DebateRoom entity definition and status transitions
- [contracts/room_result_schema.json](contracts/room_result_schema.json) - Target JSON structure for room outputs

**Architectural Decisions**:
- **MVP approach**: Subprocess invocation with output parsing (not library refactor yet)
- **Retry strategy**: Exponential backoff (1s, 2s, 4s, ...) up to max_retries
- **Error handling**: Continue after max retries (graceful degradation per spec)
- **Output parsing**: Parse stdout/stderr from debate CLI into structured DebateRoom

**Constraints**:
- Must not modify existing `document_debate_cli.py` in this WP
- Subprocess timeout must be long enough for LLM calls (consider 10+ minute rooms)
- Parse logic must be robust to debate CLI output variations
- Retry count configurable via `--max-retries` flag (default: 2)

## Subtasks & Detailed Guidance

### Subtask T008 – Create subprocess wrapper function for document_debate_cli.py invocation

**Purpose**: Establish the interface for running individual debate rooms via subprocess, abstracting the invocation details from orchestration logic.

**Steps**:
1. Create function `run_debate_room(prd_path, question, pro_prompt, con_prompt, model=None, timeout=None)` in `product_committee.py`
2. Use `subprocess.run()` with:
   - Command: `[sys.executable, document_debate_cli.py, --docx, prd_path, --request, question, --pro-prompt, pro_prompt, --con-prompt, con_prompt]`
   - Add `--model` flag if model parameter provided
   - Set `capture_output=True`, `text=True`, `timeout=timeout` (default 600 seconds)
3. Return tuple: (exit_code, stdout, stderr)

**Files**:
- `product_committee.py` (modify, add ~100 lines)
  - Add imports: `subprocess`, `sys`, `timeout`
  - Add `run_debate_room()` function with docstring
  - Handle `timeout.TimeoutExpired` exception

**Validation**:
- [ ] Function accepts all required parameters (prd_path, question, pro_prompt, con_prompt)
- [ ] Optional model parameter passed through correctly
- [ ] Timeout parameter has sensible default
- [ ] Returns tuple with exit_code, stdout, stderr
- [ ] Docstring explains purpose clearly

**Notes**:
- Timeout should be generous (10+ minutes) since debate rooms involve LLM calls
- This function will be called 4 times (once per room) in orchestration

---

### Subtask T009 – Implement stdout/stderr parsing and DebateRoom JSON extraction

**Purpose**: Parse subprocess output from debate CLI to extract structured room result (positions, verdict, takeaways).

**Steps**:
1. Add `parse_debate_output(exit_code, stdout, stderr)` function that:
2. Validate exit_code (0 = success, non-zero = failure)
3. If exit_code != 0: Return `DebateRoom` with `status="failed"` and error message from stderr
4. If exit_code == 0: Parse stdout to extract:
   - TPM position summary
   - Opponent position summary
   - Judge verdict (winner, explanation)
   - 3-5 key takeaways
5. Return `DebateRoom` object with all required fields populated

**Implementation Notes**:
- For MVP: Use simple string parsing (regex/line-by-line) since debate CLI output format is predictable
- Don't implement full JSON schema validation yet (that's enhancement per plan)
- Extract room_id from pro_prompt/con_prompt filenames (e.g., "TPM_vs_CPO" from "tpm.txt" and "cpo.txt")

**Files**:
- `product_committee.py` (modify, add ~150 lines)
  - Add `DebateRoom` dataclass or TypedDict
  - Add `parse_debate_output()` function with parsing logic
  - Handle various exit codes gracefully

**Validation**:
- [ ] Successful parsing returns DebateRoom with all required fields
- [ ] Failed exit codes return DebateRoom with status="failed"
- [ ] Error messages from stderr captured in failed results
- [ ] Room_id correctly derived from prompt filenames

**Parallel?**: No (single function)

**Notes**:
- Debate CLI output format assumed to be consistent; add examples in comments
- Parsing logic is MVP - future library refactor will eliminate need for this

---

### Subtask T010 – Implement exponential backoff retry logic (1s, 2s, 4s, ...)

**Purpose**: Add retry wrapper around `run_debate_room()` that implements exponential backoff with configurable max attempts.

**Steps**:
1. Add `run_room_with_retries(prd_path, question, pro_prompt, con_prompt, model, max_retries, verbose=False)` function
2. Implement retry loop with:
   - For attempt in range(1, max_retries + 1):
     - Call `run_debate_room()`
     - If success: break loop
     - If failure and attempt < max_retries:
       - Log retry attempt in verbose mode: "Retry {attempt}/{max_retries} after {wait_time}s: {reason}"
       - Wait for 2^(attempt-1) seconds (exponential backoff: 1s, 2s, 4s, ...)
     - If final attempt fails: mark as failed and break
3. Return final `DebateRoom` result (success or failed)

**Files**:
- `product_committee.py` (modify, add ~80 lines)
  - Add `time` import for sleep/retry delays
  - Add `run_room_with_retries()` wrapper function
  - Add logging for retry attempts (verbose only)

**Validation**:
- [ ] Exponential backoff sequence correct (1s, 2s, 4s, 8s, ...)
- [ ] max_retries parameter respected (default 2 from WP01)
- [ ] Verbose logging shows attempt numbers and failure reasons
- [ ] Final attempt failure returns DebateRoom with status="failed"
- [ ] Successful attempt (any retry number) returns DebateRoom with status="success"

**Parallel?**: No (sequential retries by design)

**Notes**:
- Exponential backoff is industry standard for handling transient network/LLM issues
- Each retry waits: 1s, 2s, 4s, 8s, 16s (for max_retries=5)

---

### Subtask T011 – Add retry attempt logging for verbose mode

**Purpose**: Enable detailed logging of retry attempts with failure reasons to help debugging and user visibility.

**Steps**:
1. In `run_room_with_retries()`, add logging statements:
   - Before first attempt: "Starting room {room_id}..."
   - After each failure: "Room {room_id} failed (attempt {attempt}/{max_retries}): {error_message}"
   - Before retry: "Retrying room {room_id} in {wait_time}s..."
   - Final failure: "Room {room_id} failed after {max_retries} attempts"
2. Only log these messages when verbose mode is enabled
3. Use logger.debug() for verbose messages

**Files**:
- `product_committee.py` (modify, add ~40 lines)
  - Add verbose parameter to `run_room_with_retries()`
  - Add logging statements with proper level (debug for verbose)
  - Use f-strings for dynamic messages

**Validation**:
- [ ] Verbose logging shows retry attempts
- [ ] Verbose logging shows failure reasons
- [ ] Normal mode (verbose=False) does not show retry details
- [ ] Final status always logged regardless of verbosity

**Parallel?**: No (logging modifications are isolated)

**Notes**:
- Follow logging strategy from plan Section 1.4
- Debug level is appropriate for detailed operational info

---

### Subtask T012 – Handle subprocess exit codes and exceptions

**Purpose**: Make subprocess wrapper robust to various subprocess failure modes (timeout, non-zero exit, crashes).

**Steps**:
1. Wrap `subprocess.run()` call in try-except block:
2. Handle `subprocess.TimeoutExpired`: Log timeout, return failure with appropriate message
3. Handle `subprocess.CalledProcessError`: Log process error, return failure
4. Handle other exceptions: Log unexpected error, return failure
5. For non-zero exit codes: Check if stderr has error message, include in result

**Files**:
- `product_committee.py` (modify, add ~50 lines)
  - Update `run_debate_room()` with exception handling
  - Add specific error type handling

**Validation**:
- [ ] Timeout exceptions caught and logged
- [ ] Process errors caught and logged
- [ ] Unexpected exceptions caught and logged
- [ ] Non-zero exit codes handled correctly
- [ ] Error messages preserved in DebateRoom results

**Parallel?**: No (single function modifications)

**Notes**:
- All exceptions should be caught and transformed into DebateRoom failures
- Never let subprocess exceptions propagate to orchestrator

---

### Subtask T013 – Create DebateRoom data structure for room results

**Purpose**: Define the data structure that represents a single debate room's execution result for use throughout orchestrator.

**Steps**:
1. Create `DebateRoom` TypedDict or dataclass with fields:
   - room_id: str (e.g., "TPM_vs_CPO")
   - status: Literal["success", "failed", "skipped_missing_prompt"]
   - timestamp: str (ISO 8601)
   - tpm_position: str
   - opponent_position: str
   - opponent_role: str ("CPO", "CFO", "CTO", "BDM")
   - judge_verdict: dict (winner, explanation, optional scores)
   - takeaways: list[str] (3-5 items)
   - error: Optional[str] (if status="failed")
2. Add helper function `create_debate_room(room_id, opponent_role)` that returns initialized structure
3. Add helper function `room_failed(room_id, opponent_role, error_message)` that returns failed structure

**Files**:
- `product_committee.py` (modify, add ~80 lines)
  - Add `DebateRoom` TypedDict at top of file
  - Add helper functions with docstrings
  - Import typing: Optional, Literal, List, Dict

**Validation**:
- [ ] DebateRoom has all required fields from data-model.md
- [ ] Status enum matches spec (success/failed/skipped_missing_prompt)
- [ ] Helper functions return properly initialized structures
- [ ] Optional fields (error, scores) are truly optional

**Parallel?**: No (data structure definition)

**Notes**:
- Using TypedDict or dataclass enables type checking and IDE autocomplete
- Helper functions make it easy to create success/failure variants

---

### Subtask T014 – Implement room status determination (success/failed/skipped)

**Purpose**: Add logic to determine and set appropriate room status based on execution outcome (success, failure after retries, or skipped due to missing prompt).

**Steps**:
1. In `run_room_with_retries()` or orchestration layer, add status logic:
2. For success: Set `status="success"` in DebateRoom result
3. For failure after max_retries: Set `status="failed"` with error message
4. For missing prompt file: Set `status="skipped_missing_prompt"` with warning log
5. Ensure timestamp is set to current time in ISO 8601 format

**Files**:
- `product_committee.py` (modify, add ~60 lines)
  - Add status determination logic in relevant functions
  - Add timestamp generation using `datetime.datetime.utcnow().isoformat()`
  - Add from datetime import

**Validation**:
- [ ] Success status set correctly on successful room completion
- [ ] Failed status set correctly after max retries exhausted
- [ ] Skipped status set correctly for missing non-TPM prompts
- [ ] Timestamp format matches ISO 8601 standard
- [ ] TPM prompt missing is fatal error (not skipped status)

**Parallel?**: No (status determination is isolated)

**Notes**:
- Status is critical for metadata.json and reflection step
- Skipped rooms must not prevent other rooms from running

---

## Test Strategy

Not applicable for this WP (unit tests in WP06).

## Risks & Mitigations

**Risk**: Debate CLI output format may change, breaking parsing logic.
- **Mitigation**: Add example outputs in comments, make parsing flexible with regex patterns

**Risk**: Subprocess timeout may be too short for slow LLM responses.
- **Mitigation**: Make timeout configurable per room or globally via CLI flag

**Risk**: Retry logic may hide transient vs. permanent failures.
- **Mitigation**: Log all failure reasons clearly in verbose mode

## Review Guidance

**Acceptance Criteria**:
- [ ] `run_debate_room()` successfully invokes debate CLI via subprocess
- [ ] DebateRoom results correctly structured with status, positions, verdict, takeaways
- [ ] Exponential backoff retry logic works correctly (1s, 2s, 4s, ...)
- [ ] max_retries parameter respected
- [ ] Verbose logging shows retry attempts and failure reasons
- [ ] All exception types handled (timeout, process error, unexpected)
- [ ] Status determination matches spec requirements

**Key Checkpoints**:
- Subprocess wrapper is abstracted from orchestration logic
- Retry strategy is exponential and configurable
- Error handling transforms exceptions into DebateRoom failures
- DebateRoom structure matches data-model.md definition

**Context for Reviewers**:
- This WP is the core interface between orchestrator and existing debate system
- Focus review on robustness of subprocess handling and retry logic
- Verify parsing logic is resilient to debate CLI output variations

## Activity Log

- 2026-02-14T08:38:48Z – unknown – lane=doing – Starting implementation
- 2026-02-14T08:39:00Z – unknown – lane=for_review – Implementation complete, ready for review
- 2026-02-14T08:39:06Z – claude – shell_pid=73239 – lane=doing – Started review via workflow command
