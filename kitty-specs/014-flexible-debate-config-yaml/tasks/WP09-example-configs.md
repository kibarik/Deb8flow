---
work_package_id: "WP09"
subtasks: ["T035", "T036", "T037", "T038"]
title: "Example Configurations"
phase: "Phase 3 - Enhancement"
lane: "planned"
dependencies: []
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP09 – Example Configurations

## Objectives & Success Criteria

Create example configurations for different domains to demonstrate system flexibility.

**Success Criteria**:
- examples/ directory exists
- Three example configs are valid and usable

## Context & Constraints

**Dependencies**: None (can be done independently after WP01)

## Subtasks

### T035 – Create examples/ Directory
- Create `examples/` in project root
- Add README explaining each example

### T036 – Legal Debate Example
- File: `examples/legal-debate.yml`
- Roles: prosecutor vs defense attorney
- 3 rounds, court-style prompts
- Well-documented with comments

### T037 – Financial Analysis Example
- File: `examples/financial-analysis.yml`
- Mode: document
- Roles: bull vs bear analyst
- Financial document analysis prompts

### T038 – Generic Template
- File: `examples/debate.generic.yml`
- Simple optimist vs skeptic roles
- Minimal rounds (2)
- Clear comments for customization

## Implementation Notes

Each example should be well-documented with:
- Description header comment
- Usage instructions
- Placeholder prompts users can customize

## Review Guidance

[ ] All examples are valid YAML
[ ] Examples demonstrate different features
[ ] Comments explain usage
[ ] README in examples/ directory

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
