# Implementation Plan: Flexible Debate Configuration with YAML

**Branch**: `014-flexible-debate-config-yaml` | **Date**: 2025-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/014-flexible-debate-config-yaml/spec.md`

## Summary

This feature transforms the hardcoded debate system into a flexible, YAML-driven configuration framework. The system will support a default `debate.yml` configuration file that preserves current PRD review behavior, while allowing users to provide custom configurations via `--debate-config` CLI flag to adapt debates for any domain (legal, medical, technical, etc.).

**Primary Requirements**:
- Default `debate.yml` with current PRD reviewer roles and 3-round structure
- `--debate-config` CLI argument to override configuration
- Support for inline and file-based role prompts
- Configurable auxiliary roles with trigger conditions
- Integration with both standard and document-based workflows

**Technical Approach**:
- Parse YAML using Python standard library only (`yaml.safe_load`)
- Adapt existing LangGraph StateGraph workflow with dynamic node construction
- Create configuration loader with validation
- Migrate current hardcoded prompts to default configuration
- Add example configurations in `examples/` directory

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Existing dependencies (langgraph, langchain, openai) + `pyyaml` (standard YAML library)
**Storage**: YAML configuration files (`debate.yml` default, custom configs via CLI)
**Testing**: pytest (existing framework)
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single project CLI utility
**Performance Goals**: Configuration load time < 2 seconds; no performance degradation with up to 10 roles
**Constraints**: Minimal dependencies principle; standard library only for YAML parsing
**Scale/Scope**: Single project with modules for configuration, validation, and workflow integration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Assessment
✅ **Python 3.12+**: Confirmed - project uses Python 3.12+
✅ **pytest required**: Feature will include test coverage for configuration loading, validation, and workflow integration
✅ **Cross-platform**: YAML configuration is platform-agnostic; standard library parsing works on all platforms
✅ **pip installable**: No new external dependencies beyond pyyaml (standard library approach)

### Post-Phase 1 Design Re-Assessment
✅ **Data model maintains simplicity**: Configuration uses standard Python dataclasses, no complex ORM or persistence layer
✅ **Schema validation is lightweight**: Manual validation with clear error messages, no heavy validation libraries
✅ **Backward compatibility preserved**: Default config maintains exact current behavior
✅ **No breaking changes**: Existing workflow architecture preserved; nodes adapted dynamically via factory pattern

### Code Quality Compliance
✅ **Spec-driven development**: Working from written specification (#014)
✅ **TDD approach**: Tests will be written first for configuration loading and validation
✅ **Minimal dependencies**: Using standard library only for YAML parsing; no additional runtime dependencies
✅ **Self-documenting code**: Configuration module will have clear, readable structure with descriptive names

### Tribal Knowledge Alignment
✅ **Preserves existing behavior**: Default `debate.yml` maintains current PRD review functionality
✅ **No breaking changes**: Existing workflow architecture preserved; nodes adapted dynamically
✅ **Rapid iteration focus**: Configuration-driven approach enables quick experimentation
✅ **Configuration is version-controlled**: YAML files can be tracked in git alongside code

### GATE STATUS: ✅ PASS - No violations detected

**Constitution Compliance**: The design aligns with all constitutional requirements:
- Minimal dependencies maintained (standard library only)
- TDD approach planned (test-first development)
- Backward compatible (default config preserves current behavior)
- Cross-platform (YAML works on all platforms)
- Self-documenting code structure with clear naming

## Project Structure

### Documentation (this feature)

```
kitty-specs/014-flexible-debate-config-yaml/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Configuration data model
├── quickstart.md        # Phase 1: User quickstart guide
├── contracts/           # Phase 1: Configuration schema contracts
└── tasks.md             # Phase 2: Work packages (created by /spec-kitty.tasks)
```

### Source Code (repository root)

```
deb8flow/
├── configurations/
│   ├── __init__.py
│   ├── llm_config.py        # Existing: LLM provider configs
│   ├── debate_config.py     # NEW: Configuration loader and validator
│   └── debate_constants.py  # Existing: Debate stage constants
│
├── nodes/
│   ├── __init__.py
│   ├── base_component.py        # Existing: Base node class
│   ├── topic_generator_node.py  # Existing
│   ├── pro_debater_node.py      # Existing: Will use config
│   ├── con_debater_node.py      # Existing: Will use config
│   ├── fact_checker_node.py     # Existing
│   ├── fact_check_router_node.py # Existing
│   ├── debate_moderator_node.py # Existing
│   ├── judge_node.py            # Existing
│   └── role_node_factory.py     # NEW: Dynamic node construction
│
├── workflow/
│   ├── __init__.py
│   ├── debate_workflow.py           # Existing: Will be refactored
│   └── document_debate_workflow.py  # Existing: Will be refactored
│
├── prompts/
│   ├── roles/                  # Existing role prompt files
│   └── [preserve existing structure]
│
├── examples/
│   ├── debate.generic.yml      # NEW: Generic template
│   ├── legal-debate.yml        # NEW: Legal domain example
│   └── financial-analysis.yml  # NEW: Financial document analysis
│
├── debate.yml                  # NEW: Default configuration (PRD behavior)
├── main.py                     # Existing: Will add --debate-config
├── document_debate_cli.py      # Existing: Will add --debate-config
├── debate_state.py             # Existing: May extend for config
│
└── tests/
    ├── test_config/
    │   ├── test_debate_config.py      # NEW: Config loading tests
    │   ├── test_config_validation.py  # NEW: Validation tests
    │   └── fixtures/
    │       ├── valid_debate.yml
    │       ├── invalid_debate.yml
    │       └── custom_roles.yml
    │
    ├── test_workflow/
    │   ├── test_configured_workflow.py  # NEW: Dynamic workflow tests
    │   └── [existing tests]
    │
    └── [existing test structure]
```

**Structure Decision**: Single project structure (existing pattern). The feature adds:
1. `configurations/debate_config.py` - Core configuration module
2. `nodes/role_node_factory.py` - Dynamic node construction
3. `debate.yml` - Default configuration file
4. `examples/` - Example configurations for different domains
5. Tests in `tests/test_config/` and `tests/test_workflow/`

## Complexity Tracking

*No constitution violations - this section not applicable*

---

## Generated Artifacts

### Phase 0: Research

**File**: `research.md`

**Research Areas Investigated**:
1. YAML Parsing and Validation Strategy
   - Decision: Use Python standard library `yaml.safe_load()` with manual validation
   - Rationale: Minimal dependencies, sufficient for schema complexity

2. Dynamic Node Construction in LangGraph
   - Decision: Factory pattern with dynamic node construction
   - Rationale: Preserves existing architecture, enables flexibility

3. Backward Compatibility Strategy
   - Decision: Preserve existing behavior in default `debate.yml`
   - Rationale: No breaking changes, opt-in to new features

4. Configuration Schema Design
   - Decision: Hierarchical schema with sections for roles, models, rounds, workflow
   - Rationale: Logical grouping, extensibility, clear validation

5. Prompt File Resolution
   - Decision: Resolve paths relative to configuration file directory
   - Rationale: Portability, predictable behavior

### Phase 1: Design

**File**: `data-model.md`

**Core Entities Defined**:
- `DebateConfig`: Root configuration object
- `WorkflowConfig`: Mode and round configuration
- `RoleConfig`: Participant role definitions
- `TriggerConfig`: Auxiliary role participation triggers
- `ModelConfig`: LLM model configurations
- `FactCheckingConfig`: Fact-checking settings

**Validation Rules Defined**:
- Required fields and type constraints
- Prompt resolution precedence (prompt_file > inline prompt)
- Model reference validation
- Trigger condition validation

**File**: `contracts/schema.md`

**Schema Contract Covers**:
- Root configuration structure
- Role configuration schema
- Auxiliary role schema with triggers
- Model configuration schema
- Fact-checking configuration schema
- Complete example configuration
- Error response formats
- Configuration precedence rules
- CLI integration contract

**File**: `quickstart.md`

**User Guide Includes**:
- Installation instructions
- First debate walkthrough
- Custom configuration creation
- Common patterns (file-based prompts, auxiliary roles, document analysis, multiple models)
- Configuration reference
- Troubleshooting guide
- Example configurations

### Design Principles Applied

1. **Minimal Dependencies**: Standard library only for YAML parsing
2. **Backward Compatibility**: Default config preserves current behavior
3. **Extensibility**: Easy to add new roles, models, or triggers
4. **Validation**: Clear error messages with specific field references
5. **Portability**: Configuration files can be shared across projects

---

## Implementation Roadmap (High-Level)

The actual implementation will be broken down into work packages by `/spec-kitty.tasks`. Expected areas:

1. **Configuration Module** (`configurations/debate_config.py`)
   - YAML loading and parsing
   - Configuration validation
   - Prompt resolution

2. **Node Factory** (`nodes/role_node_factory.py`)
   - Dynamic node construction from config
   - Model assignment based on config

3. **Workflow Refactoring** (`workflow/*.py`)
   - Adapt existing workflows to use config
   - Dynamic edge routing based on rounds

4. **CLI Integration** (`main.py`, `document_debate_cli.py`)
   - Add `--debate-config` argument
   - Config loading and validation

5. **Default Configuration** (`debate.yml`)
   - Migrate current hardcoded prompts
   - Preserve existing behavior

6. **Example Configurations** (`examples/`)
   - Legal debate template
   - Financial analysis template
   - Generic template

7. **Testing** (`tests/test_config/`, `tests/test_workflow/`)
   - Configuration loading tests
   - Validation tests
   - Workflow integration tests

---

**END OF PLAN**

**Next Steps**:
- Run `/spec-kitty.tasks` to generate work packages
- Work packages will be implemented in isolated worktrees
- Each work package will have specific prompt files for implementation