---
work_package_id: WP03
title: Workflow Integration
lane: planned
dependencies: []
subtasks:
- T011
- T012
- T013
- T014
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

# Work Package WP03 – Workflow Integration

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in frontmatter.
- **Report progress**: As you address each feedback item, update the **Activity Log** explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementer must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a must-Do before completion.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: ```<div>```, ```<script>```

Use language identifiers in code blocks: ```python```, ```bash```

---

## Objectives & Success Criteria

- **Modify DocumentDebateWorkflow.run()** – Accept optional progress_manager parameter without breaking existing behavior
- **Inject progress into state** – Add progress_manager to state dict as _progress_manager key
- **Update documentation** – Add docstring documenting new parameter
- **Integration test** – Verify progress_manager propagates through workflow correctly

## Context & Constraints

### Prerequisite Work
- WP01: Foundation - Progress Module (src/progress/ must exist)
- WP02: CLI Integration (ProgressManager instantiation code exists in document_debate_cli.py)

### Related Documents
- Spec: `kitty-specs/005-cli-progress-indicators/spec.md` – FR-001 Step Progress Display, FR-002 Verbose Mode Flag, FR-003 Default Verbosity Level
- Plan: `kitty-specs/005-cli-progress-indicators/plan.md` – Workflow integration approach, state injection strategy
- Data Model: `kitty-specs/005-cli-progress-indicators/data-model.md` – ProgressManager interface
- Existing Code: `workflow/document_debate_workflow.py` – Current workflow implementation

### Architectural Decisions
- **Optional parameter**: progress_manager defaults to None, maintaining backward compatibility
- **State injection**: Use underscore prefix `_progress_manager` to indicate transient UI data
- **Non-blocking**: Progress display must not interfere with async workflow execution
- **Type preservation**: Maintain existing return type (Dict[str, Any])

---

## Subtasks & Detailed Guidance

### Subtask T011 – Modify workflow.run() to accept optional progress_manager parameter

**Purpose**: Enable workflow to receive progress tracking without breaking existing usage.

**Files**:
- `workflow/document_debate_workflow.py` (modify existing)

**Steps**:
1. Locate run() method signature (around line 88):
   ```python
   async def run(self, initial_state: dict = None):
   ```
2. Add progress_manager parameter with default None:
   ```python
   async def run(
       self,
       initial_state: dict = None,
       progress_manager: ProgressManager = None
   ):
   ```
3. Preserve existing behavior: if initial_state is None, set to empty dict
4. Update docstring to document new parameter

**Parallel?**: No (single file modification)

**Validation**:
- [ ] run() signature includes progress_manager parameter with default None
- [ ] Existing behavior preserved when progress_manager is None
- [ ] Method remains async

---

### Subtask T012 – Inject progress_manager into state as _progress_manager

**Purpose**: Make progress manager accessible to all workflow nodes through state.

**Files**:
- `workflow/document_debate_workflow.py` (modify existing)

**Steps**:
1. After initial_state defaults are set (around line 109-114):
   ```python
   # Set default initial state if none provided
   if initial_state is None:
       initial_state = {
           "document_input": ""
       }
   ```
2. Add progress injection logic:
   ```python
   # Set default initial state if none provided
   if initial_state is None:
       initial_state = {
           "document_input": ""
       }

   # Inject progress_manager into state if provided
   if progress_manager is not None:
       initial_state = initial_state or {}
       initial_state["_progress_manager"] = progress_manager
   ```
3. Ensure initial_state is never None when passed to graph

**Parallel?**: No (follows T011 directly)

**Validation**:
- [ ] progress_manager only injected when not None
- [ ] initial_state is always a dict (never None) when passed to graph
- [ ] Underscore prefix `_progress_manager` indicates transient state data

---

### Subtask T013 – Update docstring for run() method

**Purpose**: Document the new progress_manager parameter for future developers.

**Files**:
- `workflow/document_debate_workflow.py` (modify existing)

**Steps**:
1. Locate existing docstring (around line 91-103):
   ```python
   """
   Run the document debate workflow.

   Args:
       initial_state: Optional initial state dict. Must contain 'document_input'
                     if not using default empty state.

   Returns:
       Final debate state with messages and verdict
   ```
2. Add progress_manager parameter documentation:
   ```python
   """
   Run the document debate workflow.

   Args:
       initial_state: Optional initial state dict. Must contain 'document_input'
                     if not using default empty state.
       progress_manager: Optional ProgressManager for progress tracking.
                     If provided, will be injected into state as '_progress_manager'
                     for use by workflow nodes.

   Returns:
       Final debate state with messages and verdict

   Example:
       workflow = DocumentDebateWorkflow()
       progress = ProgressManager(level=ProgressLevel.DEFAULT)
       result = await workflow.run(
           initial_state={"document_input": "..."},
           progress_manager=progress
       )
   ```
3. Maintain consistent formatting with other docstrings

**Parallel?**: No (follows T011 directly)

**Validation**:
- [ ] Docstring includes progress_manager parameter
- [ ] Docstring explains state injection behavior
- [ ] Docstring includes usage example

---

### Subtask T014 – Add integration test for workflow + progress

**Purpose**: Verify that progress manager correctly propagates through workflow to nodes.

**Files**:
- `tests/integration/test_progress_workflow.py` (new file)

**Steps**:
1. Create test file with pytest imports
2. Create mock ProgressManager that tracks method calls
3. Test with progress_manager provided:
   ```python
   async def test_workflow_with_progress_manager():
       mock_progress = MockProgressManager()
       workflow = DocumentDebateWorkflow()

       result = await workflow.run(
           initial_state={"direct_topic": "test"},
           progress_manager=mock_progress
       )

       # Verify progress was used
       assert mock_progress.start_step_calls > 0
       assert mock_progress.complete_step_calls > 0
   ```
4. Test without progress_manager (backward compatibility):
   ```python
   async def test_workflow_without_progress_manager():
       workflow = DocumentDebateWorkflow()
       result = await workflow.run(
           initial_state={"direct_topic": "test"}
       )
       # Should complete without error
       assert "messages" in result
   ```
5. Add pytest async fixture for event loop

**Parallel?**: No (independent test file)

**Validation**:
- [ ] Test passes with progress_manager provided
- [ ] Test passes without progress_manager (backward compatible)
- [ ] Mock progress calls verified (start_step, complete_step)

---

## Test Strategy

**Note**: Tests are explicitly required by the feature specification.

### Unit Tests
- **Location**: `tests/unit/test_workflow_integration.py` (create new file)
- **Purpose**: Verify workflow.run() signature and parameter handling
- **Test Cases**:
  - test_run_with_none_initial_state: Verify default empty state is used
  - test_run_with_progress_manager: Verify progress is injected into state
  - test_run_without_progress_manager: Verify backward compatibility
  - test_progress_manager_not_persisted: Verify _progress_manager not in final state

### Integration Tests
- **Location**: `tests/integration/test_progress_workflow.py`
- **Purpose**: Verify progress manager propagates to actual nodes during workflow execution
- **Test Cases**:
  - test_progress_accessible_to_nodes: Verify nodes can access _progress_manager from state
  - test_progress_steps_tracked: Verify step calls are made during execution
  - test_workflow_completion: Verify workflow completes successfully with progress

**Running Tests**:
```bash
# Unit tests
pytest tests/unit/test_workflow_integration.py -v

# Integration tests
pytest tests/integration/test_progress_workflow.py -v
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|--------|-----------|
| Breaking existing workflow | Nodes fail, crashes | Preserve None default for progress_manager, add integration test |
| State mutation side effects | Progress data pollutes state | Use underscore prefix convention, explicit about transient nature |
| Async workflow blocking | Progress bars slow execution | Use non-blocking tqdm updates, profile before finalizing |
| Backward compatibility loss | External code breaks | Test without progress_manager parameter, maintain default behavior |

---

## Review Guidance

**Key Acceptance Checkpoints for `/spec-kitty.review`**:
- [ ] workflow.run() signature updated with progress_manager parameter
- [ ] progress_manager injected into state as _progress_manager when provided
- [ ] Docstring documents new parameter and behavior
- [ ] Backward compatibility maintained (works without progress_manager)
- [ ] Integration test verifies progress propagation to nodes
- [ ] No hardcoded progress_manager references (only from parameter)

**Integration Context**:
- Next WPs (WP04, WP05) will depend on this workflow integration being complete
- Ensure workflow.run() signature matches expectations from WP02 CLI integration code
- Verify _progress_manager key matches convention from plan.md and research.md

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### Valid lanes
`planned`, `doing`, `for_review`, `done`

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to the bottom of this file (below "Valid lanes")
2. **APPEND** new entry at the **END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order)**:
```
- 2025-02-14T00:00:00Z – system – lane=planned – Prompt generated
```

---

## Valid lanes

`planned`, `doing`, `for_review`, `done`
