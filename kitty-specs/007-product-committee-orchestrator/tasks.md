# Work Packages: Product Committee Orchestrator

**Feature**: 007-product-committee-orchestrator
**Date**: 2026-02-14
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Overview

This document outlines all work packages for implementing the Product Committee Orchestrator feature. Work packages are organized by phase and priority, with each package being independently implementable and testable.

**Total Work Packages**: 6

**Total Subtasks**: 35
**Estimated Prompt Size**: ~1,800 lines

### Package Summary

| WP | Title | Phase | Priority | Subtasks | Est. Lines | Dependencies |
|----|--------|--------|----------|--------------|--------------|
| WP01 | Foundation & CLI Scaffolding | Foundation | P1 | 7 | ~300 | - |
| WP02 | Subprocess Wrapper & Retry Logic | Foundation | P1 | 7 | ~350 | WP01 |
| WP03 | Room Orchestration & Metadata Tracking | Foundation | P1 | 6 | ~300 | WP01, WP02 |
| WP04 | Self-Reflection Integration | Foundation | P1 | 4 | ~200 | WP01, WP02, WP03 |
| WP05 | Report Generation & Formatting | Foundation | P1 | 6 | ~300 | WP01, WP02, WP03, WP04 |
| WP06 | Testing & Validation | Polish | P1 | 6 | ~350 | WP01, WP02, WP03, WP04, WP05 |

**Size Distribution**:
- WP01: 300 lines ✓ (ideal: 200-500)
- WP02: 350 lines ✓ (ideal: 200-500)
- WP03: 300 lines ✓ (ideal: 200-500)
- WP04: 200 lines ✓ (ideal: 200-500)
- WP05: 300 lines ✓ (ideal: 200-500)
- WP06: 350 lines ✓ (ideal: 200-500)

**Validation**: ✓ All WPs within ideal size range (3-7 subtasks, 200-500 lines)

### Parallelization Opportunities

- WP02, WP03, WP04 can start after WP01 completes (subprocess wrapper available)
- WP05 can start after WP02 completes (reflection integration available)
- WP06 can run in parallel with implementation WPs (after foundational work complete)

---

## Work Packages

### WP01: Foundation & CLI Scaffolding

**Summary**: Set up foundational CLI structure for `product_committee.py` with all required and optional arguments, logging infrastructure, and basic project skeleton.

**Priority**: P1 (Foundation - must complete first)

**Independent Test**: Run `product_committee.py --help` and see all CLI arguments with proper descriptions and defaults.

**Subtasks**:
- [x] T001: Create `product_committee.py` with basic structure
- [x] T002: Implement argparse/click argument parsing
- [x] T003: Add `--prd`/`--docx` required argument with validation
- [ ] T004: Add `--question` required argument with validation
- [ ] T005: Add optional arguments: `--model`, `--max-retries`, `--output-dir`, `--roles-dir`, `--run-id`, `--allow-short-prd`, `--verbose`, `--quiet`
- [ ] T006: Implement Python logging infrastructure with configurable levels
- [ ] T007: Add `--help` argument with descriptive usage message

**Implementation Notes**:
- Use argparse or click based on existing project patterns
- Define argument defaults per spec (max-retries=2, output-dir=./committee_output, roles-dir=prompts/roles/)
- Set up logging with three levels: default (normal), verbose, quiet
- Create basic `if __name__ == "__main__":` block with `main()` call
- Add docstring describing orchestrator's purpose

**Parallel Opportunities**: None (foundational work)

**Dependencies**: None

**Risks**:
- Argument parsing complexity may grow; keep CLI focused on MVP scope
- Logging configuration must not interfere with subprocess output

---

### WP02: Subprocess Wrapper & Retry Logic

**Summary**: Implement subprocess wrapper that invokes `document_debate_cli.py`, parses its output, and handles retries with exponential backoff. This WP enables orchestrator to run individual debate rooms and recover from transient failures.

**Priority**: P1 (Core Logic - required before orchestration)

**Independent Test**: Subprocess wrapper can invoke a mock command, handle timeout/failure, retrying with backoff, and return structured `DebateRoom` result.

**Subtasks**:
- [ ] T008: Create subprocess wrapper function for `document_debate_cli.py` invocation
- [ ] T009: Implement stdout/stderr parsing and `DebateRoom` JSON extraction
- [ ] T010: Implement exponential backoff retry logic (1s, 2s, 4s, 8s, ...)
- [ ] T011: Add retry attempt logging for verbose mode
- [ ] T012: Handle subprocess exit codes and exceptions
- [ ] T013: Create `DebateRoom` data structure for room results
- [ ] T014: Add helper function `create_debate_room(room_id, opponent_role)` that returns initialized structure
- [ ] T015: Implement room status determination (success/failed)

**Implementation Notes**:
- Subprocess wrapper should accept: prd_path, question, pro_prompt, con_prompt, model
- Use `subprocess.run()` with timeout and capture=True
- Parse output from stdout/stderr into DebateRoom structure
- Exponential backoff: wait 2^n seconds (1s, 2s, 4s, 8s, ...)
- Log each retry attempt in verbose mode only
- For MVP: Use simple string parsing (regex/line-by-line) since debate CLI output format is predictable
- DebateRoom structure: room_id, status, timestamp, tpm_position, opponent_position, judge_verdict, takeaways, error

**Parallel Opportunities**: None (sequential subprocess calls by design)

**Dependencies**: WP01

**Risks**:
- Subprocess output parsing may be fragile; rely on structured JSON from debate CLI
- Timeout handling must balance between allowing long LLM calls and detecting hangs
- Retry logic may hide transient vs. permanent failures
- Early failure detection important - user needs to know if debate is working vs. crashed

**Review Guidance**:
- Subprocess wrapper is abstracted from orchestration logic
- Focus review on robustness of subprocess handling, retry logic, and DebateRoom structure
- Verify parsing logic handles various exit codes and stderr formats
- Ensure timeout exceptions are caught and logged appropriately

---

### WP03: Room Orchestration & Metadata Tracking

**Summary**: Implement sequential room execution logic, role prompt validation, status tracking, and metadata generation. This WP manages core orchestration flow that runs all four debate rooms and collects results for downstream processing.

**Priority**: P1 (Orchestration - core feature)

**Independent Test**: Orchestrator can run all four rooms sequentially, track statuses correctly in metadata, and generate metadata.json.

**Subtasks**:
- [ ] T015: Validate role prompt files exist (tpm.txt required, others optional)
- [ ] T016: Implement sequential room execution (TPM vs CPO/CFO/CTO/BDM) in fixed order
- [ ] T017: Collect successful room results for reflection input
- [ ] T018: Generate metadata.json with run info, room statuses, warning flags, error tracking
- [ ] T019: Handle missing non-TPM role prompts (skip room, log warning)
- [ ] T020: Implement status tracking per room (success/failed/skipped_missing_prompt)

**Implementation Notes**:
- Room execution order: CPO → CFO → CTO → BDM (fixed for MVP)
- Track room statuses in dict for metadata.json: room_statuses[room_id.lower()] = result.status
- For missing non-TPM prompts: mark as skipped_missing_prompt, log warning, don't execute room
- Collect successful room results in separate list for reflection step
- Timestamps must use ISO 8601 format (datetime.utcnow().isoformat())
- Metadata file includes: run_id, prd_path, question, model, roles_dir, start_time, end_time, room_statuses, warning_flags, errors

**Parallel Opportunities**: None (sequential by spec requirement)

**Dependencies**: WP01, WP02

**Risks**:
- Sequential execution means total runtime = sum of all rooms; ensure logging shows progress
- Missing TPM prompt must be fatal; missing others are warnings
- Metadata generation must happen after all rooms complete

**Review Guidance**:
- Status tracking is critical for metadata.json correctness
- Room execution order is fixed; verify it matches spec
- Ensure missing role prompts don't prevent other rooms from running
- Verify warning_flags are set correctly based on conditions

---

### WP04: Self-Reflection Integration

**Summary**: Implement TPM self-reflection subprocess call that consumes PRD, question, and all successful room results, then generates reflection JSON with learned insights and recommendations. This WP completes core orchestration flow before report generation.

**Priority**: P1 (Reflection - required for report generation)

**Independent Test**: Reflection subprocess can be invoked with mock room data and produces valid `tpm_reflection.json` per schema.

**Subtasks**:
- [ ] T021: Create `prompts/tpm_reflection.txt` with structured output instructions
- [ ] T022: Implement self-reflection subprocess invocation function
- [ ] T023: Parse reflection JSON output from stdout
- [ ] T024: Handle zero successful rooms case (adapt prompt, note missing perspectives)
- [ ] T025: Validate parsed JSON against `reflection_schema.json`

**Implementation Notes**:
- Reflection prompt must request JSON output matching reflection_schema.json
- Prompt receives: PRD content, question, successful room JSONs
- For zero successful rooms: prompt explicitly notes lack of perspectives
- Subprocess invocation similar to rooms but with reflection-specific prompt
- Timeout should be generous (debates are longer - synthesis takes time)

**Parallel Opportunities**: None (runs after all rooms)

**Dependencies**: WP01, WP02, WP03

**Risks**:
- Reflection prompt quality directly impacts reflection JSON quality and final report quality
- Must handle edge case of 0 successful rooms gracefully
- Consider adding "think step by step" instructions for complex synthesis

**Review Guidance**:
- Reflection prompt is distinct from debate prompts (synthesis vs. adversarial mode)
- Ensure JSON output is validated against schema
- Zero-room case is important edge case; test thoroughly

---

### WP05: Report Generation & Formatting

**Summary**: Implement final markdown report generator that synthesizes all room results, reflection, and metadata into human-readable committee report with all required sections.

**Priority**: P1 (Reporting - primary user output)

**Independent Test**: Report generator can process mock room/reflecton data and produce valid `final_report.md` with all sections populated.

**Subtasks**:
- [ ] T025: Implement markdown report structure with all required sections
- [ ] T026: Format room summaries (TPM position, opponent position, judge verdict, takeaways)
- [ ] T027: Format reflection content (learned insights, potential assessment, recommendations)
- [ ] T028: Explicitly note which rooms failed/skipped in report
- [ ] T029: Add metadata footer with generation timestamp
- [ ] T030: Generate output filename: `<output_dir>/RUN_<timestamp>_<slug>/final_report.md`

**Implementation Notes**:
- Report structure: Title, Executive Summary, Room-by-Room Analysis, TPM Reflection, Recommendations, Missing Perspectives, Metadata
- Room summaries: 3-5 takeaways per room, judge verdict
- Reflection: Learned insights by role, potential assessment (overall + confidence)
- Recommendations: Numbered, with priorities (high/medium/low), actionable
- Slug generation: lowercase, hyphenate first 3-5 words from question
- Use f-strings for multi-line templates

**Parallel Opportunities**: None (depends on all previous WPs)

**Dependencies**: WP01, WP02, WP03, WP04

**Risks**:
- Report formatting may be complex and error-prone with manual string concatenation
- Large PRDs may create very long reports; ensure readability
- Missing rooms should be clearly noted; graceful degradation verified

**Review Guidance**:
- Report is primary user-facing output; quality matters most
- Test with mock data covering full pipeline (rooms + reflection + metadata)
- Ensure markdown formatting is valid and readable
- Verify all required sections present and populated

---

### WP06: Testing & Validation

**Summary**: Implement comprehensive unit tests and E2E smoke tests for Product Committee Orchestrator, including mocks for subprocess calls and validation of all JSON outputs against their schemas.

**Priority**: P1 (Testing - required by constitution)

**Independent Test**: All unit tests pass; E2E smoke tests complete successfully with real LLM on small PRD.

**Subtasks**:
- [ ] T031: Write unit tests for CLI argument parsing (all flags)
- [ ] T032: Write unit tests for subprocess wrapper and retry logic
- [ ] T033: Write unit tests for room execution and status handling
- [ ] T034: Write unit tests for metadata generation
- [ ] T035: Write unit tests for reflection integration
- [ ] T036: Create E2E smoke test for happy path (all rooms succeed)
- [ ] T037: Create E2E smoke test for partial failure scenario

**Implementation Notes**:
- Use pytest; mock subprocess.run() calls with patch decorators
- Unit tests should cover: sequential execution, retries, status handling, metadata generation
- Mock subprocess: Mock return values (exit_code, stdout, stderr)
- E2E tests: Use real small PRD fixture; verify artifacts created and valid
- Timeout should be generous for real LLM calls (300 seconds)

**Parallel Opportunities**: Tests can be written in parallel with implementation WPs (after foundational work complete)

**Dependencies**: WP01, WP02, WP03, WP04, WP05

**Risks**:
- E2E tests with real LLM may be slow/flaky; keep minimal
- Mock strategy must accurately simulate subprocess behavior
- Comprehensive test coverage is critical for quality assurance

**Review Guidance**:
- Unit tests cover all orchestrator logic paths (sequential execution, retries, status handling)
- E2E tests verify end-to-end workflow with real debate system
- All JSON schemas must be validated in unit tests
- Mock subprocess allows deterministic, fast unit tests without LLM dependency

---

## Acceptance Criteria

Feature is complete when:
- [ ] All 35 subtasks across 6 work packages completed
- [ ] All unit tests pass (pytest)
- [ ] Both E2E smoke tests pass
- [ ] All 4 debate rooms can execute sequentially with tracked statuses
- [ ] Metadata.json generated correctly with all required fields
- [ ] Final report markdown generated with all required sections
- [ ] Graceful degradation verified (failed rooms don't crash orchestrator)

**Key Checkpoints**:
- [ ] CLI scaffolding: Argument parser works, help displays
- [ ] Subprocess wrapper: Can invoke mock commands, handle timeouts, retry correctly
- [ ] Room orchestration: Executes sequentially, statuses tracked
- [ ] Metadata generation: Includes all required fields and room statuses
- [ ] Reflection integration: Consumes successful rooms, produces valid JSON
- [ ] Report generation: Creates human-readable markdown with all sections
- [ ] Testing: Unit tests provide good coverage, E2E tests validate integration

**Context for Reviewers**:
- This is the final WP that ties together all foundational work
- Unit tests ensure orchestrator logic correctness
- E2E tests verify integration with real debate system
- Report is primary user-facing deliverable
- Consider all previous WPs when reviewing this WP

---

## Next Steps

**WP01**: CLI scaffolding and argument parsing ✓

**WP02**: Subprocess wrapper and retry logic ✓

**WP03**: Room orchestration and metadata tracking ✓

**WP04**: Self-reflection integration ✓

**WP05**: Report generation and formatting ✓

**WP06**: Testing and validation ✓

**Next**: Ready for `/spec-kitty.accept` - User can accept feature once implementation is complete.

