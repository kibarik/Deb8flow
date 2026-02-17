---
work_package_id: "WP05"
subtasks: ["T021", "T022", "T023"]
title: "Workflow Tests"
phase: "Phase 2 - Core Implementation"
lane: "planned"
dependencies: ["WP04"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP05 – Workflow Tests

## Objectives & Success Criteria

Ensure workflows work correctly with configuration and maintain backward compatibility.

**Success Criteria**:
- Workflow tests pass with default and custom configs
- Backward compatibility verified (default config = current behavior)

## Context & Constraints

**Dependencies**: WP04 (Workflow Integration)

## Subtasks

### T021 – Write Debate Workflow Tests
- Test with default config (debate.yml)
- Test with custom config (different rounds, roles)
- Test fact-checking enable/disable

### T022 – Write Document Workflow Tests
- Test with default config
- Test with custom config for document mode
- Verify document context is passed

### T023 – Test Backward Compatibility
- Side-by-side comparison with original system
- Verify output matches when using default config

## Implementation Notes

- Use test fixtures for config files
- Mock LLM responses for predictable testing
- Compare output structure with original

## Review Guidance

[ ] Tests cover default and custom configs
[ ] Backward compatibility verified
[ ] Tests pass with pytest

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
