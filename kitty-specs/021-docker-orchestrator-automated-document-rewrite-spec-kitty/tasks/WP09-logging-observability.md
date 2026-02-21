---
work_package_id: WP09
title: Logging & Observability
lane: planned
dependencies: ["WP01"]
subtasks: [T052, T053, T054, T055, T056]
phase: Phase 3 - User Interface
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec/kitty.tasks
---

# Work Package Prompt: WP09 – Logging & Observability

Implement structured logging to files and optional verbose console output.

## Objectives & Success Criteria

**Success Criteria**:
- Log files written to .orchestrator/logs/
- Logs contain debugging info (timestamps, phase transitions, errors)
- Log rotation prevents disk space issues (10MB max, 3 backups)
- Verbose mode provides additional detail
- Log format matches existing patterns

## Subtasks & Detailed Guidance

### T052 – Create LoggingSetup infrastructure
- File: `src/orchestrator/infrastructure/logging.py`
- Function: `setup_logging(config: OrchestratorConfig)`
- Creates log_dir if doesn't exist
- Returns logger instance

### T053 – Implement structured log formatting
- Formatter: `[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s`
- Use UTC timestamps
- Include phase context in log messages when available

### T054 – Add file logging with rotation
- Use logging.handlers.RotatingFileHandler
- MaxBytes: 10MB, backupCount: 3
- File: log_dir / orchestrator-YYYYMMDD-HHMMSS.log

### T055 – Implement verbose mode logging
- ConsoleHandler: add if config.verbose=True
- Set level to DEBUG if verbose, INFO otherwise
- Don't duplicate logs if verbose=False

### T056 – Add log cleanup on startup
- Remove logs older than 7 days
- Use pathlib.Path.glob() to find log files
- Check mtime (modification time)

## Test Strategy
**Test File**: tests/orchestrator/unit/test_logging.py
- Test log file creation
- Test rotation creates backups
- Test cleanup removes old logs

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
