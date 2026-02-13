---
work_package_id: "WP01"
title: "Debate State Extension for Custom Prompts"
phase: "Phase 2 - Implementation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
dependencies: []
subtasks:
- T001
- T002
- T003
- T004
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP01 – Debate State Extension for Custom Prompts

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Extend the `DebateState` TypedDict to support custom prompt content for PRO and CON debaters, enabling role-based debates without creating new node classes or workflow files.

**Success Criteria:**
- `pro_custom_prompt` field added to `DebateState` with proper typing
- `con_custom_prompt` field added to `DebateState` with proper typing
- Both fields are optional (NotRequired) and accept None values
- Existing `debate_workflow.py` continues to work without changes
- Existing `document_debate_workflow.py` continues to work without changes
- All existing tests continue to pass

## Context & Constraints

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Data Model:** [data-model.md](../data-model.md)

**Key Constraints:**
- **DO NOT create new node classes** - Extend existing nodes only
- **DO NOT create new workflow files** - Use existing `document_debate_workflow.py`
- **MUST preserve backward compatibility** - All existing tests must pass
- **MUST use NotRequired wrapper** - Fields must be truly optional
- **MUST accept None values** - Gracefully handle missing custom prompts

**Technical Context:**
- `DebateState` is a TypedDict defined in `debate_state.py` at project root
- Uses `typing_extensions.NotRequired` for optional fields
- Both `debate_workflow.py` and `document_debate_workflow.py` import this state
- State is passed through LangGraph's StateGraph mechanism

## Subtasks & Detailed Guidance

### Subtask T001 – Add pro_custom_prompt Field to DebateState

**Purpose:** Add the `pro_custom_prompt` field to carry custom PRO debater prompt content through the workflow.

**Files:**
- `debate_state.py` (modify)

**Steps:**
1. Open `debate_state.py` from project root
2. Locate the `DebateState` TypedDict class definition
3. Add `pro_custom_prompt: NotRequired[Optional[str]]` field after existing fields
4. Add docstring comment explaining the field's purpose

**Implementation Pattern:**
```python
from typing import TypedDict, List, Dict, Literal, Optional
from typing_extensions import NotRequired

class DebateState(TypedDict):
    debate_topic: str
    positions: Dict[str, str]
    messages: List[DebateMessage]
    # ... existing fields ...
    # NEW FIELD:
    # pro_custom_prompt: Optional custom prompt content for PRO debater.
    # When provided, this content is injected into the PRO system prompt
    # to enable role-based debates (e.g., TPM, CPO, Engineer, etc.)
    pro_custom_prompt: NotRequired[Optional[str]]
```

**Validation:**
- Field added with correct type annotation (`NotRequired[Optional[str]]`)
- Docstring explains field purpose clearly
- Field placed logically within TypedDict

**Parallel?** No - Must complete before other subtasks

**Notes:**
- Use `NotRequired` from `typing_extensions`
- Use `Optional` from `typing` module
- Field must be optional to allow None values

---

### Subtask T002 – Add con_custom_prompt Field to DebateState

**Purpose:** Add the `con_custom_prompt` field to carry custom CON debater prompt content through the workflow.

**Files:**
- `debate_state.py` (modify)

**Steps:**
1. Open `debate_state.py` from project root
2. Locate the `DebateState` TypedDict class definition
3. Add `con_custom_prompt: NotRequired[Optional[str]]` field after `pro_custom_prompt`
4. Add docstring comment explaining the field's purpose

**Implementation Pattern:**
```python
# In DebateState TypedDict, after pro_custom_prompt:
# con_custom_prompt: Optional custom prompt content for CON debater.
# When provided, this content is injected into the CON system prompt
# to enable role-based debates (e.g., CPO, Engineer, Skeptic, etc.)
con_custom_prompt: NotRequired[Optional[str]]
```

**Validation:**
- Field added with correct type annotation (`NotRequired[Optional[str]]`)
- Docstring explains field purpose clearly
- Field placed after `pro_custom_prompt` for logical grouping

**Parallel?** No - Depends on T001 for context

**Notes:**
- Keep both custom prompt fields together for readability
- Use same typing pattern as `pro_custom_prompt`

---

### Subtask T003 – Verify Type Imports

**Purpose:** Ensure all required type imports are present for the new fields.

**Files:**
- `debate_state.py` (modify)

**Steps:**
1. Review imports at the top of `debate_state.py`
2. Verify `Optional` is imported from `typing`
3. Verify `NotRequired` is imported from `typing_extensions`
4. Add missing imports if needed

**Implementation Pattern:**
```python
# At the top of debate_state.py:
from typing import TypedDict, List, Dict, Literal, Optional
from typing_extensions import NotRequired
```

**Validation:**
- `Optional` imported from `typing` module
- `NotRequired` imported from `typing_extensions` module
- No unused imports present
- Code compiles without import errors

**Parallel?** Yes - Can be done alongside T001-T002

**Notes:**
- `typing_extensions` is typically installed with Python 3.12+
- If import issues occur, verify `typing_extensions` package is available

---

### Subtask T004 – Verify Backward Compatibility

**Purpose:** Ensure the state extension doesn't break existing workflows.

**Files:**
- `debate_state.py` (verify)
- `workflow/debate_workflow.py` (import test)
- `workflow/document_debate_workflow.py` (import test)
- `tests/` (run existing tests)

**Steps:**
1. Import `DebateState` in Python REPL to verify no syntax errors
2. Try importing both workflow files to ensure they load the extended state
3. Run existing test suite to verify backward compatibility
4. Create a minimal test state with only required fields (no custom prompts)
5. Verify state with None values for custom prompts is valid

**Implementation Pattern:**
```python
# Test in Python REPL:
from debate_state import DebateState

# Test 1: State without custom prompts (existing behavior)
test_state: DebateState = {
    "debate_topic": "Test topic",
    "positions": {"pro": "For", "con": "Against"},
    "messages": []
}
# Should work without custom prompt fields

# Test 2: State with None custom prompts
test_state_with_none: DebateState = {
    "debate_topic": "Test topic",
    "positions": {"pro": "For", "con": "Against"},
    "messages": [],
    "pro_custom_prompt": None,
    "con_custom_prompt": None
}
# Should accept None values for optional fields

# Test 3: State with actual custom prompts
test_state_with_prompts: DebateState = {
    "debate_topic": "Test topic",
    "positions": {"pro": "For", "con": "Against"},
    "messages": [],
    "pro_custom_prompt": "You are a TPM...",
    "con_custom_prompt": "You are a CPO..."
}
# Should accept string values for custom prompts
```

**Validation:**
- Python imports `DebateState` without errors
- Both workflow files import and use the extended state
- Existing test suite passes without modification
- State without custom prompt fields works correctly
- State with None values works correctly
- State with string values works correctly

**Parallel?** Yes - Can be done after T001-T003

**Notes:**
- This is a verification task, not a code modification task
- If backward compatibility is broken, review T001-T003 for issues
- LangGraph's TypedDict handling should be compatible with NotRequired fields

## Test Strategy

**Verification Tests:**
- Import `DebateState` from Python REPL
- Create state instances with and without custom prompts
- Run `pytest` to verify existing tests still pass
- Verify both workflow files can import the extended state

**No New Tests Required:**
- This WP is about state extension only
- Full testing happens in WP05 (Testing)

**Definition of Done:**
- `pro_custom_prompt` field added to `DebateState`
- `con_custom_prompt` field added to `DebateState`
- Both fields use `NotRequired[Optional[str]]` typing
- Existing tests pass without modification
- Both workflow files can import and use the extended state

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| State extension breaks existing workflows | High | Run all existing tests after changes; verify both workflow files import correctly |
| NotRequired typing causes import errors | Medium | Verify `typing_extensions` package is installed; use correct import path |
| Optional fields not truly optional | Medium | Test state without custom prompt fields; verify None values work |
| LangGraph incompatible with NotRequired | Low | LangGraph supports TypedDict with NotRequired; verify with import test |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] Both `pro_custom_prompt` and `con_custom_prompt` fields present in `DebateState`
- [ ] Fields use correct typing: `NotRequired[Optional[str]]`
- [ ] Fields have clear docstrings explaining purpose
- [ ] Existing test suite passes without modification
- [ ] Both workflow files can import extended state
- [ ] No new node classes or workflow files created

**Review Context:**
- Spec requirement FR3: State must carry custom prompts through workflow
- Spec requirement FR6: Must maintain backward compatibility
- Data model: `DebateState` extension with `pro_custom_prompt` and `con_custom_prompt`

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry:**
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND** the new entry at the END (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format:**
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order):**
```
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created
- 2026-02-14T01:30:00Z – claude – lane=doing – Started implementation
- 2026-02-14T02:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-02-14T02:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS):**
- Adding new entry at the top (breaks chronological order)
- Using future timestamps (causes acceptance validation to fail)
- Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry as the current state. If entries are out of order, acceptance will fail even when the work is complete.

**Initial entry:**
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### Optional Phase Subdirectories

For large features, organize prompts under `tasks/` to keep bundles grouped while maintaining lexical ordering.
