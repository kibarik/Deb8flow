# Work Packages: Comprehensive Automated Test Suite

**Feature**: 001-Comprehensive Automated Test Suite
**Date**: 2025-02-13
**Status**: Draft

---

## Overview

This document organizes implementation work for the comprehensive automated test suite into focused work packages. Each work package is independently implementable and can be executed in parallel where noted.

## Work Package Summary

| WP | Title | Subtasks | Priority | Dependencies |
|----|--------|-----------|----------------|
| WP01 | Test Foundation Setup | 4 | High | None |
| WP02 | Node Unit Tests - Part 1 | 4 | High | WP01 |
| WP03 | Node Unit Tests - Part 2 | 3 | High | WP01 |
| WP04 | Integration Tests | 3 | Medium | WP02, WP03 |
| WP05 | Validation & Polish | 3 | Medium | WP04 |

**Total**: 5 work packages, 18 subtasks

---

## WP01: Test Foundation Setup

**Priority**: High
**Dependencies**: None
**Estimated Prompt Size**: ~320 lines

### Objective

Create the foundational test infrastructure including directory structure, shared fixtures, mock response data, and dependency configuration.

### Included Subtasks

- [ ] **T001**: Create test directory structure
- [ ] **T002**: Create conftest.py with shared fixtures
- [ ] **T003**: Create mock_responses.py with centralized mock LLM responses
- [ ] **T004**: Update requirements.txt with test dependencies

### Implementation Sketch

1. Create `tests/fixtures/`, `tests/unit/`, `tests/integration/` directories
2. Add `__init__.py` files to make them Python packages
3. Create `conftest.py` with shared fixtures (initial_state, mock_config)
4. Create `mock_responses.py` with realistic LLM response mocks for each node type
5. Update `requirements.txt` to add `pytest-asyncio` and `pytest-cov`

### Parallel Opportunities

All subtasks in this WP can be done in parallel.

### Dependencies

None - this is the foundation WP.

### Risks

- Mock responses may not reflect real LLM outputs → Use examples from actual runs

### Definition of Done

- [ ] Test directory structure exists with all required subdirectories
- [ ] `conftest.py` provides reusable fixtures
- [ ] `mock_responses.py` contains mocks for all 7 node types
- [ ] `requirements.txt` includes pytest-asyncio and pytest-cov

---

## WP02: Node Unit Tests - Part 1

**Priority**: High
**Dependencies**: WP01
**Estimated Prompt Size**: ~400 lines

### Objective

Create unit tests for the first batch of workflow nodes: topic generator, pro debater, con debater, and fact checker.

### Included Subtasks

- [ ] **T005**: Unit tests for topic_generator_node.py
- [ ] **T006**: Unit tests for pro_debater_node.py
- [ ] **T007**: Unit tests for con_debater_node.py
- [ ] **T008**: Unit tests for fact_checker_node.py

### Implementation Sketch

1. Create `tests/unit/test_topic_generator_node.py` with mock-based tests
2. Create `tests/unit/test_pro_debater_node.py` with mock-based tests
3. Create `tests/unit/test_con_debater_node.py` with mock-based tests
4. Enhance existing `tests/test_fact_checker_node.py` with additional test coverage

Each test file should:
- Use `@pytest.mark.asyncio` for async tests
- Mock `BaseComponent.execute_chain()` to control LLM responses
- Test node returns valid state updates
- Test edge cases (empty state, invalid inputs)

### Parallel Opportunities

Each subtask (T005-T008) can be done in parallel - different test files.

### Dependencies

Requires WP01 for test infrastructure (fixtures, mocks).

### Risks

- Existing test files may need to be moved/enhanced rather than replaced
- Async testing patterns may be unfamiliar → Follow research.md patterns

### Definition of Done

- [ ] `test_topic_generator_node.py` tests node with 3+ test cases
- [ ] `test_pro_debater_node.py` tests node with 3+ test cases
- [ ] `test_con_debater_node.py` tests node with 3+ test cases
- [ ] `test_fact_checker_node.py` enhanced with edge case tests
- [ ] All new tests use mocked LLM responses (no API calls)
- [ ] All tests pass when run with `pytest tests/unit/`

---

## WP03: Node Unit Tests - Part 2

**Priority**: High
**Dependencies**: WP01
**Estimated Prompt Size**: ~350 lines

### Objective

Create unit tests for the remaining workflow nodes: fact check router, debate moderator, and judge.

### Included Subtasks

- [ ] **T009**: Unit tests for fact_check_router_node.py
- [ ] **T010**: Unit tests for debate_moderator_node.py
- [ ] **T011**: Unit tests for judge_node.py

### Implementation Sketch

1. Create `tests/unit/test_fact_check_router_node.py` with routing logic tests
2. Create `tests/unit/test_debate_moderator_node.py` with moderation tests
3. Create `tests/unit/test_judge_node.py` with verdict generation tests

Each test file should:
- Test routing decisions (for router node)
- Test state transitions (for moderator node)
- Test verdict format (for judge node)
- Include edge cases (max fact-check counts, empty message history)

### Parallel Opportunities

Each subtask (T009-T011) can be done in parallel - different test files.

### Dependencies

Requires WP01 for test infrastructure (fixtures, mocks).

### Risks

- Router node uses Command objects which may require specific mocking patterns
- Judge verdict format needs to match expected WINNER: PRO/CON pattern

### Definition of Done

- [ ] `test_fact_check_router_node.py` tests routing decisions with 3+ cases
- [ ] `test_debate_moderator_node.py` tests state transitions with 3+ cases
- [ ] `test_judge_node.py` tests verdict generation with 3+ cases
- [ ] All new tests use mocked LLM responses
- [ ] All tests pass when run with `pytest tests/unit/`

---

## WP04: Integration Tests

**Priority**: Medium
**Dependencies**: WP02, WP03
**Estimated Prompt Size**: ~380 lines

### Objective

Create integration tests that verify the workflow executes end-to-end and state transitions occur correctly.

### Included Subtasks

- [ ] **T019**: End-to-end workflow execution test
- [ ] **T020**: State transition validation tests
- [ ] **T021**: Fact-check disqualification test

### Implementation Sketch

1. Create `tests/integration/test_workflow_execution.py`
   - Test full DebateWorkflow.run() completes
   - Verify final state contains verdict
   - Mock all node LLM calls

2. Create `tests/integration/test_state_transitions.py`
   - Test each stage transition (opening → rebuttal → counter → final_argument → verdict)
   - Verify speaker alternation
   - Test stage boundary conditions

3. Create `tests/integration/test_fact_check_disqualification.py`
   - Test that 3 fact-check failures disqualify a speaker
   - Verify workflow continues with remaining speaker
   - Test edge cases (exactly 3 failures, more than 3)

### Parallel Opportunities

T019 and T020 can be done in parallel. T021 should wait for T020.

### Dependencies

Requires WP02 and WP03 to ensure all nodes have tests first (integration tests depend on working node implementations).

### Risks

- End-to-end test may have longer execution time → Set appropriate timeout
- State machine complexity may make transition tests tricky → Reference data-model.md for valid transitions

### Definition of Done

- [ ] `test_workflow_execution.py` verifies full workflow completion
- [ ] `test_state_transitions.py` validates all stage transitions
- [ ] `test_fact_check_disqualification.py` tests 3-strikes rule
- [ ] All integration tests pass
- [ ] Tests complete in under 30 seconds total

---

## WP05: Validation & Polish

**Priority**: Medium
**Dependencies**: WP04
**Estimated Prompt Size**: ~280 lines

### Objective

Validate the complete test suite, set up configuration, and verify coverage targets are met.

### Included Subtasks

- [ ] **T022**: Create pytest configuration (pytest.ini)
- [ ] **T023**: Run full suite and verify coverage targets
- [ ] **T024**: Update documentation with actual test commands

### Implementation Sketch

1. Create `pytest.ini` with:
   - Test discovery patterns
   - Markers for unit/integration/e2e
   - Coverage configuration
   - Asyncio mode settings

2. Run full test suite:
   - `pytest --cov=. --cov-report=term --cov-report=html`
   - Verify 80% coverage target achieved
   - Identify any uncovered critical paths

3. Update documentation:
   - Add actual test execution examples to quickstart.md
   - Verify `pytest` commands work as documented
   - Add troubleshooting for any discovered issues

### Parallel Opportunities

T022 and T023 can be done in parallel. T024 should wait for T023 results.

### Dependencies

Requires WP04 to have all tests implemented before validation.

### Risks

- Coverage may fall short of 80% target → May need additional test cases
- Test execution may exceed 30 seconds → Optimize mock fixtures, reduce redundant tests

### Definition of Done

- [ ] `pytest.ini` configured with appropriate settings
- [ ] Full test suite runs successfully with `pytest`
- [ ] Coverage report shows ≥80% for core modules
- [ ] All tests complete in under 30 seconds
- [ ] Documentation (quickstart.md) verified and accurate

---

## MVP Scope

**Minimum Viable Product**: WP01 + WP02 + WP04

This combination provides:
- Test infrastructure (WP01)
- Core node tests (WP02 - topic, pro, con, fact checker)
- Basic integration validation (WP04)

**Full Feature**: All 5 work packages

---

## Execution Order

```
WP01 (Foundation)
    ├─→ WP02 (Node Tests - Part 1) [P]
    ├─→ WP03 (Node Tests - Part 2) [P]
    └─→ WP04 (Integration Tests)
            └─→ WP05 (Validation & Polish)
```

[P] = Can be parallelized

---

## Next Steps

After reviewing this tasks.md, run `/spec-kitty.implement WP01` to begin implementation.
