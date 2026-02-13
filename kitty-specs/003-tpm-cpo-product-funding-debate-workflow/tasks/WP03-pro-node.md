---
work_package_id: "WP03"
title: "PRO Debater Node Custom Prompt Injection"
phase: "Phase 2 - Implementation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
dependencies:
- WP01
- WP02
subtasks:
- T011
- T012
- T013
- T014
- T015
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP03 – PRO Debater Node Custom Prompt Injection

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Modify `pro_debater_node.py` to accept `pro_custom_prompt` from state and inject it into the base system prompt, enabling role-based debates while preserving existing functionality.

**Success Criteria:**
- `pro_custom_prompt` extracted from state in `__call__` method
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
- **MUST HANDLE NONE GRACEFULLY** - Work normally when `pro_custom_prompt` is None
- **MUST PRESERVE EXISTING CHAINS** - Only enhance prompt, don't change chain structure
- **MUST LOG CUSTOM PROMPT USAGE** - Inform users when custom prompts are active
- **MUST WORK WITH ALL STAGES** - Opening, counter, retry, document-aware variants

**Technical Context:**
- `ProDebaterNode` in `nodes/pro_debater_node.py` inherits from `BaseComponent`
- Uses lazy initialization pattern (`_ensure_chains_initialized()`)
- Base prompts imported from `prompts/pro_debater_prompts.py`
- Multiple chains: `opening_chain`, `counter_chain`, retry variants, document-aware variants
- State is passed via `__call__(self, state: DebateState)`
- `BaseComponent` provides `create_chain(system_template, human_template)` method

**Prompt Injection Strategy:**
```python
# Prepend custom prompt to base system prompt:
enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
```

## Subtasks & Detailed Guidance

### Subtask T011 – Extract pro_custom_prompt from State

**Purpose:** Retrieve the `pro_custom_prompt` field from the incoming state dictionary.

**Files:**
- `nodes/pro_debater_node.py` (modify)

**Steps:**
1. Open `nodes/pro_debater_node.py`
2. Locate the `__call__` method
3. Extract `pro_custom_prompt` from state using `.get()` method
4. Store as instance variable or pass to chain initialization method

**Implementation Pattern:**
```python
# In __call__ method, after existing state extraction:
def __call__(self, state: DebateState) -> Dict[str, Any]:
    super().__call__(state)
    self._ensure_chains_initialized()

    # NEW: Extract custom prompt from state
    pro_custom_prompt = state.get("pro_custom_prompt")

    # ... rest of existing logic
```

**Validation:**
- `pro_custom_prompt` extracted from state
- Uses `.get()` method (returns None if key missing)
- Value is available for chain creation

**Parallel?** No - Must complete before T012-T013

**Notes:**
- Use `.get()` not direct access to handle missing key gracefully
- State may not have `pro_custom_prompt` field (backward compatibility)

---

### Subtask T012 – Create _create_chain_with_custom_prompt Method

**Purpose:** Create a helper method that injects custom prompt into base system prompt.

**Files:**
- `nodes/pro_debater_node.py` (modify)

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
        self.log_debate_event("Using custom PRO prompt", prefix="PRO")
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

**Parallel?** No - Must complete before T013

**Notes:**
- Use double newline `\n\n` to separate custom from base prompt
- Log message helps users know custom prompt is active
- Keep base system prompt intact for default behavior

---

### Subtask T013 – Update _ensure_chains_initialized with Custom Prompt

**Purpose:** Modify lazy initialization to use custom prompts when creating chains.

**Files:**
- `nodes/pro_debater_node.py` (modify)

**Steps:**
1. Locate the `_ensure_chains_initialized()` method
2. Extract `pro_custom_prompt` from state (already done in T011)
3. Store `pro_custom_prompt` as instance variable
4. Replace all `self.create_chain()` calls with `self._create_chain_with_custom_prompt()`
5. Pass `pro_custom_prompt` to all chain creations
6. Update all chain variants: `opening_chain`, `opening_retry_chain`, `counter_chain`, `counter_retry_chain`, `document_opening_chain`, `document_counter_chain`

**Implementation Pattern:**
```python
def _ensure_chains_initialized(self):
    """Initialize chains lazily with custom prompt support."""
    if not self.chains_initialized:
        # Get custom prompt from state (extracted in __call__)
        pro_custom_prompt = getattr(self, "_pro_custom_prompt", None)

        # Base system prompt
        base_system_prompt = SYSTEM_PROMPT

        # Create all chains with custom prompt injection
        self.opening_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, OPENING_HUMAN_PROMPT
        )
        self.opening_retry_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, OPENING_RETRY_HUMAN_PROMPT
        )
        self.counter_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, COUNTER_HUMAN_PROMPT
        )
        self.counter_retry_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, COUNTER_RETRY_HUMAN_PROMPT
        )
        # Document-aware chains
        self.document_opening_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, DOCUMENT_OPENING_HUMAN_PROMPT
        )
        self.document_counter_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, DOCUMENT_COUNTER_HUMAN_PROMPT
        )

        self.chains_initialized = True
```

**Update __call__ to store custom prompt:**
```python
def __call__(self, state: DebateState) -> Dict[str, Any]:
    super().__call__(state)

    # NEW: Extract and store custom prompt
    pro_custom_prompt = state.get("pro_custom_prompt")
    self._pro_custom_prompt = pro_custom_prompt

    self._ensure_chains_initialized()

    # ... rest of existing logic
```

**Validation:**
- All 6 chains use `_create_chain_with_custom_prompt()` method
- `pro_custom_prompt` stored as instance variable
- Lazy initialization pattern preserved
- Existing chain logic unchanged (only prompt creation modified)

**Parallel?** No - Depends on T011-T012

**Notes:**
- Use `getattr(self, "_pro_custom_prompt", None)` for safe access
- Re-create chains if custom prompt changes (advanced - not required for MVP)
- All chain variants must be updated (opening, counter, retry, document-aware)

---

### Subtask T014 – Add Logging for Custom Prompt Usage

**Purpose:** Inform users via logs when a custom prompt is being used.

**Files:**
- `nodes/pro_debater_node.py` (modify)

**Steps:**
1. Review logging statements in `_create_chain_with_custom_prompt()`
2. Ensure custom prompt usage is logged when provided
3. Use `self.log_debate_event()` for consistent formatting
4. Include "PRO" prefix for clarity
5. Log should be visible in standard debate output

**Implementation Pattern:**
```python
# In _create_chain_with_custom_prompt(), when custom_prompt is provided:
if custom_prompt:
    enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
    # Log to inform user
    self.log_debate_event("Using custom PRO prompt", prefix="PRO")
```

**Alternative: More detailed logging**
```python
if custom_prompt:
    enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
    # Log with preview of custom prompt (first 50 chars)
    preview = custom_prompt[:50] + "..." if len(custom_prompt) > 50 else custom_prompt
    self.log_debate_event(f"Using custom PRO prompt: {preview}", prefix="PRO")
```

**Validation:**
- Custom prompt usage logged when provided
- Uses `self.log_debate_event()` method
- Log includes "PRO" prefix
- Log visible in standard debate output
- No log when custom_prompt is None

**Parallel?** Yes - Can be done alongside T013

**Notes:**
- Keep log message concise but informative
- Consider showing preview of custom prompt content
- Use consistent format with CON node

---

### Subtask T015 – Handle None custom_prompt Value

**Purpose:** Ensure node works normally when `pro_custom_prompt` is None or missing.

**Files:**
- `nodes/pro_debater_node.py` (modify)

**Steps:**
1. Review `_create_chain_with_custom_prompt()` method
2. Verify `if custom_prompt:` check handles None correctly
3. Test that base system prompt is used when custom_prompt is None
4. Ensure no errors when state doesn't have `pro_custom_prompt` field

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
    None, SYSTEM_PROMPT, OPENING_HUMAN_PROMPT
)
# Should use base SYSTEM_PROMPT only

# Test 2: custom_prompt is empty string
chain = node._create_chain_with_custom_prompt(
    "", SYSTEM_PROMPT, OPENING_HUMAN_PROMPT
)
# Should use base SYSTEM_PROMPT only

# Test 3: custom_prompt has content
chain = node._create_chain_with_custom_prompt(
    "You are a TPM...", SYSTEM_PROMPT, OPENING_HUMAN_PROMPT
)
# Should use enhanced prompt with custom content
```

**Validation:**
- Method handles `None` value without errors
- Method handles empty string without errors
- Base system prompt used when custom_prompt is falsy
- No special case handling needed (Python's `if not` handles None/"")

**Parallel?** Yes - Can be done alongside T013-T014

**Notes:**
- Python's truthiness handles None and "" automatically
- No need for explicit `is None` check
- Ensure backward compatibility with existing state (no custom prompt field)

## Test Strategy

**Manual Testing:**
- Test debate with `--pro-prompt` flag (custom prompt should be used)
- Test debate without `--pro-prompt` flag (base prompt should be used)
- Check logs for custom prompt usage message
- Verify debate content reflects custom prompt role when provided

**No Automated Tests in This WP:**
- Full testing happens in WP05 (Testing)
- This WP focuses on implementation

**Definition of Done:**
- `_create_chain_with_custom_prompt()` method implemented
- `pro_custom_prompt` extracted from state in `__call__`
- All 6 chains use custom prompt when provided
- Base system prompt preserved when custom prompt is None
- Custom prompt usage logged when present
- Existing behavior unchanged when custom prompt not provided

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Custom prompt breaks base system prompt | Medium | Prepend (don't replace) base prompt; test with various prompt styles |
| Prompt injection makes debater ignore instructions | Low | Keep base system prompt structure intact; use double newline separator |
| Lazy initialization doesn't capture prompt changes | Low | Store custom prompt as instance variable; re-init if needed |
| Custom prompt too long causes token limits | Low | CLI enforces 5000 char limit; LLM handles remaining tokens |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] `_create_chain_with_custom_prompt()` method implemented
- [ ] Custom prompt prepended to base system prompt (not replaced)
- [ ] `pro_custom_prompt` extracted from state in `__call__`
- [ ] All 6 chains (opening, counter, retry, document variants) updated
- [ ] Base system prompt used when `pro_custom_prompt` is None
- [ ] Custom prompt usage logged when provided
- [ ] Existing tests pass (backward compatibility)

**Review Context:**
- Spec requirement FR2: Custom prompts must be injected into system prompts
- Spec requirement FR4: PRO node must accept and use `pro_custom_prompt`
- Spec requirement FR6: Must work normally when custom prompt is None
- Data model: `pro_custom_prompt: NotRequired[Optional[str]]`

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
