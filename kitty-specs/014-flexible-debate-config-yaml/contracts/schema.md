# Configuration Schema Contract

**Feature**: #014 - Flexible Debate Configuration with YAML
**Version**: 1.0
**Status**: Phase 1 Design

## Schema Version

`debate_config_version: "1.0"`

## Root Structure

```yaml
# Debate Configuration Schema v1.0
debate_config_version: "1.0"

workflow:
  mode: string          # Required: "standard" | "document"
  rounds: integer       # Required: >= 1

roles:                  # Required: List of 2+ roles
  - <role_config>

auxiliary_roles:        # Optional: List of auxiliary roles
  - <role_config>

models:                 # Required: Model configurations
  <model_name>: <model_config>

fact_checking:          # Optional: Fact-checking settings
  enabled: boolean
  max_failures: integer
```

---

## RoleConfig Schema

```yaml
roles:
  - name: string              # Required: Unique identifier
    side: string              # Required: "pro" | "con" | "neutral"
    prompt: string            # Optional: Inline prompt text
    prompt_file: string       # Optional: Path to prompt file
    model: string             # Required: Model name reference
    temperature: float        # Optional: 0.0-2.0, default 0.7
    max_tokens: integer       # Optional: >0, default 1000
```

### Role Validation Rules

| Field | Type | Required | Validation | Default |
|-------|------|----------|------------|---------|
| `name` | string | Yes | Unique across all roles | - |
| `side` | string | Yes | "pro" \| "con" \| "neutral" | - |
| `prompt` | string | No* | Multiline string | - |
| `prompt_file` | string | No* | Relative path to config file | - |
| `model` | string | Yes | Must exist in `models` | - |
| `temperature` | float | No | 0.0 <= value <= 2.0 | 0.7 |
| `max_tokens` | int | No | value > 0 | 1000 |

*At least one of `prompt` or `prompt_file` is required. If both specified, `prompt_file` takes precedence.

### Role Prompt Precedence

```
prompt_file (highest priority)
    ↓
prompt (inline)
    ↓
Error (if neither specified)
```

---

## Auxiliary Role Schema

```yaml
auxiliary_roles:
  - name: string              # Required: Unique identifier
    side: string              # Required: "auxiliary"
    prompt: string            # Optional: Inline prompt text
    prompt_file: string       # Optional: Path to prompt file
    model: string             # Required: Model name reference
    trigger:                  # Required: When to participate
      after_round: integer    # Optional: Participate after round N
      on_fact_check: boolean  # Optional: Participate after fact-check
```

### Trigger Validation Rules

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `after_round` | int | No* | >= 1 |
| `on_fact_check` | bool | No* | true \| false |

*At least one trigger condition must be specified. Multiple triggers use AND logic.

---

## ModelConfig Schema

```yaml
models:
  <model_name>:
    provider: string          # Required: "openai" | "azure" | "zhipu" | "requesty"
    model_name: string        # Required: Model identifier
    api_key_env: string       # Required: Environment variable name
    azure_endpoint: string    # Optional: For provider="azure"
    api_version: string       # Optional: For provider="azure"
```

### Model Validation Rules

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `provider` | string | Yes | "openai" \| "azure" \| "zhipu" \| "requesty" |
| `model_name` | string | Yes | Valid model identifier |
| `api_key_env` | string | Yes | Must be set in environment |
| `azure_endpoint` | string | Conditional | Required if provider="azure" |
| `api_version` | string | Conditional | Required if provider="azure" |

### Supported Providers

| Provider | Description | Example model_name |
|----------|-------------|-------------------|
| `openai` | OpenAI API | "gpt-4", "gpt-3.5-turbo" |
| `azure` | Azure OpenAI | "gpt-4" |
| `zhipu` | Zhipu AI | "glm-4.7" |
| `requesty` | Requesty API | "deepseek-chat" |

---

## FactCheckingConfig Schema

```yaml
fact_checking:
  enabled: boolean           # Optional: default true
  max_failures: integer      # Optional: >= 0, default 3
```

### Fact-Checking Validation Rules

| Field | Type | Required | Validation | Default |
|-------|------|----------|------------|---------|
| `enabled` | bool | No | true \| false | true |
| `max_failures` | int | No | >= 0 | 3 |

---

## Complete Example

```yaml
# debate.yml - Default configuration
debate_config_version: "1.0"

workflow:
  mode: standard
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: |-
      You are a PRD reviewer arguing FOR the product specification.
      Focus on benefits, feasibility, and strategic value.
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

  - name: con
    side: con
    prompt_file: prompts/roles/prd_reviewer_con.md
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

auxiliary_roles:
  - name: technical_expert
    side: auxiliary
    prompt_file: prompts/roles/technical_expert.md
    model: deepseek-chat
    trigger:
      after_round: 2

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY

fact_checking:
  enabled: true
  max_failures: 3
```

---

## Error Response Format

### Validation Errors

```json
{
  "error": "ConfigurationValidationError",
  "message": "Invalid configuration",
  "details": [
    {
      "field": "roles[1].model",
      "error": "Model not found: unknown-model",
      "expected": "One of: deepseek-chat, gpt-4"
    },
    {
      "field": "workflow.rounds",
      "error": "Value out of range",
      "expected": ">= 1",
      "actual": 0
    }
  ]
}
```

### File Not Found Errors

```json
{
  "error": "ConfigurationFileNotFound",
  "message": "Configuration file not found: custom.yml",
  "suggestion": "Create the file or use --debate-config with a valid path"
}
```

### Prompt File Errors

```json
{
  "error": "PromptFileNotFound",
  "message": "Prompt file not found: prompts/roles/missing.md",
  "referenced_from": "roles[0].prompt_file",
  "config_file": "debate.yml"
}
```

---

## Configuration Precedence

When multiple sources provide configuration values:

```
1. CLI Arguments (highest priority)
   ↓
2. Custom Config File (--debate-config)
   ↓
3. Default Config File (debate.yml)
   ↓
4. Hardcoded Defaults (lowest priority)
```

### Example Precedence

```bash
# CLI: --rounds 5
# Config: rounds: 3
# Result: 5 rounds (CLI takes precedence)
```

---

## Schema Migration Policy

### Version 1.0 → 1.1 (Future)

- **New fields**: Optional fields added with defaults
- **Removed fields**: Deprecated with warning, removed in next major version
- **Modified fields**: Type changes require major version bump

### Backward Compatibility

- Configuration files from v1.0 will work with v1.0.x
- New fields added in minor versions are optional
- Breaking changes require major version increment

---

## CLI Integration Contract

### Arguments

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `--debate-config` | string | Path to custom configuration file | debate.yml |
| `--rounds` | int | Override number of rounds | From config |
| `--model` | string | Override model for all roles | From config |

### Example Usage

```bash
# Use default configuration
python main.py

# Use custom configuration
python main.py --debate-config legal-debate.yml

# Override specific values
python main.py --debate-config legal-debate.yml --rounds 5
```

---

**End of Schema Contract**
