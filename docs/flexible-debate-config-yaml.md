# Flexible Debate Configuration with YAML

## Overview

The Flexible Debate Configuration feature enables users to control debate behavior through YAML configuration files. This allows for customizable role definitions, debate rounds, model assignments, and workflow modes without modifying code.

## What It Does

This feature:

- Supports a default `debate.yml` configuration file
- Accepts custom configurations via `--debate-config` CLI flag
- Defines roles (PRO, CON, auxiliary) with flexible prompts
- Configures debate rounds and models per role
- Enables inline or file-based role prompts
- Supports configurable auxiliary roles with trigger conditions
- Provides comprehensive configuration validation

## How It Works

### Architecture

```
YAML Config File → Validation → Role/Workflow Construction → Debate Execution
```

### Data Flow

1. User provides configuration file (default or custom)
2. System validates YAML syntax and required fields
3. Roles are instantiated with their prompts
4. Workflow is constructed based on rounds and modes
5. Debate executes with configured parameters

### Configuration Precedence

```
CLI Arguments > Config File > Hardcoded Defaults
```

## Usage

### Default Configuration

Place a `debate.yml` file in the project root:

```bash
python main.py
```

The system automatically loads `debate.yml` if present.

### Custom Configuration

```bash
python main.py --debate-config path/to/custom-config.yml
```

### Document Debate with Custom Config

```bash
python document_debate_cli.py --debate-config financial-analysis.yml --docx report.docx
```

## Configuration Structure

### Required Sections

```yaml
# debate.yml
roles:
  - name: pro
    side: pro
    prompt: "You argue for the position..."
  - name: con
    side: con
    prompt: "You argue against the position..."

rounds: 4

models:
  pro: gpt-4
  con: gpt-4
  moderator: gpt-3.5-turbo

workflow: standard  # or 'document'
```

### Optional Sections

```yaml
auxiliary_roles:
  - name: fact_checker
    side: auxiliary
    prompt: "You verify factual claims..."
    trigger:
      after_round: 2

fact_checking:
  enabled: true
  max_failures: 3

temperature:
  pro: 0.7
  con: 0.7

max_tokens:
  pro: 1000
  con: 1000
```

## Role Definitions

### Minimum Requirements

Each role must define:
- `name`: Unique identifier (e.g., "pro", "con", "moderator")
- `side`: Debate affiliation (pro, con, neutral, or auxiliary)
- `prompt`: Role prompt text (inline) OR `prompt_file`: Path to external file

### Inline Prompts

```yaml
roles:
  - name: pro
    side: pro
    prompt: "You are a strong advocate for the position. Focus on evidence..."
```

### File-Based Prompts

```yaml
roles:
  - name: pro
    side: pro
    prompt_file: prompts/advocate.md
```

When both `prompt` and `prompt_file` are specified, `prompt_file` takes precedence.

### Prompt Placeholders

Prompts may contain runtime placeholders:

```yaml
prompt: "Analyze this document: {document_content}"
prompt: "Debate the topic: {topic}"
```

### Auxiliary Roles

Optional participants that activate based on triggers:

```yaml
auxiliary_roles:
  - name: domain_expert
    side: auxiliary
    prompt: "Provide expert analysis..."
    trigger:
      after_round: 2
      # OR
      on_fact_check: true
```

## Configuration Validation

### Validation Checks

The system validates:

1. **YAML Syntax**: Parse errors are reported with line numbers
2. **Required Fields**: Missing `roles`, `rounds`, `models`, or `workflow` sections
3. **Role Definitions**: At minimum, "pro" and "con" roles must be defined
4. **File References**: Prompt files must exist and be readable
5. **Model Names**: Valid LLM model identifiers
6. **Circular References**: Detects circular prompt file references

### Error Messages

Clear, actionable error messages for:

```
Error: Configuration file 'custom.yml' has invalid YAML syntax at line 15:
  15 | rounds: 4
  16 |   - extra_item
  ^^^^^^^^^^^^^^^^^
Unexpected indentation
```

```
Error: Missing required field 'models' in configuration file 'custom.yml'
Required sections: roles, rounds, models, workflow
```

## CLI Integration

### Main Python CLI

```bash
# Uses debate.yml by default
python main.py

# Uses custom configuration
python main.py --debate-config legal-debate.yml

# CLI arguments override config values
python main.py --debate-config custom.yml --model gpt-4-turbo
```

### Document Debate CLI

```bash
# Uses debate.yml by default
python document_debate_cli.py --docx report.docx

# Uses custom configuration
python document_debate_cli.py --debate-config financial.yml --docx report.docx
```

## Workflow Integration

### Dynamic Node Construction

The debate workflow constructs participant nodes based on configured roles:

```
Config Roles → Node Instantiation → Workflow Assembly
```

- Participant nodes are created from role definitions
- Routing is based on configured rounds
- Auxiliary roles activate at their trigger points
- Models are assigned per role from configuration

### Fact-Checking Control

Fact-checking behavior respects configuration:

```yaml
fact_checking:
  enabled: false  # Disables fact-checking
```

## Example Configurations

### Standard Debate

```yaml
roles:
  - name: pro
    side: pro
    prompt_file: prompts/pro-debater.md
  - name: con
    side: con
    prompt_file: prompts/con-debater.md

rounds: 4
models:
  pro: gpt-4
  con: gpt-4
  moderator: gpt-3.5-turbo
  judge: gpt-4
workflow: standard
```

### Committee Debate

```yaml
roles:
  - name: tpm
    side: pro
    prompt_file: prompts/roles/tpm.txt
  - name: cpo
    side: con
    prompt_file: prompts/roles/cpo.txt

rounds: 3
models:
  tpm: gpt-4
  cpo: gpt-4
workflow: document
```

### Legal Debate with Auxiliary Role

```yaml
roles:
  - name: prosecution
    side: pro
    prompt: "You are prosecuting the case..."
  - name: defense
    side: con
    prompt: "You are defending the case..."

auxiliary_roles:
  - name: legal_expert
    side: auxiliary
    prompt: "Provide legal precedent analysis..."
    trigger:
      after_round: 2

rounds: 5
models:
  prosecution: gpt-4
  defense: gpt-4
workflow: standard
```

## Success Criteria

- **SC-001**: Users can create new configuration in under 5 minutes
- **SC-002**: Switch configurations with single CLI argument
- **SC-003**: New role definitions take effect immediately
- **SC-004**: Configuration validation errors reported within 2 seconds
- **SC-005**: Custom role prompts correctly applied 100% of time
- **SC-006**: Support for 10+ custom role definitions
- **SC-007**: Auxiliary roles trigger reliably at configured points
- **SC-008**: Prompt files up to 100KB load without errors
- **SC-009**: 100% detection of invalid YAML syntax
- **SC-010**: Support for completely different role sets via config only

## Assumptions

1. Users have basic familiarity with YAML format
2. LangGraph workflow architecture will be preserved
3. Existing debate stages remain configurable but structurally similar
4. `--debate-config` flag is optional
5. Prompt files use UTF-8 encoding
6. Current fact-checking integration will remain but be configurable
7. Primary use case is adapting to different domains (legal, medical, technical)
8. Configuration files will be version-controlled
9. No real-time configuration reloading during active debate
10. CLI argument precedence: CLI flags > config file > hardcoded defaults

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| LLM model not available in environment | Clear error message listing valid models |
| More rounds than workflow supports | Error indicating maximum supported rounds |
| External prompt files with non-UTF-8 encoding | Error message about encoding requirement |
| Empty configuration file | Error indicating required sections are missing |
| Missing PRO or CON roles | Error listing required roles for debate |
| Extremely large prompt files (>100KB) | Load with warning, may impact performance |
| Both standard and document workflow modes specified | Error indicating only one mode allowed |
| Conflicting settings in configuration | Warning or error depending on severity |
