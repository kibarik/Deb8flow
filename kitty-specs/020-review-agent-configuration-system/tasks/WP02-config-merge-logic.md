---
work_package_id: WP02
title: Config Merge Logic
lane: "done"
dependencies: []
base_branch: main
base_commit: 8cebe9810eae9bcc2b6fe7eb8ddf0dc2a726d91c
created_at: '2026-02-21T11:10:08.742712+00:00'
subtasks: [T009, T010, T011, T012, T013]
shell_pid: "79399"
agent: "claude"
review_status: "has_feedback"
reviewed_by: "ALeks ishmanov"
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP02: Config Merge Logic

**Priority**: P0 (Foundational)
**Estimated Size**: ~280 lines (5 subtasks × ~50 lines each)
**Implementation Command**: `spec-kitty implement WP02 --base WP01`

## Objective

Implement hierarchical merge logic for profiles and CLI overrides with key-based (not full) override behavior.

## Context

The configuration system supports three levels of overrides:
1. **Base Config**: Default settings from `rewrite.review.*`
2. **Profile Override**: Selected profile preset (`rewrite.review.profiles.{profile}`)
3. **CLI Override**: Command-line flags with highest priority

**Critical Behavior**: Merge is key-based, not full override. If a profile only specifies `llm.temperature`, other base values (like `llm.model`) are inherited.

**Reference**:
- Parent WP: WP01 (value objects must exist)
- Spec: `kitty-specs/020-review-agent-configuration-system/spec.md` (User Story 3)

## Subtasks

### T009: Implement merge_with_profile() method

**Purpose**: Apply profile preset to base configuration with key-based override.

**Implementation**:

Add method to `ReviewConfig` in `src/rewrite/domain/review_config.py`:

```python
def merge_with_profile(self, profile_name: str) -> "ReviewConfig":
    """Apply profile preset configuration (key-based merge).

    The profile overrides only the keys it specifies. All other values
    are inherited from the base configuration.

    Example:
        Base: temperature=0.5, model="gpt-4o-mini"
        Profile strict: {llm: {temperature: 0.1}}
        Result: temperature=0.1, model="gpt-4o-mini" (model inherited)

    Args:
        profile_name: Name of profile to apply (e.g., "strict", "balanced")

    Returns:
        New ReviewConfig with profile values merged in

    Raises:
        KeyError: If profile_name not found in profiles dict
    """
    if profile_name not in self.profiles:
        available = ", ".join(self.profiles.keys()) if self.profiles else "none"
        raise KeyError(
            f"Profile '{profile_name}' not found. "
            f"Available profiles: {available}"
        )

    profile_dict = self.profiles[profile_name]

    # Start with current values (base config)
    new_llm = self._merge_llm_profile(profile_dict.get("llm", {}))
    new_prompts = self._merge_prompts_profile(profile_dict.get("prompts", {}))
    new_retry = self._merge_retry_profile(profile_dict.get("retry", {}))
    new_checks = self._merge_checks_profile(profile_dict.get("checks", {}))
    new_output = self._merge_output_profile(profile_dict.get("output", {}))
    new_context = self._merge_context_profile(profile_dict.get("context", {}))
    new_logging = self._merge_logging_profile(profile_dict.get("logging", {}))

    return dataclasses.replace(
        self,
        profile=profile_name,
        llm=new_llm,
        prompts=new_prompts,
        retry=new_retry,
        checks=new_checks,
        output=new_output,
        context=new_context,
        logging=new_logging,
    )

def _merge_llm_profile(self, llm_profile: Dict[str, Any]) -> LLMConfig:
    """Merge LLM profile override into current config."""
    if not llm_profile:
        return self.llm

    return LLMConfig(
        provider=llm_profile.get("provider", self.llm.provider),
        model=llm_profile.get("model", self.llm.model),
        temperature=llm_profile.get("temperature", self.llm.temperature),
        top_p=llm_profile.get("top_p", self.llm.top_p),
        max_tokens_request=llm_profile.get("max_tokens_request", self.llm.max_tokens_request),
        max_tokens_response=llm_profile.get("max_tokens_response", self.llm.max_tokens_response),
        timeout=llm_profile.get("timeout", self.llm.timeout),
    )

def _merge_prompts_profile(self, prompts_profile: Dict[str, Any]) -> PromptConfig:
    """Merge prompts profile override."""
    if not prompts_profile:
        return self.prompts

    variables = {**self.prompts.variables, **prompts_profile.get("variables", {})}

    return PromptConfig(
        system_prompt=Path(prompts_profile["system"]) if prompts_profile.get("system") else self.prompts.system_prompt,
        user_prompt=Path(prompts_profile["user"]) if prompts_profile.get("user") else self.prompts.user_prompt,
        result_template=Path(prompts_profile["result_template"]) if prompts_profile.get("result_template") else self.prompts.result_template,
        variables=variables,
    )

def _merge_retry_profile(self, retry_profile: Dict[str, Any]) -> RetryConfig:
    """Merge retry profile override."""
    if not retry_profile:
        return self.retry

    return RetryConfig(
        max_retries=retry_profile.get("max_retries", self.retry.max_retries),
        backoff=retry_profile.get("backoff", self.retry.backoff),
        initial_delay=retry_profile.get("initial_delay", self.retry.initial_delay),
    )

def _merge_checks_profile(self, checks_profile: Dict[str, Any]) -> CheckConfig:
    """Merge checks profile override."""
    if not checks_profile:
        return self.checks

    return CheckConfig(
        security=checks_profile.get("security", self.checks.security),
        performance=checks_profile.get("performance", self.checks.performance),
        style=checks_profile.get("style", self.checks.style),
    )

def _merge_output_profile(self, output_profile: Dict[str, Any]) -> OutputConfig:
    """Merge output profile override."""
    if not output_profile:
        return self.output

    return OutputConfig(
        format=output_profile.get("format", self.output.format),
        include_snippets=output_profile.get("include_snippets", self.output.include_snippets),
        max_comment_length=output_profile.get("max_comment_length", self.output.max_comment_length),
    )

def _merge_context_profile(self, context_profile: Dict[str, Any]) -> ContextConfig:
    """Merge context profile override."""
    if not context_profile:
        return self.context

    return ContextConfig(
        window_size=context_profile.get("window_size", self.context.window_size),
        include_patterns=context_profile.get("include_patterns", self.context.include_patterns),
        exclude_patterns=context_profile.get("exclude_patterns", self.context.exclude_patterns),
    )

def _merge_logging_profile(self, logging_profile: Dict[str, Any]) -> LoggingConfig:
    """Merge logging profile override."""
    if not logging_profile:
        return self.logging

    return LoggingConfig(
        level=logging_profile.get("level", self.logging.level),
        debug=logging_profile.get("debug", self.logging.debug),
    )
```

**Add import**:
```python
import dataclasses
```

**Validation**:
- [ ] Profile with single key overrides only that key
- [ ] Empty profile dict returns unchanged config
- [ ] KeyError raised for missing profile with helpful message
- [ ] Returns new instance (immutable pattern preserved)

---

### T010: Implement merge_with_cli() method

**Purpose**: Apply CLI flag overrides with highest priority.

**Implementation**:

```python
def merge_with_cli(self, cli_overrides: Dict[str, Any]) -> "ReviewConfig":
    """Apply CLI flag overrides (highest priority).

    CLI overrides take precedence over both base config and profile settings.
    Uses dot notation for nested keys (e.g., "llm.temperature").

    Example:
        cli_overrides = {"llm.temperature": 0.1, "checks.security": False}
        Result: Only these specific values changed, rest unchanged

    Args:
        cli_overrides: Dictionary of CLI flag values

    Returns:
        New ReviewConfig with CLI overrides applied

    Raises:
        ValueError: If override path is invalid or value has wrong type
    """
    if not cli_overrides:
        return self

    new_config = self

    # Process each CLI override
    for key_path, value in cli_overrides.items():
        parts = key_path.split(".")
        new_config = new_config._apply_cli_override(parts, value)

    return new_config

def _apply_cli_override(self, parts: List[str], value: Any) -> "ReviewConfig":
    """Apply a single CLI override to the config.

    Args:
        parts: Dot-separated path parts (e.g., ["llm", "temperature"])
        value: Value to set

    Returns:
        New ReviewConfig with override applied

    Raises:
        ValueError: If path is invalid or value type is wrong
    """
    if len(parts) < 2:
        raise ValueError(
            f"Invalid override path: '{'.'.join(parts)}'. "
            f"Must be in format 'section.field' (e.g., 'llm.temperature')"
        )

    section = parts[0]
    field = parts[1] if len(parts) > 1 else None

    if section == "llm":
        return self._apply_llm_cli_override(field, value)
    elif section == "prompts":
        return self._apply_prompts_cli_override(field, value)
    elif section == "retry":
        return self._apply_retry_cli_override(field, value)
    elif section == "checks":
        return self._apply_checks_cli_override(field, value)
    elif section == "output":
        return self._apply_output_cli_override(field, value)
    elif section == "context":
        return self._apply_context_cli_override(field, value)
    elif section == "logging":
        return self._apply_logging_cli_override(field, value)
    else:
        raise ValueError(f"Unknown config section: '{section}'")

def _apply_llm_cli_override(self, field: str, value: Any) -> "ReviewConfig":
    """Apply LLM CLI override."""
    valid_fields = {
        "provider": str,
        "model": str,
        "temperature": (int, float),
        "top_p": (int, float),
        "max_tokens_request": int,
        "max_tokens_response": int,
        "timeout": int,
    }

    if field not in valid_fields:
        raise ValueError(
            f"Unknown LLM field: '{field}'. "
            f"Valid fields: {', '.join(valid_fields.keys())}"
        )

    expected_type = valid_fields[field]
    if not isinstance(value, expected_type):
        raise ValueError(
            f"Invalid type for '{field}': expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )

    new_llm = dataclasses.replace(self.llm, **{field: value})
    return dataclasses.replace(self, llm=new_llm)

def _apply_checks_cli_override(self, field: str, value: Any) -> "ReviewConfig":
    """Apply checks CLI override."""
    valid_fields = {"security": bool, "performance": bool, "style": bool}

    if field not in valid_fields:
        raise ValueError(
            f"Unknown checks field: '{field}'. "
            f"Valid fields: {', '.join(valid_fields.keys())}"
        )

    if not isinstance(value, bool):
        raise ValueError(
            f"Invalid type for 'checks.{field}': expected bool, "
            f"got {type(value).__name__}"
        )

    new_checks = dataclasses.replace(self.checks, **{field: value})
    return dataclasses.replace(self, checks=new_checks)

# Similar helper methods for other sections...
```

**Validation**:
- [ ] Single override applied correctly
- [ ] Multiple overrides applied together
- [ ] Invalid section raises ValueError
- [ ] Invalid field raises ValueError with valid options
- [ ] Type mismatch raises ValueError
- [ ] Empty dict returns unchanged config

---

### T011: Create deep_merge helper function

**Purpose**: Helper for deep merging nested dictionaries.

**Implementation**:

```python
def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Values in override take precedence, but nested dicts are merged
    recursively rather than replaced.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        New merged dictionary (neither input is modified)

    Example:
        base = {"llm": {"temperature": 0.5, "model": "gpt-4"}}
        override = {"llm": {"temperature": 0.1}}
        result = {"llm": {"temperature": 0.1, "model": "gpt-4"}}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result
```

**Validation**:
- [ ] Flat dicts merge correctly
- [ ] Nested dicts merge recursively
- [ ] Override values replace base values
- [ ] Original dicts not modified (pure function)

---

### T012: Implement placeholder substitution logic

**Purpose**: Substitute placeholders in prompt templates with variable values.

**Implementation**:

```python
import re
from typing import Dict

def substitute_placeholders(template: str, variables: Dict[str, str]) -> str:
    """Substitute placeholders in template string.

    Supports {variable} syntax. Placeholder names that don't exist
    in variables are left unchanged (no error).

    Built-in placeholders:
        {file_path}: Path to file being reviewed
        {timestamp}: Current timestamp

    Args:
        template: Template string with {placeholder} markers
        variables: Dictionary of variable names to values

    Returns:
        String with placeholders replaced

    Example:
        template = "Reviewing {file_path} for {project_name}"
        variables = {"file_path": "/path/to/file.py", "project_name": "MyApp"}
        result = "Reviewing /path/to/file.py for MyApp"
    """
    # Add built-in variables
    from datetime import datetime
    all_vars = {
        "timestamp": datetime.now().isoformat(),
        **variables,
    }

    # Replace all {var} placeholders
    pattern = r"\{(\w+)\}"

    def replacer(match):
        placeholder = match.group(1)
        return str(all_vars.get(placeholder, match.group(0)))

    return re.sub(pattern, replacer, template)
```

**Validation**:
- [ ] Existing placeholders replaced
- [ ] Missing placeholders left as-is
- [ ] Multiple placeholders in one string
- [ ] Built-in variables (timestamp) work
- [ ] Special characters in values handled correctly

---

### T013: Add profile validation

**Purpose**: Validate that selected profile exists before merge.

**Implementation**:

Add helper method to `ReviewConfig`:

```python
def validate_profile(self, profile_name: str) -> None:
    """Validate that a profile exists.

    Args:
        profile_name: Profile name to validate

    Raises:
        KeyError: If profile doesn't exist
    """
    if profile_name not in self.profiles:
        available = ", ".join(sorted(self.profiles.keys())) if self.profiles else "none"
        raise KeyError(
            f"Profile '{profile_name}' not found. "
            f"Available profiles: {available}"
        )
```

**Update merge_with_profile** to use this validation:
```python
def merge_with_profile(self, profile_name: str) -> "ReviewConfig":
    self.validate_profile(profile_name)
    # ... rest of implementation
```

**Validation**:
- [ ] Valid profile passes validation
- [ ] Invalid profile raises KeyError
- [ ] Error message includes available profiles
- [ ] Empty profiles dict handled gracefully

## Test Strategy

**Manual Testing** (before WP05):
```python
# Test 1: Profile merge (key-based)
base = ReviewConfig.from_dict({
    "llm": {"temperature": 0.5, "model": "gpt-4o-mini"}
})
base.profiles = {
    "strict": {"llm": {"temperature": 0.1}}
}
merged = base.merge_with_profile("strict")
assert merged.llm.temperature == 0.1  # Overridden
assert merged.llm.model == "gpt-4o-mini"  # Inherited

# Test 2: CLI override
cli_merged = merged.merge_with_cli({"llm.temperature": 0.3})
assert cli_merged.llm.temperature == 0.3  # CLI wins

# Test 3: Placeholder substitution
template = "Review: {file_path}"
result = substitute_placeholders(template, {"file_path": "/path/to/file.py"})
assert result == "Review: /path/to/file.py"
```

## Definition of Done

- [ ] `merge_with_profile()` implements key-based merge
- [ ] `merge_with_cli()` applies CLI overrides with highest priority
- [ ] `deep_merge()` helper works for nested dicts
- [ ] `substitute_placeholders()` replaces {var} patterns
- [ ] `validate_profile()` raises helpful KeyError for invalid profiles
- [ ] All methods return new instances (immutability preserved)
- [ ] Error messages are descriptive and helpful
- [ ] Code is type-annotated

## Reviewer Guidance

**Verify**:
1. Merge is key-based, not full override
2. CLI overrides have highest priority
3. Immutable pattern preserved (dataclasses.replace)
4. Error messages include available options
5. Placeholder substitution handles missing variables gracefully

**Common Issues**:
- Full override instead of key-based merge → Profile changes too many values
- Wrong priority → CLI doesn't override profile
- Mutation instead of new instance → Breaks immutability

## Risks

- **Medium Risk**: Merge logic complexity, especially nested structures
- **Mitigation**: Comprehensive unit tests for edge cases (WP05)

## Activity Log

- 2026-02-21T11:10:08Z – claude – shell_pid=79399 – lane=doing – Assigned agent via workflow command
- 2026-02-21T11:12:29Z – claude – shell_pid=79399 – lane=for_review – Ready for review: Hierarchical merge logic with profile/CLI overrides implemented
- 2026-02-21T11:40:47Z – claude – shell_pid=79399 – lane=doing – Starting review
- 2026-02-21T11:42:31Z – claude – shell_pid=79399 – lane=planned – Moved to planned
- 2026-02-21T11:42:35Z – claude – shell_pid=79399 – lane=doing – Fixing CLI override error message bug
- 2026-02-21T11:43:20Z – claude – shell_pid=79399 – lane=for_review – Bug fixed: CLI override error messages now handle type tuples correctly
- 2026-02-21T11:43:26Z – claude – shell_pid=79399 – lane=doing – Reviewing after bug fix
- 2026-02-21T11:43:31Z – claude – shell_pid=79399 – lane=done – Review passed: Bug fixed, all merge logic methods work correctly
