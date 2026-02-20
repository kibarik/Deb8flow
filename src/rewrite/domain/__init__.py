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

__all__ = [
    # Entities
    "RevisionItem",
    "RewriteResult",
    # Value objects
    "RevisionAction",
    "RewriteStatus",
    "DocumentType",
    "RewriteConfig",
]
