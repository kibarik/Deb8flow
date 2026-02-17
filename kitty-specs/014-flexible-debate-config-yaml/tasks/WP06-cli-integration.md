---
work_package_id: "WP06"
subtasks: ["T024", "T025", "T026", "T027", "T028"]
title: "CLI Integration"
phase: "Phase 2 - Core Implementation"
lane: "planned"
dependencies: ["WP01"]
history:
  - timestamp: "2025-02-17T20:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP06 – CLI Integration

## Objectives & Success Criteria

Add `--debate-config` CLI argument to both standard and document debate CLIs.

**Success Criteria**:
- Both CLIs accept `--debate-config` argument
- Config is loaded and passed to workflow
- Clear error messages for missing/invalid configs

## Context & Constraints

**Dependencies**: WP01 (Config Data Model)

## Subtasks

### T024 – Add --debate-config to main.py
- Use argparse for argument parsing
- Default to debate.yml
- Add help text

### T025 – Add --debate-config to document_debate_cli.py
- Same approach as T024

### T026 – Config Loading in main.py
- Load config at startup
- Handle ConfigNotFoundError
- Pass config to workflow

### T027 – Config Loading in document_debate_cli.py
- Same approach as T026

### T028 – CLI Argument Precedence
- CLI args > config file > defaults
- Example: `--rounds 5` overrides config

## Implementation Notes

```python
parser.add_argument(
    '--debate-config',
    default='debate.yml',
    help='Path to debate configuration file'
)
```

## Review Guidance

[ ] Argparse used for both CLIs
[ ] Default is debate.yml
[ ] Error handling for missing files
[ ] Config passed to workflow

## Activity Log

- 2025-02-17T20:00:00Z – system – lane=planned – Prompt created
