---
work_package_id: WP05
title: Unit Tests
lane: planned
dependencies: []
subtasks: [T022, T023, T024, T025, T026, T027]
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP05: Unit Tests

**Priority**: P1
**Estimated Size**: ~340 lines (6 subtasks × ~55 lines each)
**Implementation Command**: `spec-kitty implement WP05 --base WP03`

## Objective

Comprehensive unit tests for all configuration objects and merge logic.

## Context

Tests ensure all validation rules work correctly, merge logic behaves as expected, and error messages are helpful. Target >80% coverage for `review_config.py`.

**Reference**:
- Parent WPs: WP01 (value objects), WP02 (merge logic), WP03 (loader)
- pytest documentation for test patterns

## Subtasks

### T022: Test LLMConfig validation

**Purpose**: Test all LLMConfig validation rules.

**Implementation**:

Create `tests/unit/rewrite/test_review_config.py`:

```python
"""Unit tests for review configuration objects."""
import pytest
from pathlib import Path
from src.rewrite.domain.review_config import (
    LLMConfig,
    PromptConfig,
    RetryConfig,
    CheckConfig,
    OutputConfig,
    ContextConfig,
    LoggingConfig,
    ReviewConfig,
)


class TestLLMConfig:
    """Tests for LLMConfig validation."""

    def test_default_values(self):
        """Test that all defaults are set correctly."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.max_tokens_request == 4000
        assert config.max_tokens_response == 2000
        assert config.timeout == 120

    def test_temperature_validation(self):
        """Test temperature range validation (0.0 - 1.0)."""
        # Valid values
        LLMConfig(temperature=0.0)
        LLMConfig(temperature=0.5)
        LLMConfig(temperature=1.0)

        # Invalid values
        with pytest.raises(ValueError, match="temperature"):
            LLMConfig(temperature=-0.1)
        with pytest.raises(ValueError, match="temperature"):
            LLMConfig(temperature=1.5)

    def test_top_p_validation(self):
        """Test top_p range validation (0.0 - 1.0)."""
        # Valid values
        LLMConfig(top_p=0.0)
        LLMConfig(top_p=0.5)
        LLMConfig(top_p=1.0)

        # Invalid values
        with pytest.raises(ValueError, match="top_p"):
            LLMConfig(top_p=-0.1)
        with pytest.raises(ValueError, match="top_p"):
            LLMConfig(top_p=1.5)

    def test_positive_values_validation(self):
        """Test that numeric values must be positive."""
        with pytest.raises(ValueError, match="max_tokens_request"):
            LLMConfig(max_tokens_request=0)
        with pytest.raises(ValueError, match="max_tokens_response"):
            LLMConfig(max_tokens_response=0)
        with pytest.raises(ValueError, match="timeout"):
            LLMConfig(timeout=0)

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            top_p=0.7,
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.temperature == 0.3
        assert config.top_p == 0.7
```

**Validation**:
- [ ] All validation rules tested
- [ ] Edge cases (0.0, 1.0 boundaries) tested
- [ ] Error messages contain the field name

---

### T023: Test profile merge logic

**Purpose**: Test profile merge inheritance and override behavior.

**Implementation**:

```python
class TestProfileMerge:
    """Tests for profile merge logic."""

    def test_profile_override_single_key(self):
        """Test that profile overrides only specified keys."""
        base = ReviewConfig(
            llm=LLMConfig(temperature=0.5, model="gpt-4o-mini"),
            profiles={
                "strict": {"llm": {"temperature": 0.1}}
            }
        )
        merged = base.merge_with_profile("strict")

        assert merged.llm.temperature == 0.1  # Overridden
        assert merged.llm.model == "gpt-4o-mini"  # Inherited

    def test_profile_override_nested_keys(self):
        """Test profile override for nested configurations."""
        base = ReviewConfig(
            llm=LLMConfig(temperature=0.5, top_p=0.9),
            profiles={
                "custom": {
                    "llm": {"temperature": 0.2, "top_p": 0.5}
                }
            }
        )
        merged = base.merge_with_profile("custom")

        assert merged.llm.temperature == 0.2
        assert merged.llm.top_p == 0.5

    def test_profile_override_checks(self):
        """Test profile override for checks configuration."""
        base = ReviewConfig(
            checks=CheckConfig(security=True, performance=True, style=True),
            profiles={
                "security_only": {"checks": {"performance": False, "style": False}}
            }
        )
        merged = base.merge_with_profile("security_only")

        assert merged.checks.security == True  # Inherited
        assert merged.checks.performance == False  # Overridden
        assert merged.checks.style == False  # Overridden

    def test_empty_profile_unchanged(self):
        """Test that empty profile dict doesn't change config."""
        base = ReviewConfig(llm=LLMConfig(temperature=0.5))
        base.profiles = {"empty": {}}
        merged = base.merge_with_profile("empty")

        assert merged.llm.temperature == 0.5

    def test_profile_not_found_error(self):
        """Test helpful error when profile doesn't exist."""
        base = ReviewConfig(profiles={"strict": {}})

        with pytest.raises(KeyError, match="Profile 'xyz' not found"):
            base.merge_with_profile("xyz")

    def test_merge_returns_new_instance(self):
        """Test that merge returns a new instance (immutability)."""
        base = ReviewConfig(
            llm=LLMConfig(temperature=0.5),
            profiles={"strict": {"llm": {"temperature": 0.1}}}
        )
        merged = base.merge_with_profile("strict")

        assert base is not merged
        assert base.llm.temperature == 0.5  # Unchanged
        assert merged.llm.temperature == 0.1
```

**Validation**:
- [ ] Key-based override verified
- [ ] Nested merges tested
- [ ] Empty profile handled
- [ ] Immutability preserved

---

### T024: Test CLI override logic

**Purpose**: Test CLI override priority over profiles.

**Implementation**:

```python
class TestCLIMerge:
    """Tests for CLI override logic."""

    def test_single_cli_override(self):
        """Test single CLI override."""
        base = ReviewConfig(llm=LLMConfig(temperature=0.5))
        merged = base.merge_with_cli({"llm.temperature": 0.1})

        assert merged.llm.temperature == 0.1

    def test_multiple_cli_overrides(self):
        """Test multiple CLI overrides applied together."""
        base = ReviewConfig(
            llm=LLMConfig(temperature=0.5, top_p=0.9),
            checks=CheckConfig(security=True, performance=True),
        )
        merged = base.merge_with_cli({
            "llm.temperature": 0.2,
            "llm.top_p": 0.7,
            "checks.security": False,
        })

        assert merged.llm.temperature == 0.2
        assert merged.llm.top_p == 0.7
        assert merged.checks.security == False
        assert merged.checks.performance == True  # Unchanged

    def test_cli_overrides_profile(self):
        """Test that CLI has highest priority over profile."""
        base = ReviewConfig(
            llm=LLMConfig(temperature=0.5),
            profiles={
                "strict": {"llm": {"temperature": 0.1}}
            }
        )
        with_profile = base.merge_with_profile("strict")
        with_cli = with_profile.merge_with_cli({"llm.temperature": 0.3})

        assert with_profile.llm.temperature == 0.1
        assert with_cli.llm.temperature == 0.3  # CLI wins

    def test_invalid_section_error(self):
        """Test error for invalid config section."""
        base = ReviewConfig()

        with pytest.raises(ValueError, match="Unknown config section"):
            base.merge_with_cli({"invalid_section.field": "value"})

    def test_invalid_field_error(self):
        """Test error for invalid field in valid section."""
        base = ReviewConfig()

        with pytest.raises(ValueError, match="Unknown LLM field"):
            base.merge_with_cli({"llm.invalid_field": "value"})
```

**Validation**:
- [ ] CLI override works for single value
- [ ] Multiple overrides applied together
- [ ] CLI has highest priority
- [ ] Invalid paths raise helpful errors

---

### T025: Test placeholder substitution

**Purpose**: Test placeholder substitution in prompts.

**Implementation**:

```python
from src.rewrite.domain.review_config import substitute_placeholders


class TestPlaceholderSubstitution:
    """Tests for placeholder substitution."""

    def test_single_placeholder(self):
        """Test single placeholder substitution."""
        result = substitute_placeholders(
            "File: {file_path}",
            {"file_path": "/path/to/file.py"}
        )
        assert result == "File: /path/to/file.py"

    def test_multiple_placeholders(self):
        """Test multiple placeholders in one string."""
        result = substitute_placeholders(
            "Review: {file_path} for {project}",
            {"file_path": "/path/to/file.py", "project": "MyApp"}
        )
        assert result == "Review: /path/to/file.py for MyApp"

    def test_missing_placeholder_unchanged(self):
        """Test that missing placeholders are left unchanged."""
        result = substitute_placeholders(
            "File: {file_path} {missing_var}",
            {"file_path": "/path/to/file.py"}
        )
        assert result == "File: /path/to/file.py {missing_var}"

    def test_builtin_timestamp(self):
        """Test built-in timestamp placeholder."""
        result = substitute_placeholders(
            "Generated at: {timestamp}",
            {}
        )
        assert "Generated at:" in result
        assert len(result) > 20  # Has timestamp

    def test_special_characters(self):
        """Test handling of special characters in values."""
        result = substitute_placeholders(
            "Path: {file_path}",
            {"file_path": "/path/with spaces/file.py"}
        )
        assert result == "Path: /path/with spaces/file.py"
```

**Validation**:
- [ ] Single placeholder works
- [ ] Multiple placeholders work
- [ ] Missing placeholders handled gracefully
- [ ] Built-in variables work

---

### T026: Test configuration validation errors

**Purpose**: Test all validation error paths.

**Implementation**:

```python
class TestValidationErrors:
    """Tests for configuration validation errors."""

    def test_retry_config_validation(self):
        """Test RetryConfig validation."""
        with pytest.raises(ValueError, match="max_retries"):
            RetryConfig(max_retries=-1)

        with pytest.raises(ValueError, match="backoff"):
            RetryConfig(backoff="invalid")

    def test_output_config_validation(self):
        """Test OutputConfig validation."""
        with pytest.raises(ValueError, match="format"):
            OutputConfig(format="xml")

        with pytest.raises(ValueError, match="max_comment_length"):
            OutputConfig(max_comment_length=0)

    def test_logging_config_validation(self):
        """Test LoggingConfig validation."""
        with pytest.raises(ValueError, match="level"):
            LoggingConfig(level="INVALID")

        # Case insensitive
        config = LoggingConfig(level="debug")  # lowercase
        assert config.level == "debug"  # or converted to uppercase

    def test_checks_all_disabled_error(self):
        """Test error when all checks are disabled."""
        from src.rewrite.infrastructure.config_loader import validate_config

        config = ReviewConfig(
            checks=CheckConfig(security=False, performance=False, style=False)
        )

        with pytest.raises(ValueError, match="At least one check"):
            validate_config(config)
```

**Validation**:
- [ ] All validation error paths tested
- [ ] Error messages contain relevant info
- [ ] Edge cases covered

---

### T027: Test edge cases

**Purpose**: Test uncommon edge cases and boundaries.

**Implementation**:

```python
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_config_dict(self):
        """Test loading from empty dict uses defaults."""
        config = ReviewConfig.from_dict({})
        assert config.profile == "balanced"
        assert config.llm.temperature == 0.7

    def test_from_dict_with_partial_config(self):
        """Test loading with partial configuration."""
        config = ReviewConfig.from_dict({
            "llm": {"temperature": 0.3}
        })
        assert config.llm.temperature == 0.3
        assert config.llm.model == "gpt-4o-mini"  # Default

    def test_large_context_window(self):
        """Test very large context window values."""
        config = ContextConfig(window_size=128000)
        assert config.window_size == 128000

    def test_empty_pattern_lists(self):
        """Test empty include/exclude patterns."""
        config = ContextConfig(
            include_patterns=[],
            exclude_patterns=[]
        )
        assert config.include_patterns == []
        assert config.exclude_patterns == []

    def test_immutability_cannot_modify(self):
        """Test that frozen dataclass cannot be modified."""
        config = LLMConfig()

        with pytest.raises(Exception):  # FrozenInstanceError
            config.temperature = 0.5

    def test_prompt_variables_merge(self):
        """Test that prompt variables merge correctly."""
        base = ReviewConfig(
            prompts=PromptConfig(variables={"a": "1", "b": "2"}),
            profiles={
                "custom": {"prompts": {"variables": {"b": "3", "c": "4"}}}
            }
        )
        merged = base.merge_with_profile("custom")

        assert merged.prompts.variables["a"] == "1"  # Inherited
        assert merged.prompts.variables["b"] == "3"  # Overridden
        assert merged.prompts.variables["c"] == "4"  # Added
```

**Validation**:
- [ ] Empty config handled
- [ ] Partial config loads correctly
- [ ] Large values accepted
- [ ] Immutability enforced

## Files Created

- `tests/unit/rewrite/test_review_config.py` (new, ~300 lines)

## Test Execution

```bash
# Run all review config tests
pytest tests/unit/rewrite/test_review_config.py -v

# Run with coverage
pytest tests/unit/rewrite/test_review_config.py --cov=src/rewrite/domain/review_config --cov-report=term-missing
```

## Definition of Done

- [ ] All validation rules have tests
- [ ] Merge logic tested for all scenarios
- [ ] CLI override tested with priority verification
- [ ] Placeholder substitution tested
- [ ] Error messages validated
- [ ] Edge cases covered
- [ ] pytest passes for all tests
- [ ] Coverage >80% for review_config.py

## Reviewer Guidance

**Verify**:
1. Tests use pytest fixtures where appropriate
2. Error messages are asserted in tests
3. Immutability is tested
4. Edge cases are covered

**Common Issues**:
- Missing edge case tests → Add boundary tests
- Not asserting error messages → Verify helpful errors
- Coverage gaps → Add tests for uncovered lines

## Risks

- **Low Risk**: Standard unit testing
- **Mitigation**: Comprehensive test coverage
