---
work_package_id: "WP03"
subtasks: ["T011", "T012", "T013", "T014", "T015"]
title: "Node Factory"
phase: "Phase 2 - Core Implementation"
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

# Work Package Prompt: WP03 – Node Factory

## Objectives & Success Criteria

Create a factory module for dynamically constructing debate nodes from configuration. This enables the workflow to build nodes based on config rather than hardcoded instantiation.

**Success Criteria**:
- Node factory module exists with clear API
- ProDebaterNode, ConDebaterNode can be created from config
- Auxiliary role nodes can be created from config
- Nodes receive correct prompts (resolved) and model configs
- Tests verify factory creates nodes with correct parameters

## Context & Constraints

**Supporting Documents**:
- Data Model: `kitty-specs/014-flexible-debate-config-yaml/data-model.md` - RoleConfig, ModelConfig
- Research: `kitty-specs/014-flexible-debate-config-yaml/research.md` - Factory pattern decision

**Dependencies**: WP01 (Configuration Data Model)

## Subtasks & Detailed Guidance

### Subtask T011 – Create Node Factory Module

Create `nodes/role_node_factory.py` with imports and module docstring.

### Subtask T012 – Implement ProDebaterNode Factory

Implement `create_pro_debater_node(role_config: RoleConfig, model_config: ModelConfig) -> ProDebaterNode`

- Extract prompt from role_config.resolved_prompt
- Create ProDebaterNode with model config
- Pass temperature and max_tokens if supported

### Subtask T013 – Implement ConDebaterNode Factory

Implement `create_con_debater_node(role_config: RoleConfig, model_config: ModelConfig) -> ConDebaterNode`

- Similar structure to T012
- Use ConDebaterNode class

### Subtask T014 – Implement Auxiliary Node Factory

Implement `create_auxiliary_node(role_config: RoleConfig, model_config: ModelConfig) -> BaseComponent`

- For MVP: reuse ProDebaterNode or ConDebaterNode based on context
- Future: create specialized auxiliary node class
- Must handle trigger conditions

### Subtask T015 – Write Tests for Node Factory

Create `tests/test_nodes/test_role_node_factory.py` with:
- Test pro node creation with correct prompt and model
- Test con node creation with correct prompt and model
- Test auxiliary node creation
- Verify node parameters match config values

## Test Strategy

Test with mock configs to verify:
- Correct node class is instantiated
- Prompt and model are passed correctly
- Temperature and max_tokens are applied

## Risks & Mitigations

**Risk**: Auxiliary role behavior may not fit existing node patterns
**Mitigation**: Start with basic reuse of existing nodes; extend if needed

## Review Guidance

[ ] Factory functions have clear type hints
[ ] Nodes receive resolved_prompt (not prompt_file reference)
[ ] Model configs are correctly converted to LLM configs
[ ] Tests cover all node types

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
