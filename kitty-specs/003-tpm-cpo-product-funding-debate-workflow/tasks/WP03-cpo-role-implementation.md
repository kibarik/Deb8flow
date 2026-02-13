---
work_package_id: "WP03"
subtasks:
  - "T005"
  - "T010"
  - "T011"
  - "T012"
title: "CPO Role Implementation"
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

# Work Package Prompt: WP03 – CPO Role Implementation

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- [ ] `generate_rebuttal()` produces rigorous rebuttal challenging TPM's claims
- [ ] `generate_final_argument()` produces compelling final argument summarizing skeptical position
- [ ] Node uses LLM configuration from `requesty_llm_config_map`

## Context & Constraints

**Implementation Command**:
```bash
spec-kitty implement WP03 --base WP01
```

**Reference Documents**:
- [Data Model](../data-model.md) - State entity definitions
- [CPO Node Contract](../contracts/cpo_node.py.md) - CPO node interface
- [CPO Prompts Contract](../contracts/cpo_prompts.py.md) - Prompt template specification
- [Quickstart](../quickstart.md) - Usage examples
- [BaseComponent](../../../../nodes/base_component.py) - Base class to inherit from
- [Existing con_debater_node.py](../../../../nodes/con_debater_node.py) - Reference for similar implementation

**Architectural Decisions**:
- Follow same pattern as `ConDebaterNode` from existing codebase
- Use separate prompts file for CPO role (not combined with TPM)
- Pass state to methods to access debate_topic, prd_input, messages

**Constraints**:
- Must inherit from `BaseComponent` (not direct implementation)
- Must use LLM from `requesty_llm_config_map["deepseek-chat"]`
- State uses `TpmCpoDebateState` from WP01

## Subtasks & Detailed Guidance

### Subtask T005 – Create CPO Prompts File

**Purpose**: Define prompt templates for CPO's rebuttal and final argument.

**Steps**:
1. Create `prompts/cpo_prompts.py`
2. Define `REBUTTAL_PROMPT_TEMPLATE`:
   - Role: Chief Product Officer evaluating a project funding proposal
   - Context: PRD input, project topic, TPM's opening
   - Focus: Incomplete market analysis, resource allocation impact, team focus risks, unrealistic assumptions
   - Placeholder: `{prd_input}`, `{debate_topic}`, `{tpm_opening}`
3. Define `FINAL_ARGUMENT_PROMPT_TEMPLATE`:
   - Role: CPO delivering final argument
   - Context: PRD input, project topic, full debate history
   - Focus: Summarize skeptical position, key unresolved concerns, risk vs benefit assessment, funding recommendation
   - Placeholder: `{prd_input}`, `{debate_topic}`, `{debate_history}`
4. Encourage rigorous questioning (skeptic but constructive)

**Files**: `prompts/cpo_prompts.py` (create, ~70 lines)

**Parallel?**: Can proceed alongside T004 (TPM prompts)

**Notes**:
- CPO prompts maintain skeptical tone throughout
- Rebuttal should identify specific gaps (not generic skepticism)
- Final argument should request clear funding decision (Approve/Deny)

### Subtask T010 – Create CPO Node Class

**Purpose**: Create the CPO skeptic node class inheriting from BaseComponent.

**Steps**:
1. Create `nodes/cpo_node.py`
2. Import `BaseComponent` from `.base_component`
3. Define `CPONode(BaseComponent)` class:
   ```python
   class CPONode(BaseComponent):
       def __init__(self, llm_config: dict):
           super().__init__(llm_config)
   ```
4. Import prompts: `from prompts.cpo_prompts import REBUTTAL_PROMPT_TEMPLATE, FINAL_ARGUMENT_PROMPT_TEMPLATE`

**Files**: `nodes/cpo_node.py` (create, ~20 lines)

**Parallel?**: Depends on T005 (prompts needed)

**Notes**:
- Follow exact pattern of `ConDebaterNode` from existing codebase
- LLM config passed to base class for client initialization

### Subtask T011 – Implement generate_rebuttal() Method

**Purpose**: Generate CPO's rebuttal challenging TPM's opening statement.

**Steps**:
1. In `CPONode` class, add `generate_rebuttal(self, state: TpmCpoDebateState) -> str` method
2. Extract TPM's opening from state["messages"] (find most recent "tpm" message with stage="opening")
3. Format prompt with state fields and TPM's opening:
   ```python
   prompt = REBUTTAL_PROMPT_TEMPLATE.format(
       prd_input=state["prd_input"],
       debate_topic=state["debate_topic"],
       tpm_opening=tpm_message["content"]
   )
   ```
4. Call LLM: `response = self.llm_client.generate(prompt)`
5. Extract content from response (remove any wrapper/markdown)
6. Return content as string

**Files**: `nodes/cpo_node.py` (modify, add ~35 lines)

**Parallel?**: Depends on T010

**Notes**:
- State uses `TpmCpoDebateState` from WP01 (type-safe access)
- Handle edge cases: empty state, missing TPM opening
- Response should be rigorous but identify specific concerns (not blanket rejection)

### Subtask T012 – Implement generate_final_argument() Method

**Purpose**: Generate CPO's final argument summarizing skeptical position.

**Steps**:
1. In `CPONode` class, add `generate_final_argument(self, state: TpmCpoDebateState) -> str` method
2. Build debate history from state["messages"] (format as transcript)
3. Format prompt with state fields and debate history:
   ```python
   prompt = FINAL_ARGUMENT_PROMPT_TEMPLATE.format(
       prd_input=state["prd_input"],
       debate_topic=state["debate_topic"],
       debate_history=debate_transcript
   )
   ```
4. Call LLM and extract content
5. Return content as string

**Files**: `nodes/cpo_node.py` (modify, add ~35 lines)

**Parallel?**: Depends on T010

**Notes**:
- Debate history should include all messages to date (TPM and CPO)
- Format as readable transcript (speaker labels, stage progression)
- Final argument should conclude with clear recommendation

## Test Strategy

**Manual Testing** (tests not auto-generated):
1. Create test PRD input and mock TPM opening
2. Mock state with prd_input, debate_topic, and TPM opening in messages
3. Call `generate_rebuttal()` and verify:
   - Returns non-empty string
   - Content challenges TPM's specific claims
   - Content identifies resource/completeness concerns
   - Tone is skeptical but constructive
4. Add full debate history to state
5. Call `generate_final_argument()` and verify:
   - Returns non-empty string
   - Content summarizes key concerns
   - Content provides clear recommendation (Approve/Deny)
   - References debate history appropriately

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CPO too skeptical (blocking all projects) | Medium | Prompts encourage constructive skepticism, focus on specific concerns |
| LLM hallucinates debate history | Low | Format debate transcript clearly, limit length |
| State type mismatches | Medium | Use `TpmCpoDebateState` from WP01 explicitly |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] `cpo_prompts.py` has both REBUTTAL and FINAL_ARGUMENT templates
- [ ] `CPONode` inherits from `BaseComponent`
- [ ] `generate_rebuttal()` accepts state, returns string
- [ ] `generate_final_argument()` accepts state, returns string
- [ ] Both methods format prompts with required state fields
- [ ] TPM opening correctly extracted from messages list
- [ ] Debate history formatted as readable transcript
- [ ] LLM client called via base class pattern

**Review Context**:
- Compare with `ConDebaterNode` implementation for consistency
- Verify prompt templates include all required placeholders
- Check state access uses correct field names from `TpmCpoDebateState`

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP03 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
