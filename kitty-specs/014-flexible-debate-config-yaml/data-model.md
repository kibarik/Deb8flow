# Data Model: Flexible Debate Configuration

**Feature**: #014 - Flexible Debate Configuration with YAML
**Date**: 2025-02-17
**Status**: Phase 1 Design

## Overview

This document defines the data structures and entities for the YAML-based configuration system. The data model supports hierarchical configuration with validation, type safety, and clear error messages.

## Core Entities

### 1. DebateConfig (Root Configuration)

The root configuration object loaded from `debate.yml` or custom config files.

**Attributes**:
- `workflow` (WorkflowConfig): Workflow mode and round configuration
- `roles` (List[RoleConfig]): Primary debate participant roles
- `auxiliary_roles` (Optional[List[RoleConfig]]): Optional auxiliary participants
- `models` (Dict[str, ModelConfig]): LLM model configurations
- `fact_checking` (Optional[FactCheckingConfig]): Fact-checking settings

**Validation Rules**:
- `workflow.mode` must be "standard" or "document"
- `workflow.rounds` must be >= 1
- At least two roles must be defined (one "pro", one "con")
- All referenced model names must exist in `models` dict
- If `prompt_file` is specified, file must exist and be readable

**Example**:
```yaml
workflow:
  mode: standard
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: "You argue for..."
    model: deepseek-chat

models:
  deepseek-chat:
    provider: requesty
    api_key_env: REQ_API_KEY
```

---

### 2. WorkflowConfig

Debate workflow parameters controlling mode and duration.

**Attributes**:
- `mode` (str): Workflow mode - "standard" or "document"
- `rounds` (int): Number of debate rounds to execute

**Validation Rules**:
- `mode` ∈ {"standard", "document"}
- `rounds` ∈ ℕ, rounds >= 1

**State Transitions**:
- Config is immutable after loading
- Different modes use different workflow classes (DebateWorkflow vs DocumentDebateWorkflow)

---

### 3. RoleConfig

Definition of a debate participant role.

**Attributes**:
- `name` (str): Unique identifier for the role
- `side` (str): Debate affiliation - "pro", "con", "neutral", or "auxiliary"
- `prompt` (Optional[str]): Inline role prompt text
- `prompt_file` (Optional[str]): Path to external prompt file
- `model` (str): Reference to model configuration name
- `temperature` (Optional[float]): Sampling temperature (default: 0.7)
- `max_tokens` (Optional[int]): Token limit for responses (default: 1000)
- `trigger` (Optional[TriggerConfig]): For auxiliary roles, when to participate

**Validation Rules**:
- `name` must be unique across all roles
- `side` ∈ {"pro", "con", "neutral", "auxiliary"}
- At least one of `prompt` or `prompt_file` must be specified
- If both specified, `prompt_file` takes precedence
- `temperature` ∈ [0.0, 2.0]
- `max_tokens` > 0
- Auxiliary roles MUST specify `trigger`
- Primary roles MUST NOT specify `trigger`

**Prompt Resolution**:
```python
def get_prompt(role: RoleConfig, config_dir: Path) -> str:
    """
    Resolve prompt text from inline or file source.
    Precedence: prompt_file > inline prompt
    """
    if role.prompt_file:
        path = config_dir / role.prompt_file
        return path.read_text(encoding='utf-8')
    elif role.prompt:
        return role.prompt
    else:
        raise ValidationError(f"Role {role.name} has no prompt")
```

---

### 4. TriggerConfig

Defines when an auxiliary role should participate in the debate.

**Attributes**:
- `after_round` (Optional[int]): Participate after this round number
- `on_fact_check` (Optional[bool]): Participate after fact-checking

**Validation Rules**:
- At least one trigger condition must be specified
- `after_round` must be >= 1
- Multiple triggers can be combined (AND logic)

**Examples**:
```yaml
# Participate after round 2
trigger:
  after_round: 2

# Participate after fact-check
trigger:
  on_fact_check: true

# Participate after round 2 AND after fact-check
trigger:
  after_round: 2
  on_fact_check: true
```

---

### 5. ModelConfig

LLM model configuration with provider-specific settings.

**Attributes**:
- `provider` (str): LLM provider - "openai", "azure", "zhipu", "requesty"
- `model_name` (str): Model identifier (e.g., "gpt-4", "deepseek-chat")
- `api_key_env` (str): Environment variable name containing API key
- `azure_endpoint` (Optional[str]): Azure OpenAI endpoint (if provider=azure)
- `api_version` (Optional[str]): Azure API version (if provider=azure)

**Validation Rules**:
- `provider` ∈ {"openai", "azure", "zhipu", "requesty"}
- `api_key_env` must be set in environment or raise error
- For `provider="azure"`, `azure_endpoint` and `api_version` are required

---

### 6. FactCheckingConfig

Configuration for fact-checking behavior.

**Attributes**:
- `enabled` (bool): Whether fact-checking is active
- `max_failures` (int): Maximum fact-check failures before disqualification

**Validation Rules**:
- `max_failures` >= 0

---

## Data Relationships

```
DebateConfig (root)
├── WorkflowConfig
│   ├── mode: "standard" | "document"
│   └── rounds: int
│
├── List[RoleConfig] (roles)
│   ├── RoleConfig[0] -> ModelConfig (via model name)
│   ├── RoleConfig[1] -> ModelConfig (via model name)
│   └── ...
│
├── List[RoleConfig] (auxiliary_roles, optional)
│   └── RoleConfig -> TriggerConfig
│
├── Dict[str, ModelConfig] (models)
│   ├── "deepseek-chat" -> ModelConfig
│   └── ...
│
└── FactCheckingConfig (optional)
```

## Configuration Loading Flow

```python
# 1. Load YAML file
raw_data = yaml.safe_load(config_file_path)

# 2. Parse into dataclasses
config = DebateConfig.from_dict(raw_data, config_file_path)

# 3. Validate
validate_config(config)

# 4. Resolve prompts
for role in config.roles:
    role.resolved_prompt = resolve_prompt(role, config_file_path.parent)

# 5. Create LLM configs
llm_configs = create_llm_configs(config.models)
```

## Error Handling

| Error Type | Condition | Error Message |
|-----------|-----------|---------------|
| `ConfigNotFoundError` | Config file doesn't exist | "Configuration file not found: {path}" |
| `ValidationError` | Required field missing | "Missing required field: {field_name}" |
| `ValidationError` | Invalid value for field | "Invalid {field_name}: {value}. Expected: {expected}" |
| `ValidationError` | Duplicate role name | "Duplicate role name: {name}" |
| `PromptFileNotFoundError` | Prompt file doesn't exist | "Prompt file not found: {path}" |
| `ModelNotFoundError` | Referenced model doesn't exist | "Model not found: {name}" |

## Type Definitions

```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path

@dataclass
class TriggerConfig:
    after_round: Optional[int] = None
    on_fact_check: Optional[bool] = None

@dataclass
class RoleConfig:
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
    provider: str  # "openai", "azure", "zhipu", "requesty"
    model_name: str
    api_key_env: str
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = None

@dataclass
class WorkflowConfig:
    mode: str  # "standard", "document"
    rounds: int = 3

@dataclass
class FactCheckingConfig:
    enabled: bool = True
    max_failures: int = 3

@dataclass
class DebateConfig:
    workflow: WorkflowConfig
    roles: List[RoleConfig]
    auxiliary_roles: Optional[List[RoleConfig]] = None
    models: Dict[str, ModelConfig] = None
    fact_checking: Optional[FactCheckingConfig] = None
```

## Validation Pseudocode

```python
def validate_config(config: DebateConfig):
    # Validate workflow
    if config.workflow.mode not in ["standard", "document"]:
        raise ValidationError(f"Invalid workflow mode: {config.workflow.mode}")

    if config.workflow.rounds < 1:
        raise ValidationError(f"Rounds must be >= 1, got: {config.workflow.rounds}")

    # Validate roles
    role_names = set()
    for role in config.roles:
        if role.name in role_names:
            raise ValidationError(f"Duplicate role name: {role.name}")
        role_names.add(role.name)

        if role.side not in ["pro", "con", "neutral"]:
            raise ValidationError(f"Invalid side for {role.name}: {role.side}")

        if not role.prompt and not role.prompt_file:
            raise ValidationError(f"Role {role.name} has no prompt")

        if role.name not in config.models:
            raise ValidationError(f"Model not found: {role.name}")

    # Validate required roles
    if "pro" not in {r.side for r in config.roles}:
        raise ValidationError("Missing required role: pro")

    if "con" not in {r.side for r in config.roles}:
        raise ValidationError("Missing required role: con")

    # Validate auxiliary roles
    if config.auxiliary_roles:
        for role in config.auxiliary_roles:
            if not role.trigger:
                raise ValidationError(f"Auxiliary role {role.name} missing trigger")
```

---

## Migration from Hardcoded Roles

### Before (Hardcoded)
```python
# In workflow/debate_workflow.py
pro_node = ProDebaterNode(llm_config, prompts.pro_debater_system)
con_node = ConDebaterNode(llm_config, prompts.con_debater_system)
```

### After (Config-Driven)
```python
# Load from debate.yml
config = load_config("debate.yml")

# Factory creates nodes
pro_role = next(r for r in config.roles if r.side == "pro")
con_role = next(r for r in config.roles if r.side == "con")

pro_node = ProDebaterNode(
    config.models[pro_role.model],
    pro_role.resolved_prompt
)
con_node = ConDebaterNode(
    config.models[con_role.model],
    con_role.resolved_prompt
)
```

---

**End of Data Model**
