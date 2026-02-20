"""
Unit tests for progress reporter.
"""
import pytest
from io import StringIO
import logging
from pathlib import Path
from src.rewrite.adapters.progress_reporter import ProgressReporter
from src.rewrite.domain.entities import RewriteResult, RevisionItem
from src.rewrite.domain.value_objects import RewriteStatus
from src.rewrite.domain.value_objects import RevisionAction


@pytest.fixture
def reporter():
    """Create reporter instance."""
    return ProgressReporter(verbose=True)


@pytest.fixture
def sample_revision():
    """Create sample revision."""
    return RevisionItem(
        id="R001",
        content="Add error handling",
        section="CPO",
        action=RevisionAction.UPDATE
    )


class TestProgressReporter:
    """Test suite for ProgressReporter."""

    def test_prefixes(self, reporter):
        """Test log prefixes are correct."""
        assert reporter.PREFIX_REWRITE == "[REWRITE]"
        assert reporter.PREFIX_DEBATE == "[DEBATE]"
        assert reporter.PREFIX_JUDGE == "[JUDGE]"

    def test_report_reading_files(self, reporter, caplog):
        """Test file reading report."""
        with caplog.at_level(logging.INFO):
            reporter.report_reading_files(
                Path("test.md"),
                Path("conclusion.md")
            )

        assert "[REWRITE]" in caplog.text
        assert "Reading source file" in caplog.text

    def test_report_revisions_found(self, reporter, caplog):
        """Test revisions found report."""
        with caplog.at_level(logging.INFO):
            reporter.report_revisions_found(5)

        assert "Found 5 revision" in caplog.text

    def test_report_debate_round(self, reporter, caplog):
        """Test debate round report."""
        with caplog.at_level(logging.INFO):
            reporter.report_debate_starting(2, 5)

        assert "[DEBATE]" in caplog.text
        assert "round 2/5" in caplog.text

    def test_report_success_result(self, reporter, caplog):
        """Test success result report."""
        result = RewriteResult(
            status=RewriteStatus.SUCCESS,
            revisions_applied=5,
            revisions_verified=5,
            revisions_total=5,
            unverified=(),
            rounds_completed=2,
            backup_path=Path("test.md.backup"),
            source_path=Path("test.md"),
            output_path=Path("test.md")
        )

        with caplog.at_level(logging.INFO):
            reporter.report_result(result)

        assert "Complete" in caplog.text
        assert "All 5" in caplog.text

    def test_report_partial_result(self, reporter, caplog):
        """Test partial result report."""
        revision = RevisionItem(
            id="R001", content="Unverified", section="X",
            action=RevisionAction.UPDATE
        )
        result = RewriteResult(
            status=RewriteStatus.PARTIAL,
            revisions_applied=5,
            revisions_verified=3,
            revisions_total=5,
            unverified=(revision,),
            rounds_completed=5,
            backup_path=Path("test.md.backup"),
            source_path=Path("test.md"),
            output_path=Path("test.md")
        )

        with caplog.at_level(logging.INFO):
            reporter.report_result(result)

        assert "Partial" in caplog.text
        assert "3/5" in caplog.text
        assert "Recommendations" in caplog.text
