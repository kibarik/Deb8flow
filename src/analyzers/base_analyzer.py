"""
Base analyzer for enhanced conclusion pipeline.

This module provides the EnhancedAnalyzer base class that extends BaseComponent
with additional utilities for the two-stage enhanced conclusion pipeline:

- LLM chain creation methods for structured and unstructured output
- Prompt loading utility for markdown prompts
- Retry logic with exponential backoff for reliability

Example:
    >>> from src.analyzers.base_analyzer import EnhancedAnalyzer
    >>> analyzer = EnhancedAnalyzer(llm_config)
    >>> chain = analyzer._create_text_chain()
"""

import logging
import time
from functools import wraps
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import from project structure
from nodes.base_component import BaseComponent

__all__ = ["EnhancedAnalyzer"]

T = TypeVar('T', bound=object)


class EnhancedAnalyzer(BaseComponent):
    """Base class for enhanced conclusion analyzers.

    Provides LLM chain creation, prompt loading, and retry logic
    for the two-stage enhanced conclusion pipeline.

    Extends BaseComponent to maintain consistency with existing debate nodes.

    Attributes:
        logger: Logger instance for tracking operations
        _prompts_dir: Path to prompts directory

    Example:
        >>> analyzer = EnhancedAnalyzer(llm_config)
        >>> chain = analyzer._create_text_chain()
    """

    def __init__(self, llm_config=None):
        """Initialize the enhanced analyzer.

        Args:
            llm_config: LLM configuration (optional, inherited from BaseComponent)
        """
        super().__init__(llm_config)
        self._prompts_dir = Path("src/prompts/enhanced_conclusion")

    def __call__(self, *args, **kwargs):
        """Subclasses must implement __call__ method.

        Raises:
            NotImplementedError: Always - subclasses must implement
        """
        raise NotImplementedError("Subclasses must implement __call__")

    def _create_structured_chain(self, prompt_template: str, output_model: Type[T]):
        """Create chain for structured (Pydantic) output.

        Checks if LLM supports native structured output (OpenAI).
        Falls back to PydanticOutputParser for other LLMs.

        Args:
            prompt_template: Prompt template string
            output_model: Pydantic model for structured output

        Returns:
            LangChain chain that produces structured output

        Example:
            >>> chain = analyzer._create_structured_chain(prompt, Verdict)
            >>> result = chain.invoke({"input": "data"})
        """
        from langchain.output_parsers import PydanticOutputParser

        # Check if LLM supports structured output
        if hasattr(self.llm, 'with_structured_output'):
            # OpenAI supports native structured output
            structured_llm = self.llm.with_structured_output(output_model)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a debate analyst. Follow instructions precisely."),
                ("human", "{input}")
            ])
            return prompt | structured_llm
        else:
            # Fallback: use PydanticOutputParser
            parser = PydanticOutputParser(pydantic_object=output_model)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a debate analyst. Output ONLY valid JSON."),
                ("human", "{format_instructions}\n\n{input}")
            ])
            return prompt | self.llm | parser

    def _create_text_chain(self, system_message: str = None):
        """Create chain for unstructured (text) output.

        Args:
            system_message: Optional custom system message
                Defaults to JSON output instruction

        Returns:
            LangChain chain that produces text output

        Example:
            >>> chain = analyzer._create_text_chain()
            >>> result = chain.invoke({"input": "data"})
        """
        system_msg = system_message or "You are a debate analyst. Output ONLY valid JSON, no markdown."
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "{input}")
        ])
        return prompt | self.llm | StrOutputParser()

    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from markdown file.

        Args:
            prompt_name: Name of prompt file (e.g., 'verdict_extraction_prompt.md')

        Returns:
            Prompt template as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist

        Example:
            >>> prompt = analyzer._load_prompt('verdict_extraction_prompt.md')
        """
        prompt_path = self._prompts_dir / prompt_name

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        # Read with UTF-8 encoding for Russian/English support
        return prompt_path.read_text(encoding='utf-8')

    def _format_prompt(self, prompt_template: str, **kwargs) -> str:
        """Format prompt template with variables.

        Args:
            prompt_template: Prompt template string
            **kwargs: Variables to substitute

        Returns:
            Formatted prompt string

        Example:
            >>> formatted = analyzer._format_prompt(
            ...     "Hello {name}",
            ...     name="World"
            ... )
        """
        return prompt_template.format(**kwargs)

    def _invoke_with_retry(self, chain, input_data: Dict[str, Any]):
        """Invoke chain with retry logic and exponential backoff.

        Args:
            chain: LangChain chain to invoke
            input_data: Input data for the chain

        Returns:
            Chain output

        Raises:
            Exception: Last exception after all retries exhausted

        Example:
            >>> result = analyzer._invoke_with_retry(chain, {"input": "data"})
        """
        return self._retry_with_backoff()(chain.invoke)(input_data)

    def _retry_with_backoff(self, max_retries=3, base_delay=1.0):
        """Create retry decorator with exponential backoff.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (doubled each retry)

        Returns:
            Decorator function

        Example:
            >>> @analyzer._retry_with_backoff(max_retries=3)
            >>> def my_function():
            ...     return risky_operation()
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed: {e}. "
                                f"Retrying in {delay}s..."
                            )
                            time.sleep(delay)
                        else:
                            self.logger.error(
                                f"All {max_retries} attempts failed: {e}"
                            )
                raise last_exception
            return wrapper
        return decorator
