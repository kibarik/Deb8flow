"""Integration tests for orchestrator workflow (WP01 components only)."""

from pathlib import Path
import pytest

from src.orchestrator.domain.models import (
    OrchestratorConfig,
    ArtifactMetadata,
)


@pytest.fixture
def config(tmp_path):
    return OrchestratorConfig(
        log_dir=str(tmp_path / ".orchestrator" / "logs"),
        docker_image="test-image:latest",
    )


class TestArtifactParsing:
    def test_parse_spec_metadata(self):
        spec_path = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/spec.md")
        metadata = ArtifactMetadata.from_markdown(spec_path)
        assert metadata.artifact_type == "spec"
        assert "mission" in metadata.frontmatter

    def test_parse_incomplete_artifact(self, tmp_path):
        spec_file = tmp_path / "incomplete.md"
        spec_file.write_text("---\nfeature_number: \"021\"\n---\n\n[NEEDS CLARIFICATION]")
        metadata = ArtifactMetadata.from_markdown(spec_file)
        assert metadata.is_complete is False


class TestConfigurationLoading:
    def test_load_config_with_defaults(self, tmp_path):
        from src.orchestrator.adapters.config_loader import load_orchestrator_config
        config_path = tmp_path / "config.yaml"
        config_path.write_text("# Empty\n")
        config = load_orchestrator_config(config_path)
        assert config.max_retries == 3


class TestSampleFiles:
    def test_sample_source_exists(self):
        source = Path("tests/orchestrator/fixtures/sample_source.md")
        assert source.exists()

    def test_mock_artifacts_exist(self):
        spec = Path("tests/orchestrator/fixtures/mock_spec_kitty_artifacts/spec.md")
        assert spec.exists()
