---
work_package_id: WP07
title: Documentation
lane: "done"
dependencies: []
base_branch: main
base_commit: add8e148c801af6906614dcb1459157db211fdd3
created_at: '2026-02-21T11:18:34.637788+00:00'
subtasks: [T032, T033, T034, T035, T036]
shell_pid: "81109"
agent: "claude"
reviewed_by: "ALeks ishmanov"
review_status: "approved"
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP07: Documentation

**Priority**: P2
**Estimated Size**: ~300 lines (5 subtasks × ~55 lines each)
**Implementation Command**: `spec-kitty implement WP07 --base WP04`

## Objective

Create user documentation for review agent configuration system.

## Context

Documentation must follow project style (see `docs/rewrite.md`) and provide clear examples for all configuration options. This satisfies the constitution requirement for feature documentation.

**Reference**:
- Parent WPs: WP01-WP04 (implementation must be understood)
- Project constitution: `.kittify/memory/constitution.md`
- Existing docs: `docs/rewrite.md` (for style reference)

## Subtasks

### T032: Create docs/review-agent-config.md with overview

**Purpose**: Create main documentation file with feature overview.

**Implementation**:

Create `docs/review-agent-config.md`:

```markdown
# Review Agent Configuration

The Review Agent Configuration System allows fine-grained control over how the review agent analyzes code. All configuration is managed through `config/debate_config.yaml` in the `rewrite.review` section.

## Overview

The configuration system supports:
- **Custom Prompts**: Define system and user prompts with placeholder substitution
- **LLM Settings**: Control model selection, temperature, and other parameters
- **Profiles**: Quick-switch between strict, balanced, and lenient review modes
- **Selective Checks**: Enable/disable security, performance, and style checks
- **Output Control**: Configure output format (markdown/JSON) and verbosity
- **Context Management**: Set context window size and file filtering patterns

## Configuration Location

Configuration is stored in `config/debate_config.yaml` under the `rewrite.review` section:

```yaml
rewrite:
  review:
    profile: "balanced"
    llm:
      provider: "openai"
      model: "gpt-4o-mini"
      temperature: 0.7
    # ... more options
```

## Quick Start

### Minimal Configuration

The minimal configuration uses all defaults:

```yaml
rewrite:
  review:
    profile: "balanced"
```

### Custom Model

```yaml
rewrite:
  review:
    llm:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.5
```

### Custom Prompts

```yaml
rewrite:
  review:
    prompts:
      system: "src/prompts/review/my_system.md"
      user: "src/prompts/review/my_user.md"
      variables:
        project_name: "MyProject"
```

## Configuration Reference

See the sections below for detailed configuration options.
```

**Validation**:
- [ ] Documentation created in correct location
- [ ] Overview section explains the feature
- [ ] Quick start examples provided
- [ ] References detailed sections

---

### T033: Add configuration examples for common scenarios

**Purpose**: Provide examples for typical use cases.

**Implementation**:

Add to `docs/review-agent-config.md`:

```markdown
## Common Configuration Scenarios

### Security-Focused Review

For security audits, enable only security checks with strict settings:

```yaml
rewrite:
  review:
    profile: "strict"
    checks:
      security: true
      performance: false
      style: false
    llm:
      temperature: 0.1  # More deterministic
```

### Quick Style Check

For fast style reviews during development:

```yaml
rewrite:
  review:
    profile: "lenient"
    checks:
      security: false
      performance: false
      style: true
    llm:
      temperature: 0.9  # More creative
```

### CI/CD Integration

For CI/CD pipelines, use JSON output:

```yaml
rewrite:
  review:
    output:
      format: "json"
      include_snippets: true
      max_comment_length: 200
    logging:
      level: "ERROR"  # Less verbose in CI
```

### Large Codebase Review

For large codebases, limit context and filter files:

```yaml
rewrite:
  review:
    context:
      window_size: 4000
      include_patterns:
        - "src/**/*.py"
        - "lib/**/*.py"
      exclude_patterns:
        - "**/test_*.py"
        - "**/__pycache__/**"
        - "**/migrations/**"
```

### Custom Prompts with Variables

Use custom prompts with project-specific variables:

```yaml
rewrite:
  review:
    prompts:
      system: "config/prompts/review_system.md"
      user: "config/prompts/review_user.md"
      variables:
        project_name: "Deb8flow"
        team_context: "Backend team focusing on Python"
        coding_standard: "PEP 8 with Google style docstrings"
```

The variables can be used in prompt files with `{variable_name}` syntax.
```

**Validation**:
- [ ] 5+ common scenarios documented
- [ ] Each scenario has complete YAML example
- [ ] Examples cover different feature combinations

---

### T034: Document profile system and merge behavior

**Purpose**: Explain profiles, merge strategy, and priority.

**Implementation**:

Add to `docs/review-agent-config.md`:

```markdown
## Profile System

Profiles are preset configurations that override base settings. Three profiles are included:

### Built-in Profiles

**strict** - Comprehensive review with low creativity:
- `temperature: 0.1` - Highly deterministic
- `top_p: 0.5` - Focused sampling
- All checks enabled (security, performance, style)
- JSON output for parsing

**balanced** - Balanced review (default):
- `temperature: 0.5` - Moderate creativity
- `top_p: 0.8` - Broad sampling
- Security and performance checks enabled
- Markdown output

**lenient** - Lightweight style-focused review:
- `temperature: 0.9` - High creativity
- `top_p: 0.95` - Very diverse sampling
- Only style checks enabled
- Markdown output

### Using Profiles

**Via config file:**
```yaml
rewrite:
  review:
    profile: "strict"
```

**Via CLI:**
```bash
debate review --profile strict
```

### Merge Behavior

Profiles use **key-based merge**, not full override:

1. **Base Config**: Default values from `rewrite.review.*`
2. **Profile Override**: Selected profile overrides only specified keys
3. **CLI Override**: CLI flags have highest priority

**Example:**

```yaml
# Base config
rewrite:
  review:
    llm:
      temperature: 0.5
      model: "gpt-4o-mini"
    profiles:
      strict:
        llm:
          temperature: 0.1  # Only temperature specified
```

When using `--profile strict`:
- `temperature` becomes `0.1` (overridden)
- `model` stays `gpt-4o-mini` (inherited)

### Custom Profiles

You can define custom profiles in the config:

```yaml
rewrite:
  review:
    profiles:
      custom_profile:
        llm:
          temperature: 0.3
          top_p: 0.7
        checks:
          security: true
          performance: false
          style: false
```

Use with:
```bash
debate review --profile custom_profile
```

### Priority Order

Configuration is applied in this order:

1. Base config (`rewrite.review.*`)
2. Profile preset (`rewrite.review.profiles.{name}`)
3. CLI flags (highest priority)

**Example:**
```yaml
# Base: temperature = 0.5
# Profile strict: temperature = 0.1
# CLI: --temperature 0.3
# Final: temperature = 0.3 (CLI wins)
```
```

**Validation**:
- [ ] All built-in profiles documented
- [ ] Key-based merge explained
- [ ] Priority order clearly shown
- [ ] Custom profile example provided

---

### T035: Document placeholder system and variables

**Purpose**: Explain placeholder substitution in prompts.

**Implementation**:

Add to `docs/review-agent-config.md`:

```markdown
## Placeholder System

Prompts and templates support `{variable}` placeholders for dynamic content.

### Built-in Placeholders

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `{file_path}` | Path to file being reviewed | `/path/to/file.py` |
| `{timestamp}` | Current timestamp | `2025-02-21T13:45:30` |
| `{project_name}` | From `prompt_variables` | `Deb8flow` |
| `{team_context}` | From `prompt_variables` | `Backend team` |
| `{*}` | Any key from `prompt_variables` | Custom variables |

### Using Placeholders

**Configure variables:**
```yaml
rewrite:
  review:
    prompts:
      variables:
        project_name: "MyApp"
        team_context: "Frontend team"
        coding_standard: "Airbnb style guide"
```

**Use in prompt file:**
```markdown
Please review the following code for {project_name}.

Team context: {team_context}
Coding standard: {coding_standard}

File: {file_path}
```

**Result after substitution:**
```markdown
Please review the following code for MyApp.

Team context: Frontend team
Coding standard: Airbnb style guide

File: /path/to/file.py
```

### Custom Variables

Add any custom variables you need:

```yaml
rewrite:
  review:
    prompts:
      variables:
        repository_url: "https://github.com/user/repo"
        jira_project: "PROJ"
        sprint_number: "42"
```

Use them in prompts: `{repository_url}`, `{jira_project}`, `{sprint_number}`.

### Placeholder Behavior

- **Found variables**: Replaced with their values
- **Missing variables**: Left as-is (no error)
- **Special characters**: Handled correctly (spaces, colons, etc.)

### Result Templates

Output templates use placeholders to format review results:

```yaml
rewrite:
  review:
    prompts:
      result_template: "config/prompts/result_template.md"
```

**Template file:**
```markdown
# Review Report

**File**: {file_path}
**Date**: {timestamp}
**Profile**: {profile}

## Summary
{summary}

## Rating
{rating}/10

---
Generated by {provider} {model} (temperature: {temperature})
```
```

**Validation**:
- [ ] All built-in placeholders listed
- [ ] Custom variables explained
- [ ] Missing variable behavior documented
- [ ] Result template example provided

---

### T036: Add migration guide from old config

**Purpose**: Help users transition from old config format.

**Implementation**:

Add to `docs/review-agent-config.md`:

```markdown
## Migration Guide

### From Previous Config Format

The review configuration is now under `rewrite.review`. If you were using an older config format, here's how to migrate.

**Old format (if you had custom LLM settings):**
```yaml
llm:
  model: "gpt-4"
  temperature: 0.8
```

**New format:**
```yaml
rewrite:
  review:
    llm:
      model: "gpt-4"
      temperature: 0.8
```

### Backward Compatibility

Existing configurations continue to work. The review section is optional - if not specified, all defaults are used.

### Adding Review Config to Existing Setup

If your `config/debate_config.yaml` doesn't have a `rewrite.review` section:

1. Add the section under `rewrite`:
```yaml
rewrite:
  # Your existing settings...
  max_rounds: 5

  # Add review config:
  review:
    profile: "balanced"
```

2. Start with the profile that matches your needs:
   - `strict` - For thorough code review
   - `balanced` - For everyday development (default)
   - `lenient` - For quick style checks

3. Customize from there:
```yaml
rewrite:
  review:
    profile: "balanced"
    llm:
      temperature: 0.5  # Adjust as needed
    checks:
      security: true
      performance: true
      style: false  # Disable if not needed
```

### Environment Variable Migration

Environment variables now support default values:

**Old format:**
```yaml
model: "${MODEL}"
```

**New format (with default):**
```yaml
model: "${MODEL:gpt-4o-mini}"
```

If `MODEL` is not set, uses `gpt-4o-mini` as fallback.

### Checklist

- [ ] Add `rewrite.review` section to `config/debate_config.yaml`
- [ ] Set default profile (strict/balanced/lenient)
- [ ] Configure LLM settings if needed
- [ ] Enable/disable checks as needed
- [ ] Test with: `debate review --help`
```

**Validation**:
- [ ] Migration from old config documented
- [ ] Backward compatibility explained
- [ ] Step-by-step migration guide provided
- [ ] Checklist for migration completion

## Files Created

- `docs/review-agent-config.md` (new, ~400 lines)

## Documentation Structure

```markdown
# Review Agent Configuration

1. Overview
2. Quick Start
3. Configuration Reference
   - LLM Settings
   - Prompt Configuration
   - Retry Policy
   - Checks Configuration
   - Output Settings
   - Context Settings
   - Logging Settings
4. Profile System
5. Placeholder System
6. Common Scenarios
7. Migration Guide
8. Troubleshooting
```

## Definition of Done

- [ ] Documentation created at `docs/review-agent-config.md`
- [ ] All config options documented
- [ ] Examples provided for common scenarios
- [ ] Profile system clearly explained
- [ ] Placeholder system documented
- [ ] Migration guide included
- [ ] Documentation follows project style (matches docs/rewrite.md)
- [ ] Constitution requirement met (feature documentation exists)

## Reviewer Guidance

**Verify**:
1. All config options from spec are documented
2. YAML examples are valid and tested
3. Code blocks use proper syntax highlighting
4. Links work (if any)
5. Style matches existing documentation

**Common Issues**:
- Missing options → Compare with spec.md FR-XXX
- Invalid YAML examples → Test examples in actual file
- Inconsistent terminology → Use terms from spec

## Risks

- **Low Risk**: Documentation task
- **Mitigation**: Reference spec for complete option list

## Activity Log

- 2026-02-21T11:18:34Z – claude – shell_pid=81109 – lane=doing – Assigned agent via workflow command
- 2026-02-21T11:20:19Z – claude – shell_pid=81109 – lane=for_review – Ready for review: Complete user documentation for review agent configuration system
- 2026-02-21T11:43:39Z – claude – shell_pid=81109 – lane=doing – Reviewing WP07
- 2026-02-21T11:44:05Z – claude – shell_pid=81109 – lane=done – Review passed
