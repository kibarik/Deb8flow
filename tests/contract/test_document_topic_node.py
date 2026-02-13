"""
Contract tests for DocumentTopicNode.

This module verifies that the DocumentTopicNode properly implements
the contract for generating debate topics from document input.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from nodes.document_topic_node import DocumentTopicNodefrom docx import Documentfrom nodes.document_topic_node import DocumentTopicNode
from debate_state import DebateState
from configurations.llm_config import RequestyLLMConfig


class TestDocumentTopicNodeContract(unittest.TestCase):
    """Contract tests for DocumentTopicNode implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm_config = RequestyLLMConfig(
            model_name="deepseek/deepseek-chat",
            req_api_key="test-key"
        )
        # Mock the LLM initialization to avoid actual API calls
        with patch('nodes.base_component.BaseComponent._init_llm'):
            self.node = DocumentTopicNode(self.llm_config)

    def test_document_topic_node_requires_document_input(self):
        """Test that DocumentTopicNode requires document_input in state."""
        state_without_doc = {
            "debate_topic": "",
            "positions": {},
            "messages": []
        }

        with self.assertRaises(ValueError) as context:
            self.node(state_without_doc)

        self.assertIn("Document input is required", str(context.exception))

    def test_document_topic_node_accepts_text_input(self):
        """Test that DocumentTopicNode accepts pre-extracted text."""
        # Mock the chain execution
        self.node.execute_chain = Mock(return_value="Test debate topic from document")
        self.node.logger = Mock()

        state_with_text = {
            "document_input": "Sample document text for testing.",
            "debate_topic": "",
            "positions": {},
            "messages": []
        }

        result = self.node(state_with_text)

        self.assertIn("debate_topic", result)
        self.assertEqual(result["debate_topic"], "Test debate topic from document")
        self.assertIn("positions", result)
        self.assertEqual(result["stage"], "opening")
        self.assertEqual(result["speaker"], "pro")

    def test_document_topic_node_returns_expected_structure(self):
        """Test that DocumentTopicNode returns properly structured state."""
        self.node.execute_chain = Mock(return_value="Generated topic")
        self.node.logger = Mock()

        state = {
            "document_input": "Test document",
            "debate_topic": "",
            "positions": {},
            "messages": []
        }

        result = self.node(state)

        # Verify all expected fields are present
        expected_fields = ["debate_topic", "positions", "stage", "speaker"]
        for field in expected_fields:
            self.assertIn(field, result,
                         f"DocumentTopicNode result must include '{field}' field")

        # Verify values
        self.assertEqual(result["stage"], "opening")
        self.assertEqual(result["speaker"], "pro")
        self.assertEqual(result["positions"]["pro"], "In favor")
        self.assertEqual(result["positions"]["con"], "Against")

    def test_document_topic_node_handles_docx_file_path(self):
        """Test that DocumentTopicNode can handle .docx file paths."""
        # Mock Document and chain execution
        with patch('nodes.document_topic_node.DocumentTopicNode') as MockDocument:
            mock_doc = Mock()
            mock_doc.paragraphs = [Mock(text="Sample document content")]
            MockDocument.return_value = mock_doc

            self.node.execute_chain = Mock(return_value="Topic from file")
            self.node.logger = Mock()

            state = {
                "document_input": "/path/to/document.docx",
                "debate_topic": "",
                "positions": {},
                "messages": []
            }

            result = self.node(state)

            # Verify Document was called with the file path
            MockDocument.assert_called_once_with("/path/to/document.docx")
            self.assertEqual(result["debate_topic"], "Topic from file")


if __name__ == '__main__':
    unittest.main()
