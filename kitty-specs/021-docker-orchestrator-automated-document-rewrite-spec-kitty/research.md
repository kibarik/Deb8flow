# Research: Docker Orchestrator for Automated Document Rewrite

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Date**: 2026-02-21
**Phase**: Phase 0 - Research

## Overview

This document consolidates research findings for the Docker Orchestrator feature, resolving outstanding technical questions from the implementation plan.

## Research Question 1: Docker SDK Best Practices for Python

### Decision: Use docker-py with context managers and explicit cleanup

**Rationale**:
- `docker` package (docker-py) is the official Python SDK maintained by Docker
- Context managers (`with` statements) ensure proper resource cleanup
- Explicit container removal prevents orphaned containers
- Log streaming via `attach()` with `logs=True` provides real-time output

**Implementation Pattern**:
```python
import docker

client = docker.from_env()

# Container lifecycle
container = client.containers.run(
    image="claude-code:latest",
    detach=True,
    volumes={host_path: {'bind': container_path, 'mode': 'rw'}},
    environment={"CLAUDE_API_KEY": api_key}
)

# Stream logs
for line in container.logs(stream=True, follow=True):
    print(line.decode('utf-8').strip())

# Cleanup
container.stop()
container.remove(force=True)
```

**Alternatives Considered**:
- **docker-py async API**: Rejected due to constitution's preference for simplicity
- **podman API**: Rejected due to Docker being the standard
- **docker-compose python library**: Rejected as overkill for single-container use case

### Best Practices Summary

1. **Always use context managers** or try/finally blocks for cleanup
2. **Set resource limits** (mem_limit, cpu_quota) to prevent resource exhaustion
3. **Use named containers** with timestamps for debugging
4. **Implement health checks** to verify container readiness
5. **Stream logs in separate thread** to avoid blocking main workflow
6. **Handle Docker daemon connection errors** gracefully with clear user messages

## Research Question 2: Claude Code CLI Subprocess Communication

### Decision: Use stdin/stdout with JSON-RPC-like protocol

**Rationale**:
- Claude Code CLI supports stdin-based command input
- Stdout provides structured output that can be parsed
- JSON format allows for structured responses and error handling
- Avoids complexities of socket-based IPC

**Implementation Pattern**:
```python
import subprocess
import json

process = subprocess.Popen(
    ['claude', '--interactive'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line buffered
)

# Send command
command = {'type': 'spec-kitty', 'action': 'specify', 'args': {...}}
process.stdin.write(json.dumps(command) + '\n')
process.stdin.flush()

# Read response
response_line = process.stdout.readline()
response = json.loads(response_line)
```

**Protocol Specification**:
- Commands sent as JSON objects, one per line
- Responses include: `status` (success/error), `data`, `error` (if applicable)
- Spec-Kitty commands: `/spec-kitty.specify`, `/spec-kitty.plan`, etc.
- State detection via examining kitty-specs directory for artifacts

**Alternatives Considered**:
- **Socket-based communication**: Rejected due to complexity
- **Temporary file exchange**: Rejected due to race conditions
- **Direct API calls**: Rejected per spec requirement (only orchestrate existing tools)

### Communication Contract

**Command Format**:
```json
{
  "type": "spec-kitty",
  "command": "/spec-kitty.specify",
  "args": {
    "description": "Feature description",
    "auto_advance": false
  },
  "timeout": 300
}
```

**Response Format**:
```json
{
  "status": "success",
  "data": {
    "phase": "specify",
    "artifact_path": "kitty-specs/.../spec.md",
    "requires_input": false
  }
}
```

## Research Question 3: Spec-Kitty Artifact Parsing

### Decision: Parse markdown files using regex and frontmatter detection

**Rationale**:
- Spec-Kitty artifacts are markdown with structured sections
- Frontmatter (YAML between `---`) contains metadata
- Section headers (`##`) indicate structure
- Validation criteria can be extracted from specific sections

**Artifact Structures**:

**spec.md**:
- Frontmatter: feature_number, slug, status
- Sections: Overview, Requirements, Success Criteria, Edge Cases
- Completion: All mandatory sections populated, no `[NEEDS CLARIFICATION]`

**plan.md**:
- Frontmatter: branch, date, spec link
- Sections: Technical Context, Project Structure, Phase Gates
- Completion: Phase gates checked off

**tasks.md**:
- Frontmatter: feature, work_packages
- Sections: WP## tasks with status
- Completion: All tasks have status

**Implementation Pattern**:
```python
import re
from pathlib import Path

def parse_spec(spec_path: Path) -> dict:
    content = spec_path.read_text()

    # Extract frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    frontmatter = yaml.safe_load(frontmatter_match.group(1))

    # Check for clarifications needed
    clarifications = re.findall(r'\[NEEDS CLARIFICATION:([^\]]+)\]', content)

    # Validate mandatory sections
    mandatory_sections = ['Overview', 'Requirements', 'Success Criteria']
    present_sections = re.findall(r'^## (.+)$', content, re.MULTILINE)

    return {
        'frontmatter': frontmatter,
        'clarifications_needed': len(clarifications),
        'mandatory_sections_complete': all(s in present_sections for s in mandatory_sections),
        'is_complete': len(clarifications) == 0
    }
```

## Research Question 4: Artifact Validation Prompts

### Decision: Use structured prompts with validation criteria

**Rationale**:
- Structured prompts ensure consistent validation
- Criteria-based prompts allow for specific validation rules
- Enables retry with context on validation failure

**Validation Prompt Template**:
```markdown
You are validating the quality of a {artifact_type} artifact for the Spec-Kitty workflow.

## Artifact Content
{artifact_content}

## Validation Criteria
1. Completeness: All mandatory sections are present and populated
2. Clarity: Requirements are unambiguous and testable
3. No placeholders: No [NEEDS CLARIFICATION] markers remain
4. Success criteria: All success criteria are measurable and technology-agnostic

## Your Task
Evaluate the artifact against each criterion and provide:
1. Overall assessment: PASS/FAIL
2. Specific issues found (if any)
3. Recommended improvements (if applicable)

Respond in JSON format:
{
  "overall": "PASS|FAIL",
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"]
}
```

**Retry Prompt**:
```markdown
Previous validation failed with the following issues:
{validation_issues}

Please revise the {artifact_type} to address these issues while maintaining the original intent.

Original {artifact_type}:
{artifact_content}
```

## Research Question 5: Threading Patterns for CLI Tools

### Decision: Use ThreadPoolExecutor with futures for concurrent I/O operations

**Rationale**:
- I/O-bound operations benefit from threading (container logs, agent communication)
- ThreadPoolExecutor provides clean API for managing concurrent tasks
- Futures allow for timeout and cancellation support
- Avoids complexity of async/await while providing necessary concurrency

**Implementation Pattern**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_with_concurrent_ops():
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit concurrent tasks
        log_future = executor.submit(stream_container_logs, container)
        health_future = executor.submit(check_container_health, container)
        agent_future = executor.submit(monitor_agent_process, process)

        # Wait for specific tasks with timeout
        try:
            health_result = health_future.result(timeout=30)
        except TimeoutError:
            health_future.cancel()
            raise OrchestratorError("Container health check timed out")

        # Collect results
        logs = log_future.result()
        agent_status = agent_future.result()
```

**Best Practices**:
1. **Limit thread pool size** to avoid resource exhaustion (3-5 threads for CLI)
2. **Always use timeouts** on future.result() calls
3. **Cancel futures** that are no longer needed
4. **Use daemon threads** for background tasks
5. **Share state via thread-safe queues** when needed
6. **Handle exceptions** in worker threads properly

**Threading Architecture for Orchestrator**:
- **Main thread**: Workflow orchestration, state machine
- **Thread 1**: Container log streaming
- **Thread 2**: Claude Code agent subprocess monitoring
- **Thread 3**: (optional) Progress reporter updates

## Summary of Decisions

| Question | Decision | Key Consideration |
|----------|----------|-------------------|
| Docker SDK | docker-py with context managers | Official SDK, clean resource management |
| CLI communication | stdin/stdout with JSON | Simplicity, structured data |
| Artifact parsing | Regex + YAML frontmatter | Markdown structure, metadata access |
| Validation prompts | Structured criteria-based | Consistency, retry support |
| Threading | ThreadPoolExecutor | I/O concurrency without async complexity |

## Next Steps

With research complete, proceed to Phase 1:
1. Generate `data-model.md` from entity definitions
2. Create contract specifications (config, CLI, agent protocol)
3. Draft `quickstart.md` with usage examples
4. Re-check constitution compliance post-design
