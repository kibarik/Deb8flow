# Work Packages: Product Committee Orchestrator

**Feature**: 007-product-committee-orchestrator
**Date**: 2026-02-14
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Overview

This document outlines all work packages for implementing the Product Committee Orchestrator feature. Work packages are organized by phase and priority, with each package being independently implementable and testable.

**Total Work Packages**: 6
**Total Subtasks**: 35
**Estimated Prompt Size**: 6 WPs × ~5-6 subtasks × ~50 lines/subtask = ~1,500-1,800 total lines

## Package Summary

| WP | Title | Phase | Priority | Subtasks | Est. Lines | Dependencies |
|----|--------|--------|----------|-------------|--------------|
| WP01 | Foundation | P1 | 6 | ~300 | - |
| WP02 | Core Logic | P1 | 7 | ~350 | WP01 |
| WP03 | Orchestration | P1 | 6 | ~300 | WP01, WP02 |
| WP04 | Reflection | P1 | 4 | ~200 | WP01, WP02, WP03 |
| WP05 | Reporting | P1 | 6 | ~300 | WP01, WP02, WP03, WP04 |
| WP06 | Testing | P1 | 6 | ~350 | WP01-WP05 |

## Work Packages

### WP01: Foundation & CLI Scaffolding

**Summary**: Set up the foundational CLI structure for `product_committee.py` with all argument parsing, basic orchestration skeleton, and logging infrastructure.

**Priority**: P1 (Foundation - must complete first)
**Phase**: Foundation

**Independent Test**: Can run `product_committee.py --help` and see all CLI arguments with proper descriptions. Basic skeleton runs without errors.

**Subtasks**:
- [ ] T001: Create `product_committee.py` with basic structure and main entry point
- [ ] T002: Implement argparse/click for all required and optional CLI arguments
- [ ] T003: Add `--prd`/`--docx` required argument with validation
- [ ] T004: Add `--question` required argument with validation
- [ ] T005: Add optional arguments: `--model`, `--max-retries`, `--output-dir`, `--roles-dir`, `--run-id`
- [ ] T006: Add `--allow-short-prd`, `--verbose`, `--quiet` flag arguments
- [ ] T007: Implement Python logging infrastructure with configurable levels

**Implementation Notes**:
- Use argparse or click (match existing `document_debate_cli.py` pattern)
- Define argument defaults per spec (max-retries=2, output-dir=./committee_output, roles-dir=prompts/roles/)
- Set up logging with three levels: default (normal), verbose, quiet
- Create basic main() function that orchestrates the full flow

**Parallel Opportunities**: None (foundational work)

**Dependencies**: None

**Risks**:
- Argument parsing complexity may grow; keep CLI focused on MVP scope
- Logging configuration must not interfere with subprocess output

---

### WP02: Subprocess Wrapper & Retry Logic

**Summary**: Implement the subprocess wrapper that invokes `document_debate_cli.py`, parses its output, and handles retries with exponential backoff.

**Priority**: P1 (Core Logic - required before orchestration)
**Phase**: Foundation

**Independent Test**: Subprocess wrapper can invoke a mock command, handle timeouts, parse JSON output, and retry on failure.

**Subtasks**:
- [ ] T008: Create subprocess wrapper function for `document_debate_cli.py` invocation
- [ ] T009: Implement stdout/stderr parsing and room JSON extraction
- [ ] T010: Implement exponential backoff retry logic (1s, 2s, 4s, ...)
- [ ] T011: Add retry attempt logging with failure reasons
- [ ] T012: Handle subprocess exit codes and exceptions
- [ ] T013: Create DebateRoom data structure for parsed results
- [ ] T014: Implement room status determination (success/failed)

**Implementation Notes**:
- Subprocess wrapper should accept: prd_path, question, pro_prompt, con_prompt, model
- Use subprocess.run() with timeout and capture=True
- Parse output from stdout/stderr into DebateRoom structure
- Exponential backoff: wait 2^n seconds (1s, 2s, 4s, 8s, ...)
- Log each retry attempt in verbose mode only

**Parallel Opportunities**: None (sequential subprocess calls by design)

**Dependencies**: WP01

**Risks**:
- Subprocess output parsing may be fragile; rely on structured JSON from debate CLI
- Timeout handling must balance between allowing long LLM calls and detecting hangs

---

### WP03: Room Orchestration & Metadata Tracking

**Summary**: Implement the sequential room execution logic, role prompt validation, status tracking, and metadata generation.

**Priority**: P1 (Orchestration - core feature)
**Phase**: Foundation

**Independent Test**: Orchestrator can run all 4 rooms sequentially, track statuses, and generate metadata.json.

**Subtasks**:
- [ ] T015: Validate role prompt files exist (tpm.txt required, others optional)
- [ ] T016: Implement sequential room execution (TPM vs CPO/CFO/CTO/BDM)
- [ ] T017: Collect successful room results for reflection input
- [ ] T018: Generate metadata.json with run info and room statuses
- [ ] T019: Handle missing role prompts (skip room, log warning)
- [ ] T020: Implement status tracking per room (success/failed/skipped)

**Implementation Notes**:
- Room execution order: CPO → CFO → CTO → BDM (fixed for MVP)
- Track room statuses in dict for metadata.json
- For missing non-TPM prompts: mark as skipped_missing_prompt
- Collect successful room JSONs for reflection step

**Parallel Opportunities**: None (sequential by spec requirement)

**Dependencies**: WP01, WP02

**Risks**:
- Sequential execution means total runtime = sum of all rooms; ensure logging shows progress
- Missing TPM prompt must be fatal; missing others are warnings

---

### WP04: Self-Reflection Integration

**Summary**: Implement the TPM self-reflection step that consumes PRD, question, and room results, then generates reflection JSON.

**Priority**: P1 (Reflection - required for report generation)
**Phase**: Foundation

**Independent Test**: Self-reflection can process successful room results and generate reflection.json with learned insights.

**Subtasks**:
- [ ] T021: Create `prompts/tpm_reflection.txt` with structured output instructions
- [ ] T022: Implement self-reflection subprocess invocation
- [ ] T023: Parse reflection JSON output per schema
- [ ] T024: Handle case with zero successful rooms (adapt prompt)

**Implementation Notes**:
- Reflection prompt should request JSON output matching reflection_schema.json
- Prompt receives: PRD text, question, successful room results
- If all rooms failed: prompt explicitly notes lack of perspectives
- Subprocess invocation similar to rooms but with reflection-specific prompt

**Parallel Opportunities**: None (runs after all rooms)

**Dependencies**: WP01, WP02, WP03

**Risks**:
- Reflection prompt quality directly impacts report quality
- Must handle edge case of 0 successful rooms gracefully

---

### WP05: Report Generation & Formatting

**Summary**: Implement the final markdown report generation that synthesizes all room results, reflection, and metadata into human-readable format.

**Priority**: P1 (Reporting - primary user output)
**Phase**: Foundation

**Independent Test**: Report generator can create final_report.md with all sections populated from room JSONs, reflection, and metadata.

**Subtasks**:
- [ ] T025: Implement markdown report structure with all required sections
- [ ] T026: Format room summaries (positions, verdict, takeaways) per room
- [ ] T027: Format reflection content (learned insights, recommendations)
- [ ] T028: Explicitly note missing/failed rooms in report
- [ ] T029: Implement slug generation from question (3-5 words, hyphenated)
- [ ] T030: Create timestamped run directory per spec (RUN_YYYY-MM-DD_HHMMSS_slug)

**Implementation Notes**:
- Report sections: Executive Summary, Room-by-Room Analysis, TPM Reflection, Recommendations, Missing Perspectives
- Slug generation: lowercase, hyphenate first 3-5 words from question
- Directory creation: fail if output directory not writable (fatal error per spec)
- Write all JSON files before report for validation

**Parallel Opportunities**: None (depends on all previous WPs)

**Dependencies**: WP01, WP02, WP03, WP04

**Risks**:
- Report formatting must handle partial failures gracefully
- Large PRDs may create long reports; ensure readability

---

### WP06: Testing & Validation

**Summary**: Implement comprehensive unit tests and E2E smoke tests for the orchestrator, including mocks for subprocess calls.

**Priority**: P1 (Testing - required by constitution)
**Phase**: Polish

**Independent Test**: All unit tests pass; E2E smoke tests complete successfully with real LLM on small PRD.

**Subtasks**:
- [ ] T031: Write unit tests for argument parsing (all flags)
- [ ] T032: Write unit tests for subprocess wrapper and retry logic
- [ ] T033: Write unit tests for room execution and status handling
- [ ] T034: Write unit tests for metadata generation
- [ ] T035: Write unit tests for reflection integration
- [ ] T036: Write unit tests for report generation
- [ ] T037: Create E2E smoke test for happy path (all rooms succeed)
- [ ] T038: Create E2E smoke test for partial failure scenario

**Implementation Notes**:
- Use pytest; mock subprocess.run() calls with patch decorators
- Unit tests should cover: sequential execution, retries, status handling, edge cases
- Mock LLM responses for deterministic testing
- E2E tests: use real small PRD, verify artifacts created and valid
- Happy path E2E: verify all 4 rooms, reflection, report, metadata
- Failure E2E: simulate one room failure, verify graceful degradation

**Parallel Opportunities**: Tests can be written in parallel with implementation (TDD approach)

**Dependencies**: WP01, WP02, WP03, WP04, WP05

**Risks**:
- E2E tests with real LLM may be slow/flaky; keep minimal (2 tests max)
- Mock design must accurately simulate subprocess behavior

---

## Acceptance Criteria

Feature is complete when:
- [ ] All 35 subtasks across 6 work packages are marked as done
- [ ] All unit tests pass (pytest)
- [ ] Both E2E smoke tests pass
- [ ] final_report.md generates correctly with all required sections
- [ ] Graceful degradation verified (failed rooms don't crash orchestrator)
- [ ] Metadata.json contains accurate room statuses and timestamps
- [ ] CLI accepts all specified arguments with correct defaults
- [ ] Logging works correctly at all three levels (default, verbose, quiet)
