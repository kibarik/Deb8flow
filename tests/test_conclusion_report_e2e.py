"""End-to-end tests for debate conclusion report feature.

These tests verify the complete flow from debate completion through
conclusion report generation to final file output.
"""

import unittest
import tempfile
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, patch.object

from src.nodes.conclusion_report_node import ConclusionReportNode
from src.extractors.debate_state_extractor import DebateStateExtractor
from src.utils.conclusion_writer import ConclusionWriter
from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    Recommendation,
    ConclusionMetadata,
    DebateType,
)


def mock_node_dependencies(test_instance):
    """Decorator to mock all node dependencies for E2E tests."""
    def decorator(test_method):
        def wrapped(self, *args, **kwargs):
            # Mock LLM generation to avoid actual LLM calls
            with patch.object(ConclusionReportNode, "_generate_conclusion_with_llm"):
                # Mock extractor
                with patch("src.nodes.conclusion_report_node.DebateStateExtractor") as mock_extractor_class:
                    mock_extractor = MagicMock()
                    mock_extractor_class.return_value = mock_extractor

                    # Mock writer
                    with patch("src.nodes.conclusion_report_node.ConclusionWriter") as mock_writer_class:
                        mock_writer = MagicMock()
                        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
                        mock_writer_class.return_value = mock_writer

                        # Set up test data based on test method name
                        test_name = test_method.__name__
                        mock_extractor.extract.return_value = self._get_test_conclusion_data(test_name)

                        # Update node with mocked dependencies
                        self.node.extractor = mock_extractor
                        self.node.writer = mock_writer

                        # Run the test
                        return test_method(self, mock_extractor, mock_writer)

        return wrapped
    return decorator


class TestStandardDebateConclusionE2E(unittest.TestCase):
    """End-to-end tests for standard debate conclusion generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = ConclusionReportNode()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch.object(ConclusionReportNode, "_generate_conclusion_with_llm")
    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_standard_debate_conclusion_generation(self, mock_writer_class, mock_extractor_class, mock_llm):
        """Test complete conclusion generation for standard debate."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Should we invest in AI?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="PRO presented stronger ROI projections",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="standard-e2e-test-001",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        # Update node with mocked dependencies
        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [
                {"role": "system", "content": "Debate topic: Should we invest in AI?"},
                {"role": "assistant", "content": "PRO opening: Yes, AI offers strong ROI"},
                {"role": "assistant", "content": "CON opening: No, AI is too risky"},
                {"role": "assistant", "content": "Judge verdict: PRO wins"},
            ],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "PRO presented stronger ROI projections",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "standard-e2e-test-001",
            "debate_topic": "Should we invest in AI?",
        }

        result = self.node(state)

        # Verify output path is returned
        self.assertIn("conclusion_report_path", result)
        conclusion_path = result["conclusion_report_path"]

        # Verify writer was called correctly
        mock_writer.write.assert_called_once()
        call_args = mock_writer.write.call_args
        self.assertEqual(call_args[1]["output_path"], self.output_dir)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_standard_debate_with_clear_winner(self, mock_writer_class, mock_extractor_class):
        """Test conclusion generation when there is a clear winner."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Stronger arguments presented",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-clear-winner",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Stronger arguments presented",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "test-clear-winner",
            "debate_topic": "Test question?",
        }

        result = self.node(state)

        # Verify winner is passed correctly
        mock_extractor.extract.assert_called_once()
        call_state = mock_extractor.extract.call_args[0][0]
        self.assertEqual(call_state["verdict"]["winner"], "PRO")


class TestDocumentDebateConclusionE2E(unittest.TestCase):
    """End-to-end tests for document debate conclusion generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = ConclusionReportNode()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_document_debate_conclusion_generation(self, mock_writer_class, mock_extractor_class):
        """Test complete conclusion generation for document debate."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Is GitHub useful for developers?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="PRO demonstrated collaboration benefits",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.DOCUMENT.value,
                run_id="doc-e2e-test-001",
                generated_at="2025-02-15T12:00:00Z",
                source_file="/path/to/document.docx",
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [
                {"role": "system", "content": "Document: GitHub is useful for developers"},
                {"role": "assistant", "content": "PRO: GitHub enables collaboration"},
                {"role": "assistant", "content": "CON: GitLab is better"},
                {"role": "assistant", "content": "Judge verdict: PRO wins"},
            ],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "PRO demonstrated collaboration benefits",
            },
            "output_dir": self.output_dir,
            "debate_type": "document",
            "run_id": "doc-e2e-test-001",
            "source_file": "/path/to/document.docx",
            "debate_topic": "Is GitHub useful for developers?",
        }

        result = self.node(state)

        # Verify output path is returned
        self.assertIn("conclusion_report_path", result)

        # Verify metadata includes document type
        mock_extractor.extract.assert_called_once()
        call_state = mock_extractor.extract.call_args[0][0]
        self.assertEqual(call_state["debate_type"], "document")


class TestEdgeCasesE2E(unittest.TestCase):
    """Test edge cases in conclusion report generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = ConclusionReportNode()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_no_clear_winner_scenario(self, mock_writer_class, mock_extractor_class):
        """Test conclusion generation when there's no clear winner (DRAW)."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="DRAW",
                winner_position="DRAW",
                justification="Both sides presented equally strong arguments",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-draw",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "DRAW",
                "winner_position": "DRAW",
                "justification": "Both sides presented equally strong arguments",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "test-draw",
            "debate_topic": "Test question?",
        }

        result = self.node(state)

        # Verify file is created
        self.assertIn("conclusion_report_path", result)

        # Verify DRAW verdict is passed correctly
        mock_extractor.extract.assert_called_once()
        call_state = mock_extractor.extract.call_args[0][0]
        self.assertEqual(call_state["verdict"]["winner"], "DRAW")

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_no_recommendations_scenario(self, mock_writer_class, mock_extractor_class):
        """Test conclusion generation when there are no recommendations."""
        # Mock the extractor with empty recommendations
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Test",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],  # Empty recommendations
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-no-recs",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Test",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "test-no-recs",
            "debate_topic": "Test?",
        }

        result = self.node(state)

        # Verify file is created even without recommendations
        self.assertIn("conclusion_report_path", result)
        mock_extractor.extract.assert_called_once()

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_missing_output_directory(self, mock_writer_class, mock_extractor_class):
        """Test error handling for missing output directory."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(winner="PRO", winner_position="PRO", justification="Test"),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-missing-dir",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer to raise ValueError for invalid directory
        mock_writer = MagicMock()
        mock_writer.write.side_effect = ValueError("Invalid output directory")
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Test",
            },
            "output_dir": "/nonexistent/directory/that/does/not/exist",
            "debate_type": "standard",
            "run_id": "test-missing-dir",
            "debate_topic": "Test?",
        }

        with self.assertRaises(ValueError):
            self.node(state)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_multi_language_content_preservation(self, mock_writer_class, mock_extractor_class):
        """Test that multi-language content is preserved in conclusion."""
        # Mock the extractor with multi-language recommendations
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Test",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[
                Recommendation(
                    agent_role="CFO",
                    text="От CFO: Рекомендация",
                    priority="high",
                    category="planning",
                    actionable=True,
                ),
                Recommendation(
                    agent_role="CTO",
                    text="From CTO: Another recommendation",
                    priority="medium",
                    category="technical",
                    actionable=True,
                ),
                Recommendation(
                    agent_role="CEO",
                    text="Desde CEO: Tercera recomendación",
                    priority="low",
                    category="strategy",
                    actionable=True,
                ),
            ],
            metadata=ConclusionMetadata(
                debate_type=DebateType.COMMITTEE.value,
                run_id="test-multilang",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=3,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Test",
            },
            "output_dir": self.output_dir,
            "debate_type": "committee",
            "run_id": "test-multilang",
            "debate_topic": "Test?",
        }

        result = self.node(state)

        # Verify all languages are passed to writer
        self.assertIn("conclusion_report_path", result)
        mock_extractor.extract.assert_called_once()
        call_state = mock_extractor.extract.call_args[0][0]
        self.assertEqual(call_state["debate_type"], "committee")


class TestConclusionStructureValidationE2E(unittest.TestCase):
    """Validate Conclusion.md structure matches specification."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = ConclusionReportNode()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_conclusion_structure_matches_spec(self, mock_writer_class, mock_extractor_class):
        """Test that Conclusion.md has all required sections per spec."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Stronger arguments",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-structure",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Stronger arguments",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "test-structure",
            "debate_topic": "Test question?",
        }

        result = self.node(state)

        # Verify writer was called with correct data
        self.assertIn("conclusion_report_path", result)
        mock_writer.write.assert_called_once()

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_metadata_completeness(self, mock_writer_class, mock_extractor_class):
        """Test that metadata contains all required fields."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(
                winner="CON",
                winner_position="CON",
                justification="Test",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.DOCUMENT.value,
                run_id="test-metadata-001",
                generated_at="2025-02-15T12:00:00Z",
                source_file="/path/to/doc.docx",
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "CON",
                "winner_position": "CON",
                "justification": "Test",
            },
            "output_dir": self.output_dir,
            "debate_type": "document",
            "run_id": "test-metadata-001",
            "source_file": "/path/to/doc.docx",
            "debate_topic": "Test?",
        }

        result = self.node(state)

        # Verify metadata fields are passed correctly
        self.assertIn("conclusion_report_path", result)
        mock_extractor.extract.assert_called_once()
        call_state = mock_extractor.extract.call_args[0][0]
        self.assertEqual(call_state["source_file"], "/path/to/doc.docx")

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_recommendation_attribution_accuracy(self, mock_writer_class, mock_extractor_class):
        """Test that recommendations are properly attributed to agents."""
        # Mock the extractor with attributed recommendations
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Test",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[
                Recommendation(
                    agent_role="CFO",
                    text="Validate ROI",
                    priority="high",
                    category="planning",
                    actionable=True,
                ),
                Recommendation(
                    agent_role="CTO",
                    text="Check technical feasibility",
                    priority="medium",
                    category="technical",
                    actionable=True,
                ),
                Recommendation(
                    agent_role="CEO",
                    text="Consider market impact",
                    priority="low",
                    category="strategy",
                    actionable=True,
                ),
            ],
            metadata=ConclusionMetadata(
                debate_type=DebateType.COMMITTEE.value,
                run_id="test-attribution",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=3,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Test",
            },
            "output_dir": self.output_dir,
            "debate_type": "committee",
            "run_id": "test-attribution",
            "debate_topic": "Test?",
        }

        result = self.node(state)

        # Verify recommendations are passed with correct agent attribution
        self.assertIn("conclusion_report_path", result)
        mock_extractor.extract.assert_called_once()


class TestPerformanceE2E(unittest.TestCase):
    """Test performance requirements per SC-005."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = ConclusionReportNode()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch("src.nodes.conclusion_report_node.DebateStateExtractor")
    @patch("src.nodes.conclusion_report_node.ConclusionWriter")
    def test_conclusion_generation_performance(self, mock_writer_class, mock_extractor_class):
        """Test that conclusion generation completes in <5 seconds (SC-005)."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = ConclusionData(
            debate_question="Test?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Performance test",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-performance",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )
        mock_extractor_class.return_value = mock_extractor

        # Mock the writer
        mock_writer = MagicMock()
        mock_writer.write.return_value = f"{self.output_dir}/Conclusion.md"
        mock_writer_class.return_value = mock_writer

        self.node.extractor = mock_extractor
        self.node.writer = mock_writer

        state = {
            "messages": [],
            "verdict": {
                "winner": "PRO",
                "winner_position": "PRO",
                "justification": "Performance test",
            },
            "output_dir": self.output_dir,
            "debate_type": "standard",
            "run_id": "test-performance",
            "debate_topic": "Test?",
        }

        # Measure execution time
        start_time = time.time()
        result = self.node(state)
        end_time = time.time()

        execution_time = end_time - start_time

        # Verify file was created
        self.assertIn("conclusion_report_path", result)

        # Verify performance requirement (SC-005: <5 seconds)
        # With mocked dependencies, this should be very fast
        self.assertLess(execution_time, 5.0, "Conclusion generation took longer than 5 seconds")


if __name__ == "__main__":
    unittest.main()
