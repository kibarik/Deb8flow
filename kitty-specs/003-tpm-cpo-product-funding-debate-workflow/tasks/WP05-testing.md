---
work_package_id: "WP05"
title: "Backward Compatibility and New Functionality Tests"
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
- WP03
- WP04
subtasks:
- T021
- T022
- T023
- T024
- T025
- T026
- T027
- T028
- T029
- T030
- T031
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP05 – Backward Compatibility and New Functionality Tests

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Create comprehensive tests to verify backward compatibility is maintained and new custom prompt functionality works correctly across all scenarios.

**Success Criteria:**
- All existing tests pass without modification (backward compatibility)
- Tests verify CLI behavior with no custom prompts (default)
- Tests verify CLI behavior with PRO-only custom prompt
- Tests verify CLI behavior with CON-only custom prompt
- Tests verify CLI behavior with both custom prompts
- Tests verify file validation (missing, empty, too large)
- Tests verify state propagation through workflow
- Tests verify PRO node prompt injection
- Tests verify CON node prompt injection
- All new tests pass

## Context & Constraints

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Quickstart:** [quickstart.md](../quickstart.md)

**Key Constraints:**
- **MUST NOT MODIFY EXISTING TESTS** - All existing tests must pass as-is
- **MUST TEST BACKWARD COMPATIBILITY** - Verify default behavior unchanged
- **MUST TEST ALL VALIDATION RULES** - Missing, empty, too large files
- **MUST TEST CUSTOM PROMPT SCENARIOS** - PRO-only, CON-only, both
- **USE PYTEST** - Project uses pytest for testing
- **USE FIXTURES WHERE APPROPRIATE** - Reusable test data

**Technical Context:**
- Tests are in `tests/` directory at project root
- Project uses pytest framework
- Mock LLM responses for predictable testing
- File I/O tests should use `tmp_path` fixture
- State propagation tests verify workflow execution

## Subtasks & Detailed Guidance

### Subtask T021 – Run Existing Test Suite

**Purpose:** Verify all existing tests still pass after state and node modifications.

**Files:**
- `tests/` (existing)
- Terminal (for running pytest)

**Steps:**
1. Open terminal to project root
2. Run pytest: `pytest`
3. Review results for any failures
4. If failures exist, determine if related to state extension
5. Fix any regressions in implementation WPs (WP01-WP04)

**Implementation Pattern:**
```bash
# Run all tests:
pytest

# Run with verbose output:
pytest -v

# Run specific test file:
pytest tests/test_debate_workflow.py

# Run with coverage (if coverage installed):
pytest --cov=.
```

**Validation:**
- All existing tests pass
- No test failures related to state extension
- No test failures related to node modifications
- Test suite completes without errors

**Parallel?** No - Must complete before other test tasks

**Notes:**
- If tests fail, fix regressions in WP01-WP04
- Do NOT modify existing tests to make them pass
- Focus on backward compatibility

---

### Subtask T022 – Test CLI with No Custom Prompts (Default)

**Purpose:** Verify CLI works exactly as before when custom prompt flags are not provided.

**Files:**
- `tests/test_document_debate_cli.py` (create)

**Steps:**
1. Create `tests/test_document_debate_cli.py`
2. Import `validate_prompt_file` function
3. Test CLI with `--text` only (no custom prompts)
4. Verify no custom prompts in state
5. Verify workflow runs normally

**Implementation Pattern:**
```python
# tests/test_document_debate_cli.py
import pytest
from unittest.mock import patch, MagicMock
from document_debate_cli import main, validate_prompt_file

def test_cli_without_custom_prompts(tmp_path, caplog):
    """Test CLI works normally without custom prompt flags."""
    # Create minimal state input
    text_input = "Test topic for debate"

    # Mock argparse and workflow
    with patch('sys.argv', ['document_debate_cli.py', '--text', text_input]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={
                "messages": [{"content": "Test verdict"}]
            })

            # Run CLI (should not raise errors)
            # Note: May need to handle sys.exit() in tests

            # Verify workflow was called with state without custom prompts
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']

            assert "pro_custom_prompt" not in initial_state or initial_state.get("pro_custom_prompt") is None
            assert "con_custom_prompt" not in initial_state or initial_state.get("con_custom_prompt") is None
```

**Validation:**
- Test file created
- CLI runs without errors when no custom prompts provided
- State does not include custom prompt fields
- Existing behavior preserved

**Parallel?** Yes - Can be done alongside T023-T025

**Notes:**
- May need to mock `sys.exit()` for testing CLI
- Use `tmp_path` fixture for file operations
- Focus on state initialization, not full workflow execution

---

### Subtask T023 – Test CLI with PRO-Only Custom Prompt

**Purpose:** Verify CLI works correctly when only `--pro-prompt` is provided.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Create test with valid PRO prompt file
3. Provide `--pro-prompt` flag only
4. Verify `pro_custom_prompt` is in state
5. Verify `con_custom_prompt` is None or missing

**Implementation Pattern:**
```python
def test_cli_with_pro_prompt_only(tmp_path):
    """Test CLI works when only --pro-prompt is provided."""
    # Create a valid PRO prompt file
    pro_prompt_file = tmp_path / "pro_prompt.txt"
    pro_prompt_file.write_text("You are a TPM advocating for project funding.")

    # Mock argparse and workflow
    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--pro-prompt', str(pro_prompt_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={"messages": []})

            # Run CLI

            # Verify state includes pro_custom_prompt
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']

            assert initial_state.get("pro_custom_prompt") == "You are a TPM advocating for project funding."
            assert "con_custom_prompt" not in initial_state or initial_state.get("con_custom_prompt") is None
```

**Validation:**
- Test file created
- CLI accepts `--pro-prompt` flag alone
- State includes `pro_custom_prompt` with correct content
- State does not include `con_custom_prompt`
- No errors during execution

**Parallel?** Yes - Can be done alongside T022, T024-T025

**Notes:**
- Test single-side customization scenario
- Verify CON side uses default behavior

---

### Subtask T024 – Test CLI with CON-Only Custom Prompt

**Purpose:** Verify CLI works correctly when only `--con-prompt` is provided.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Create test with valid CON prompt file
3. Provide `--con-prompt` flag only
4. Verify `con_custom_prompt` is in state
5. Verify `pro_custom_prompt` is None or missing

**Implementation Pattern:**
```python
def test_cli_with_con_prompt_only(tmp_path):
    """Test CLI works when only --con-prompt is provided."""
    # Create a valid CON prompt file
    con_prompt_file = tmp_path / "con_prompt.txt"
    con_prompt_file.write_text("You are a CPO evaluating resource allocation.")

    # Mock argparse and workflow
    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--con-prompt', str(con_prompt_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={"messages": []})

            # Run CLI

            # Verify state includes con_custom_prompt
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']

            assert initial_state.get("con_custom_prompt") == "You are a CPO evaluating resource allocation."
            assert "pro_custom_prompt" not in initial_state or initial_state.get("pro_custom_prompt") is None
```

**Validation:**
- Test file created
- CLI accepts `--con-prompt` flag alone
- State includes `con_custom_prompt` with correct content
- State does not include `pro_custom_prompt`
- No errors during execution

**Parallel?** Yes - Can be done alongside T022-T023, T025

**Notes:**
- Test single-side customization scenario
- Verify PRO side uses default behavior

---

### Subtask T025 – Test CLI with Both Custom Prompts

**Purpose:** Verify CLI works correctly when both `--pro-prompt` and `--con-prompt` are provided.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Create test with both valid PRO and CON prompt files
3. Provide both `--pro-prompt` and `--con-prompt` flags
4. Verify both custom prompts are in state
5. Verify both have correct content

**Implementation Pattern:**
```python
def test_cli_with_both_custom_prompts(tmp_path):
    """Test CLI works when both --pro-prompt and --con-prompt are provided."""
    # Create valid prompt files
    pro_prompt_file = tmp_path / "pro_prompt.txt"
    pro_prompt_file.write_text("You are a TPM advocating for project funding.")
    con_prompt_file = tmp_path / "con_prompt.txt"
    con_prompt_file.write_text("You are a CPO evaluating resource allocation.")

    # Mock argparse and workflow
    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--pro-prompt', str(pro_prompt_file),
        '--con-prompt', str(con_prompt_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={"messages": []})

            # Run CLI

            # Verify state includes both custom prompts
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']

            assert initial_state.get("pro_custom_prompt") == "You are a TPM advocating for project funding."
            assert initial_state.get("con_custom_prompt") == "You are a CPO evaluating resource allocation."
```

**Validation:**
- Test file created
- CLI accepts both `--pro-prompt` and `--con-prompt` flags
- State includes both custom prompts with correct content
- No errors during execution

**Parallel?** Yes - Can be done alongside T022-T024

**Notes:**
- Test full customization scenario (both sides)
- Verify independent handling of both flags

---

### Subtask T026 – Test File Validation (Missing File)

**Purpose:** Verify validation fails with clear error when file doesn't exist.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Test `validate_prompt_file()` with non-existent path
3. Verify function returns `(False, error_message)`
4. Verify error message includes "not found"

**Implementation Pattern:**
```python
def test_validate_prompt_file_missing():
    """Test validation fails for missing file."""
    is_valid, error = validate_prompt_file("nonexistent_file.txt")

    assert is_valid is False
    assert "not found" in error.lower()
    assert "nonexistent_file.txt" in error
```

**Validation:**
- Test function returns `False` for missing file
- Error message clearly indicates file not found
- Error message includes file path

**Parallel?** Yes - Can be done alongside T027-T028

**Notes:**
- Test validation function directly (unit test)
- No need to test through CLI for this case

---

### Subtask T027 – Test File Validation (Empty File)

**Purpose:** Verify validation fails with clear error when file is empty.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Create empty file using `tmp_path` fixture
3. Test `validate_prompt_file()` with empty file path
4. Verify function returns `(False, error_message)`
5. Verify error message includes "empty"

**Implementation Pattern:**
```python
def test_validate_prompt_file_empty(tmp_path):
    """Test validation fails for empty file."""
    # Create empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    is_valid, error = validate_prompt_file(str(empty_file))

    assert is_valid is False
    assert "empty" in error.lower()
    assert str(empty_file) in error
```

**Validation:**
- Test function returns `False` for empty file
- Error message clearly indicates file is empty
- Error message includes file path

**Parallel?** Yes - Can be done alongside T026, T028

**Notes:**
- Use `tmp_path` pytest fixture for temporary files
- File size check should catch 0-byte files

---

### Subtask T028 – Test File Validation (File Too Large)

**Purpose:** Verify validation fails with clear error when file exceeds 5000 characters.

**Files:**
- `tests/test_document_debate_cli.py` (create/modify)

**Steps:**
1. Open or create `tests/test_document_debate_cli.py`
2. Create file with > 5000 characters using `tmp_path` fixture
3. Test `validate_prompt_file()` with large file path
4. Verify function returns `(False, error_message)`
5. Verify error message includes "too large" and limit

**Implementation Pattern:**
```python
def test_validate_prompt_file_too_large(tmp_path):
    """Test validation fails for file exceeding 5000 characters."""
    # Create file with 5001 characters
    large_file = tmp_path / "large.txt"
    large_file.write_text("x" * 5001)

    is_valid, error = validate_prompt_file(str(large_file))

    assert is_valid is False
    assert "too large" in error.lower()
    assert "5000" in error  # Error mentions the limit
    assert str(large_file) in error
```

**Validation:**
- Test function returns `False` for files > 5000 chars
- Error message clearly indicates file too large
- Error message includes character limit (5000)
- Error message includes file path

**Parallel?** Yes - Can be done alongside T026-T027

**Notes:**
- Test boundary at exactly 5000 characters (should pass)
- Test one character over limit (should fail)

---

### Subtask T029 – Test State Propagation Through Workflow

**Purpose:** Verify custom prompt fields propagate through workflow to nodes.

**Files:**
- `tests/test_workflow_state.py` (create)

**Steps:**
1. Create `tests/test_workflow_state.py`
2. Create state with both `pro_custom_prompt` and `con_custom_prompt`
3. Mock workflow execution
4. Verify nodes receive custom prompts in state
5. Verify state fields preserved through workflow

**Implementation Pattern:**
```python
# tests/test_workflow_state.py
import pytest
from unittest.mock import patch, MagicMock
from debate_state import DebateState
from workflow.document_debate_workflow import DocumentDebateWorkflow

def test_state_propagation_with_custom_prompts():
    """Test custom prompt fields propagate through workflow."""
    # Create initial state with custom prompts
    initial_state: DebateState = {
        "debate_topic": "Test topic",
        "positions": {"pro": "For", "con": "Against"},
        "messages": [],
        "pro_custom_prompt": "You are a TPM...",
        "con_custom_prompt": "You are a CPO..."
    }

    # Mock nodes to verify they receive custom prompts
    with patch('workflow.document_debate_workflow.ProDebaterNode') as mock_pro_node:
        with patch('workflow.document_debate_workflow.ConDebaterNode') as mock_con_node:
            mock_pro_node.return_value = MagicMock()
            mock_con_node.return_value = MagicMock()

            # Run workflow
            workflow = DocumentDebateWorkflow()
            result = workflow.run(initial_state=initial_state)

            # Verify nodes were called with state containing custom prompts
            # This requires inspecting mock calls
            assert True  # Placeholder for actual verification
```

**Validation:**
- Test file created
- Initial state includes custom prompts
- Nodes receive custom prompts in their `__call__` methods
- State fields preserved through workflow stages

**Parallel?** Yes - Can be done alongside T030-T031

**Notes:**
- May need to inspect mock call arguments
- Focus on state passing, not full workflow logic
- Use existing workflow mocking patterns from project

---

### Subtask T030 – Test Prompt Injection in PRO Node

**Purpose:** Verify PRO node correctly injects custom prompt into system prompt.

**Files:**
- `tests/test_pro_debater_node.py` (create)

**Steps:**
1. Create `tests/test_pro_debater_node.py`
2. Create `ProDebaterNode` instance
3. Create state with `pro_custom_prompt`
4. Call `_create_chain_with_custom_prompt()` method
5. Verify enhanced prompt includes custom content
6. Verify base prompt not replaced (custom prepended)

**Implementation Pattern:**
```python
# tests/test_pro_debater_node.py
import pytest
from unittest.mock import MagicMock
from nodes.pro_debater_node import ProDebaterNode
from prompts.pro_debater_prompts import SYSTEM_PROMPT

def test_pro_node_custom_prompt_injection():
    """Test PRO node injects custom prompt correctly."""
    # Mock LLM config
    mock_llm_config = MagicMock()
    mock_llm_config.model_name = "gpt-4"

    # Create PRO node
    pro_node = ProDebaterNode(mock_llm_config)

    # Test chain creation with custom prompt
    custom_prompt = "You are a TPM advocating for funding."
    enhanced_system_prompt = pro_node._create_chain_with_custom_prompt(
        custom_prompt, SYSTEM_PROMPT, "Test human prompt"
    )

    # Verify custom prompt prepended to base prompt
    assert enhanced_system_prompt.startswith(custom_prompt)
    assert SYSTEM_PROMPT in enhanced_system_prompt
    assert enhanced_system_prompt == f"{custom_prompt}\n\n{SYSTEM_PROMPT}"

def test_pro_node_no_custom_prompt():
    """Test PRO node uses base prompt when custom prompt is None."""
    mock_llm_config = MagicMock()
    mock_llm_config.model_name = "gpt-4"

    pro_node = ProDebaterNode(mock_llm_config)

    # Test chain creation without custom prompt
    enhanced_system_prompt = pro_node._create_chain_with_custom_prompt(
        None, SYSTEM_PROMPT, "Test human prompt"
    )

    # Verify base prompt used unchanged
    assert enhanced_system_prompt == SYSTEM_PROMPT
```

**Validation:**
- Test file created
- Custom prompt prepended to base system prompt
- Base system prompt preserved (not replaced)
- None case handled correctly (base prompt used)

**Parallel?** Yes - Can be done alongside T031

**Notes:**
- Test with mock LLM config (not actual API calls)
- Verify string formatting exactly
- Test both with and without custom prompt

---

### Subtask T031 – Test Prompt Injection in CON Node

**Purpose:** Verify CON node correctly injects custom prompt into system prompt.

**Files:**
- `tests/test_con_debater_node.py` (create)

**Steps:**
1. Create `tests/test_con_debater_node.py`
2. Create `ConDebaterNode` instance
3. Create state with `con_custom_prompt`
4. Call `_create_chain_with_custom_prompt()` method
5. Verify enhanced prompt includes custom content
6. Verify base prompt not replaced (custom prepended)

**Implementation Pattern:**
```python
# tests/test_con_debater_node.py
import pytest
from unittest.mock import MagicMock
from nodes.con_debater_node import ConDebaterNode
from prompts.con_debater_prompts import SYSTEM_PROMPT

def test_con_node_custom_prompt_injection():
    """Test CON node injects custom prompt correctly."""
    # Mock LLM config
    mock_llm_config = MagicMock()
    mock_llm_config.model_name = "gpt-4"

    # Create CON node
    con_node = ConDebaterNode(mock_llm_config)

    # Test chain creation with custom prompt
    custom_prompt = "You are a CPO evaluating resources."
    enhanced_system_prompt = con_node._create_chain_with_custom_prompt(
        custom_prompt, SYSTEM_PROMPT, "Test human prompt"
    )

    # Verify custom prompt prepended to base prompt
    assert enhanced_system_prompt.startswith(custom_prompt)
    assert SYSTEM_PROMPT in enhanced_system_prompt
    assert enhanced_system_prompt == f"{custom_prompt}\n\n{SYSTEM_PROMPT}"

def test_con_node_no_custom_prompt():
    """Test CON node uses base prompt when custom prompt is None."""
    mock_llm_config = MagicMock()
    mock_llm_config.model_name = "gpt-4"

    con_node = ConDebaterNode(mock_llm_config)

    # Test chain creation without custom prompt
    enhanced_system_prompt = con_node._create_chain_with_custom_prompt(
        None, SYSTEM_PROMPT, "Test human prompt"
    )

    # Verify base prompt used unchanged
    assert enhanced_system_prompt == SYSTEM_PROMPT
```

**Validation:**
- Test file created
- Custom prompt prepended to base system prompt
- Base system prompt preserved (not replaced)
- None case handled correctly (base prompt used)

**Parallel?** Yes - Can be done alongside T030

**Notes:**
- Test with mock LLM config (not actual API calls)
- Verify string formatting exactly
- Test both with and without custom prompt

## Test Strategy

**Test Categories:**
1. **Backward Compatibility Tests** (T021) - Ensure existing tests pass
2. **CLI Behavior Tests** (T022-T025) - Verify all flag combinations
3. **Validation Tests** (T026-T028) - Verify file validation logic
4. **Integration Tests** (T029) - Verify state propagation
5. **Unit Tests** (T030-T031) - Verify node prompt injection

**Test Execution:**
```bash
# Run all tests (including new):
pytest

# Run only new tests:
pytest tests/test_document_debate_cli.py
pytest tests/test_workflow_state.py
pytest tests/test_pro_debater_node.py
pytest tests/test_con_debater_node.py

# Run with coverage:
pytest --cov=.
```

**Definition of Done:**
- All existing tests pass without modification
- T022-T025: All CLI flag combinations tested
- T026-T028: All validation rules tested
- T029: State propagation verified
- T030-T031: Node prompt injection verified
- All new tests pass

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing tests fail due to state extension | High | Run T021 first; fix regressions before continuing |
| Mock tests don't reflect real behavior | Medium | Use integration tests where possible; test with real file I/O |
| Tests don't cover edge cases | Low | Include validation tests, single-side customization, both prompts |
| Test mocking too complex | Medium | Keep tests simple; focus on specific behavior being tested |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] All existing tests pass (T021)
- [ ] CLI with no custom prompts tested (T022)
- [ ] CLI with PRO-only custom prompt tested (T023)
- [ ] CLI with CON-only custom prompt tested (T024)
- [ ] CLI with both custom prompts tested (T025)
- [ ] File validation: missing file tested (T026)
- [ ] File validation: empty file tested (T027)
- [ ] File validation: too large tested (T028)
- [ ] State propagation tested (T029)
- [ ] PRO node prompt injection tested (T030)
- [ ] CON node prompt injection tested (T031)
- [ ] All new tests pass

**Review Context:**
- Spec requirement FR6: Must maintain backward compatibility
- Spec requirement FR5: File validation rules must be tested
- Spec requirement FR1-FR4: New functionality must be tested
- Quickstart scenarios: All example use cases should be tested

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
