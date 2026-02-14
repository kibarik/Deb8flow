"""
Tests for document_debate_cli.py custom prompt functionality.

Tests verify:
- CLI argument parsing works correctly
- File validation functions properly
- Custom prompts are passed to state
- Backward compatibility is maintained
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock
from document_debate_cli import validate_prompt_file, main


def test_validate_prompt_file_missing():
    """Test validation fails for missing file."""
    is_valid, error = validate_prompt_file("nonexistent.txt")
    assert not is_valid
    assert "not found" in error.lower()


def test_validate_prompt_file_empty(tmp_path):
    """Test validation fails for empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    is_valid, error = validate_prompt_file(str(empty_file))
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_prompt_file_too_large(tmp_path):
    """Test validation fails for file exceeding 5000 characters."""
    large_file = tmp_path / "large.txt"
    large_file.write_text("x" * 5001)
    is_valid, error = validate_prompt_file(str(large_file))
    assert not is_valid
    assert "too large" in error.lower()


def test_validate_prompt_file_valid(tmp_path):
    """Test validation succeeds for valid file."""
    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("You are a TPM advocating for funding.")
    is_valid, content = validate_prompt_file(str(valid_file))
    assert is_valid
    assert content == "You are a TPM advocating for funding."


def test_validate_prompt_file_with_special_chars(tmp_path):
    """Test validation handles special characters."""
    valid_file = tmp_path / "special.txt"
    valid_file.write_text("Test: Привет! 你好！")
    is_valid, content = validate_prompt_file(str(valid_file))
    assert is_valid
    assert "Привет" in content


def test_backward_compatibility_default_behavior():
    """Test that CLI works without custom prompts (default behavior)."""
    # Test with --text only (no custom prompts)
    with patch('sys.argv', ['document_debate_cli.py', '--text', 'GitHub полезен для разработчиков']):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={
                "messages": [{"content": "Test verdict"}]
            })
            # Should not raise errors
            main()
            # Verify workflow was called with correct state
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']

            # Verify no custom prompts in state
            assert initial_state.get('pro_custom_prompt') is None
            assert initial_state.get('con_custom_prompt') is None


def test_cli_with_pro_prompt_only(tmp_path):
    """Test CLI with only PRO custom prompt."""
    # Create a valid PRO prompt file
    pro_file = tmp_path / "pro_prompt.txt"
    pro_file.write_text("You are a TPM advocating for project funding.")

    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--pro-prompt', str(pro_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={
                "messages": [{"content": "Test verdict"}]
            })
            main()
            # Verify state has pro_custom_prompt
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']
            assert initial_state.get('pro_custom_prompt') == "You are a TPM advocating for project funding."
            assert initial_state.get('con_custom_prompt') is None


def test_cli_with_con_prompt_only(tmp_path):
    """Test CLI with only CON custom prompt."""
    # Create a valid CON prompt file
    con_file = tmp_path / "con_prompt.txt"
    con_file.write_text("You are a CPO evaluating resource allocation.")

    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--con-prompt', str(con_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={
                "messages": [{"content": "Test verdict"}]
            })
            main()
            # Verify state has con_custom_prompt
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']
            assert initial_state.get('con_custom_prompt') == "You are a CPO evaluating resource allocation."
            assert initial_state.get('pro_custom_prompt') is None


def test_cli_with_both_custom_prompts(tmp_path):
    """Test CLI with both PRO and CON custom prompts."""
    # Create valid prompt files
    pro_file = tmp_path / "pro_prompt.txt"
    pro_file.write_text("You are a TPM advocating for funding.")
    con_file = tmp_path / "con_prompt.txt"
    con_file.write_text("You are a CPO evaluating resources.")

    with patch('sys.argv', [
        'document_debate_cli.py',
        '--text', 'Test topic',
        '--pro-prompt', str(pro_file),
        '--con-prompt', str(con_file)
    ]):
        with patch('document_debate_cli.DocumentDebateWorkflow') as mock_workflow:
            mock_workflow.return_value.run = MagicMock(return_value={
                "messages": [{"content": "Test verdict"}]
            })
            main()
            # Verify state has both custom prompts
            call_args = mock_workflow.return_value.run.call_args
            initial_state = call_args[1]['initial_state']
            assert initial_state.get('pro_custom_prompt') == "You are a TPM advocating for funding."
            assert initial_state.get('con_custom_prompt') == "You are a CPO evaluating resource allocation."
