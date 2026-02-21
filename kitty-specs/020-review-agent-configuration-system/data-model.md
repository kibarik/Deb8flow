# Data Model: Review Agent Configuration System

**Feature**: 020-review-agent-configuration-system
**Date**: 2025-02-21

## Overview

Документ описывает структуру данных для системы конфигурации review агента. Все конфигурационные объекты реализованы как immutable dataclass value objects, соответствующие паттерну существующего `RewriteConfig`.

## Entities

### 1. ReviewConfig (Root)

Основной объект конфигурации, содержащий все настройки review агента.

```python
@dataclass(frozen=True)
class ReviewConfig:
    """Root configuration for review agent."""

    # Profile selection
    profile: str = "balanced"

    # Sub-configurations
    llm: LLMConfig
    prompts: PromptConfig
    retry: RetryConfig
    checks: CheckConfig
    output: OutputConfig
    context: ContextConfig
    logging: LoggingConfig

    # Available profile presets
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "ReviewConfig":
        """Load from YAML config dict with profile merge."""
        ...

    def merge_with_profile(self, profile_name: str) -> "ReviewConfig":
        """Apply profile preset (hierarchical merge)."""
        ...

    def merge_with_cli(self, cli_overrides: Dict[str, Any]) -> "ReviewConfig":
        """Apply CLI flag overrides (highest priority)."""
        ...
```

### 2. LLMConfig

Параметры LLM провайдера и модели.

```python
@dataclass(frozen=True)
class LLMConfig:
    """LLM provider and model configuration."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens_request: int = 4000
    max_tokens_response: int = 2000
    timeout: int = 120

    def __post_init__(self):
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("temperature must be between 0.0 and 1.0")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
```

### 3. PromptConfig

Конфигурация промптов и шаблонов.

```python
@dataclass(frozen=True)
class PromptConfig:
    """Prompt and template configuration."""

    system_prompt: Optional[Path] = None
    user_prompt: Optional[Path] = None
    result_template: Optional[Path] = None
    variables: Dict[str, str] = field(default_factory=dict)
```

### 4. RetryConfig

Конфигурация retry политики.

```python
@dataclass(frozen=True)
class RetryConfig:
    """Retry policy configuration."""

    max_retries: int = 3
    backoff: str = "exponential"  # "exponential" | "linear" | "constant"
    initial_delay: float = 1.0

    def __post_init__(self):
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.backoff not in ("exponential", "linear", "constant"):
            raise ValueError(f"Invalid backoff: {self.backoff}")
```

### 5. CheckConfig

Включённые проверки.

```python
@dataclass(frozen=True)
class CheckConfig:
    """Check enable/disable configuration."""

    security: bool = True
    performance: bool = True
    style: bool = True
```

### 6. OutputConfig

Настройки форматирования вывода.

```python
@dataclass(frozen=True)
class OutputConfig:
    """Output format configuration."""

    format: str = "markdown"  # "markdown" | "json"
    include_snippets: bool = True
    max_comment_length: int = 500

    def __post_init__(self):
        if self.format not in ("markdown", "json"):
            raise ValueError(f"Invalid format: {self.format}")
```

### 7. ContextConfig

Настройки контекста и фильтрации.

```python
@dataclass(frozen=True)
class ContextConfig:
    """Context and filtering configuration."""

    window_size: int = 8000
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
```

### 8. LoggingConfig

Настройки логирования.

```python
@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"  # "ERROR" | "WARN" | "INFO" | "DEBUG"
    debug: bool = False

    def __post_init__(self):
        valid_levels = ("ERROR", "WARN", "INFO", "DEBUG")
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")
```

## Relationships

```
ReviewConfig (root)
├── profile: str
├── llm: LLMConfig
├── prompts: PromptConfig
│   └── variables: Dict[str, str]
├── retry: RetryConfig
├── checks: CheckConfig
├── output: OutputConfig
├── context: ContextConfig
├── logging: LoggingConfig
└── profiles: Dict[str, Dict]  # Profile presets
```

## Merge Strategy

Иерархический мердж конфигурации:

1. **Base Config**: Базовые настройки из `rewrite.review.*`
2. **Profile Override**: Применяется выбранный профиль (`rewrite.review.profiles.{profile}`)
   - Мердж по ключам (не полный override)
   - Только указанные поля заменяются
3. **CLI Override**: CLI флаги с наивысшим приоритетом

```python
# Pseudo-code
def load_review_config(config_path: Path, profile: str = None, cli_overrides: Dict = None):
    base = load_yaml(config_path)["rewrite"]["review"]
    config = ReviewConfig.from_dict(base)

    if profile:
        config = config.merge_with_profile(profile)

    if cli_overrides:
        config = config.merge_with_cli(cli_overrides)

    return config
```

## Placeholder Substitution

Поддерживаемые плейсхолдеры в промптах:

| Placeholder | Source | Example |
|------------|--------|---------|
| `{file_path}` | CLI argument | `/path/to/file.py` |
| `{project_name}` | `prompt_variables.project_name` | `Deb8flow` |
| `{team_context}` | `prompt_variables.team_context` | `Backend team` |
| `{*}` | Any key from `prompt_variables` | Custom variables |

## Validation Rules

1. **temperature**: 0.0 ≤ value ≤ 1.0
2. **top_p**: 0.0 ≤ value ≤ 1.0
3. **max_retries**: ≥ 0
4. **backoff**: "exponential" | "linear" | "constant"
5. **format**: "markdown" | "json"
6. **log_level**: "ERROR" | "WARN" | "INFO" | "DEBUG"
7. **profile**: Должен существовать в `profiles` dict

## State Transitions

```
[YAML File]
    ↓ from_dict()
[ReviewConfig (base)]
    ↓ merge_with_profile(profile_name)
[ReviewConfig (base + profile)]
    ↓ merge_with_cli(cli_overrides)
[ReviewConfig (final)]
```

## Error Handling

| Error Type | Condition | Handling |
|-----------|-----------|----------|
| `ValueError` | Invalid temperature/top_p range | Raise with descriptive message |
| `ValueError` | Invalid backoff/format/level | Raise with valid options |
| `KeyError` | Profile not found | Raise with available profiles |
| `FileNotFoundError` | Prompt file not found | Raise with file path |
| `TypeError` | Wrong type for config value | Raise with expected type |
