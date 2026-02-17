---
work_package_id: WP03
title: Testing & Validation
lane: "doing"
dependencies: []
base_branch: main
base_commit: 6358c4792bf147682b4376e7e634dde67c02fbef
created_at: '2026-02-17T14:53:08.625137+00:00'
subtasks:
- T012
- T013
- T014
- T015
- T016
- T017
phase: Phase 1 - Testing
assignee: ''
agent: ''
shell_pid: "59933"
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-17T16:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP03 – Testing & Validation

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: `python`, `bash`

---

## Objectives & Success Criteria

**Primary Objective**: Comprehensive E2E testing of the language flag feature and verification of backward compatibility.

**Success Criteria**:
- E2E test verifies `--language` flag works in standard debate
- E2E test verifies `--language` flag works in document debate
- Backward compatibility test confirms no flag = existing behavior
- All existing E2E tests pass without modification
- Language setting properly propagates through workflows

---

## Context & Constraints

**Feature Specification**: [spec.md](../spec.md)
**Implementation Plan**: [plan.md](../plan.md)
**Quickstart Guide**: [quickstart.md](../quickstart.md)

**Prerequisites**:
- WP01 must be complete (DebateState and BaseComponent changes)
- WP02 must be complete (CLI flag integration)

**Testing Philosophy**:
- **E2E focus**: Tests verify full workflow execution
- **Backward compatibility**: Existing tests must pass
- **Pragmatic validation**: Check for injection presence, not actual AI language compliance (unreliable)

**Constitution Requirements**:
- pytest is required for all features
- Tests should cover critical paths
- Focus on correctness and testability

---

## Subtasks & Detailed Guidance

### Subtask T012 – Verify debate_workflow.py state propagation

**Purpose**: Confirm that `debate_workflow.py` properly carries `language_setting` through the workflow state.

**Files**:
- `workflow/debate_workflow.py`

**Steps**:

1. **Read the workflow file** to understand state management:
   ```bash
   head -100 workflow/debate_workflow.py
   ```

2. **Check initial state handling**:
   - Look for `run()` method signature
   - Check if it accepts `initial_state` parameter
   - Verify state is merged/updated correctly

3. **Verify state flow**:
   - Initial state → workflow state
   - Workflow state → individual agent nodes
   - Agent nodes receive state via `__call__()`

4. **No changes needed** - this is verification only:
   - If state propagation looks correct, note it
   - If issues found, document for WP01/WP02 fixes

**Validation**:
- [ ] State propagation path is understood
- [ ] `language_setting` reaches agent nodes via state
- [ ] No hardcoded state resets that would overwrite language_setting

**Notes**:
- This is a code review task, not implementation
- Document findings for the test cases below

---

### Subtask T013 – Verify document_debate_workflow.py state propagation

**Purpose**: Confirm that `document_debate_workflow.py` properly carries `language_setting` through the workflow state.

**Files**:
- `workflow/document_debate_workflow.py`

**Steps**:

1. **Read the workflow file** to understand state management:
   ```bash
   head -100 workflow/document_debate_workflow.py
   ```

2. **Check initial state handling**:
   - Look for `run()` method signature
   - Check if it accepts `initial_state` parameter
   - Verify state is merged/updated correctly

3. **Verify state flow**:
   - Initial state → workflow state
   - Workflow state → topic generator node
   - Topic generator → debate nodes

4. **No changes needed** - this is verification only

**Validation**:
- [ ] State propagation path is understood
- [ ] `language_setting` reaches all agent nodes
- [ ] No state drops between workflow stages

**Notes**:
- Document workflow may have different state flow than standard debate
- Note any differences for test design

---

### Subtask T014 – Add E2E test for --language flag in standard debate

**Purpose**: Create an end-to-end test that verifies the `--language` flag works in standard debates.

**Files**:
- `tests/e2e/test_full_debate_flow.py` (add to existing file)

**Steps**:

1. **Read existing test structure**:
   ```bash
   head -50 tests/e2e/test_full_debate_flow.py
   ```

2. **Add new test function**:
   ```python
   def test_language_flag_standard_debate():
       """Test that --language flag injects language setting into standard debate."""
       import subprocess
       import sys

       # Run debate with language flag
       result = subprocess.run(
           [sys.executable, "main.py", "--language", "Русский официальный стиль"],
           capture_output=True,
           text=True,
           timeout=60
       )

       # Check that workflow ran
       assert result.returncode == 0, f"Workflow failed: {result.stderr}"

       # Note: We can't easily verify AI output language without API calls
       # But we can verify the workflow completed without errors
       assert "DEBATE VERDICT" in result.stdout or "Workflow completed" in result.stdout
   ```

3. **Alternative approach** (if subprocess doesn't work):
   ```python
   def test_language_flag_in_state():
       """Test that language setting propagates through state."""
       from workflow.debate_workflow import DebateWorkflow

       language_setting = "Test Language Setting"
       initial_state = {"language_setting": language_setting}

       # Mock the workflow to avoid actual LLM calls
       # This test verifies state handling, not AI behavior
       workflow = DebateWorkflow()

       # Verify initial state is accepted
       assert initial_state["language_setting"] == language_setting
   ```

**Validation**:
- [ ] Test runs successfully
- [ ] Workflow completes with language flag
- [ ] No errors related to language_setting

**Notes**:
- E2E tests may require API keys; skip if not available
- Focus on state propagation, not AI language compliance
- Use pytest markers for slow tests: `@pytest.mark.slow`

---

### Subtask T015 – Add E2E test for --language flag in document debate [PARALLEL]

**Purpose**: Create an end-to-end test that verifies the `--language` flag works in document-based debates.

**Files**:
- `tests/e2e/test_document_debate_e2e.py` (add to existing file)

**Steps**:

1. **Read existing test structure**:
   ```bash
   head -50 tests/e2e/test_document_debate_e2e.py
   ```

2. **Add new test function**:
   ```python
   def test_language_flag_document_debate():
       """Test that --language flag works with document debate."""
       import subprocess
   import sys

       # Run document debate with language flag
       result = subprocess.run(
           [sys.executable, "document_debate_cli.py",
              "--text", "Test topic",
              "--language", "English, concise and factual"],
           capture_output=True,
           text=True,
           timeout=60
       )

       # Check that workflow ran
       assert result.returncode == 0, f"Workflow failed: {result.stderr}"

       # Verify workflow completed
       assert "DEBATE VERDICT" in result.stdout or "Workflow completed" in result.stdout
   ```

**Validation**:
- [ ] Test runs successfully
- [ ] Works with `--text` mode
- [ ] Language setting accepted without error

**Parallel Notes**: Can be written simultaneously with T014

---

### Subtask T016 – Add backward compatibility test

**Purpose**: Verify that existing behavior is preserved when `--language` flag is not provided.

**Files**:
- `tests/e2e/test_full_debate_flow.py` (add to existing file)

**Steps**:

1. **Add backward compatibility test**:
   ```python
   def test_backward_compatibility_no_language_flag():
       """Test that debates work without --language flag (backward compatibility)."""
       import subprocess
       import sys

       # Run debate WITHOUT language flag
       result = subprocess.run(
           [sys.executable, "main.py"],
           capture_output=True,
           text=True,
           timeout=60
       )

       # Check that workflow ran normally
       assert result.returncode == 0, f"Workflow failed: {result.stderr}"

       # Verify normal completion
       assert "DEBATE VERDICT" in result.stdout or "Workflow completed" in result.stdout

       # Verify no language-related errors
       assert "language" not in result.stderr.lower()
       assert "Language and Style Setting" not in result.stdout
   ```

2. **Also test document debate**:
   ```python
   def test_backward_compatibility_document_debate_no_flag():
       """Test that document debate works without --language flag."""
       import subprocess
       import sys

       result = subprocess.run(
           [sys.executable, "document_debate_cli.py", "--text", "Test topic"],
           capture_output=True,
           text=True,
           timeout=60
       )

       assert result.returncode == 0, f"Workflow failed: {result.stderr}"
   ```

**Validation**:
- [ ] Both tests pass
- [ ] No language-related errors or warnings
- [ ] Outputs match pre-feature behavior

**Notes**:
- Critical test: ensures feature doesn't break existing usage
- Compare output with baseline if available

---

### Subtask T017 – Verify all existing E2E tests pass

**Purpose**: Run the full E2E test suite to ensure no regressions were introduced.

**Files**:
- All E2E test files

**Steps**:

1. **Run all E2E tests**:
   ```bash
   pytest tests/e2e/ -v
   ```

2. **Run specific test files**:
   ```bash
   pytest tests/e2e/test_full_debate_flow.py -v
   pytest tests/e2e/test_document_debate_e2e.py -v
   ```

3. **Check for failures**:
   - If tests fail, investigate root cause
   - Fix in WP01/WP02 if needed
   - Document any test updates required

4. **Run with coverage** (optional):
   ```bash
   pytest tests/e2e/ --cov=nodes --cov=workflow
   ```

**Validation**:
- [ ] All existing E2E tests pass
- [ ] No new warnings introduced
- [ ] Coverage report shows new code tested

**Remediation**:
- If tests fail: fix implementation in WP01/WP02
- If tests need updates: document why and apply changes

---

## Test Strategy

**Test Files Modified**:
- `tests/e2e/test_full_debate_flow.py` - Add T014, T016
- `tests/e2e/test_document_debate_e2e.py` - Add T015

**Running Tests**:
```bash
# Run new tests only
pytest tests/e2e/test_full_debate_flow.py::test_language_flag_standard_debate -v
pytest tests/e2e/test_document_debate_e2e.py::test_language_flag_document_debate -v
pytest tests/e2e/test_full_debate_flow.py::test_backward_compatibility_no_language_flag -v

# Run all E2E tests
pytest tests/e2e/ -v

# Run with slow test marker
pytest tests/e2e/ -v -m "not slow"  # Skip slow tests
pytest tests/e2e/ -v -m slow  # Only slow tests
```

**Test Categories**:
1. **New feature tests**: T014, T015 - Verify language flag works
2. **Backward compatibility**: T016, T017 - Ensure no regressions
3. **State verification**: T012, T013 - Code review, not tests

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| E2E tests require API keys | High | Skip tests if keys not available; use pytest markers |
| AI language behavior non-deterministic | Medium | Test state propagation, not actual AI output |
| Tests timeout on slow systems | Low | Increase timeout values; mark as slow |
| Existing tests fail due to state changes | Medium | Fix implementation, not tests (backward compat is critical) |

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. At least 2 new E2E tests for language flag functionality
2. Backward compatibility test passes (no flag = same behavior)
3. All existing E2E tests pass without modification
4. State propagation verified through both workflows
5. Tests can run without API keys (graceful skip)

**What to Review**:
- Test coverage of new feature
- Backward compatibility verification
- Test reliability (not flaky due to AI non-determinism)

**Red Flags**:
- Tests that verify actual AI language output (unreliable)
- Skipping backward compatibility tests
- Tests that require real LLM calls without fallbacks

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

- 2025-02-17T16:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP03 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

**Implementation Command**:
```bash
spec-kitty implement WP03 --base WP02
```
