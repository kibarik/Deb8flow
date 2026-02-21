# CLI Contract: Orchestrator Command

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Contract Type**: CLI Interface
**Version**: 1.0.0

## Command Syntax

```bash
poetry run python scripts/orchestrator <source-file> <corrections-file> [options]
```

## Positional Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `source-file` | path | Yes | Path to the source document to process (any text file) |
| `corrections-file` | path | Yes | Path to the corrections file with revision instructions |

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | path | `<source>.corrected.<ext>` | Output file path |
| `--config, -c` | path | `config/debate_config.yaml` | Path to configuration file |
| `--max-retries` | int | (from config) | Override max retries per phase |
| `--timeout` | int | (from config) | Override container timeout in seconds |
| `--keep-containers` | flag | false | Keep containers running after completion |
| `--verbose, -v` | flag | (from config) | Enable verbose output |
| `--quiet, -q` | flag | false | Suppress console output (logs only) |
| `--dry-run` | flag | false | Validate input without executing |
| `--help, -h` | flag | - | Show help message |
| `--version` | flag | - | Show version information |

## Exit Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Workflow completed successfully, output file generated |
| 1 | PARTIAL | Workflow partially completed, some phases failed |
| 2 | FAILED | Workflow failed before completion |
| 3 | VALIDATION_ERROR | Input validation failed (missing files, invalid config) |
| 4 | DOCKER_ERROR | Docker unavailable or container operation failed |
| 5 | TIMEOUT | Workflow exceeded configured timeout |
| 130 | INTERRUPTED | User interrupted with Ctrl+C |

## Console Output Format

### Normal Output (Quiet Mode Disabled)

```
[ORCHESTRATOR] Starting Docker Orchestrator v1.0.0
[ORCHESTRATOR] Configuration loaded from: config/debate_config.yaml
[ORCHESTRATOR] Validating prerequisites...
[ORCHESTRATOR] ✓ Docker available (Docker version 27.0.0)
[ORCHESTRATOR] ✓ Claude Code CLI available (version 2.1.0)
[ORCHESTRATOR] ✓ Spec-Kitty CLI available (version 0.11.0)
[ORCHESTRATOR] Starting containers...
[ORCHESTRATOR] Container started: claude-orchestrator-abc123
[ORCHESTRATOR] Reading source file: docs/spec.md (1247 lines)
[ORCHESTRATOR] Reading corrections file: reviews/changes.md (23 items)
[ORCHESTRATOR]
[ORCHESTRATOR] Phase: specify → Running /spec-kitty.specify
[ORCHESTRATOR] Phase: specify → Artifact generated
[ORCHESTRATOR] Phase: specify → Validating spec...
[ORCHESTRATOR] Phase: specify → Validation passed (1/1 attempts)
[ORCHESTRATOR]
[ORCHESTRATOR] Phase: research → Running /spec-kitty.research
[ORCHESTRATOR] Phase: research → Research complete
[ORCHESTRATOR]
[ORCHESTRATOR] Phase: plan → Running /spec-kitty.plan
[ORCHESTRATOR] Phase: plan → Artifact generated
[ORCHESTRATOR] Phase: plan → Validating plan...
[ORCHESTRATOR] Phase: plan → Validation passed (1/1 attempts)
[ORCHESTRATOR]
... (continues for tasks, implement, review, accept)
[ORCHESTRATOR]
[ORCHESTRATOR] Copying corrected output...
[ORCHESTRATOR] Output written to: docs/spec.corrected.md
[ORCHESTRATOR] Stopping container...
[ORCHESTRATOR] ✓ Container stopped and removed
[ORCHESTRATOR]
[ORCHESTRATOR] Complete: 7/7 phases successful, 0 retries, 12m 34s total
```

### Retry Output

```
[ORCHESTRATOR] Phase: specify → Validating spec...
[ORCHESTRATOR] Phase: specify → Validation failed: Incomplete requirements section
[ORCHESTRATOR] Phase: specify → Retrying (1/3)...
[ORCHESTRATOR] Phase: specify → Running /spec-kitty.specify (retry)
[ORCHESTRATOR] Phase: specify → Validation passed (2/2 attempts)
```

### Error Output

```
[ORCHESTRATOR] ERROR: Docker daemon is not running
[ORCHESTRATOR] HINT: Start Docker with: open -a Docker (macOS) or systemctl start docker (Linux)
[ORCHESTRATOR] EXIT CODE: 4
```

### Verbose Output

```
[ORCHESTRATOR] [DEBUG] Loading config from config/debate_config.yaml
[ORCHESTRATOR] [DEBUG] Config: max_retries=3, validation_timeout=30
[ORCHESTRATOR] [DEBUG] Container command: docker run -d --name claude-orchestrator-abc123 ...
[ORCHESTRATOR] [DEBUG] Agent process PID: 12345
...
```

### Quiet Mode

```
[ORCHESTRATOR] Processing: docs/spec.md
[ORCHESTRATOR] Complete: Output written to docs/spec.corrected.md
```

### Dry Run Output

```
[ORCHESTRATOR] Dry run mode - no execution
[ORCHESTRATOR] ✓ Source file exists: docs/spec.md
[ORCHESTRATOR] ✓ Corrections file exists: reviews/changes.md
[ORCHESTRATOR] ✓ Output path writable: docs/spec.corrected.md
[ORCHESTRATOR] ✓ Docker available
[ORCHESTRATOR] ✓ Configuration valid
[ORCHESTRATOR] Dry run complete - ready to execute
```

## Input Validation

### Source File Validation

**Checks**:
1. File exists and is readable
2. File is text-based (detected via mime-type or extension)
3. File size is reasonable (<10MB default, configurable)

**Errors**:
- File not found: `VALIDATION_ERROR` (code 3)
- File not readable: `VALIDATION_ERROR` (code 3)
- File too large: `VALIDATION_ERROR` (code 3)
- Binary file detected: `VALIDATION_ERROR` (code 3)

### Corrections File Validation

**Checks**:
1. File exists and is readable
2. File contains parseable text (markdown or plain text)
3. File is not empty (after whitespace stripping)

**Errors**:
- Same as source file validation

### Configuration Validation

**Checks**:
1. Config file exists or defaults available
2. YAML is valid
3. All required values present or have defaults
4. Values match schema constraints

**Errors**:
- Config invalid: `VALIDATION_ERROR` (code 3)

### Docker Validation

**Checks**:
1. Docker daemon is running
2. Docker API is accessible
3. User has permission to run containers

**Errors**:
- Docker not available: `DOCKER_ERROR` (code 4)
- Permission denied: `DOCKER_ERROR` (code 4)

## Examples

### Basic Usage

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md
```

### Custom Output Path

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md -o docs/updated-spec.md
```

### Verbose Mode

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md --verbose
```

### Keep Containers for Debugging

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md --keep-containers
```

### Dry Run

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md --dry-run
```

### Custom Config File

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md -c config/production.yaml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCHESTRATOR_CONFIG` | Override config file path | `config/debate_config.yaml` |
| `ORCHESTRATOR_LOG_DIR` | Override log directory | `.orchestrator/logs` |
| `ORCHESTRATOR_DOCKER_IMAGE` | Override Docker image | `claude-code:latest` |
| `CLAUDE_API_KEY` | Claude API key for container | Required |

## Signal Handling

### SIGINT (Ctrl+C)

**Behavior**:
1. Set flag to stop workflow after current phase
2. Wait for current container operation to complete (max 30s)
3. Stop containers gracefully
4. Write partial results to output file
5. Exit with code 130 (INTERRUPTED)
6. Display summary of completed phases

### SIGTERM

**Behavior**: Same as SIGINT

## Progress Indication

### Phase Progress

Displayed as: `[ORCHESTRATOR] Phase: <name> → <status>`

**Status values**:
- `Running /spec-kitty.<phase>` - Phase starting
- `Artifact generated` - Phase produced artifact
- `Validating...` - Validation in progress
- `Validation passed` - Validation successful
- `Validation failed` - Validation failed, will retry
- `Retrying (N/M)` - Retry attempt N of M
- `Complete` - Phase finished successfully

### Overall Progress

At end of execution:
```
[ORCHESTRATOR] Complete: <completed>/<total> phases successful, <retries> retries, <duration> total
```
