"""
Domain layer for rewrite feature.

Contains entities and value objects that define the core domain model.
"""
from .entities import RevisionItem, RewriteResult
from .value_objects import (
    RevisionAction,
    RewriteStatus,
    DocumentType,
    RewriteConfig
)
from .review_config import (
    ReviewConfig,
    LLMConfig,
    PromptConfig,
    RetryConfig,
    CheckConfig,
    OutputConfig,
    ContextConfig,
    LoggingConfig,
    deep_merge,
    substitute_placeholders,
)

__all__ = [
    # Entities
    "RevisionItem",
    "RewriteResult",
    # Value objects from value_objects.py
    "RevisionAction",
    "RewriteStatus",
    "DocumentType",
    "RewriteConfig",
    # Value objects from review_config.py
    "ReviewConfig",
    "LLMConfig",
    "PromptConfig",
    "RetryConfig",
    "CheckConfig",
    "OutputConfig",
    "ContextConfig",
    "LoggingConfig",
    # Helper functions
    "deep_merge",
    "substitute_placeholders",
]
