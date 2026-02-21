---
work_package_id: WP01
title: Review Config Value Objects
lane: "for_review"
dependencies: []
base_branch: main
base_commit: 63396379c2cf6a54188f3252c15d3fee32db3f19
created_at: '2026-02-21T10:59:29.536139+00:00'
subtasks: [T001, T002, T003, T004, T005, T006, T007, T008]
shell_pid: "78439"
agent: "claude"
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP01: Review Config Value Objects

**Priority**: P0 (Foundational)
**Estimated Size**: ~420 lines (8 subtasks × ~50 lines each)
**Implementation Command**: `spec-kitty implement WP01`

## Objective

Create all dataclass value objects for review configuration following the existing `RewriteConfig` pattern in `src/rewrite/domain/value_objects.py`.

## Context

The Review Agent Configuration System requires multiple configuration objects to manage LLM settings, prompts, retry policies, output formatting, and more. All objects follow the immutable dataclass pattern established by `RewriteConfig`.

**Reference Files**:
- Existing pattern: `src/rewrite/domain/value_objects.py` (RewriteConfig)
- Data model spec: `kitty-specs/020-review-agent-configuration-system/data-model.md`

## Subtasks

### T001: Create LLMConfig dataclass with validation

**Purpose**: Define LLM provider and model configuration with validation.

**Implementation**:

Create `LLMConfig` in `src/rewrite/domain/review_config.py`:

```python
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

@dataclass(frozen=True)
class LLMConfig:
    """LLM provider and model configuration.

    Attributes:
        provider: LLM provider name (e.g., "openai", "anthropic")
        model: Model identifier (e.g., "gpt-4o-mini")
        temperature: Sampling temperature (0.0 - 1.0)
        top_p: Nucleus sampling parameter (0.0 - 1.0)
        max_tokens_request: Max tokens for outgoing requests
        max_tokens_response: Max tokens for response generation
        timeout: Request timeout in seconds
    """
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens_request: int = 4000
    max_tokens_response: int = 2000
    timeout: int = 120

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(
                f"temperature must be between 0.0 and 1.0, got {self.temperature}"
            )
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError(
                f"top_p must be between 0.0 and 1.0, got {self.top_p}"
            )
        if self.max_tokens_request < 1:
            raise ValueError("max_tokens_request must be positive")
        if self.max_tokens_response < 1:
            raise ValueError("max_tokens_response must be positive")
        if self.timeout < 1:
            raise ValueError("timeout must be positive")
```

**Validation**:
- [ ] ValueError raised for temperature outside 0.0-1.0
- [ ] ValueError raised for top_p outside 0.0-1.0
- [ ] All defaults are valid

---

### T002: Create PromptConfig dataclass

**Purpose**: Define prompt and template configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class PromptConfig:
    """Prompt and template configuration.

    Attributes:
        system_prompt: Path to system prompt template (optional)
        user_prompt: Path to user prompt template (optional)
        result_template: Path to result output template (optional)
        variables: Dictionary of variables for placeholder substitution
    """
    system_prompt: Optional[Path] = None
    user_prompt: Optional[Path] = None
    result_template: Optional[Path] = None
    variables: Dict[str, str] = field(default_factory=dict)
```

**Validation**:
- [ ] All fields are optional with None defaults
- [ ] variables defaults to empty dict

---

### T003: Create RetryConfig dataclass with validation

**Purpose**: Define retry policy configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class RetryConfig:
    """Retry policy configuration.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff: Backoff strategy - "exponential", "linear", or "constant"
        initial_delay: Initial delay in seconds before first retry
    """
    max_retries: int = 3
    backoff: str = "exponential"
    initial_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError(
                f"max_retries must be non-negative, got {self.max_retries}"
            )
        if self.backoff not in ("exponential", "linear", "constant"):
            raise ValueError(
                f"backoff must be 'exponential', 'linear', or 'constant', "
                f"got '{self.backoff}'"
            )
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")
```

**Validation**:
- [ ] ValueError for negative max_retries
- [ ] ValueError for invalid backoff type
- [ ] ValueError for negative initial_delay

---

### T004: Create CheckConfig dataclass

**Purpose**: Define check enable/disable configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class CheckConfig:
    """Check enable/disable configuration.

    Attributes:
        security: Enable security checks
        performance: Enable performance checks
        style: Enable style checks
    """
    security: bool = True
    performance: bool = True
    style: bool = True
```

**Validation**:
- [ ] All fields default to True
- [ ] All fields accept boolean values

---

### T005: Create OutputConfig dataclass with validation

**Purpose**: Define output format configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class OutputConfig:
    """Output format configuration.

    Attributes:
        format: Output format - "markdown" or "json"
        include_snippets: Include code snippets in output
        max_comment_length: Maximum length for individual comments
    """
    format: str = "markdown"
    include_snippets: bool = True
    max_comment_length: int = 500

    def __post_init__(self):
        """Validate configuration values."""
        if self.format not in ("markdown", "json"):
            raise ValueError(
                f"format must be 'markdown' or 'json', got '{self.format}'"
            )
        if self.max_comment_length < 1:
            raise ValueError("max_comment_length must be positive")
```

**Validation**:
- [ ] ValueError for invalid format
- [ ] ValueError for non-positive max_comment_length

---

### T006: Create ContextConfig dataclass

**Purpose**: Define context and filtering configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class ContextConfig:
    """Context and filtering configuration.

    Attributes:
        window_size: Maximum context window size in tokens
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
    """
    window_size: int = 8000
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
```

**Validation**:
- [ ] window_size defaults to 8000
- [ ] Patterns default to empty lists

---

### T007: Create LoggingConfig dataclass with validation

**Purpose**: Define logging configuration.

**Implementation**:

```python
@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration.

    Attributes:
        level: Log level - "ERROR", "WARN", "INFO", or "DEBUG"
        debug: Enable debug mode with statistics
    """
    level: str = "INFO"
    debug: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        valid_levels = ("ERROR", "WARN", "INFO", "DEBUG")
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"level must be one of {valid_levels}, got '{self.level}'"
            )
```

**Validation**:
- [ ] ValueError for invalid log level
- [ ] Case-insensitive level validation (accepts "info", "INFO", "Info")

---

### T008: Create ReviewConfig root dataclass with from_dict()

**Purpose**: Create root configuration object that contains all sub-configurations and loads from YAML dict.

**Implementation**:

```python
@dataclass(frozen=True)
class ReviewConfig:
    """Root configuration for review agent.

    This is the main configuration object that contains all sub-configurations
    and handles loading from YAML dictionary structure.

    Attributes:
        profile: Default profile name (strict/balanced/lenient)
        llm: LLM configuration
        prompts: Prompt configuration
        retry: Retry policy configuration
        checks: Check configuration
        output: Output configuration
        context: Context configuration
        logging: Logging configuration
        profiles: Dictionary of profile presets for merge operations
    """
    profile: str = "balanced"
    llm: LLMConfig = field(default_factory=LLMConfig)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    checks: CheckConfig = field(default_factory=CheckConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "ReviewConfig":
        """Create ReviewConfig from YAML config dictionary.

        Expected structure:
        {
            "profile": "balanced",
            "llm": {"provider": "openai", "model": "gpt-4o-mini", ...},
            "prompts": {"system_prompt": "path/to/file.md", ...},
            ...
        }

        Args:
            config: Dictionary from loaded YAML file

        Returns:
            ReviewConfig instance with values extracted or defaults

        Raises:
            ValueError: If configuration values are invalid
            TypeError: If configuration has wrong types
        """
        # Extract LLM config
        llm_dict = config.get("llm", {})
        llm = LLMConfig(
            provider=llm_dict.get("provider", "openai"),
            model=llm_dict.get("model", "gpt-4o-mini"),
            temperature=llm_dict.get("temperature", 0.7),
            top_p=llm_dict.get("top_p", 0.9),
            max_tokens_request=llm_dict.get("max_tokens_request", 4000),
            max_tokens_response=llm_dict.get("max_tokens_response", 2000),
            timeout=llm_dict.get("timeout", 120),
        )

        # Extract prompts config
        prompts_dict = config.get("prompts", {})
        prompts = PromptConfig(
            system_prompt=Path(prompts_dict["system"]) if prompts_dict.get("system") else None,
            user_prompt=Path(prompts_dict["user"]) if prompts_dict.get("user") else None,
            result_template=Path(prompts_dict["result_template"]) if prompts_dict.get("result_template") else None,
            variables=prompts_dict.get("variables", {}),
        )

        # Extract retry config
        retry_dict = config.get("retry", {})
        retry = RetryConfig(
            max_retries=retry_dict.get("max_retries", 3),
            backoff=retry_dict.get("backoff", "exponential"),
            initial_delay=retry_dict.get("initial_delay", 1.0),
        )

        # Extract checks config
        checks_dict = config.get("checks", {})
        checks = CheckConfig(
            security=checks_dict.get("security", True),
            performance=checks_dict.get("performance", True),
            style=checks_dict.get("style", True),
        )

        # Extract output config
        output_dict = config.get("output", {})
        output = OutputConfig(
            format=output_dict.get("format", "markdown"),
            include_snippets=output_dict.get("include_snippets", True),
            max_comment_length=output_dict.get("max_comment_length", 500),
        )

        # Extract context config
        context_dict = config.get("context", {})
        context = ContextConfig(
            window_size=context_dict.get("window_size", 8000),
            include_patterns=context_dict.get("include_patterns", []),
            exclude_patterns=context_dict.get("exclude_patterns", []),
        )

        # Extract logging config
        logging_dict = config.get("logging", {})
        logging = LoggingConfig(
            level=logging_dict.get("level", "INFO"),
            debug=logging_dict.get("debug", False),
        )

        # Extract profiles
        profiles = config.get("profiles", {})

        return cls(
            profile=config.get("profile", "balanced"),
            llm=llm,
            prompts=prompts,
            retry=retry,
            checks=checks,
            output=output,
            context=context,
            logging=logging,
            profiles=profiles,
        )
```

**Validation**:
- [ ] from_dict() loads empty dict with all defaults
- [ ] from_dict() loads partial config with defaults for missing values
- [ ] from_dict() loads full config correctly
- [ ] Validation errors propagate from sub-configs
- [ ] Path objects created for prompt files when specified

**Files Modified/Created**:
- `src/rewrite/domain/review_config.py` (new file, ~250 lines)

**Import Statement**:
Add to `src/rewrite/domain/__init__.py`:
```python
from .review_config import (
    ReviewConfig,
    LLMConfig,
    PromptConfig,
    RetryConfig,
    CheckConfig,
    OutputConfig,
    ContextConfig,
    LoggingConfig,
)
```

## Test Strategy

**Manual Testing** (before WP05):
```python
# Test 1: Create with defaults
config = LLMConfig()
assert config.temperature == 0.7

# Test 2: Validation
try:
    LLMConfig(temperature=1.5)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "temperature" in str(e)

# Test 3: from_dict loading
config_dict = {
    "llm": {"temperature": 0.5},
    "checks": {"security": False}
}
review_config = ReviewConfig.from_dict(config_dict)
assert review_config.llm.temperature == 0.5
assert review_config.checks.security == False
```

## Definition of Done

- [ ] All 8 dataclasses defined in `src/rewrite/domain/review_config.py`
- [ ] All validation rules implemented in `__post_init__`
- [ ] `ReviewConfig.from_dict()` successfully parses nested dict structure
- [ ] ValueError raised for all invalid inputs
- [ ] Default values match specification
- [ ] Imports work correctly from `src.rewrite.domain.review_config`
- [ ] Code style matches existing `RewriteConfig` pattern
- [ ] File is type-annotated with mypy-compatible hints

## Reviewer Guidance

**Verify**:
1. All dataclasses use `frozen=True` for immutability
2. Validation error messages are descriptive
3. `from_dict()` handles missing keys with defaults
4. Type hints are complete and correct
5. Docstrings follow project style

**Common Issues**:
- Missing `frozen=True` → Dataclass becomes mutable
- Incomplete validation → Invalid values accepted
- Wrong default values → Doesn't match spec

## Risks

- **Low Risk**: Follows existing patterns
- **Mitigation**: Reference `RewriteConfig` implementation for style consistency

## Activity Log

- 2026-02-21T10:59:29Z – claude – shell_pid=78439 – lane=doing – Assigned agent via workflow command
- 2026-02-21T11:00:46Z – claude – shell_pid=78439 – lane=for_review – Ready for review: All 8 review config value objects implemented with validation
