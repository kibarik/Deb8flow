---
work_package_id: WP04
title: Node Instrumentation - Part 1
lane: planned
dependencies: []
subtasks:
- T015
- T016
- T017
- T018
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

# Work Package WP04 – Node Instrumentation - Part 1

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in frontmatter.
- **Report progress**: As you address each feedback item, update the **Activity Log** explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementer must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a Must-Do before completion.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: ```<div>```, ```<script>```

Use language identifiers in code blocks: ```python```, ```bash```

---

## Objectives & Success Criteria

- **Instrument document_topic_node.py** – Add progress hooks for step "Generating debate topic"
- **Instrument pro_debater_node.py** – Add progress hooks for step "Generating pro arguments"
- **Instrument con_debater_node.py** – Add progress hooks for step "Generating con arguments"
- **Add verbose LLM output** – Display LLM API call details in VERBOSE mode
- **Zero regressions** – All existing functionality preserved

## Context & Constraints

### Prerequisite Work
- WP03: Workflow Integration (state injection via _progress_manager key complete)
- WP01: Foundation - Progress Module (ProgressManager, CLIOutput classes exist)

### Related Documents
- Spec: `kitty-specs/005-cli-progress-indicators/spec.md` – FR-001 Step Progress Display, FR-002 Verbose Mode
- Plan: `kitty-specs/005-cli-progress-indicators/plan.md` – Node instrumentation strategy
- Data Model: `kitty-specs/005-cli-progress-indicators/data-model.md` – ProgressManager interface
- Existing Code: `nodes/document_topic_node.py`, `nodes/pro_debater_node.py`, `nodes/con_debater_node.py`

### Architectural Decisions
- **Progress extraction**: Use state.get("_progress_manager") pattern (accessor returns None)
- **Step positioning**: Hardcode step numbers (1=topic, 2=pro, 3=con) based on workflow order
- **Optional integration**: Progress only added if _progress_manager exists in state (graceful degradation)
- **Verbose flag**: Check progress.level == ProgressLevel.VERBOSE before adding verbose logging

---

## Subtasks & Detailed Guidance

### Subtask T015 – Instrument document_topic_node.py with progress hooks

**Purpose**: Add progress tracking to the document topic generation node.

**Files**:
- `nodes/document_topic_node.py` (modify existing)

**Steps**:
1. Add import at top of file (after existing imports):
   ```python
   from src.progress import ProgressManager
   ```
2. Locate __call__ method (starts around line 28)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before LLM invocation (after line 81, before self.execute_chain):
   ```python
   if progress:
       progress.start_step("Generating debate topic", total=1, current=1)
   ```
5. Add complete_step() call after LLM invocation (after line 85, after return):
   ```python
   if progress:
       progress.complete_step()
   ```
6. Add verbose logging for LLM API call (after line 82 if progress.level check):
   ```python
   if progress and progress.level == ProgressLevel.VERBOSE:
       # Get verbose output reference (self.output.verbose if available, or use print)
       print("Calling LLM API for topic generation...")
   ```

**Parallel?**: Yes (independent file modification)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Generating debate topic", total=1, current=1
- [ ] complete_step() called after LLM invocation
- [ ] Works when _progress_manager not in state (graceful)
- [ ] Verbose output only shown in VERBOSE mode

---

### Subtask T016 – Instrument pro_debater_node.py with progress hooks

**Purpose**: Add progress tracking to the pro debater node.

**Files**:
- `nodes/pro_debater_node.py` (modify existing)

**Steps**:
1. Add import at top of file (after existing imports):
   ```python
   from src.progress import ProgressManager, ProgressLevel
   ```
2. Locate __call__ method (starts around line 32)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before first LLM invocation (around line 44, after super().__call__):
   ```python
   if progress:
       progress.start_step("Generating pro arguments", total=1, current=2)
   ```
5. Add complete_step() call after LLM invocation (after line 87, before return):
   ```python
   if progress:
       progress.complete_step()
   ```
6. Add verbose logging for LLM API call (after line 45 if progress.level check):
   ```python
   if progress and progress.level == ProgressLevel.VERBOSE:
       print("Calling LLM API for pro argument generation...")
   ```

**Parallel?**: Yes (independent file modification)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Generating pro arguments", total=1, current=2
- [ ] complete_step() called after LLM invocation
- [ ] Works when _progress_manager not in state (graceful)
- [ ] Verbose output only shown in VERBOSE mode

---

### Subtask T017 – Instrument con_debater_node.py with progress hooks

**Purpose**: Add progress tracking to the con debater node.

**Files**:
- `nodes/con_debater_node.py` (modify existing)

**Steps**:
1. Add import at top of file (after existing imports):
   ```python
   from src.progress import ProgressManager, ProgressLevel
   ```
2. Locate __call__ method (starts around line 30)
3. Extract progress from state at method start:
   ```python
   progress = state.get("_progress_manager")
   ```
4. Add start_step() call before first LLM invocation (around line 43, after super().__call__):
   ```python
   if progress:
       progress.start_step("Generating con arguments", total=1, current=3)
   ```
5. Add complete_step() call after LLM invocation (after line 86, before return):
   ```python
   if progress:
       progress.complete_step()
   ```
6. Add verbose logging for LLM API call (after line 39 if progress.level check):
   ```python
   if progress and progress.level == ProgressLevel.VERBOSE:
       print("Calling LLM API for con argument generation...")
   ```

**Parallel?**: Yes (independent file modification)

**Validation**:
- [ ] Progress imported from src.progress
- [ ] start_step() called with "Generating con arguments", total=1, current=3
- [ ] complete_step() called after LLM invocation
- [ ] Works when _progress_manager not in state (graceful)
- [ ] Verbose output only shown in VERBOSE mode

---

### Subtask T018 – Add verbose output for LLM API calls

**Purpose**: Provide detailed internal operation visibility in VERBOSE mode.

**Files**:
- `nodes/document_topic_node.py` (modify existing - add verbose logging)
- `nodes/pro_debater_node.py` (modify existing - add verbose logging)
- `nodes/con_debater_node.py` (modify existing - add verbose logging)

**Steps**:
1. For each node, add verbose logging after progress.start_step() call:
   ```python
   # After start_step call, check if VERBOSE
   if progress and progress.level == ProgressLevel.VERBOSE:
       # Option 1: Use CLIOutput if available (from state["_progress_manager"])
       output = state.get("_cli_output")
       if output:
           output.verbose(f"Preparing LLM request for {debate_topic}")

       # Option 2: Direct print with context
       print(f"[VERBOSE] Generating argument for debate: {debate_topic}")
   ```
2. Ensure verbose messages provide context (which step, which operation)
3. Don't add verbose logging to nodes that don't have LLM calls

**Parallel?**: Yes (modifies same files as T015-T017)

**Validation**:
- [ ] Verbose messages only shown when --verbose flag used
- [ ] Messages provide context about operation (step name, API call)
- [ ] No verbose output in QUIET or DEFAULT modes
- [ ] Format is consistent across all three nodes

---

## Test Strategy

**Note**: Tests are explicitly required by the feature specification.

### Unit Tests
- **Location**: `tests/unit/test_node_instrumentation_part1.py` (create new file)
- **Purpose**: Verify progress hooks work correctly in isolation
- **Test Cases**:
  - test_document_topic_progress_hooks():
    Mock ProgressManager, verify start_step() and complete_step() called
  - test_pro_debater_progress_hooks():
    Mock ProgressManager, verify start_step() and complete_step() called
  - test_con_debater_progress_hooks():
    Mock ProgressManager, verify start_step() and complete_step() called
  - test_verbose_logging_only_verbose():
    Set ProgressLevel.VERBOSE, verify verbose messages printed
  - test_quiet_mode_no_verbose():
    Set ProgressLevel.QUIET, verify no verbose messages printed
  - test_progress_manager_optional():
    Run node without _progress_manager in state, verify no errors

### Integration Tests
- **Location**: `tests/integration/test_node_progress_part1.py` (create new file)
- **Purpose**: Verify nodes work correctly within workflow context
- **Test Cases**:
  - test_document_topic_with_workflow():
    Run DocumentTopicNode through workflow, verify progress shown
  - test_all_verbosity_levels():
    Run nodes with QUIET, DEFAULT, VERBOSE, verify correct output
  - test_workflow_propagation():
    Verify _progress_manager propagates from workflow to nodes

**Running Tests**:
```bash
# Unit tests
pytest tests/unit/test_node_instrumentation_part1.py -v

# Integration tests
pytest tests/integration/test_node_progress_part1.py -v
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|--------|-----------|
| Hardoded step numbers | Steps don't match actual workflow | Use step 1-6 sequence matching spec, allow flexible "current" parameter |
| Progress overhead | tqdm adds >5% slowdown | Profile before finalizing, optimize tqdm refresh rate |
| Import errors | src.progress not found during execution | Verify Python path includes project root, use relative imports |
| Regressions | Existing node behavior broken | Add comprehensive unit tests for each modified node |
| Windows encoding | tqdm unicode display issues | Test on Windows terminal, verify UTF-8 support |

---

## Review Guidance

**Key Acceptance Checkpoints for `/spec-kitty.review`**:
- [ ] All three nodes (document_topic, pro_debater, con_debater) have progress hooks
- [ ] start_step() called with appropriate step name and position
- [ ] complete_step() called after LLM operations
- [ ] Verbose logging only in VERBOSE mode
- [ ] No errors when _progress_manager missing from state (graceful)
- [ ] All existing node tests still pass (no regressions)
- [ ] Step numbers match workflow order: 1=topic, 2=pro, 3=con

**Integration Context**:
- Next WP (WP05) will instrument remaining nodes (moderator, fact_checker, judge)
- Ensure progress step numbers continue sequentially (4-6)
- Verify no duplicate step numbers or naming conflicts

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
