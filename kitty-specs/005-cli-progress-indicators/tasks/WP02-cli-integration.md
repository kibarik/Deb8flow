---
work_package_id: WP02
title: CLI Integration
lane: planned
dependencies: []
subtasks:
- T006
- T007
- T008
- T009
- T010
phase: Phase1
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-14T00:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package WP02 – CLI Integration

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the **Activity Log** explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementer must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a must-Do before completion.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: ``<div>``, ``<script>``

Use language identifiers in code blocks: ```python```, ```bash```

---

## Objectives & Success Criteria

- **Integrate verbosity flags into CLI** – Add `--verbose` and `--quiet` arguments to document_debate_cli.py
- **Create ProgressManager/CLIOutput instances** – Instantiate based on user flags with proper precedence (quiet > verbose > default)
- **Pass progress to workflow** – Call DocumentDebateWorkflow.run() with progress_manager parameter
- **Add tqdm dependency** – Update requirements.txt with tqdm>=4.66.0
- **Test all verbosity modes** – Verify quiet, default, and verbose modes work correctly

## Context & Constraints

### Prerequisite Work
- WP01 (Foundation - Progress Module) must be complete
  - `src/progress/progress_manager.py` exists
  - `src/progress/cli_output.py` exists
  - `src/progress/__init__.py` exports both classes

### Related Documents
- Spec: `kitty-specs/005-cli-progress-indicators/spec.md` – FR-002: Verbose Mode Flag, FR-005: Quiet Mode Flag
- Plan: `kitty-specs/005-cli-progress-indicators/plan.md` – CLI integration approach
- Data Model: `kitty-specs/005-cli-progress-indicators/data-model.md` – ProgressLevel enum values
- Existing Code: `document_debate_cli.py` – Current argparse setup

### Architectural Decisions
- **Verbosity precedence**: quiet flag overrides verbose flag (if both set, quiet wins)
- **Dependency injection**: Pass ProgressManager to workflow.run(), not to individual nodes
- **Import path**: Import from `src.progress` (absolute or relative to project root)

---

## Subtasks & Detailed Guidance

### Subtask T006 – Add --verbose and --quiet argument flags to argparse

**Purpose**: Extend the CLI argument parser to support verbosity control flags.

**Files**:
- `document_debate_cli.py` (modify existing)

**Steps**:
1. Locate the argparse.ArgumentParser setup in main() function (around line 80)
2. Add two new arguments:
   ```python
   parser.add_argument(
       "--verbose",
       action="store_true",
       help="Enable detailed progress output with sub-steps and timing"
   )
   parser.add_argument(
       "--quiet", "-q",
       action="store_true",
       help="Suppress non-critical output, only show errors and final verdict"
   )
   ```
3. Position after existing `--request` argument (maintain logical grouping)
4. Ensure help text matches FR-002 and FR-005 from spec

**Parallel?**: No (modifies same file as T007-T008)

**Validation**:
- [ ] `--verbose` flag recognized by CLI (no error when used)
- [ ] `--quiet` and `-q` short flag both work
- [ ] Help text displays correctly with `--help` flag

---

### Subtask T007 – Instantiate ProgressManager and CLIOutput based on flags

**Purpose**: Create progress tracking instances based on user's verbosity preference.

**Files**:
- `document_debate_cli.py` (modify existing)

**Steps**:
1. Add import for progress module and ProgressLevel enum:
   ```python
   from src.progress import ProgressManager, CLIOutput, ProgressLevel
   ```
2. After args = parser.parse_args(), determine verbosity level:
   ```python
   # Determine verbosity level with precedence: quiet > verbose > default
   if args.quiet:
       verbosity = ProgressLevel.QUIET
   elif args.verbose:
       verbosity = ProgressLevel.VERBOSE
   else:
       verbosity = ProgressLevel.DEFAULT
   ```
3. Create ProgressManager and CLIOutput instances:
   ```python
   progress = ProgressManager(level=verbosity)
   output = CLIOutput(level=verbosity)
   ```
4. Pass both to workflow if needed (for potential future logging use)

**Parallel?**: No (uses same file and imports as T008)

**Validation**:
- [ ] QUIET flag creates ProgressManager with QUIET level
- [ ] verbose flag creates ProgressManager with VERBOSE level
- [ ] No flags creates ProgressManager with DEFAULT level
- [ ] Both flags set: quiet takes precedence (verified by level value)

---

### Subtask T008 – Pass progress_manager to workflow.run()

**Purpose**: Enable workflow to receive and propagate progress tracking.

**Files**:
- `document_debate_cli.py` (modify existing)
- `workflow/document_debate_workflow.py` (reference for method signature)

**Steps**:
1. Locate the workflow execution (around line 153):
   ```python
   workflow = DocumentDebateWorkflow()
   workflow_result = await workflow.run(initial_state=initial_state)
   ```
2. Update the run() call to include progress_manager:
   ```python
   workflow_result = await workflow.run(
       initial_state=initial_state,
       progress_manager=progress
   )
   ```
3. Verify workflow.run() signature matches (will be modified in WP03)
4. Ensure progress variable is defined before workflow.run() call

**Parallel?**: Yes (can be done independently of WP01, but imports progress module)

**Validation**:
- [ ] ProgressManager instance passed to workflow.run()
- [ ] No runtime error when progress_manager parameter added
- [ ] Workflow can access progress_manager through state (verified in WP03)

---

### Subtask T009 – Update requirements.txt with tqdm>=4.66.0

**Purpose**: Add tqdm as a project dependency for progress bar functionality.

**Files**:
- `requirements.txt` (modify existing)

**Steps**:
1. Open requirements.txt (currently has rich==14.0.0)
2. Add tqdm line after python-docx line:
   ```
   tqdm>=4.66.0
   ```
3. Ensure version constraint matches compatibility requirements
4. Verify alphabetical/logical ordering (core deps first)

**Parallel?**: Yes (independent of other tasks)

**Validation**:
- [ ] `tqdm>=4.66.0` added to requirements.txt
- [ ] Version is >= 4.66.0 (supports RichTqdm from plan.md)
- [ ] File syntax is valid (one package per line)

---

### Subtask T010 – Test CLI with different verbosity levels

**Purpose**: Verify all three verbosity modes work correctly from CLI.

**Files**:
- `document_debate_cli.py` (testing modified file)

**Steps**:
1. Test QUIET mode: `python3 document_debate_cli.py --docx test.docx --request "test" --quiet`
   - Expected: Minimal output, no progress bars
2. Test DEFAULT mode: `python3 document_debate_cli.py --docx test.docx --request "test"`
   - Expected: Step progress displayed
3. Test VERBOSE mode: `python3 document_debate_cli.py --docx test.docx --request "test" --verbose`
   - Expected: Detailed progress with sub-steps
4. Test flag precedence: `python3 ... --quiet --verbose`
   - Expected: Quiet mode takes precedence

**Parallel?**: No (integration test, depends on T006-T009)

**Validation**:
- [ ] QUIET mode suppresses progress bars
- [ ] DEFAULT mode shows step progress
- [ ] VERBOSE mode shows detailed information
- [ ] Flag precedence works correctly (quiet > verbose)

---

## Test Strategy

**Note**: Tests are explicitly required by the feature specification.

### Unit Tests
- **Location**: `tests/unit/test_cli_integration.py` (create new file)
- **Purpose**: Verify CLI argument parsing and ProgressManager instantiation
- **Test Cases**:
  - test_verbosity_flags(): Verify all three flag combinations parse correctly
  - test_progress_manager_creation(): Verify correct ProgressLevel values used
  - test_import_from_progress_module(): Verify imports work correctly

### Integration Tests
- **Location**: `tests/integration/test_cli_verbosity.py` (create new file)
- **Purpose**: Verify CLI + workflow integration with all verbosity levels
- **Test Cases**:
  - test_quiet_mode(): Run workflow with --quiet, verify minimal output
  - test_default_mode(): Run workflow without flags, verify step progress
  - test_verbose_mode(): Run workflow with --verbose, verify detailed output
  - test_flag_precedence(): Verify --quiet overrides --verbose

### Running Tests
```bash
# Unit tests only for this WP
pytest tests/unit/test_cli_integration.py -v

# Full integration tests
pytest tests/integration/test_cli_verbosity.py -v
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|--------|-----------|
| Import path issues | ModuleNotFoundError when running CLI | Verify src.progress is in Python path, use relative imports if needed |
| tqdm version conflict | RichTqdm unavailable in older tqdm | Pin tqdm>=4.66.0 in requirements.txt |
| Progress overhead | NFR-001 violated (>5% slowdown) | Profile before WP06, optimize tqdm refresh rate if needed |
| Verbosity state confusion | Wrong level applied | Add debug logging of verbosity level during development |

---

## Review Guidance

**Key Acceptance Checkpoints for `/spec-kitty.review`**:
- [ ] Verbosity flags added with correct argparse syntax
- [ ] ProgressLevel determination logic handles all flag combinations
- [ ] ProgressManager and CLIOutput instantiated with correct level
- [ ] progress_manager passed to workflow.run() successfully
- [ ] requirements.txt includes tqdm>=4.66.0
- [ ] All three verbosity modes tested and working

**Integration Context**:
- Next WP (WP03) will depend on workflow.run() accepting progress_manager parameter
- Ensure T008 matches expected workflow.run() signature from plan.md
- Verify no hardcoded API keys or credentials in any modified code
