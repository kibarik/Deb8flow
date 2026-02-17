---
work_package_id: WP09
title: Testing & Validation
lane: planned
dependencies: []
subtasks:
- T044
- T045
- T046
- T047
- T048
phase: Phase 4 - Validation
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-17T21:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP09 – Testing & Validation

## Objectives & Success Criteria

- **Goal**: Complete test coverage for all components, validate quickstart scenarios, ensure no regressions.
- **Success Criteria**:
  - Contract tests validate all JSON schemas
  - E2E tests for .docx and .md documents work
  - Quickstart scenarios validated
  - Full test suite passes with no regressions
  - All acceptance criteria from spec met

## Context & Constraints

- **Prerequisites**: All previous WPs (needs full implementation to test)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/spec.md` - Success criteria and acceptance scenarios
  - `kitty-specs/015-document-rewrite-agent/contracts/` - JSON schemas to validate
  - `kitty-specs/015-document-rewrite-agent/quickstart.md` - User scenarios to validate
- **Constraints**:
  - Tests must not break existing functionality
  - Use existing test patterns from codebase
  - Mock external dependencies (LLM, file system)

## Subtasks & Detailed Guidance

### Subtask T044 – Contract tests

**Purpose**: Validate that all data structures match their JSON schema contracts.

**Steps**:
1. Create `tests/contract/test_rewriter_contract.py`
2. Test `RewriteRequest` contract:
   - Create sample RewriteRequest
   - Validate against `rewriter_agent_contract.json` schema
   - Test required fields, data types, formats
3. Test `RewriteResult` contract:
   - Create sample RewriteResult
   - Validate against schema
   - Test all fields present
4. Test `ConversionResult` contract:
   - Create sample ConversionResult
   - Validate against `converter_interface.json`
5. Test file operation contracts:
   - Validate metadata JSON structure
   - Test filename generation pattern

**Files**:
- `tests/contract/test_rewriter_contract.py` (new, ~150 lines)

**Commands**:
```bash
pytest tests/contract/test_rewriter_contract.py -v
```

**Notes**:
- Use `jsonschema` library for validation
- Load schemas from `kitty-specs/015-document-rewrite-agent/contracts/`
- Test both valid and invalid inputs

---

### Subtask T045 – E2E test (.docx)

**Purpose**: Test full --make-review flow with a .docx document.

**Steps**:
1. Create `tests/test_rewriter_e2e.py`
2. Create test fixture: sample .docx with known content
3. Test full flow:
   - Run `product_committee.py --prd sample.docx --question "test" --make-review`
   - Verify output directory created
   - Verify original file copied
   - Verify conclusion.md created
   - Verify rewritten file created with correct name format
   - Verify metadata JSON created
4. Mock LLM calls for faster, reliable testing
5. Verify content changes applied (based on mock conclusion)

**Files**:
- `tests/test_rewriter_e2e.py` (new, ~100 lines for this test)

**Commands**:
```bash
pytest tests/test_rewriter_e2e.py::test_docx_e2e -v -s
```

**Notes**:
- Use `subprocess.run()` to invoke CLI
- Use temporary directory for test outputs
- Mock LLM to control test behavior

---

### Subtask T046 – E2E test (.md)

**Purpose**: Test full --make-review flow with a markdown document.

**Steps**:
1. In `tests/test_rewriter_e2e.py`, add .md E2E test
2. Create test fixture: sample .md file
3. Test flow similar to T045 but with .md input
4. Verify markdown conversion works correctly
5. Verify output is .md format

**Files**:
- `tests/test_rewriter_e2e.py` (append, ~80 lines for this test)

**Commands**:
```bash
pytest tests/test_rewriter_e2e.py::test_markdown_e2e -v -s
```

---

### Subtask T047 – Validate quickstart scenarios

**Purpose**: Manually or automatically validate the scenarios from quickstart.md.

**Steps**:
1. Review quickstart.md scenarios:
   - Basic usage with --make-review flag
   - Format support (.docx, .md, .txt)
   - Error handling (corrupted files, missing files)
2. For each scenario:
   - Set up test conditions
   - Run the scenario
   - Verify expected outcome
   - Document results
3. Create validation report:
   - Scenario name
   - Status (pass/fail)
   - Notes or issues found
4. Update quickstart.md if any scenarios don't work as documented

**Files**:
- `tests/validation/quickstart_validation_report.md` (new, ~100 lines)

**Notes**:
- This can be manual testing or automated if feasible
- Focus on the core scenarios from quickstart
- Document any deviations from expected behavior

---

### Subtask T048 – Full test suite run

**Purpose**: Run all tests and ensure no regressions in existing functionality.

**Steps**:
1. Run full test suite:
   ```bash
   pytest tests/ -v --tb=short
   ```
2. Check for new test failures
3. Check for regressions in existing tests
4. Verify coverage for new code (optional):
   ```bash
   pytest --cov=src.agents --cov=src.converters --cov=src.utils.file_utils --cov-report=term-missing
   ```
5. Fix any failing tests
6. Document any known issues or limitations

**Files**:
- No new files, run existing tests

**Validation**:
- [ ] All new tests pass
- [ ] No regressions in existing tests
- [ ] Coverage acceptable for new code (optional)

**Notes**:
- Run tests in clean environment (fresh venv)
- Check for flaky tests (random failures)
- Document any test issues in README

---

## Test Strategy

Comprehensive testing strategy:
1. Contract tests validate data structures
2. E2E tests validate full user workflows
3. Quickstart validation ensures user-facing docs are accurate
4. Regression testing ensures nothing broken

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| E2E tests may be flaky | Use mocks, proper fixtures, cleanup |
| Quickstart scenarios may be incomplete | Document gaps, update as needed |
| Test execution time too long | Separate unit from integration/E2E |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] Contract tests validate all schemas
- [ ] E2E tests for .docx and .md pass
- [ ] Quickstart scenarios validated
- [ ] Full test suite passes
- [ ] No regressions in existing tests
- [ ] All success criteria from spec.md met

**Context for reviewers**:
- Verify tests cover all user stories from spec.md
- Check that error cases are tested
- Confirm quickstart validation documented
- Ensure test quality (not just passing but meaningful)

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
