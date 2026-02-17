---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
  - "T004"
  - "T005"
  - "T006"
title: "Configuration Data Model"
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
---

# Work Package Prompt: WP01 – Configuration Data Model

## Objectives & Success Criteria

Create the core configuration data structures and YAML loader using Python standard library. This work package establishes the foundation for all configuration-driven functionality.

**Success Criteria**:
- All configuration dataclasses (DebateConfig, WorkflowConfig, RoleConfig, etc.) are defined with proper type hints
- YAML loader parses valid configuration files using `yaml.safe_load()`
- Configuration validation catches all required field errors with clear, actionable messages
- Prompt resolution correctly handles inline prompts, file references, and precedence rules
- Error classes provide specific error types with helpful messages
- Public API is exported through module `__init__.py`

## Context & Constraints

**Supporting Documents**:
- Constitution: `.kittify/memory/constitution.md` - Minimal dependencies principle, TDD approach
- Spec: `kitty-specs/014-flexible-debate-config-yaml/spec.md` - FR-001 through FR-025
- Data Model: `kitty-specs/014-flexible-debate-config-yaml/data-model.md` - Complete entity definitions
- Schema Contract: `kitty-specs/014-flexible-debate-config-yaml/contracts/schema.md` - YAML schema and validation rules
- Research: `kitty-specs/014-flexible-debate-config-yaml/research.md` - Standard library YAML parsing decision

**Architectural Decisions**:
- Use Python standard library only (`yaml.safe_load()`) - no Pydantic or other dependencies
- Use `dataclasses` for type safety and clarity
- Preserve backward compatibility - default config must match current hardcoded behavior
- Configuration validation must provide specific field-level error messages

**Constraints**:
- Must use `yaml.safe_load()` (not `yaml.load()`) to prevent code injection
- Prompt files are resolved relative to config file directory
- `prompt_file` takes precedence over inline `prompt`
- All model references must exist in `models` dict

## Subtasks & Detailed Guidance

### Subtask T001 – Create Configuration Dataclasses

**Purpose**: Define the core data structures for configuration with proper type hints and validation.

**Steps**:

1. Create `configurations/debate_config.py` with the following dataclasses:

```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path

@dataclass
class TriggerConfig:
    """Defines when an auxiliary role participates in the debate."""
    after_round: Optional[int] = None
    on_fact_check: Optional[bool] = None

@dataclass
class RoleConfig:
    """Definition of a debate participant role."""
    name: str
    side: str  # "pro", "con", "neutral", "auxiliary"
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None
    model: str = "deepseek-chat"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    trigger: Optional[TriggerConfig] = None

@dataclass
class ModelConfig:
    """LLM model configuration."""
    provider: str  # "openai", "azure", "zhipu", "requesty"
    model_name: str
    api_key_env: str
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = None

@dataclass
class WorkflowConfig:
    """Debate workflow parameters."""
    mode: str  # "standard", "document"
    rounds: int = 3

@dataclass
class FactCheckingConfig:
    """Fact-checking configuration."""
    enabled: bool = True
    max_failures: int = 3

@dataclass
class DebateConfig:
    """Root configuration object loaded from YAML."""
    workflow: WorkflowConfig
    roles: List[RoleConfig]
    auxiliary_roles: Optional[List[RoleConfig]] = None
    models: Dict[str, ModelConfig] = None
    fact_checking: Optional[FactCheckingConfig] = None
```

2. Add docstrings to each dataclass explaining their purpose
3. Include type hints for all fields
4. Set appropriate defaults for optional fields

**Files**:
- `configurations/debate_config.py` (new file, ~150 lines)

**Parallel?**: No - this is the foundation for other subtasks

**Notes**:
- Follow the data model specification exactly
- Use Optional[T] for fields that may not be present
- Default values should match the schema contract

---

### Subtask T002 – Implement YAML Configuration Loader

**Purpose**: Load and parse YAML configuration files safely using standard library.

**Steps**:

1. Add `load_config()` function to `configurations/debate_config.py`:

```python
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str) -> DebateConfig:
    """
    Load debate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        DebateConfig object

    Raises:
        ConfigNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML syntax is invalid
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise ConfigNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with open(config_file, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)

    # Convert dict to DebateConfig
    return parse_config_dict(raw_data, config_file)
```

2. Add `parse_config_dict()` function to convert raw dict to dataclasses:

```python
def parse_config_dict(data: Dict[str, Any], config_file: Path) -> DebateConfig:
    """Parse configuration dict into DebateConfig object."""
    # Parse workflow
    workflow_data = data.get('workflow', {})
    workflow = WorkflowConfig(
        mode=workflow_data.get('mode', 'standard'),
        rounds=workflow_data.get('rounds', 3)
    )

    # Parse models
    models_data = data.get('models', {})
    models = {
        name: ModelConfig(
            provider=model['provider'],
            model_name=model['model_name'],
            api_key_env=model['api_key_env'],
            azure_endpoint=model.get('azure_endpoint'),
            api_version=model.get('api_version')
        )
        for name, model in models_data.items()
    }

    # Parse roles
    roles_data = data.get('roles', [])
    roles = [parse_role_config(role) for role in roles_data]

    # Parse auxiliary roles
    aux_roles_data = data.get('auxiliary_roles', [])
    auxiliary_roles = [parse_role_config(role) for role in aux_roles_data] if aux_roles_data else None

    # Parse fact-checking
    fc_data = data.get('fact_checking', {})
    fact_checking = FactCheckingConfig(
        enabled=fc_data.get('enabled', True),
        max_failures=fc_data.get('max_failures', 3)
    ) if fc_data else None

    return DebateConfig(
        workflow=workflow,
        roles=roles,
        auxiliary_roles=auxiliary_roles,
        models=models,
        fact_checking=fact_checking
    )

def parse_role_config(role_data: Dict[str, Any]) -> RoleConfig:
    """Parse role configuration dict into RoleConfig object."""
    trigger_data = role_data.get('trigger')
    trigger = TriggerConfig(
        after_round=trigger_data.get('after_round'),
        on_fact_check=trigger_data.get('on_fact_check')
    ) if trigger_data else None

    return RoleConfig(
        name=role_data['name'],
        side=role_data['side'],
        prompt=role_data.get('prompt'),
        prompt_file=role_data.get('prompt_file'),
        model=role_data.get('model', 'deepseek-chat'),
        temperature=role_data.get('temperature', 0.7),
        max_tokens=role_data.get('max_tokens', 1000),
        trigger=trigger
    )
```

**Files**:
- `configurations/debate_config.py` (modify, add ~100 lines)

**Parallel?**: Yes - can proceed once T001 dataclass structure is defined

**Notes**:
- Use `yaml.safe_load()` to prevent code injection
- Handle missing optional fields with defaults
- Preserve the config_file Path for use in prompt resolution

---

### Subtask T003 – Implement Configuration Validation

**Purpose**: Validate configuration structure and values with clear error messages.

**Steps**:

1. Add validation function to `configurations/debate_config.py`:

```python
def validate_config(config: DebateConfig) -> None:
    """
    Validate configuration object.

    Args:
        config: DebateConfig to validate

    Raises:
        ValidationError: If configuration is invalid
    """
    errors = []

    # Validate workflow
    if config.workflow.mode not in ["standard", "document"]:
        errors.append(f"Invalid workflow mode: {config.workflow.mode}. Must be 'standard' or 'document'")

    if config.workflow.rounds < 1:
        errors.append(f"Rounds must be >= 1, got: {config.workflow.rounds}")

    # Validate roles
    role_names = set()
    has_pro = False
    has_con = False

    for role in config.roles:
        # Check unique names
        if role.name in role_names:
            errors.append(f"Duplicate role name: {role.name}")
        role_names.add(role.name)

        # Check side
        if role.side not in ["pro", "con", "neutral"]:
            errors.append(f"Invalid side for {role.name}: {role.side}. Must be 'pro', 'con', or 'neutral'")

        # Track required sides
        if role.side == "pro":
            has_pro = True
        elif role.side == "con":
            has_con = True

        # Check prompt
        if not role.prompt and not role.prompt_file:
            errors.append(f"Role {role.name} has no prompt (need 'prompt' or 'prompt_file')")

        # Check model reference
        if role.model not in config.models:
            errors.append(f"Model not found for role {role.name}: {role.model}")

        # Check temperature range
        if role.temperature < 0.0 or role.temperature > 2.0:
            errors.append(f"Temperature for {role.name} out of range [0.0, 2.0]: {role.temperature}")

        # Check max_tokens
        if role.max_tokens <= 0:
            errors.append(f"max_tokens for {role.name} must be > 0: {role.max_tokens}")

    # Check required roles
    if not has_pro:
        errors.append("Missing required role with side='pro'")
    if not has_con:
        errors.append("Missing required role with side='con'")

    # Validate auxiliary roles
    if config.auxiliary_roles:
        for role in config.auxiliary_roles:
            if not role.trigger:
                errors.append(f"Auxiliary role {role.name} missing trigger condition")
            if role.side != "auxiliary":
                errors.append(f"Auxiliary role {role.name} must have side='auxiliary'")

    if errors:
        raise ValidationError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
```

2. Update `load_config()` to call validation:

```python
def load_config(config_path: str) -> DebateConfig:
    # ... existing code ...
    config = parse_config_dict(raw_data, config_file)
    validate_config(config)  # Add this line
    return config
```

**Files**:
- `configurations/debate_config.py` (modify, add ~80 lines)

**Parallel?**: Yes - can proceed once T001 dataclass structure is defined

**Notes**:
- Collect all errors before raising (don't fail on first error)
- Error messages should be specific: include field name and expected value
- Follow the validation rules from the schema contract

---

### Subtask T004 – Implement Prompt Resolution

**Purpose**: Resolve role prompts from inline text or external files with correct precedence.

**Steps**:

1. Add prompt resolution function to `configurations/debate_config.py`:

```python
def resolve_prompt(role: RoleConfig, config_dir: Path) -> str:
    """
    Resolve role prompt from inline text or external file.

    Precedence: prompt_file > inline prompt

    Args:
        role: Role configuration
        config_dir: Directory containing the config file (for resolving relative paths)

    Returns:
        Resolved prompt text

    Raises:
        PromptFileNotFoundError: If prompt_file doesn't exist
        ValidationError: If neither prompt nor prompt_file is specified
    """
    # Check prompt_file first (highest priority)
    if role.prompt_file:
        prompt_path = config_dir / role.prompt_file
        if not prompt_path.exists():
            raise PromptFileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Referenced from role: {role.name}"
            )
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            raise ValidationError(
                f"Prompt file encoding error (not UTF-8): {prompt_path}"
            )

    # Fall back to inline prompt
    if role.prompt:
        return role.prompt

    # Neither specified
    raise ValidationError(
        f"Role {role.name} has no prompt. "
        f"Specify either 'prompt' or 'prompt_file'."
    )

def resolve_all_prompts(config: DebateConfig, config_file: Path) -> DebateConfig:
    """
    Resolve all role prompts in configuration.

    Args:
        config: Configuration with unresolved prompts
        config_file: Path to config file (for resolving relative paths)

    Returns:
        Configuration with resolved prompts (stores in new field)
    """
    config_dir = config_file.parent

    # Resolve primary role prompts
    for role in config.roles:
        role.resolved_prompt = resolve_prompt(role, config_dir)

    # Resolve auxiliary role prompts
    if config.auxiliary_roles:
        for role in config.auxiliary_roles:
            role.resolved_prompt = resolve_prompt(role, config_dir)

    return config
```

2. Update `load_config()` to resolve prompts:

```python
def load_config(config_path: str) -> DebateConfig:
    # ... existing code ...
    validate_config(config)
    config = resolve_all_prompts(config, config_file)  # Add this line
    return config
```

**Files**:
- `configurations/debate_config.py` (modify, add ~60 lines)

**Parallel?**: Yes - can proceed once T001 dataclass structure is defined

**Notes**:
- Prompt files are resolved relative to config file directory
- Support UTF-8 encoding only (per spec assumption)
- `prompt_file` takes precedence over inline `prompt`
- Add `resolved_prompt` field to RoleConfig at runtime

---

### Subtask T005 – Add Configuration Error Classes

**Purpose**: Define specific exception types for configuration errors with helpful messages.

**Steps**:

1. Add error classes to `configurations/debate_config.py`:

```python
class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass

class ConfigNotFoundError(ConfigError):
    """Raised when configuration file doesn't exist."""
    pass

class ValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass

class PromptFileNotFoundError(ConfigError):
    """Raised when referenced prompt file doesn't exist."""
    pass

class ModelNotFoundError(ConfigError):
    """Raised when referenced model doesn't exist in models dict."""
    pass
```

2. Update validation and prompt resolution to use these error types:

```python
# In validate_config(), for model reference check:
if role.model not in config.models:
    raise ModelNotFoundError(
        f"Model not found for role {role.name}: {role.model}. "
        f"Available models: {list(config.models.keys())}"
    )
```

**Files**:
- `configurations/debate_config.py` (modify, add ~30 lines)

**Parallel?**: Yes - can proceed once T001 dataclass structure is defined

**Notes**:
- All config errors inherit from `ConfigError` base class
- Error messages should include file paths and available options
- These exceptions will be caught by CLI for user-friendly display

---

### Subtask T006 – Create Module Init File

**Purpose**: Export public API through module `__init__.py`.

**Steps**:

1. Create `configurations/__init__.py`:

```python
"""
Debate configuration system.

This module provides YAML-based configuration for debate roles,
workflows, and models.
"""

from .debate_config import (
    DebateConfig,
    WorkflowConfig,
    RoleConfig,
    TriggerConfig,
    ModelConfig,
    FactCheckingConfig,
    load_config,
    validate_config,
    resolve_prompt,
    ConfigError,
    ConfigNotFoundError,
    ValidationError,
    PromptFileNotFoundError,
    ModelNotFoundError,
)

__all__ = [
    "DebateConfig",
    "WorkflowConfig",
    "RoleConfig",
    "TriggerConfig",
    "ModelConfig",
    "FactCheckingConfig",
    "load_config",
    "validate_config",
    "resolve_prompt",
    "ConfigError",
    "ConfigNotFoundError",
    "ValidationError",
    "PromptFileNotFoundError",
    "ModelNotFoundError",
]
```

**Files**:
- `configurations/__init__.py` (new file, ~35 lines)

**Parallel?**: No - depends on all previous subtasks

**Notes**:
- Keep imports minimal (only what users need)
- Include docstring explaining the module
- Maintain alphabetical order in `__all__`

## Test Strategy

Tests will be created in WP02 (Configuration Tests). Focus on writing clean, testable code structure:

- Each function should have a single responsibility
- Error paths should be clear and testable
- Use dependency injection for file system operations (where possible)

## Risks & Mitigations

**Risk**: YAML parsing errors may produce cryptic messages
**Mitigation**: Catch `yaml.YAMLError` and wrap with context about file path and line number

**Risk**: Prompt file encoding issues
**Mitigation**: Explicitly handle `UnicodeDecodeError` and suggest UTF-8 encoding

**Risk**: Circular imports in configurations module
**Mitigation**: Keep `__init__.py` minimal; avoid importing submodules that import back

## Review Guidance

**Key Acceptance Checkpoints**:
- [ ] All dataclasses have proper type hints and docstrings
- [ ] `yaml.safe_load()` is used (not `yaml.load()`)
- [ ] Validation catches all required field errors from schema contract
- [ ] Prompt resolution implements correct precedence (file > inline)
- [ ] Error classes inherit from `ConfigError` base
- [ ] Module `__init__.py` exports clean public API
- [ ] Code is self-documenting with clear variable names

**Context for Reviewers**:
- Data model spec: `kitty-specs/014-flexible-debate-config-yaml/data-model.md`
- Schema contract: `kitty-specs/014-flexible-debate-config-yaml/contracts/schema.md`
- Constitution: Minimal dependencies, self-documenting code

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created

---

### Valid lanes

To change lane: `spec-kitty agent tasks move-task WP01 --to <lane>`
Valid lanes: `planned`, `doing`, `for_review`, `done`
