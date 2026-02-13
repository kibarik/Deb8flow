---
work_package_id: "WP02"
subtasks:
  - "T004"
  - "T007"
  - "T008"
  - "T009"
title: "TPM Role Implementation"
phase: "Phase 1 - Design & Contracts"
lane: "planned"
dependencies: ["WP01"]
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

# Work Package Prompt: WP02 – TPM Role Implementation

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

- Implement TPM (Technical Product Manager) advocate agent that argues for project funding
- Create role-specific prompts that guide the LLM to generate compelling opening statements and counter-arguments
- Enable TPM to reference PRD content, debate topic, and CPO's rebuttals

**Success Criteria**:
- [ ] `prompts/tpm_prompts.py` created with OPENING and COUNTER templates
- [ ] `nodes/tpm_node.py` created with TPMNode class inheriting from BaseComponent
- [ ] `generate_opening()` produces compelling opening statements for project launch
- [ ] `generate_counter()` produces persuasive counter-arguments addressing CPO's concerns
- [ ] Node uses LLM configuration from `requesty_llm_config_map`

## Context & Constraints

**Implementation Command**:
```bash
spec-kitty implement WP02 --base WP01
```

**Reference Documents**:
- [Data Model](../data-model.md) - State entity definitions
- [TPM Node Contract](../contracts/tpm_node.py.md) - TPM node interface
- [TPM Prompts Contract](../contracts/tpm_prompts.py.md) - Prompt template specification
- [Quickstart](../quickstart.md) - Usage examples
- [BaseComponent](../../../../nodes/base_component.py) - Base class to inherit from
- [Existing pro_debater_node.py](../../../../nodes/pro_debater_node.py) - Reference for similar implementation

**Architectural Decisions**:
- Follow same pattern as `ProDebaterNode` from existing codebase
- Use separate prompts file for TPM role (not combined with CPO)
- Pass state to methods to access debate_topic, prd_input, messages

**Constraints**:
- Must inherit from `BaseComponent` (not direct implementation)
- Must use LLM from `requesty_llm_config_map["deepseek-chat"]`
- State uses `TpmCpoDebateState` from WP01

## Subtasks & Detailed Guidance

### Subtask T004 – Create TPM Prompts File

**Purpose**: Define prompt templates for TPM's opening statement and counter-argument.

**Steps**:
1. Create `prompts/tpm_prompts.py`
2. Define `OPENING_PROMPT_TEMPLATE`:
   - Role: Technical Product Manager advocating for project funding
   - Context: PRD input, project topic
   - Focus: Market opportunity, technical feasibility, business value, why now
   - Placeholder: `{prd_input}`, `{debate_topic}`
3. Define `COUNTER_PROMPT_TEMPLATE`:
   - Role: TPM responding to CPO's rebuttal
   - Context: PRD input, project topic, CPO's rebuttal
   - Focus: Address resource concerns, completeness gaps, competitive risks
   - Placeholder: `{prd_input}`, `{debate_topic}`, `{cpo_rebuttal}`
4. Encourage verifiable claims (for fact-checking)

**Files**: `prompts/tpm_prompts.py` (create, ~60 lines)

**Parallel?**: Can proceed alongside T005 (CPO prompts)

**Notes**:
- Prompt quality significantly impacts debate quality
- TPM should be optimistic but grounded in evidence
- Reference existing `pro_debater_prompts.py` for tone and structure

### Subtask T007 – Create TPM Node Class

**Purpose**: Create the TPM advocate node class inheriting from BaseComponent.

**Steps**:
1. Create `nodes/tpm_node.py`
2. Import `BaseComponent` from `.base_component`
3. Define `TPMNode(BaseComponent)` class:
   ```python
   class TPMNode(BaseComponent):
       def __init__(self, llm_config: dict):
           super().__init__(llm_config)
   ```
4. Import prompts: `from prompts.tpm_prompts import OPENING_PROMPT_TEMPLATE, COUNTER_PROMPT_TEMPLATE`

**Files**: `nodes/tpm_node.py` (create, ~20 lines)

**Parallel?**: Depends on T004 (prompts needed)

**Notes**:
- Follow exact pattern of `ProDebaterNode` from existing codebase
- LLM config passed to base class for client initialization

### Subtask T008 – Implement generate_opening() Method

**Purpose**: Generate TPM's opening statement advocating for project launch.

**Steps**:
1. In `TPMNode` class, add `generate_opening(self, state: TpmCpoDebateState) -> str` method
2. Format prompt with state fields:
   ```python
   prompt = OPENING_PROMPT_TEMPLATE.format(
       prd_input=state["prd_input"],
       debate_topic=state["debate_topic"]
   )
   ```
3. Call LLM: `response = self.llm_client.generate(prompt)`
4. Extract content from response (remove any wrapper/markdown)
5. Return content as string

**Files**: `nodes/tpm_node.py` (modify, add ~30 lines)

**Parallel?**: Depends on T007

**Notes**:
- State uses `TpmCpoDebateState` from WP01 (type-safe access)
- Handle edge cases: empty state, missing debate_topic
- Response should be persuasive but factual (not over-promising)

### Subtask T009 – Implement generate_counter() Method

**Purpose**: Generate TPM's counter-argument addressing CPO's rebuttal.

**Steps**:
1. In `TPMNode` class, add `generate_counter(self, state: TpmCpoDebateState) -> str` method
2. Extract CPO's rebuttal from state["messages"] (find most recent "cpo" message)
3. Format prompt with state fields and CPO's rebuttal:
   ```python
   prompt = COUNTER_PROMPT_TEMPLATE.format(
       prd_input=state["prd_input"],
       debate_topic=state["debate_topic"],
       cpo_rebuttal=cpo_message["content"]
   )
   ```
4. Call LLM and extract content
5. Return content as string

**Files**: `nodes/tpm_node.py` (modify, add ~35 lines)

**Parallel?**: Depends on T007

**Notes**:
- Must find CPO's rebuttal in messages list (stage="rebuttal", speaker="cpo")
- Counter should directly address CPO's specific concerns
- Provide additional evidence to support original claims

## Test Strategy

**Manual Testing** (tests not auto-generated):
1. Create test PRD input (2-3 paragraphs)
2. Mock state with prd_input and debate_topic
3. Call `generate_opening()` and verify:
   - Returns non-empty string
   - Content references PRD project concept
   - Content advocates for launch (not skeptical)
4. Add mock CPO rebuttal to state["messages"]
5. Call `generate_counter()` and verify:
   - Returns non-empty string
   - Content addresses specific CPO concerns
   - Tone is constructive counter-argument

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM prompt quality issues | High | Reference existing prompts, test with multiple PRDs |
| State type mismatches | Medium | Use `TpmCpoDebateState` from WP01 explicitly |
| Empty LLM responses | Low | Add validation for non-empty content, retry if needed |
| Token limit exceeded | Low | Handle long PRDs by truncating in prompt |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] `tpm_prompts.py` has both OPENING and COUNTER templates
- [ ] `TPMNode` inherits from `BaseComponent`
- [ ] `generate_opening()` accepts state, returns string
- [ ] `generate_counter()` accepts state, returns string
- [ ] Both methods format prompts with required state fields
- [ ] CPO rebuttal correctly extracted from messages list
- [ ] LLM client called via base class pattern

**Review Context**:
- Compare with `ProDebaterNode` implementation for consistency
- Verify prompt templates include all required placeholders
- Check state access uses correct field names from `TpmCpoDebateState`

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP02 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
