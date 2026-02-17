---
work_package_id: "WP04"
subtasks: ["T016", "T017", "T018", "T019", "T020"]
title: "Workflow Integration"
phase: "Phase 2 - Core Implementation"
lane: "planned"
dependencies: ["WP01", "WP03"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP04 – Workflow Integration

## Objectives & Success Criteria

Refactor existing workflows to use configuration-driven node construction and dynamic round routing.

**Success Criteria**:
- DebateWorkflow loads config and uses node factory
- DocumentDebateWorkflow loads config and uses node factory
- Round count is configurable (not hardcoded)
- Workflows preserve existing behavior with default config

## Context & Constraints

**Dependencies**: WP01 (Config), WP03 (Node Factory)

**Key Decision**: Adapt existing workflow structure - don't rewrite

## Subtasks

### T016 – Refactor DebateWorkflow
- Load debate.yml by default in `workflow/debate_workflow.py`
- Use node factory to construct PRO and CON nodes
- Pass config to workflow initialization

### T017 – Dynamic Round Routing (Standard)
- Replace hardcoded round count with config.workflow.rounds
- Route debate stages based on configured rounds

### T018 – Refactor DocumentDebateWorkflow  
- Load debate.yml by default in `workflow/document_debate_workflow.py`
- Use node factory for participant nodes

### T019 – Dynamic Round Routing (Document)
- Apply config.workflow.rounds to document workflow

### T020 – Update DebateState (if needed)
- Check if state needs config-related fields
- Add only if necessary (prefer keeping config separate)

## Implementation Notes

- Preserve StateGraph structure
- Use factory.create_pro_debater_node(), factory.create_con_debater_node()
- Load config once at workflow initialization
- Support config parameter override

## Test Strategy

Tests in WP05 will verify workflows work with config.

## Risks & Mitigations

**Risk**: Breaking existing behavior
**Mitigation**: Test with default config first; must match current output

## Review Guidance

[ ] Workflows load debate.yml by default
[ ] Node factory is used (not hardcoded instantiation)
[ ] Round count comes from config
[ ] Existing workflow structure preserved

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
