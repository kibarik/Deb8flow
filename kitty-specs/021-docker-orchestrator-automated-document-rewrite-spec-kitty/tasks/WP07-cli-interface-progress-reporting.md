---
work_package_id: WP07
title: CLI Interface & Progress Reporting
lane: "for_review"
dependencies: [WP01, WP05]
base_branch: 021-docker-orchestrator-automated-document-rewrite-spec-kitty-WP01
base_commit: efea11972a13c65db4a9d9082e60ae9e967d2558
created_at: '2026-02-21T22:24:35.259475+00:00'
subtasks: [T041, T042, T043, T044, T045, T046]
phase: Phase 3 - User Interface
shell_pid: "52176"
agent: "claude-opus"
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP07 – CLI Interface & Progress Reporting

Implement CLI argument parsing and console progress reporting.

## Objectives & Success Criteria

**Success Criteria**:
- CLI accepts source/corrections paths and options (help, output, config, verbose, dry-run)
- Argument validation checks file paths exist and are readable
- Console output shows [ORCHESTRATOR] prefixed progress messages
- Progress reporter formats phase transitions consistently
- Verbose mode provides additional detail
- Ctrl+C handled gracefully

## Subtasks & Detailed Guidance

### T041 – Create CLI argument parser adapter
- File: `src/orchestrator/adapters/cli.py`
- Use argparse following scripts/rewrite pattern
- Arguments: positional (source, corrections), --output, --config, --max-retries, --timeout, --keep-containers, --verbose, --dry-run
- Return parsed args dict

### T042 – Implement argument validation
- Validate source file exists and is readable
- Validate corrections file exists and is readable
- Validate output path directory is writable
- Raise FileNotFoundError with clear message if validation fails

### T043 – Create ProgressReporter adapter
- File: `src/orchestrator/adapters/progress_reporter.py`
- Methods: phase_start(), phase_complete(), phase_error(), summary()
- Format: "[ORCHESTRATOR] Phase: <name> → <status>"
- Respect verbose flag for additional detail

### T044 – Implement phase progress display
- phase_start(): print "Phase: <name> → Running /spec-kitty.<phase>"
- phase_complete(): print "Phase: <name> → Validation passed (N/M attempts)"
- phase_error(): print "Phase: <name> → ERROR: <message>"

### T045 – Implement summary and result display
- summary(): print "Complete: <completed>/<total> phases successful, <retries> retries, <duration> total"
- Show output_path if success
- Show failed_phase and error_summary if failed

### T046 – Add Ctrl+C signal handler
- Register signal.SIGINT and signal.SIGTERM handler
- Set shutdown_flag
- Orchestrator checks flag between phases
- Print "Interrupted by user" with partial results summary

## Test Strategy
**Test File**: `tests/orchestrator/unit/test_cli.py`
- Test argument parsing
- Test validation passes/raises
- Test progress reporter output format

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
- 2026-02-21T22:24:35Z – claude-opus – shell_pid=52176 – lane=doing – Assigned agent via workflow command
- 2026-02-21T22:26:58Z – claude-opus – shell_pid=52176 – lane=for_review – Ready for review: CLI Interface & Progress Reporting complete with 21 passing tests
