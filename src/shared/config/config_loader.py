"""
Configuration loader for debate system.

Loads and validates YAML configuration files with support for
environment variable substitution and sensible defaults.
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


def load_env_file(env_path: Optional[Union[str, Path]] = None) -> None:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file (default: .env in current directory)
    """
    if env_path is None:
        env_path = Path(".env")
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        logger.debug(f"No .env file found at {env_path}")
        return

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE or KEY="VALUE" or KEY='VALUE'
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
                        logger.debug(f"Loaded {key} from .env file")

        logger.info(f"Loaded environment variables from {env_path}")

    except Exception as e:
        logger.warning(f"Failed to load .env file: {e}")


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    base_url: str = Field(default="", description="API base URL (empty for OpenAI default)")
    model: str = Field(default="gpt-4o-mini", description="Model name")
    fallback_models: list[str] = Field(default_factory=list, description="Fallback models to try on rate limits")
    api_key: str = Field(default="", description="API key (empty to use env var)")
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    max_tokens: int = Field(default=5000, ge=1, le=32000)
    timeout: int = Field(default=60, ge=1)

    @field_validator("api_key")
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

    def get_effective_base_url(self) -> Optional[str]:
        """Get the effective base URL (None for OpenAI default)."""
        return self.base_url if self.base_url else None

    def get_all_models(self) -> list[str]:
        """Get all models (primary + fallbacks)."""
        return [self.model] + self.fallback_models


class DebateConfig(BaseModel):
    """Debate execution configuration."""
    max_retries: int = Field(default=2, ge=0, le=10)
    max_concurrency: int = Field(default=2, ge=0, le=4)
    language: str = Field(default="")

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        """Normalize language code."""
        return v.strip().lower() if v else ""


class OutputConfig(BaseModel):
    """Output configuration."""
    directory: str = Field(default="./committee_output")
    save_dialogues: bool = Field(default=True)
    save_metadata: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Logging configuration."""
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


class AgentConfig(BaseModel):
    """Configuration for a single debate agent."""
    name: str = Field(description="Agent name/identifier (e.g., 'TPM', 'CPO')")
    prompt_path: str = Field(description="Path to the agent's prompt file")
    role: str = Field(default="opponent", description="Role: 'main' (PRO) or 'opponent' (CON)")

    @field_validator("prompt_path")
    @classmethod
    def validate_prompt_path(cls, v: str) -> str:
        """Validate and resolve prompt path."""
        path = Path(v)
        # If path exists, return as-is
        if path.exists():
            return str(path)

        # Support both absolute and relative paths
        if not path.is_absolute():
            # Try relative to common locations
            for base in [Path.cwd(), Path.cwd() / "config" / "prompts" / "roles"]:
                candidate = base / v
                if candidate.exists():
                    return str(candidate)
                # Also try with just the filename
                candidate = base / path.name
                if candidate.exists():
                    return str(candidate)
        return v


class AgentsConfig(BaseModel):
    """Configuration for debate agents and matchmaking."""
    main_agent: Optional[AgentConfig] = Field(default=None, description="Main agent (PRO position)")
    opponents: list[AgentConfig] = Field(default_factory=list, description="Opponent agents (CON position)")

    @field_validator("main_agent")
    @classmethod
    def validate_main_agent(cls, v: Optional[AgentConfig]) -> Optional[AgentConfig]:
        """Validate that main agent exists."""
        if v is not None and v.role != "main":
            logger.warning(f"Main agent should have role='main', got '{v.role}'")
            v.role = "main"
        return v

    def get_all_agents(self) -> list[AgentConfig]:
        """Get all configured agents (main + opponents)."""
        agents = []
        if self.main_agent:
            agents.append(self.main_agent)
        agents.extend(self.opponents)
        return agents

    def get_main_agent_prompt_path(self) -> str:
        """Get main agent prompt path."""
        if not self.main_agent:
            raise ValueError("No main agent configured")
        return self.main_agent.prompt_path

    def get_opponent_configs(self) -> list[tuple[str, str]]:
        """Get list of (name, prompt_path) tuples for opponents."""
        return [(opp.name, opp.prompt_path) for opp in self.opponents]

    @classmethod
    def from_dict(cls, data: dict) -> "AgentsConfig":
        """
        Create agents config from dictionary.

        Expected format:
        {
            "main": {"name": "TPM", "prompt": "path/to/tpm.txt"},
            "opponents": [
                {"name": "CPO", "prompt": "path/to/cpo.txt"},
                {"name": "CFO", "prompt": "path/to/cfo.txt"}
            ]
        }
        """
        main = None
        if "main" in data and data["main"]:
            main_data = data["main"]
            main = AgentConfig(
                name=main_data.get("name", "MAIN"),
                prompt_path=main_data.get("prompt", main_data.get("prompt_path", "")),
                role="main"
            )

        opponents = []
        if "opponents" in data:
            for opp_data in data["opponents"]:
                opponents.append(AgentConfig(
                    name=opp_data.get("name", "UNKNOWN"),
                    prompt_path=opp_data.get("prompt", opp_data.get("prompt_path", "")),
                    role="opponent"
                ))

        return cls(main_agent=main, opponents=opponents)


class DebateConfigFile(BaseModel):
    """Complete debate configuration file."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    debate: DebateConfig = Field(default_factory=DebateConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: Union[str, Path], load_env: bool = True) -> "DebateConfigFile":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file
            load_env: Whether to load .env file (default: True)

        Returns:
            DebateConfigFile instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValidationError: If configuration is invalid
        """
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Load .env file first
        if load_env:
            load_env_file()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML config: {e}")

        # Substitute environment variables
        data = substitute_env_vars(data)

        # Handle agents section separately
        agents_config = None
        if "agents" in data:
            agents_data = data.pop("agents")
            if agents_data:
                agents_config = AgentsConfig.from_dict(agents_data)

        # Create config instance
        config = cls(**data)
        if agents_config:
            config.agents = agents_config

        return config

    @classmethod
    def from_yaml_or_default(cls, path: Optional[Union[str, Path]] = None, load_env: bool = True) -> "DebateConfigFile":
        """
        Load configuration from YAML file or return defaults.

        Args:
            path: Path to YAML configuration file (optional)
            load_env: Whether to load .env file (default: True)

        Returns:
            DebateConfigFile instance with defaults if file not found
        """
        if path:
            try:
                return cls.from_yaml(path)
            except FileNotFoundError:
                logger.info(f"Config file not found: {path}, using defaults")
            except Exception as e:
                logger.warning(f"Failed to load config from {path}: {e}, using defaults")

        return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {
            "llm": self.llm.model_dump(),
            "debate": self.debate.model_dump(),
            "output": self.output.model_dump(),
            "logging": self.logging.model_dump()
        }
        # Add agents if configured
        if self.agents.main_agent or self.agents.opponents:
            result["agents"] = {
                "main": {
                    "name": self.agents.main_agent.name,
                    "prompt": self.agents.main_agent.prompt_path
                } if self.agents.main_agent else None,
                "opponents": [
                    {"name": opp.name, "prompt": opp.prompt_path}
                    for opp in self.agents.opponents
                ]
            }
        return result

    def get_cli_args_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary suitable for CLI arguments.

        Returns dictionary with keys matching CLI argument names.
        """
        return {
            "model": self.llm.model,
            "base_url": self.llm.get_effective_base_url(),
            "api_key": self.llm.api_key if self.llm.api_key else None,
            "temperature": self.llm.temperature,
            "max_retries": self.debate.max_retries,
            "max_concurrency": self.debate.max_concurrency,
            "language": self.debate.language or None,
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


def load_config(config_path: Optional[Union[str, Path]] = None) -> DebateConfigFile:
    """
    Load debate configuration from file or use defaults.

    This is the main entry point for configuration loading.

    Args:
        config_path: Path to YAML configuration file (optional)
                     If not provided, looks for debate_config.yaml in current directory

    Returns:
        DebateConfigFile instance
    """
    # Try provided path, then default locations
    paths_to_try = []

    if config_path:
        paths_to_try.append(Path(config_path))

    # Add default locations
    paths_to_try.extend([
        Path("debate_config.yaml"),
        Path("config/debate_config.yaml"),
        Path("../debate_config.yaml"),
    ])

    for path in paths_to_try:
        if path.exists():
            logger.info(f"Loading configuration from: {path}")
            return DebateConfigFile.from_yaml(path)

    logger.info("No configuration file found, using defaults")
    return DebateConfigFile()


# Example configurations for common providers
EXAMPLE_CONFIGS = {
    "openai": {
        "llm": {
            "base_url": "",
            "model": "gpt-4o-mini",
            "temperature": 0.8
        }
    },
    "deepseek": {
        "llm": {
            "base_url": "https://api.requesty.ai/v1",
            "model": "deepseek-chat",
            "temperature": 0.8
        }
    },
    "zhipu": {
        "llm": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4",
            "temperature": 0.8
        }
    },
    "ollama": {
        "llm": {
            "base_url": "http://localhost:11434/v1",
            "model": "llama3",
            "temperature": 0.8
        }
    }
}
