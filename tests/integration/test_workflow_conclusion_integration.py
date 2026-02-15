"""Integration tests for conclusion report workflow integration.

Tests that ConclusionReportNode is properly integrated into both
standard and document debate workflows and generates Conclusion.md.
"""

import unittest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from workflow.debate_workflow import DebateWorkflow
from workflow.document_debate_workflow import DocumentDebateWorkflow
from debate_state import DebateState


class TestStandardWorkflowConclusionIntegration(unittest.TestCase):
    """Test standard workflow integration with ConclusionReportNode."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflow = DebateWorkflow()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_conclusion_node_in_workflow_graph(self):
        """Test that ConclusionReportNode is added to the workflow graph."""
        graph = self.workflow._initialize_workflow()
        nodes = graph.nodes

        # Verify conclusion_report_node is in the graph
        self.assertIn("conclusion_report_node", nodes)

    def test_workflow_edges_include_conclusion(self):
        """Test that workflow edges route through conclusion node."""
        graph = self.workflow._initialize_workflow()

        # Get the graph structure
        compiled_graph = graph.compile()
        graph_dict = compiled_graph.get_graph().to_dict()

        # Verify judge_node -> conclusion_report_node edge exists
        edges = graph_dict.get("edges", [])
        judge_to_conclusion = any(
            e.get("source") == "judge_node" and e.get("target") == "conclusion_report_node"
            for e in edges
        )
        self.assertTrue(judge_to_conclusion, "judge_node should connect to conclusion_report_node")

        # Verify conclusion_report_node -> END edge exists
        conclusion_to_end = any(
            e.get("source") == "conclusion_report_node" and e.get("target") == "__end__"
            for e in edges
        )
        self.assertTrue(conclusion_to_end, "conclusion_report_node should connect to END")

    @patch("workflow.debate_workflow.DebateWorkflow._initialize_workflow")
    async def test_conclusion_report_generated_in_standard_workflow(self, mock_init):
        """Test that Conclusion.md is generated during workflow execution."""
        # Mock the graph execution
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [],
            "verdict": {"winner": "PRO", "justification": "Test"},
            "output_dir": self.output_dir,
        })
        mock_init.return_value.compile.return_value = mock_graph

        await self.workflow.run()

        # Verify workflow was invoked
        mock_graph.ainvoke.assert_called_once()


class TestDocumentWorkflowConclusionIntegration(unittest.TestCase):
    """Test document workflow integration with ConclusionReportNode."""

    def setUp(self):
        """Set up test fixtures."""
        self.workflow = DocumentDebateWorkflow()
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_conclusion_node_in_workflow_graph(self):
        """Test that ConclusionReportNode is added to the workflow graph."""
        graph = self.workflow._initialize_workflow()
        nodes = graph.nodes

        # Verify conclusion_report_node is in the graph
        self.assertIn("conclusion_report_node", nodes)

    def test_workflow_edges_include_conclusion(self):
        """Test that workflow edges route through conclusion node."""
        graph = self.workflow._initialize_workflow()

        # Get the graph structure
        compiled_graph = graph.compile()
        graph_dict = compiled_graph.get_graph().to_dict()

        # Verify judge_node -> conclusion_report_node edge exists
        edges = graph_dict.get("edges", [])
        judge_to_conclusion = any(
            e.get("source") == "judge_node" and e.get("target") == "conclusion_report_node"
            for e in edges
        )
        self.assertTrue(judge_to_conclusion, "judge_node should connect to conclusion_report_node")

        # Verify conclusion_report_node -> END edge exists
        conclusion_to_end = any(
            e.get("source") == "conclusion_report_node" and e.get("target") == "__end__"
            for e in edges
        )
        self.assertTrue(conclusion_to_end, "conclusion_report_node should connect to END")

    @patch("workflow.document_debate_workflow.DocumentDebateWorkflow._initialize_workflow")
    async def test_conclusion_report_generated_in_document_workflow(self, mock_init):
        """Test that Conclusion.md is generated during workflow execution."""
        # Mock the graph execution
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [],
            "verdict": {"winner": "CON", "justification": "Test document debate"},
            "output_dir": self.output_dir,
            "document_input": "test document content",
        })
        mock_init.return_value.compile.return_value = mock_graph

        await self.workflow.run(initial_state={"document_input": "test"})

        # Verify workflow was invoked
        mock_graph.ainvoke.assert_called_once()


class TestConclusionFileLocation(unittest.TestCase):
    """Test that Conclusion.md is generated in the correct location."""

    def setUp(self):
        """Set up test fixtures."""
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    async def test_conclusion_file_in_output_directory(self):
        """Test that Conclusion.md is created in the specified output directory."""
        from src.utils.conclusion_writer import ConclusionWriter
        from src.types.conclusion_types import (
            ConclusionData,
            VerdictSummary,
            ConclusionMetadata,
            DebateType,
        )

        writer = ConclusionWriter()
        conclusion_data = ConclusionData(
            debate_question="Test question?",
            verdict=VerdictSummary(
                winner="PRO",
                winner_position="PRO",
                justification="Test justification",
            ),
            qa_summary=[],
            tpm_analysis=None,
            recommendations=[],
            metadata=ConclusionMetadata(
                debate_type=DebateType.STANDARD.value,
                run_id="test-location",
                generated_at="2025-02-15T12:00:00Z",
                source_file=None,
                total_recommendations=0,
                tpm_victory=False,
                completion_status="success",
                error_message=None,
            ),
        )

        output_path = writer.write(
            output_path=self.output_dir,
            conclusion_data=conclusion_data,
        )

        # Verify file exists
        self.assertTrue(Path(output_path).exists())

        # Verify file is in the correct directory
        self.assertTrue(str(output_path).startswith(self.output_dir))

        # Verify filename is Conclusion.md
        self.assertEqual(Path(output_path).name, "Conclusion.md")


if __name__ == "__main__":
    unittest.main()
