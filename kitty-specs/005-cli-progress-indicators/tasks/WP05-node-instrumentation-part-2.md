---
work_package_id: WP05
title: Node Instrumentation - Part 2
lane: planned
dependencies: []
subtasks:
- T019
- T020
- T021
- T022
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

# Work Package WP05 – Node Instrumentation - Part 2

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

- **Instrument remaining nodes** – Add progress hooks to debate_moderator_node.py, fact_check_node.py, judge_node.py
- **Follow WP04 pattern** – Use same progress extraction and step calling approach
- **Unit test coverage** – Add comprehensive tests for all instrumented nodes
- **Zero regressions** – All existing functionality preserved

## Context & Constraints

### Prerequisite Work
- WP03: Workflow Integration (state injection via _progress_manager key complete)
- WP04: Node Instrumentation - Part 1 (pattern established, progress_manager available in nodes)

### Related Documents
- Spec: `kitty-specs/005-cli-progress-indicators/spec.md` – FR-001 Step Progress Display
- Plan: `kitty-specs/005-cli-progress-indicators/plan.md` – Node instrumentation strategy
- Data Model: `kitty-specs/005-cli-progress-indicators/data-model.md` – ProgressManager interface
- Existing Code: `nodes/debate_moderator_node.py`, `nodes/fact_check_node.py`, `nodes/judge_node.py`

### Architectural Decisions
- **Consistent pattern**: Use exact same progress extraction code as WP04 (state.get("_progress_manager"))
- **Step positioning**: Continue sequential numbering (4=moderator, 5=fact_check, 6=judge)
- **Optional integration**: All progress calls wrapped in `if progress:` to support graceful degradation
- **Verbose flag**: Add verbose logging for LLM API calls when progress.level == ProgressLevel.VERBOSE

---

## Subtasks & Detailed Guidance

### Subtask T019 – Instrument debate_moderator_node.py with progress hooks

**Purpose**: Add progress tracking to debate moderator node.

**Files**:
- `nodes/debate_moderator_node.py` (modify existing)

**Steps**:
1. Add import at top of file:
   ```python
   from src.progress import ProgressManager, ProgressLevel
   ```
2. Locate __call__ method (around line 32)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before main logic:
   ```python
   if progress:
       progress.start_step("Moderating debate flow", total=1, current=4)
   ```
5. Add complete_step() call before return
6. Add verbose logging if applicable (not typically needed for moderator)

**Parallel?**: Yes (independent file)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Moderating debate flow", total=1, current=4
- [ ] complete_step() called at end of method
- [ ] Works when _progress_manager missing from state (graceful)

---

### Subtask T020 – Instrument fact_check_node.py with progress hooks

**Purpose**: Add progress tracking to fact checker node.

**Files**:
- `nodes/fact_check_node.py` (modify existing)

**Steps**:
1. Add import at top of file:
   ```python
   from src.progress import ProgressManager, ProgressLevel
   ```
2. Locate __call__ method (around line 13)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before main logic:
   ```python
   if progress:
       progress.start_step("Fact checking arguments", total=1, current=5)
   ```
5. Add complete_step() call before return
6. Add verbose logging for fact check operations (if VERBOSE):
   ```python
   if progress and progress.level == ProgressLevel.VERBOSE:
       # Use progress.verbose or similar
       print(f"Checking facts for statement: {statement_to_check}")
   ```

**Parallel?**: Yes (independent file)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Fact checking arguments", total=1, current=5
- [ ] complete_step() called at end of method
- [ ] Verbose logging only shows in VERBOSE mode
- [ ] Works when _progress_manager missing from state (graceful)

---

### Subtask T021 – Instrument judge_node.py with progress hooks

**Purpose**: Add progress tracking to judge node for final verdict step.

**Files**:
- `nodes/judge_node.py` (modify existing)

**Steps**:
1. Add import at top of file:
   ```python
   from src.progress import ProgressManager, ProgressLevel
   ```
2. Locate __call__ method (around line 14)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before main logic:
   ```python
   if progress:
       progress.start_step("Evaluating arguments and rendering verdict", total=1, current=6)
   ```
5. Add complete_step() call before return
6. Add verbose logging for verdict generation (if VERBOSE):
   ```python
   if progress and progress.level == ProgressLevel.VERBOSE:
       print(f"Judge analyzing {len(messages)} messages...")
   ```

**Parallel?**: Yes (independent file)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Evaluating arguments and rendering verdict", total=1, current=6
- [ ] complete_step() called at end of method
- [ ] Verbose logging only shows in VERBOSE mode
- [ ] Works when _progress_manager missing from state (graceful)

---

### Subtask T022 – Add unit tests for instrumented nodes

**Purpose**: Ensure all instrumented nodes have test coverage for progress integration.

**Files**:
- `tests/unit/test_node_instrumentation_part2.py` (new file)

**Steps**:
1. Create test file with pytest and mock imports
2. Create fixture for ProgressManager mock
3. Test debate_moderator_node.py with progress:
   ```python
   async def test_moderator_with_progress_manager():
       mock_progress = MockProgressManager()
       state = {
           "_progress_manager": mock_progress,
           "messages": [],
           "stage": "rebuttal"
       }
       node = DebateModeratorNode(llm_config={})
       result = await node(state)
       assert mock_progress.start_step_calls == ["Moderating debate flow"]
       assert mock_progress.complete_step_calls == 1
   ```
4. Test fact_check_node.py with progress
5. Test judge_node.py with progress
6. Test graceful degradation when progress_manager missing:
   ```python
   async def test_node_without_progress_manager():
       state = {"messages": [], "stage": "final_argument"}
       node = JudgeNode(llm_config={})
       result = await node(state)
       assert "messages" in result
       assert result["speaker"] == "judge"
   ```

**Parallel?**: Yes (independent test file)

**Validation**:
- [ ] All three nodes tested with progress manager
- [ ] start_step() verified for each node
- [ ] complete_step() verified for each node
- [ ] Missing progress_manager doesn't cause crashes
- [ ] All tests pass with pytest

---

## Test Strategy

**Note**: Tests are explicitly required by the feature specification.

### Unit Tests
- **Location**: `tests/unit/test_node_instrumentation_part2.py` (create new file)
- **Purpose**: Verify remaining nodes (moderator, fact checker, judge) work with progress manager
- **Test Cases**:
  - test_moderator_with_progress_manager: Verify progress hooks called
  - test_fact_checker_with_progress_manager: Verify progress hooks called
  - test_judge_with_progress_manager: Verify progress hooks called
  - test_node_without_progress_manager: Verify backward compatibility
  - test_graceful_degradation: Verify no crashes when progress missing

### Integration Tests
- **Location**: `tests/integration/test_full_node_progress.py` (create new file)
- **Purpose**: Verify all six nodes work together with progress in workflow
- **Test Cases**:
  - test_full_workflow_with_verbose: Run workflow with --verbose, verify detailed output
  - test_full_workflow_with_quiet: Run workflow with --quiet, verify minimal output
  - test_full_workflow_default: Run workflow without flags, verify step progress
  - test_step_sequence: Verify step numbers 1-6 appear in order
  - test_progress_persistence: Verify progress state doesn't pollute across nodes

**Running Tests**:
```bash
# Unit tests for this WP
pytest tests/unit/test_node_instrumentation_part2.py -v

# Full integration tests
pytest tests/integration/test_full_node_progress.py -v
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|--------|-----------|
| Inconsistent progress patterns | Nodes display progress differently | Follow WP04 pattern exactly, use same state.get() approach |
| Step numbering conflicts | Wrong step numbers used | Verify step numbers (4-6) don't conflict with WP04 |
| LLM API timing variability | Progress bars update irregularly | Use tqdm with auto-refresh, don't manually control updates |
| Verbose mode overload | Too much output in VERBOSE | Keep verbose output minimal, only for key operations |
| Import path issues | src.progress not found during node execution | Test import path, verify PYTHONPATH includes project root |

---

## Review Guidance

**Key Acceptance Checkpoints for `/spec-kitty.review`**:
- [ ] All three nodes (debate_moderator, fact_check, judge) instrumented with progress
- [ ] start_step() calls match step names and positions (4-6)
- [ ] complete_step() called in all instrumented nodes
- [ ] Verbose logging only shows in VERBOSE mode
- [ ] Graceful degradation (no crashes) when progress_manager missing
- [ ] Unit tests cover all three nodes
- [ ] Integration test verifies full workflow with all nodes
- [ ] No existing functionality broken by modifications

**Integration Context**:
- Next WP (WP06) will add end-to-end testing and documentation polish
- Ensure all six instrumented nodes follow same pattern as WP04
- Verify step numbers form complete sequence: 1-6 (topic, pro, con, moderator, fact check, judge)
- Confirm progress tracking works across entire workflow in all verbosity modes

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
