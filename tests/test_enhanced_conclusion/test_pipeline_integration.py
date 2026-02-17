"""
Unit tests for Enhanced Pipeline Integration in ConclusionReportNode.

Tests verify:
- Committee debate detection and routing (T041)
- Enhanced pipeline execution (T042)
- Final report reading logic (T043)
- Output path to committee_output/{run_id}/conclusion.md (T044)
- End-to-end integration test (T045)
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.nodes.conclusion_report_node import ConclusionReportNode
from src.types.enhanced_conclusion_types import (
    Verdict,
    RoleAnalysis,
    CriticalGap,
    Recommendation,
    EvidenceReference,
)


@pytest.fixture
def mock_final_report():
    """Mock final_report.md content for testing."""
    return """# Product Committee Report

**Run ID:** RUN_20260215_202208_test
**Generated:** 2026-02-15T20:22:08Z

---

## Committee Question

Should we approve the PRD for the new AI-powered feature?

---

## Executive Summary

This report synthesizes debate results from 4 committee rooms.

---

## Room-by-Room Analysis

### TPM_vs_CPO

**Status:** success

**Winner:** TPM

**Judge Explanation:** TPM demonstrated clear product vision and user value.

**Key Takeaways:**
- User value proposition is strong
- Market timing is favorable

**Full Dialogue:**

**PRO** (opening):
The PRD presents a compelling vision for AI-powered features that address real user needs.

**CON** (rebuttal):
While the vision is compelling, the implementation timeline seems overly aggressive.

---

### TPM_vs_CFO

**Status:** success

**Winner:** CFO

**Judge Explanation:** Financial concerns are significant and require additional planning.

**Key Takeaways:**
- Financial model lacks conservative scenarios
- Implementation costs are underestimated
"""


@pytest.fixture
def mock_verdict():
    """Mock verdict for testing."""
    # Create a valid Verdict with 120-150 words
    answer_words = " ".join(["word"] * 130)
    return Verdict(
        answer=answer_words,
        confidence="Medium",
        rationale="Split decision with 3-1 outcome. Financial concerns were significant.",
        room_outcomes="PRO won 3/4 rooms"
    )


@pytest.fixture
def mock_role_analyses():
    """Mock role analyses for testing."""
    return [
        RoleAnalysis(
            role_name="CFO",
            strengths=[],
            weaknesses=[
                {
                    "description": "Financial model lacks conservative scenarios",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="The financial model is overly optimistic."
                    )
                }
            ]
        )
    ]


@pytest.fixture
def mock_gaps():
    """Mock critical gaps for testing."""
    return [
        CriticalGap(
            title="Incomplete Financial Analysis",
            severity="High",
            description="The financial model lacks conservative scenarios.",
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


@pytest.fixture
def mock_recommendations():
    """Mock recommendations for testing."""
    return [
        Recommendation(
            priority="High",
            problem="The PRD lacks a comprehensive financial analysis",
            action="Add a detailed Financial Analysis section to the PRD",
            metric="PRD includes complete financial analysis with ROI projections",
            source_evidence=EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=2,
                quote="The financial model is overly optimistic."
            )
        )
    ]


class TestCommitteeDebateDetection:
    """Test committee debate detection and routing (T041)."""

    def test_detect_committee_debate_with_custom_prompts(self):
        """Test detection of committee debate when custom prompts are present."""
        node = ConclusionReportNode()
        state = {
            "pro_custom_prompt": "TPM role prompt",
            "con_custom_prompt": "CFO role prompt",
            "debate_topic": "Should we approve the PRD?"
        }

        debate_type = node._detect_debate_type(state)
        assert debate_type.value == "committee"

    def test_detect_standard_debate(self):
        """Test detection of standard debate without custom prompts."""
        node = ConclusionReportNode()
        state = {
            "debate_topic": "Should we invest in AI?"
        }

        debate_type = node._detect_debate_type(state)
        assert debate_type.value == "standard"

    def test_detect_document_debate(self):
        """Test detection of document debate."""
        node = ConclusionReportNode()
        state = {
            "document_input": "path/to/document.docx",
            "debate_topic": "Should we invest in AI?"
        }

        debate_type = node._detect_debate_type(state)
        assert debate_type.value == "document"


class TestEnhancedPipelineExecution:
    """Test enhanced pipeline execution (T042)."""

    @patch('src.nodes.conclusion_report_node.VerdictExtractor')
    @patch('src.nodes.conclusion_report_node.RoleAnalyzer')
    @patch('src.nodes.conclusion_report_node.GapRecommendationGenerator')
    @patch('src.nodes.conclusion_report_node.EnhancedConclusionWriter')
    def test_run_enhanced_pipeline_success(
        self, mock_writer_class, mock_gap_class, mock_role_class, mock_verdict_class,
        mock_final_report, mock_verdict, mock_role_analyses, mock_gaps, mock_recommendations
    ):
        """Test successful execution of enhanced pipeline."""
        # Setup mocks
        mock_verdict_extractor = MagicMock()
        mock_verdict_extractor.extract.return_value = mock_verdict
        mock_verdict_class.return_value = mock_verdict_extractor

        mock_role_analyzer = MagicMock()
        mock_role_analyzer.analyze.return_value = mock_role_analyses
        mock_role_class.return_value = mock_role_analyzer

        mock_gap_generator = MagicMock()
        mock_gap_generator.generate.return_value = (mock_gaps, mock_recommendations)
        mock_gap_class.return_value = mock_gap_generator

        mock_writer = MagicMock()
        mock_output = MagicMock()
        mock_output.rename.return_value = None
        mock_writer.write.return_value = mock_output
        mock_writer_class.return_value = mock_writer

        # Create node with temporary committee output directory
        node = ConclusionReportNode()

        # Create mock state with run_id
        state = {
            "run_id": "RUN_20260215_202208_test",
            "debate_topic": "Should we approve the PRD?"
        }

        # Create temporary committee output directory with final_report.md
        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_20260215_202208_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text(mock_final_report, encoding="utf-8")

            # Patch Path to use temp directory
            with patch('pathlib.Path', lambda *args, **kwargs: Path(tmpdir).joinpath(*args[1:] if len(args) > 1 else args[0]) if args and 'committee_output' in str(args[0]) else Path(*args, **kwargs)):
                # Change to temp directory for test
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    result_path = node._run_enhanced_pipeline(state)
                finally:
                    os.chdir(original_cwd)

        # Verify pipeline was executed
        mock_verdict_extractor.extract.assert_called_once()
        mock_role_analyzer.analyze.assert_called_once()
        mock_gap_generator.generate.assert_called_once()
        mock_writer.write.assert_called_once()

    @patch('src.nodes.conclusion_report_node.VerdictExtractor')
    def test_run_enhanced_pipeline_fallback_on_error(self, mock_verdict_class):
        """Test fallback to basic conclusion when enhanced pipeline fails."""
        # Setup mock that raises exception
        mock_verdict_extractor = MagicMock()
        mock_verdict_extractor.extract.side_effect = Exception("LLM call failed")
        mock_verdict_class.return_value = mock_verdict_extractor

        node = ConclusionReportNode()

        state = {
            "run_id": "RUN_20260215_202208_test",
            "debate_topic": "Should we approve the PRD?"
        }

        # Create temporary committee output directory with final_report.md
        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_20260215_202208_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text("Mock report", encoding="utf-8")

            # Should raise Exception when pipeline fails (no fallback implemented yet)
            with pytest.raises(Exception, match="LLM call failed"):
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    node._run_enhanced_pipeline(state)
                finally:
                    os.chdir(original_cwd)


class TestFinalReportReading:
    """Test final_report.md reading logic (T043)."""

    def test_read_final_report_success(self, mock_final_report):
        """Test successful reading of final_report.md."""
        node = ConclusionReportNode()

        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_20260215_202208_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text(mock_final_report, encoding="utf-8")

            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                content = node._read_final_report("RUN_20260215_202208_test")
            finally:
                os.chdir(original_cwd)

            assert content == mock_final_report
            assert len(content) > 0

    def test_read_final_report_utf8_encoding(self):
        """Test UTF-8 encoding support for Russian text."""
        node = ConclusionReportNode()
        russian_text = "# Report\n\nКомитет достиг единогласного решения."

        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text(russian_text, encoding="utf-8")

            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                content = node._read_final_report("RUN_test")
            finally:
                os.chdir(original_cwd)

            assert "Комитет достиг единогласного решения" in content

    def test_read_final_report_file_not_found(self):
        """Test error handling when final_report.md is missing."""
        node = ConclusionReportNode()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory but not the file
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_missing"
            committee_dir.mkdir(parents=True)

            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with pytest.raises(ValueError, match="final_report.md not found"):
                    node._read_final_report("RUN_missing")
            finally:
                os.chdir(original_cwd)


class TestOutputPathHandling:
    """Test output path to committee_output/{run_id}/conclusion.md (T044)."""

    @patch('src.nodes.conclusion_report_node.VerdictExtractor')
    @patch('src.nodes.conclusion_report_node.RoleAnalyzer')
    @patch('src.nodes.conclusion_report_node.GapRecommendationGenerator')
    @patch('src.nodes.conclusion_report_node.EnhancedConclusionWriter')
    def test_output_path_committee_output_location(
        self, mock_writer_class, mock_gap_class, mock_role_class, mock_verdict_class,
        mock_final_report, mock_verdict, mock_role_analyses, mock_gaps, mock_recommendations
    ):
        """Test enhanced conclusion written to committee_output/{run_id}/conclusion.md."""
        # Setup mocks
        mock_verdict_extractor = MagicMock()
        mock_verdict_extractor.extract.return_value = mock_verdict
        mock_verdict_class.return_value = mock_verdict_extractor

        mock_role_analyzer = MagicMock()
        mock_role_analyzer.analyze.return_value = mock_role_analyses
        mock_role_class.return_value = mock_role_analyzer

        mock_gap_generator = MagicMock()
        mock_gap_generator.generate.return_value = (mock_gaps, mock_recommendations)
        mock_gap_class.return_value = mock_gap_generator

        # Track the output path
        written_path = None

        def mock_write(conclusion, output_dir, run_id=None):
            nonlocal written_path
            written_path = output_dir / "conclusion.md"
            written_path.parent.mkdir(parents=True, exist_ok=True)
            written_path.write_text("# Mock Conclusion", encoding="utf-8")
            # Return a temp path that will be renamed
            temp_path = output_dir / f"enhanced_conclusion_{run_id}.md"
            temp_path.write_text("# Mock Conclusion", encoding="utf-8")
            return temp_path

        mock_writer = MagicMock()
        mock_writer.write.side_effect = mock_write
        mock_writer_class.return_value = mock_writer

        node = ConclusionReportNode()

        state = {
            "run_id": "RUN_20260215_202208_test",
            "debate_topic": "Should we approve the PRD?"
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_20260215_202208_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text(mock_final_report, encoding="utf-8")

            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result_path = node._run_enhanced_pipeline(state)
            finally:
                os.chdir(original_cwd)

            # Verify output path
            assert "committee_output" in result_path
            assert "RUN_20260215_202208_test" in result_path
            assert "conclusion.md" in result_path


class TestEndToEndIntegration:
    """Test end-to-end integration (T045)."""

    @patch('src.nodes.conclusion_report_node.VerdictExtractor')
    @patch('src.nodes.conclusion_report_node.RoleAnalyzer')
    @patch('src.nodes.conclusion_report_node.GapRecommendationGenerator')
    @patch('src.nodes.conclusion_report_node.EnhancedConclusionWriter')
    def test_committee_debate_full_pipeline(
        self, mock_writer_class, mock_gap_class, mock_role_class, mock_verdict_class,
        mock_final_report, mock_verdict, mock_role_analyses, mock_gaps, mock_recommendations
    ):
        """Test complete pipeline execution with mock final_report.md."""
        # Setup mocks
        mock_verdict_extractor = MagicMock()
        mock_verdict_extractor.extract.return_value = mock_verdict
        mock_verdict_class.return_value = mock_verdict_extractor

        mock_role_analyzer = MagicMock()
        mock_role_analyzer.analyze.return_value = mock_role_analyses
        mock_role_class.return_value = mock_role_analyzer

        mock_gap_generator = MagicMock()
        mock_gap_generator.generate.return_value = (mock_gaps, mock_recommendations)
        mock_gap_class.return_value = mock_gap_generator

        # Track calls
        calls = []

        def mock_write(conclusion, output_dir, run_id=None):
            calls.append(("write", conclusion, output_dir, run_id))
            output_path = output_dir / f"enhanced_conclusion_{run_id}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("# Enhanced Conclusion", encoding="utf-8")
            return output_path

        mock_writer = MagicMock()
        mock_writer.write.side_effect = mock_write
        mock_writer_class.return_value = mock_writer

        node = ConclusionReportNode()

        # Committee debate state
        state = {
            "run_id": "RUN_20260215_202208_test",
            "pro_custom_prompt": "TPM role",
            "con_custom_prompt": "CFO role",
            "debate_topic": "Should we approve the PRD?"
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            committee_dir = Path(tmpdir) / "committee_output" / "RUN_20260215_202208_test"
            committee_dir.mkdir(parents=True)
            final_report_path = committee_dir / "final_report.md"
            final_report_path.write_text(mock_final_report, encoding="utf-8")

            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = node(state)
            finally:
                os.chdir(original_cwd)

        # Verify committee debate was detected and routed to enhanced pipeline
        assert "conclusion_report_path" in result
        assert "committee_output" in result["conclusion_report_path"]

        # Verify all pipeline stages were called
        mock_verdict_extractor.extract.assert_called_once()
        mock_role_analyzer.analyze.assert_called_once()
        mock_gap_generator.generate.assert_called_once()
        assert len(calls) == 1

    def test_standard_debate_uses_existing_pipeline(self):
        """Test that standard debates use the existing pipeline (not enhanced)."""
        node = ConclusionReportNode()

        state = {
            "debate_topic": "Should we invest in AI?",
            "messages": []
        }

        # Mock the existing pipeline methods
        with patch.object(node, '_generate_conclusion_with_llm', return_value='{"verdict": {"winner": "PRO"}}'):
            with patch.object(node, '_parse_llm_response', return_value={"verdict": {"winner": "PRO"}, "qa_summary": [], "tpm_analysis": None, "recommendations": [], "metadata": {"generated_at": "2026-02-15T12:00:00Z"}}):
                with patch.object(node, '_write_conclusion_report', return_value="/path/to/conclusion.md"):
                    result = node(state)

        # Verify standard pipeline was used (no enhanced pipeline calls)
        assert "conclusion_report_path" in result
        assert "/path/to/conclusion.md" == result["conclusion_report_path"]


class TestRunIdExtraction:
    """Test run_id extraction from state."""

    def test_get_run_id_from_state_direct(self):
        """Test run_id extraction when directly in state."""
        node = ConclusionReportNode()
        state = {"run_id": "RUN_123"}

        run_id = node._get_run_id_from_state(state)
        assert run_id == "RUN_123"

    def test_get_run_id_from_state_from_output_dir(self):
        """Test run_id extraction from output_dir path."""
        node = ConclusionReportNode()
        state = {
            "output_dir": "committee_output/RUN_456",
            "debate_topic": "Test topic"
        }

        run_id = node._get_run_id_from_state(state)
        assert run_id == "RUN_456"

    def test_get_run_id_from_state_fallback_generation(self):
        """Test run_id generation fallback when not in state."""
        node = ConclusionReportNode()
        state = {
            "debate_topic": "Should we approve the PRD?"
        }

        run_id = node._get_run_id_from_state(state)
        # Should generate a run_id from the topic
        assert run_id is not None
        assert len(run_id) > 0
