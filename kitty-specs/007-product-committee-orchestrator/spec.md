# Feature Specification: Product Committee Orchestrator

**Feature Branch**: `007-product-committee-orchestrator`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description provided via `/spec-kitty.specify`

## Clarifications

### Session 2026-02-14

- Q: How should the "compressed PRD brief" in FR-009 be generated? → A: Compressed PRD brief is formed by product_committee.py via automatic compression of PRD to 500-1500 words using a separate model call
- Q: Should --allow-short-prd be added to CLI interface? → A: Yes, added as FR-041 (optional flag that enforces minimum PRD length and aborts if < 100 chars when set)
- Q: What format should room_id and room_status have in JSON outputs? → A: room_id is string (e.g., "TPM_vs_CPO"), room_status is "success" | "failed" | "skipped_missing_prompt" in both metadata.json and each room JSON
- Q: How should --model flag be passed to underlying script? → A: Pass --model value through to document_debate_cli.py if supported; otherwise ignore with warning
- Q: Is SC-006 (10-minute runtime) a hard SLA? → A: No, it's a soft target; violations don't count as feature failure but should be documented

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Committee Review (Priority: P1)

A product manager, founder, or consultant has drafted a PRD document and wants to stress-test it with a virtual product committee before presenting to real stakeholders. They run the orchestrator with their PRD and a strategic question (e.g., "what's the potential of this project?"). The system runs four debate rooms sequentially and produces a comprehensive report showing how their idea holds up against CPO, CFO, CTO, and BDM perspectives, plus TPM's synthesized self-reflection.

**Why this priority**: This is the core value proposition - providing multi-perspective PRD review without needing to schedule actual stakeholder meetings.

**Independent Test**: Can be fully tested by running `product_committee.py` with a sample PRD and question, verifying all four rooms complete, and confirming both JSON artifacts and final markdown report are generated with differentiated perspectives.

**Acceptance Scenarios**:

1. **Given** a valid PRD file (.docx or text) exists, **When** user runs `python product_committee.py --prd path/to/prd.docx --question "what's the potential?"`, **Then** all four debate rooms execute sequentially and produce structured JSON outputs plus a final markdown report in a timestamped output directory.
2. **Given** all four rooms complete successfully, **When** user opens `final_report.md`, **Then** they see clearly differentiated summaries from each role (CPO, CFO, CTO, BDM) and TPM's synthesized recommendations.

---

### User Story 2 - Graceful Partial Failure Handling (Priority: P2)

A user runs the committee review, but network issues cause one room (e.g., TPM vs CFO) to fail after retries. The system continues running the remaining rooms and still produces a final report, explicitly noting which perspective is missing and allowing TPM self-reflection to proceed with available data.

**Why this priority**: Ensures users get value even when things go wrong, rather than losing the entire run due to a single room failure.

**Independent Test**: Can be tested by artificially failing one room (e.g., invalid prompt file or network interruption) and verifying that other rooms complete, metadata correctly marks the failed room, and final report acknowledges the missing perspective.

**Acceptance Scenarios**:

1. **Given** one debate room fails after retries, **When** the failure occurs, **Then** the system logs the error, marks the room as failed in metadata, and continues to the next room.
2. **Given** one or more rooms have failed, **When** TPM self-reflection runs, **Then** it receives information about which rooms succeeded/failed and adapts its analysis accordingly, explicitly noting missing perspectives in the final report.

---

### User Story 3 - Iterative PRD Refinement (Priority: P3)

After receiving the committee report, a user makes edits to their PRD based on the feedback and reruns the orchestrator to see if their changes address the concerns raised. The new run creates a separate timestamped output folder, allowing comparison of results before and after changes.

**Why this priority**: Supports the intended iterative workflow where PRDs are reviewed multiple times as they evolve.

**Independent Test**: Can be tested by running the orchestrator twice with the same PRD, verifying that two separate timestamped output directories are created with independent results and metadata.

**Acceptance Scenarios**:

1. **Given** a previous committee run exists, **When** user runs the orchestrator again (with or without PRD changes), **Then** a new timestamped output folder is created without overwriting previous results.
2. **Given** a user has modified their PRD based on previous feedback, **When** they run the orchestrator again, **Then** they can compare the new report against the previous one to see if concerns were addressed.

---

### User Story 4 - Flexible Role Configuration (Priority: P4)

A user wants to use custom role prompts (e.g., industry-specific executive personas) or has stored role prompts in a non-standard location. They use `--roles-dir` to point to their custom prompt directory, and the system uses those prompts instead of the defaults.

**Why this priority**: Enables customization and advanced use cases without requiring code changes.

**Independent Test**: Can be tested by creating a custom roles directory with modified prompts and running with `--roles-dir`, verifying the system uses the custom prompts.

**Acceptance Scenarios**:

1. **Given** a custom roles directory exists with valid role prompt files, **When** user runs `product_committee.py --roles-dir /path/to/custom_roles`, **Then** the system loads prompts from the custom directory instead of the default `prompts/roles/`.

---

### Edge Cases

**Input Validation Edge Cases**:

- PRD file does not exist or is unreadable → Immediate error with clear message, non-zero exit code, no rooms run
- PRD file is empty or contains < 100 characters → Warning logged, `prd_too_short: true` in metadata, run allowed to proceed (unless `--allow-short-prd` is set, in which case error and abort instead)
- Question is empty or contains < 5 characters → Error, require non-empty question before proceeding
- Question is very short but valid → Warning logged recommending reformulation, but run allowed

**Role Prompt Edge Cases**:

- `prompts/roles/tpm.txt` is missing → Fatal error, abort immediately (no TPM = no committee)
- Any other role prompt file is missing → Warning logged, room marked as `skipped_missing_prompt` in metadata, other rooms continue
- Role prompt file exists but is empty → Warning logged, room may produce poor quality results but still runs

**Execution Edge Cases**:

- All four rooms fail → Self-reflection still runs with zero room data, acknowledges no perspectives were available
- Only one room succeeds → Self-reflection runs with single perspective, explicitly notes limited data in report
- Network timeout during a room → Retry up to `--max-retries` times, then mark failed if still timing out
- LLM API rate limiting during a room → Retry with exponential backoff up to `--max-retries`

**Output Edge Cases**:

- Output directory does not exist → Create the directory tree as needed
- Output directory is not writable → Error before any rooms run, with clear message
- Disk space insufficient during run → Best effort to complete, but error if critical writes fail
- Same `--run-id` used twice → Overwrite previous run (user responsibility)

**Large Document Edge Cases**:

- PRD is 30-50 pages or larger → Parse and run, but may exceed target runtime
- PRD contains mixed languages (e.g., English + Russian) → System should handle and produce coherent output
- PRD contains only images or non-text content → Warning about low text content, but proceed if user insists

## Requirements *(mandatory)*

### Functional Requirements

**Core Orchestration**:

- **FR-001**: System MUST run four separate debate rooms sequentially: TPM vs CPO, TPM vs CFO, TPM vs CTO, and TPM vs BDM
- **FR-002**: Each room MUST invoke `document_debate_cli.py` with the PRD path, the user's question, TPM's prompt file as PRO, and the role-specific prompt file as CON
- **FR-003**: System MUST execute rooms one at a time, not in parallel
- **FR-004**: System MUST retry failed rooms up to the specified `--max-retries` count (default: 2)
- **FR-005**: System MUST mark a room as failed after exhausting retries, log the failure reason, and continue to the next room

**Room Output Capture**:

- **FR-006**: Each room MUST produce a JSON file containing at least: room ID (string, e.g., "TPM_vs_CPO"), TPM position summary, opponent position summary, judge verdict (winner + explanation), and 3-5 key takeaways
- **FR-007**: Room JSON files MUST be named `tpm_cpo.json`, `tpm_cfo.json`, `tpm_cto.json`, and `tpm_bdm.json` respectively

**TPM Self-Reflection**:

- **FR-008**: System MUST run TPM self-reflection after all four rooms complete
- **FR-009**: Self-reflection MUST receive as input: a compressed PRD brief (formed by product_committee.py via automatic compression of PRD to 500-1500 words using a separate model call), the original question, and all successful room JSON results
- **FR-010**: Self-reflection MUST always run, even if zero rooms succeeded
- **FR-011**: Self-reflection MUST produce: what TPM learned from each role, updated project potential assessment, concrete recommendations for PRD author, and which arguments were accepted/rejected
- **FR-012**: Self-reflection output MUST be saved as `tpm_reflection.json`

**Input Handling**:

- **FR-013**: System MUST accept PRD input via `--prd` or `--docx` flag (synonyms)
- **FR-014**: System MUST accept the committee question via `--question` flag
- **FR-015**: System MUST validate PRD file exists and is readable before running any rooms
- **FR-016**: System MUST validate question is non-empty before running any rooms
- **FR-017**: System MUST warn but allow proceeding if PRD is < 100 characters (unless `--allow-short-prd` flag is set to require minimum)

**Role Prompt Management**:

- **FR-018**: System MUST load role prompt files from `prompts/roles/` directory by default
- **FR-019**: System MUST support overriding the roles directory via `--roles-dir` flag
- **FR-020**: System MUST fail immediately if `tpm.txt` is missing from the roles directory
- **FR-021**: System MUST skip a room (mark as `skipped_missing_prompt`) if that role's prompt file is missing (for non-TPM roles)

**Output Organization**:

- **FR-022**: System MUST create a timestamped run subdirectory under `--output-dir` with format `RUN_YYYY-MM-DD_HHMMSS_slug`
- **FR-023**: System MUST save all room JSONs, reflection JSON, final report, and metadata in the run subdirectory
- **FR-024**: System MUST generate `final_report.md` as a human-readable summary of all rooms and reflection
- **FR-025**: System MUST generate `metadata.json` containing: PRD path, question, model, timestamps, role prompt paths, per-room status, and warning flags

**CLI Interface**:

- **FR-026**: System MUST provide `--prd`/`--docx` (required) for PRD file path
- **FR-027**: System MUST provide `--question` (required) for the committee question
- **FR-028**: System MUST provide `--model` (optional, passed through to underlying debate CLI if that script supports it; otherwise MAY ignore with warning)
- **FR-029**: System MUST provide `--max-retries` (optional, default 2) for retry count per room
- **FR-030**: System MUST provide `--output-dir` (optional, default `./committee_output`) for base output location
- **FR-031**: System MUST provide `--roles-dir` (optional, default `prompts/roles/`) for role prompt location
- **FR-032**: System MUST provide `--run-id` (optional) for manual run identifier override
- **FR-041**: System MUST provide `--allow-short-prd` (optional) that, when set, enforces minimum PRD length and aborts run if PRD < 100 characters

**Error Handling**:

- **FR-033**: System MUST exit with non-zero code if PRD file is missing/unreadable
- **FR-034**: System MUST exit with non-zero code if question is empty
- **FR-035**: System MUST exit with non-zero code if TPM prompt file is missing
- **FR-036**: System MUST NOT exit with non-zero code if individual rooms fail (only for unrecoverable setup errors)

**Final Report Content**:

- **FR-037**: `final_report.md` MUST include brief summary of each room (TPM position, opponent position, judge verdict)
- **FR-038**: `final_report.md` MUST include TPM self-reflection content
- **FR-039**: `final_report.md` MUST explicitly note which rooms failed or were skipped
- **FR-040**: `final_report.md` MUST present concrete, actionable recommendations rather than generic advice

### Key Entities

- **Committee Run**: Represents a single execution of the product committee orchestrator with a specific PRD and question. Contains all room results, reflection, and metadata.
- **Debate Room**: Represents one perspective matchup (TPM vs CPO/CFO/CTO/BDM). Contains structured JSON output with positions, verdict, and takeaways.
- **Room Status**: The execution state of a debate room. Possible values: `success`, `failed` (after retries), `skipped_missing_prompt`. Stored as `status` field in metadata.json and, where possible, in each room JSON.
- **TPM Reflection**: The synthesized analysis produced after all rooms complete. Contains learned insights, updated potential assessment, and recommendations.
- **Run Metadata**: Administrative data about the committee run. Contains input paths, timestamps, model info, room statuses, and warning flags.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A full committee run (all available rooms + self-reflection) completes without unhandled exceptions for a valid PRD and question
- **SC-002**: Partial failures (1-3 rooms) are correctly surfaced in both `metadata.json` (with status codes) and `final_report.md` (with explicit notes about missing perspectives), without causing the entire run to fail
- **SC-003**: `final_report.md` contains clearly differentiated perspectives per role rather than repetitive or generic content
- **SC-004**: `final_report.md` provides at least 3 concrete, actionable recommendations that a user can apply to revise their PRD
- **SC-005**: Users are able to iteratively rerun the orchestrator after editing their PRD, with each run creating an independent timestamped output folder
- **SC-006**: A complete run with all four rooms succeeds and produces all expected artifacts (4 room JSONs + reflection JSON + final report + metadata) in under 10 minutes on a local laptop with standard network conditions (soft target, not hard SLA; violations don't count as feature failure but should be documented)
