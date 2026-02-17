# Research: Flexible Debate Configuration with YAML

**Feature**: #014 - Flexible Debate Configuration with YAML
**Date**: 2025-02-17
**Status**: Complete

## Overview

This document captures research findings for implementing YAML-based configuration in the Deb8flow debate system. Research focused on configuration validation patterns, dynamic workflow construction in LangGraph, and backward compatibility strategies.

## Research Questions & Findings

### RQ-01: YAML Parsing and Validation Strategy

**Question**: How should we parse and validate YAML configuration while adhering to the minimal dependencies principle?

**Investigation**:
- Evaluated: Pydantic (adds dependency), OmegaConf/Hydra (heavy), standard library `yaml` + manual validation
- Reviewed existing project dependencies and patterns
- Analyzed validation requirements from FR-001 through FR-025

**Decision**: Use Python standard library `yaml.safe_load()` with manual validation

**Rationale**:
- **Minimal dependencies**: Standard library is already available; no new dependencies
- **Sufficient complexity**: Configuration schema is straightforward (nested dicts, lists, strings)
- **Explicit validation**: Manual validation allows custom error messages as required by FR-023
- **Performance**: Standard library parsing is fast (< 2 seconds for SC-004)

**Alternatives Considered**:
- **Pydantic**: Provides automatic validation and type checking, but adds a dependency. Rejected due to "minimal dependencies" constitution principle.
- **OmegaConf/Hydra**: Feature-rich but overkill for this use case. Rejected due to complexity and additional dependencies.

**Implementation Notes**:
- Use `yaml.safe_load()` to prevent code injection
- Create `DebateConfig` dataclass for type-safe access
- Implement `validate_config()` function with clear error messages
- Support path resolution for `prompt_file` references relative to config file directory

---

### RQ-02: Dynamic Node Construction in LangGraph

**Question**: How can we make LangGraph workflow nodes dynamically configurable while preserving the existing StateGraph architecture?

**Investigation**:
- Analyzed existing `debate_workflow.py` and `document_debate_workflow.py`
- Reviewed LangGraph documentation for dynamic node addition
- Examined `BaseComponent` pattern in `nodes/base_component.py`
- Studied current node initialization with LLM configs

**Decision**: Factory pattern with dynamic node construction based on configuration

**Rationale**:
- **Preserves architecture**: Maintains existing LangGraph StateGraph structure
- **Minimal changes**: Adapts existing nodes rather than rewriting workflow
- **Flexibility**: Factory can construct nodes with any role configuration
- **Testability**: Factory can be tested independently from workflow

**Implementation Pattern**:
```python
# Factory function to create nodes from configuration
def create_role_nodes(config: DebateConfig) -> Dict[str, BaseComponent]:
    nodes = {}
    for role in config.roles:
        llm_config = config.models.get(role.name, default_llm_config)
        if role.side == "pro":
            nodes[f"{role.name}_node"] = ProDebaterNode(llm_config, role.prompt)
        elif role.side == "con":
            nodes[f"{role.name}_node"] = ConDebaterNode(llm_config, role.prompt)
        # ... handle auxiliary roles
    return nodes

# Workflow uses factory to build nodes
def _initialize_workflow(self, config: DebateConfig):
    workflow = StateGraph(DebateState)
    role_nodes = create_role_nodes(config)
    for name, node in role_nodes.items():
        workflow.add_node(name, node)
    # ... configure edges based on rounds
```

**Alternatives Considered**:
- **Separate workflow classes**: Would duplicate code between standard and document workflows. Rejected to avoid duplication.
- **Template-based workflow**: Too complex for current needs. Rejected to preserve simplicity.

---

### RQ-03: Backward Compatibility Strategy

**Question**: How can we introduce YAML configuration without breaking existing behavior?

**Investigation**:
- Reviewed current hardcoded prompts in `prompts/roles/`
- Analyzed existing 3-round debate structure
- Examined current model assignments (Requesty/DeepSeek)
- Studied existing CLI interface in `main.py`

**Decision**: Preserve existing behavior in default `debate.yml`

**Rationale**:
- **No breaking changes**: Existing deployments continue working unchanged
- **Opt-in to new features**: Custom configurations require explicit `--debate-config` flag
- **Documentation continuity**: Current examples and tutorials remain valid
- **Migration path**: Users can adopt new features at their own pace

**Migration Approach**:
1. Create `debate.yml` with exact current behavior:
   - PRO role: Current PRD reviewer prompts
   - CON role: Current PRD reviewer prompts
   - 3 rounds: opening → rebuttal → counter → final_argument
   - Model: Requesty/DeepSeek (current default)
   - Fact-checking: Current behavior (enabled)
2. Add `--debate-config` flag for custom configs
3. Provide `examples/debate.generic.yml` as a generic template
4. Document migration path in README

**Implementation Notes**:
- Default config path: `./debate.yml` (project root)
- Override precedence: CLI args > config file > defaults
- Fallback: If `debate.yml` missing, show helpful error (not crash)

---

### RQ-04: Configuration Schema Design

**Question**: What YAML structure best supports the feature requirements while remaining maintainable?

**Investigation**:
- Analyzed FR-003 through FR-010 for required fields
- Reviewed user stories for configuration patterns
- Studied existing role definitions in `prompts/roles/`
- Evaluated inline vs. file-based prompt patterns

**Decision**: Hierarchical schema with sections for roles, models, rounds, workflow

**Proposed Schema**:
```yaml
# debate.yml - Default configuration preserving current PRD review behavior

workflow:
  mode: standard  # standard | document
  rounds: 3

roles:
  - name: pro
    side: pro
    prompt: |-
      You are a PRD reviewer arguing FOR the product specification...
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

  - name: con
    side: con
    prompt_file: prompts/roles/prd_reviewer_con.md  # Alternative to inline prompt
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 1000

auxiliary_roles:
  - name: domain_expert
    trigger:
      after_round: 2
    prompt_file: prompts/roles/domain_expert.md
    model: deepseek-chat

models:
  deepseek-chat:
    provider: requesty
    api_key_env: REQ_API_KEY
    model_name: deepseek-chat

fact_checking:
  enabled: true
  max_failures: 3
```

**Rationale**:
- **Logical grouping**: Related settings grouped together
- **Flexibility**: Supports both inline and file-based prompts
- **Extensibility**: Easy to add new roles or auxiliary participants
- **Validation**: Clear structure enables precise error messages

---

### RQ-05: Prompt File Resolution

**Question**: How should `prompt_file` paths be resolved to support reusable configurations?

**Investigation**:
- Reviewed FR-007 (paths relative to config file directory)
- Analyzed use case: sharing configs across projects
- Evaluated absolute vs. relative path approaches

**Decision**: Resolve paths relative to configuration file directory

**Rationale**:
- **Portability**: Configs can be shared across projects with same directory structure
- **Predictability**: Same config works regardless of CWD
- **Error messages**: Clear which file is missing when resolution fails

**Implementation**:
```python
import os
from pathlib import Path

def resolve_prompt_file(config_path: str, prompt_file: str) -> str:
    """
    Resolve prompt_file path relative to config file directory.
    """
    config_dir = Path(config_path).parent
    resolved_path = config_dir / prompt_file
    if not resolved_path.exists():
        raise ConfigurationError(
            f"Prompt file not found: {resolved_path}\n"
            f"Referenced from: {config_path}"
        )
    return str(resolved_path)
```

---

## Best Practices Identified

### YAML Configuration Best Practices
1. **Use safe_load()**: Prevent code injection from untrusted YAML
2. **Validate early**: Catch configuration errors before workflow execution
3. **Clear error messages**: Include file path and field name in validation errors
4. **Schema documentation**: Include comments in default config explaining each field

### LangGraph Dynamic Workflows
1. **Factory pattern**: Centralize node construction logic
2. **Separate concerns**: Factory handles node creation, workflow handles routing
3. **Preserve state types**: Don't change `DebateState` structure unnecessarily
4. **Test nodes independently**: Unit test node behavior before workflow integration

### Backward Compatibility
1. **Default behavior**: Default config should match existing behavior exactly
2. **Opt-in changes**: New features require explicit configuration
3. **Documentation**: Update docs to explain both old and new approaches
4. **Deprecation path**: If old APIs are kept, document deprecation timeline

---

## Open Questions (Resolved)

All research questions have been resolved. No outstanding clarifications needed.

---

## References

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- Python YAML Documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
- Existing codebase: `workflow/debate_workflow.py`, `nodes/base_component.py`
- Feature Specification: `kitty-specs/014-flexible-debate-config-yaml/spec.md`
