"""
LLM infrastructure for debate execution.

This package provides AI-powered debate orchestration using
LangChain and OpenAI-compatible APIs.
"""

from .debate_orchestrator import (
    LLMDebateOrchestrator,
    SimpleDebateOrchestrator,
    DebateMessage
)

__all__ = [
    "LLMDebateOrchestrator",
    "SimpleDebateOrchestrator",
    "DebateMessage"
]
