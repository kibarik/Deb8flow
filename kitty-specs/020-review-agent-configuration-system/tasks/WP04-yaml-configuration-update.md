---
work_package_id: WP04
title: YAML Configuration Update
lane: "doing"
dependencies: []
base_branch: main
base_commit: 574d20f74d3947d239161d4228d97463529b61c9
created_at: '2026-02-21T11:14:02.874092+00:00'
subtasks: [T018, T019, T020, T021]
shell_pid: "80140"
agent: "claude"
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP04: YAML Configuration Update

**Priority**: P1
**Estimated Size**: ~240 lines (4 subtasks × ~55 lines each)
**Implementation Command**: `spec-kitty implement WP04 --base WP01`

## Objective

Update `config/debate_config.yaml` with review section including profiles, prompts, and all configuration options.

## Context

The YAML config file needs a new `rewrite.review` section with all configuration options for the review agent. This includes profile presets (strict/balanced/lenient) that override base settings.

**Reference**:
- Parent WP: WP01 (value objects define the structure)
- Config schema: `kitty-specs/020-review-agent-configuration-system/plan.md`

## Subtasks

### T018: Add review section to debate_config.yaml

**Purpose**: Add the complete review configuration section.

**Implementation**:

Edit `config/debate_config.yaml`, add under `rewrite:` section:

```yaml
# Rewrite Configuration
# Settings for the document rewrite script with debate verification
rewrite:
  # Maximum verification rounds (default: 5)
  max_rounds: 5

  # Number of revisions to process per AI batch (default: 5)
  batch_size: 5

  # Prompt paths for rewrite-specific debate
  prompts:
    pro: "src/prompts/rewrite/pro_verification.md"
    con: "src/prompts/rewrite/con_verification.md"
    judge: "src/prompts/rewrite/judge_verdict.md"

  # Output settings
  backup_suffix: ".backup"
  partial_report: "rewrite_partial_report.md"

  # ============================================
  # Review Agent Configuration
  # ============================================
  review:
    # Default profile to use (strict/balanced/lenient)
    profile: "balanced"

    # LLM Settings
    # Environment variables can be used with ${VAR:default} syntax
    llm:
      provider: "${DEBATE_PROVIDER:openai}"
      model: "${DEBATE_MODEL:gpt-4o-mini}"
      temperature: ${DEBATE_TEMPERATURE:0.7}
      top_p: 0.9
      max_tokens_request: 4000
      max_tokens_response: 2000
      timeout: 120

    # Custom Prompts
    # Paths to custom prompt templates (optional)
    prompts:
      system: null  # "src/prompts/review/system_prompt.md"
      user: null    # "src/prompts/review/user_prompt.md"
      result_template: null  # "src/prompts/review/result_template.md"

      # Variables for placeholder substitution in prompts
      variables:
        project_name: "Deb8flow"
        team_context: "Backend development team"

    # Retry Policy
    retry:
      max_retries: 3
      backoff: "exponential"  # Options: exponential, linear, constant
      initial_delay: 1.0

    # Checks Configuration
    # Enable/disable specific check types
    checks:
      security: true
      performance: true
      style: true

    # Output Format
    output:
      format: "markdown"  # Options: markdown, json
      include_snippets: true
      max_comment_length: 500

    # Context Settings
    context:
      window_size: 8000
      include_patterns: []
      exclude_patterns: []

    # Logging
    logging:
      level: "INFO"  # Options: ERROR, WARN, INFO, DEBUG
      debug: false

    # Profile Presets
    # These override base settings when selected via --profile flag
    profiles:
      # Strict: Low temperature, all checks enabled, JSON output
      strict:
        llm:
          temperature: 0.1
          top_p: 0.5
        checks:
          security: true
          performance: true
          style: true
        output:
          format: "json"

      # Balanced: Medium temperature, most checks, markdown output
      balanced:
        llm:
          temperature: 0.5
          top_p: 0.8
        checks:
          security: true
          performance: true
          style: false
        output:
          format: "markdown"

      # Lenient: High temperature, style checks only
      lenient:
        llm:
          temperature: 0.9
          top_p: 0.95
        checks:
          security: false
          performance: false
          style: true
        output:
          format: "markdown"
```

**Validation**:
- [ ] YAML is valid and parses correctly
- [ ] All sections from spec are present
- [ ] Comments explain each option
- [ ] Environment variable syntax is correct

---

### T019: Add three profile presets

**Purpose**: Ensure strict, balanced, lenient profiles are defined.

**Implementation**:

Profiles are already included in T018. Verify they have appropriate values:

```yaml
profiles:
  strict:
    llm:
      temperature: 0.1    # Very deterministic
      top_p: 0.5         # Focused sampling
    checks:
      security: true
      performance: true
      style: true
    output:
      format: "json"     # Machine-readable output

  balanced:
    llm:
      temperature: 0.5   # Balanced creativity
      top_p: 0.8
    checks:
      security: true
      performance: true
      style: false       # Style checks optional
    output:
      format: "markdown"

  lenient:
    llm:
      temperature: 0.9   # High creativity
      top_p: 0.95        # Very diverse sampling
    checks:
      security: false
      performance: false
      style: true        # Only style checks
    output:
      format: "markdown"
```

**Validation**:
- [ ] Strict profile: temperature < 0.2, all checks on
- [ ] Balanced profile: 0.3 < temperature < 0.7
- [ ] Lenient profile: temperature > 0.8
- [ ] All profiles have valid values

---

### T020: Document all default values in comments

**Purpose**: Add inline comments explaining defaults and ranges.

**Implementation**:

Add comments for each option:

```yaml
review:
  # Default profile: balanced, strict, or lenient
  profile: "balanced"

  llm:
    # LLM provider: openai, anthropic, etc.
    provider: "${DEBATE_PROVIDER:openai}"

    # Model name (e.g., gpt-4o-mini, claude-3-5-sonnet-20241022)
    model: "${DEBATE_MODEL:gpt-4o-mini}"

    # Sampling temperature: 0.0 (focused) to 1.0 (creative)
    temperature: ${DEBATE_TEMPERATURE:0.7}

    # Nucleus sampling: 0.0 to 1.0
    top_p: 0.9

    # Max tokens for request/response
    max_tokens_request: 4000   # Outgoing request size
    max_tokens_response: 2000  # Max response length

    # Request timeout in seconds
    timeout: 120

  retry:
    max_retries: 3           # 0 = no retries
    backoff: "exponential"   # exponential, linear, constant
    initial_delay: 1.0       # Seconds before first retry

  checks:
    security: true    # Enable security vulnerability checks
    performance: true # Enable performance issue checks
    style: true       # Enable code style checks

  output:
    format: "markdown"           # markdown or json
    include_snippets: true       # Include code snippets in output
    max_comment_length: 500      # Max characters per comment

  context:
    window_size: 8000            # Max context tokens
    include_patterns: []         # Glob patterns to include (e.g., ["src/**/*.py"])
    exclude_patterns: []         # Glob patterns to exclude (e.g., ["**/test_*.py"])

  logging:
    level: "INFO"    # ERROR, WARN, INFO, or DEBUG
    debug: false     # Enable debug mode with statistics
```

**Validation**:
- [ ] Every option has a comment
- [ ] Valid ranges are documented
- [ ] Default values are shown
- [ ] Examples are provided where helpful

---

### T021: Create example directory structure for prompts

**Purpose**: Create placeholder directory and example prompts.

**Implementation**:

```bash
mkdir -p src/prompts/review
```

Create placeholder files:

`src/prompts/review/.gitkeep`:
```
# This directory stores custom prompts for the review agent
#
# Files:
#   system_prompt.md    - System prompt for review agent
#   user_prompt.md      - User prompt template
#   result_template.md  - Output format template
```

`src/prompts/review/system_prompt.md.example`:
```markdown
# Review Agent System Prompt

You are a code review assistant for the {project_name} project.

## Team Context
{team_context}

## Review Guidelines
1. Focus on correctness, security, and maintainability
2. Be specific and actionable in your feedback
3. Consider the project's coding standards
4. Prioritize critical issues over minor style nitpicks
```

`src/prompts/review/user_prompt.md.example`:
```markdown
# Code Review Request

Please review the following code file:

**File**: {file_path}
**Language**: Python

```python
{file_content}
```

Please provide:
1. Summary of your review
2. Specific issues found (if any)
3. Recommendations for improvement
4. Overall assessment (1-10)
```

`src/prompts/review/result_template.md.example`:
```markdown
# Code Review Report

**File**: {file_path}
**Date**: {timestamp}
**Reviewer**: AI Review Agent
**Profile**: {profile}

## Summary
{summary}

## Issues Found
{issues}

## Rating
{rating}/10

## Recommendations
{recommendations}

---
*Generated by {provider} {model} (temperature: {temperature})*
```

**Validation**:
- [ ] Directory created
- [ ] .gitkeep file exists (for version control)
- [ ] Example prompts show placeholder usage
- [ ] Examples demonstrate all built-in placeholders

## Files Modified/Created

- `config/debate_config.yaml` (modify, add ~60 lines)
- `src/prompts/review/.gitkeep` (new)
- `src/prompts/review/system_prompt.md.example` (new)
- `src/prompts/review/user_prompt.md.example` (new)
- `src/prompts/review/result_template.md.example` (new)

## Definition of Done

- [ ] YAML is valid (parses without error)
- [ ] Review section complete with all options
- [ ] Three profiles defined (strict/balanced/lenient)
- [ ] Comments document all options
- [ ] Example prompts directory created
- [ ] Config loader can load the review section

## Reviewer Guidance

**Verify**:
1. YAML indentation is correct (2 spaces)
2. Environment variable syntax is ${VAR:default}
3. All config options from spec are present
4. Example prompts demonstrate placeholder usage

**Common Issues**:
- Wrong indentation → YAML parse error
- Missing quotes → Strings interpreted as types
- Invalid env var syntax → Variables not expanded

## Risks

- **Low Risk**: Straightforward YAML addition
- **Mitigation**: Validate YAML parses correctly

## Activity Log

- 2026-02-21T11:14:02Z – claude – shell_pid=80140 – lane=doing – Assigned agent via workflow command
