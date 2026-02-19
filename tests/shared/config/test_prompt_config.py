"""Tests for prompt configuration."""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError

from shared.config.models import (
    PromptsConfig,
    DebateModeConfig,
    DebateConfigFull,
    PromptPathsConfig
)


class TestPromptsConfig:
    """Test prompt configuration validation."""

    def test_valid_prompts_config(self):
        """Test loading valid prompts configuration."""
        config = {
            "stages": {
                "opening_pro": "src/prompts/debate/stages/opening_pro.md",
                "opening_con": "src/prompts/debate/stages/opening_con.md",
                "rebuttal_pro": "src/prompts/debate/stages/rebuttal_pro.md",
                "rebuttal_con": "src/prompts/debate/stages/rebuttal_con.md",
                "counter_pro": "src/prompts/debate/stages/counter_pro.md",
                "counter_con": "src/prompts/debate/stages/counter_con.md",
                "final_pro": "src/prompts/debate/stages/final_pro.md",
                "final_con": "src/prompts/debate/stages/final_con.md"
            },
            "judge": "src/prompts/debate/judge/verdict.md",
            "context": "src/prompts/debate/context/debate_context.md",
            "analysis": {
                "system": "src/prompts/analysis/system_prompt.md",
                "takeaway": "src/prompts/analysis/takeaway_analysis.md"
            }
        }
        prompts_config = PromptsConfig(**config)
        assert prompts_config.judge == "src/prompts/debate/judge/verdict.md"
        assert len(prompts_config.stages) == 8

    def test_missing_required_stages(self):
        """Test that missing stages raise validation error."""
        config = {
            "stages": {
                "opening_pro": "src/prompts/debate/stages/opening_pro.md"
            },
            "judge": "src/prompts/debate/judge/verdict.md",
            "context": "src/prompts/debate/context/debate_context.md"
        }
        with pytest.raises(ValidationError) as exc_info:
            PromptsConfig(**config)
        assert "Missing required stage prompts" in str(exc_info.value)

    def test_empty_judge_path_raises_error(self):
        """Test that empty judge path raises error."""
        config = {
            "stages": {
                "opening_pro": "src/prompts/debate/stages/opening_pro.md"
            },
            "judge": "",
            "context": "src/prompts/debate/context/debate_context.md"
        }
        with pytest.raises(ValidationError):
            PromptsConfig(**config)


class TestDebateModeConfig:
    """Test debate mode configuration validation."""

    def test_valid_standard_mode(self):
        """Test standard mode is valid."""
        config = DebateModeConfig(mode="standard")
        assert config.mode == "standard"

    def test_valid_simple_mode(self):
        """Test simple mode is valid."""
        config = DebateModeConfig(mode="simple")
        assert config.mode == "simple"

    def test_invalid_mode_raises_error(self):
        """Test invalid mode raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DebateModeConfig(mode="invalid")
        assert "Invalid debate mode" in str(exc_info.value)

    def test_default_mode_is_standard(self):
        """Test default mode is standard."""
        config = DebateModeConfig()
        assert config.mode == "standard"


class TestConfigLoading:
    """Test loading full configuration from file."""

    def test_load_debate_config_yaml(self):
        """Test loading config from YAML file."""
        config_path = Path("config/debate_config.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config_dict = yaml.safe_load(f)

        # Should have prompts section
        assert "prompts" in config_dict
        assert "stages" in config_dict["prompts"]
        assert "judge" in config_dict["prompts"]

        # Should have debate mode
        assert "debate" in config_dict
        assert "mode" in config_dict["debate"]

        # Validate with Pydantic
        config = DebateConfigFull(**config_dict)
        assert config.prompts.judge
        assert config.debate.mode in ["standard", "simple"]

    def test_prompts_config_required_stages(self):
        """Test that prompts config validates required stages."""
        config = {
            "stages": {
                "opening_pro": "src/prompts/debate/stages/opening_pro.md",
                "opening_con": "src/prompts/debate/stages/opening_con.md",
                "rebuttal_pro": "src/prompts/debate/stages/rebuttal_pro.md",
                "rebuttal_con": "src/prompts/debate/stages/rebuttal_con.md",
                "counter_pro": "src/prompts/debate/stages/counter_pro.md",
                "counter_con": "src/prompts/debate/stages/counter_con.md",
                "final_pro": "src/prompts/debate/stages/final_pro.md",
                "final_con": "src/prompts/debate/stages/final_con.md"
            },
            "judge": "src/prompts/debate/judge/verdict.md",
            "context": "src/prompts/debate/context/debate_context.md",
            "analysis": {
                "system": "src/prompts/analysis/system_prompt.md",
                "takeaway": "src/prompts/analysis/takeaway_analysis.md"
            }
        }

        prompts_config = PromptPathsConfig(**config)
        assert prompts_config.judge == "src/prompts/debate/judge/verdict.md"
        assert len(prompts_config.stages) == 8
