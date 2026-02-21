---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
  - "T004"
  - "T005"
title: "Foundation & Configuration"
phase: "Phase 0 - Foundation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2026-02-21T19:45:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt created via /spec-kitty.tasks"
dependencies: []
---

# Work Package Prompt: WP01 – Foundation & Configuration

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: ```python, ```bash

---

## Objectives & Success Criteria

Establish the project foundation with proper directory structure, configuration system, and shared utilities.

**Success Criteria**:
- `src/orchestrator/` directory created with clean architecture subdirectories (adapters/, application/, domain/, infrastructure/, prompts/)
- Docker SDK added to `pyproject.toml` dependencies
- `OrchestratorConfig` domain model implemented with all fields from data-model.md
- Configuration loads from `config/debate_config.yaml` with fallback to defaults
- Configuration validates all fields against schema rules (type, range, enum)
- Integration with existing `src/shared/config` system working

---

## Context & Constraints

**Supporting Documents**:
- Spec: [kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/spec.md](../spec.md) - FR-011, FR-012, Configuration section
- Plan: [kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/plan.md](../plan.md) - Project Structure section
- Data Model: [kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/data-model.md](../data-model.md) - OrchestratorConfig entity
- Config Contract: [kitty-specs/021-docker-orchestrator-automated-document-rewrite-spec-kitty/contracts/config-schema.yaml](../contracts/config-schema.yaml) - Full schema

**Architectural Decisions**:
- Follow existing `src/rewrite` clean architecture pattern
- Use Pydantic for configuration validation (aligns with existing config system patterns)
- Configuration is single-source-of-truth: loaded once, validated, then accessed as read-only
- Thread-safety not required for config (immutable after load)

**Constraints**:
- Must integrate with existing `src/shared/config` infrastructure
- Cannot modify existing config loading behavior (extend only)
- Docker SDK version must be compatible with Python 3.12+

---

## Subtasks & Detailed Guidance

### Subtask T001 – Create project structure and module hierarchy

**Purpose**: Establish the directory structure following clean architecture principles.

**Steps**:
1. Create `src/orchestrator/` directory with subdirectories:
   - `__init__.py` (empty, marks package)
   - `adapters/__init__.py`
   - `application/__init__.py`
   - `domain/__init__.py`
   - `infrastructure/__init__.py`
   - `prompts/__init__.py`
2. Add `__pycache__/` to `.gitignore` if not already present
3. Verify structure matches plan.md Project Structure section

**Files**:
- `src/orchestrator/__init__.py`
- `src/orchestrator/adapters/__init__.py`
- `src/orchestrator/application/__init__.py`
- `src/orchestrator/domain/__init__.py`
- `src/orchestrator/infrastructure/__init__.py`
- `src/orchestrator/prompts/__init__.py`

**Parallel?**: Yes (different directories, no dependencies)

**Notes**:
- Follow the exact structure from plan.md
- Reference `src/rewrite/` for naming conventions

---

### Subtask T002 – Add Docker dependency to pyproject.toml

**Purpose**: Enable Docker SDK usage for container management.

**Steps**:
1. Open `pyproject.toml`
2. Add `docker = {version = "^7.0.0"}` to dependencies (use ^ for minor version compatibility)
3. Run `poetry lock` to update lock file
4. Verify `poetry show docker` shows the package

**Files**:
- `pyproject.toml` (dependencies section)
- `poetry.lock` (auto-updated)

**Parallel?**: Yes (independent file change)

**Notes**:
- Docker SDK 7.0+ is required for modern Python APIs
- Version constraint allows patch updates but requires manual review for minor bumps

---

### Subtask T003 – Implement OrchestratorConfig domain model

**Purpose**: Create the configuration dataclass with all fields and validation.

**Steps**:
1. Create `src/orchestrator/domain/models.py`
2. Define `OrchestratorConfig` as a Pydantic `BaseModel` (or dataclass with `@dataclass` if Pydantic not used elsewhere)
3. Add all fields from data-model.md OrchestratorConfig entity:
   - `max_retries: int = 3`
   - `validation_timeout: int = 30`
   - `auto_accept: bool = False`
   - `keep_containers: bool = False`
   - `output_suffix: str = ".corrected."`
   - `timestamp_output: bool = False`
   - `overwrite_output: str = "error"` (enum: error|overwrite|timestamp)
   - `docker_image: str = "claude-code:latest"`
   - `container_timeout: int = 3600`
   - `container_memory_limit: Optional[str] = "2g"`
   - `container_cpu_quota: Optional[float] = 1.0`
   - `log_dir: str = ".orchestrator/logs"`
   - `log_level: str = "INFO"` (enum: DEBUG|INFO|WARNING|ERROR|CRITICAL)
   - `verbose: bool = False`
   - `claude_cli_path: Optional[str] = None` (optional path to Claude Code CLI)
   - `phases: List[PhaseConfig] = []`
4. Define nested `PhaseConfig` model with fields: `name`, `enabled`, `validate`, `timeout`
5. Add Pydantic validators for constraints:
   - `@validator('max_retries')` - check >= 0
   - `@validator('validation_timeout', 'container_timeout')` - check > 0
   - `@validator('log_level')` - check valid enum values
   - `@validator('overwrite_output')` - check valid enum values
   - `@validator('phases')` - check unique phase names

**Files**:
- `src/orchestrator/domain/models.py` (new file, ~150 lines)

**Parallel?**: Yes (independent model file)

**Notes**:
- Use Pydantic v2 syntax if available (check existing codebase patterns)
- Reference `src/shared/config/` for existing config patterns
- Include type hints for all fields
- Add docstrings for the class and each field

---

### Subtask T004 – Create configuration loader adapter

**Purpose**: Load configuration from debate_config.yaml with defaults and validation.

**Steps**:
1. Create `src/orchestrator/adapters/config_loader.py`
2. Import `DebateConfigFile` from `src.shared.config`
3. Define `load_orchestrator_config(config_path: Path) -> OrchestratorConfig`:
   - Call `DebateConfigFile.from_yaml_or_default(path=config_path, load_env=True)`
   - Extract `orchestrator:` section from config dict (use `.get('orchestrator', {})`)
   - If section missing, log warning and use all defaults
   - Validate dict against schema (Pydantic does this automatically)
   - Return `OrchestratorConfig(**orchestrator_dict)`
4. Define `ConfigValidationError` exception class
5. Add error handling for:
   - File not found: Use defaults, log warning
   - Invalid YAML: Raise `ConfigValidationError`
   - Invalid value: Pydantic raises `ValidationError`, wrap in `ConfigValidationError`
   - Unknown field: Log warning, continue (forward compatibility)

**Files**:
- `src/orchestrator/adapters/config_loader.py` (new file, ~100 lines)

**Parallel?**: No (depends on T003 for OrchestratorConfig)

**Notes**:
- Follow existing `src/rewrite/adapters/` patterns for adapter naming
- Use structured logging: `logger.warning()` not `print()`
- Import `OrchestratorConfig` from `src.orchestrator.domain.models`

---

### Subtask T005 – Add configuration schema validation

**Purpose**: Ensure all configuration values conform to schema rules.

**Steps**:
1. Add validation method to `OrchestratorConfig` class:
   ```python
   def is_valid(self) -> bool:
       """Check if all validations pass."""
       try:
           self.validate()
           return True
       except ValidationError:
           return False

   @property
   def errors(self) -> List[str]:
       """Return list of validation errors."""
       try:
           self.validate()
           return []
       except ValidationError as e:
           return [str(err) for err in e.errors()]
   ```
2. Add cross-field validation in Pydantic `@model_validator`:
   - Check `container_cpu_quota > 0` if set
   - Check phase names are unique
   - Check phase names are valid (one of 7 Spec-Kitty phases)
3. Add default phases if `phases` list is empty:
   - Populate with all 7 phases (specify, research, plan, tasks, implement, review, accept)
   - Set enabled=True for all
   - Set validate=True for specify, plan, tasks, implement (per spec)

**Files**:
- `src/orchestrator/domain/models.py` (extend T003)

**Parallel?**: No (extends T003)

**Notes**:
- Default phase configuration from spec.md Configuration section
- Validation should fail fast and clearly (user-friendly error messages)

---

## Test Strategy

Tests are per-constitution requirement. Write unit tests for configuration loading:

**Test File**: `tests/orchestrator/unit/test_config_loader.py`

**Tests**:
1. `test_load_config_with_valid_yaml()` - Loads config successfully
2. `test_load_config_with_missing_file()` - Uses defaults
3. `test_load_config_with_invalid_yaml()` - Raises ConfigValidationError
4. `test_load_config_with_invalid_field()` - Raises ConfigValidationError with details
5. `test_orchestrator_config_defaults()` - All defaults applied correctly
6. `test_orchestrator_config_validation()` - Validates constraints
7. `test_default_phases_populated()` - Empty phases list gets defaults

**Run Command**: `poetry run pytest tests/orchestrator/unit/test_config_loader.py -v`

**Fixtures**: Create sample YAML configs in `tests/orchestrator/fixtures/config/`

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pydantic version incompatibility | Medium | Check existing codebase for Pydantic usage patterns, match version |
| Config system integration complexity | Medium | Reference existing `src/rewrite/adapters/` config loading code |
| Docker SDK version conflicts | Low | Pin to ^7.0.0, test with `poetry check` |

---

## Review Guidance

**Acceptance Checkpoints**:
1. Directory structure matches plan.md exactly
2. `poetry lock` completed successfully
3. `OrchestratorConfig` model has all required fields with correct defaults
4. Configuration loads from actual `config/debate_config.yaml` (test manually)
5. Validation errors are clear and actionable
6. Integration with `src/shared/config` verified

**Review Context**:
- Verify clean architecture separation (domain has no dependencies on adapters/infrastructure)
- Check that Pydantic validators cover all constraints from config-schema.yaml
- Ensure error messages guide users to fix configuration issues
- Confirm defaults match spec.md Configuration section

---

## Activity Log

- 2026-02-21T19:45:00Z – system – lane=planned – Prompt created.
