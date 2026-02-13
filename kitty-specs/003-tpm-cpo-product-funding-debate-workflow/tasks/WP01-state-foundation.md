---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
title: "State Foundation"
phase: "Phase 1 - Design & Contracts"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2025-02-13T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP01 – State Foundation

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
Use language identifiers in code blocks: ```python, ```bash

---

## Objectives & Success Criteria

- Add TPM-CPO debate state structures to existing `debate_state.py` without breaking existing debate workflows
- Enable TPM and CPO nodes to use typed state with PRD input field
- Maintain backward compatibility with existing `DebateState` usage in features 001 and 002

**Success Criteria**:
- [ ] `TpmCpoDebateStage` Literal defined with all four stages
- [ ] `TpmCpoDebateMessage` TypedDict defined with speaker, content, validated, stage fields
- [ ] `TpmCpoDebateState` TypedDict defined with all required and optional fields
- [ ] Existing debate workflows (001, 002) continue to work without modification
- [ ] Type checking passes for new state structures

## Context & Constraints

**Reference Documents**:
- [Data Model](../data-model.md) - State entity definitions
- [State Contract](../contracts/tpm_cpo_debate_state.py.md) - Interface specification
- [Existing debate_state.py](../../../../debate_state.py) - Current implementation to extend

**Architectural Decisions**:
- Follow exact pattern of existing `DebateState` and `DebateMessage`
- Use `NotRequired` for optional fields to maintain flexibility
- Add new state classes alongside existing ones (don't modify `DebateState`)

**Constraints**:
- Cannot modify existing `DebateState` (would break features 001, 002)
- Must use typing_extensions for `NotRequired` (Python 3.11+)
- State field names must match contracts exactly

## Subtasks & Detailed Guidance

### Subtask T001 – Add TpmCpoDebateStage Literal

**Purpose**: Define the four debate stages as a type-safe Literal to prevent invalid stage values.

**Steps**:
1. Open `debate_state.py` in the repository root
2. Add import: `from typing_extensions import NotRequired` (if not present)
3. Define `TpmCpoDebateStage` Literal:
   ```python
   TpmCpoDebateStage = Literal["opening", "rebutal", "counter", "final_argument"]
   ```
4. Place below existing `DebateStage` definition for consistency

**Files**: `debate_state.py` (modify, ~5 lines added)

**Parallel?**: No (must complete before T002, T003)

**Notes**:
- Literal order matches debate flow sequence
- Must match contract exactly: "opening", "rebutal", "counter", "final_argument"

### Subtask T002 – Add TpmCpoDebateMessage TypedDict

**Purpose**: Define the message structure for individual TPM-CPO debate messages.

**Steps**:
1. In `debate_state.py`, add `TpmCpoDebateMessage` TypedDict below `TpmCpoDebateStage`
2. Define with these fields:
   ```python
   class TpmCpoDebateMessage(TypedDict):
       speaker: str  # "tpm" or "cpo"
       content: str  # The message produced
       validated: bool  # Whether the FactChecker verified this message
       stage: TpmCpoDebateStage  # The stage when this message was produced
   ```
3. Place below existing `DebateMessage` for consistency

**Files**: `debate_state.py` (modify, ~7 lines added)

**Parallel?**: No (depends on T001)

**Notes**:
- `speaker` field uses "tpm"/"cpo" (not "pro"/"con")
- `stage` field uses `TpmCpoDebateStage` from T001
- Type annotation enables validation of message structure

### Subtask T003 – Add TpmCpoDebateState TypedDict

**Purpose**: Define the complete state container for TPM-CPO funding debates.

**Steps**:
1. In `debate_state.py`, add `TpmCpoDebateState` TypedDict below `TpmCpoDebateMessage`
2. Define with these fields (use `NotRequired` for optional):
   ```python
   class TpmCpoDebateState(TypedDict):
       debate_topic: str
       positions: Dict[str, str]
       messages: List[TpmCpoDebateMessage]
       prd_input: str  # PRD text content
       stage: NotRequired[str]
       speaker: NotRequired[str]
       times_tpm_fact_checked: NotRequired[int]
       times_cpo_fact_checked: NotRequired[int]
       funding_decision: NotRequired[str]  # "approve" or "deny"
       verdict_reasoning: NotRequired[str]
   ```
3. Add imports if needed: `from typing import Dict, List`

**Files**: `debate_state.py` (modify, ~15 lines added)

**Parallel?**: No (depends on T001, T002)

**Notes**:
- `prd_input` is the key new field for PRD-based debates
- Optional fields use `NotRequired` for runtime flexibility
- `messages` uses `TpmCpoDebateMessage` from T002 for type safety
- Follows exact pattern of existing `DebateState`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing workflows | High | Add new state classes, don't modify existing `DebateState` |
| Type mismatch with contracts | Medium | Match field names and types exactly from contracts |
| Missing imports | Low | Verify `NotRequired` and `Literal` imports present |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] All three TypedDicts defined with correct field types
- [ ] `TpmCpoDebateStage` uses correct Literal values
- [ ] `TpmCpoDebateMessage.stage` references `TpmCpoDebateStage`
- [ ] `TpmCpoDebateState.messages` uses `List[TpmCpoDebateMessage]`
- [ ] Optional fields use `NotRequired` correctly
- [ ] Existing debate workflows still function

**Review Context**:
- Verify no modifications to `DebateState` or `DebateMessage`
- Check import statements include required types
- Confirm field names match contracts exactly

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP01 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### Optional Phase Subdirectories

For large features, organize prompts under `tasks/` to keep bundles grouped while maintaining lexical ordering.

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
