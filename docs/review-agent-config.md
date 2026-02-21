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

### LLM Settings

Configure the LLM provider and model parameters:

```yaml
llm:
  provider: "openai"              # LLM provider (openai, anthropic, etc.)
  model: "gpt-4o-mini"           # Model identifier
  temperature: 0.7                # Sampling temperature (0.0 - 1.0)
  top_p: 0.9                      # Nucleus sampling (0.0 - 1.0)
  max_tokens_request: 4000       # Max tokens for outgoing requests
  max_tokens_response: 2000      # Max tokens for response generation
  timeout: 120                    # Request timeout in seconds
```

### Custom Prompts

Define custom prompts for the review agent:

```yaml
prompts:
  system: "path/to/system_prompt.md"
  user: "path/to/user_prompt.md"
  result_template: "path/to/template.md"
  variables:
    project_name: "MyProject"
    team_context: "Backend team"
```

### Retry Policy

Configure retry behavior for API failures:

```yaml
retry:
  max_retries: 3                 # Maximum number of retry attempts
  backoff: "exponential"         # Backoff strategy: exponential, linear, constant
  initial_delay: 1.0             # Initial delay in seconds before first retry
```

### Checks Configuration

Enable/disable specific check types:

```yaml
checks:
  security: true     # Enable security vulnerability checks
  performance: true  # Enable performance issue checks
  style: true        # Enable code style checks
```

### Output Format

Control the output format and verbosity:

```yaml
output:
  format: "markdown"              # Output format: markdown or json
  include_snippets: true          # Include code snippets in output
  max_comment_length: 500         # Maximum length per comment
```

### Context Settings

Configure context window and file filtering:

```yaml
context:
  window_size: 8000               # Maximum context window in tokens
  include_patterns:               # Glob patterns for files to include
    - "src/**/*.py"
  exclude_patterns:               # Glob patterns for files to exclude
    - "**/test_*.py"
```

### Logging

Configure logging verbosity:

```yaml
logging:
  level: "INFO"                    # Log level: ERROR, WARN, INFO, DEBUG
  debug: false                    # Enable debug mode with statistics
```

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
3. **CLI Override**: CLI flags with highest priority

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
        output:
          format: "markdown"
```

Use with:
```bash
debate review --profile custom_profile
```

## Placeholder System

Prompts and templates support `{variable}` placeholders for dynamic content.

### Built-in Placeholders

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `{file_path}` | Path to file being reviewed | `/path/to/file.py` |
| `{timestamp}` | Current timestamp | `2025-02-21T13:45:30` |
| `{project_name}` | From `prompt_variables.project_name` | `Deb8flow` |
| `{team_context}` | From `prompt_variables.team_context` | `Backend team` |
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

## Error Messages

| Error | Message | Fix |
|-------|---------|-----|
| Invalid temperature | `temperature must be between 0.0 and 1.0` | Use value in range |
| Invalid top_p | `top_p must be between 0.0 and 1.0` | Use value in range |
| Profile not found | `Profile 'xyz' not found. Available: strict, balanced, lenient` | Use valid profile |
| Invalid format | `Invalid format: 'xml'. Must be 'markdown' or 'json'` | Use valid format |
| Prompt file not found | `Prompt file not found: /path/to/file.md` | Create file or fix path |
| Missing profile | `Profile 'xyz' not found. Available: ...` | Use valid profile name |
| No checks enabled | `At least one check must be enabled` | Enable at least one check |

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

## API Reference

### Configuration Classes

The configuration system provides the following Python classes:

- **ReviewConfig**: Root configuration object
- **LLMConfig**: LLM provider and model settings
- **PromptConfig**: Prompt and template configuration
- **RetryConfig**: Retry policy configuration
- **CheckConfig**: Check enable/disable configuration
- **OutputConfig**: Output format configuration
- **ContextConfig**: Context and filtering configuration
- **LoggingConfig**: Logging configuration

### Load Configuration Programmatically

```python
from src.rewrite.infrastructure.config_loader import load_config

# Load configuration
config = load_config(Path("config/debate_config.yaml"))

# Load with profile
config = load_config(Path("config/debate_config.yaml"), profile="strict")

# Load with CLI overrides
config = load_config(
    Path("config/debate_config.yaml"),
    cli_overrides={"llm.temperature": 0.3}
)
```

## Troubleshooting

### Configuration Not Loading

1. Verify YAML syntax is correct
2. Check that `rewrite.review` section exists
3. Ensure file paths in prompts are correct

### Profile Not Applying

1. Check that profile name is spelled correctly
2. Verify profile is defined in `rewrite.review.profiles`
3. Ensure profile settings are valid

### CLI Overrides Not Working

1. Verify override path format: `section.field`
2. Check that value type matches expected type
3. Remember CLI has highest priority

### Placeholder Not Substituting

1. Verify variable is defined in `prompt_variables`
2. Check placeholder spelling matches variable name
3. Built-in variables: `{file_path}`, `{timestamp}`

## Related Documentation

- [Rewrite Documentation](rewrite.md)
- [Debate Configuration Guide](../config/debate_config.md)
- [Architecture Overview](../architecture.md)
