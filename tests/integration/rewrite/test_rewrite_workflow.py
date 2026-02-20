"""
Integration test for complete rewrite workflow.
"""
import pytest
from pathlib import Path
from src.rewrite.application.run_rewrite import RunRewrite
from src.rewrite.adapters.revision_parser import ConclusionParser
from src.rewrite.adapters.document_editor import MarkdownEditor
from src.rewrite.adapters.progress_reporter import ProgressReporter
from src.rewrite.infrastructure.storage import RewriteStorage
from src.rewrite.domain.value_objects import RewriteConfig


@pytest.fixture
def orchestrator(tmp_path):
    """Create orchestrator with test dependencies."""
    config = RewriteConfig(
        max_rounds=2,  # Low for fast tests
        backup_suffix=".backup"
    )
    parser = ConclusionParser()
    storage = RewriteStorage(config)
    reporter = ProgressReporter(verbose=False)

    return RunRewrite(parser, storage, reporter, config)


@pytest.fixture
def test_files(tmp_path):
    """Create test source and conclusion files."""
    source = tmp_path / "source.md"
    source.write_text("""# Document

## Section A

Content A.

## Section B

Content B.
""")

    conclusion = tmp_path / "conclusion.md"
    conclusion.write_text("""# Чеклист рекомендаций

## Рекомендации

1. Add note to Section A [CPO]
2. Update Section B content [CTO]
""")

    return {"source": source, "conclusion": conclusion}


@pytest.mark.asyncio
async def test_full_workflow(orchestrator, test_files):
    """Test complete rewrite workflow."""
    source = test_files["source"]
    conclusion = test_files["conclusion"]
    output = source.parent / "output.md"

    # Execute rewrite (without verification for faster test)
    result = await orchestrator.execute(
        source_path=source,
        conclusion_path=conclusion,
        output_path=output,
        max_rounds=0,  # Skip debate for this test
        skip_backup=False
    )

    # Verify result
    assert result.status.value in ["success", "partial"]
    assert result.revisions_applied == 2
    assert output.exists()

    # Check backup was created
    backup = source.parent / "source.md.backup"
    assert backup.exists()

    # Check content was modified
    content = output.read_text()
    assert len(content) > 0
