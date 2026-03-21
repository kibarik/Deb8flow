"""
Tests for SDD configuration loader.

Tests cover:
1. YAML parsing
2. Environment variable substitution
3. Validation with clear error messages
4. Prompt path resolution
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from src.shared.config.sdd_config_loader import (
    load_sdd_config,
    SddConfigFile,
    substitute_env_vars,
    resolve_prompt_path,
    SddLLMConfig,
    SddDebateConfig,
    SddAgentsConfig,
    SddPromptsConfig,
)


class TestEnvVarSubstitution:
    """Test environment variable substitution."""

    def test_substitute_simple_var(self):
        """Test simple ${VAR} substitution."""
        os.environ["TEST_VAR"] = "test_value"
        result = substitute_env_vars("${TEST_VAR}")
        assert result == "test_value"
        del os.environ["TEST_VAR"]

    def test_substitute_var_with_default(self):
        """Test ${VAR:default} substitution with default value."""
        result = substitute_env_vars("${NONEXISTENT_VAR:default_value}")
        assert result == "default_value"

    def test_substitute_in_dict(self):
        """Test substitution in dictionary values."""
        os.environ["KEY"] = "value"
        result = substitute_env_vars({"key": "${KEY}", "other": "static"})
        assert result == {"key": "value", "other": "static"}
        del os.environ["KEY"]

    def test_substitute_in_list(self):
        """Test substitution in list values."""
        os.environ["ITEM"] = "item_value"
        result = substitute_env_vars(["${ITEM}", "static"])
        assert result == ["item_value", "static"]
        del os.environ["ITEM"]

    def test_substitute_nested(self):
        """Test substitution in nested structures."""
        os.environ["VAR"] = "value"
        result = substitute_env_vars({
            "key": "${VAR}",
            "nested": {"list": ["${VAR}", "static"]}
        })
        assert result == {
            "key": "value",
            "nested": {"list": ["value", "static"]}
        }
        del os.environ["VAR"]

    def test_no_substitute_non_string(self):
        """Test that non-string values are passed through."""
        result = substitute_env_vars({"int": 42, "float": 3.14, "bool": True})
        assert result == {"int": 42, "float": 3.14, "bool": True}


class TestPromptPathResolution:
    """Test prompt file path resolution."""

    def test_resolve_absolute_path(self):
        """Test resolving absolute path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("test prompt")
            f.flush()
            result = resolve_prompt_path(f.name)
            assert result == f.name
            Path(f.name).unlink()

    def test_resolve_relative_to_project_root(self):
        """Test resolving relative path to project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("test prompt")

            result = resolve_prompt_path("test.md", Path(tmpdir))
            assert result == str(test_file)

    def test_resolve_relative_to_prompts_dir(self):
        """Test resolving relative path to src/prompts/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "src" / "prompts"
            prompts_dir.mkdir(parents=True)
            test_file = prompts_dir / "test.md"
            test_file.write_text("test prompt")

            result = resolve_prompt_path("test.md", Path(tmpdir))
            assert result == str(test_file)

    def test_resolve_not_found(self):
        """Test error when file not found."""
        with pytest.raises(FileNotFoundError) as exc_info:
            resolve_prompt_path("nonexistent.md", Path("/tmp"))

        assert "Prompt file not found" in str(exc_info.value)
        assert "nonexistent.md" in str(exc_info.value)


class TestSddLLMConfig:
    """Test LLM configuration model."""

    def test_default_values(self):
        """Test default LLM config values."""
        config = SddLLMConfig()
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.8
        assert config.max_tokens == 5000
        assert config.timeout == 120
        assert config.base_url == ""
        assert config.fallback_models == []

    def test_api_key_from_env(self):
        """Test API key resolution from environment."""
        os.environ["OPENAI_API_KEY"] = "test_key"
        # Pass empty string to trigger environment lookup
        config = SddLLMConfig(api_key="")
        assert config.api_key == "test_key"
        del os.environ["OPENAI_API_KEY"]

    def test_custom_values(self):
        """Test custom LLM config values."""
        config = SddLLMConfig(
            model="gpt-4o",
            temperature=0.5,
            max_tokens=3000,
            timeout=60
        )
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.max_tokens == 3000
        assert config.timeout == 60

    def test_temperature_validation(self):
        """Test temperature range validation."""
        with pytest.raises(ValidationError):
            SddLLMConfig(temperature=3.0)  # Too high

        with pytest.raises(ValidationError):
            SddLLMConfig(temperature=-0.5)  # Too low


class TestSddDebateConfig:
    """Test debate configuration model."""

    def test_default_values(self):
        """Test default debate config values."""
        config = SddDebateConfig()
        assert config.mode == "standard"
        assert config.max_retries == 2
        assert config.max_concurrency == 0
        assert config.language == "ru"

    def test_mode_validation(self):
        """Test debate mode validation."""
        with pytest.raises(ValidationError) as exc_info:
            SddDebateConfig(mode="invalid")

        assert "Invalid debate mode" in str(exc_info.value)

    def test_valid_modes(self):
        """Test that valid modes are accepted."""
        for mode in ["standard", "simple"]:
            config = SddDebateConfig(mode=mode)
            assert config.mode == mode

    def test_mode_case_insensitive(self):
        """Test that mode is normalized to lowercase."""
        config = SddDebateConfig(mode="STANDARD")
        assert config.mode == "standard"


class TestSddAgentsConfig:
    """Test agents configuration model."""

    def test_from_dict(self):
        """Test creating agents config from dictionary."""
        data = {
            "main": {"name": "Architect", "prompt": "path/to/architect.md"},
            "opponents": [
                {"name": "DevLead", "prompt": "path/to/devlead.md"},
                {"name": "QA", "prompt": "path/to/qa.md"}
            ]
        }
        config = SddAgentsConfig.from_dict(data)

        assert config.main.name == "Architect"
        assert config.main.prompt == "path/to/architect.md"
        assert len(config.opponents) == 2
        assert config.opponents[0].name == "DevLead"
        assert config.opponents[1].name == "QA"

    def test_get_all_agents(self):
        """Test getting all agents (main + opponents)."""
        data = {
            "main": {"name": "Architect", "prompt": "architect.md"},
            "opponents": [
                {"name": "DevLead", "prompt": "devlead.md"}
            ]
        }
        config = SddAgentsConfig.from_dict(data)

        all_agents = config.get_all_agents()
        assert len(all_agents) == 2
        assert all_agents[0].name == "Architect"
        assert all_agents[1].name == "DevLead"


class TestSddConfigFile:
    """Test complete SDD configuration file loading."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid SDD config file."""
        config_data = {
            "llm": {
                "model": "gpt-4o-mini",
                "temperature": 0.8,
                "api_key": "${OPENAI_API_KEY:test_key}"
            },
            "debate": {
                "mode": "standard",
                "language": "ru"
            },
            "prompts": {
                "stages": {
                    "opening_pro": "src/prompts/debate/stages/opening_pro.md",
                    "opening_con": "src/prompts/debate/stages/opening_con.md"
                },
                "judge": "src/prompts/debate/judge/verdict.md",
                "context": "src/prompts/debate/context/debate_context.md",
                "roles": {
                    "architect": "src/prompts/sdd/architect.md",
                    "devlead": "src/prompts/sdd/devlead.md",
                    "qa": "src/prompts/sdd/qa.md",
                    "security": "src/prompts/sdd/security.md"
                }
            },
            "agents": {
                "main": {
                    "name": "Architect",
                    "prompt": "src/prompts/sdd/architect.md"
                },
                "opponents": [
                    {"name": "DevLead", "prompt": "src/prompts/sdd/devlead.md"}
                ]
            },
            "output": {
                "directory": "./sdd_output"
            },
            "logging": {
                "level": "INFO"
            }
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = SddConfigFile.from_yaml(config_file)

        assert config.llm.model == "gpt-4o-mini"
        assert config.llm.api_key == "test_key"  # env var substituted
        assert config.debate.mode == "standard"
        assert config.debate.language == "ru"
        assert config.agents.main.name == "Architect"
        assert len(config.agents.opponents) == 1

    def test_missing_required_section(self, tmp_path):
        """Test error when required section is missing."""
        config_data = {
            "llm": {"model": "gpt-4o-mini"},
            # Missing "debate", "prompts", "agents", "output", "logging"
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            SddConfigFile.from_yaml(config_file)

        assert "missing required sections" in str(exc_info.value).lower()

    def test_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            SddConfigFile.from_yaml("nonexistent_config.yaml")

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_yaml(self, tmp_path):
        """Test error when YAML is invalid."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            SddConfigFile.from_yaml(config_file)

    def test_to_dict(self, tmp_path):
        """Test converting config to dictionary."""
        config_data = {
            "llm": {"model": "gpt-4o-mini"},
            "debate": {"mode": "standard"},
            "prompts": {
                "stages": {},
                "judge": "judge.md",
                "context": "context.md",
                "roles": {}
            },
            "agents": {
                "main": {"name": "Architect", "prompt": "architect.md"},
                "opponents": []
            },
            "output": {"directory": "./sdd_output"},
            "logging": {"level": "INFO"}
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = SddConfigFile.from_yaml(config_file)
        config_dict = config.to_dict()

        assert config_dict["llm"]["model"] == "gpt-4o-mini"
        assert config_dict["debate"]["mode"] == "standard"

    def test_get_cli_args_dict(self, tmp_path):
        """Test getting CLI arguments dictionary."""
        config_data = {
            "llm": {"model": "gpt-4o-mini", "temperature": 0.7},
            "debate": {"mode": "standard", "max_retries": 3},
            "prompts": {
                "stages": {},
                "judge": "judge.md",
                "context": "context.md",
                "roles": {}
            },
            "agents": {
                "main": {"name": "Architect", "prompt": "architect.md"},
                "opponents": []
            },
            "output": {"directory": "./sdd_output"},
            "logging": {"level": "INFO"}
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = SddConfigFile.from_yaml(config_file)
        cli_args = config.get_cli_args_dict()

        assert cli_args["model"] == "gpt-4o-mini"
        assert cli_args["temperature"] == 0.7
        assert cli_args["max_retries"] == 3
        assert cli_args["mode"] == "standard"


class TestLoadSddConfig:
    """Test the main load_sdd_config function."""

    def test_load_from_default_location(self, tmp_path):
        """Test loading from default config location."""
        # Create config/sdd_config.yaml
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_data = {
            "llm": {"model": "gpt-4o-mini"},
            "debate": {"mode": "standard"},
            "prompts": {
                "stages": {},
                "judge": "judge.md",
                "context": "context.md",
                "roles": {}
            },
            "agents": {
                "main": {"name": "Architect", "prompt": "architect.md"},
                "opponents": []
            },
            "output": {"directory": "./sdd_output"},
            "logging": {"level": "INFO"}
        }

        config_file = config_dir / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Change to tmp_path and load
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            config = load_sdd_config()
            assert config.llm.model == "gpt-4o-mini"
        finally:
            os.chdir(original_cwd)

    def test_load_from_custom_path(self, tmp_path):
        """Test loading from custom path."""
        config_data = {
            "llm": {"model": "custom-model"},
            "debate": {"mode": "simple"},
            "prompts": {
                "stages": {},
                "judge": "judge.md",
                "context": "context.md",
                "roles": {}
            },
            "agents": {
                "main": {"name": "Architect", "prompt": "architect.md"},
                "opponents": []
            },
            "output": {"directory": "./output"},
            "logging": {"level": "DEBUG"}
        }

        config_file = tmp_path / "custom_sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = load_sdd_config(config_file)
        assert config.llm.model == "custom-model"
        assert config.debate.mode == "simple"

    def test_load_file_not_found(self, tmp_path):
        """Test error when file not found."""
        # Change to tmp_path (empty directory, no config files)
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            # Try to load a non-existent file in empty directory
            with pytest.raises(FileNotFoundError) as exc_info:
                load_sdd_config("nonexistent.yaml")

            assert "SDD configuration file not found" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)


class TestValidationErrors:
    """Test validation error messages."""

    def test_invalid_debate_mode_error_message(self, tmp_path):
        """Test that invalid debate mode produces clear error."""
        config_data = {
            "llm": {"model": "gpt-4o-mini"},
            "debate": {"mode": "invalid_mode"},
            "prompts": {
                "stages": {},
                "judge": "judge.md",
                "context": "context.md",
                "roles": {}
            },
            "agents": {
                "main": {"name": "Architect", "prompt": "architect.md"},
                "opponents": []
            },
            "output": {"directory": "./sdd_output"},
            "logging": {"level": "INFO"}
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            SddConfigFile.from_yaml(config_file)

        error_msg = str(exc_info.value).lower()
        assert "validation failed" in error_msg or "invalid" in error_msg

    def test_missing_sections_error_message(self, tmp_path):
        """Test that missing sections produce clear error."""
        config_data = {
            "llm": {"model": "gpt-4o-mini"},
            # Missing other required sections
        }

        config_file = tmp_path / "sdd_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            SddConfigFile.from_yaml(config_file)

        error_msg = str(exc_info.value)
        assert "missing required sections" in error_msg
        assert "debate" in error_msg
        assert "prompts" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
