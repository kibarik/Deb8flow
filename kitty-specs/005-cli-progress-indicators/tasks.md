# Work Packages: CLI Progress Indicators for Document Debate

**Feature**: 005-cli-progress-indicators
**Date**: 2025-02-14
**Status**: Planned

---

## Overview

Add real-time progress tracking to the document debate CLI workflow using tqdm. This feature eliminates user uncertainty during long-running LLM operations by displaying step-by-step progress with configurable verbosity levels.

**Total Work Packages**: 6
**Total Subtasks**: 26
**Average WP Size**: ~4 subtasks, ~350 lines per prompt

---

## WP01: Foundation - Progress Module

**Goal**: Create the foundational `src/progress/` module with core progress tracking classes.

**Priority**: 1 (must exist before any other work)
**Independent Test**: Yes - can be unit tested in isolation

**Subtasks**:
- [ ] T001: Create ProgressLevel enum (QUIET, DEFAULT, VERBOSE)
- [ ] T002: Create ProgressManager class with tqdm integration
- [ ] T003: Create CLIOutput class for verbosity filtering
- [ ] T004: Write __init__.py for progress module
- [ ] T005: Add unit tests for ProgressManager

**Implementation Sketch**:
1. Create `src/progress/` directory structure
2. Implement ProgressLevel enum with three values
3. Implement ProgressManager with tqdm.rich, handle verbosity
4. Implement CLIOutput with info/verbose/error/success methods
5. Create __init__.py exposing both classes
6. Write unit tests for each class

**Parallel Opportunities**: None - foundational work

**Dependencies**: None

**Estimated Prompt Size**: ~350 lines

---

## WP02: CLI Integration

**Goal**: Integrate progress tracking into the main CLI entry point.

**Priority**: 2 (depends on WP01)

**Subtasks**:
- [ ] T006: Add --verbose and --quiet argument flags to argparse
- [ ] T007: Instantiate ProgressManager and CLIOutput based on flags
- [ ] T008: Pass progress_manager to workflow.run()
- [ ] T009: Update requirements.txt with tqdm>=4.66.0
- [ ] T010: Test CLI with different verbosity levels

**Implementation Sketch**:
1. Extend argparse in document_debate_cli.py with new flags
2. Parse flags and determine ProgressLevel (quiet > verbose > default)
3. Create ProgressManager and CLIOutput instances
4. Pass progress_manager to DocumentDebateWorkflow.run()
5. Update requirements.txt
6. Test all three verbosity modes

**Parallel Opportunities**: T006-T008 can be done in parallel with WP01

**Dependencies**: WP01 (progress module must exist)

**Estimated Prompt Size**: ~380 lines

---

## WP03: Workflow Integration

**Goal**: Modify DocumentDebateWorkflow to accept and propagate progress manager.

**Priority**: 3 (depends on WP01, WP02)

**Subtasks**:
- [ ] T011: Modify workflow.run() to accept optional progress_manager parameter
- [ ] T012: Inject progress_manager into state as _progress_manager
- [ ] T013: Update docstring for run() method
- [ ] T014: Add integration test for workflow + progress

**Implementation Sketch**:
1. Update run() signature: `async def run(self, initial_state=None, progress_manager=None)`
2. If progress_manager provided, add to initial_state["_progress_manager"]
3. Update docstring to document new parameter
4. Write integration test verifying progress is accessible in state

**Parallel Opportunities**: None (workflow is single file)

**Dependencies**: WP01, WP02

**Estimated Prompt Size**: ~320 lines

---

## WP04: Node Instrumentation - Part 1

**Goal**: Add progress hooks to document, pro, and con debater nodes.

**Priority**: 4 (depends on WP03)

**Subtasks**:
- [ ] T015: Instrument document_topic_node.py with progress hooks
- [ ] T016: Instrument pro_debater_node.py with progress hooks
- [ ] T017: Instrument con_debater_node.py with progress hooks
- [ ] T018: Add verbose output for LLM API calls

**Implementation Sketch**:
1. In each node's __call__ method, extract progress from state["_progress_manager"]
2. Call progress.start_step() before LLM invocation
3. Call progress.complete_step() after LLM invocation
4. Add verbose logging for LLM API calls (when in VERBOSE mode)

**Parallel Opportunities**: T015, T016, T017 can be done in parallel (different files)

**Dependencies**: WP03 (workflow must inject progress into state)

**Estimated Prompt Size**: ~420 lines

---

## WP05: Node Instrumentation - Part 2

**Goal**: Add progress hooks to remaining nodes (moderator, fact checker, judge).

**Priority**: 5 (depends on WP03)

**Subtasks**:
- [ ] T019: Instrument debate_moderator_node.py with progress hooks
- [ ] T020: Instrument fact_check_node.py with progress hooks
- [ ] T021: Instrument judge_node.py with progress hooks
- [ ] T022: Add unit tests for instrumented nodes

**Implementation Sketch**:
1. Apply same pattern as WP04 to remaining nodes
2. Each node extracts progress from state and uses it
3. Write unit tests verifying progress integration
4. Ensure step names match workflow sequence

**Parallel Opportunities**: T019, T020, T021 can be done in parallel

**Dependencies**: WP03 (workflow must inject progress into state)

**Estimated Prompt Size**: ~400 lines

---

## WP06: Documentation & Polish

**Goal**: Finalize documentation and add end-to-end testing.

**Priority**: 6 (depends on all other WPs)

**Subtasks**:
- [ ] T023: Verify quickstart.md is complete (already exists)
- [ ] T024: Verify agent context update is complete (already done)
- [ ] T025: Add end-to-end test for full workflow with progress
- [ ] T026: Verify progress display across all verbosity levels

**Implementation Sketch**:
1. Review existing quickstart.md for completeness
2. Verify agent context includes tqdm and progress module
3. Write e2e test running full workflow with each verbosity level
4. Manually verify progress bars render correctly

**Parallel Opportunities**: None (final validation work)

**Dependencies**: WP01, WP02, WP03, WP04, WP05

**Estimated Prompt Size**: ~280 lines

---

## Summary

| Work Package | Subtasks | Est. Lines | Dependencies |
|-------------|-----------|-------------|--------------|
| WP01: Foundation | 5 | ~350 | None |
| WP02: CLI Integration | 5 | ~380 | WP01 |
| WP03: Workflow Integration | 4 | ~320 | WP01, WP02 |
| WP04: Node Instrumentation - Part 1 | 4 | ~420 | WP03 |
| WP05: Node Instrumentation - Part 2 | 4 | ~400 | WP03 |
| WP06: Documentation & Polish | 4 | ~280 | All |
| **Total** | **26** | **~2,150** | |

**MVP Scope**: WP01 + WP02 + WP03 (enables basic progress functionality)
**Full Feature**: All 6 WPs (complete progress tracking across all nodes)

---

## Size Validation

✓ All work packages within ideal range (3-7 subtasks each)
✓ All estimated prompts under 500 lines
✓ No work package exceeds 10 subtasks
✓ Work packages are focused and independently implementable
✓ Clear dependency chain: WP01 → WP02 → WP03 → WP04/WP05 → WP06
