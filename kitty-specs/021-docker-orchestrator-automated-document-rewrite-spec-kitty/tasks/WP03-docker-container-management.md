---
work_package_id: WP03
title: Docker Container Management
lane: "doing"
dependencies: [WP01]
base_branch: 021-docker-orchestrator-automated-document-rewrite-spec-kitty-WP02
base_commit: b8709ff21832280547a97707d77a0d508d2dd9e8
created_at: '2026-02-21T22:22:23.885678+00:00'
subtasks:
- T012
- T013
- T014
- T015
- T016
- T017
- T018
- T018-A
- T018-B
phase: Phase 1 - Infrastructure
assignee: ''
agent: ''
shell_pid: "51418"
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-21T19:45:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP03 – Docker Container Management

Implement Docker container lifecycle management using Docker SDK with health checks, log streaming, and cleanup.

## Objectives & Success Criteria

**Success Criteria**:
- `DockerClient` wrapper manages container lifecycle (start, health check, stop, remove)
- Containers start with correct volume mounts, environment variables, and resource limits
- Health check polls container status until ready or timeout
- Log streaming captures container output in real-time via ThreadPoolExecutor
- Containers stop and remove cleanly on all exit paths (success, failure, interrupt)
- Pre-flight validation checks Docker availability and returns actionable errors

## Context & Constraints

**Supporting Documents**:
- Research: [kitty-specs/.../research.md](../research.md) - Docker SDK best practices
- Spec: [kitty-specs/.../spec.md](../spec.md) - FR-005, FR-018, FR-019
- Config: [kitty-specs/.../contracts/config-schema.yaml](../contracts/config-schema.yaml) - Container settings

**Constraints**:
- Must use docker-py (Docker Python SDK), not docker-compose
- Container name must be unique to avoid collisions (use timestamp + uuid suffix)
- Resource limits from config must be applied (memory, CPU)
- Cleanup must happen even on exceptions (use try/finally or context manager)

## Subtasks & Detailed Guidance

### Subtask T012 – Create DockerClient wrapper adapter

**Purpose**: Wrap Docker SDK with orchestration-specific interface.

**Steps**:
1. Create `src/orchestrator/adapters/docker_client.py`
2. Import docker and typing
3. Define `DockerClient` class:
   ```python
   class DockerClient:
       def __init__(self, config: OrchestratorConfig):
           self.config = config
           self.client = docker.from_env()
           self.container = None
   ```
4. Add methods stubs for T013-T018
5. Add `__enter__` and `__exit__` for context manager support
6. Add pre-flight check: `is_available() -> bool` method

**Files**:
- `src/orchestrator/adapters/docker_client.py` (new file, ~150 lines)

**Parallel?**: Yes

---

### Subtask T013 – Implement container start with volume mounts

**Purpose**: Start container with correct configuration.

**Steps**:
1. Implement `start(self, source_path: Path, workdir: Path) -> str`:
   - Generate unique container name: `claude-orchestrator-{timestamp}-{uuid4[:8]}`
   - Prepare volume mounts: {workdir: {'bind': '/workspace', 'mode': 'rw'}}
   - Set environment: {CLAUDE_API_KEY: os.getenv('CLAUDE_API_KEY')}
   - Set resource limits: mem_limit=config.container_memory_limit
   - Run container detached: `self.client.containers.run(...)`
   - Return container ID

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012)

---

### Subtask T014 – Implement container health check

**Purpose**: Poll container until ready or timeout.

**Steps**:
1. Implement `health_check(self) -> bool`:
   - Poll `container.status` every 1 second
   - Return True when status is "running"
   - Return False if timeout (config.container_timeout)
   - Log progress: "Waiting for container to be ready..."

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012, T013)

---

### Subtask T015 – Implement real-time log streaming

**Purpose**: Capture container logs in background thread.

**Steps**:
1. Implement `stream_logs(self, callback: Callable[[str], None])`:
   - Use `ThreadPoolExecutor` with 1 worker
   - Submit log streaming task: `for line in self.container.logs(stream=True, follow=True): callback(line.decode('utf-8'))`
   - Store future for cancellation
   - Implement `stop_log_streaming()` to cancel future
2. Log callback writes to Orchestrator's log file

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012, T013)

---

### Subtask T016 – Implement container stop and cleanup

**Purpose**: Ensure containers stop and remove on all exit paths.

**Steps**:
1. Implement `stop(self, force: bool = False)`:
   - Call `self.container.stop(timeout=10)`
   - If force: `self.container.kill()`
   - Always call `self.container.remove(force=True)`
   - Set `self.container = None`
2. Implement `__exit__` to call `stop()` automatically
3. Add exception handling: if container already stopped, ignore

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012, T013)

---

### Subtask T017 – Add pre-flight Docker availability validation

**Purpose**: Check Docker is available before starting workflow.

**Steps**:
1. Implement `is_available(self) -> tuple[bool, str]`:
   - Try `docker.from_env()`
   - Try `client.ping()`
   - Try `client.version()`
   - Return (True, "") or (False, error_message)
2. Add check in `start()`: if not available, raise `DockerUnavailableError`

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012)

---

### Subtask T018-A – Add Docker image pre-flight check

**Purpose**: Verify required Docker image exists before starting container.

**Steps**:
1. Implement `check_image(self) -> tuple[bool, str]`:
   - Try `client.images.get(self.config.docker_image)`
   - If image exists, return (True, "")
   - If image not found, try `client.images.pull(self.config.docker_image)`
   - If pull succeeds, return (True, "pulled")
   - If pull fails, return (False, error_message)
2. Add check in `start()` before container run:
   - Call `check_image()`
   - If failed, raise `DockerImageError` with actionable message
3. Log image status: "Using image: {image_name} (cached)" or "Using image: {image_name} (pulled)"

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012, T017)

**Notes**:
- Pull may take time; consider config option to skip pull (use --no-pull flag)
- Handle network errors during pull gracefully

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012)

---

### Subtask T018-B – Handle container resource limits and timeouts

**Purpose**: Apply resource limits from configuration.

**Steps**:
1. In `start()`, apply resource limits:
   - `mem_limit=self.config.container_memory_limit`
   - `cpu_quota=int(self.config.container_cpu_quota * 100000)` (Docker uses 100000 as base)
2. Set `nano_cpus` for CPU quota
3. Add `detach=True`, `remove=False` (we manage removal)
4. Validate limits are positive numbers

**Files**:
- `src/orchestrator/adapters/docker_client.py` (extends T012)

**Parallel?**: No (depends on T012, T013)

---

## Test Strategy

**Test File**: `tests/orchestrator/unit/test_docker_client.py`

**Tests**:
1. `test_container_starts_with_volume_mounts()` - Mock docker.run
2. `test_health_check_returns_true_when_ready()` - Mock container.status
3. `test_health_check_times_out()` - Mock timeout
4. `test_log_streams_in_background()` - Mock ThreadPoolExecutor
5. `test_stop_cleans_up_container()` - Mock container.stop/remove
6. `test_is_available_checks_docker()` - Mock docker.from_env

**Run Command**: `poetry run pytest tests/orchestrator/unit/test_docker_client.py -v`

**Fixtures**: Mock `docker.from_env()` return value

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Container name collisions | Medium | Use timestamp + UUID suffix |
| Log streaming thread doesn't terminate | High | Use Future cancellation, timeout |
| Cleanup doesn't run on exception | High | Use try/finally or context manager |

---

## Review Guidance

**Acceptance Checkpoints**:
1. Container starts with unique name
2. Volume mounts map host workspace to /workspace
3. Health check polls with configurable timeout
4. Log streaming runs in background thread
5. Cleanup happens in finally block
6. Pre-flight check returns actionable error messages

**Review Context**:
- Verify resource limits are applied correctly (CPU quota math)
- Check that context manager pattern ensures cleanup
- Ensure thread-safe access to self.container

---

## Activity Log

- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
