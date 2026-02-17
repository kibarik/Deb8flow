---
work_package_id: WP07
title: CLI Integration – document_debate_cli.py
lane: planned
dependencies:
- WP02
subtasks:
- T033
- T034
- T035
- T036
- T037
phase: Phase 3 - Integration
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

# Work Package Prompt: WP07 – CLI Integration (document_debate_cli.py)

## Objectives & Success Criteria

- **Goal**: Add `--make-review` flag to document_debate_cli.py with file copying and rewriter invocation.
- **Success Criteria**:
  - `--make-review` flag added to argument parser
  - Original file copied to run-id directory before workflow
  - Rewriter agent invoked after workflow completes
  - Status messages displayed using rich formatting
  - Integration test verifies full flow

## Context & Constraints

- **Prerequisites**: WP02 (file ops), WP05 (rewriter agent)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/spec.md` - User Story 1 acceptance scenarios
  - `kitty-specs/015-document-rewrite-agent/plan.md` - CLI integration approach
  - `document_debate_cli.py` - Existing CLI to modify
- **Constraints**:
  - Must not break existing functionality
  - Rewriter invocation wrapped in try/except
  - Handle both --docx and --text input modes
  - Status messages use existing rich formatting patterns

## Subtasks & Detailed Guidance

### Subtask T033 – Add --make-review argument

**Purpose**: Add the CLI flag that triggers the rewrite functionality for document debates.

**Steps**:
1. Open `document_debate_cli.py`
2. Locate the argument parser section
3. Add new argument: `--make-review` with `action="store_true"`, `help="Automatically rewrite document based on debate conclusions"`
4. Store the argument value
5. Pass through to the main debate function

**Files**:
- `document_debate_cli.py` (modify, ~10 lines added)

**Validation**:
- [ ] `--make-review` flag recognized
- [ ] Default is False when not provided
- [ ] Help text is clear

---

### Subtask T034 – Implement file copy logic

**Purpose**: Copy the original document to the run-id directory before running the workflow.

**Steps**:
1. In `document_debate_cli.py`, locate where run-id directory is created
2. Add file copy logic after directory creation:
   - Check if `--make-review` flag set
   - Determine input file path from `--docx` or `--text` argument
   - Call `copy_document_with_metadata(input_path, run_id_dir)`
   - Log success using rich

**Files**:
- `document_debate_cli.py` (modify, ~20 lines added)

**Validation**:
- [ ] Works with `--docx` input
- [ ] Works with `--text` input
- [ ] File copied to run-id directory
- [ ] Error handled gracefully

**Notes**:
- Document debate may not have run-id directory - create if needed
- Handle both input modes (--docx and --text)

---

### Subtask T035 – Implement rewriter invocation

**Purpose**: Invoke the rewriter agent after the workflow completes.

**Steps**:
1. In `document_debate_cli.py`, locate where workflow completes
2. Add rewriter invocation after workflow finishes:
   - Check `--make-review` flag and workflow success
   - Build `RewriteRequest` with appropriate paths
   - Create `RewriterAgent` and call `rewrite_document()`
   - Handle result with status messages
   - Wrap in try/except

**Files**:
- `document_debate_cli.py` (modify, ~40 lines added)

**Validation**:
- [ ] Rewriter invoked after workflow succeeds
- [ ] Works with both --docx and --text inputs
- [ ] Success/failure displayed
- [ ] Exceptions caught

---

### Subtask T036 – Add rewriter status output

**Purpose**: Display clear status messages about the rewrite operation.

**Steps**:
1. Add status messages similar to WP06:
   - Start message: Running document rewriter...
   - Success: Rewrite complete with filename and stats
   - Failure: Rewrite failed with error
2. Use rich formatting consistent with existing CLI

**Files**:
- `document_debate_cli.py` (modify, ~15 lines added)

**Validation**:
- [ ] Messages use rich formatting
- [ ] Success shows filename and stats
- [ ] Failure shows error

---

### Subtask T037 – Document debate integration test

**Purpose**: Test the full --make-review flow for document debates.

**Steps**:
1. Create `tests/integration/test_document_debate_rewrite.py`
2. Test fixtures: sample .docx, conclusion.md
3. Test cases:
   - `test_make_review_with_docx()` - Full flow with .docx
   - `test_make_review_with_text()` - Full flow with --text
   - `test_make_review_without_flag()` - Skips without flag
4. Mock LLM calls

**Files**:
- `tests/integration/test_document_debate_rewrite.py` (new, ~100 lines)

**Commands**:
```bash
pytest tests/integration/test_document_debate_rewrite.py -v
```

---

## Test Strategy

Similar to WP06 but for document_debate_cli.py. Verify:
- Both input modes work
- Rewriter invoked at correct time
- Status messages displayed
- Error handling preserves workflow results

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Different input paths for --docx vs --text | Normalize to single input path |
| Document debate may not create run-id dir | Create directory if missing |
| Existing functionality broken | Run existing tests |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] `--make-review` flag added
- [ ] Works with both --docx and --text inputs
- [ ] Rewriter invoked after workflow
- [ ] Status messages use rich formatting
- [ ] Integration test passes
- [ ] Existing tests still pass

**Context for reviewers**:
- Verify input path normalization works for both modes
- Check that run-id directory is created if missing
- Confirm rewriter uses same LLM config as workflow

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
