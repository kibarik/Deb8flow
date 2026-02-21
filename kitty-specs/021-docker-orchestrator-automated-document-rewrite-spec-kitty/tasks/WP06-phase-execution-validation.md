---
work_package_id: WP06
title: Phase Execution & Validation
lane: planned
dependencies: ["WP04", "WP05"]
subtasks: [T034, T035, T036, T037, T038, T039, T040]
phase: Phase 2 - Core Workflow
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP06 – Phase Execution & Validation

Execute Spec-Kitty phases via Claude Code agent and validate artifacts.

## Objectives & Success Criteria

**Success Criteria**:
- Each Spec-Kitty phase executes via claude_agent command helpers
- Artifact validation runs after phases with validate=True
- Validation failures trigger retries up to max_retries
- Invalid artifacts cause workflow abort after max retries
- Validation prompts use configurable templates
- Artifact completeness detects [NEEDS CLARIFICATION] markers

## Subtasks & Detailed Guidance

### T034 – Create PhaseRunner application class
- File: `src/orchestrator/application/phase_runner.py`
- Takes: claude_agent, artifact_validator, config
- Method: `execute_phase(phase_name: str) -> WorkflowPhase`

### T035 – Implement phase execution for each Spec-Kitty command
- Map phase names to agent helpers:
  - "specify" → agent.run_specify(description)
  - "research" → agent.run_research()
  - "plan" → agent.run_plan()
  - etc.
- Parse result dict for artifact_path
- Return WorkflowPhase with status

### T036 – Implement ArtifactValidator for spec/plan/tasks
- File: `src/orchestrator/application/artifact_validator.py`
- Method: `validate(artifact_path: Path, artifact_type: str) -> ValidationStatus`
- Uses ArtifactMetadata to check completeness
- Calls agent with validation prompt
- Parses response: {status: "passed"/"failed", issues: []}

### T037 – Create validation prompt templates
- Directory: `src/orchestrator/prompts/`
- Files: `validation.md` (template for validation)
- Template includes: artifact type, artifact content, validation criteria
- Use {artifact_type}, {artifact_content} placeholders

### T038 – Implement retry logic with context accumulation
- In execute_phase: if validation fails and attempts < max_retries
- Accumulate validation issues in context
- Re-run phase with additional feedback
- Increment attempts counter
- Stop retrying after max_retries, set status=failed

### T039 – Add artifact completeness detection
- Use ArtifactMetadata.from_markdown(artifact_path)
- Check: clarifications_needed == 0
- Check: all mandatory sections present
- Check: no [NEEDS CLARIFICATION] markers

### T040 – Implement validation timeout handling
- Pass config.validation_timeout to agent
- On timeout: set validation_result=failed
- Log timeout event
- Proceed with retry or abort

## Test Strategy
**Test File**: `tests/orchestrator/unit/test_phase_runner.py`
- Mock claude_agent responses
- Test successful phase execution
- Test validation failure triggers retry
- Test max_retries abort

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Spec-Kitty commands may change | High | Version pin container image |
| Validation quality varies | Medium | Tunable prompts in config |

## Activity Log
- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
