"""
Configuration loader for SDD (Software Design Specification) analyzer.

Loads and validates sdd_config.yaml with support for environment variable
substitution, path resolution, and comprehensive validation.
"""

import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


def substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute environment variables in configuration values.

    Supports syntax: ${VAR_NAME} or ${VAR_NAME:default_value}

    Args:
        value: Configuration value (string, dict, list, or other)

    Returns:
        Value with environment variables substituted
    """
    if isinstance(value, str):
        # Pattern for ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(var_name, default_value)

        return re.sub(pattern, replace_var, value)

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]

    return value


def resolve_prompt_path(prompt_path: str, project_root: Optional[Path] = None) -> str:
    """
    Resolve prompt file path relative to project root.

    Args:
        prompt_path: Path to prompt file (relative or absolute)
        project_root: Project root directory (defaults to current working directory)

    Returns:
        Resolved absolute path to prompt file

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    if project_root is None:
        project_root = Path.cwd()

    path = Path(prompt_path)

    # If absolute path, return as-is
    if path.is_absolute():
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return str(path)

    # Try relative to project root
    resolved = project_root / path
    if resolved.exists():
        return str(resolved)

    # Try relative to src/prompts/
    resolved = project_root / "src" / "prompts" / path
    if resolved.exists():
        return str(resolved)

    # Try relative to current directory
    resolved = Path.cwd() / path
    if resolved.exists():
        return str(resolved)

    raise FileNotFoundError(
        f"Prompt file not found: {prompt_path}\n"
        f"Tried locations:\n"
        f"  - {project_root / path}\n"
        f"  - {project_root / 'src' / 'prompts' / path}\n"
        f"  - {Path.cwd() / path}"
    )


class SddLLMConfig(BaseModel):
    """LLM provider configuration for SDD analysis."""
    base_url: str = Field(default="", description="API base URL")
    model: str = Field(default="gpt-4o-mini", description="Model name")
    fallback_models: list[str] = Field(default_factory=list, description="Fallback models")
    api_key: str = Field(default="", description="API key")
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    max_tokens: int = Field(default=5000, ge=1)
    timeout: int = Field(default=120, ge=1)

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_api_key(cls, v: str) -> str:
        """Resolve API key from argument or environment."""
        if v:
            return v
        # Try common environment variables
        for env_var in ["OPENAI_API_KEY", "LLM_API_KEY", "API_KEY"]:
            env_value = os.environ.get(env_var)
            if env_value:
                logger.debug(f"Using API key from {env_var}")
                return env_value
        return ""


class SddDebateConfig(BaseModel):
    """Debate execution configuration for SDD analysis."""
    mode: str = Field(default="standard", description="Debate mode: standard or simple")
    max_retries: int = Field(default=2, ge=0, le=10)
    max_concurrency: int = Field(default=0, ge=0)
    language: str = Field(default="ru", description="Output language")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate debate mode."""
        valid_modes = ['standard', 'simple']
        v_lower = v.lower()
        if v_lower not in valid_modes:
            raise ValueError(f"Invalid debate mode: {v}. Must be one of {valid_modes}")
        return v_lower


class SddPromptsConfig(BaseModel):
    """SDD-specific prompts configuration."""
    stages: Dict[str, str] = Field(default_factory=dict, description="Debate stage prompts")
    judge: str = Field(default="", description="Judge prompt path")
    context: str = Field(default="", description="Context template path")
    analysis: Dict[str, str] = Field(default_factory=dict, description="Analysis prompts")
    roles: Dict[str, str] = Field(default_factory=dict, description="SDD role prompts")

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate required SDD roles are present."""
        required_roles = ["architect", "devlead", "qa", "security"]
        missing = [r for r in required_roles if r not in v]
        if missing:
            logger.warning(f"Missing recommended SDD roles: {missing}")
        return v


class SddAgentConfig(BaseModel):
    """Configuration for a single SDD agent."""
    name: str = Field(description="Agent name")
    prompt: str = Field(description="Path to agent prompt file")


class SddAgentsConfig(BaseModel):
    """SDD agents configuration."""
    main: SddAgentConfig = Field(description="Main agent (Architect, PRO)")
    opponents: list[SddAgentConfig] = Field(default_factory=list, description="Opponent agents (CON)")

    def get_all_agents(self) -> list[SddAgentConfig]:
        """Get all configured agents."""
        return [self.main] + self.opponents

    @classmethod
    def from_dict(cls, data: dict) -> "SddAgentsConfig":
        """
        Create agents config from dictionary.

        Expected format:
        {
            "main": {"name": "Architect", "prompt": "path/to/architect.md"},
            "opponents": [
                {"name": "DevLead", "prompt": "path/to/devlead.md"}
            ]
        }
        """
        main_data = data.get("main", {})
        main = SddAgentConfig(
            name=main_data.get("name", "Architect"),
            prompt=main_data.get("prompt", "")
        )

        opponents = []
        for opp_data in data.get("opponents", []):
            opponents.append(SddAgentConfig(
                name=opp_data.get("name", "Unknown"),
                prompt=opp_data.get("prompt", "")
            ))

        return cls(main=main, opponents=opponents)


class SddOutputConfig(BaseModel):
    """SDD output configuration."""
    directory: str = Field(default="./sdd_output", description="Output directory")
    save_dialogues: bool = Field(default=True)
    save_metadata: bool = Field(default=True)


class SddLoggingConfig(BaseModel):
    """SDD logging configuration."""
    level: str = Field(default="INFO")
    verbose: bool = Field(default=False)
    quiet: bool = Field(default=False)

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', using 'INFO'")
            return "INFO"
        return v_upper


class SddRewriteConfig(BaseModel):
    """SDD document rewrite configuration."""
    max_rounds: int = Field(default=5, ge=1, description="Maximum verification rounds")
    backup_suffix: str = Field(default=".backup")
    partial_report: str = Field(default="sdd_rewrite_partial_report.md")

    # Review agent configuration
    review: Dict[str, Any] = Field(default_factory=dict, description="Review agent config")

    # Prompt paths for rewrite debate
    prompts: Dict[str, str] = Field(default_factory=dict, description="Rewrite debate prompts")


class SddConfigFile(BaseModel):
    """Complete SDD configuration file."""

    llm: SddLLMConfig = Field(default_factory=SddLLMConfig)
    debate: SddDebateConfig = Field(default_factory=SddDebateConfig)
    prompts: SddPromptsConfig = Field(default_factory=SddPromptsConfig)
    agents: SddAgentsConfig = Field(default_factory=lambda: SddAgentsConfig(
        main=SddAgentConfig(name="Architect", prompt=""),
        opponents=[]
    ))
    output: SddOutputConfig = Field(default_factory=SddOutputConfig)
    logging: SddLoggingConfig = Field(default_factory=SddLoggingConfig)
    rewrite: Optional[SddRewriteConfig] = Field(default=None)

    @classmethod
    def from_yaml(cls, path: Union[str, Path], project_root: Optional[Path] = None) -> "SddConfigFile":
        """
        Load SDD configuration from YAML file.

        Args:
            path: Path to sdd_config.yaml
            project_root: Project root directory for path resolution

        Returns:
            SddConfigFile instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValueError: If configuration validation fails
        """
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"SDD configuration file not found: {path}\n"
                f"Please create config/sdd_config.yaml"
            )

        if project_root is None:
            project_root = config_path.parent.parent

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse SDD config YAML: {e}")

        # Substitute environment variables
        data = substitute_env_vars(data)

        # Validate required top-level sections
        required_sections = ["llm", "debate", "prompts", "agents", "output", "logging"]
        missing_sections = [s for s in required_sections if s not in data]
        if missing_sections:
            raise ValueError(
                f"SDD config missing required sections: {missing_sections}\n"
                f"Required sections: {required_sections}"
            )

        # Handle agents section separately
        agents_config = None
        if "agents" in data:
            agents_data = data.pop("agents")
            agents_config = SddAgentsConfig.from_dict(agents_data)

        # Handle rewrite section (optional)
        rewrite_data = data.pop("rewrite", None)
        rewrite_config = SddRewriteConfig(**rewrite_data) if rewrite_data else None

        # Create config instance
        try:
            config = cls(**data)
        except Exception as e:
            raise ValueError(f"SDD config validation failed: {e}")

        if agents_config:
            config.agents = agents_config

        if rewrite_config:
            config.rewrite = rewrite_config

        # Resolve prompt paths
        config._resolve_prompt_paths(project_root)

        logger.info(f"Loaded SDD configuration from: {config_path}")
        return config

    def _resolve_prompt_paths(self, project_root: Path) -> None:
        """Resolve all prompt file paths relative to project root."""
        # Resolve stage prompts
        for stage, path in self.prompts.stages.items():
            try:
                self.prompts.stages[stage] = resolve_prompt_path(path, project_root)
            except FileNotFoundError as e:
                logger.warning(f"Stage prompt '{stage}': {e}")

        # Resolve judge and context
        for key in ["judge", "context"]:
            path = getattr(self.prompts, key, None)
            if path:
                try:
                    setattr(self.prompts, key, resolve_prompt_path(path, project_root))
                except FileNotFoundError as e:
                    logger.warning(f"{key.capitalize()} prompt: {e}")

        # Resolve analysis prompts
        for analysis_type, path in self.prompts.analysis.items():
            try:
                self.prompts.analysis[analysis_type] = resolve_prompt_path(path, project_root)
            except FileNotFoundError as e:
                logger.warning(f"Analysis prompt '{analysis_type}': {e}")

        # Resolve role prompts
        for role, path in self.prompts.roles.items():
            try:
                self.prompts.roles[role] = resolve_prompt_path(path, project_root)
            except FileNotFoundError as e:
                logger.warning(f"Role prompt '{role}': {e}")

        # Resolve agent prompts
        try:
            self.agents.main.prompt = resolve_prompt_path(self.agents.main.prompt, project_root)
        except FileNotFoundError as e:
            logger.warning(f"Main agent prompt: {e}")

        for opponent in self.agents.opponents:
            try:
                opponent.prompt = resolve_prompt_path(opponent.prompt, project_root)
            except FileNotFoundError as e:
                logger.warning(f"Opponent '{opponent.name}' prompt: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def get_cli_args_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary suitable for CLI arguments.

        Returns dictionary with keys matching CLI argument names.
        """
        return {
            "model": self.llm.model,
            "base_url": self.llm.base_url or None,
            "api_key": self.llm.api_key if self.llm.api_key else None,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "timeout": self.llm.timeout,
            "max_retries": self.debate.max_retries,
            "max_concurrency": self.debate.max_concurrency,
            "language": self.debate.language or None,
            "mode": self.debate.mode,
            "output_dir": Path(self.output.directory),
            "verbose": self.logging.verbose,
            "quiet": self.logging.quiet
        }

    def setup_logging(self) -> None:
        """Configure logging based on configuration."""
        if self.logging.quiet:
            level = logging.WARNING
        elif self.logging.verbose:
            level = logging.DEBUG
        else:
            level = getattr(logging, self.logging.level, logging.INFO)

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def load_sdd_config(
    config_path: Optional[Union[str, Path]] = None,
    project_root: Optional[Path] = None
) -> SddConfigFile:
    """
    Load SDD configuration from file.

    This is the main entry point for SDD configuration loading.

    Args:
        config_path: Path to sdd_config.yaml
                     If not provided, looks in config/sdd_config.yaml
        project_root: Project root directory for path resolution
                     If not provided, inferred from config path

    Returns:
        SddConfigFile instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid

    Example:
        >>> config = load_sdd_config("config/sdd_config.yaml")
        >>> print(config.llm.model)
        gpt-4o-mini
        >>> print(config.agents.main.name)
        Architect
    """
    # Try provided path, then default locations
    paths_to_try = []

    if config_path:
        paths_to_try.append(Path(config_path))

    # Add default locations
    paths_to_try.extend([
        Path("config/sdd_config.yaml"),
        Path("sdd_config.yaml"),
        Path("../config/sdd_config.yaml"),
    ])

    for path in paths_to_try:
        if path.exists():
            logger.info(f"Loading SDD configuration from: {path}")
            return SddConfigFile.from_yaml(path, project_root)

    # If not found, provide helpful error
    raise FileNotFoundError(
        f"SDD configuration file not found.\n"
        f"Tried locations: {[str(p) for p in paths_to_try]}\n"
        f"Please create config/sdd_config.yaml"
    )
