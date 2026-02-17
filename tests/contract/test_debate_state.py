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

    def test_language_setting_field_exists(self):
        """Test that DebateState includes language_setting field (Feature 012)."""
        type_hints = get_type_hints(DebateState, include_extras=True)

        # Check that language_setting is in the type hints
        self.assertIn('language_setting', type_hints,
                     "DebateState must include 'language_setting' field for language/style configuration")

    def test_language_setting_with_value(self):
        """Test that DebateState can accept language_setting with a value."""
        state_with_language = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": [],
            "language_setting": "Русский официальный стиль"
        }

        try:
            state = DebateState(**state_with_language)
            self.assertEqual(state["language_setting"], "Русский официальный стиль")
        except Exception as e:
            self.fail(f"Failed to create DebateState with language_setting: {e}")

    def test_language_setting_with_none(self):
        """Test that DebateState can accept language_setting with None value."""
        state_with_none = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": [],
            "language_setting": None
        }

        try:
            state = DebateState(**state_with_none)
            self.assertIsNone(state["language_setting"])
        except Exception as e:
            self.fail(f"Failed to create DebateState with language_setting=None: {e}")

    def test_language_setting_optional(self):
        """Test that DebateState works without language_setting (backward compatibility)."""
        state_without_language = {
            "debate_topic": "Test topic",
            "positions": {"pro": "In favor", "con": "Against"},
            "messages": []
            # language_setting omitted
        }

        try:
            state = DebateState(**state_without_language)
            # Should work fine without language_setting
            self.assertNotIn("language_setting", state)
        except Exception as e:
            self.fail(f"Failed to create DebateState without language_setting: {e}")


if __name__ == '__main__':
    unittest.main()
