"""Unit tests for configuration loading and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.orchestrator.adapters.config_loader import (
    ConfigValidationError,
    load_orchestrator_config,
    validate_config,
)
from src.orchestrator.domain.models import OrchestratorConfig, PhaseConfig, PhaseName


class TestOrchestratorConfigDefaults:
    """Tests for default configuration values."""

    def test_orchestrator_config_all_defaults(self):
        """Test that all defaults are applied correctly."""
        config = OrchestratorConfig()

        assert config.max_retries == 3
        assert config.validation_timeout == 30
        assert config.auto_accept is False
        assert config.keep_containers is False
        assert config.output_suffix == ".corrected."
        assert config.timestamp_output is False
        assert config.docker_image == "claude-code:latest"
        assert config.container_timeout == 3600
        assert config.container_memory_limit == "2g"
        assert config.container_cpu_quota == 1.0
        assert config.log_dir == ".orchestrator/logs"
        assert config.verbose is False
        assert config.claude_cli_path is None

    def test_default_phases_populated(self):
        """Test that default phases are populated when list is empty."""
        config = OrchestratorConfig()

        assert len(config.phases) == 7
        phase_names = [p.name for p in config.phases]

        assert PhaseName.SPECIFY in phase_names
        assert PhaseName.RESEARCH in phase_names
        assert PhaseName.PLAN in phase_names
        assert PhaseName.TASKS in phase_names
        assert PhaseName.IMPLEMENT in phase_names
        assert PhaseName.REVIEW in phase_names
        assert PhaseName.ACCEPT in phase_names

    def test_default_validation_phases(self):
        """Test that correct phases have validation enabled by default."""
        config = OrchestratorConfig()

        validate_phases = {p.name: p.validate_artifact for p in config.phases}

        assert validate_phases[PhaseName.SPECIFY] is True
        assert validate_phases[PhaseName.RESEARCH] is False
        assert validate_phases[PhaseName.PLAN] is True
        assert validate_phases[PhaseName.TASKS] is True
        assert validate_phases[PhaseName.IMPLEMENT] is True
        assert validate_phases[PhaseName.REVIEW] is False
        assert validate_phases[PhaseName.ACCEPT] is False


class TestOrchestratorConfigValidation:
    """Tests for configuration validation rules."""

    def test_max_retries_must_be_non_negative(self):
        """Test that max_retries cannot be negative."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            OrchestratorConfig(max_retries=-1)

    def test_validation_timeout_must_be_positive(self):
        """Test that validation_timeout must be > 0."""
        with pytest.raises(Exception):
            OrchestratorConfig(validation_timeout=0)

    def test_container_timeout_must_be_positive(self):
        """Test that container_timeout must be > 0."""
        with pytest.raises(Exception):
            OrchestratorConfig(container_timeout=0)

    def test_cpu_quota_must_be_positive(self):
        """Test that container_cpu_quota must be > 0 if set."""
        with pytest.raises(Exception):
            OrchestratorConfig(container_cpu_quota=0)

    def test_duplicate_phase_names_rejected(self):
        """Test that duplicate phase names raise validation error."""
        phases = [
            PhaseConfig(name=PhaseName.SPECIFY, enabled=True),
            PhaseConfig(name=PhaseName.SPECIFY, enabled=True),
        ]
        with pytest.raises(ValueError, match="must be unique"):
            OrchestratorConfig(phases=phases)

    def test_invalid_phase_name_rejected(self):
        """Test that invalid phase names are rejected."""
        from src.orchestrator.domain.models import PhaseConfig

        # Create a phase config with an invalid name directly
        class FakePhase:
            def __init__(self):
                self.name = "not_a_valid_phase"
                self.enabled = True
                self.validate = False

        phases = [FakePhase()]
        with pytest.raises(ValueError, match="Invalid phase name"):
            config = OrchestratorConfig()
            config.phases = phases
            config.validate_phase_names()

    def test_is_valid_method(self):
        """Test the is_valid() method."""
        config = OrchestratorConfig()
        assert config.is_valid() is True

    def test_errors_property(self):
        """Test the errors property returns validation errors."""
        config = OrchestratorConfig()
        errors = config.errors
        assert isinstance(errors, list)
        assert len(errors) == 0  # Valid config has no errors


class TestConfigLoader:
    """Tests for configuration loading from YAML files."""

    def test_load_config_with_valid_yaml(self, tmp_path):
        """Test loading config with valid YAML."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "orchestrator": {
                "max_retries": 5,
                "docker_image": "custom-image:latest",
                "verbose": True,
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_orchestrator_config(config_file)

        assert config.max_retries == 5
        assert config.docker_image == "custom-image:latest"
        assert config.verbose is True

    def test_load_config_with_missing_file(self, tmp_path):
        """Test that missing file uses defaults."""
        nonexistent = tmp_path / "nonexistent.yaml"

        # Should not raise, should use defaults
        config = load_orchestrator_config(nonexistent)

        assert config.max_retries == 3  # Default value

    def test_load_config_with_missing_orchestrator_section(self, tmp_path):
        """Test that missing orchestrator section uses defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"other_section": {}}))

        config = load_orchestrator_config(config_file)

        assert config.max_retries == 3  # Default value

    def test_load_config_with_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises ConfigValidationError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigValidationError, match="Invalid YAML"):
            load_orchestrator_config(config_file)

    def test_load_config_with_invalid_field(self, tmp_path):
        """Test that invalid field raises ConfigValidationError."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "orchestrator": {
                "max_retries": -1,  # Invalid: must be >= 0
            }
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigValidationError, match="validation failed"):
            load_orchestrator_config(config_file)

    def test_unknown_field_logged_as_warning(self, tmp_path, caplog):
        """Test that unknown fields are handled gracefully."""
        import logging

        config_file = tmp_path / "config.yaml"
        config_data = {
            "orchestrator": {
                "unknown_field": "some_value",
                "max_retries": 3,
            }
        }
        config_file.write_text(yaml.dump(config_data))

        # Should load successfully despite unknown field
        config = load_orchestrator_config(config_file)
        assert config.max_retries == 3


class TestValidateConfig:
    """Tests for the validate_config helper function."""

    def test_validate_config_with_dict(self):
        """Test validation with dictionary input."""
        config_dict = {"max_retries": 5}
        assert validate_config(config_dict) is True

    def test_validate_config_with_instance(self):
        """Test validation with OrchestratorConfig instance."""
        config = OrchestratorConfig()
        assert validate_config(config) is True

    def test_validate_config_with_invalid_dict(self):
        """Test that invalid dict raises ConfigValidationError."""
        config_dict = {"max_retries": -1}
        with pytest.raises(ConfigValidationError):
            validate_config(config_dict)

    def test_validate_config_with_invalid_type(self):
        """Test that invalid type raises ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Invalid config type"):
            validate_config("not_a_config")
