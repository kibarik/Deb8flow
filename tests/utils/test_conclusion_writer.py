"""Unit tests for ConclusionWriter.

Tests markdown formatting and file writing functionality.
"""

import unittest
import tempfile
from pathlib import Path

from src.utils.conclusion_writer import ConclusionWriter
from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
    DebateType,
)


class TestConclusionWriter(unittest.TestCase):
    """Test cases for ConclusionWriter."""

    def setUp(self):
        """Set up test writer."""
        self.writer = ConclusionWriter()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test output directory."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_write_basic_conclusion_report(self):
        """Test writing basic conclusion report."""
        conclusion_data = ConclusionData(
            debate_question="Should we invest in AI?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="PRO presented stronger ROI projections",
                confidence=None,
            ),
            qa_summary=[
                QAPair(
                    question="What is the ROI timeline?",
                    answer="18 months with proper testing",
                    stage="rebuttal",
                    speaker="CON",
                    validated=True,
                    priority=1,
                )
            ],
            tpm_analysis=TPMAnalysis(
                position_summary="TPM argues for 18-month timeline",
                weaknesses=[],
                recommended_improvements=["Add historical velocity data"],
                victory_assessment="won",
            ),
            recommendations=[
                Recommendation(
                    agent_role="CFO",
                    text="От CFO: Validate ROI calculations with historical data",
                    priority="high",
                    category="planning",
                    actionable=True,
                )
            ],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="standard-20250215-test123",
                generated_at="2025-02-15T12:34:56Z",
                source_file=None,
                total_recommendations=1,
                tpm_victory=True,
                completion_status="success",
                error_message=None,
            ),
        )

        output_path = self.writer.write(
            output_path=self.output_dir,
            conclusion_data=conclusion_data,
        )

        # Verify file was created
        self.assertTrue(Path(output_path).exists())

    def test_format_conclusion_report_with_all_sections(self):
        """Test formatting with all report sections."""
        conclusion_data = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="CON",
                winner_position="CON",
                justification="CON demonstrated stronger market understanding",
                confidence=0.75,
            ),
            qa_summary=[
                QAPair(
                    question="Key question 1",
                    answer="Key answer 1",
                    stage="opening",
                    speaker="PRO",
                    validated=True,
                    priority=1,
                ),
                QAPair(
                    question="Key question 2",
                    answer="Key answer 2",
                    stage="rebuttal",
                    speaker="CON",
                    validated=False,
                    priority=2,
                ),
            ],
            tpm_analysis=TPMAnalysis(
                position_summary="TPM position summary",
                weaknesses=[
                    TPMWeakness(
                        category="unjustified_assumption",
                        description="Assumes doubling of team velocity",
                        severity="high",
                        source="CFO",
                        context="No historical data provided",
                    )
                ],
                recommended_improvements=["Improvement 1", "Improvement 2"],
                victory_assessment="lost",
            ),
            recommendations=[
                Recommendation(
                    agent_role="TPM",
                    text="Recommendation text",
                    priority="medium",
                    category="improvement",
                    actionable=True,
                ),
                Recommendation(
                    agent_role="CPO",
                    text="Another recommendation",
                    priority="low",
                    category=None,
                    actionable=False,
                ),
            ],
            metadata=ConclusionMetadata(
                debate_type=DebateType.DOCUMENT.value,
                run_id="doc-20250215-test456",
                generated_at="2025-02-15T12:34:56Z",
                source_file="/path/to/document.docx",
                total_recommendations=2,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )

        markdown = self.writer._format_conclusion_report(conclusion_data)

        # Verify key sections are present
        self.assertIn("# Debate Conclusion Report", markdown)
        self.assertIn("## Debate Question", markdown)
        self.assertIn("## Judge's Verdict", markdown)
        self.assertIn("## Key Question-Answer Pairs", markdown)
        self.assertIn("## TPM Position Analysis", markdown)
        self.assertIn("## Recommendations", markdown)
        self.assertIn("## Metadata", markdown)

    def test_write_with_no_recommendations_placeholder(self):
        """Test writing with 'Нет рекомендаций' placeholder."""
        conclusion_data = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Test justification",
            ),
            qa_summary=[],
            tpm_analysis=TPMAnalysis(
                position_summary="No position",
                weaknesses=[],
                recommended_improvements=[],
                victory_assessment="unclear",
            ),
            recommendations=[],  # Empty recommendations
            metadata=ConclusionMetadata(
                debate_type=DebateType.COMMITTEE.value,
                run_id="test-123",
                generated_at="2025-02-15T12:34:56Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )

        output_path = self.writer.write(
            output_path=self.output_dir,
            conclusion_data=conclusion_data,
        )

        # Verify placeholder is included
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("*Нет рекомендаций*", content)

    def test_escape_markdown(self):
        """Test markdown escaping functionality."""
        test_text = "Text with *bold* and _italic_ markers"
        escaped = self.writer.escape_markdown(test_text)

        self.assertEqual(escaped, r"Text with \*bold\* and _italic_ markers")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        self.assertEqual(self.writer.sanitize_filename("normal.txt"), "normal.txt")
        self.assertEqual(self.writer.sanitize_filename("file with spaces.txt"), "file_with_spaces.txt")
        self.assertEqual(self.writer.sanitize_filename("file/with/slashes.txt"), "file_with_slashes.txt")
        self.assertEqual(self.writer.sanitize_filename("file<>with<>bad.txt"), "file_with_bad_chars.txt")

    def test_write_with_invalid_output_directory(self):
        """Test error handling for invalid output directory."""
        conclusion_data = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(winner="PRO", winner_position="PRO", justification="Test"),
            qa_summary=[],
            tpm_analysis=TPMAnalysis(position_summary="", weaknesses=[], recommended_improvements=[], victory_assessment="unclear"),
            recommendations=[],
            metadata=ConclusionMetadata(debate_type="standard", run_id="test", generated_at="2025-02-15T12:34:56Z", source_file=None, total_recommendations=0, tpm_victory=False, completion_status="success", error_message=None),
        )

        with self.assertRaises(ValueError):
            self.writer.write(
                output_path="/nonexistent/directory/path",
                conclusion_data=conclusion_data,
            )


class TestConclusionWriterEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test writer."""
        self.writer = ConclusionWriter()

    def test_format_with_empty_qa_summary(self):
        """Test formatting with empty Q&A summary."""
        conclusion_data = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(winner="PRO", winner_position="PRO", justification="Test"),
            qa_summary=[],  # Empty
            tpm_analysis=TPMAnalysis(position_summary="", weaknesses=[], recommended_improvements=[], victory_assessment="unclear"),
            recommendations=[],
            metadata=ConclusionMetadata(debate_type="standard", run_id="test", generated_at="2025-02-15T12:34:56Z", source_file=None, total_recommendations=0, tpm_victory=False, completion_status="success", error_message=None),
        )

        markdown = self.writer._format_conclusion_report(conclusion_data)

        # Should not crash with empty Q&A
        self.assertIn("## Key Question-Answer Pairs", markdown)

    def test_format_with_no_tpm_analysis(self):
        """Test formatting with missing TPM analysis."""
        conclusion_data = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(winner="PRO", winner_position="PRO", justification="Test"),
            qa_summary=[
                QAPair(
                    question="Q?",
                    answer="A",
                    stage="opening",
                    speaker="PRO",
                    validated=True,
                    priority=1,
                )
            ],
            tpm_analysis={},  # Missing
            recommendations=[
                Recommendation(
                    agent_role="TPM",
                    text="Recommendation",
                    priority="high",
                    category="improvement",
                    actionable=True,
                )
            ],
            metadata=ConclusionMetadata(debate_type="standard", run_id="test", generated_at="2025-02-15T12:34:56Z", source_file=None, total_recommendations=1, tpm_victory=False, completion_status="success", error_message=None),
        )

        markdown = self.writer._format_conclusion_report(conclusion_data)

        # Should handle missing TPM analysis gracefully
        self.assertIn("## Recommendations", markdown)


if __name__ == "__main__":
    unittest.main()
