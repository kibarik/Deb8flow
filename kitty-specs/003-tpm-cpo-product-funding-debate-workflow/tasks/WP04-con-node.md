---
work_package_id: "WP04"
title: "CON Debater Node Custom Prompt Injection"
phase: "Phase 2 - Implementation"
lane: "done"
assignee: ""
agent: ""
shell_pid: ""
review_status: "approved"
reviewed_by: "ALeks ishmanov"
dependencies:
- WP01
- WP02
subtasks:
- T016
- T017
- T018
- T019
- T020
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP04 – CON Debater Node Custom Prompt Injection

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Modify `con_debater_node.py` to accept `con_custom_prompt` from state and inject it into the base system prompt, enabling role-based debates while preserving existing functionality.

**Success Criteria:**
- `con_custom_prompt` extracted from state in `__call__` method
- Custom prompt injected into base `SYSTEM_PROMPT` when provided
- Base system prompt structure preserved (custom prompt prepended)
- Chains use enhanced prompt when custom prompt provided
- Chains use base prompt when custom prompt is None
- Custom prompt usage logged when present
- Existing tests continue to pass

## Context & Constraints

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Data Model:** [data-model.md](../data-model.md)

**Key Constraints:**
- **DO NOT REPLACE BASE SYSTEM PROMPT** - Custom prompt must be prepended or appended
- **MUST HANDLE NONE GRACEFULLY** - Work normally when `con_custom_prompt` is None
- **MUST PRESERVE EXISTING CHAINS** - Only enhance prompt, don't change chain structure
- **MUST LOG CUSTOM PROMPT USAGE** - Inform users when custom prompts are active
- **MUST WORK WITH ALL STAGES** - Rebuttal, final argument, retry, document-aware variants
- **CON NODE USES __INIT__ PATTERN** - Chains created in `__init__`, not lazy initialization

**Technical Context:**
- `ConDebaterNode` in `nodes/con_debater_node.py` inherits from `BaseComponent`
- Uses `__init__` pattern (chains created at initialization, not lazy)
- Base prompts imported from `prompts/con_debater_prompts.py`
- Multiple chains: `rebuttal_chain`, `final_argument_chain`, retry variants, document-aware variants
- State is passed via `__call__(self, state: DebateState)`
- `BaseComponent` provides `create_chain(system_template, human_template)` method

**CON Node Pattern Difference:**
Unlike PRO node which uses lazy initialization, CON node creates chains in `__init__`:
```python
# Current CON node pattern:
def __init__(self, llm_config, temperature: float = 0.7):
    super().__init__(llm_config, temperature)
    self.rebuttal_chain = self.create_chain(SYSTEM_PROMPT, REBUTTAL_HUMAN_PROMPT)
    # ... other chains created here
```

This means we need a different strategy for custom prompt support:
1. Store base chains in `__init__`
2. Re-create chains with custom prompt in `__call__` if needed
3. Detect custom prompt changes and re-initialize

## Subtasks & Detailed Guidance

### Subtask T016 – Extract con_custom_prompt from State

**Purpose:** Retrieve the `con_custom_prompt` field from the incoming state dictionary.

**Files:**
- `nodes/con_debater_node.py` (modify)

**Steps:**
1. Open `nodes/con_debater_node.py`
2. Locate the `__call__` method
3. Extract `con_custom_prompt` from state using `.get()` method
4. Store as instance variable for later use

**Implementation Pattern:**
```python
# In __call__ method, after super().__call__(state):
def __call__(self, state: DebateState) -> Dict[str, Any]:
    super().__call__(state)

    # NEW: Extract custom prompt from state
    con_custom_prompt = state.get("con_custom_prompt")

    # ... rest of existing logic
```

**Validation:**
- `con_custom_prompt` extracted from state
- Uses `.get()` method (returns None if key missing)
- Value is available for chain creation

**Parallel?** No - Must complete before T017-T018

**Notes:**
- Use `.get()` not direct access to handle missing key gracefully
- State may not have `con_custom_prompt` field (backward compatibility)

---

### Subtask T017 – Create _create_chain_with_custom_prompt Method

**Purpose:** Create a helper method that injects custom prompt into base system prompt.

**Files:**
- `nodes/con_debater_node.py` (modify)

**Steps:**
1. Add new method `_create_chain_with_custom_prompt()` to the class
2. Accept parameters: `custom_prompt`, `base_system_prompt`, `human_prompt`
3. Check if `custom_prompt` is not None and not empty
4. If provided, prepend to base system prompt
5. Call `self.create_chain()` with enhanced system prompt
6. Return the created chain
7. Log custom prompt usage when provided

**Implementation Pattern:**
```python
def _create_chain_with_custom_prompt(
    self,
    custom_prompt: Optional[str],
    base_system_prompt: str,
    human_prompt: str
) -> RunnableSequence:
    """Create a chain with optional custom prompt injection.

    Args:
        custom_prompt: Optional custom prompt content to inject
        base_system_prompt: Base system prompt to enhance
        human_prompt: Human prompt template for the chain

    Returns:
        RunnableSequence chain for LLM invocation
    """
    if custom_prompt:
        # Prepend custom prompt to base system prompt
        enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
        self.log_debate_event("Using custom CON prompt", prefix="CON")
    else:
        enhanced_system_prompt = base_system_prompt

    return self.create_chain(enhanced_system_prompt, human_prompt)
```

**Validation:**
- Method accepts `Optional[str]` for custom prompt
- Method returns `RunnableSequence` (chain type)
- Custom prompt prepended to base system prompt (not replacing)
- Base system prompt preserved when custom prompt is None
- Custom prompt usage logged when provided
- Method uses `self.create_chain()` from BaseComponent

**Parallel?** No - Must complete before T018

**Notes:**
- Use same pattern as PRO node for consistency
- Use double newline `\n\n` to separate custom from base prompt
- Keep base system prompt intact for default behavior

---

### Subtask T018 – Update __init__ with Custom Prompt Support

**Purpose:** Modify `__init__` to support dynamic custom prompt injection.

**Files:**
- `nodes/con_debater_node.py` (modify)

**Steps:**
1. Locate the `__init__` method
2. Add instance variable to track last custom prompt used
3. Add instance variable to track if chains need re-creation
4. Create base chains in `__init__` (existing pattern preserved)
5. Add method to re-create chains with custom prompt if needed

**Implementation Pattern:**
```python
def __init__(self, llm_config, temperature: float = 0.7):
    super().__init__(llm_config, temperature)

    # NEW: Track custom prompt for dynamic chain creation
    self._last_custom_prompt = None
    self._base_system_prompt = SYSTEM_PROMPT

    # Create base chains (without custom prompt)
    # These will be re-created with custom prompt if needed in __call__
    self._init_base_chains()

def _init_base_chains(self):
    """Initialize base chains without custom prompt."""
    self.rebuttal_chain = self.create_chain(self._base_system_prompt, REBUTTAL_HUMAN_PROMPT)
    self.rebuttal_retry_chain = self.create_chain(self._base_system_prompt, REBUTTAL_RETRY_HUMAN_PROMPT)
    self.final_argument_chain = self.create_chain(self._base_system_prompt, FINAL_ARGUMENT_HUMAN_PROMPT)
    self.final_argument_retry_chain = self.create_chain(self._base_system_prompt, FINAL_ARGUMENT_RETRY_HUMAN_PROMPT)
    # Document-aware chains
    self.document_rebuttal_chain = self.create_chain(self._base_system_prompt, DOCUMENT_REBUTTAL_HUMAN_PROMPT)
    self.document_final_argument_chain = self.create_chain(self._base_system_prompt, DOCUMENT_FINAL_ARGUMENT_HUMAN_PROMPT)

def _ensure_chains_with_custom_prompt(self, custom_prompt: Optional[str]):
    """Re-create chains with custom prompt if it changed."""
    # Check if custom prompt changed
    if custom_prompt == self._last_custom_prompt:
        return  # No change, use existing chains

    # Custom prompt changed or first time with custom prompt
    self._last_custom_prompt = custom_prompt

    # Re-create all chains with custom prompt
    self.rebuttal_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, REBUTTAL_HUMAN_PROMPT
    )
    self.rebuttal_retry_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, REBUTTAL_RETRY_HUMAN_PROMPT
    )
    self.final_argument_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, FINAL_ARGUMENT_HUMAN_PROMPT
    )
    self.final_argument_retry_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, FINAL_ARGUMENT_RETRY_HUMAN_PROMPT
    )
    # Document-aware chains
    self.document_rebuttal_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, DOCUMENT_REBUTTAL_HUMAN_PROMPT
    )
    self.document_final_argument_chain = self._create_chain_with_custom_prompt(
        custom_prompt, self._base_system_prompt, DOCUMENT_FINAL_ARGUMENT_HUMAN_PROMPT
    )
```

**Update __call__ to use custom prompt:**
```python
def __call__(self, state: DebateState) -> Dict[str, Any]:
    super().__call__(state)

    # NEW: Extract and apply custom prompt
    con_custom_prompt = state.get("con_custom_prompt")
    self._ensure_chains_with_custom_prompt(con_custom_prompt)

    # ... rest of existing logic
```

**Validation:**
- `__init__` creates base chains without custom prompt
- `_ensure_chains_with_custom_prompt()` method implemented
- Chains re-created only when custom prompt changes
- All 6 chains support custom prompt injection
- Existing `__init__` pattern preserved (chains created at init)

**Parallel?** No - Depends on T016-T017

**Notes:**
- CON node uses different pattern than PRO node (no lazy initialization)
- Store `self._base_system_prompt` to avoid importing in each method
- Custom prompt change detection avoids unnecessary chain re-creation
- All chain variants must be updated (rebuttal, final, retry, document-aware)

---

### Subtask T019 – Add Logging for Custom Prompt Usage

**Purpose:** Inform users via logs when a custom prompt is being used.

**Files:**
- `nodes/con_debater_node.py` (modify)

**Steps:**
1. Review logging statements in `_create_chain_with_custom_prompt()`
2. Ensure custom prompt usage is logged when provided
3. Use `self.log_debate_event()` for consistent formatting
4. Include "CON" prefix for clarity
5. Log should be visible in standard debate output

**Implementation Pattern:**
```python
# In _create_chain_with_custom_prompt(), when custom_prompt is provided:
if custom_prompt:
    enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
    # Log to inform user
    self.log_debate_event("Using custom CON prompt", prefix="CON")
```

**Alternative: More detailed logging**
```python
if custom_prompt:
    enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
    # Log with preview of custom prompt (first 50 chars)
    preview = custom_prompt[:50] + "..." if len(custom_prompt) > 50 else custom_prompt
    self.log_debate_event(f"Using custom CON prompt: {preview}", prefix="CON")
```

**Validation:**
- Custom prompt usage logged when provided
- Uses `self.log_debate_event()` method
- Log includes "CON" prefix
- Log visible in standard debate output
- No log when custom_prompt is None

**Parallel?** Yes - Can be done alongside T018

**Notes:**
- Keep log message concise but informative
- Consider showing preview of custom prompt content
- Use consistent format with PRO node

---

### Subtask T020 – Handle None custom_prompt Value

**Purpose:** Ensure node works normally when `con_custom_prompt` is None or missing.

**Files:**
- `nodes/con_debater_node.py` (modify)

**Steps:**
1. Review `_create_chain_with_custom_prompt()` method
2. Verify `if custom_prompt:` check handles None correctly
3. Test that base system prompt is used when custom_prompt is None
4. Ensure no errors when state doesn't have `con_custom_prompt` field

**Implementation Pattern:**
```python
# In _create_chain_with_custom_prompt():
def _create_chain_with_custom_prompt(
    self,
    custom_prompt: Optional[str],
    base_system_prompt: str,
    human_prompt: str
) -> RunnableSequence:
    # Handle None or empty custom prompt
    if not custom_prompt:  # This handles None, "", etc.
        # Use base system prompt only
        return self.create_chain(base_system_prompt, human_prompt)

    # Custom prompt provided - inject it
    enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
    return self.create_chain(enhanced_system_prompt, human_prompt)
```

**Test Cases:**
```python
# Test 1: custom_prompt is None
chain = node._create_chain_with_custom_prompt(
    None, SYSTEM_PROMPT, REBUTTAL_HUMAN_PROMPT
)
# Should use base SYSTEM_PROMPT only

# Test 2: custom_prompt is empty string
chain = node._create_chain_with_custom_prompt(
    "", SYSTEM_PROMPT, REBUTTAL_HUMAN_PROMPT
)
# Should use base SYSTEM_PROMPT only

# Test 3: custom_prompt has content
chain = node._create_chain_with_custom_prompt(
    "You are a CPO...", SYSTEM_PROMPT, REBUTTAL_HUMAN_PROMPT
)
# Should use enhanced prompt with custom content
```

**Validation:**
- Method handles `None` value without errors
- Method handles empty string without errors
- Base system prompt used when custom_prompt is falsy
- No special case handling needed (Python's `if not` handles None/"")

**Parallel?** Yes - Can be done alongside T018-T019

**Notes:**
- Python's truthiness handles None and "" automatically
- No need for explicit `is None` check
- Ensure backward compatibility with existing state (no custom prompt field)

## Test Strategy

**Manual Testing:**
- Test debate with `--con-prompt` flag (custom prompt should be used)
- Test debate without `--con-prompt` flag (base prompt should be used)
- Check logs for custom prompt usage message
- Verify debate content reflects custom prompt role when provided

**No Automated Tests in This WP:**
- Full testing happens in WP05 (Testing)
- This WP focuses on implementation

**Definition of Done:**
- `_create_chain_with_custom_prompt()` method implemented
- `_ensure_chains_with_custom_prompt()` method implemented
- `con_custom_prompt` extracted from state in `__call__`
- All 6 chains (rebuttal, final, retry, document variants) support custom prompt
- Base system prompt used when `con_custom_prompt` is None
- Custom prompt usage logged when provided
- Existing behavior unchanged when custom prompt not provided

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CON node uses __init__ pattern (different from PRO) | Medium | Store base chains; re-create with custom prompt when detected |
| Custom prompt breaks base system prompt | Medium | Prepend (don't replace) base prompt; test with various prompt styles |
| Prompt injection makes debater ignore instructions | Low | Keep base system prompt structure intact; use double newline separator |
| Custom prompt too long causes token limits | Low | CLI enforces 5000 char limit; LLM handles remaining tokens |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] `_create_chain_with_custom_prompt()` method implemented
- [ ] `_ensure_chains_with_custom_prompt()` method implemented (or equivalent)
- [ ] Custom prompt prepended to base system prompt (not replaced)
- [ ] `con_custom_prompt` extracted from state in `__call__`
- [ ] All 6 chains (rebuttal, final, retry, document variants) support custom prompt
- [ ] Base system prompt used when `con_custom_prompt` is None
- [ ] Custom prompt usage logged when provided
- [ ] Existing tests pass (backward compatibility)

**Review Context:**
- Spec requirement FR2: Custom prompts must be injected into system prompts
- Spec requirement FR4: CON node must accept and use `con_custom_prompt`
- Spec requirement FR6: Must work normally when custom prompt is None
- Data model: `con_custom_prompt: NotRequired[Optional[str]]`

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
- 2026-02-13T23:57:52Z – unknown – lane=for_review – Ready for review: CON debater node with custom prompt injection
- 2026-02-14T00:00:44Z – unknown – lane=done – Implementation complete - approved via review
