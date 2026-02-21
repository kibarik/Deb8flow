---
work_package_id: WP04
title: Claude Code Agent Communication
lane: planned
dependencies: []
subtasks:
- T019
- T020
- T021
- T022
- T023
- T024
- T025
- T026
phase: Phase 1 - Infrastructure
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP04 – Claude Code Agent Communication

Implement subprocess communication with Claude Code CLI using JSON-based protocol.

## Objectives & Success Criteria

**Success Criteria**:
- Claude Code subprocess starts with stdin/stdout pipes
- JSON commands sent with UUID tracking
- Responses parsed and matched to requests by UUID
- Timeout handling terminates hung subprocess (SIGTERM, then SIGKILL)
- Subprocess cleanup works on all exit paths
- Retry logic handles transient failures
- Spec-Kitty command helpers send correct slash commands

## Context & Constraints

**Supporting Documents**:
- Research: [kitty-specs/.../research.md](../research.md) - Claude Code CLI subprocess communication
- Contract: [kitty-specs/.../contracts/agent-protocol.md](../contracts/agent-protocol.md) - Full protocol spec
- Data Model: [kitty-specs/.../data-model.md](../data-model.md) - State synchronization

**Constraints**:
- Must use subprocess.Popen (not asyncio subprocess)
- JSONL format: one JSON object per line with newline delimiter
- UUID v4 for request/response matching
- No custom LLM or agent kernels (per FR-024)

## Subtasks & Detailed Guidance

### Subtask T019 – Create ClaudeCodeAgent infrastructure class

**Purpose**: Define the agent class structure.

**Steps**:
1. Create `src/orchestrator/infrastructure/claude_code_agent.py`
2. Define `ClaudeCodeAgent` class with attributes:
   - `subprocess: Optional[subprocess.Popen]`
   - `pending_requests: Dict[str, concurrent.futures.Future]`
   - `config: OrchestratorConfig`
3. Add stub methods for T020-T026

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (new file, ~200 lines)

**Parallel?**: Yes

---

### Subtask T020 – Implement subprocess start with stdin/stdout pipes

**Purpose**: Start Claude Code CLI subprocess with correct configuration.

**Steps**:
1. Implement `start(self) -> None`:
   - Build command: `['claude', '--interactive']` (or equivalent)
   - Create Popen with `stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1`
   - Start response reader thread (for T022)
   - Store in `self.subprocess`

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T021 – Implement JSON command sending with UUID

**Purpose**: Send structured commands to subprocess.

**Steps**:
1. Implement `send_command(self, command: str, args: dict, timeout: int) -> dict`:
   - Generate UUID v4
   - Build request dict: `{id, type: "spec-kitty", command, args, timeout}`
   - Write JSON + newline to stdin
   - Flush stdin
   - Create Future, store in pending_requests
   - Wait for Future with timeout
   - Return response dict

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T022 – Implement response parsing and UUID matching

**Purpose**: Read and route responses to waiting futures.

**Steps**:
1. Implement `_read_responses()` in background thread:
   - Read line from stdout: `line = self.subprocess.stdout.readline()`
   - Parse JSON: `response = json.loads(line)`
   - Extract UUID from response.id
   - Find matching Future in pending_requests
   - Set Future result with response
   - Remove from pending_requests
2. Handle parse errors: log error, continue (don't crash)

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T023 – Implement timeout handling with SIGTERM/SIGKILL

**Purpose**: Terminate hung subprocess gracefully then forcefully.

**Steps**:
1. Implement timeout in `send_command()` using threading.Timer:
   - Create Timer that calls `_terminate_subprocess()`
   - On timeout: send SIGTERM, wait 5 seconds
   - If still running: send SIGKILL
   - Set Future with TimeoutError exception
2. Implement `_terminate_subprocess()`:
   - `self.subprocess.send_signal(signal.SIGTERM)`
   - `time.sleep(5)`
   - If poll() is None: `self.subprocess.kill()`

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T024 – Implement subprocess cleanup and termination

**Purpose**: Clean up subprocess resources on all exit paths.

**Steps**:
1. Implement `stop(self)`:
   - Stop response reader thread
   - Terminate subprocess if running
   - Wait for subprocess (timeout=5)
   - Close stdin/stdout/stderr pipes
   - Set `self.subprocess = None`
2. Add to `__del__`: call `stop()` if not stopped

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T025 – Add retry logic for transient subprocess failures

**Purpose**: Retry commands on transient failures (timeout, parse error).

**Steps**:
1. Modify `send_command()` to retry up to config.max_retries
2. Retry on: TimeoutError, JSONDecodeError, subprocess timeout
3. Do NOT retry on: other exceptions, validation failures
4. Add delay between retries: 1 second * attempt_number
5. Log retry attempts

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

### Subtask T026 – Implement Spec-Kitty command helpers

**Purpose**: Provide convenient methods for Spec-Kitty slash commands.

**Steps**:
1. Add helper methods:
   - `run_specify(description: str) -> dict`
   - `run_research() -> dict`
   - `run_plan() -> dict`
   - `run_tasks() -> dict`
   - `run_implement(wp_number: str) -> dict`
   - `run_review(task_id: str) -> dict`
   - `run_accept() -> dict`
2. Each helper calls `send_command()` with appropriate command and args

**Files**:
- `src/orchestrator/infrastructure/claude_code_agent.py` (extends T019)

**Parallel?**: No

---

## Test Strategy

**Test File**: `tests/orchestrator/unit/test_claude_code_agent.py`

**Tests**:
1. `test_subprocess_starts_with_pipes()` - Mock Popen
2. `test_send_command_with_uuid()` - Verify UUID generation
3. `test_response_matching_by_uuid()` - Mock response routing
4. `test_timeout_terminates_subprocess()` - Mock Timer
5. `test_stop_cleans_up_resources()` - Mock cleanup
6. `test_retry_on_transient_failure()` - Mock retries

**Run Command**: `poetry run pytest tests/orchestrator/unit/test_claude_code_agent.py -v`

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Claude Code CLI doesn't support stdin/stdout | High | Verify with actual CLI, have fallback plan |
| Subprocess buffers output | Medium | Use line-buffered mode (bufsize=1) |
| Race condition in timeout handling | High | Use threading.Lock around subprocess access |

---

## Review Guidance

**Acceptance Checkpoints**:
1. Subprocess starts with correct flags (text=True, bufsize=1)
2. UUIDs are unique and properly tracked
3. Response reader runs in background thread
4. Timeout uses SIGTERM then SIGKILL pattern
5. Retry logic has exponential backoff
6. Spec-Kitty helpers use correct slash commands

**Review Context**:
- Verify that pending_requests doesn't leak memory
- Check that thread terminates cleanly
- Ensure no deadlock between send and receive threads

---

## Activity Log

- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
