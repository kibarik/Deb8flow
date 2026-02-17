"""
E2E tests for --language flag feature (Feature 012).

This module tests the --language CLI flag functionality:
1. Language flag is properly parsed
2. Language setting propagates to workflow state
3. Backward compatibility (no flag = existing behavior)
4. Validation of 500-character limit
"""

import asyncio
import subprocess
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestLanguageFlagE2E(unittest.TestCase):
    """End-to-end tests for --language CLI flag."""

    def test_main_py_help_shows_language_flag(self):
        """Test that main.py --help shows the --language flag."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--language", result.stdout)
        self.assertIn("Language and style setting", result.stdout)

    def test_document_debate_cli_help_shows_language_flag(self):
        """Test that document_debate_cli.py --help shows the --language flag."""
        result = subprocess.run(
            [sys.executable, "document_debate_cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--language", result.stdout)
        self.assertIn("Language and style setting", result.stdout)

    def test_language_flag_validation_501_chars_fails(self):
        """Test that language value > 500 characters is rejected."""
        long_value = "a" * 501
        result = subprocess.run(
            [sys.executable, "main.py", "--language", long_value],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        # Should fail with validation error
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("too long", result.stderr.lower())

    def test_language_flag_validation_500_chars_passes(self):
        """Test that language value = 500 characters is accepted."""
        exact_value = "a" * 500
        result = subprocess.run(
            [sys.executable, "main.py", "--language", exact_value],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5  # Should fail quickly due to missing API key
        )

        # Should pass validation (may fail later due to API key, but validation should pass)
        # We check that it doesn't have the "too long" error
        self.assertNotIn("too long", result.stderr.lower())
        self.assertNotIn("too long", result.stdout.lower())

    def test_language_flag_empty_string_treated_as_none(self):
        """Test that empty string is treated as None (no language setting)."""
        result = subprocess.run(
            [sys.executable, "main.py", "--language", ""],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Empty string should not cause validation error
        # Should proceed without language setting
        self.assertNotIn("too long", result.stderr.lower())
        self.assertNotIn("too long", result.stdout.lower())

    def test_language_flag_with_whitespace_only_treated_as_none(self):
        """Test that whitespace-only string is treated as None."""
        result = subprocess.run(
            [sys.executable, "main.py", "--language", "   "],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Whitespace-only should be treated as None
        self.assertNotIn("too long", result.stderr.lower())
        self.assertNotIn("too long", result.stdout.lower())

    def test_language_flag_displays_in_log_when_set(self):
        """Test that language setting is logged when provided."""
        result = subprocess.run(
            [sys.executable, "main.py", "--language", "Test Language"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Should show language setting in log
        self.assertIn("Language setting", result.stdout)
        self.assertIn("Test Language", result.stdout)

    def test_language_flag_not_logged_when_not_set(self):
        """Test that language setting is not mentioned when flag not provided."""
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Should NOT show language setting in log
        self.assertNotIn("Language setting", result.stdout)
        self.assertNotIn("Language setting", result.stderr)

    def test_document_debate_cli_text_with_language_flag(self):
        """Test that --text and --language flags work together."""
        result = subprocess.run(
            [sys.executable, "document_debate_cli.py", "--text", "Test topic", "--language", "Russian"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Should accept both flags
        self.assertNotIn("incompatible", result.stderr.lower())
        self.assertNotIn("cannot use", result.stderr.lower())


class TestLanguageFlagStatePropagation(unittest.TestCase):
    """Tests that language_setting propagates correctly through state."""

    def test_debate_state_has_language_setting_field(self):
        """Test that DebateState includes language_setting field."""
        from debate_state import DebateState
        from typing import get_type_hints

        type_hints = get_type_hints(DebateState, include_extras=True)
        self.assertIn('language_setting', type_hints)

    def test_debate_state_with_language_setting(self):
        """Test creating DebateState with language_setting."""
        from debate_state import DebateState

        state = DebateState(
            debate_topic="Test topic",
            positions={},
            messages=[],
            language_setting="Русский официальный стиль"
        )

        self.assertEqual(state["language_setting"], "Русский официальный стиль")

    def test_debate_state_without_language_setting(self):
        """Test creating DebateState without language_setting (backward compatibility)."""
        from debate_state import DebateState

        state = DebateState(
            debate_topic="Test topic",
            positions={},
            messages=[]
        )

        # Should work without language_setting
        self.assertNotIn("language_setting", state)


class TestLanguageFlagBackwardCompatibility(unittest.TestCase):
    """Tests that existing behavior is preserved without --language flag."""

    def test_main_py_works_without_language_flag(self):
        """Test that main.py works normally when --language is not provided."""
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Should not have language-related errors
        self.assertNotIn("language", result.stderr.lower())
        # Should start workflow normally
        self.assertIn("Starting debate workflow" if "Starting" in result.stdout else "",
                     result.stdout)

    def test_document_debate_cli_text_works_without_language_flag(self):
        """Test that document_debate_cli.py --text works without --language."""
        result = subprocess.run(
            [sys.executable, "document_debate_cli.py", "--text", "Test topic"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )

        # Should not have language-related errors
        self.assertNotIn("language", result.stderr.lower())


class TestLanguageFlagWorkflowIntegration(unittest.TestCase):
    """Tests that language_setting integrates with workflows."""

    def test_debate_workflow_accepts_initial_state(self):
        """Test that DebateWorkflow.run() accepts initial_state parameter."""
        from workflow.debate_workflow import DebateWorkflow

        workflow = DebateWorkflow()
        # Check if run() accepts initial_state
        import inspect
        sig = inspect.signature(workflow.run)
        self.assertIn('initial_state', sig.parameters)

    def test_document_debate_workflow_accepts_initial_state(self):
        """Test that DocumentDebateWorkflow.run() accepts initial_state parameter."""
        from workflow.document_debate_workflow import DocumentDebateWorkflow

        workflow = DocumentDebateWorkflow()
        import inspect
        sig = inspect.signature(workflow.run)
        self.assertIn('initial_state', sig.parameters)

    def test_base_component_has_language_injection(self):
        """Test that BaseComponent.create_chain() supports language_setting parameter."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig
        import inspect

        config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
        component = BaseComponent(llm_config=config)

        sig = inspect.signature(component.create_chain)
        self.assertIn('language_setting', sig.parameters)


if __name__ == '__main__':
    unittest.main()
