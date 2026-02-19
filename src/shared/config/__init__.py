"""
Configuration management for debate system.

This package provides YAML-based configuration loading with
environment variable support and sensible defaults.
"""

from .config_loader import (
    DebateConfigFile,
    LLMConfig,
    DebateConfig,
    OutputConfig,
    LoggingConfig,
    AgentConfig,
    AgentsConfig,
    load_config,
    EXAMPLE_CONFIGS
)

from .models import (
    PromptsConfig,
    DebateModeConfig,
    LLMConfigModel,
    AgentsConfigModel,
    DebateConfigFull,
    PromptPathsConfig
)

__all__ = [
    # From config_loader
    "DebateConfigFile",
    "LLMConfig",
    "DebateConfig",
    "OutputConfig",
    "LoggingConfig",
    "AgentConfig",
    "AgentsConfig",
    "load_config",
    "EXAMPLE_CONFIGS",
    # From models
    "PromptsConfig",
    "DebateModeConfig",
    "LLMConfigModel",
    "AgentsConfigModel",
    "DebateConfigFull",
    "PromptPathsConfig"
]
