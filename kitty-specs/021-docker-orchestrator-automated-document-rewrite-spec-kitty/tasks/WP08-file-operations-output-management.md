---
work_package_id: WP08
title: File Operations & Output Management
lane: "for_review"
dependencies: [WP01]
base_branch: 021-docker-orchestrator-automated-document-rewrite-spec-kitty-WP01
base_commit: efea11972a13c65db4a9d9082e60ae9e967d2558
created_at: '2026-02-21T22:24:42.445794+00:00'
subtasks: [T047, T048, T049, T050, T051]
phase: Phase 3 - User Interface
shell_pid: "52262"
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP08 – File Operations & Output Management

Implement file reading, output generation, and preservation of originals.

## Objectives & Success Criteria

**Success Criteria**:
- Source and corrections files read correctly with encoding detection
- Multiple file format support (markdown, text, code)
- Output file written with .corrected. suffix
- Original files never modified
- Output file conflicts handled per config (error/overwrite/timestamp)

## Subtasks & Detailed Guidance

### T047 – Create FileOperations infrastructure class
- File: `src/orchestrator/infrastructure/filesystem.py`
- Methods: read_source(), read_corrections(), write_output(), generate_output_path()

### T048 – Implement file reading with encoding detection
- Try encodings: utf-8, latin-1, cp1252
- Use chardet or similar if available, else manual detection
- Raise FileNotFoundError with clear message if file doesn't exist

### T049 – Implement output path generation
- Use config.output_suffix (default: ".corrected.")
- If config.timestamp_output: add timestamp suffix
- Return: source_path.with_suffix(ext + suffix + ext)

### T050 – Implement corrected file writing
- Write atomically: write to temp file, then rename
- Temp file: output_path.with_suffix('.tmp')
- Use shutil.move for atomic rename
- Ensure original never modified

### T051 – Add output file conflict handling
- Check if output_path exists
- Handle per config.overwrite_output:
  - "error": raise FileExistsError
  - "overwrite": write directly
  - "timestamp": generate new path with timestamp

## Test Strategy
**Test File**: `tests/orchestrator/unit/test_filesystem.py`
- Test file reading with various encodings
- Test atomic write preserves original
- Test conflict handling modes

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
- 2026-02-21T22:28:49Z – unknown – shell_pid=52262 – lane=for_review – Ready for review: File Operations & Output Management complete with 17 passing tests
