"""
Integration tests for review configuration loading workflow.

Tests complete workflow from YAML loading to profile application and CLI overrides.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.rewrite.infrastructure.config_loader import load_config
from src.rewrite.domain.review_config import ReviewConfig


class TestConfigLoadingWorkflow:
    """Tests for complete config loading workflow."""

    def test_load_full_config(self, tmp_path):
        """Test loading complete configuration from YAML file."""
        config_content = {
            "rewrite": {
                "review": {
                    "profile": "strict",
                    "llm": {
                        "provider": "anthropic",
                        "model": "claude-3-5-sonnet-20241022",
                        "temperature": 0.3,
                    },
                    "checks": {
                        "security": True,
                        "performance": True,
                        "style": False,
                    },
                    "profiles": {
                        "strict": {
                            "llm": {"temperature": 0.1}
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.profile == "strict"
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3-5-sonnet-20241022"
        assert config.llm.temperature == 0.3
        assert config.checks.security is True
        assert config.checks.style is False

    def test_load_minimal_config_with_defaults(self, tmp_path):
        """Test loading minimal config uses all defaults."""
        config_content = {"rewrite": {"review": {}}}
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.profile == "balanced"
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o-mini"
        assert config.llm.temperature == 0.7

    def test_load_with_env_var_expansion(self, tmp_path):
        """Test environment variable expansion in config."""
        os.environ["TEST_PROVIDER"] = "anthropic"
        os.environ["TEST_MODEL"] = "claude-3-opus-20240229"

        config_content = {
            "rewrite": {
                "review": {
                    "llm": {
                        "provider": "${TEST_PROVIDER}",
                        "model": "${TEST_MODEL}",
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3-opus-20240229"

        # Cleanup
        del os.environ["TEST_PROVIDER"]
        del os.environ["TEST_MODEL"]

    def test_load_with_env_var_default(self, tmp_path):
        """Test env var default value when variable not set."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {
                        "temperature": "${UNSET_VAR:0.5}",
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.llm.temperature == 0.5


class TestProfileApplication:
    """Tests for profile application workflow."""

    def test_apply_strict_profile(self, tmp_path):
        """Test applying strict profile changes settings."""
        config_content = {
            "rewrite": {
                "review": {
                    "profile": "balanced",
                    "llm": {"temperature": 0.5},
                    "profiles": {
                        "strict": {
                            "llm": {"temperature": 0.1, "top_p": 0.5},
                            "checks": {"security": True, "performance": True, "style": True},
                            "output": {"format": "json"}
                        },
                        "balanced": {}
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="strict")

        assert config.profile == "strict"
        assert config.llm.temperature == 0.1  # Overridden
        assert config.llm.top_p == 0.5  # Overridden

    def test_apply_balanced_profile(self, tmp_path):
        """Test applying balanced profile."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5},
                    "profiles": {
                        "balanced": {
                            "llm": {"temperature": 0.5, "top_p": 0.8},
                            "checks": {"security": True, "performance": True, "style": False},
                            "output": {"format": "markdown"}
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="balanced")

        assert config.llm.temperature == 0.5
        assert config.llm.top_p == 0.8
        assert config.checks.style is False
        assert config.output.format == "markdown"

    def test_profile_inheritance_behavior(self, tmp_path):
        """Test that profile inherits unspecified values."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5, "model": "gpt-4o-mini"},
                    "profiles": {
                        "custom": {
                            "llm": {"temperature": 0.2}  # Only temperature specified
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="custom")

        assert config.llm.temperature == 0.2  # Overridden
        assert config.llm.model == "gpt-4o-mini"  # Inherited


class TestCLIOverride:
    """Tests for CLI override workflow."""

    def test_cli_overrides_base_config(self, tmp_path):
        """Test CLI override of base configuration."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            cli_overrides={"llm.temperature": 0.1}
        )

        assert config.llm.temperature == 0.1

    def test_cli_overrides_profile(self, tmp_path):
        """Test CLI override has highest priority over profile."""
        config_content = {
            "rewrite": {
                "review": {
                    "profiles": {
                        "strict": {"llm": {"temperature": 0.1}}
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            profile="strict",
            cli_overrides={"llm.temperature": 0.05}
        )

        assert config.llm.temperature == 0.05  # CLI wins

    def test_multiple_cli_overrides(self, tmp_path):
        """Test multiple CLI overrides applied."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5, "top_p": 0.9},
                    "checks": {"security": True, "performance": True}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            cli_overrides={
                "llm.temperature": 0.3,
                "llm.top_p": 0.7,
                "checks.security": False
            }
        )

        assert config.llm.temperature == 0.3
        assert config.llm.top_p == 0.7
        assert config.checks.security is False
        assert config.checks.performance is True  # Unchanged


class TestInvalidConfigHandling:
    """Tests for invalid configuration handling."""

    def test_missing_config_file(self, tmp_path):
        """Test error when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(config_file)

        assert "Configuration file not found" in str(exc_info.value)

    def test_invalid_yaml_syntax(self, tmp_path):
        """Test error when YAML has invalid syntax."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("rewrite:\n  review:\n    llm:\n      temperature: 0.5\n\n  bad indent\n")

        with pytest.raises(Exception) as exc_info:
            load_config(config_file)

        # Error should mention YAML parsing
        assert "YAML" in str(exc_info.value).upper() or "parse" in str(exc_info.value).lower()

    def test_invalid_temperature_value(self, tmp_path):
        """Test validation error for invalid temperature."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 1.5}  # Invalid
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)

        assert "temperature" in str(exc_info.value)

    def test_missing_profile_error(self, tmp_path):
        """Test error when specified profile doesn't exist."""
        config_content = {
            "rewrite": {
                "review": {
                    "profiles": {}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(KeyError) as exc_info:
            load_config(config_file, profile="nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_all_checks_disabled_error(self, tmp_path):
        """Test error when all checks are disabled."""
        config_content = {
            "rewrite": {
                "review": {
                    "checks": {
                        "security": False,
                        "performance": False,
                        "style": False
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)

        assert "At least one check" in str(exc_info.value)
