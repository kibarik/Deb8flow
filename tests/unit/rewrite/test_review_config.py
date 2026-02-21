"""
Unit tests for review configuration objects.
"""
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
    substitute_placeholders,
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


class TestPromptConfig:
    """Tests for PromptConfig."""

    def test_default_values(self):
        """Test default values are None."""
        config = PromptConfig()
        assert config.system_prompt is None
        assert config.user_prompt is None
        assert config.result_template is None
        assert config.variables == {}

    def test_custom_values(self):
        """Test custom values."""
        config = PromptConfig(
            system_prompt=Path("/path/to/system.md"),
            variables={"project": "MyApp"}
        )
        assert config.system_prompt == Path("/path/to/system.md")
        assert config.variables == {"project": "MyApp"}


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self):
        """Test default values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.backoff == "exponential"
        assert config.initial_delay == 1.0

    def test_negative_retries_error(self):
        """Test error on negative retries."""
        with pytest.raises(ValueError, match="max_retries"):
            RetryConfig(max_retries=-1)

    def test_invalid_backoff_error(self):
        """Test error on invalid backoff."""
        with pytest.raises(ValueError, match="backoff"):
            RetryConfig(backoff="invalid")


class TestCheckConfig:
    """Tests for CheckConfig."""

    def test_default_values(self):
        """Test all defaults are True."""
        config = CheckConfig()
        assert config.security is True
        assert config.performance is True
        assert config.style is True

    def test_custom_values(self):
        """Test custom boolean values."""
        config = CheckConfig(security=False, performance=True)
        assert config.security is False
        assert config.performance is True


class TestOutputConfig:
    """Tests for OutputConfig."""

    def test_default_values(self):
        """Test default values."""
        config = OutputConfig()
        assert config.format == "markdown"
        assert config.include_snippets is True
        assert config.max_comment_length == 500

    def test_invalid_format_error(self):
        """Test error on invalid format."""
        with pytest.raises(ValueError, match="format"):
            OutputConfig(format="xml")

    def test_invalid_max_length_error(self):
        """Test error on non-positive max length."""
        with pytest.raises(ValueError, match="max_comment_length"):
            OutputConfig(max_comment_length=0)


class TestContextConfig:
    """Tests for ContextConfig."""

    def test_default_values(self):
        """Test default values."""
        config = ContextConfig()
        assert config.window_size == 8000
        assert config.include_patterns == []
        assert config.exclude_patterns == []

    def test_custom_patterns(self):
        """Test custom pattern lists."""
        config = ContextConfig(
            include_patterns=["src/**/*.py"],
            exclude_patterns=["**/test_*.py"]
        )
        assert "src/**/*.py" in config.include_patterns
        assert "**/test_*.py" in config.exclude_patterns


class TestLoggingConfig:
    """Tests for LoggingConfig."""

    def test_default_values(self):
        """Test default values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.debug is False

    def test_invalid_level_error(self):
        """Test error on invalid log level."""
        with pytest.raises(ValueError, match="level"):
            LoggingConfig(level="INVALID")


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
        assert merged.checks.performance is True  # Unchanged

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
