---
work_package_id: WP06
title: CLI Integration – product_committee.py
lane: planned
dependencies:
- WP02
subtasks:
- T028
- T029
- T030
- T031
- T032
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

# Work Package Prompt: WP06 – CLI Integration (product_committee.py)

## Objectives & Success Criteria

- **Goal**: Add `--make-review` flag to product_committee.py with file copying and rewriter invocation.
- **Success Criteria**:
  - `--make-review` flag added to argument parser
  - Original file copied to run-id directory before debate
  - Rewriter agent invoked after conclusion.md generated
  - Status messages displayed using rich formatting
  - Integration test verifies full flow

## Context & Constraints

- **Prerequisites**: WP02 (file ops), WP05 (rewriter agent)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/spec.md` - User Story 1 acceptance scenarios
  - `kitty-specs/015-document-rewrite-agent/plan.md` - CLI integration approach
  - `product_committee.py` - Existing CLI to modify
- **Constraints**:
  - Must not break existing functionality
  - Rewriter invocation wrapped in try/except (never crash main workflow)
  - Status messages use existing rich formatting patterns
  - File copy happens BEFORE debate (in case debate fails)

## Subtasks & Detailed Guidance

### Subtask T028 – Add --make-review argument

**Purpose**: Add the CLI flag that triggers the rewrite functionality.

**Steps**:
1. Open `product_committee.py`
2. Locate the argument parser section (likely using `argparse`)
3. Add new argument: `--make-review` with `action="store_true"`, `help="Automatically rewrite document based on debate conclusions"`
4. Store the argument value in a variable (e.g., `args.make_review`)
5. Pass the flag through to the main committee function

**Files**:
- `product_committee.py` (modify, ~10 lines added)

**Validation**:
- [ ] `--make-review` flag recognized by CLI
- [ ] Default value is False when flag not provided
- [ ] Help text is clear and concise

**Notes**:
- Follow existing argument pattern in the file
- Group with other output-related flags if present

---

### Subtask T029 – Implement file copy logic

**Purpose**: Copy the original document to the run-id directory before running the debate.

**Steps**:
1. In `product_committee.py`, locate where run-id directory is created
2. After directory creation, add file copy logic:
   - Check if `--make-review` flag is set
   - If True and `--prd` argument provided:
     - Get original document path from `args.prd`
     - Get run-id directory path (already created)
     - Call `copy_document_with_metadata(args.prd, run_id_dir)` from WP02
     - Log success message using rich: `[green]✓[/green] Copied original to {run_id_dir}/`
   - Handle errors: log warning but continue with debate

**Files**:
- `product_committee.py` (modify, ~20 lines added)

**Imports needed**:
```python
from src.utils.file_utils import copy_document_with_metadata
```

**Validation**:
- [ ] File copied to run-id directory when `--make-review` set
- [ ] Original filename preserved in copy
- [ ] Error handled gracefully if copy fails
- [ ] Rich formatted success message displayed

**Notes**:
- Copy must happen BEFORE debate starts (in case debate fails, we still have the copy)
- Use existing rich console for formatted output
- Log both success and failure cases

---

### Subtask T030 – Implement rewriter invocation

**Purpose**: Invoke the rewriter agent after the debate completes and conclusion is saved.

**Steps**:
1. In `product_committee.py`, locate where `save_artifacts()` is called (after debate completes)
2. After artifacts saved, add rewriter invocation:
   - Check if `--make-review` flag is set
   - If True and debate succeeded:
     - Import `RewriterAgent` from `src.agents.rewriter_agent`
     - Create `RewriteRequest` with:
       - `original_document_path`: copied file in run-id dir
       - `conclusion_path`: `conclusion.md` in run-id dir
       - `output_directory`: run-id dir
       - `original_filename`: original filename
       - `format`: detected from extension
       - `model_config`: reuse debate LLM config
     - Create `RewriterAgent` with LLM config
     - Call `rewriter.rewrite_document(request)`
     - Handle result: display success/failure message
   - Wrap in try/except: log error but don't crash

**Files**:
- `product_committee.py` (modify, ~40 lines added)

**Imports needed**:
```python
from src.agents.rewriter_agent import RewriterAgent
from src.types.rewrite_types import RewriteRequest, DocumentFormat
```

**Validation**:
- [ ] Rewriter agent invoked after debate succeeds
- [ ] RewriteRequest populated with correct values
- [ ] Success/failure status displayed to user
- [ ] Exceptions caught and logged without crashing

**Notes**:
- Only invoke if debate succeeded (conclusion.md exists)
- Use the same LLM config as the debate (reuse existing config)
- Display status using rich: green checkmark for success, red X for failure

---

### Subtask T031 – Add rewriter status output

**Purpose**: Display clear status messages about the rewrite operation.

**Steps**:
1. In `product_committee.py`, add status messages for rewriter operations:
   - Start message: `[dim]→[/dim] Running document rewriter...`
   - Success message: `[green]✓[/green] Rewrite complete: {output_file}`
     - Show: recommendations applied, processing time
   - Failure message: `[red]✗[/red] Rewrite failed: {error}`
   - Include rewrite metadata in output:
     - Original file, rewritten file, recommendations count
2. Use rich formatting for all messages (consistent with existing CLI style)
3. Add blank line before rewriter output for visual separation

**Files**:
- `product_committee.py` (modify, ~15 lines added for status output)

**Example output**:
```
[green]✓[/green] Committee debate complete
[dim]→[/dim] Running document rewriter...
[green]✓[/green] Rewrite complete: RUN_20260217_123456/prd_20260217_123456.docx
  Applied 7/7 recommendations in 45.2 seconds
```

**Validation**:
- [ ] Status messages use rich formatting
- [ ] Success case shows output filename and stats
- [ ] Failure case shows error message
- [ ] Messages are clear and actionable

---

### Subtask T032 – Product committee integration test

**Purpose**: Test the full --make-review flow for product committee debates.

**Steps**:
1. Create `tests/integration/test_product_committee_rewrite.py` (new file)
2. Create test fixtures: sample .docx file, minimal conclusion.md
3. Test full flow:
   - `test_make_review_flag_copies_file()` - File copied to run-id
   - `test_make_review_invokes_rewriter()` - Rewriter called
   - `test_make_review_creates_output()` - Rewritten file created
   - `test_make_review_without_flag_skips()` - No rewriter without flag
   - `test_debate_failure_skips_rewriter()` - Rewriter not called on debate failure
4. Mock LLM calls to avoid actual API usage in tests
5. Verify output file naming format matches specification

**Files**:
- `tests/integration/test_product_committee_rewrite.py` (new, ~120 lines)

**Commands**:
```bash
pytest tests/integration/test_product_committee_rewrite.py -v
```

**Mocking**:
- Use `unittest.mock.patch` to mock `RewriterAgent.rewrite_document()`
- Or use `unittest.mock.Mock` to simulate rewriter behavior

---

## Test Strategy

Integration tests should verify:
- Flag triggers all expected behavior
- File copy happens before debate
- Rewriter invoked after debate succeeds
- Error handling preserves debate results
- Output files created with correct names

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Debate failure should still preserve copied file | Separate try/except blocks for copy and rewriter |
| Rewriter timeout hangs main workflow | Add timeout, wrap in try/except |
| Existing functionality broken by changes | Run existing tests to verify no regression |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] `--make-review` flag added to argument parser
- [ ] File copy happens BEFORE debate runs
- [ ] Rewriter invoked AFTER conclusion.md saved
- [ ] Rich formatted status messages displayed
- [ ] Integration test passes
- [ ] Existing product_committee tests still pass

**Context for reviewers**:
- Verify that file copy uses `copy_document_with_metadata()` from WP02
- Check that rewriter uses same LLM config as debate
- Confirm error handling never crashes the main workflow
- Ensure status messages follow existing rich formatting patterns

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
