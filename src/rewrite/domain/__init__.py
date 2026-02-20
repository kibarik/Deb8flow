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
from .change_record import ChangeRecord

__all__ = [
    # Entities
    "RevisionItem",
    "RewriteResult",
    # Change tracking
    "ChangeRecord",
    # Value objects
    "RevisionAction",
    "RewriteStatus",
    "DocumentType",
    "RewriteConfig",
]
