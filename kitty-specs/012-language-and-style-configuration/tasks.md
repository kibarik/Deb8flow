# Tasks: Language and Style Configuration

**Feature**: 012-language-and-style-configuration
**Status**: Draft
**Created**: 2025-02-17
**Total Work Packages**: 3
**Total Subtasks**: 17

## Overview

This feature adds a `--language` CLI flag that allows users to specify language and tone settings for all AI agents in debates. The implementation follows a layered approach:

1. **Foundation**: Add language_setting to DebateState and modify BaseComponent for injection
2. **CLI Integration**: Add --language flag to both CLI entry points
3. **Testing**: E2E tests and backward compatibility validation

**Implementation Strategy**: Centralized language injection in `BaseComponent.create_chain()` ensures all agents automatically receive the language setting without modifying individual prompt files.

---

## WP01: State & Base Component Foundation

**Goal**: Add language_setting to the state system and implement centralized language injection in BaseComponent.

**Priority**: Foundation (required for all other work)

**Success Criteria**:
- DebateState includes `language_setting: NotRequired[Optional[str]]`
- BaseComponent captures and injects language setting into system prompts
- Contract test validates state field
- Unit test validates injection logic

**Included Subtasks**:
- [x] T001: Add `language_setting: NotRequired[Optional[str]]` to DebateState
- [x] T002: Add contract test for language_setting field
- [x] T003: Modify `BaseComponent.__call__()` to capture language_setting from state
- [x] T004: Modify `BaseComponent.create_chain()` to accept language_setting parameter
- [x] T005: Implement language injection logic (prepend to system template)
- [x] T006: Add unit test for language injection in BaseComponent

**Implementation Sketch**:
1. Update `debate_state.py` with new field (maintains backward compatibility)
2. Update `BaseComponent.__call__()` to capture `language_setting` when present
3. Modify `create_chain()` signature to accept optional `language_setting`
4. Implement injection: if `language_setting` is truthy, prepend to system_template
5. Add tests to verify behavior with and without language setting

**Parallel Opportunities**: None (sequential - state must exist before BaseComponent can use it)

**Dependencies**: None

**Risks**:
- Risk: Breaking existing agent chains if create_chain() signature change not backward compatible
- Mitigation: Make language_setting parameter optional with default None

**Estimated Prompt Size**: ~350 lines

**Prompt File**: [tasks/WP01-state-and-base-component-foundation.md](tasks/WP01-state-and-base-component-foundation.md)

---

## WP02: CLI Integration

**Goal**: Add `--language` flag to both CLI entry points with validation and state propagation.

**Priority**: High (user-facing feature)

**Success Criteria**:
- Both `main.py` and `document_debate_cli.py` accept `--language` argument
- Length validation (500 chars max) prevents excessive input
- Language setting properly passed to initial state
- Empty strings treated as None (no injection)

**Included Subtasks**:
- [ ] T007: Add `--language` argparse argument to `main.py`
- [ ] T008: Add `--language` argparse argument to `document_debate_cli.py` [P]
- [ ] T009: Implement length validation (500 chars max) in both CLIs [P]
- [ ] T010: Pass `language_setting` to initial state in `main.py`
- [ ] T011: Pass `language_setting` to initial state in `document_debate_cli.py` [P]

**Implementation Sketch**:
1. Add argparse argument to both CLI files (can be done in parallel)
2. Implement validation: if `len(args.language) > 500`, error and exit
3. Handle empty string: use `args.language if args.language else None`
4. Add `language_setting` to base_state dictionary in both files
5. Verify state propagation to workflow initialization

**Parallel Opportunities**: T007/T008 and T010/T011 can be done in parallel (different files)

**Dependencies**: WP01 (DebateState must have language_setting field)

**Risks**:
- Risk: Argument parsing errors if syntax incorrect
- Mitigation: Test both short and long language strings, verify help text

**Estimated Prompt Size**: ~300 lines

**Prompt File**: [tasks/WP02-cli-integration.md](tasks/WP02-cli-integration.md)

---

## WP03: Testing & Validation

**Goal**: Comprehensive E2E tests and backward compatibility verification.

**Priority**: High (ensures feature works and doesn't break existing behavior)

**Success Criteria**:
- E2E test verifies language flag works in standard debate
- E2E test verifies language flag works in document debate
- Backward compatibility test confirms no flag = existing behavior
- All existing E2E tests pass without modification

**Included Subtasks**:
- [ ] T012: Verify debate_workflow.py properly propagates language_setting
- [ ] T013: Verify document_debate_workflow.py properly propagates language_setting
- [ ] T014: Add E2E test for `--language` flag in standard debate
- [ ] T015: Add E2E test for `--language` flag in document debate
- [ ] T016: Add backward compatibility test (no flag)
- [ ] T017: Verify all existing E2E tests pass

**Implementation Sketch**:
1. Review workflow files to understand state propagation
2. Create test helper function for language flag testing
3. Add test case: standard debate with "Russian formal" language setting
4. Add test case: document debate with "concise English" language setting
5. Add test case: no language flag (verify backward compatibility)
6. Run full test suite and verify all existing tests pass

**Parallel Opportunities**: T014/T015 can be written in parallel (different test files)

**Dependencies**: WP01, WP02 (feature must be implemented before testing)

**Risks**:
- Risk: Language instruction not respected by AI models (flaky tests)
- Mitigation: Use simple, explicit language instructions; tests check for presence in prompts, not actual output language

**Estimated Prompt Size**: ~300 lines

**Prompt File**: [tasks/WP03-testing-and-validation.md](tasks/WP03-testing-and-validation.md)

---

## MVP Scope

**Minimum Viable Product**: WP01 + WP02

Completing WP01 and WP02 provides a working feature:
- Users can specify `--language` flag
- Language setting is injected into all agent prompts
- System remains backward compatible

**WP03** adds confidence through comprehensive testing but is not required for basic functionality.

---

## Dependency Graph

```
WP01 (Foundation)
    │
    ├───── WP02 (CLI Integration) ─────┐
    │                                  │
    └──────────────────────────────────┴───── WP03 (Testing)
```

**Implementation Order**:
1. WP01: Foundation (no dependencies)
2. WP02: CLI Integration (depends on WP01)
3. WP03: Testing (depends on WP01 + WP02)

---

## Size Distribution

| Work Package | Subtasks | Estimated Lines |
|--------------|----------|-----------------|
| WP01: State & Base Component | 6 | ~350 |
| WP02: CLI Integration | 5 | ~300 |
| WP03: Testing & Validation | 5 | ~300 |

**Total**: 17 subtasks across 3 work packages

**Validation**: ✅ All WPs within ideal range (3-7 subtasks, 200-500 lines)

---

## Next Steps

1. Run `spec-kitty implement WP01` to start implementation
2. After WP01 completes, run `spec-kitty implement WP02 --base WP01`
3. After WP02 completes, run `spec-kitty implement WP03 --base WP02`
4. Run `/spec-kitty.analyze` for cross-artifact validation
5. Run `/spec-kitty.accept` for final acceptance

---

**Generated**: 2025-02-17
**Template Version**: 0.11.0+
