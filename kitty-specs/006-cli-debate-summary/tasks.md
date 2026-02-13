# Tasks: CLI Debate Summary Output

**Feature**: 006-cli-debate-summary
**Status**: Planned
**Last Updated**: 2026-02-14

## Overview

This document outlines the work packages for implementing a console-based summary output feature for the document debate CLI tool. The summary displays each original question paired with its final decided answer after the AI debate winner is selected.

## Work Package Summary

| WP | Title | Priority | Subtasks | Est. Size |
|----|-------|----------|----------|-----------|
| WP01 | Summary Data Model & State Enhancement | P0 | 5 | ~300 lines |
| WP02 | CLI Summary Display Integration | P0 | 5 | ~350 lines |
| WP03 | Edge Case Handling & Validation | P1 | 4 | ~250 lines |

**Total Work Packages**: 3
**Total Subtasks**: 14
**Average Prompt Size**: ~300 lines per WP

---

## WP01: Summary Data Model & State Enhancement

**Goal**: Enhance the debate state and data model to capture the information needed for summary output.

**Priority**: P0 (Foundational - required by WP02)

**Included Subtasks**:
- [ ] **T001**: Add `original_question` field to DebateState TypedDict
- [ ] **T002**: Add `final_answer` field to DebateState to store judge's conclusion
- [ ] **T003**: Update DocumentTopicNode to preserve original question in state
- [ ] **T004**: Update JudgeNode to extract and store final answer in state
- [ ] **T005**: Add state validation to ensure summary fields are populated

**Implementation Sketch**:
1. Modify `debate_state.py` to add new TypedDict fields
2. Update `document_topic_node.py` to capture and store `original_question`
3. Modify `judge_node.py` to parse and store `final_answer` from verdict
4. Add validation logic in workflow to verify summary data availability

**Parallel Opportunities**: None - state changes must be sequential

**Dependencies**: None (foundational work)

**Risks**:
- TypedDict changes may break existing type checks
- JudgeNode JSON parsing may need enhancement to extract final answer

**Independent Testing**:
- Run existing workflow with sample debate
- Verify state contains `original_question` and `final_answer`
- Check type validation passes

---

## WP02: CLI Summary Display Integration

**Goal**: Implement the console summary output in the CLI tool after winner selection.

**Priority**: P0 (Core feature)

**Included Subtasks**:
- [ ] **T006**: Create `DebateSummaryFormatter` class for output formatting
- [ ] **T007**: Implement `format_summary()` method with question/answer display
- [ ] **T008**: Add summary display to `document_debate_cli.py` main function
- [ ] **T009**: Style summary output with Rich console formatting
- [ ] **T010**: Ensure summary appears after verdict display

**Implementation Sketch**:
1. Create new module `cli/debate_summary_formatter.py`
2. Implement formatter with template:
   ```
   === DEBATE SUMMARY ===

   Q: {original_question}
   A: {final_answer}

   =======================
   ```
3. Integrate formatter call in CLI after verdict display
4. Use Rich formatting for headers and separators

**Parallel Opportunities**: T006-T007 can be done in parallel with T008-T010

**Dependencies**: WP01 (requires state fields from T001-T005)

**Risks**:
- Summary placement in CLI flow may feel awkward
- Formatting may not align with existing Rich styling

**Independent Testing**:
- Run CLI with single question debate
- Verify summary appears after verdict
- Check formatting is readable and consistent

---

## WP03: Edge Case Handling & Validation

**Goal**: Handle edge cases gracefully and validate summary output under various conditions.

**Priority**: P1 (Quality assurance)

**Included Subtasks**:
- [ ] **T011**: Handle missing `original_question` (display placeholder or skip)
- [ ] **T012**: Handle missing `final_answer` (display verdict instead)
- [ ] **T013**: Handle empty/null state (display appropriate message)
- [ ] **T014**: Add manual test scenarios for all edge cases

**Implementation Sketch**:
1. Add defensive checks in `DebateSummaryFormatter`
2. Implement fallback display logic for missing data
3. Add error handling to prevent summary from breaking workflow
4. Document test scenarios and expected behaviors

**Parallel Opportunities**: T011-T013 can be done in parallel with T014

**Dependencies**: WP02 (requires formatter from WP02)

**Risks**:
- Edge cases may be more numerous than anticipated
- Error handling may mask real bugs

**Independent Testing**:
- Test with debates that have no clear winner
- Test with malformed state data
- Verify workflow completes even when summary fails

---

## MVP Scope Recommendation

**Minimum Viable Product**: WP01 + WP02

These two work packages deliver the core functionality:
- State captures question and answer (WP01)
- CLI displays summary (WP02)

WP03 (edge cases) is quality assurance that can be added post-MVP if needed.

---

## Parallelization Strategy

**Phase 1** (Sequential): WP01 must complete first (state changes)
**Phase 2** (Parallel-ready): WP02 can begin once WP01-T001 is complete
**Phase 3** (Sequential): WP03 depends on WP02 completion

---

## Definition of Done

A work package is complete when:
- [ ] All subtasks are implemented
- [ ] Code follows project patterns (similar to existing nodes/CLI)
- [ ] Type hints are included where applicable
- [ ] Manual testing confirms expected behavior
- [ ] No regressions in existing functionality

---

## Notes

- Feature is intentionally simple: console output only, no file persistence
- Summary format is fixed: "Q: {question}" followed by "A: {answer}"
- Backward compatibility is maintained via Optional state fields
- No automated tests are included unless explicitly requested
