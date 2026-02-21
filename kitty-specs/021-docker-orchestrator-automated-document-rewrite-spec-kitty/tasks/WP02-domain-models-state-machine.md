---
work_package_id: WP02
title: Domain Models & State Machine
lane: "doing"
dependencies: [WP01]
base_branch: 021-docker-orchestrator-automated-document-rewrite-spec-kitty-WP01
base_commit: efea11972a13c65db4a9d9082e60ae9e967d2558
created_at: '2026-02-21T22:19:52.178490+00:00'
subtasks:
- T006
- T007
- T008
- T009
- T010
- T011
phase: Phase 0 - Foundation
assignee: ''
agent: "claude-opus"
shell_pid: "50813"
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP02 – Domain Models & State Machine

## Review Feedback
*[Empty - reviewers will populate if work is returned]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`

---

## Objectives & Success Criteria

Implement core domain entities and workflow state machine with thread-safe transitions.

**Success Criteria**:
- `WorkflowPhase`, `OrchestratorResult`, `ArtifactMetadata` models implemented
- `PhaseStatus` and `ValidationStatus` enums with all values
- State machine enforces valid transitions (pending→running→completed/failed/retrying)
- Thread-safe phase state updates using `threading.Lock`
- `OrchestratorResult.from_phases()` aggregates phase results correctly
- `ArtifactMetadata` parses markdown frontmatter and detects completeness

---

## Context & Constraints

**Supporting Documents**:
- Data Model: [kitty-specs/.../data-model.md](../data-model.md) - All entity definitions
- Spec: [kitty-specs/.../spec.md](../spec.md) - WorkflowPhase and OrchestratorResult entities

**Constraints**:
- Thread-safety required (ThreadPoolExecutor will access phase state)
- State transitions must be exhaustive (no undefined states)
- Use Python 3.12+ enum syntax with StrEnum for status values

---

## Subtasks & Detailed Guidance

### Subtask T006 – Implement WorkflowPhase domain model

**Purpose**: Create the phase tracking model with state metadata.

**Steps**:
1. Create `src/orchestrator/domain/phase.py` (separate file for phase-related models)
2. Import necessary modules: `datetime`, `pathlib.Path`, `dataclasses`, `threading.Lock`
3. Define `PhaseStatus` enum: `pending`, `running`, `completed`, `failed`, `retrying`
4. Define `ValidationStatus` enum: `passed`, `failed`, `skipped`
5. Define `WorkflowPhase` dataclass with fields from data-model.md
6. Add `threading.Lock` instance field for thread-safe updates
7. Initialize `attempts = 0` and create `started_at`, `completed_at` as Optional[datetime]

**Files**:
- `src/orchestrator/domain/phase.py` (new file, ~120 lines)

**Parallel?**: Yes

---

### Subtask T007 – Implement PhaseStatus and ValidationStatus enums

**Purpose**: Define strongly-typed status enums.

**Steps**:
1. In `src/orchestrator/domain/phase.py`, define enums:
   ```python
   from enum import Enum

   class PhaseStatus(str, Enum):
       PENDING = "pending"
       RUNNING = "running"
       COMPLETED = "completed"
       FAILED = "failed"
       RETRYING = "retrying"

   class ValidationStatus(str, Enum):
       PASSED = "passed"
       FAILED = "failed"
       SKIPPED = "skipped"
   ```

**Files**:
- `src/orchestrator/domain/phase.py` (extends T006)

**Parallel?**: Yes (part of T006)

---

### Subtask T008 – Implement state transition logic with validation

**Purpose**: Enforce valid state transitions per data-model.md state machine.

**Steps**:
1. Add `transition_to(status: PhaseStatus)` method to `WorkflowPhase`:
   - Acquire lock
   - Check if transition is valid (use transition table)
   - Update status and timestamps appropriately
   - Release lock
2. Define transition rules:
   - `pending` can go to `running`
   - `running` can go to `completed`, `failed`, `retrying`
   - `retrying` can go to `running`
   - All other transitions raise `InvalidStateTransitionError`
3. Add `can_transition_to(status: PhaseStatus) -> bool` helper
4. Update `attempts` counter on each transition to `running`
5. Set `started_at` on first `pending`→`running`
6. Set `completed_at` on transition to terminal states (`completed`, `failed`)

**Files**:
- `src/orchestrator/domain/phase.py` (extends T006)

**Parallel?**: No (depends on T006, T007)

**Notes**:
- Define `InvalidStateTransitionError` exception class
- Lock must be reentrant (use `threading.RLock`)

---

### Subtask T009 – Implement OrchestratorResult domain model

**Purpose**: Aggregate final workflow execution results.

**Steps**:
1. Add `OrchestratorResult` dataclass to `src/orchestrator/domain/models.py`
2. Include all fields from data-model.md
3. Define `ResultStatus` enum: `success`, `partial`, `failed`
4. Add class method `from_phases(phases: List[WorkflowPhase]) -> OrchestratorResult`:
   - Count completed vs total phases
   - Sum total retries across all phases
   - Determine status: success if all completed, partial if some completed, failed if none
   - Extract failed_phase if any phase failed
   - Aggregate error_summary from phase error_messages

**Files**:
- `src/orchestrator/domain/models.py` (extend T003 output)

**Parallel?**: Yes (separate from phase models)

---

### Subtask T010 – Implement ArtifactMetadata domain model

**Purpose**: Extract and validate Spec-Kitty artifact metadata.

**Steps**:
1. Add `ArtifactMetadata` dataclass to `src/orchestrator/domain/models.py`
2. Add fields: `artifact_type`, `path`, `frontmatter`, `mandatory_sections`, `present_sections`, `clarifications_needed`, `is_complete`
3. Add `from_markdown(path: Path) -> ArtifactMetadata` class method:
   - Read file content
   - Parse YAML frontmatter between `---` delimiters
   - Extract section headers (lines starting with `##`)
   - Count `[NEEDS CLARIFICATION: ...]` markers
   - Determine `is_complete`: no clarifications + all mandatory sections present
4. Define `mandatory_sections` per artifact type:
   - spec: Overview, Requirements, Success Criteria
   - plan: Technical Context, Project Structure, Phase Gates
   - tasks: Work Package sections

**Files**:
- `src/orchestrator/domain/models.py` (extend T003 output)

**Parallel?**: Yes

**Notes**:
- Use `yaml.safe_load()` for frontmatter parsing
- Use `re.findall(r'^## (.+)$', content, re.MULTILINE)` for section extraction

---

### Subtask T011 – Add thread-safety to phase state updates

**Purpose**: Ensure phase state can be safely updated from multiple threads.

**Steps**:
1. In `WorkflowPhase`, add `self._lock = threading.RLock()`
2. Wrap all state-modifying methods with lock:
   ```python
   def transition_to(self, status: PhaseStatus):
       with self._lock:
           if not self.can_transition_to(status):
               raise InvalidStateTransitionError(...)
           self.status = status
           # ... update timestamps etc.
   ```
3. Make `status` property thread-safe with lock:
   ```python
   @property
   def status(self) -> PhaseStatus:
       with self._lock:
           return self._status

   @status.setter
   def status(self, value: PhaseStatus):
       with self._lock:
           self._status = value
   ```
4. Add thread-safe `increment_attempts()` method
5. **Identify mutable fields requiring synchronization**:
   - `self._status` (PhaseStatus) - mutable via transitions
   - `self.attempts` (int) - mutable via increment_attempts()
   - `self.started_at` (datetime|None) - mutable on first start
   - `self.completed_at` (datetime|None) - mutable on terminal states
   - `self.error_message` (str|None) - mutable on failures
   - **Immutable fields** (no lock needed for reads): `name`, `artifact_path`, `validation_result`

**Files**:
- `src/orchestrator/domain/phase.py` (extends T006)

**Parallel?**: No (modifies T006 output)

**Notes**:
- RLock allows re-acquisition in same thread
- All reads of mutable state must also use lock
- Immutable fields can be read without synchronization

---

## Test Strategy

**Test File**: `tests/orchestrator/unit/test_workflow_state.py`

**Tests**:
1. `test_phase_status_enum_values()` - All enum values defined
2. `test_valid_transitions()` - Valid transitions succeed
3. `test_invalid_transitions_raise_error()` - Invalid transitions fail
4. `test_thread_safe_state_updates()` - Multiple threads can update state
5. `test_orchestrator_result_from_phases()` - Aggregates correctly
6. `test_artifact_metadata_parsing()` - Parses frontmatter and sections
7. `test_artifact_completeness_detection()` - Detects incomplete artifacts

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Thread-safety bugs | High | Use RLock consistently, test with threading |
| State machine complexity | Medium | Document all valid transitions in code comments |
| Markdown parsing edge cases | Low | Handle malformed frontmatter gracefully |

---

## Review Guidance

**Acceptance Checkpoints**:
1. All enum values match data-model.md exactly
2. State transition logic is exhaustive (no undefined paths)
3. Thread-safety implemented with RLock
4. OrchestratorResult aggregation logic handles all phase statuses
5. ArtifactMetadata detects `[NEEDS CLARIFICATION]` markers correctly

**Review Context**:
- Verify no race conditions in state updates
- Check that `can_transition_to()` matches `transition_to()` logic
- Ensure timestamp updates happen at correct transition points

---

## Activity Log

- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
- 2026-02-21T22:19:52Z – claude-opus – shell_pid=50813 – lane=doing – Assigned agent via workflow command
