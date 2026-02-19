"""Factory for creating debate orchestrators."""

import logging
from typing import Optional, Union

from .debate_orchestrator import SimpleDebateOrchestrator
from .standard_orchestrator import StandardDebateOrchestrator
from ...application.prompt_loader import PromptLoader
from ...domain.entities import DebateMode


logger = logging.getLogger(__name__)


class DebateOrchestratorFactory:
    """
    Factory for creating debate orchestrators based on mode.

    This factory centralizes orchestrator creation logic and ensures
    consistent initialization across the application.
    """

    @staticmethod
    def create(
        mode: DebateMode,
        prompt_loader: Optional[PromptLoader] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en"
    ):
        """
        Create a debate orchestrator based on the specified mode.

        Args:
            mode: Debate mode (standard or simple)
            prompt_loader: PromptLoader for loading prompts (optional)
            model: LLM model name
            temperature: Sampling temperature
            api_key: API key for LLM
            base_url: Base URL for LLM API
            language: Output language

        Returns:
            Configured orchestrator instance

        Raises:
            ValueError: If mode is invalid
        """
        logger.info(f"Creating {mode.value} debate orchestrator")

        if mode == DebateMode.STANDARD:
            return StandardDebateOrchestrator(
                prompt_loader=prompt_loader,
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url,
                language=language
            )
        elif mode == DebateMode.SIMPLE:
            return SimpleDebateOrchestrator(
                prompt_loader=prompt_loader,
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url,
                language=language
            )
        else:
            raise ValueError(f"Unsupported debate mode: {mode}")


def create_orchestrator(
    mode: Union[str, DebateMode],
    prompt_loader: Optional[PromptLoader] = None,
    **kwargs
):
    """
    Convenience function for creating orchestrators.

    Args:
        mode: Debate mode as string or DebateMode enum
        prompt_loader: PromptLoader instance (optional)
        **kwargs: Additional arguments passed to orchestrator

    Returns:
        Configured orchestrator instance
    """
    # Convert string to enum if needed
    if isinstance(mode, str):
        mode = DebateMode.from_string(mode)

    return DebateOrchestratorFactory.create(mode, prompt_loader, **kwargs)
