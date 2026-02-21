# Agent Protocol Contract: Claude Code Subprocess Communication

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Contract Type**: Agent Communication Protocol
**Version**: 1.0.0

## Overview

This contract defines the communication protocol between the Python orchestrator and the Claude Code CLI subprocess. The orchestrator manages the subprocess via stdin/stdout using a JSON-based command/response protocol.

## Transport

**Method**: Subprocess stdin/stdout
**Format**: Line-delimited JSON (JSONL)
**Encoding**: UTF-8
**Buffering**: Line-buffered (`\n` delimiter)

## Connection Lifecycle

```
Orchestrator                    Claude Code Subprocess
     │                                  │
     │  POPEN(cmd, stdin=PIPE,          │
     │          stdout=PIPE)             │
     ├─────────────────────────────────>│
     │                                  │
     │  JSON command                    │
     ├─────────────────────────────────>│
     │                                  │
     │                        [Process command]
     │                                  │
     │  JSON response                   │
     │<─────────────────────────────────┤
     │                                  │
     │  [Repeat for each command]       │
     │                                  │
     │  terminate() / close()            │
     ├─────────────────────────────────>│
     │                                  │
```

## Command Format

### Request

```json
{
  "id": "uuid-v4",
  "type": "spec-kitty",
  "command": "/spec-kitty.specify",
  "args": {
    "description": "Feature description",
    "feature_name": "my-feature",
    "auto_advance": false
  },
  "timeout": 300
}
```

**Fields**:
- `id` (string, required): Unique request identifier (UUID v4)
- `type` (string, required): Command type (`spec-kitty`, `system`, `status`)
- `command` (string, required): Spec-Kitty slash command or system command
- `args` (object, optional): Command arguments
- `timeout` (int, optional): Request timeout in seconds

### Response

```json
{
  "id": "uuid-v4",
  "status": "success",
  "data": {
    "phase": "specify",
    "artifact_path": "kitty-specs/001-my-feature/spec.md",
    "requires_input": false,
    "message": "Specification created"
  }
}
```

**Success Response Fields**:
- `id` (string, required): Matching request ID
- `status` (string, required): "success"
- `data` (object, required): Response data
- `message` (string, optional): Human-readable message

**Error Response Fields**:
```json
{
  "id": "uuid-v4",
  "status": "error",
  "error": {
    "code": "COMMAND_FAILED",
    "message": "Failed to execute /spec-kitty.specify",
    "details": {
      "exit_code": 1,
      "stderr": "Error: Feature description required"
    }
  }
}
```

- `status` (string, required): "error"
- `error` (object, required): Error details
  - `code` (string, required): Error code
  - `message` (string, required): Error message
  - `details` (object, optional): Additional error context

## Command Types

### spec-kitty Commands

Execute Spec-Kitty slash commands.

**Available Commands**:
- `/spec-kitty.specify`
- `/spec-kitty.research`
- `/spec-kitty.plan`
- `/spec-kitty.tasks`
- `/spec-kitty.implement <wp-number>`
- `/spec-kitty.review <task-id>`
- `/spec-kitty.accept`

**Request Format**:
```json
{
  "id": "uuid",
  "type": "spec-kitty",
  "command": "/spec-kitty.specify",
  "args": {
    "description": "Feature description text",
    "auto_advance": false
  }
}
```

**Response Format**:
```json
{
  "id": "uuid",
  "status": "success",
  "data": {
    "phase": "specify",
    "artifact_path": "kitty-specs/001-feature/spec.md",
    "completed": true
  }
}
```

### System Commands

Control and query subprocess state.

**Available Commands**:
- `status` - Get current state
- `ping` - Health check
- `feature` - Get current feature context
- `artifact` - Read artifact content

**Request Format**:
```json
{
  "id": "uuid",
  "type": "system",
  "command": "status"
}
```

**Response Format**:
```json
{
  "id": "uuid",
  "status": "success",
  "data": {
    "state": "idle",
    "current_feature": "001-feature",
    "current_phase": "plan",
    "claude_code_version": "2.1.0",
    "spec_kitty_version": "0.11.0"
  }
}
```

### Validation Commands

Validate Spec-Kitty artifacts.

**Command**: `validate`

**Request Format**:
```json
{
  "id": "uuid",
  "type": "validation",
  "command": "validate",
  "args": {
    "artifact_type": "spec",
    "artifact_path": "kitty-specs/001-feature/spec.md"
  }
}
```

**Response Format**:
```json
{
  "id": "uuid",
  "status": "success",
  "data": {
    "valid": true,
    "issues": [],
    "recommendations": []
  }
}
```

## State Synchronization

### Artifact Detection

The orchestrator detects Spec-Kitty artifacts by:
1. Reading `kitty-specs/` directory
2. Parsing artifact frontmatter (YAML)
3. Checking artifact completion status

**State Query**:
```json
{
  "id": "uuid",
  "type": "system",
  "command": "artifact",
  "args": {
    "artifact_type": "spec"
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "success",
  "data": {
    "exists": true,
    "path": "kitty-specs/001-feature/spec.md",
    "status": "complete",
    "frontmatter": {
      "feature_number": "001",
      "slug": "001-my-feature",
      "status": "Draft"
    }
  }
}
```

### Phase Completion Detection

A phase is considered complete when:
1. Artifact file exists
2. Artifact has all mandatory sections
3. No `[NEEDS CLARIFICATION]` markers
4. Status is not "Draft"

**Validation**:
```json
{
  "id": "uuid",
  "type": "validation",
  "command": "is_complete",
  "args": {
    "phase": "specify"
  }
}
```

## Error Handling

### Timeout Handling

If command exceeds `timeout`:
1. Send SIGTERM to subprocess
2. Wait 5 seconds
3. If still running, send SIGKILL
4. Return timeout error response

```json
{
  "id": "uuid",
  "status": "error",
  "error": {
    "code": "TIMEOUT",
    "message": "Command exceeded timeout of 300s"
  }
}
```

### Parse Error Handling

If JSON cannot be parsed:
```json
{
  "id": "unknown",
  "status": "error",
  "error": {
    "code": "PARSE_ERROR",
    "message": "Invalid JSON: Unexpected token at line 5"
  }
}
```

### Unknown Command Handling

```json
{
  "id": "uuid",
  "status": "error",
  "error": {
    "code": "UNKNOWN_COMMAND",
    "message": "Unknown command: /spec-kitty.invalid"
  }
}
```

## Example Session

```json
// Orchestrator → Claude Code
{"id":"a1b2c3d4","type":"system","command":"ping"}

// Claude Code → Orchestrator
{"id":"a1b2c3d4","status":"success","data":{"alive":true}}

// Orchestrator → Claude Code
{"id":"e5f6g7h8","type":"spec-kitty","command":"/spec-kitty.specify","args":{"description":"Add user authentication"}}

// Claude Code → Orchestrator
{"id":"e5f6g7h8","status":"success","data":{"phase":"specify","artifact_path":"kitty-specs/021-auth/spec.md","completed":true}}

// Orchestrator → Claude Code
{"id":"i9j0k1l2","type":"validation","command":"validate","args":{"artifact_type":"spec","artifact_path":"kitty-specs/021-auth/spec.md"}}

// Claude Code → Orchestrator
{"id":"i9j0k1l2","status":"success","data":{"valid":true,"issues":[]}}
```

## Threading Considerations

### Producer-Consumer Pattern

```python
# Thread 1: Command producer
def send_commands():
    for command in workflow_commands:
        subprocess.stdin.write(json.dumps(command) + '\n')
        subprocess.stdin.flush()

# Thread 2: Response consumer
def read_responses():
    for line in subprocess.stdout:
        response = json.loads(line)
        handle_response(response)
```

### Thread Safety

- **Write side**: Single thread writes to stdin
- **Read side**: Single thread reads from stdout
- **Synchronization**: Use queue for response processing
- **Timeout**: Use `select` or `threading.Timer` for timeouts

## Implementation Requirements

### Orchestrator Must

1. Generate unique request IDs (UUID v4)
2. Match responses to requests by ID
3. Enforce timeouts per request
4. Handle subprocess termination gracefully
5. Validate response format before processing
6. Log all commands/responses in debug mode

### Claude Code Subprocess Must

1. Respond to every request (even errors)
2. Include matching request ID in response
3. Return structured errors with codes
4. Flush output after each response
5. Handle invalid JSON gracefully
6. Support concurrent request handling (queue internally)

## Backward Compatibility

### Version Negotiation

On connection, exchange versions:

```json
// Orchestrator → Claude Code
{"id":"version-check","type":"system","command":"version"}

// Claude Code → Orchestrator
{"id":"version-check","status":"success","data":{"protocol_version":"1.0","min_compatible":"1.0"}}
```

If versions incompatible, orchestrator aborts with clear error message.
