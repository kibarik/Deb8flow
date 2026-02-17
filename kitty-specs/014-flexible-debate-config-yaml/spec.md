# Feature Specification: Flexible Debate Configuration with YAML

**Feature Branch**: `014-flexible-debate-config-yaml`
**Created**: 2025-02-17
**Status**: Draft
**Input**: User description: "хочу поработать над гибкостью системы, чтобы я мог гибко управлять количеством ролей. ASIS - сейчас коммитет напрямую привязан к ролям в файлах ПРОБЛЕМА - я не могу использовать другие prompt инструкции, роли, файлы. Система решает только одну узкую задачу с PRD документом TOBE я могу гибко задать главную роль и список вспомогательных ролей для дебатов при запуске cli команды, чтобы инструмент был адаптивным под любой тип дискуссий с любыми ролями и вводными документами"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Default YAML Configuration (Priority: P1)

As a developer, I want to run debates using a default YAML configuration file so that I can quickly start debates without specifying all parameters manually.

**Why this priority**: This is the foundation - without a working default config, no other scenarios work. It provides the baseline functionality.

**Independent Test**: Can be fully tested by running `python main.py` and verifying that debates execute with the default `debate.yml` configuration, producing expected debate output with proper role behavior.

**Acceptance Scenarios**:

1. **Given** a fresh project installation with `debate.yml` present, **When** I run `python main.py`, **Then** the debate executes using all configuration values from `debate.yml` (roles, rounds, models, workflow mode)
2. **Given** a `debate.yml` with custom role definitions, **When** the debate runs, **Then** each participant behaves according to their configured role prompts
3. **Given** the default configuration, **When** I examine the debate output, **Then** I can see PRO and CON participants following their defined roles through all configured rounds

---

### User Story 2 - Custom Configuration Override (Priority: P1)

As a user, I want to provide a custom YAML configuration file via `--debate-config` flag so that I can adapt the debate system to different use cases without modifying code.

**Why this priority**: This is the core flexibility mechanism - without it, users can't customize debates for their specific needs.

**Independent Test**: Can be fully tested by creating a custom YAML file with different roles/rounds, running `python main.py --debate-config custom.yml`, and verifying the debate follows the custom configuration instead of defaults.

**Acceptance Scenarios**:

1. **Given** a custom configuration file `legal-debate.yml` with lawyer roles, **When** I run `python main.py --debate-config legal-debate.yml`, **Then** the debate executes with lawyer roles instead of default PRD reviewer roles
2. **Given** a configuration file with 5 debate rounds, **When** I run the debate, **Then** the system completes exactly 5 rounds before proceeding to verdict
3. **Given** a configuration file that specifies a different LLM model, **When** I run the debate, **Then** all participants use the specified model

---

### User Story 3 - Inline and File-Based Role Prompts (Priority: P2)

As a user, I want to define role prompts either inline in the YAML or by referencing external prompt files so that I can choose between convenience and reusability.

**Why this priority**: Important for power users and reusability, but debates can work with inline-only prompts. This enhances maintainability and sharing.

**Independent Test**: Can be tested by creating two configurations - one with inline prompts, one referencing external files - and verifying both produce debates where participants follow their respective role prompts.

**Acceptance Scenarios**:

1. **Given** a role with inline prompt text in `debate.yml`, **When** the debate runs, **Then** the participant uses the inline prompt text
2. **Given** a role with `prompt_file: prompts/skeptical-reviewer.md`, **When** the debate runs, **Then** the participant loads and uses the prompt from the external file
3. **Given** a role with both inline prompt and `prompt_file` specified, **When** the debate runs, **Then** the system uses the external file content and ignores the inline text
4. **Given** a missing prompt file reference, **When** the debate runs, **Then** the system reports a clear error indicating which file is missing

---

### User Story 4 - Configurable Auxiliary Roles (Priority: P2)

As a user, I want to define optional auxiliary roles (beyond the main PRO/CON debaters) in the configuration so that I can add specialized perspectives like fact-checkers, domain experts, or devil's advocates.

**Why this priority**: Extends the system's capability but core debates work with just PRO/CON. This enables more sophisticated discussion formats.

**Independent Test**: Can be tested by configuring a debate with an auxiliary role (e.g., fact-checker), running the debate, and verifying the auxiliary role participates according to its configured trigger conditions.

**Acceptance Scenarios**:

1. **Given** a configuration with an auxiliary `domain_expert` role, **When** the debate reaches the configured trigger point, **Then** the domain expert contributes input before continuing
2. **Given** a configuration without auxiliary roles, **When** the debate runs, **Then** only PRO and CON participate
3. **Given** multiple auxiliary roles, **When** the debate runs, **Then** each auxiliary role activates according to its configured schedule or trigger conditions

---

### User Story 5 - Document Debate Configuration (Priority: P3)

As a user, I want to use custom configurations with document-based debates so that I can analyze different types of documents with specialized roles.

**Why this priority**: Extends document debates but they work with default config. Lower priority as it's an enhancement to an existing feature.

**Independent Test**: Can be tested by running `python document_debate_cli.py --debate-config financial-analysis.yml --docx report.docx` and verifying specialized financial analysis roles are used.

**Acceptance Scenarios**:

1. **Given** a custom configuration for financial document analysis, **When** I run document debate with `--debate-config financial.yml`, **Then** the document is analyzed using financial analyst roles
2. **Given** a document debate without `--debate-config`, **When** the debate runs, **Then** it uses the default configuration
3. **Given** a document debate with custom config, **When** the debate completes, **Then** the verdict reflects the specialized perspective defined in the custom configuration

---

### User Story 6 - Configuration Validation (Priority: P3)

As a user, I want clear error messages when my configuration file is invalid so that I can quickly identify and fix configuration mistakes.

**Why this priority**: Important for usability but doesn't block core functionality. Users can work with valid configs without this.

**Independent Test**: Can be tested by creating invalid YAML files (missing required fields, wrong types, syntax errors) and verifying appropriate error messages are shown.

**Acceptance Scenarios**:

1. **Given** a configuration file with invalid YAML syntax, **When** I run the debate, **Then** the system shows a clear error message indicating the syntax error location
2. **Given** a configuration file missing required `roles` section, **When** I run the debate, **Then** the system reports which required fields are missing
3. **Given** a configuration file with invalid model names, **When** I run the debate, **Then** the system lists valid model options and highlights the invalid entry
4. **Given** a configuration file with circular prompt file references, **When** I run the debate, **Then** the system detects the circular reference and reports it clearly

---

### Edge Cases

- What happens when the configuration file specifies an LLM model that isn't available in the current environment?
- How does the system handle a configuration that defines more rounds than the workflow supports?
- What happens when external prompt files contain non-UTF-8 encoding?
- How does the system behave when a configuration file is provided but is empty?
- What happens when role names in the configuration don't match expected workflow participants (e.g., missing PRO or CON)?
- How does the system handle extremely large prompt files (e.g., >100KB)?
- What happens when a configuration specifies both standard and document workflow modes?
- How does the system handle configuration files with inconsistent or conflicting settings?

## Requirements *(mandatory)*

### Functional Requirements

#### Configuration Structure

- **FR-001**: System MUST support a default `debate.yml` configuration file in the project root directory
- **FR-002**: System MUST accept a `--debate-config <path>` CLI argument to override the default configuration
- **FR-003**: Configuration file MUST define the following sections:
  - `roles`: Definitions of all participant roles
  - `rounds`: Number of debate rounds
  - `models`: LLM model assignments per role
  - `workflow`: Debate workflow mode (standard or document-based)
- **FR-004**: Configuration file MAY optionally define:
  - `auxiliary_roles`: Optional additional participant roles
  - `fact_checking`: Enable/disable and configure fact-checking behavior
  - `temperature`: Temperature settings for each role
  - `max_tokens`: Token limits per role

#### Role Definition

- **FR-005**: Each role MUST define at minimum:
  - `name`: Unique identifier for the role (e.g., "pro", "con", "moderator")
  - `side`: Debate side affiliation (pro, con, neutral, or auxiliary)
  - `prompt`: Role prompt text (inline) OR `prompt_file`: Path to external prompt file
- **FR-006**: When both `prompt` and `prompt_file` are specified for a role, the system MUST use `prompt_file` content and ignore the inline `prompt`
- **FR-007**: External prompt files MUST be resolved relative to the configuration file's directory
- **FR-008**: Role prompts MAY contain placeholders that are substituted at runtime (e.g., `{document_content}`, `{topic}`)
- **FR-009**: The system MUST support at minimum the required workflow roles: "pro" and "con"
- **FR-010**: Auxiliary roles MUST define a `trigger` condition specifying when they participate (e.g., "after_round: 2", "on_fact_check: true")

#### CLI Integration

- **FR-011**: The existing `main.py` CLI MUST load configuration from `debate.yml` by default
- **FR-012**: The existing `document_debate_cli.py` MUST support `--debate-config` argument
- **FR-013**: When `--debate-config` is provided, it MUST override the default `debate.yml` completely
- **FR-014**: CLI arguments MAY override specific configuration values (precedence: CLI args > config file > defaults)
- **FR-015**: The system MUST validate the configuration file exists before starting the debate

#### Workflow Integration

- **FR-016**: The debate workflow MUST construct participant nodes based on configured roles instead of hardcoded PRO/CON definitions
- **FR-017**: The workflow MUST route debate stages based on the configured number of rounds
- **FR-018**: Auxiliary role triggers MUST be evaluated at appropriate workflow transition points
- **FR-019**: The system MUST assign LLM models to participants based on the `models` section in configuration
- **FR-020**: Fact-checking behavior MUST respect the `fact_checking.enabled` setting from configuration

#### Error Handling

- **FR-021**: System MUST provide clear error messages when the configuration file is not found
- **FR-022**: System MUST validate required configuration fields are present before starting the debate
- **FR-023**: System MUST report which specific configuration validation failed (field name, expected format)
- **FR-024**: System MUST handle missing prompt files with explicit error messages including the file path
- **FR-025**: System MUST validate that required workflow roles (pro, con) are defined in the configuration

### Key Entities

- **Debate Configuration**: The complete YAML configuration file containing all settings for a debate session, including roles, rounds, models, and workflow parameters
- **Role**: A participant definition containing name, side affiliation, prompt content (inline or file-referenced), model assignment, and optional parameters like temperature and token limits
- **Prompt Definition**: The instructions given to an AI participant, either embedded inline in the configuration or loaded from an external text/markdown file
- **Round Configuration**: The number of debate rounds to execute, controlling the length of the debate
- **Model Assignment**: Mapping of roles to specific LLM models, allowing different participants to use different models
- **Auxiliary Role**: Optional participant that is not a primary debater (PRO/CON), participating based on trigger conditions
- **Trigger Condition**: A rule defining when an auxiliary role should participate (e.g., after specific rounds, on events)
- **Workflow Mode**: The type of debate to run (standard or document-based)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new debate configuration in under 5 minutes by copying and modifying `debate.yml`
- **SC-002**: Users can switch between different debate configurations by changing a single CLI argument
- **SC-003**: New role definitions take effect immediately without code changes or restarts (beyond initial invocation)
- **SC-004**: Configuration validation errors are reported within 2 seconds of invocation
- **SC-005**: Users can define custom role prompts that are correctly applied to debate participants 100% of the time
- **SC-006**: The system supports at least 10 custom role definitions in a single configuration without performance degradation
- **SC-007**: Auxiliary roles participate at their configured trigger points with 100% reliability
- **SC-008**: Prompt files up to 100KB are loaded and applied without errors
- **SC-009**: Configuration validation detects and reports 100% of invalid YAML syntax errors before debate execution
- **SC-010**: Users can successfully run debates with completely different role sets (e.g., legal, medical, technical) using only configuration changes

## Assumptions

1. Users have basic familiarity with YAML file format
2. The current LangGraph-based workflow architecture will be preserved (not rewritten)
3. Existing debate stages (opening, rebuttal, counter, final_argument) will remain configurable but structurally similar
4. The `--debate-config` flag will be optional; if not provided, the system uses default `debate.yml`
5. Prompt files will use UTF-8 encoding
6. The current fact-checking integration will remain but be configurable
7. Users will primarily use this feature for adapting the system to different domains (legal, medical, technical, etc.)
8. Configuration files will be version-controlled alongside project code
9. The system will not need to support real-time configuration reloading during an active debate
10. CLI argument precedence will follow: CLI flags > config file > hardcoded defaults
