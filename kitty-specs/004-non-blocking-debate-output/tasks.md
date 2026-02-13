# Tasks: Non-Blocking Debate Output Recording

**Feature**: 004-non-blocking-debate-output
**Date**: 2025-02-14
**Total Subtasks**: 24
**Total Work Packages**: 4

## Overview

This feature adds async file output recording to the document debate CLI. Work is organized into 4 work packages:

1. **WP01**: Output Module Foundation (8 subtasks) - Create the src/output module
2. **WP02**: CLI Integration (5 subtasks) - Add --output argument and writer creation
3. **WP03**: Workflow Node Integration (6 subtasks) - Wire writer into all debate nodes
4. **WP04**: Testing (5 subtasks) - Unit and integration tests

**Dependency Chain**: WP01 → WP02 → WP03 (WP04 can run in parallel with WP02-WP03)

---

## WP01: Output Module Foundation

**Prompt File**: [WP01-output-module-foundation.md](./tasks/WP01-output-module-foundation.md)

**Goal**: Create the src/output module with AsyncFileWriter and TranscriptFormatter classes.

**Priority**: P1 (Foundation - required for all other work)

**Subtasks** (8 subtasks, ~450 lines):
- [ ] **T001**: Create `src/output/__init__.py` with module exports
- [ ] **T002**: Implement `TranscriptFormatter` class with `format_message()` method
- [ ] **T003**: Implement `TranscriptFormatter.validate_path()` method
- [ ] **T004**: Implement `DebateMessage` dataclass/entity
- [ ] **T005**: Implement `AsyncFileWriter.__init__()` with queue and task setup
- [ ] **T006**: Implement `AsyncFileWriter._writer_task()` background task with aiofiles
- [ ] **T007**: Implement `AsyncFileWriter.write_message()` method
- [ ] **T008**: Implement `AsyncFileWriter.close()` method with queue drain

**Implementation Sketch**:
1. Create directory structure: `src/output/`
2. Implement DebateMessage dataclass first (simplest, used by others)
3. Implement TranscriptFormatter with format_message() and validate_path()
4. Implement AsyncFileWriter with full async queue processing
5. Export public classes from __init__.py
6. Verify module imports without errors

**Parallel Opportunities**: None (module must be built sequentially)

**Dependencies**: None (first WP)

**Risks**:
- asyncio.Queue usage must be correct (maxsize=1000, proper task_done())
- aiofiles API differences from built-in open()
- Background task lifecycle management (start, stop, cleanup)

**Estimated Prompt Size**: ~450 lines

---

## WP02: CLI Integration

**Prompt File**: [WP02-cli-integration.md](./tasks/WP02-cli-integration.md)

**Goal**: Add --output argument to CLI and integrate AsyncFileWriter creation/cleanup.

**Priority**: P1 (User-facing functionality)

**Subtasks** (5 subtasks, ~280 lines):
- [ ] **T009**: Add `--output` argument to argparse in `document_debate_cli.py`
- [ ] **T010**: Add `aiofiles>=24.1.0` dependency to `requirements.txt`
- [ ] **T011**: Create `AsyncFileWriter` instance in CLI main() with error handling
- [ ] **T012**: Pass `output_writer` parameter to `workflow.run()`
- [ ] **T013**: Add writer cleanup in finally block (await writer.close())

**Implementation Sketch**:
1. Add argparse argument for --output
2. Update requirements.txt with aiofiles dependency
3. In main(): create writer if args.output provided, handle init failures gracefully
4. Pass writer to workflow.run()
5. Wrap workflow execution in try/finally for cleanup
6. Test CLI with --output flag manually

**Parallel Opportunities**: None (sequential CLI modifications)

**Dependencies**: WP01 (requires AsyncFileWriter to be implemented)

**Risks**:
- Writer creation might fail (path unwritable) - must not crash CLI
- Forgetting to call close() could leave writes incomplete
- Writer might be None - all code must handle this case

**Estimated Prompt Size**: ~280 lines

---

## WP03: Workflow Node Integration

**Prompt File**: [WP03-workflow-node-integration.md](./tasks/WP03-workflow-node-integration.md)

**Goal**: Wire output_writer into DocumentDebateWorkflow and all debate nodes.

**Priority**: P1 (Core functionality)

**Subtasks** (6 subtasks, ~380 lines):
- [ ] **T014**: Modify `DocumentDebateWorkflow.run()` to accept optional `output_writer` parameter
- [ ] **T015**: Update `document_topic_node.py` to write messages to output_writer
- [ ] **T016**: Update `pro_debater_node.py` to write messages to output_writer
- [ ] **T017**: Update `con_debater_node.py` to write messages to output_writer
- [ ] **T018**: Update `judge_node.py` to write messages to output_writer
- [ ] **T019**: Update `debate_moderator_node.py` to write messages (if applicable)

**Implementation Sketch**:
1. Modify workflow.run() signature to accept output_writer=None
2. For each node function: add output_writer=None parameter
3. In each node: if output_writer and output_writer.enabled: create DebateMessage and write
4. Extract speaker label from node context (PRO/CON/JUDGE/MODERATOR)
5. Use datetime.now(timezone.utc).isoformat() for timestamps
6. Pass output_writer through workflow state or function parameters (decide approach)

**Parallel Opportunities**: **[P]** All node updates can be done in parallel by different agents (different files)

**Dependencies**: WP01 (requires AsyncFileWriter, DebateMessage), WP02 (for workflow.run signature)

**Risks**:
- Nodes might not have direct access to output_writer if not passed through state
- Different nodes have different message structures - need consistent DebateMessage creation
- Race conditions if multiple nodes write simultaneously (queue handles this, but verify)

**Estimated Prompt Size**: ~380 lines

---

## WP04: Testing

**Prompt File**: [WP04-testing.md](./tasks/WP04-testing.md)

**Goal**: Write unit tests for output module and integration tests for full workflow.

**Priority**: P2 (Important but can run in parallel with implementation)

**Subtasks** (5 subtasks, ~320 lines):
- [ ] **T020**: Create `tests/unit/output/__init__.py` test directory
- [ ] **T021**: Write unit tests for `TranscriptFormatter` (format_message, validate_path)
- [ ] **T022**: Write unit tests for `AsyncFileWriter` (mock aiofiles, test queue behavior)
- [ ] **T023**: Write integration test for full workflow with output file
- [ ] **T024**: Write error scenario tests (read-only path, disk full simulation)

**Implementation Sketch**:
1. Create tests/unit/output/ directory
2. Test TranscriptFormatter with various DebateMessage inputs
3. Test AsyncFileWriter with mocked aiofiles to verify queue operations
4. Write end-to-end test: run workflow with --output, verify file content
5. Test error scenarios: unwritable path, concurrent writes, special characters

**Parallel Opportunities**: **[P]** Can run in parallel with WP02 and WP03

**Dependencies**: WP01 (requires module to test), WP02-WP03 (for integration tests)

**Risks**:
- Mocking aiofiles correctly requires understanding async mocking patterns
- Integration test timing: must wait for async writes to complete before checking file
- Error scenarios may be hard to simulate (disk full, permission denied)

**Estimated Prompt Size**: ~320 lines

---

## Summary

| WP | Subtasks | Est. Lines | Priority | Can Parallelize |
|-----|-----------|-------------|----------|------------------|
| WP01 | 8 | ~450 | P1 | No |
| WP02 | 5 | ~280 | P1 | No |
| WP03 | 6 | ~380 | P1 | Yes (files) |
| WP04 | 5 | ~320 | P2 | Yes (with WP02+) |

**Total Estimated Lines**: ~1430

**Size Validation**:
- ✅ All WPs within acceptable range (280-450 lines)
- ✅ All WPs under 700-line maximum
- ✅ Average ~360 lines per WP - well-sized for focused implementation

**MVP Scope**: WP01 + WP02 enables CLI with --output flag and async writes (minimum viable)

**Next Command**: `/spec-kitty.implement WP01` (after running `spec-kitty.agent feature finalize-tasks --json`)
