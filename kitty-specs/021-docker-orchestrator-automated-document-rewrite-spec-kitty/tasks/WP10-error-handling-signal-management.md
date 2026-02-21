---
work_package_id: WP10
title: Error Handling & Signal Management
lane: "planned"
dependencies: [WP03, WP04, WP05]
base_branch: 021-docker-orchestrator-automated-document-rewrite-spec-kitty-WP01
base_commit: efea11972a13c65db4a9d9082e60ae9e967d2558
created_at: '2026-02-21T22:31:11.013029+00:00'
subtasks: [T057, T058, T059, T060, T061, T062]
phase: Phase 4 - Quality
shell_pid: "55426"
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec/kitty.tasks
---

# Work Package Prompt: WP10 – Error Handling & Signal Management

Implement comprehensive error handling and graceful signal management.

## Objectives & Success Criteria

**Success Criteria**:
- All error paths exit with appropriate exit codes (0=success, 1=partial, 2=failed, etc.)
- Docker containers cleaned up on all exits
- Ctrl+C handled gracefully with partial results
- Error messages are actionable
- No resource leaks on any exit path

## Subtasks & Detailed Guidance

### T057 – Create OrchestratorError exception hierarchy
- File: `src/orchestrator/domain/exceptions.py`
- Classes: OrchestratorError (base), DockerError, AgentError, ValidationError, ConfigError
- Each has exit_code attribute

### T058 – Implement error code mapping
- Function: `get_exit_code(result: OrchestratorResult) -> int`
- Map: success=0, partial=1, failed=2, validation_error=3, docker_error=4, timeout=5
- Signal interrupt: 130

### T059 – Add container cleanup on error paths
- In orchestrator.execute(): use try/finally
- Finally: call container_manager.stop(), claude_agent.stop()
- Also catch: Exception, cleanup, re-raise

### T060 – Implement graceful shutdown on signals
- Signal handler sets shutdown_event (threading.Event)
- Orchestrator checks event between phases
- On shutdown: stop current phase, write partial results, exit 130

### T061 – Add partial result preservation on abort
- If abort during workflow: copy current artifact to output path
- Use partial artifact (even if incomplete)
- Log warning about partial results

### T062 – Create error message templates
- Define templates for each error type
- Include: what went wrong, how to fix, next steps
- Example: "Docker daemon not running. Start with: open -a Docker"

## Test Strategy
**Test File**: tests/orchestrator/unit/test_error_handling.py
- Test exception hierarchy
- Test exit code mapping
- Test cleanup runs on exception

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
- 2026-02-21T23:18:45Z – unknown – shell_pid=55426 – lane=planned – Moved back to planned: Requires WP03, WP04, WP05 which are not complete
