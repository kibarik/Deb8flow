---
work_package_id: "WP02"
subtasks:
  - "T007"
  - "T008"
  - "T009"
  - "T010"
title: "Configuration Tests"
phase: "Phase 1 - Foundation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
dependencies: ["WP01"]
---

# Work Package Prompt: WP02 – Configuration Tests

## Objectives & Success Criteria

Ensure configuration loading and validation works correctly with valid and invalid inputs, following TDD principles from the constitution.

**Success Criteria**:
- All configuration tests pass with pytest
- Edge cases from spec acceptance scenarios are covered
- Error messages are clear and actionable
- Test fixtures cover valid, invalid, and boundary cases

## Context & Constraints

**Supporting Documents**:
- Constitution: `.kittify/memory/constitution.md` - TDD approach, pytest required
- Spec: `kitty-specs/014-flexible-debate-config-yaml/spec.md` - User story acceptance scenarios
- Data Model: `kitty-specs/014-flexible-debate-config-yaml/data-model.md` - Validation rules

**Dependencies**:
- WP01 must be complete (Configuration Data Model)

## Subtasks & Detailed Guidance

### Subtask T007 – Tests: Config Loading

**Purpose**: Verify configuration loading works with valid YAML files.

**Steps**:

1. Create `tests/test_config/test_debate_config.py` with test class:

```python
import pytest
from pathlib import Path
from configurations.debate_config import (
    load_config,
    DebateConfig,
    ValidationError,
    ConfigNotFoundError
)

class TestConfigLoading:
    """Test configuration loading from YAML files."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_content = """
workflow:
  mode: standard
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: "You argue for..."
    model: deepseek-chat
  - name: con
    side: con
    prompt: "You argue against..."
    model: deepseek-chat

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert isinstance(config, DebateConfig)
        assert config.workflow.mode == "standard"
        assert config.workflow.rounds == 3
        assert len(config.roles) == 2

    def test_load_config_with_defaults(self, tmp_path):
        """Test loading config with optional fields omitted."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "Prompt"
  - name: con
    side: con
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.workflow.rounds == 3  # Default value

    def test_load_missing_file_raises_error(self):
        """Test loading non-existent file raises ConfigNotFoundError."""
        with pytest.raises(ConfigNotFoundError):
            load_config("/nonexistent/path.yml")
```

**Files**:
- `tests/test_config/test_debate_config.py` (new file, start with ~80 lines)

**Parallel?**: No - foundation for other test subtasks

**Notes**:
- Use pytest fixtures for temp directory (`tmp_path`)
- Test both complete and minimal configs
- Verify default values are applied

---

### Subtask T008 – Tests: Config Validation

**Purpose**: Verify validation catches all required field errors and type violations.

**Steps**:

1. Add validation tests to `tests/test_config/test_debate_config.py`:

```python
class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_workflow_mode_raises_error(self, tmp_path):
        """Test invalid workflow mode raises ValidationError."""
        config_content = """
workflow:
  mode: invalid_mode
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Invalid workflow mode" in str(exc_info.value)

    def test_rounds_below_one_raises_error(self, tmp_path):
        """Test rounds < 1 raises ValidationError."""
        config_content = """
workflow:
  mode: standard
  rounds: 0

roles:
  - name: pro
    side: pro
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Rounds must be >= 1" in str(exc_info.value)

    def test_missing_pro_role_raises_error(self, tmp_path):
        """Test missing PRO role raises ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: neutral
    side: neutral
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Missing required role" in str(exc_info.value)
        assert "side='pro'" in str(exc_info.value)

    def test_duplicate_role_names_raises_error(self, tmp_path):
        """Test duplicate role names raise ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "Prompt"
  - name: pro
    side: con
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Duplicate role name" in str(exc_info.value)

    def test_invalid_side_raises_error(self, tmp_path):
        """Test invalid side value raises ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: invalid
    prompt: "Prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Invalid side" in str(exc_info.value)

    def test_model_not_found_raises_error(self, tmp_path):
        """Test missing model reference raises ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "Prompt"
    model: nonexistent_model

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Model not found" in str(exc_info.value)

    def test_temperature_out_of_range_raises_error(self, tmp_path):
        """Test temperature outside [0.0, 2.0] raises ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "Prompt"
    temperature: 2.5

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "Temperature" in str(exc_info.value)
        assert "out of range" in str(exc_info.value)

    def test_multiple_errors_reported_together(self, tmp_path):
        """Test that multiple validation errors are reported together."""
        config_content = """
workflow:
  mode: invalid
  rounds: 0

roles:
  - name: pro
    side: invalid
    prompt: "Prompt"
    model: nonexistent

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        error_msg = str(exc_info.value)
        # Should contain multiple errors
        assert "Invalid workflow mode" in error_msg
        assert "Rounds must be >= 1" in error_msg
        assert "Invalid side" in error_msg
```

**Files**:
- `tests/test_config/test_debate_config.py` (modify, add ~150 lines)

**Parallel?**: Yes - can be written alongside T009, T010

**Notes**:
- Test each validation rule from schema contract
- Verify error messages are specific and helpful
- Test that multiple errors are collected before raising

---

### Subtask T009 – Tests: Prompt Resolution

**Purpose**: Verify prompt resolution works with inline prompts, file references, and precedence rules.

**Steps**:

1. Add prompt resolution tests to `tests/test_config/test_debate_config.py`:

```python
from configurations.debate_config import PromptFileNotFoundError

class TestPromptResolution:
    """Test prompt resolution from inline text and files."""

    def test_inline_prompt_is_resolved(self, tmp_path):
        """Test inline prompt is used when no prompt_file specified."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "This is an inline prompt"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        pro_role = config.roles[0]

        assert hasattr(pro_role, 'resolved_prompt')
        assert pro_role.resolved_prompt == "This is an inline prompt"

    def test_prompt_file_is_loaded(self, tmp_path):
        """Test prompt is loaded from file when prompt_file specified."""
        # Create prompt file
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        prompt_file = prompts_dir / "pro_prompt.md"
        prompt_file.write_text("Prompt from file")

        # Create config
        config_content = f"""
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt_file: prompts/pro_prompt.md

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        pro_role = config.roles[0]

        assert pro_role.resolved_prompt == "Prompt from file"

    def test_prompt_file_takes_precedence_over_inline(self, tmp_path):
        """Test prompt_file is used when both prompt and prompt_file specified."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        prompt_file = prompts_dir / "pro_prompt.md"
        prompt_file.write_text("File prompt")

        config_content = f"""
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "Inline prompt"
    prompt_file: prompts/pro_prompt.md

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        pro_role = config.roles[0]

        # File should take precedence
        assert pro_role.resolved_prompt == "File prompt"

    def test_missing_prompt_file_raises_error(self, tmp_path):
        """Test missing prompt file raises PromptFileNotFoundError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt_file: nonexistent.md

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(PromptFileNotFoundError) as exc_info:
            load_config(str(config_file))

        assert "not found" in str(exc_info.value)

    def test_no_prompt_raises_error(self, tmp_path):
        """Test role with no prompt or prompt_file raises ValidationError."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        assert "no prompt" in str(exc_info.value).lower()

    def test_prompt_file_relative_to_config_dir(self, tmp_path):
        """Test prompt files are resolved relative to config directory."""
        # Create nested structure
        config_dir = tmp_path / "subdir"
        config_dir.mkdir()
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        prompt_file = prompts_dir / "role.md"
        prompt_file.write_text("Nested prompt")

        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt_file: prompts/role.md

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = config_dir / "test.yml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        pro_role = config.roles[0]

        assert pro_role.resolved_prompt == "Nested prompt"
```

**Files**:
- `tests/test_config/test_debate_config.py` (modify, add ~130 lines)

**Parallel?**: Yes - can be written alongside T008, T010

**Notes**:
- Test relative path resolution carefully
- Verify precedence: file > inline
- Test error cases with clear messages

---

### Subtask T010 – Tests: Error Handling

**Purpose**: Verify error handling provides clear, actionable messages.

**Steps**:

1. Add error handling tests to `tests/test_config/test_debate_config.py`:

```python
class TestErrorHandling:
    """Test error messages are clear and actionable."""

    def test_config_not_found_error_includes_path(self):
        """Test ConfigNotFoundError includes file path."""
        with pytest.raises(ConfigNotFoundError) as exc_info:
            load_config("/path/to/missing.yml")

        assert "/path/to/missing.yml" in str(exc_info.value)

    def test_validation_error_lists_multiple_issues(self, tmp_path):
        """Test ValidationError collects multiple issues."""
        config_content = """
workflow:
  mode: bad
  rounds: -1

roles:
  - name: pro
    side: invalid
    prompt: "P"

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        error_msg = str(exc_info.value)
        # Should list all errors
        assert "workflow mode" in error_msg.lower() or "mode" in error_msg.lower()
        assert "rounds" in error_msg.lower()
        assert "side" in error_msg.lower()

    def test_prompt_file_error_includes_role_name(self, tmp_path):
        """Test PromptFileNotFoundError includes role context."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: my_special_role
    side: pro
    prompt_file: missing.md

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(PromptFileNotFoundError) as exc_info:
            load_config(str(config_file))

        error_msg = str(exc_info.value)
        assert "my_special_role" in error_msg
        assert "missing.md" in error_msg

    def test_model_not_found_error_lists_available_models(self, tmp_path):
        """Test ModelNotFoundError lists available models."""
        config_content = """
workflow:
  mode: standard

roles:
  - name: pro
    side: pro
    prompt: "P"
    model: gpt-4

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
"""
        config_file = tmp_path / "test.yml"
        config_file.write_text(config_content)

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        error_msg = str(exc_info.value)
        assert "deepseek-chat" in error_msg  # Available model listed
```

**Files**:
- `tests/test_config/test_debate_config.py` (modify, add ~80 lines)

**Parallel?**: Yes - can be written alongside T008, T009

**Notes**:
- Error messages should include context (file paths, role names)
- Test that available options are listed (e.g., available models)
- Verify errors are actionable (user knows what to fix)

## Test Strategy

**Running Tests**:
```bash
# Run all config tests
pytest tests/test_config/test_debate_config.py -v

# Run specific test class
pytest tests/test_config/test_debate_config.py::TestConfigLoading -v

# Run with coverage
pytest tests/test_config/ --cov=configurations.debate_config
```

**Test Fixtures**:
- Use pytest's `tmp_path` fixture for temporary config files
- Create reusable fixtures for common config structures

## Risks & Mitigations

**Risk**: Test setup may be complex (multiple files, directories)
**Mitigation**: Use pytest fixtures to reduce duplication

**Risk**: Tests may be fragile to file system differences
**Mitigation**: Use `tmp_path` for all file operations; avoid absolute paths

## Review Guidance

**Key Acceptance Checkpoints**:
- [ ] All test functions follow pytest conventions (test_*)
- [ ] Test fixtures use `tmp_path` for temp files
- [ ] Edge cases from spec acceptance scenarios are covered
- [ ] Error messages are verified to be clear and actionable
- [ ] Tests cover both success and failure paths
- [ ] No test relies on external state (file system outside tmp_path)

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created

---

### Valid lanes

To change lane: `spec-kitty agent tasks move-task WP02 --to <lane>`
Valid lanes: `planned`, `doing`, `for_review`, `done`
