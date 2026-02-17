"""
Unit tests for EnhancedConclusionWriter.

Tests verify:
- Markdown formatting of enhanced conclusion
- UTF-8 encoding support
- Empty list handling
- Evidence reference formatting
"""

import pytest
from pathlib import Path
import tempfile

from src.writers.enhanced_conclusion_writer import EnhancedConclusionWriter
from src.types.enhanced_conclusion_types import (
    EnhancedConclusion,
    Verdict,
    RoleAnalysis,
    EvidenceReference,
    CriticalGap,
    Recommendation,
)


@pytest.fixture
def writer():
    """Create EnhancedConclusionWriter instance."""
    return EnhancedConclusionWriter()


@pytest.fixture
def sample_conclusion():
    """Sample enhanced conclusion for testing."""
    # Create a valid Verdict with 120-150 words
    answer_words = " ".join(["word"] * 130)

    verdict = Verdict(
        answer=answer_words,
        confidence="Medium",
        rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning.",
        room_outcomes="PRO won 3/4 rooms"
    )

    role_analyses = [
        RoleAnalysis(
            role_name="CFO",
            strengths=[],
            weaknesses=[
                {
                    "description": "Financial model lacks conservative scenarios and needs more detailed analysis of implementation costs.",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="The financial model is overly optimistic with no downside analysis."
                    )
                }
            ]
        )
    ]

    gaps = [
        CriticalGap(
            title="Incomplete Financial Analysis",
            severity="High",
            description="The financial model lacks conservative scenarios and detailed implementation costs.",
            sources=["CFO"],
            evidence=[
                EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=2,
                    quote="The financial model is overly optimistic."
                )
            ]
        )
    ]

    recommendations = [
        Recommendation(
            priority="High",
            problem="The PRD lacks a comprehensive financial analysis with conservative scenarios",
            action="Add a detailed Financial Analysis section to the PRD with multiple scenarios",
            metric="PRD includes complete financial analysis with ROI projections",
            source_evidence=EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=2,
                quote="The financial model is overly optimistic."
            )
        )
    ]

    return EnhancedConclusion(
        verdict=verdict,
        role_analyses=role_analyses,
        critical_gaps=gaps,
        recommendations=recommendations
    )


class TestEnhancedConclusionWriter:
    """Test EnhancedConclusionWriter functionality."""

    def test_format_to_string(self, writer, sample_conclusion):
        """Test formatting conclusion to markdown string."""
        markdown = writer.format_to_string(sample_conclusion)

        assert "# Enhanced Committee Conclusion Report" in markdown
        assert "## Verdict" in markdown
        assert "## Role-Based Analysis" in markdown
        assert "## Critical Gaps" in markdown
        assert "## Recommendations" in markdown

    def test_write_to_file(self, writer, sample_conclusion):
        """Test writing conclusion to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)

            result = writer.write(sample_conclusion, output_path)

            assert result.exists()
            assert result.name == "enhanced_conclusion.md"

            # Verify content
            content = result.read_text(encoding="utf-8")
            assert "# Enhanced Committee Conclusion Report" in content

    def test_write_with_run_id(self, writer, sample_conclusion):
        """Test writing conclusion with run ID in filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)

            result = writer.write(sample_conclusion, output_path, run_id="RUN_123")

            assert result.name == "enhanced_conclusion_RUN_123.md"

    def test_utf8_encoding_support(self, writer):
        """Test UTF-8 encoding support for Russian text."""
        # Create conclusion with Russian text
        answer_words = " ".join(["word"] * 130)
        verdict = Verdict(
            answer=answer_words,
            confidence="High",
            rationale="Комитет достиг единогласного решения. Технические и бизнес аргументы были убедительными.",
            room_outcomes="PRO won 4/4 rooms"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        # Format and verify Russian text is preserved
        markdown = writer.format_to_string(conclusion)
        assert "Технические и бизнес аргументы были убедительными" in markdown

    def test_empty_lists_handled(self, writer):
        """Test handling of empty lists."""
        answer_words = " ".join(["word"] * 130)
        verdict = Verdict(
            answer=answer_words,
            confidence="High",
            rationale="Test rationale that is long enough to meet validation requirements.",
            room_outcomes="PRO won 4/4 rooms"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        markdown = writer.format_to_string(conclusion)

        # Should have "None" or "No ... identified" for empty sections
        assert "No critical gaps identified" in markdown
        assert "No recommendations generated" in markdown

    def test_evidence_references_formatted(self, writer, sample_conclusion):
        """Test evidence references are formatted correctly."""
        markdown = writer.format_to_string(sample_conclusion)

        # Should include room_id, speaker_role, turn_index
        assert "TPM_vs_CFO" in markdown
        assert "CFO" in markdown
        assert "Turn 2" in markdown
