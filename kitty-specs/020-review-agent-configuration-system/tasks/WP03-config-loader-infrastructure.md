---
work_package_id: WP03
title: Config Loader Infrastructure
lane: "done"
dependencies: []
base_branch: main
base_commit: 228e94976f3278af45211400c017a9f6bcde34d3
created_at: '2026-02-21T11:12:33.059167+00:00'
subtasks: [T014, T015, T016, T017]
shell_pid: "79802"
agent: "claude"
reviewed_by: "ALeks ishmanov"
review_status: "approved"
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP03: Config Loader Infrastructure

**Priority**: P0 (Foundational)
**Estimated Size**: ~240 lines (4 subtasks × ~55 lines each)
**Implementation Command**: `spec-kitty implement WP03 --base WP02`

## Objective

Create config loader with YAML parsing, environment variable expansion, and validation.

## Context

The config loader is responsible for reading `config/debate_config.yaml`, expanding environment variables (${VAR:default} syntax), and returning a validated ReviewConfig object.

**Reference Files**:
- Parent WPs: WP01 (value objects), WP02 (merge logic)
- Target config: `config/debate_config.yaml`

## Subtasks

### T014: Create config_loader.py with load_config() function

**Purpose**: Create the main config loading function.

**Implementation**:

Create `src/rewrite/infrastructure/config_loader.py`:

```python
"""Configuration loader for review agent.

Loads YAML configuration files with environment variable expansion
and validation.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from ..domain.review_config import ReviewConfig


logger = __import__("logging").getLogger(__name__)


def load_config(
    config_path: Path,
    profile: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> ReviewConfig:
    """Load and parse review configuration from YAML file.

    Args:
        config_path: Path to debate_config.yaml file
        profile: Optional profile name to apply
        cli_overrides: Optional CLI flag overrides

    Returns:
        Fully loaded and merged ReviewConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create config/debate_config.yaml or specify correct path."
        )

    # Load YAML file
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f) or {}

    # Extract rewrite section
    rewrite_config = raw_config.get("rewrite", {})
    review_dict = rewrite_config.get("review", {})

    # Expand environment variables
    review_dict = _expand_env_vars(review_dict)

    # Load base configuration
    config = ReviewConfig.from_dict(review_dict)

    # Apply profile if specified
    if profile:
        config = config.merge_with_profile(profile)

    # Apply CLI overrides if provided
    if cli_overrides:
        config = config.merge_with_cli(cli_overrides)

    logger.info(f"Loaded review config from {config_path}")
    if profile:
        logger.info(f"Applied profile: {profile}")
    if cli_overrides:
        logger.info(f"Applied CLI overrides: {list(cli_overrides.keys())}")

    return config
```

**Validation**:
- [ ] FileNotFoundError for missing config file
- [ ] Empty YAML returns defaults
- [ ] Review section extracted correctly
- [ ] Profile applied via merge_with_profile()
- [ ] CLI overrides applied via merge_with_cli()

---

### T015: Add environment variable expansion

**Purpose**: Expand ${VAR:default} syntax in config values.

**Implementation**:

```python
def _expand_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Expand environment variables in configuration dict.

    Supports ${VAR} and ${VAR:default} syntax.
    Recursively processes nested dictionaries and lists.

    Args:
        config: Configuration dict with potential env vars

    Returns:
        Config with env vars expanded

    Examples:
        "${API_KEY}" → os.environ["API_KEY"]
        "${API_KEY:default_value}" → "default_value" if API_KEY not set
        "${MODEL:gpt-4o-mini}" → "gpt-4o-mini" if MODEL not set
    """
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        return _expand_env_vars_string(config)
    else:
        return config


def _expand_env_vars_string(value: str) -> str:
    """Expand environment variables in a single string value.

    Args:
        value: String that may contain ${VAR} or ${VAR:default}

    Returns:
        String with env vars expanded

    Raises:
        ValueError: If required env var (no default) is not set
    """
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2)

        if var_name in os.environ:
            return os.environ[var_name]
        elif default_value is not None:
            return default_value
        else:
            raise ValueError(
                f"Required environment variable '{var_name}' is not set. "
                f"Set it or provide a default: ${{{var_name}:default_value}}"
            )

    return re.sub(pattern, replacer, value)
```

**Validation**:
- [ ] ${VAR} expands to environment variable
- [ ] ${VAR:default} uses default if not set
- [ ] Required env var raises ValueError if missing
- [ ] Nested dicts processed recursively
- [ ] Lists processed recursively
- [ ] Non-string values passed through unchanged

---

### T016: Implement configuration validation

**Purpose**: Add validation with clear error messages.

**Implementation**:

```python
def validate_config(config: ReviewConfig) -> None:
    """Validate configuration and raise helpful errors.

    Args:
        config: ReviewConfig to validate

    Raises:
        ValueError: If configuration is invalid with helpful message
    """
    errors = []

    # Validate profile exists if specified
    if config.profile and config.profile not in config.profiles:
        errors.append(
            f"Profile '{config.profile}' not found. "
            f"Available: {', '.join(config.profiles.keys())}"
        )

    # Validate prompt files exist if specified
    if config.prompts.system_prompt and not config.prompts.system_prompt.exists():
        errors.append(
            f"System prompt file not found: {config.prompts.system_prompt}"
        )
    if config.prompts.user_prompt and not config.prompts.user_prompt.exists():
        errors.append(
            f"User prompt file not found: {config.prompts.user_prompt}"
        )
    if config.prompts.result_template and not config.prompts.result_template.exists():
        errors.append(
            f"Result template file not found: {config.prompts.result_template}"
        )

    # Validate at least one check is enabled
    if not any([config.checks.security, config.checks.performance, config.checks.style]):
        errors.append(
            "At least one check must be enabled. "
            "Current: security=False, performance=False, style=False"
        )

    # Warn if context window too small
    if config.context.window_size < 1000:
        logger.warning(
            f"Context window size ({config.context.window_size}) is very small. "
            f"Consider using at least 1000 tokens."
        )

    if errors:
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
```

**Update load_config** to call validation:

```python
def load_config(...) -> ReviewConfig:
    # ... existing code ...

    # Validate final configuration
    validate_config(config)

    return config
```

**Validation**:
- [ ] Valid config passes without error
- [ ] Missing profile raises ValueError
- [ ] Missing prompt file raises ValueError
- [ ] All checks disabled raises ValueError
- [ ] Multiple errors reported together

---

### T017: Add error handling with clear messages

**Purpose**: Provide helpful error messages for common issues.

**Implementation**:

```python
class ConfigLoadError(Exception):
    """Base exception for config loading errors."""
    pass


class ConfigValidationError(ConfigLoadError):
    """Raised when configuration validation fails."""
    pass


class ConfigFileNotFoundError(ConfigLoadError):
    """Raised when config file is not found."""
    pass


def load_config_safe(
    config_path: Path,
    profile: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> ReviewConfig:
    """Load config with enhanced error handling.

    Provides helpful error messages and suggestions for common issues.

    Args:
        config_path: Path to config file
        profile: Optional profile name
        cli_overrides: Optional CLI overrides

    Returns:
        Loaded and validated ReviewConfig

    Raises:
        ConfigFileNotFoundError: With helpful message if file not found
        ConfigValidationError: With details if validation fails
        ConfigLoadError: For other loading errors
    """
    try:
        return load_config(config_path, profile, cli_overrides)
    except FileNotFoundError as e:
        raise ConfigFileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"\n"
            f"Please ensure config/debate_config.yaml exists.\n"
            f"You can copy the example from the project template."
        ) from e
    except ValueError as e:
        if "validation" in str(e).lower():
            raise ConfigValidationError(
                f"Configuration validation failed:\n{e}\n"
                f"\n"
                f"Please check your config/debate_config.yaml file."
            ) from e
        raise
    except yaml.YAMLError as e:
        raise ConfigLoadError(
            f"Failed to parse YAML file: {config_path}\n"
            f"Error: {e}\n"
            f"\n"
            f"Please check your YAML syntax."
        ) from e
```

**Validation**:
- [ ] ConfigFileNotFoundError raised with message for missing file
- [ ] ConfigValidationError raised for validation failures
- [ ] YAML errors caught and reported clearly
- [ ] Suggestions included in error messages

## Test Strategy

**Manual Testing** (before WP05):
```python
# Test 1: Load config file
config = load_config(Path("config/debate_config.yaml"))
assert config.profile == "balanced"

# Test 2: Env var expansion
os.environ["TEST_VAR"] = "test_value"
expanded = _expand_env_vars({"model": "${TEST_VAR}"})
assert expanded["model"] == "test_value"

# Test 3: Validation
try:
    validate_config(ReviewConfig(checks=CheckConfig(security=False, performance=False, style=False)))
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "At least one check" in str(e)
```

## Definition of Done

- [ ] `load_config()` loads YAML and returns ReviewConfig
- [ ] Environment variables expanded with ${VAR:default} syntax
- [ ] Validation errors are descriptive
- [ ] Error handling provides helpful messages
- [ ] ConfigFileNotFoundError, ConfigValidationError defined
- [ ] Logging added for config loading steps

## Reviewer Guidance

**Verify**:
1. YAML loading uses PyYAML safe_load
2. Env var expansion handles nested structures
3. Validation errors aggregate all issues
4. Error messages are actionable

**Common Issues**:
- Unsafe YAML loading → Use yaml.safe_load()
- Missing env vars → Provide helpful error
- Silent validation failures → Aggregate and report

## Risks

- **Low Risk**: Standard YAML loading and env var expansion
- **Mitigation**: Comprehensive error handling

## Activity Log

- 2026-02-21T11:12:33Z – claude – shell_pid=79802 – lane=doing – Assigned agent via workflow command
- 2026-02-21T11:13:52Z – claude – shell_pid=79802 – lane=for_review – Ready for review: Config loader with YAML parsing, env var expansion, and validation
- 2026-02-21T11:43:37Z – claude – shell_pid=79802 – lane=doing – Reviewing WP03
- 2026-02-21T11:43:48Z – claude – shell_pid=79802 – lane=done – Review passed: Config loader with env var expansion and validation complete
