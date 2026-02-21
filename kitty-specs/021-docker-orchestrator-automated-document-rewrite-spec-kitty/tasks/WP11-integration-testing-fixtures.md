---
work_package_id: WP11
title: Integration Testing & Fixtures
lane: planned
dependencies: ["WP01", "WP02", "WP03", "WP04", "WP05", "WP06", "WP07", "WP08", "WP09", "WP10"]
subtasks: [T063, T064, T065, T066, T067]
phase: Phase 4 - Quality
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec/kitty.tasks
---

# Work Package Prompt: WP11 – Integration Testing & Fixtures

Create integration tests and test fixtures for end-to-end validation.

## Objectives & Success Criteria

**Success Criteria**:
- Integration tests cover main workflow (happy path)
- Mock Docker and Claude Code for testing
- Test fixtures provide sample artifacts
- Tests validate error handling paths
- Test suite runs in CI environment

## Subtasks & Detailed Guidance

### T063 – Create test fixtures directory and sample files
- Directory: tests/orchestrator/fixtures/
- Files: sample_source.md, sample_corrections.md, mock_spec_kitty_artifacts/spec.md, plan.md, tasks.md
- Include valid and invalid artifact examples

### T064 – Mock Docker client for testing
- Use unittest.mock.patch('docker.from_env')
- Return fake container with logs(), stop(), remove() methods
- Simulate health check success/failure

### T065 – Mock Claude Code agent for testing
- Mock subprocess.Popen
- Return fake responses for Spec-Kitty commands
- Simulate timeout, parse error

### T066 – Write integration test for happy path
- Test: full workflow executes successfully
- Mock all dependencies
- Assert all phases complete
- Assert output file created

### T067 – Write integration tests for error paths
- Test: Docker unavailable
- Test: Agent crash
- Test: Validation failure
- Test: Ctrl+C interrupt
- Assert correct exit codes

## Test Strategy
**Test File**: tests/orchestrator/integration/test_orchestrator.py
- Run with: poetry run pytest tests/orchestrator/integration/ -v
- Use fixtures from T063

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
