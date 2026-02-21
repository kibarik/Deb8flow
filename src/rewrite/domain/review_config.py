"""
Review agent configuration value objects.

This module contains all dataclass value objects for the review agent
configuration system. All objects are immutable (frozen=True) and follow
the pattern established by RewriteConfig.
"""
import dataclasses
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass(frozen=True)
class LLMConfig:
    """LLM provider and model configuration.

    Attributes:
        provider: LLM provider name (e.g., "openai", "anthropic")
        model: Model identifier (e.g., "gpt-4o-mini")
        temperature: Sampling temperature (0.0 - 1.0)
        top_p: Nucleus sampling parameter (0.0 - 1.0)
        max_tokens_request: Max tokens for outgoing requests
        max_tokens_response: Max tokens for response generation
        timeout: Request timeout in seconds
    """
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens_request: int = 4000
    max_tokens_response: int = 2000
    timeout: int = 120

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(
                f"temperature must be between 0.0 and 1.0, got {self.temperature}"
            )
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError(
                f"top_p must be between 0.0 and 1.0, got {self.top_p}"
            )
        if self.max_tokens_request < 1:
            raise ValueError("max_tokens_request must be positive")
        if self.max_tokens_response < 1:
            raise ValueError("max_tokens_response must be positive")
        if self.timeout < 1:
            raise ValueError("timeout must be positive")


@dataclass(frozen=True)
class PromptConfig:
    """Prompt and template configuration.

    Attributes:
        system_prompt: Path to system prompt template (optional)
        user_prompt: Path to user prompt template (optional)
        result_template: Path to result output template (optional)
        variables: Dictionary of variables for placeholder substitution
    """
    system_prompt: Optional[Path] = None
    user_prompt: Optional[Path] = None
    result_template: Optional[Path] = None
    variables: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetryConfig:
    """Retry policy configuration.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff: Backoff strategy - "exponential", "linear", or "constant"
        initial_delay: Initial delay in seconds before first retry
    """
    max_retries: int = 3
    backoff: str = "exponential"
    initial_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError(
                f"max_retries must be non-negative, got {self.max_retries}"
            )
        if self.backoff not in ("exponential", "linear", "constant"):
            raise ValueError(
                f"backoff must be 'exponential', 'linear', or 'constant', "
                f"got '{self.backoff}'"
            )
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")


@dataclass(frozen=True)
class CheckConfig:
    """Check enable/disable configuration.

    Attributes:
        security: Enable security checks
        performance: Enable performance checks
        style: Enable style checks
    """
    security: bool = True
    performance: bool = True
    style: bool = True


@dataclass(frozen=True)
class OutputConfig:
    """Output format configuration.

    Attributes:
        format: Output format - "markdown" or "json"
        include_snippets: Include code snippets in output
        max_comment_length: Maximum length for individual comments
    """
    format: str = "markdown"
    include_snippets: bool = True
    max_comment_length: int = 500

    def __post_init__(self):
        """Validate configuration values."""
        if self.format not in ("markdown", "json"):
            raise ValueError(
                f"format must be 'markdown' or 'json', got '{self.format}'"
            )
        if self.max_comment_length < 1:
            raise ValueError("max_comment_length must be positive")


@dataclass(frozen=True)
class ContextConfig:
    """Context and filtering configuration.

    Attributes:
        window_size: Maximum context window size in tokens
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
    """
    window_size: int = 8000
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration.

    Attributes:
        level: Log level - "ERROR", "WARN", "INFO", or "DEBUG"
        debug: Enable debug mode with statistics
    """
    level: str = "INFO"
    debug: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        valid_levels = ("ERROR", "WARN", "INFO", "DEBUG")
        if self.level.upper() not in valid_levels:
            raise ValueError(
                f"level must be one of {valid_levels}, got '{self.level}'"
            )


@dataclass(frozen=True)
class ReviewConfig:
    """Root configuration for review agent.

    This is the main configuration object that contains all sub-configurations
    and handles loading from YAML dictionary structure.

    Attributes:
        profile: Default profile name (strict/balanced/lenient)
        llm: LLM configuration
        prompts: Prompt configuration
        retry: Retry policy configuration
        checks: Check configuration
        output: Output configuration
        context: Context configuration
        logging: Logging configuration
        profiles: Dictionary of profile presets for merge operations
    """
    profile: str = "balanced"
    llm: LLMConfig = field(default_factory=LLMConfig)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    checks: CheckConfig = field(default_factory=CheckConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "ReviewConfig":
        """Create ReviewConfig from YAML config dictionary.

        Expected structure:
        {
            "profile": "balanced",
            "llm": {"provider": "openai", "model": "gpt-4o-mini", ...},
            "prompts": {"system_prompt": "path/to/file.md", ...},
            ...
        }

        Args:
            config: Dictionary from loaded YAML file

        Returns:
            ReviewConfig instance with values extracted or defaults

        Raises:
            ValueError: If configuration values are invalid
            TypeError: If configuration has wrong types
        """
        # Extract LLM config
        llm_dict = config.get("llm", {})
        llm = LLMConfig(
            provider=llm_dict.get("provider", "openai"),
            model=llm_dict.get("model", "gpt-4o-mini"),
            temperature=llm_dict.get("temperature", 0.7),
            top_p=llm_dict.get("top_p", 0.9),
            max_tokens_request=llm_dict.get("max_tokens_request", 4000),
            max_tokens_response=llm_dict.get("max_tokens_response", 2000),
            timeout=llm_dict.get("timeout", 120),
        )

        # Extract prompts config
        prompts_dict = config.get("prompts", {})
        prompts = PromptConfig(
            system_prompt=Path(prompts_dict["system"]) if prompts_dict.get("system") else None,
            user_prompt=Path(prompts_dict["user"]) if prompts_dict.get("user") else None,
            result_template=Path(prompts_dict["result_template"]) if prompts_dict.get("result_template") else None,
            variables=prompts_dict.get("variables", {}),
        )

        # Extract retry config
        retry_dict = config.get("retry", {})
        retry = RetryConfig(
            max_retries=retry_dict.get("max_retries", 3),
            backoff=retry_dict.get("backoff", "exponential"),
            initial_delay=retry_dict.get("initial_delay", 1.0),
        )

        # Extract checks config
        checks_dict = config.get("checks", {})
        checks = CheckConfig(
            security=checks_dict.get("security", True),
            performance=checks_dict.get("performance", True),
            style=checks_dict.get("style", True),
        )

        # Extract output config
        output_dict = config.get("output", {})
        output = OutputConfig(
            format=output_dict.get("format", "markdown"),
            include_snippets=output_dict.get("include_snippets", True),
            max_comment_length=output_dict.get("max_comment_length", 500),
        )

        # Extract context config
        context_dict = config.get("context", {})
        context = ContextConfig(
            window_size=context_dict.get("window_size", 8000),
            include_patterns=context_dict.get("include_patterns", []),
            exclude_patterns=context_dict.get("exclude_patterns", []),
        )

        # Extract logging config
        logging_dict = config.get("logging", {})
        logging = LoggingConfig(
            level=logging_dict.get("level", "INFO"),
            debug=logging_dict.get("debug", False),
        )

        # Extract profiles
        profiles = config.get("profiles", {})

        return cls(
            profile=config.get("profile", "balanced"),
            llm=llm,
            prompts=prompts,
            retry=retry,
            checks=checks,
            output=output,
            context=context,
            logging=logging,
            profiles=profiles,
        )

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
        self.validate_profile(profile_name)

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

    def _merge_llm_profile(self, llm_profile: Dict[str, Any]) -> "LLMConfig":
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

    def _merge_prompts_profile(self, prompts_profile: Dict[str, Any]) -> "PromptConfig":
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

    def _merge_retry_profile(self, retry_profile: Dict[str, Any]) -> "RetryConfig":
        """Merge retry profile override."""
        if not retry_profile:
            return self.retry

        return RetryConfig(
            max_retries=retry_profile.get("max_retries", self.retry.max_retries),
            backoff=retry_profile.get("backoff", self.retry.backoff),
            initial_delay=retry_profile.get("initial_delay", self.retry.initial_delay),
        )

    def _merge_checks_profile(self, checks_profile: Dict[str, Any]) -> "CheckConfig":
        """Merge checks profile override."""
        if not checks_profile:
            return self.checks

        return CheckConfig(
            security=checks_profile.get("security", self.checks.security),
            performance=checks_profile.get("performance", self.checks.performance),
            style=checks_profile.get("style", self.checks.style),
        )

    def _merge_output_profile(self, output_profile: Dict[str, Any]) -> "OutputConfig":
        """Merge output profile override."""
        if not output_profile:
            return self.output

        return OutputConfig(
            format=output_profile.get("format", self.output.format),
            include_snippets=output_profile.get("include_snippets", self.output.include_snippets),
            max_comment_length=output_profile.get("max_comment_length", self.output.max_comment_length),
        )

    def _merge_context_profile(self, context_profile: Dict[str, Any]) -> "ContextConfig":
        """Merge context profile override."""
        if not context_profile:
            return self.context

        return ContextConfig(
            window_size=context_profile.get("window_size", self.context.window_size),
            include_patterns=context_profile.get("include_patterns", self.context.include_patterns),
            exclude_patterns=context_profile.get("exclude_patterns", self.context.exclude_patterns),
        )

    def _merge_logging_profile(self, logging_profile: Dict[str, Any]) -> "LoggingConfig":
        """Merge logging profile override."""
        if not logging_profile:
            return self.logging

        return LoggingConfig(
            level=logging_profile.get("level", self.logging.level),
            debug=logging_profile.get("debug", self.logging.debug),
        )

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
            # Format type name for error message (handles both single types and tuples)
            if isinstance(expected_type, tuple):
                type_names = " or ".join(t.__name__ for t in expected_type)
            else:
                type_names = expected_type.__name__
            raise ValueError(
                f"Invalid type for '{field}': expected {type_names}, "
                f"got {type(value).__name__}"
            )

        new_llm = dataclasses.replace(self.llm, **{field: value})
        return dataclasses.replace(self, llm=new_llm)

    def _apply_prompts_cli_override(self, field: str, value: Any) -> "ReviewConfig":
        """Apply prompts CLI override."""
        if field == "variables":
            if not isinstance(value, dict):
                raise ValueError(
                    f"Invalid type for 'prompts.variables': expected dict, "
                    f"got {type(value).__name__}"
                )
            new_prompts = dataclasses.replace(self.prompts, variables=value)
            return dataclasses.replace(self, prompts=new_prompts)
        else:
            raise ValueError(
                f"Unknown prompts field: '{field}'. "
                f"Valid fields: variables"
            )

    def _apply_retry_cli_override(self, field: str, value: Any) -> "ReviewConfig":
        """Apply retry CLI override."""
        valid_fields = {
            "max_retries": int,
            "backoff": str,
            "initial_delay": (int, float),
        }

        if field not in valid_fields:
            raise ValueError(
                f"Unknown retry field: '{field}'. "
                f"Valid fields: {', '.join(valid_fields.keys())}"
            )

        expected_type = valid_fields[field]
        if not isinstance(value, expected_type):
            # Format type name for error message (handles both single types and tuples)
            if isinstance(expected_type, tuple):
                type_names = " or ".join(t.__name__ for t in expected_type)
            else:
                type_names = expected_type.__name__
            raise ValueError(
                f"Invalid type for '{field}': expected {type_names}, "
                f"got {type(value).__name__}"
            )

        new_retry = dataclasses.replace(self.retry, **{field: value})
        return dataclasses.replace(self, retry=new_retry)

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

    def _apply_output_cli_override(self, field: str, value: Any) -> "ReviewConfig":
        """Apply output CLI override."""
        valid_fields = {
            "format": str,
            "include_snippets": bool,
            "max_comment_length": int,
        }

        if field not in valid_fields:
            raise ValueError(
                f"Unknown output field: '{field}'. "
                f"Valid fields: {', '.join(valid_fields.keys())}"
            )

        expected_type = valid_fields[field]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Invalid type for '{field}': expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

        new_output = dataclasses.replace(self.output, **{field: value})
        return dataclasses.replace(self, output=new_output)

    def _apply_context_cli_override(self, field: str, value: Any) -> "ReviewConfig":
        """Apply context CLI override."""
        if field == "window_size":
            if not isinstance(value, int):
                raise ValueError(
                    f"Invalid type for 'context.window_size': expected int, "
                    f"got {type(value).__name__}"
                )
            new_context = dataclasses.replace(self.context, window_size=value)
            return dataclasses.replace(self, context=new_context)
        elif field == "include_patterns":
            if not isinstance(value, list):
                raise ValueError(
                    f"Invalid type for 'context.include_patterns': expected list, "
                    f"got {type(value).__name__}"
                )
            new_context = dataclasses.replace(self.context, include_patterns=value)
            return dataclasses.replace(self, context=new_context)
        elif field == "exclude_patterns":
            if not isinstance(value, list):
                raise ValueError(
                    f"Invalid type for 'context.exclude_patterns': expected list, "
                    f"got {type(value).__name__}"
                )
            new_context = dataclasses.replace(self.context, exclude_patterns=value)
            return dataclasses.replace(self, context=new_context)
        else:
            raise ValueError(
                f"Unknown context field: '{field}'. "
                f"Valid fields: window_size, include_patterns, exclude_patterns"
            )

    def _apply_logging_cli_override(self, field: str, value: Any) -> "ReviewConfig":
        """Apply logging CLI override."""
        valid_fields = {"level": str, "debug": bool}

        if field not in valid_fields:
            raise ValueError(
                f"Unknown logging field: '{field}'. "
                f"Valid fields: {', '.join(valid_fields.keys())}"
            )

        expected_type = valid_fields[field]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Invalid type for '{field}': expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

        new_logging = dataclasses.replace(self.logging, **{field: value})
        return dataclasses.replace(self, logging=new_logging)


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
