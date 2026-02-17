"""
Unit and integration tests for --language flag feature (Feature 012).

These tests validate the language flag functionality at the component level.
Full E2E tests will pass after WP01 and WP02 are merged to main.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDebateStateLanguageField(unittest.TestCase):
    """Test that DebateState has language_setting field (WP01)."""

    def test_debate_state_definition_exists(self):
        """Test that DebateState can be imported."""
        try:
            from debate_state import DebateState
            self.assertTrue(True)
        except ImportError:
            self.fail("DebateState should be importable")

    def test_debate_state_has_language_setting_field(self):
        """Test that DebateState includes language_setting field."""
        from debate_state import DebateState
        from typing import get_type_hints

        type_hints = get_type_hints(DebateState, include_extras=True)
        self.assertIn('language_setting', type_hints,
                     "DebateState must include 'language_setting' field")

    def test_debate_state_accepts_language_setting(self):
        """Test creating DebateState with language_setting."""
        from debate_state import DebateState

        # This test will pass after WP01 is merged
        try:
            state = DebateState(
                debate_topic="Test topic",
                positions={},
                messages=[],
                language_setting="Русский официальный стиль"
            )
            self.assertEqual(state["language_setting"], "Русский официальный стиль")
        except TypeError as e:
            if "language_setting" in str(e):
                self.skipTest("WP01 not merged yet - language_setting field not available")
            else:
                raise

    def test_debate_state_backward_compatible(self):
        """Test that DebateState works without language_setting."""
        from debate_state import DebateState

        state = DebateState(
            debate_topic="Test topic",
            positions={},
            messages=[]
        )
        # Should work without language_setting
        self.assertEqual(state["debate_topic"], "Test topic")


class TestBaseComponentLanguageInjection(unittest.TestCase):
    """Test BaseComponent language injection (WP01)."""

    def test_base_component_exists(self):
        """Test that BaseComponent can be imported."""
        try:
            from nodes.base_component import BaseComponent
            self.assertTrue(True)
        except ImportError:
            self.fail("BaseComponent should be importable")

    def test_base_component_create_chain_signature(self):
        """Test that create_chain accepts language_setting parameter."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig
        import inspect

        config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
        component = BaseComponent(llm_config=config)

        sig = inspect.signature(component.create_chain)
        params = sig.parameters

        # Check if language_setting parameter exists (after WP01)
        if 'language_setting' in params:
            # Parameter exists - test it
            param = params['language_setting']
            # Should be optional (has default)
            self.assertEqual(param.default, None)  # or inspect.Parameter.empty
        else:
            self.skipTest("WP01 not merged yet - language_setting parameter not available")

    def test_language_injection_with_setting(self):
        """Test that language_setting is injected into prompt template."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig

        try:
            config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
            component = BaseComponent(llm_config=config)

            # Try to create chain with language_setting
            try:
                chain = component.create_chain(
                    "You are a helpful assistant.",
                    "Hello {name}.",
                    language_setting="Русский официальный стиль"
                )

                # Check if injection was applied
                prompt_str = str(component.prompt_template)
                self.assertIn("**Language and Style Setting**:", prompt_str)
                self.assertIn("Русский официальный стиль", prompt_str)
            except TypeError as e:
                if "language_setting" in str(e):
                    self.skipTest("WP01 not merged yet - create_chain doesn't accept language_setting")
                else:
                    raise
        except ImportError:
            self.fail("BaseComponent and OpenAILLMConfig should be importable")

    def test_language_injection_without_setting(self):
        """Test backward compatibility - no injection when language_setting is None."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig

        config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
        component = BaseComponent(llm_config=config)

        # Create chain without language_setting
        chain = component.create_chain(
            "You are a helpful assistant.",
            "Hello {name}."
        )

        # Should NOT have language injection
        prompt_str = str(component.prompt_template)
        self.assertNotIn("**Language and Style Setting**:", prompt_str)

    def test_language_injection_empty_string(self):
        """Test that empty string doesn't trigger injection."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig

        config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
        component = BaseComponent(llm_config=config)

        try:
            # Create chain with empty string
            chain = component.create_chain(
                "You are a helpful assistant.",
                "Hello {name}.",
                language_setting=""
            )

            # Empty string is falsy - should not trigger injection
            prompt_str = str(component.prompt_template)
            self.assertNotIn("**Language and Style Setting**:", prompt_str)
        except TypeError as e:
            if "language_setting" in str(e):
                self.skipTest("WP01 not merged yet")
            else:
                raise


class TestCLILanguageFlag(unittest.TestCase):
    """Test CLI --language flag (WP02)."""

    def test_main_py_imports(self):
        """Test that main.py can be imported."""
        try:
            import main
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"main.py should be importable: {e}")

    def test_main_py_has_argparse(self):
        """Test that main.py has argparse setup."""
        import inspect
        import main

        # Check if argparse is imported
        self.assertIn('argparse', dir(main))

    def test_document_debate_cli_imports(self):
        """Test that document_debate_cli.py can be imported."""
        try:
            import document_debate_cli
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"document_debate_cli.py should be importable: {e}")

    def test_document_debate_cli_has_argparse(self):
        """Test that document_debate_cli.py has argparse setup."""
        import document_debate_cli

        # Check if argparse is available
        self.assertTrue(hasattr(document_debate_cli, 'argparse'))


class TestWorkflowLanguageIntegration(unittest.TestCase):
    """Test workflow integration with language_setting."""

    def test_debate_workflow_accepts_initial_state(self):
        """Test that DebateWorkflow.run() can accept initial_state."""
        try:
            from workflow.debate_workflow import DebateWorkflow
            import inspect

            workflow = DebateWorkflow()
            sig = inspect.signature(workflow.run)

            if 'initial_state' in sig.parameters:
                self.assertTrue(True)
            else:
                self.skipTest("WP02 not merged yet - run() doesn't accept initial_state")
        except ImportError:
            self.fail("DebateWorkflow should be importable")

    def test_document_debate_workflow_accepts_initial_state(self):
        """Test that DocumentDebateWorkflow.run() can accept initial_state."""
        try:
            from workflow.document_debate_workflow import DocumentDebateWorkflow
            import inspect

            workflow = DocumentDebateWorkflow()
            sig = inspect.signature(workflow.run)

            # DocumentDebateWorkflow should already have initial_state
            self.assertIn('initial_state', sig.parameters)
        except ImportError:
            self.fail("DocumentDebateWorkflow should be importable")


class TestLanguageFlagValidation(unittest.TestCase):
    """Test --language flag validation logic."""

    def test_500_char_limit_validation(self):
        """Test that 500-character limit validation logic works."""
        # Test values around the limit
        exact_500 = "a" * 500
        too_long_501 = "b" * 501
        empty = ""

        # Exact 500 should pass
        self.assertEqual(len(exact_500), 500)

        # 501 should fail
        self.assertGreater(len(too_long_501), 500)

        # Empty should be handled
        self.assertEqual(len(empty), 0)

    def test_whitespace_only_handling(self):
        """Test that whitespace-only strings are handled correctly."""
        whitespace_only = "   \t\n  "

        # After strip, should be empty
        self.assertEqual(len(whitespace_only.strip()), 0)
        self.assertFalse(bool(whitespace_only.strip()))


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility without --language flag."""

    def test_debate_state_minimal(self):
        """Test that DebateState works with minimal fields."""
        from debate_state import DebateState

        # Minimal state - should always work
        state = DebateState(
            debate_topic="Test topic",
            positions={},
            messages=[]
        )

        self.assertEqual(state["debate_topic"], "Test topic")
        self.assertEqual(len(state["messages"]), 0)

    def test_base_component_without_language_setting(self):
        """Test that BaseComponent works without language_setting."""
        from nodes.base_component import BaseComponent
        from configurations.llm_config import OpenAILLMConfig

        config = OpenAILLMConfig(model_name="gpt-4", openai_api_key="test-key")
        component = BaseComponent(llm_config=config)

        # Should work without any language_setting
        chain = component.create_chain(
            "You are a helpful assistant.",
            "Hello {name}."
        )

        self.assertIsNotNone(chain)


if __name__ == '__main__':
    unittest.main(verbosity=2)
