---
work_package_id: "WP07"
subtasks: ["T029", "T030"]
title: "CLI Tests"
phase: "Phase 2 - Core Implementation"
lane: "planned"
dependencies: ["WP06"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP07 – CLI Tests

## Objectives & Success Criteria

Ensure CLI integration works correctly with various config scenarios.

**Success Criteria**:
- CLI tests pass for default, custom, missing, and invalid configs

## Context & Constraints

**Dependencies**: WP06 (CLI Integration)

## Subtasks

### T029 – Write main.py CLI Tests
- Test with --debate-config pointing to valid config
- Test with missing file (error handling)
- Test with invalid config (validation error)
- Test without --debate-config (uses default)
- Test CLI argument precedence

### T030 – Write document_debate_cli.py Tests
- Same test cases as T029
- Test with document workflow mode

## Implementation Notes

- Use test fixtures directory with sample configs
- Mock workflow execution to avoid full debate runs
- Verify error messages are user-friendly

## Review Guidance

[ ] Tests cover all config scenarios
[ ] Error cases tested
[ ] Precedence rules verified

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
