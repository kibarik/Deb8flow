"""
Domain entities for rewrite feature.

Entities represent core domain concepts with identity.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from .value_objects import RevisionAction, RewriteStatus


@dataclass
class RevisionItem:
    """
    A single revision item extracted from conclusion.md.

    Represents one actionable change to be applied to a document.
    Each revision has a unique identity (id) and tracks whether
    it has been verified by the debate process.

    Attributes:
        id: Unique identifier (auto-generated sequence, e.g., "REV001")
        content: Full text of the revision/recommendation
        section: Target section reference (e.g., "CPO", "general")
        action: Type of revision to apply (default: UPDATE)
        context: Optional surrounding context for locating target
        verified: Whether debate confirmed this revision (default: False)
    """
    id: str
    content: str
    section: str
    action: RevisionAction = RevisionAction.UPDATE
    context: Optional[str] = None
    verified: bool = False

    def __post_init__(self):
        """Validate revision item after initialization."""
        if not self.id:
            raise ValueError("RevisionItem.id cannot be empty")
        if not self.content or not self.content.strip():
            raise ValueError("RevisionItem.content cannot be empty")
        if not self.section or not self.section.strip():
            raise ValueError("RevisionItem.section cannot be empty")

    def mark_verified(self) -> None:
        """Mark this revision as verified by debate."""
        self.verified = True

    def mark_unverified(self) -> None:
        """Mark this revision as unverified (for re-verification)."""
        self.verified = False

    @property
    def display_text(self) -> str:
        """Get a human-readable representation of this revision."""
        status = "✓" if self.verified else "✗"
        return f"{status} [{self.id}] {self.content[:50]}..."


@dataclass(frozen=True)
class RewriteResult:
    """
    Immutable result of a rewrite operation.

    Contains complete information about what was done during
    the rewrite process, including counts and lists of revisions.

    Attributes:
        status: Final status of the operation
        revisions_applied: Number of revisions applied to document
        revisions_verified: Number of revisions verified by debate
        revisions_total: Total number of revisions in conclusion
        unverified: List of revisions not verified (immutable copy)
        rounds_completed: Number of debate rounds executed
        backup_path: Path to backup file created (None if --no-backup)
        source_path: Original source document path
        output_path: Final output document path
    """
    status: RewriteStatus
    revisions_applied: int
    revisions_verified: int
    revisions_total: int
    unverified: tuple[RevisionItem, ...]  # Use tuple for immutability
    rounds_completed: int
    backup_path: Optional[Path]
    source_path: Path
    output_path: Path

    def __post_init__(self):
        """Validate rewrite result invariants."""
        # Validate count relationships
        if not (0 <= self.revisions_verified <= self.revisions_applied <= self.revisions_total):
            raise ValueError(
                f"Invalid revision counts: "
                f"verified({self.revisions_verified}) <= "
                f"applied({self.revisions_applied}) <= "
                f"total({self.revisions_total})"
            )

        # Validate status matches counts
        if self.status == RewriteStatus.SUCCESS and self.revisions_verified != self.revisions_total:
            raise ValueError("SUCCESS status requires all revisions verified")
        if self.status == RewriteStatus.PARTIAL and self.revisions_applied == 0:
            raise ValueError("PARTIAL status requires at least one revision applied")
        if self.status == RewriteStatus.FAILED and self.revisions_applied > 0:
            raise ValueError("FAILED status requires no revisions applied")

    @property
    def is_complete(self) -> bool:
        """Check if all revisions were verified."""
        return self.status == RewriteStatus.SUCCESS

    @property
    def is_partial(self) -> bool:
        """Check if some revisions were not verified."""
        return self.status == RewriteStatus.PARTIAL

    @property
    def verification_rate(self) -> float:
        """Get the rate of verified revisions (0.0 to 1.0)."""
        if self.revisions_total == 0:
            return 1.0
        return self.revisions_verified / self.revisions_total

    @property
    def unverified_count(self) -> int:
        """Get the number of unverified revisions."""
        return len(self.unverified)

    def get_summary(self) -> str:
        """Get a human-readable summary of the result."""
        if self.is_complete:
            return f"Complete: All {self.revisions_total} revisions verified"
        elif self.is_partial:
            return (
                f"Partial: {self.revisions_verified}/{self.revisions_total} verified, "
                f"{self.unverified_count} unverified"
            )
        else:
            return f"Failed: No revisions could be applied"
