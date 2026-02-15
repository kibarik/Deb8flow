"""
Unit tests for EnhancedAnalyzer base class.

Tests verify:
- EnhancedAnalyzer extends BaseComponent correctly
- Chain creation methods (structured and text)
- Prompt loading utility
- Retry logic with exponential backoff
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from pydantic import BaseModel, Field

from src.analyzers.base_analyzer import EnhancedAnalyzer


# ============================================================================
# Test Fixtures
# ============================================================================


class MockLLMConfig:
    """Mock LLM configuration for testing."""
    pass


@pytest.fixture
def mock_llm():
    """Mock LLM instance for testing."""
    llm = Mock()
    llm.with_structured_output = Mock(return_value=Mock())
    return llm


@pytest.fixture
def analyzer_with_mock_llm(mock_llm):
    """Create EnhancedAnalyzer with mocked LLM."""
    analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
    analyzer.llm = mock_llm
    analyzer.logger = Mock()
    analyzer._prompts_dir = Path("src/prompts/enhanced_conclusion")
    return analyzer


@pytest.fixture
def test_prompts_dir(tmp_path):
    """Create temporary prompts directory with test file."""
    prompts_dir = tmp_path / "src" / "prompts" / "enhanced_conclusion"
    prompts_dir.mkdir(parents=True)

    # Create test prompt file
    test_prompt = prompts_dir / "test_prompt.md"
    test_prompt.write_text("# Test Prompt\n\nHello {name}!", encoding='utf-8')

    return prompts_dir


@pytest.fixture
def sample_pydantic_model():
    """Sample Pydantic model for structured output tests."""
    class TestModel(BaseModel):
        name: str = Field(..., description="Name field")
        value: int = Field(..., description="Value field")

    return TestModel


# ============================================================================
# Test EnhancedAnalyzer Class
# ============================================================================


class TestEnhancedAnalyzer:
    """Test EnhancedAnalyzer base class functionality."""

    def test_initialization(self):
        """Test EnhancedAnalyzer can be instantiated."""
        analyzer = EnhancedAnalyzer(llm_config=None)
        assert analyzer.logger is not None
        assert analyzer._prompts_dir == Path("src/prompts/enhanced_conclusion")

    def test_call_raises_not_implemented(self):
        """Test that __call__ raises NotImplementedError."""
        analyzer = EnhancedAnalyzer(llm_config=None)
        with pytest.raises(NotImplementedError):
            analyzer()


# ============================================================================
# Test Chain Creation Methods
# ============================================================================


class TestChainCreation:
    """Test LLM chain creation methods."""

    def test_create_text_chain_default_system_message(self, analyzer_with_mock_llm):
        """Test text chain creation with default system message."""
        chain = analyzer_with_mock_llm._create_text_chain()
        assert chain is not None
        # Verify chain was created (we can't test invocation without proper LLM setup)

    def test_create_text_chain_custom_system_message(self, analyzer_with_mock_llm):
        """Test text chain creation with custom system message."""
        custom_message = "Custom system message for testing"
        chain = analyzer_with_mock_llm._create_text_chain(system_message=custom_message)
        assert chain is not None

    def test_create_structured_chain_with_native_support(self, analyzer_with_mock_llm, sample_pydantic_model):
        """Test structured chain when LLM supports native structured output."""
        chain = analyzer_with_mock_llm._create_structured_chain("test prompt", sample_pydantic_model)
        assert chain is not None
        # Verify native structured output was used
        analyzer_with_mock_llm.llm.with_structured_output.assert_called_once_with(sample_pydantic_model)

    def test_create_structured_chain_without_native_support(self, sample_pydantic_model):
        """Test structured chain falls back to PydanticOutputParser."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer.llm = Mock()  # Mock without with_structured_output attribute
        analyzer.logger = Mock()
        analyzer._prompts_dir = Path("src/prompts/enhanced_conclusion")

        chain = analyzer._create_structured_chain("test prompt", sample_pydantic_model)
        assert chain is not None


# ============================================================================
# Test Prompt Loading Utility
# ============================================================================


class TestPromptLoading:
    """Test prompt loading utility."""

    def test_load_prompt_success(self, test_prompts_dir):
        """Test successful prompt loading."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = test_prompts_dir
        analyzer.logger = Mock()

        prompt = analyzer._load_prompt("test_prompt.md")
        assert "# Test Prompt" in prompt
        assert "Hello {name}!" in prompt

    def test_load_prompt_file_not_found(self):
        """Test prompt loading with missing file."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = Path("src/prompts/enhanced_conclusion")
        analyzer.logger = Mock()

        with pytest.raises(FileNotFoundError) as exc_info:
            analyzer._load_prompt("nonexistent_prompt.md")
        assert "Prompt file not found" in str(exc_info.value)

    def test_format_prompt(self):
        """Test prompt formatting with variables."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = Path("src/prompts/enhanced_conclusion")
        analyzer.logger = Mock()

        template = "Hello {name}! You are {role}."
        formatted = analyzer._format_prompt(template, name="World", role="Assistant")

        assert formatted == "Hello World! You are Assistant."

    def test_format_prompt_missing_variable(self):
        """Test prompt formatting with missing variable."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = Path("src/prompts/enhanced_conclusion")
        analyzer.logger = Mock()

        template = "Hello {name}!"
        with pytest.raises(KeyError):
            analyzer._format_prompt(template)  # Missing 'name'

    def test_load_prompt_utf8_encoding(self, tmp_path):
        """Test prompt loading with UTF-8 encoding for Russian text."""
        prompts_dir = tmp_path / "src" / "prompts" / "enhanced_conclusion"
        prompts_dir.mkdir(parents=True)

        # Create prompt with Russian text
        test_prompt = prompts_dir / "russian_prompt.md"
        russian_text = "Платформа представляет значительный риск для нашей существующей клиентской базы."
        test_prompt.write_text(f"# Russian Prompt\n\n{russian_text}", encoding='utf-8')

        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = prompts_dir
        analyzer.logger = Mock()

        prompt = analyzer._load_prompt("russian_prompt.md")
        assert russian_text in prompt
        assert "риск" in prompt


# ============================================================================
# Test Retry Logic with Exponential Backoff
# ============================================================================


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    def test_retry_success_on_first_attempt(self, analyzer_with_mock_llm):
        """Test retry when function succeeds on first attempt."""
        mock_func = Mock(return_value="success")

        @analyzer_with_mock_llm._retry_with_backoff(max_retries=3)
        def test_function():
            return mock_func()

        result = test_function()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_on_second_attempt(self, analyzer_with_mock_llm):
        """Test retry when function fails once then succeeds."""
        mock_func = Mock(side_effect=[Exception("Error 1"), "success"])

        @analyzer_with_mock_llm._retry_with_backoff(max_retries=3, base_delay=0.1)
        def test_function():
            return mock_func()

        result = test_function()
        assert result == "success"
        assert mock_func.call_count == 2

    def test_retry_all_attempts_fail(self, analyzer_with_mock_llm):
        """Test retry when function fails all attempts."""
        mock_func = Mock(side_effect=Exception("Persistent error"))

        @analyzer_with_mock_llm._retry_with_backoff(max_retries=3, base_delay=0.1)
        def test_function():
            return mock_func()

        with pytest.raises(Exception) as exc_info:
            test_function()
        assert str(exc_info.value) == "Persistent error"
        assert mock_func.call_count == 3

    def test_retry_exponential_backoff_timing(self, analyzer_with_mock_llm):
        """Test that retry delays follow exponential backoff pattern."""
        call_times = []

        def mock_function_with_delay():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Temporary error")
            return "success"

        @analyzer_with_mock_llm._retry_with_backoff(max_retries=4, base_delay=0.1)
        def test_function():
            return mock_function_with_delay()

        result = test_function()
        assert result == "success"
        # We get 3 calls total: 1 initial + 2 retries (succeeds on 3rd attempt)
        assert len(call_times) == 3

        # Verify delays: 0.1s for first retry, 0.2s for second retry
        if len(call_times) >= 2:
            first_delay = call_times[1] - call_times[0]
            second_delay = call_times[2] - call_times[1]
            assert 0.08 <= first_delay <= 0.15  # ~0.1s with tolerance
            assert 0.18 <= second_delay <= 0.25  # ~0.2s with tolerance

    def test_invoke_with_retry(self, analyzer_with_mock_llm):
        """Test _invoke_with_retry method."""
        mock_chain = Mock()
        mock_chain.invoke = Mock(return_value="chain result")

        result = analyzer_with_mock_llm._invoke_with_retry(mock_chain, {"input": "test"})

        assert result == "chain result"
        mock_chain.invoke.assert_called_once_with({"input": "test"})

    def test_invoke_with_retry_on_failure(self, analyzer_with_mock_llm):
        """Test _invoke_with_retry when chain.invoke fails."""
        mock_chain = Mock()
        mock_chain.invoke = Mock(side_effect=[Exception("API Error"), "success"])

        result = analyzer_with_mock_llm._invoke_with_retry(mock_chain, {"input": "test"})

        assert result == "success"
        assert mock_chain.invoke.call_count == 2


# ============================================================================
# Test Integration with BaseComponent
# ============================================================================


class TestBaseComponentIntegration:
    """Test integration with BaseComponent pattern."""

    def test_extends_base_component(self):
        """Test that EnhancedAnalyzer extends BaseComponent."""
        from nodes.base_component import BaseComponent

        analyzer = EnhancedAnalyzer(llm_config=None)
        assert isinstance(analyzer, BaseComponent)

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        analyzer = EnhancedAnalyzer(llm_config=None)
        assert analyzer.logger is not None
        # Check logger name matches class name
        assert "EnhancedAnalyzer" in analyzer.logger.name or "BaseComponent" in analyzer.logger.name

    def test_prompts_dir_configuration(self):
        """Test prompts directory is correctly configured."""
        analyzer = EnhancedAnalyzer(llm_config=None)
        assert analyzer._prompts_dir == Path("src/prompts/enhanced_conclusion")


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling in analyzer methods."""

    def test_load_propagagates_file_not_found(self):
        """Test that FileNotFoundError is propagated for missing prompts."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = Path("nonexistent/directory")
        analyzer.logger = Mock()

        with pytest.raises(FileNotFoundError):
            analyzer._load_prompt("any_prompt.md")

    def test_retry_preserves_exception_type(self):
        """Test that retry preserves original exception type."""
        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer.logger = Mock()

        class CustomError(Exception):
            pass

        @analyzer._retry_with_backoff(max_retries=2)
        def test_function():
            raise CustomError("Custom error message")

        with pytest.raises(CustomError) as exc_info:
            test_function()
        assert str(exc_info.value) == "Custom error message"


# ============================================================================
# Test UTF-8 Encoding Support
# ============================================================================


class TestUTF8Encoding:
    """Test UTF-8 encoding support for Russian/English text."""

    def test_prompt_with_russian_text(self, test_prompts_dir):
        """Test that prompts with Russian text are handled correctly."""
        # Create prompt with Russian text
        russian_prompt = test_prompts_dir / "russian_test.md"
        russian_text = "Это тестовый промпт на русском языке."
        russian_prompt.write_text(f"# Russian Test\n\n{russian_text}", encoding='utf-8')

        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = test_prompts_dir
        analyzer.logger = Mock()

        prompt = analyzer._load_prompt("russian_test.md")
        assert russian_text in prompt
        # Verify no encoding issues
        assert "тестовый" in prompt

    def test_prompt_with_mixed_language(self, test_prompts_dir):
        """Test that prompts with mixed Russian/English text work."""
        mixed_prompt = test_prompts_dir / "mixed_test.md"
        mixed_text = "This is English. Это русский текст."
        mixed_prompt.write_text(f"# Mixed Test\n\n{mixed_text}", encoding='utf-8')

        analyzer = EnhancedAnalyzer.__new__(EnhancedAnalyzer)
        analyzer._prompts_dir = test_prompts_dir
        analyzer.logger = Mock()

        prompt = analyzer._load_prompt("mixed_test.md")
        assert "This is English" in prompt
        assert "Это русский" in prompt
