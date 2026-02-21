# Feature Specification: Docker Orchestrator for Automated Document Rewrite via Claude Code + Spec-Kitty

**Feature Branch**: `021-docker-orchestrator-automated-document-rewrite-spec-kitty`
**Created**: 2026-02-21T19:44:11Z
**Status**: Draft
**Input**: User description: "Создать Docker-оркестратор для автоматической доработки документов через Claude Code + Spec-Kitty. Запуск: poetry run python scripts/rewrite <source-file> <corrections-file>. В Python-скрипте поверх Claude Code работает отдельный AI-агент‑«вайб‑кодер», который следит за состоянием проекта, анализирует артефакты Spec-Kitty (spec, plan, tasks и т.д.) и сам отправляет команды в Claude Code/Spec‑Kit, его единственная миссия — довести весь workflow от начала до конца. Под капотом скрипт управляет Docker-контейнерами с преднастроенным окружением Claude Code + Spec-Kitty и необходимыми MCP/CLI‑инструментами, прогоняя документ через полный цикл: specify → research → plan → tasks → implement → review → accept. Режим работы полностью автоматический задаётся в config/debate_config.yaml, все паузы после /specify, /plan, /tasks, /implement обрабатываются этим агентом без участия человека, включая базовую валидацию качества промежуточных артефактов и ограниченные ретраи при неудаче. Выход: всегда новый исправленный файл рядом с исходником, оригинал сохраняется. Никакой кастомной разработки ядра агентов или собственных LLM — только оркестрация и настройка поверх уже существующих инструментов Claude Code + Spec-Kitty."

## Overview

This feature creates a Docker-based orchestration system that automatically processes text documents through the complete Spec-Kitty workflow. Unlike the existing `rewrite` script which applies direct revisions with debate verification, this orchestrator manages the full feature development lifecycle: from initial specification through implementation and acceptance. The system runs in one-shot mode (one document per execution) and uses a stateful AI agent to validate artifacts and perform conditional retries.

## Background

The existing `rewrite` script applies revisions directly to documents but is limited to simple edit operations. Users need a way to:

1. **Run full Spec-Kitty workflows** automatically without manual intervention at each phase
2. **Process any text document** (markdown specs, PRDs, technical docs, code, mixed repositories)
3. **Validate artifacts** after each key phase (spec, plan, tasks, implement)
4. **Handle failures gracefully** with limited conditional retries
5. **Preserve originals** while generating corrected versions

The orchestrator solves these problems by:
- Managing Docker containers with preconfigured Claude Code + Spec-Kitty environment
- Running an AI agent that monitors project state and drives the workflow forward
- Automatically handling all Spec-Kitty pauses (specify, plan, tasks, implement)
- Providing configurable behavior via `config/debate_config.yaml`

## User Scenarios & Testing

### User Story 1 - Basic Document Rewrite (Priority: P1)

**Persona**: Developer who needs to update a technical specification based on a review document

**Flow**:
1. User has `docs/architecture.md` that needs updates per `reviews/arch-changes.md`
2. User invokes: `poetry run python scripts/orchestrator docs/architecture.md reviews/arch-changes.md`
3. System starts Docker containers with Claude Code + Spec-Kitty environment
4. AI agent reads source and corrections files
5. Agent runs `/spec-kitty.specify` to create initial specification
6. Agent validates generated spec, triggers retry if needed
7. Agent runs `/spec-kitty.research` to gather context
8. Agent runs `/spec-kitty.plan` to generate design artifacts
9. Agent validates plan quality
10. Agent runs `/spec-kitty.tasks` to create work packages
11. Agent runs `/spec-kitty.implement` for each work package
12. Agent runs `/spec-kitty.review` to validate implementation
13. Agent runs `/spec-kitty.accept` to finalize
14. System writes corrected output to `docs/architecture.corrected.md`
15. System stops containers and exits with summary

**Outcome**: Original preserved, new corrected file generated, full workflow completed automatically

**Why this priority**: This is the core value proposition - end-to-end automated document processing

**Independent Test**: Can be tested by running orchestrator on a simple markdown file with basic corrections and verifying the output file is created with corrections applied

**Acceptance Scenarios**:
1. **Given** a valid source file and corrections file, **When** orchestrator is invoked, **Then** corrected output file is generated and original is preserved
2. **Given** Docker is not available, **When** orchestrator is invoked, **Then** clear error message is displayed with setup instructions
3. **Given** workflow completes successfully, **When** orchestrator exits, **Then** exit code is 0 and summary shows all phases completed

---

### User Story 2 - Artifact Validation and Retry (Priority: P2)

**Persona**: Power user running orchestrator on complex document requiring multiple retry attempts

**Flow**:
1. User runs orchestrator with complex corrections
2. After `/spec-kitty.specify`, agent validates generated spec
3. Validation fails (spec is incomplete or unclear)
4. Agent triggers retry with additional context
5. On second attempt, validation passes
6. Similar validation/retry occurs after `/spec-kitty.plan`
7. Plan validation succeeds on first attempt
8. Workflow continues through remaining phases

**Outcome**: System handles validation failures gracefully with limited retries before failing

**Why this priority**: Ensures reliability and quality of generated artifacts

**Independent Test**: Can be tested by providing corrections that will initially fail validation (e.g., ambiguous requirements) and verifying retry behavior

**Acceptance Scenarios**:
1. **Given** spec validation fails, **When** retry limit not reached, **Then** agent retries with additional context
2. **Given** validation fails after max retries, **When** limit exceeded, **Then** orchestrator exits with error code and partial results
3. **Given** validation passes, **When** phase completes, **Then** workflow proceeds to next phase

---

### User Story 3 - Configurable Workflow Settings (Priority: P2)

**Persona**: DevOps engineer tuning orchestrator behavior for specific use cases

**Flow**:
1. User opens `config/debate_config.yaml`
2. User finds `orchestrator:` section with settings
3. User modifies `max_retries` from default 3 to 5
4. User adjusts `validation_timeout` from 30s to 60s
5. User optionally sets `auto_accept: true` to skip final acceptance prompt
6. User runs orchestrator with custom settings
7. System respects configured values throughout workflow

**Outcome**: Flexible behavior tuned to specific requirements

**Why this priority**: Enables customization without code changes

**Independent Test**: Can be tested by modifying config values and verifying they affect orchestrator behavior

**Acceptance Scenarios**:
1. **Given** config file exists, **When** orchestrator starts, **Then** settings are loaded from config
2. **Given** config file missing, **When** orchestrator starts, **Then** default values are used
3. **Given** invalid config value, **When** orchestrator starts, **Then** validation error with clear message

---

### User Story 4 - Progress Monitoring and Logging (Priority: P3)

**Persona**: User running orchestrator on large document that takes significant time

**Flow**:
1. User runs orchestrator command
2. Console displays real-time progress:
   ```
   [ORCHESTRATOR] Starting Docker containers...
   [ORCHESTRATOR] Containers ready
   [ORCHESTRATOR] Reading: docs/spec.md (1247 lines)
   [ORCHESTRATOR] Reading: reviews/changes.md (23 items)
   [ORCHESTRATOR] Phase: specify → Running /spec-kitty.specify
   [ORCHESTRATOR] Phase: specify → Artifact generated
   [ORCHESTRATOR] Phase: specify → Validating spec...
   [ORCHESTRATOR] Phase: specify → Validation passed
   [ORCHESTRATOR] Phase: research → Running /spec-kitty.research
   ...
   [ORCHESTRATOR] Complete: Output written to docs/spec.corrected.md
   [ORCHESTRATOR] Summary: 7 phases, 2 retries, 12m total
   ```
3. Detailed logs written to `.orchestrator/logs/` directory
4. User can interrupt with Ctrl+C and receive partial results summary

**Outcome**: Full visibility into workflow progress and ability to debug issues

**Why this priority**: Important for user experience and debugging

**Independent Test**: Can be tested by running orchestrator and verifying console output and log files

**Acceptance Scenarios**:
1. **Given** orchestrator running, **When** each phase starts/ends, **Then** console shows current phase and status
2. **Given** orchestrator completes, **When** finishing, **Then** summary shows phases, retries, and duration
3. **Given** user interrupts, **When** Ctrl+C pressed, **Then** graceful shutdown with partial results

---

### Edge Cases

- What happens when source file doesn't exist?
- What happens when corrections file is empty or malformed?
- What happens when Docker daemon is not running?
- What happens when Claude Code API quota is exceeded?
- What happens when Spec-Kitty workflow is updated (incompatible commands)?
- What happens when file permissions prevent writing output?
- What happens when container runs out of disk space?
- What happens when network connectivity is lost mid-workflow?
- What happens when source file contains non-UTF-8 content?
- What happens when corrections file contains conflicting instructions?

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide CLI interface accepting source file path and corrections file path
- **FR-002**: System MUST support any text-based file format (markdown, plain text, code files) without hard format restrictions
- **FR-003**: System MUST preserve original source file unchanged
- **FR-004**: System MUST write corrected output to new file with `.corrected.` suffix (e.g., `file.corrected.md`)
- **FR-005**: System MUST start Docker containers with preconfigured Claude Code + Spec-Kitty environment
- **FR-006**: System MUST run AI agent that monitors project state and drives Spec-Kitty workflow
- **FR-007**: System MUST execute full workflow: specify → research → plan → tasks → implement → review → accept
- **FR-008**: System MUST validate artifacts after each key phase (spec, plan, tasks, implement)
- **FR-009**: System MUST perform conditional retries when validation fails (up to configured limit)
- **FR-010**: System MUST handle all Spec-Kitty pauses automatically without user intervention
- **FR-011**: System MUST read configuration from `config/debate_config.yaml`
- **FR-012**: System MUST use default values when config file is missing or incomplete
- **FR-013**: System MUST display real-time progress to console showing current phase and status
- **FR-014**: System MUST write detailed logs to `.orchestrator/logs/` directory
- **FR-015**: System MUST exit with code 0 on successful completion
- **FR-016**: System MUST exit with non-zero code on failure
- **FR-017**: System MUST handle Ctrl+C gracefully with partial results summary
- **FR-018**: System MUST clean up Docker containers after completion (unless configured otherwise)
- **FR-019**: System MUST validate Docker availability before starting workflow
- **FR-020**: System MUST validate Claude Code + Spec-Kitty installation in containers
- **FR-021**: AI agent MUST analyze Spec-Kitty artifacts (spec.md, plan.md, tasks.md) to determine workflow state
- **FR-022**: AI agent MUST send appropriate commands to Claude Code/Spec-Kitty based on current state
- **FR-023**: System MUST run in one-shot mode (single execution per invocation, no daemon)
- **FR-024**: System MUST NOT implement custom LLM or agent kernels (only orchestrate existing tools)

### Key Entities

#### OrchestratorConfig

| Attribute | Type | Description |
|-----------|------|-------------|
| `max_retries` | int | Maximum retry attempts per phase (default: 3) |
| `validation_timeout` | int | Seconds to wait for validation (default: 30) |
| `auto_accept` | boolean | Skip final acceptance prompt (default: false) |
| `keep_containers` | boolean | Don't stop containers after completion (default: false) |
| `output_suffix` | string | Suffix for output files (default: ".corrected.") |
| `log_dir` | path | Directory for logs (default: ".orchestrator/logs") |
| `docker_image` | string | Container image to use (default: "claude-code:latest") |

#### WorkflowPhase

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Phase identifier (specify, research, plan, tasks, implement, review, accept) |
| `status` | enum | pending, running, completed, failed, retrying |
| `attempts` | int | Number of execution attempts |
| `artifact_path` | path | Path to generated artifact (if any) |
| `validation_result` | enum | passed, failed, skipped |

#### OrchestratorResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | enum | success, partial, failed |
| `phases_completed` | int | Number of phases successfully completed |
| `total_retries` | int | Total retry attempts across all phases |
| `duration_seconds` | int | Total execution time |
| `output_path` | path | Path to corrected output file |
| `failed_phase` | string | Name of phase that failed (if any) |
| `container_id` | string | Docker container ID for debugging |

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can process a 10-page markdown document with 20 corrections in under 15 minutes
- **SC-002**: Orchestrator completes full workflow without manual intervention in 95%+ of cases
- **SC-003**: Artifact validation catches 90%+ of incomplete or incorrect artifacts
- **SC-004**: System recovers from transient failures (API errors, network issues) via retries in 80%+ of cases
- **SC-005**: Exit codes correctly indicate success/failure for shell scripting integration
- **SC-006**: Console output provides sufficient detail for users to understand current phase and progress
- **SC-007**: Log files contain enough information to debug failures without reproducing
- **SC-008**: Original files are never modified (100% preservation)
- **SC-009**: Docker containers are cleaned up on successful completion (unless configured otherwise)
- **SC-010**: System validates prerequisites (Docker, Claude Code) before starting workflow

## Assumptions

1. **Docker is installed** and running on the host system
2. **Claude Code** and **Spec-Kitty** are available in the container image
3. **MCP/CLI tools** required by Spec-Kitty are preconfigured in containers
4. **Network connectivity** is available for Claude Code API calls
5. **Sufficient disk space** exists for container images and artifacts
6. **File permissions** allow reading source files and writing output files
7. **config/debate_config.yaml** exists or system can use defaults
8. **Source and corrections files** are compatible with Spec-Kitty workflow
9. **One execution per invocation** (no concurrent orchestrator instances sharing resources)
10. **No custom agent development** - only orchestration of existing Claude Code + Spec-Kitty tools

## Dependencies

### Internal Dependencies

1. **Existing rewrite script** (`scripts/rewrite`) - as reference for CLI pattern
2. **Configuration system** (`src/shared/config/`) - for loading debate_config.yaml
3. **Logging infrastructure** - for consistent log formatting
4. **Error handling patterns** - from existing rewrite implementation

### External Dependencies

1. **Docker Engine** - for container management
2. **Docker Python SDK** - for programmatic container control
3. **Claude Code CLI** - preinstalled in container image
4. **Spec-Kitty CLI** - preinstalled in container image
5. **Required MCP servers** - preinstalled and configured in container
6. **File system** - for reading/writing documents and artifacts

## Out of Scope

The following items are explicitly out of scope for this feature:

1. **Persistent daemon mode** - system runs one-shot only
2. **Batch processing** - only one document per invocation
3. **Custom LLM models** - only uses Claude Code via existing tools
4. **Agent kernel development** - only orchestrates existing Spec-Kitty
5. **Web UI** - CLI interface only
6. **Interactive debugging** - no breakpoint/step-through capabilities
7. **Version control integration** - no git commits or branch creation
8. **Multi-container orchestration** - single container pattern
9. **Docker Compose integration** - direct Docker SDK usage
10. **Parallel phase execution** - strictly sequential workflow
11. **Custom prompt engineering** - uses default Spec-Kitty prompts
12. **Container image building** - assumes pre-built image exists

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Spec-Kitty command interface changes | High | Medium | Version pin container image; clear error on incompatibility |
| Docker resource exhaustion | Medium | Low | Resource limits in config; pre-flight checks |
| Claude Code API rate limits | High | Medium | Configurable delays between API calls; retry with backoff |
| Validation accuracy too low | High | Medium | Tunable validation prompts; manual review opt-out |
| Container image not available | High | Low | Clear setup instructions; image pull with progress |
| File encoding issues | Medium | Low | Multiple encoding detection; clear error messages |
| Network interruption during workflow | Medium | Medium | State persistence; resume capability if feasible |
| Infinite loops in agent logic | High | Low | Phase timeout; maximum iteration limits |
| Output file already exists | Low | Medium | Timestamp suffix; configurable overwrite behavior |
| Insufficient disk space | Medium | Low | Pre-flight space check; clear error messages |

## Configuration

The following settings will be added to `config/debate_config.yaml`:

```yaml
orchestrator:
  # Workflow control
  max_retries: 3
  validation_timeout: 30
  auto_accept: false

  # Output settings
  output_suffix: ".corrected."
  timestamp_output: false

  # Container management
  docker_image: "claude-code:latest"
  keep_containers: false
  container_timeout: 3600

  # Logging
  log_dir: ".orchestrator/logs"
  log_level: "INFO"
  verbose: false

  # Phase configuration
  phases:
    - name: "specify"
      enabled: true
      validate: true
    - name: "research"
      enabled: true
      validate: false
    - name: "plan"
      enabled: true
      validate: true
    - name: "tasks"
      enabled: true
      validate: true
    - name: "implement"
      enabled: true
      validate: true
    - name: "review"
      enabled: true
      validate: false
    - name: "accept"
      enabled: true
      validate: false
```
