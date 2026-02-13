"""
Contract tests for DebateState extension.

This module verifies that the DebateState TypedDict properly extends
to support document_input field for document-based debates.
"""

import unittest
from typing import get_type_hints
from debate_state import DebateState


class TestDebateStateContract(unittest.TestCase):
    """Contract tests for DebateState TypedDict extension."""

    def test_debate_state_has_document_input_field(self):
        """Test that DebateState includes document_input field."""
        type_hints = get_type_hints(DebateState, include_extras=True)

        # Check that document_input is in the type hints
        self.assertIn('document_input', type_hints,
                     "DebateState must include 'document_input' field for document-based debates")

    def test_debate_state_has_required_fields(self):
        """Test that DebateState includes all required fields."""
        type_hints = get_type_hints(DebateState, include_extras=True)

        required_fields = [
            'debate_topic',
            'positions',
            'messages'
        ]

        for field in required_fields:
            self.assertIn(field, type_hints,
                         f"DebateState must include '{field}' field")

    def test_debate_state_supports_optional_fields(self):
        """Test that DebateState properly supports optional fields."""
        # Create a minimal valid state
        minimal_state = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": []
        }

        # Verify it can be created without error
        try:
            state = DebateState(**minimal_state)
            self.assertEqual(state["debate_topic"], "Test topic")
        except Exception as e:
            self.fail(f"Failed to create minimal DebateState: {e}")

    def test_debate_state_with_document_input(self):
        """Test that DebateState can accept document_input."""
        state_with_doc = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": [],
            "document_input": "Sample document text for testing."
        }

        try:
            state = DebateState(**state_with_doc)
            self.assertEqual(state["document_input"], "Sample document text for testing.")
        except Exception as e:
            self.fail(f"Failed to create DebateState with document_input: {e}")

    def test_document_input_accepts_file_path(self):
        """Test that document_input can accept .docx file paths."""
        state_with_file = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": [],
            "document_input": "/path/to/document.docx"
        }

        try:
            state = DebateState(**state_with_file)
            self.assertTrue(state["document_input"].endswith(".docx"))
        except Exception as e:
            self.fail(f"Failed to create DebateState with .docx file path: {e}")


if __name__ == '__main__':
    unittest.main()
