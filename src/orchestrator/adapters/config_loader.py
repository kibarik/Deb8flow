"""Configuration loader adapter for orchestrator settings.

This module handles loading and validation of orchestrator configuration
from the debate_config.yaml file, with fallback to sensible defaults.
"""

import logging
from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError

from src.orchestrator.domain.models import OrchestratorConfig

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails.

    Attributes:
        message: Human-readable error message
        field: Optional field name that caused the error
        original_error: The original validation exception
    """

    def __init__(self, message: str, field: str = None, original_error: Exception = None):
        self.message = message
        self.field = field
        self.original_error = original_error
        super().__init__(self.message)


def load_orchestrator_config(config_path: Path) -> OrchestratorConfig:
    """Load orchestrator configuration from debate_config.yaml.

    Loads the orchestrator: section from the config file, validates
    all values against the schema, and returns an OrchestratorConfig
    instance. Falls back to defaults if the section is missing.

    Args:
        config_path: Path to the debate_config.yaml file

    Returns:
        OrchestratorConfig instance with validated settings

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    # Default configuration (all values will be defaults)
    orchestrator_dict = {}

    # Try to load from file
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                full_config = yaml.safe_load(f) or {}

            # Extract orchestrator section if present
            if isinstance(full_config, dict):
                orchestrator_dict = full_config.get("orchestrator", {})
                if not orchestrator_dict:
                    logger.info(
                        "No 'orchestrator' section found in config, using defaults"
                    )
                else:
                    logger.debug(
                        f"Loaded orchestrator config from {config_path}"
                    )

        except yaml.YAMLError as e:
            raise ConfigValidationError(
                f"Invalid YAML in config file: {e}",
                original_error=e
            )
        except Exception as e:
            raise ConfigValidationError(
                f"Error reading config file: {e}",
                original_error=e
            )
    else:
        logger.warning(
            f"Config file not found: {config_path}, using defaults"
        )

    # Validate and create config
    try:
        config = OrchestratorConfig(**orchestrator_dict)
        logger.info("Orchestrator configuration loaded successfully")
        return config

    except ValidationError as e:
        # Convert Pydantic ValidationError to ConfigValidationError
        errors = e.errors()
        error_messages = []
        for error in errors:
            field = " -> ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_messages.append(f"  {field}: {msg}")

        raise ConfigValidationError(
            f"Configuration validation failed:\n" + "\n".join(error_messages),
            original_error=e
        )

    except Exception as e:
        raise ConfigValidationError(
            f"Unexpected error loading configuration: {e}",
            original_error=e
        )


def validate_config(config: Union[dict, OrchestratorConfig]) -> bool:
    """Validate a configuration dictionary or instance.

    Args:
        config: Either a dict or OrchestratorConfig to validate

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    try:
        if isinstance(config, dict):
            OrchestratorConfig(**config)
        elif isinstance(config, OrchestratorConfig):
            # Pydantic v2 validates on model construction
            # If we have an instance, it's already validated
            pass
        else:
            raise ConfigValidationError(
                f"Invalid config type: {type(config)}"
            )
        return True

    except ValidationError as e:
        raise ConfigValidationError(
            f"Configuration validation failed: {e}",
            original_error=e
        )
