# Work Packages: Custom Prompt Debate Workflow

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Branch:** `feature-003-tpm-cpo-product-funding-debate-workflow`
**Generated:** 2026-02-14
**Mission:** software-dev

## Overview

This feature enables custom role-based debates through CLI prompt injection. Instead of creating separate node classes for each role combination (e.g., TPM vs CPO), the system accepts custom prompt files that are injected into existing PRO and CON debater system prompts. This approach allows flexible role customization without duplicating infrastructure.

**Key Design Decisions:**
- Extend existing `document_debate_cli.py` with `--pro-prompt` and `--con-prompt` flags
- Extend `DebateState` with `pro_custom_prompt` and `con_custom_prompt` fields
- Modify existing `pro_debater_node.py` and `con_debater_node.py` to inject custom prompts
- No new node classes, workflow files, or prompt files needed
- Reuse existing `document_debate_workflow.py` orchestration
- Custom prompts add role context on top of base system prompts

---

## Work Package: WP01 - State Extension

**Title:** Debate State Extension for Custom Prompts
**Work Package ID:** WP01
**Priority:** P0 (Foundation)
**Lane:** planned
**Dependencies:** None
**Parallel:** No

**Goal:** Extend `DebateState` TypedDict to support custom prompt content for PRO and CON debaters.

**Prompt:** `/tasks/WP01-state-extension.md`

### Summary

Add two new optional fields to `DebateState` to carry custom prompt content through the workflow:

1. `pro_custom_prompt: NotRequired[Optional[str]]` - Custom PRO debater prompt content
2. `con_custom_prompt: NotRequired[Optional[str]]` - Custom CON debater prompt content

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T001 | Add pro_custom_prompt field to DebateState | No | `debate_state.py` (modify) |
| T002 | Add con_custom_prompt field to DebateState | No | `debate_state.py` (modify) |
| T003 | Add type hints for optional custom prompts | No | `debate_state.py` (modify) |
| T004 | Verify backward compatibility with existing workflows | Yes | `debate_state.py` (modify), `tests/` (create) |

### Implementation Notes

**State Extension Pattern:**
```python
from typing import TypedDict, List, Dict, Literal, Optional
from typing_extensions import NotRequired

class DebateState(TypedDict):
    # ... existing fields ...
    pro_custom_prompt: NotRequired[Optional[str]]  # Custom PRO debater prompt content
    con_custom_prompt: NotRequired[Optional[str]]  # Custom CON debater prompt content
```

**Validation Requirements:**
- Fields must be optional (NotRequired)
- Must accept None values
- Must not break existing `debate_workflow.py`
- Must not break existing `document_debate_workflow.py`

### Dependencies

- None (foundation work package)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| State extension breaks existing workflows | Run all existing tests after changes; verify typed dict compatibility |
| Optional fields not properly handled | Use NotRequired wrapper; test with None values |

---

## Work Package: WP02 - CLI Flags & Validation

**Title:** CLI Custom Prompt Flags and File Validation
**Work Package ID:** WP02
**Priority:** P0 (Foundation)
**Lane:** planned
**Dependencies:** WP01
**Parallel:** No

**Goal:** Add `--pro-prompt` and `--con-prompt` CLI flags to `document_debate_cli.py` with file validation logic.

**Prompt:** `/tasks/WP02-cli-validation.md`

### Summary

Extend the document debate CLI to accept custom prompt file paths and validate them before workflow execution:

1. Add `--pro-prompt <path>` flag (optional)
2. Add `--con-prompt <path>` flag (optional)
3. Implement file validation function
4. Pass validated prompts to state initialization
5. Handle validation errors with clear messages

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T005 | Add --pro-prompt CLI argument | No | `document_debate_cli.py` (modify) |
| T006 | Add --con-prompt CLI argument | No | `document_debate_cli.py` (modify) |
| T007 | Implement validate_prompt_file function | No | `document_debate_cli.py` (modify) |
| T008 | Integrate validation into argument parsing | No | `document_debate_cli.py` (modify) |
| T009 | Pass validated prompts to initial_state | No | `document_debate_cli.py` (modify) |
| T010 | Add validation error handling and messages | Yes | `document_debate_cli.py` (modify) |

### Implementation Notes

**Validation Function Pattern:**
```python
def validate_prompt_file(file_path: str) -> tuple[bool, str]:
    """Validate custom prompt file exists, is non-empty, and within size limits.

    Args:
        file_path: Path to prompt file

    Returns:
        Tuple of (is_valid, content_or_error_message)
    """
    # Check file exists
    if not os.path.exists(file_path):
        return False, f"Prompt file not found: {file_path}"

    # Check file not empty
    if os.path.getsize(file_path) == 0:
        return False, f"Prompt file is empty: {file_path}"

    # Check file size <= 5000 chars
    with open(file_path, 'r') as f:
        content = f.read()
        if len(content) > 5000:
            return False, f"Prompt file too large (max 5000 characters): {file_path}"

    return True, content
```

**CLI Argument Pattern:**
```python
parser.add_argument(
    '--pro-prompt',
    type=str,
    help='Path to custom PRO debater prompt file'
)
parser.add_argument(
    '--con-prompt',
    type=str,
    help='Path to custom CON debater prompt file'
)
```

**State Initialization Pattern:**
```python
base_state = {
    "debate_topic": "",
    "positions": {},
    "messages": []
}

# Validate and add custom prompts if provided
if args.pro_prompt:
    is_valid, result = validate_prompt_file(args.pro_prompt)
    if not is_valid:
        logger.error(f"❌ {result}")
        sys.exit(1)
    base_state["pro_custom_prompt"] = result

if args.con_prompt:
    is_valid, result = validate_prompt_file(args.con_prompt)
    if not is_valid:
        logger.error(f"❌ {result}")
        sys.exit(1)
    base_state["con_custom_prompt"] = result
```

### Dependencies

- Depends on WP01 (state extension must exist before CLI can set fields)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| File I/O errors during validation | Validate files exist before workflow starts; catch exceptions |
| Empty files cause unexpected behavior | Check file size and content before processing |
| Large files impact performance | Enforce 5000 character limit; display clear error |

---

## Work Package: WP03 - PRO Node Modifications

**Title:** PRO Debater Node Custom Prompt Injection
**Work Package ID:** WP03
**Priority:** P1 (Feature)
**Lane:** planned
**Dependencies:** WP01, WP02
**Parallel:** Yes (can run alongside WP04)

**Goal:** Modify `pro_debater_node.py` to accept and inject `pro_custom_prompt` into system prompts.

**Prompt:** `/tasks/WP03-pro-node.md`

### Summary

Update the PRO debater node to use custom prompts when provided by the state:

1. Extract `pro_custom_prompt` from state
2. Inject custom prompt into base system prompt
3. Use enhanced prompt for chain creation
4. Handle None value (no custom prompt) gracefully
5. Log custom prompt usage when present

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T011 | Extract pro_custom_prompt from state | No | `nodes/pro_debater_node.py` (modify) |
| T012 | Create _create_chain_with_custom_prompt method | No | `nodes/pro_debater_node.py` (modify) |
| T013 | Update _ensure_chains_initialized with custom prompt | No | `nodes/pro_debater_node.py` (modify) |
| T014 | Add logging for custom prompt usage | Yes | `nodes/pro_debater_node.py` (modify) |
| T015 | Handle None custom_prompt value | Yes | `nodes/pro_debater_node.py` (modify) |

### Implementation Notes

**Chain Creation Pattern:**
```python
def _create_chain_with_custom_prompt(self, custom_prompt: Optional[str], system_prompt: str, human_prompt: str):
    """Create a chain with optional custom prompt injection.

    Args:
        custom_prompt: Optional custom prompt content to inject
        system_prompt: Base system prompt
        human_prompt: Human prompt template

    Returns:
        RunnableSequence chain for LLM invocation
    """
    if custom_prompt:
        # Inject custom prompt into base system prompt
        enhanced_system_prompt = f"{custom_prompt}\n\n{system_prompt}"
        self.log_debate_event("Using custom PRO prompt", prefix="PRO")
    else:
        enhanced_system_prompt = system_prompt

    return self.create_chain(enhanced_system_prompt, human_prompt)
```

**Lazy Initialization Pattern:**
```python
def _ensure_chains_initialized(self):
    """Initialize chains lazily with custom prompt support."""
    if not self.chains_initialized:
        pro_custom_prompt = self.state.get("pro_custom_prompt")

        # Base system prompt
        base_system_prompt = SYSTEM_PROMPT

        # Create all chains with custom prompt injection
        self.opening_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, OPENING_HUMAN_PROMPT
        )
        self.opening_retry_chain = self._create_chain_with_custom_prompt(
            pro_custom_prompt, base_system_prompt, OPENING_RETRY_HUMAN_PROMPT
        )
        # ... repeat for all chains
        self.chains_initialized = True
```

### Dependencies

- Depends on WP01 (state must have `pro_custom_prompt` field)
- Depends on WP02 (CLI must pass validated prompt to state)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Custom prompt breaks base system prompt | Test injection with various prompt styles; prepend to preserve base structure |
| Prompt injection makes debater ignore instructions | Keep base system prompt structure intact; use prepending strategy |
| Lazy initialization doesn't capture prompt changes | Initialize chains on each call or detect prompt changes |

---

## Work Package: WP04 - CON Node Modifications

**Title:** CON Debater Node Custom Prompt Injection
**Work Package ID:** WP04
**Priority:** P1 (Feature)
**Lane:** planned
**Dependencies:** WP01, WP02
**Parallel:** Yes (can run alongside WP03)

**Goal:** Modify `con_debater_node.py` to accept and inject `con_custom_prompt` into system prompts.

**Prompt:** `/tasks/WP04-con-node.md`

### Summary

Update the CON debater node to use custom prompts when provided by the state:

1. Extract `con_custom_prompt` from state
2. Inject custom prompt into base system prompt
3. Use enhanced prompt for chain creation
4. Handle None value (no custom prompt) gracefully
5. Log custom prompt usage when present

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T016 | Extract con_custom_prompt from state | No | `nodes/con_debater_node.py` (modify) |
| T017 | Create _create_chain_with_custom_prompt method | No | `nodes/con_debater_node.py` (modify) |
| T018 | Update __init__ with custom prompt support | No | `nodes/con_debater_node.py` (modify) |
| T019 | Add logging for custom prompt usage | Yes | `nodes/con_debater_node.py` (modify) |
| T020 | Handle None custom_prompt value | Yes | `nodes/con_debater_node.py` (modify) |

### Implementation Notes

**Chain Creation Pattern:**
```python
def _create_chain_with_custom_prompt(self, custom_prompt: Optional[str], system_prompt: str, human_prompt: str):
    """Create a chain with optional custom prompt injection.

    Args:
        custom_prompt: Optional custom prompt content to inject
        system_prompt: Base system prompt
        human_prompt: Human prompt template

    Returns:
        RunnableSequence chain for LLM invocation
    """
    if custom_prompt:
        # Inject custom prompt into base system prompt
        enhanced_system_prompt = f"{custom_prompt}\n\n{system_prompt}"
        self.log_debate_event("Using custom CON prompt", prefix="CON")
    else:
        enhanced_system_prompt = system_prompt

    return self.create_chain(enhanced_system_prompt, human_prompt)
```

**Initialization Pattern (CON node uses __init__ for chains):**
```python
def __init__(self, llm_config, temperature: float = 0.7):
    super().__init__(llm_config, temperature)
    # Note: CON node creates chains in __init__, not lazily
    # We'll need to update this pattern to support custom prompts
    # Store base chains and re-create with custom prompt when needed
    self.base_system_prompt = SYSTEM_PROMPT
    self.base_chains_initialized = False
```

**Updated __call__ Pattern:**
```python
def __call__(self, state: DebateState) -> Dict[str, Any]:
    super().__call__(state)

    # Extract custom prompt from state
    con_custom_prompt = state.get("con_custom_prompt")

    # Initialize or re-create chains with custom prompt
    if con_custom_prompt != getattr(self, "_last_custom_prompt", None):
        self._init_chains_with_custom_prompt(con_custom_prompt)
        self._last_custom_prompt = con_custom_prompt

    # ... rest of __call__ logic
```

### Dependencies

- Depends on WP01 (state must have `con_custom_prompt` field)
- Depends on WP02 (CLI must pass validated prompt to state)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| CON node uses __init__ pattern (not lazy) | Store base chains and re-create when custom prompt detected |
| Custom prompt breaks base system prompt | Test injection with various prompt styles; prepend to preserve base structure |
| Prompt injection makes debater ignore instructions | Keep base system prompt structure intact; use prepending strategy |

---

## Work Package: WP05 - Testing

**Title:** Backward Compatibility and New Functionality Tests
**Work Package ID:** WP05
**Priority:** P1 (Quality)
**Lane:** planned
**Dependencies:** WP01, WP02, WP03, WP04
**Parallel:** No

**Goal:** Ensure backward compatibility is maintained and new custom prompt functionality works correctly.

**Prompt:** `/tasks/WP05-testing.md`

### Summary

Create comprehensive tests to verify both backward compatibility and new custom prompt functionality:

1. Run existing test suite to verify backward compatibility
2. Test CLI with no custom prompts (default behavior)
3. Test CLI with PRO-only custom prompt
4. Test CLI with CON-only custom prompt
5. Test CLI with both custom prompts
6. Test file validation (missing, empty, too large)
7. Test state propagation through workflow
8. Test prompt injection in PRO node
9. Test prompt injection in CON node

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T021 | Run existing test suite for backward compatibility | No | `tests/` (existing) |
| T022 | Test CLI with no custom prompts (default) | Yes | `tests/test_document_debate_cli.py` (create) |
| T023 | Test CLI with PRO-only custom prompt | Yes | `tests/test_document_debate_cli.py` (create) |
| T024 | Test CLI with CON-only custom prompt | Yes | `tests/test_document_debate_cli.py` (create) |
| T025 | Test CLI with both custom prompts | Yes | `tests/test_document_debate_cli.py` (create) |
| T026 | Test file validation (missing file) | Yes | `tests/test_document_debate_cli.py` (create) |
| T027 | Test file validation (empty file) | Yes | `tests/test_document_debate_cli.py` (create) |
| T028 | Test file validation (file too large) | Yes | `tests/test_document_debate_cli.py` (create) |
| T029 | Test state propagation through workflow | Yes | `tests/test_workflow_state.py` (create) |
| T030 | Test prompt injection in PRO node | Yes | `tests/test_pro_debater_node.py` (create) |
| T031 | Test prompt injection in CON node | Yes | `tests/test_con_debater_node.py` (create) |

### Implementation Notes

**Test File Structure:**
```python
# tests/test_document_debate_cli.py
import pytest
from document_debate_cli import validate_prompt_file, main

def test_validate_prompt_file_missing():
    """Test validation fails for missing file."""
    is_valid, error = validate_prompt_file("nonexistent.txt")
    assert not is_valid
    assert "not found" in error.lower()

def test_validate_prompt_file_empty(tmp_path):
    """Test validation fails for empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    is_valid, error = validate_prompt_file(str(empty_file))
    assert not is_valid
    assert "empty" in error.lower()

def test_validate_prompt_file_too_large(tmp_path):
    """Test validation fails for file exceeding 5000 characters."""
    large_file = tmp_path / "large.txt"
    large_file.write_text("x" * 5001)
    is_valid, error = validate_prompt_file(str(large_file))
    assert not is_valid
    assert "too large" in error.lower()
```

**Backward Compatibility Test:**
```python
def test_backward_compatibility_default_behavior():
    """Test that existing tests still pass without custom prompts."""
    # Run existing debate workflow without custom prompts
    # Verify it works exactly as before
    result = run_debate(topic="Test topic")
    assert result["verdict"] is not None
    assert len(result["messages"]) > 0
```

### Dependencies

- Depends on WP01-WP04 (all implementation must be complete)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Backward compatibility broken | Run full existing test suite first; fix any regressions immediately |
| New tests don't cover edge cases | Include validation tests, single-side customization, both prompts |
| Mock tests don't reflect real behavior | Use integration tests where possible; test with real file I/O |

---

## Work Package: WP06 - Documentation Updates

**Title:** Documentation and Quickstart Updates
**Work Package ID:** WP06
**Priority:** P2 (Polish)
**Lane:** planned
**Dependencies:** WP01, WP02, WP03, WP04, WP05
**Parallel:** No

**Goal:** Update project documentation to reflect custom prompt functionality.

**Prompt:** `/tasks/WP06-documentation.md`

### Summary

Update documentation to guide users on using custom prompt functionality:

1. Update README.md with custom prompt examples
2. Update CLAUDE.md with new CLI flags
3. Verify quickstart.md examples are accurate
4. Add prompt file examples to documentation

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T032 | Update README.md with custom prompt usage | Yes | `README.md` (modify) |
| T033 | Update CLAUDE.md with new CLI flags | Yes | `CLAUDE.md` (modify) |
| T034 | Verify quickstart.md examples | Yes | `kitty-specs/003/quickstart.md` (verify) |
| T035 | Add prompt file examples | Yes | `docs/examples/` (create) |

### Implementation Notes

**README Section to Add:**
```markdown
### Custom Role-Based Debates

You can customize debater roles using prompt files:

\`\`\`bash
# Create role-specific prompt files
echo "You are a TPM advocating for funding..." > tpm_prompt.txt
echo "You are a CPO evaluating resources..." > cpo_prompt.txt

# Run debate with custom roles
python3 document_debate_cli.py \\
  --text "Build AI feature X" \\
  --pro-prompt tpm_prompt.txt \\
  --con-prompt cpo_prompt.txt
\`\`\`
```

### Dependencies

- Depends on WP01-WP05 (all implementation and testing complete)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Documentation examples don't match implementation | Test all examples before documenting; verify with actual CLI |
| Missing edge cases in docs | Include error handling examples; document validation rules |

---

## Dependency & Execution Summary

**Sequence:**
1. WP01 (State Extension) - Must complete first
2. WP02 (CLI & Validation) - Depends on WP01
3. WP03 (PRO Node) & WP04 (CON Node) - Can proceed in parallel after WP01-WP02
4. WP05 (Testing) - Depends on WP01-WP04
5. WP06 (Documentation) - Depends on WP01-WP05

**Parallelization:**
- WP03 and WP04 can proceed in parallel once WP01 and WP02 are complete
- All documentation tasks in WP06 can proceed in parallel

**MVP Scope:**
- WP01-WP04 constitute the minimal viable feature
- WP05 is required for quality assurance
- WP06 is polish work

---

## Subtask Index (Reference)

| Subtask ID | Summary | Work Package | Priority | Parallel? |
|------------|---------|--------------|----------|-----------|
| T001 | Add pro_custom_prompt field to DebateState | WP01 | P0 | No |
| T002 | Add con_custom_prompt field to DebateState | WP01 | P0 | No |
| T003 | Add type hints for optional custom prompts | WP01 | P0 | No |
| T004 | Verify backward compatibility with existing workflows | WP01 | P0 | Yes |
| T005 | Add --pro-prompt CLI argument | WP02 | P0 | No |
| T006 | Add --con-prompt CLI argument | WP02 | P0 | No |
| T007 | Implement validate_prompt_file function | WP02 | P0 | No |
| T008 | Integrate validation into argument parsing | WP02 | P0 | No |
| T009 | Pass validated prompts to initial_state | WP02 | P0 | No |
| T010 | Add validation error handling and messages | WP02 | P0 | Yes |
| T011 | Extract pro_custom_prompt from state | WP03 | P1 | No |
| T012 | Create _create_chain_with_custom_prompt method | WP03 | P1 | No |
| T013 | Update _ensure_chains_initialized with custom prompt | WP03 | P1 | No |
| T014 | Add logging for custom prompt usage | WP03 | P1 | Yes |
| T015 | Handle None custom_prompt value | WP03 | P1 | Yes |
| T016 | Extract con_custom_prompt from state | WP04 | P1 | No |
| T017 | Create _create_chain_with_custom_prompt method | WP04 | P1 | No |
| T018 | Update __init__ with custom prompt support | WP04 | P1 | No |
| T019 | Add logging for custom prompt usage | WP04 | P1 | Yes |
| T020 | Handle None custom_prompt value | WP04 | P1 | Yes |
| T021 | Run existing test suite for backward compatibility | WP05 | P1 | No |
| T022 | Test CLI with no custom prompts (default) | WP05 | P1 | Yes |
| T023 | Test CLI with PRO-only custom prompt | WP05 | P1 | Yes |
| T024 | Test CLI with CON-only custom prompt | WP05 | P1 | Yes |
| T025 | Test CLI with both custom prompts | WP05 | P1 | Yes |
| T026 | Test file validation (missing file) | WP05 | P1 | Yes |
| T027 | Test file validation (empty file) | WP05 | P1 | Yes |
| T028 | Test file validation (file too large) | WP05 | P1 | Yes |
| T029 | Test state propagation through workflow | WP05 | P1 | Yes |
| T030 | Test prompt injection in PRO node | WP05 | P1 | Yes |
| T031 | Test prompt injection in CON node | WP05 | P1 | Yes |
| T032 | Update README.md with custom prompt usage | WP06 | P2 | Yes |
| T033 | Update CLAUDE.md with new CLI flags | WP06 | P2 | Yes |
| T034 | Verify quickstart.md examples | WP06 | P2 | Yes |
| T035 | Add prompt file examples | WP06 | P2 | Yes |

---

## Success Criteria

**Functional Requirements (FR1-FR6):**
- [ ] CLI accepts `--pro-prompt` and `--con-prompt` flags independently (FR1)
- [ ] Custom prompts are injected into system prompts correctly (FR2)
- [ ] State carries `pro_custom_prompt` and `con_custom_prompt` through workflow (FR3)
- [ ] PRO node uses custom prompt when provided (FR4)
- [ ] CON node uses custom prompt when provided (FR4)
- [ ] File validation prevents invalid inputs with clear errors (FR5)
- [ ] Standard debates work exactly as before (FR6)

**Non-Functional Requirements:**
- [ ] No new node classes created (NFR1)
- [ ] No new workflow files created (NFR1)
- [ ] Error messages clearly indicate what went wrong (NFR2)
- [ ] Validation happens before workflow starts (NFR2)
- [ ] Custom prompt usage is logged when present (NFR3)
- [ ] All existing tests continue to pass (Backward Compatibility)

**Acceptance Tests:**
- [ ] TPM vs CPO debate demonstrates role-specific arguments
- [ ] Standard debate without custom prompts works as before
- [ ] PRO-only customization works correctly
- [ ] CON-only customization works correctly
- [ ] Invalid prompt file shows clear error message
- [ ] Empty prompt file shows clear error message
- [ ] Large prompt file (>5000 chars) shows clear error message
