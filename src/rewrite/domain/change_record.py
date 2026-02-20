"""
Change tracking domain entities.

Records the before/after state of each applied revision.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChangeRecord:
    """
    Record of a single change applied to a document.

    Captures the before/after state for review purposes.

    Attributes:
        revision_id: ID of the revision that was applied
        section: Section where change was applied
        action: Action type (INSERT/UPDATE/DELETE)
        before: Original content (empty for INSERT)
        after: New content (empty for DELETE)
        line_number: Optional line number where change occurred
        context_lines: Optional context lines around the change
    """
    revision_id: str
    section: str
    action: str
    before: str
    after: str
    line_number: Optional[int] = None
    context_lines: Optional[tuple[str, ...]] = None

    @property
    def display_before(self) -> str:
        """Get before content for display (truncated if needed)."""
        if not self.before:
            return "(empty)"
        if len(self.before) > 200:
            return self.before[:200] + "..."
        return self.before

    @property
    def display_after(self) -> str:
        """Get after content for display (truncated if needed)."""
        if not self.after:
            return "(empty)"
        if len(self.after) > 200:
            return self.after[:200] + "..."
        return self.after

    def to_markdown(self) -> str:
        """Convert change record to markdown format for review."""
        lines = [
            f"### Задание {self.revision_id}",
            f"**Секция:** `{self.section}`",
            f"**Действие:** {self.action}",
            ""
        ]

        if self.line_number:
            lines.append(f"**Строка:** {self.line_number}")
            lines.append("")

        lines.append("**Было:**")
        lines.append("```")
        lines.append(self.display_before)
        lines.append("```")
        lines.append("")

        lines.append("**Стало:**")
        lines.append("```")
        lines.append(self.display_after)
        lines.append("```")

        if self.context_lines:
            lines.append("")
            lines.append("**Контекст:**")
            for ctx in self.context_lines:
                lines.append(f"  {ctx}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)
