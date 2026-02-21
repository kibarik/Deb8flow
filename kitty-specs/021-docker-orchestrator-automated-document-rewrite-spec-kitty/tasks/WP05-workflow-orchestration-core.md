---
work_package_id: WP05
title: Workflow Orchestration Core
lane: planned
dependencies: ["WP02", "WP03", "WP04"]
subtasks: [T027, T028, T029, T030, T031, T032, T033]
phase: Phase 2 - Core Workflow
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP05 – Workflow Orchestration Core

Implement main orchestration loop driving Spec-Kitty phases sequentially.

## Objectives & Success Criteria

**Success Criteria**:
- Orchestrator executes all 7 phases sequentially (specify → accept)
- Phase state tracked correctly in WorkflowPhase objects
- Workflow aborts on critical failures with cleanup
- Partial results preserved on abort/interrupt
- Progress callbacks fire for each phase transition
- OrchestratorResult aggregates phase results correctly

## Subtasks & Detailed Guidance

### T027 – Create Orchestrator application class
- File: `src/orchestrator/application/orchestrator.py`
- Class takes: config, container_manager, claude_agent, progress_reporter
- Add `execute(source_path, corrections_path) -> OrchestratorResult` method stub

### T028 – Implement main workflow execution loop
- Define phase order: ["specify", "research", "plan", "tasks", "implement", "review", "accept"]
- For each phase: run phase, check if enabled in config
- Track phase state in List[WorkflowPhase]
- Handle exceptions: catch, log, transition to failed state
- Continue to next phase or abort based on severity

### T029 – Implement phase transition logic
- Before phase: set status to "running", increment attempts
- After phase: set status based on result
- Call progress reporter with phase status
- Update timestamps (started_at, completed_at)

### T030 – Implement workflow abort and cleanup
- On critical error: set abort flag, stop current phase
- Call container_manager.stop() and claude_agent.stop()
- Write partial results if output path known
- Return OrchestratorResult with status="partial" or "failed"

### T031 – Add progress callback hooks
- Define callback signature: `ProgressCallback = Callable[[str, PhaseStatus], None]`
- Call callback on each phase transition
- Pass phase name and status to callback
- Allow None callback (no-op)

### T032 – Implement OrchestratorResult aggregation
- Call `OrchestratorResult.from_phases(phases)`
- Add error_summary from phase error_messages
- Calculate duration from first phase start to last phase end

### T033 – Document workflow pause/resume as out-of-scope
- **Decision**: Pause/resume is out-of-scope for v1.0
- **Rationale**: State persistence to disk adds complexity (serialization, recovery logic, state validation)
- **Alternative**: Full workflow completes in one session. On failure, user restarts from beginning.
- **Documentation**: Add note to `docs/orchestrator.md` explaining this limitation
- **Future consideration**: If demand emerges, add as v2.0 feature with state checkpointing

## Test Strategy
**Test File**: `tests/orchestrator/unit/test_orchestrator.py`
- Mock container_manager and claude_agent
- Test successful workflow through all phases
- Test abort on critical failure
- Test partial result preservation

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex state management | High | Keep phase state in single list |
| Cleanup doesn't run | High | Use try/finally around execute() |

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
