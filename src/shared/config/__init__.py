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
    load_config,
    EXAMPLE_CONFIGS
)

__all__ = [
    "DebateConfigFile",
    "LLMConfig",
    "DebateConfig",
    "OutputConfig",
    "LoggingConfig",
    "load_config",
    "EXAMPLE_CONFIGS"
]
