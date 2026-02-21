"""Integration tests for orchestrator workflow.

These tests validate integration between components from completed work packages.
Currently tests WP01 (Configuration) components only.

As more WPs complete, additional integration tests will be added.
"""

from pathlib import Path
import pytest

from src.orchestrator.domain.models import (
    OrchestratorConfig,
    ResultStatus,
    ArtifactMetadata,
    OverwriteOutputMode,
    PhaseName,
)


@pytest.fixture
def config(tmp_path):
    """Create test configuration."""
    return OrchestratorConfig(
        log_dir=str(tmp_path / ".orchestrator" / "logs"),
        docker_image="test-image:latest",
        container_timeout=60,
        max_retries=2,
        verbose=False,
    )


class TestArtifactParsing:
    """Tests for Spec-Kitty artifact parsing."""

    def test_parse_spec_metadata(self):
        """Test parsing spec.md metadata."""
        spec_path = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/spec.md")
        metadata = ArtifactMetadata.from_markdown(spec_path)

        assert metadata.artifact_type == "spec"
        assert "mission" in metadata.frontmatter

    def test_parse_incomplete_artifact(self, tmp_path):
        """Test detection of incomplete artifact."""
        spec_file = tmp_path / "incomplete.md"
        spec_file.write_text("---\nfeature_number: \"021\"\n---\n\n## Overview\n[NEEDS CLARIFICATION]")

        metadata = ArtifactMetadata.from_markdown(spec_file)
        assert metadata.is_complete is False


class TestConfigurationLoading:
    """Tests for configuration loading."""

    def test_load_config_with_defaults(self, tmp_path):
        """Test loading config without orchestrator section."""
        from src.orchestrator.adapters.config_loader import load_orchestrator_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("# Empty config\n")
        config = load_orchestrator_config(config_path)

        assert config.max_retries == 3
        assert config.docker_image == "claude-code:latest"

    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config raises validation error."""
        from src.orchestrator.adapters.config_loader import ConfigValidationError, load_orchestrator_config

        config_path = tmp_path / "config.yaml"
        config_path.write_text("orchestrator:\n  max_retries: -1\n")

        with pytest.raises(ConfigValidationError):
            load_orchestrator_config(config_path)


class TestSampleFiles:
    """Tests for sample fixture files."""

    def test_sample_source_exists(self):
        """Test that sample source file exists."""
        source = Path("tests/orchestrator/fixtures/sample_source.md")
        assert source.exists()

    def test_mock_artifacts_exist(self):
        """Test that mock Spec-Kitty artifacts exist."""
        spec = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/spec.md")
        plan = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/plan.md")
        tasks = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/tasks.md")

        assert spec.exists()
        assert plan.exists()
        assert tasks.exists()
