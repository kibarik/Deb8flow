"""Tests for PromptLoader service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from shared.debate.application.prompt_loader import (
    PromptLoader,
    PromptContext,
    ValidationResult,
    create_prompt_loader
)
from shared.config.models import PromptsConfig


@pytest.fixture
def temp_prompt_dir(tmp_path):
    """Create temporary prompt directory structure."""
    # Create directories
    (tmp_path / "prompts" / "debate" / "stages").mkdir(parents=True)
    (tmp_path / "prompts" / "debate" / "judge").mkdir(parents=True)
    (tmp_path / "prompts" / "debate" / "context").mkdir(parents=True)
    (tmp_path / "prompts" / "analysis").mkdir(parents=True)

    # Create test prompt files
    (tmp_path / "prompts" / "debate" / "stages" / "opening_pro.md").write_text(
        "Question: {question}\n\nTopic: {topic}"
    )
    (tmp_path / "prompts" / "debate" / "judge" / "verdict.md").write_text(
        "Question: {question}\n\nContext: {recent_context}"
    )
    (tmp_path / "prompts" / "debate" / "context" / "debate_context.md").write_text(
        "Q: {question}\nTopic: {topic}\nPRD: {prd_content}"
    )
    (tmp_path / "prompts" / "analysis" / "takeaway_analysis.md").write_text(
        "Q: {question}\nDialogue: {dialogue_summary}"
    )

    return tmp_path


@pytest.fixture
def prompt_config(temp_prompt_dir):
    """Create test prompt configuration."""
    base = str(temp_prompt_dir / "prompts")

    return PromptsConfig(
        stages={
            "opening_pro": f"{base}/debate/stages/opening_pro.md",
            "opening_con": f"{base}/debate/stages/opening_con.md",
            "rebuttal_pro": f"{base}/debate/stages/rebuttal_pro.md",
            "rebuttal_con": f"{base}/debate/stages/rebuttal_con.md",
            "counter_pro": f"{base}/debate/stages/counter_pro.md",
            "counter_con": f"{base}/debate/stages/counter_con.md",
            "final_pro": f"{base}/debate/stages/final_pro.md",
            "final_con": f"{base}/debate/stages/final_con.md",
        },
        judge=f"{base}/debate/judge/verdict.md",
        context=f"{base}/debate/context/debate_context.md",
        analysis={
            "system": f"{base}/analysis/system_prompt.md",
            "takeaway": f"{base}/analysis/takeaway_analysis.md"
        }
    )


@pytest.fixture
def prompt_loader(prompt_config, temp_prompt_dir):
    """Create PromptLoader instance for testing."""
    return PromptLoader(prompt_config, base_path=temp_prompt_dir)


class TestPromptLoaderInitialization:
    """Test PromptLoader initialization and loading."""

    def test_loads_prompts_on_init(self, prompt_loader):
        """Test that prompts are loaded into cache on initialization."""
        assert len(prompt_loader.get_cached_prompt_ids()) > 0
        assert "debate.stages.opening_pro" in prompt_loader._cache
        assert "debate.judge" in prompt_loader._cache

    def test_missing_file_raises_error(self, temp_prompt_dir):
        """Test that missing prompt files raise FileNotFoundError."""
        config = PromptsConfig(
            stages={},
            judge="nonexistent.md",
            context="context.md",
            analysis={}
        )
        with pytest.raises(FileNotFoundError):
            PromptLoader(config, base_path=temp_prompt_dir)

    def test_empty_file_raises_error(self, temp_prompt_dir):
        """Test that empty prompt files raise ValueError."""
        empty_file = temp_prompt_dir / "prompts" / "empty.md"
        empty_file.write_text("")

        config = PromptsConfig(
            stages={},
            judge=str(empty_file),
            context="context.md",
            analysis={}
        )
        with pytest.raises(ValueError, match="empty"):
            PromptLoader(config, base_path=temp_prompt_dir)


class TestPromptLoading:
    """Test prompt loading methods."""

    def test_load_cached_prompt(self, prompt_loader):
        """Test loading a prompt from cache."""
        prompt = prompt_loader.load("debate.judge")
        assert "Question:" in prompt
        assert "{question}" in prompt

    def test_load_nonexistent_prompt_raises_error(self, prompt_loader):
        """Test loading nonexistent prompt raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            prompt_loader.load("nonexistent.prompt")

    def test_load_with_context(self, prompt_loader):
        """Test loading prompt with context substitution."""
        context = PromptContext(
            question="Should we build this?",
            topic="A new feature",
            recent_context="Previous arguments..."
        )
        rendered = prompt_loader.load_with_context("debate.judge", context)

        assert "Should we build this?" in rendered
        assert "Previous arguments..." in rendered
        assert "{question}" not in rendered  # Variables substituted

    def test_load_with_context_missing_variable_raises_error(self, prompt_loader):
        """Test missing context variable raises ValueError."""
        context = PromptContext(question="Test")
        # Missing 'recent_context'

        with pytest.raises(ValueError, match="Missing required variable"):
            prompt_loader.load_with_context("debate.judge", context)


class TestTemplateRendering:
    """Test template variable rendering."""

    def test_simple_variable_substitution(self, prompt_loader):
        """Test basic variable substitution."""
        context = PromptContext(
            question="Test Question",
            topic="Test Topic",
            prd_content="Test PRD"
        )
        rendered = prompt_loader.load_with_context("debate.context", context)

        assert "Test Question" in rendered
        assert "Test Topic" in rendered
        assert "Test PRD" in rendered

    def test_all_context_variables(self, prompt_loader):
        """Test all PromptContext fields can be used."""
        context = PromptContext(
            question="Q",
            topic="T",
            prd_content="P",
            language="ru",
            recent_context="R",
            pro_prompt="PRO",
            con_prompt="CON",
            dialogue_summary="D",
            verdict_explanation="V",
            winner="PRO",
            min_takeaways=3,
            max_takeaways=10
        )
        # Should not raise any errors
        prompt_loader.load_with_context("debate.context", context)


class TestValidation:
    """Test prompt validation."""

    def test_validate_valid_prompt(self, prompt_loader):
        """Test validating a valid prompt."""
        result = prompt_loader.validate("debate.judge")
        assert result.is_valid
        assert result.prompt_id == "debate.judge"
        assert len(result.errors) == 0

    def test_validate_missing_required_vars(self, temp_prompt_dir):
        """Test validation detects missing required variables."""
        # Create prompt without required variables
        (temp_prompt_dir / "prompts" / "debate" / "stages" / "test.md").write_text(
            "Just some text without variables"
        )

        config = PromptsConfig(
            stages={
                "opening_pro": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                # ... (other stages required for validation)
                "opening_con": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "rebuttal_pro": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "rebuttal_con": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "counter_pro": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "counter_con": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "final_pro": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                "final_con": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
            },
            judge=f"{temp_prompt_dir}/prompts/debate/judge/verdict.md",
            context=f"{temp_prompt_dir}/prompts/debate/context/debate_context.md",
            analysis={}
        )

        loader = PromptLoader(config, base_path=temp_prompt_dir)
        result = loader.validate("debate.stages.opening_pro")

        assert not result.is_valid
        assert len(result.missing_variables) > 0


class TestCaching:
    """Test prompt caching behavior."""

    def test_reload_clears_cache(self, prompt_loader, temp_prompt_dir):
        """Test that reload clears and repopulates cache."""
        original_cache_size = len(prompt_loader.get_cached_prompt_ids())

        # Modify a file
        judge_file = temp_prompt_dir / "prompts" / "debate" / "judge" / "verdict.md"
        original_content = judge_file.read_text()
        judge_file.write_text("Modified content")

        prompt_loader.reload()

        assert "Modified content" in prompt_loader.load("debate.judge")

        # Restore original
        judge_file.write_text(original_content)


class TestPromptContext:
    """Test PromptContext dataclass."""

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all context fields."""
        context = PromptContext(
            question="Q",
            topic="T",
            prd_content="P"
        )
        context_dict = context.to_dict()

        assert "question" in context_dict
        assert "topic" in context_dict
        assert "prd_content" in context_dict
        assert context_dict["question"] == "Q"


class TestFactoryFunction:
    """Test the factory function."""

    def test_create_prompt_loader(self, prompt_config, temp_prompt_dir):
        """Test factory function creates PromptLoader."""
        loader = create_prompt_loader(prompt_config, temp_prompt_dir)
        assert isinstance(loader, PromptLoader)
        assert len(loader.get_cached_prompt_ids()) > 0
