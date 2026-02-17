"""
Unit tests for BaseComponent language injection (Feature 012).

This module verifies that language_setting is properly injected into
agent prompts when provided, and that backward compatibility is maintained.
"""

import pytest
from nodes.base_component import BaseComponent
from configurations.llm_config import OpenAILLMConfig


@pytest.fixture
def mock_llm_config():
    """Mock LLM config for testing."""
    return OpenAILLMConfig(
        model_name="gpt-4",
        openai_api_key="test-key-for-unit-tests"
    )


def test_create_chain_without_language_setting(mock_llm_config):
    """Test create_chain works without language setting (backward compatibility)."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant."
    human_template = "Hello {name}."

    chain = component.create_chain(system_template, human_template)

    assert chain is not None
    assert component.prompt_template is not None
    # Verify no injection in system message
    prompt_str = str(component.prompt_template)
    assert "**Language and Style Setting**:" not in prompt_str


def test_create_chain_with_language_setting(mock_llm_config):
    """Test create_chain injects language setting when provided."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant."
    human_template = "Hello {name}."
    language_setting = "Русский официальный стиль"

    chain = component.create_chain(system_template, human_template, language_setting)

    assert chain is not None
    # Verify injection was prepended to system template
    prompt_str = str(component.prompt_template)
    assert "**Language and Style Setting**:" in prompt_str
    assert language_setting in prompt_str
    # Verify injection comes before original system template
    assert prompt_str.index("**Language and Style Setting**:") < prompt_str.index("You are a helpful assistant")


def test_create_chain_with_english_concise_setting(mock_llm_config):
    """Test create_chain with English concise language setting."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant."
    human_template = "Hello {name}."
    language_setting = "English, concise and factual, no fluff"

    chain = component.create_chain(system_template, human_template, language_setting)

    assert chain is not None
    prompt_str = str(component.prompt_template)
    assert "**Language and Style Setting**:" in prompt_str
    assert language_setting in prompt_str


def test_create_chain_empty_language_setting(mock_llm_config):
    """Test create_chain treats empty string as no language setting."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant."
    human_template = "Hello {name}."

    chain = component.create_chain(system_template, human_template, "")

    # Empty string should not trigger injection (falsy value)
    assert chain is not None
    prompt_str = str(component.prompt_template)
    assert "**Language and Style Setting**:" not in prompt_str


def test_create_chain_none_language_setting(mock_llm_config):
    """Test create_chain treats None as no language setting."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant."
    human_template = "Hello {name}."

    chain = component.create_chain(system_template, human_template, None)

    # None should not trigger injection
    assert chain is not None
    prompt_str = str(component.prompt_template)
    assert "**Language and Style Setting**:" not in prompt_str


def test_language_injection_format_correct(mock_llm_config):
    """Test that language injection uses the correct format."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "Original system message."
    human_template = "Hello."
    language_setting = "Test Language"

    component.create_chain(system_template, human_template, language_setting)

    prompt_str = str(component.prompt_template)

    # Verify injection contains the key elements (format may have escaped newlines in string repr)
    assert "**Language and Style Setting**:" in prompt_str
    assert "Test Language" in prompt_str
    assert "Original system message." in prompt_str
    # Verify the injection comes before the original template
    assert prompt_str.index("**Language and Style Setting**:") < prompt_str.index("Original system message")


def test_language_injection_preserves_original_template(mock_llm_config):
    """Test that language injection preserves the original system template."""
    component = BaseComponent(llm_config=mock_llm_config)
    system_template = "You are a helpful assistant. Be concise and accurate."
    human_template = "Hello."
    language_setting = "Russian formal style"

    component.create_chain(system_template, human_template, language_setting)

    prompt_str = str(component.prompt_template)

    # Verify original template is preserved
    assert "You are a helpful assistant. Be concise and accurate." in prompt_str
    assert "Be concise and accurate" in prompt_str


def test_base_component_callable_captures_language_setting(mock_llm_config):
    """Test that __call__ captures language_setting from state."""
    component = BaseComponent(llm_config=mock_llm_config)

    state_with_language = {
        "debate_topic": "Test topic",
        "positions": {},
        "messages": [],
        "language_setting": "Test Language Setting"
    }

    # Call the component with state
    component(state_with_language)

    # Verify language_setting was captured as an attribute
    assert hasattr(component, 'language_setting')
    assert component.language_setting == "Test Language Setting"


def test_base_component_callable_without_language_setting(mock_llm_config):
    """Test that __call__ works without language_setting in state."""
    component = BaseComponent(llm_config=mock_llm_config)

    state_without_language = {
        "debate_topic": "Test topic",
        "positions": {},
        "messages": []
        # No language_setting
    }

    # Call the component with state
    component(state_without_language)

    # language_setting attribute should not exist (not in state)
    assert not hasattr(component, 'language_setting')
