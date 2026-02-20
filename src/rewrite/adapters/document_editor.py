"""
Document editor for applying revisions to source documents.

Supports markdown (section-based) and text (keyword-based) editing.
"""
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod

from ..domain.entities import RevisionItem
from ..domain.value_objects import DocumentType, RevisionAction


logger = logging.getLogger(__name__)


class BaseEditor(ABC):
    """Abstract base for document editors."""

    @abstractmethod
    def apply_revision(self, content: str, revision: RevisionItem) -> str:
        """Apply a single revision to document content."""
        pass

    @abstractmethod
    def find_target_location(self, content: str, revision: RevisionItem) -> int:
        """Find the character position to apply revision."""
        pass


class MarkdownEditor(BaseEditor):
    """
    Editor for markdown files with section-based editing.

    Parses markdown into sections based on headers (##, ###).
    Matches revisions to sections by name similarity or keywords.
    """

    # Header patterns
    SECTION_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def __init__(self):
        """Initialize markdown editor."""
        self.sections: List[Tuple[str, str, int, int]] = []  # (level, title, start, end)

    def parse_sections(self, content: str) -> None:
        """
        Parse markdown content into sections.

        Populates self.sections with tuples of (level, title, start_pos, end_pos).

        Args:
            content: Full markdown document content
        """
        self.sections = []
        matches = list(self.SECTION_PATTERN.finditer(content))

        if not matches:
            # No sections found, treat entire content as one section
            self.sections.append(("0", "root", 0, len(content)))
            return

        # Add section from start to first header
        if matches[0].start() > 0:
            self.sections.append(("0", "root", 0, matches[0].start()))

        # Add each section
        for i, match in enumerate(matches):
            level, title = match.groups()
            start = match.end() + 1  # Start after header line
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            self.sections.append((str(len(level)), title.strip(), start, end))

    def match_section_score(self, section_name: str, title: str) -> float:
        """
        Calculate similarity score between section name and title.

        Returns 0.0 to 1.0, where 1.0 is exact match.

        Args:
            section_name: Target section name from revision
            title: Actual section title from document

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Exact match
        if section_name.lower() == title.lower():
            return 1.0

        # Contains match
        if section_name.lower() in title.lower() or title.lower() in section_name.lower():
            return 0.8

        # Word overlap (Jaccard similarity)
        s_words = set(section_name.lower().split())
        t_words = set(title.lower().split())
        if s_words and t_words:
            intersection = s_words & t_words
            union = s_words | t_words
            return len(intersection) / len(union)

        return 0.0

    def find_best_section(self, content: str, section_name: str) -> Optional[Tuple[int, int]]:
        """
        Find the best matching section using similarity scoring.

        Returns section with highest score above threshold (0.5).

        Args:
            content: Full document content
            section_name: Target section name

        Returns:
            Tuple of (start_pos, end_pos) or None if no good match
        """
        self.parse_sections(content)

        best_match = None
        best_score = 0.0
        best_title = ""

        for level, title, start, end in self.sections:
            score = self.match_section_score(section_name, title)
            if score > best_score:
                best_score = score
                best_match = (start, end)
                best_title = title

        # Only return if match is good enough
        if best_score >= 0.5:
            if best_score < 1.0:
                logger.info(f"Section '{section_name}' matched to '{best_title}' with score {best_score:.2f}")
            return best_match

        return None

    def find_section(self, content: str, section_name: str) -> Optional[Tuple[int, int]]:
        """
        Find a section by name with fuzzy matching.

        Args:
            content: Full document content
            section_name: Name of section to find

        Returns:
            Tuple of (start_pos, end_pos) or None if not found
        """
        return self.find_best_section(content, section_name)

    def find_target_location(self, content: str, revision: RevisionItem) -> int:
        """Find the character position to apply revision."""
        section = self.find_section(content, revision.section)
        if section:
            return section[0]  # Insert at start of section
        return len(content)  # Append to end if section not found

    def _insert_content(self, content: str, new_content: str, pos: int) -> str:
        """Insert content at position."""
        return content[:pos] + "\n" + new_content + "\n" + content[pos:]

    def _update_content(self, content: str, revision: RevisionItem, pos: int) -> str:
        """Update content by finding and replacing matching text."""
        section_range = self.find_section(content, revision.section)
        if not section_range:
            # Fallback to insert
            return self._insert_content(content, revision.content, pos)

        start, end = section_range
        section_content = content[start:end]

        # Try to find similar text to replace
        words = revision.content.split()[:3]  # First 3 words
        pattern = re.compile(re.escape(' '.join(words)), re.IGNORECASE)
        match = pattern.search(section_content)

        if match:
            # Replace matched portion
            new_section = section_content[:match.start()] + revision.content + section_content[match.end():]
            return content[:start] + new_section + content[end:]

        # If no match, append to section
        return content[:end] + "\n" + revision.content + content[end:]

    def _delete_content(self, content: str, revision: RevisionItem) -> str:
        """Delete content matching revision."""
        # Find and remove matching paragraph
        section_range = self.find_section(content, revision.section)
        if not section_range:
            return content

        start, end = section_range
        section_content = content[start:end]

        # Try to find and remove matching paragraph
        lines = section_content.split('\n')
        for i, line in enumerate(lines):
            if revision.content.lower() in line.lower():
                # Remove this line
                lines.pop(i)
                break

        new_section = '\n'.join(lines)
        return content[:start] + new_section + content[end:]

    def apply_revision(self, content: str, revision: RevisionItem) -> str:
        """
        Apply revision to markdown content with validation.

        Args:
            content: Original document content
            revision: Revision to apply

        Returns:
            Modified content

        Raises:
            ValueError: If revision cannot be applied
        """
        try:
            if revision.action == RevisionAction.DELETE:
                new_content = self._delete_content(content, revision)
            elif revision.action == RevisionAction.INSERT:
                pos = self.find_target_location(content, revision)
                new_content = self._insert_content(content, revision.content, pos)
            elif revision.action == RevisionAction.UPDATE:
                new_content = self._update_content(content, revision, self.find_target_location(content, revision))
            else:
                logger.warning(f"Unknown action {revision.action}, skipping")
                return content

            # Validate result is not empty
            if not new_content or not new_content.strip():
                logger.warning(f"Revision {revision.id} resulted in empty content, skipping")
                return content

            return new_content

        except Exception as e:
            logger.error(f"Failed to apply revision {revision.id}: {e}")
            return content  # Return original on error


class TextEditor(BaseEditor):
    """
    Editor for plain text files with keyword-based location.

    Finds insertion points using keyword matching and context hints.
    """

    def find_target_location(self, content: str, revision: RevisionItem) -> int:
        """
        Find target location using keyword matching.

        Args:
            content: Full document content
            revision: Revision with section/context as keywords

        Returns:
            Character position for insertion
        """
        keywords = [revision.section]
        if revision.context:
            keywords.append(revision.context)

        # Try each keyword
        for keyword in keywords:
            pos = content.find(keyword)
            if pos != -1:
                # Insert after the keyword line
                line_end = content.find('\n', pos)
                if line_end != -1:
                    return line_end + 1
                return pos + len(keyword)

        # Fallback: append to end
        return len(content)

    def apply_revision(self, content: str, revision: RevisionItem) -> str:
        """Apply revision to text content."""
        pos = self.find_target_location(content, revision)

        if revision.action == RevisionAction.DELETE:
            # Find and remove line containing keyword
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if revision.section.lower() in line.lower():
                    lines.pop(i)
                    break
            return '\n'.join(lines)

        elif revision.action == RevisionAction.INSERT:
            return content[:pos] + revision.content + '\n' + content[pos:]

        elif revision.action == RevisionAction.UPDATE:
            # Find line with keyword and replace
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if revision.section.lower() in line.lower():
                    lines[i] = revision.content
                    break
            return '\n'.join(lines)

        return content


def create_editor(doc_type: DocumentType) -> BaseEditor:
    """
    Factory function to create appropriate editor for document type.

    Args:
        doc_type: Type of document to edit

    Returns:
        Appropriate editor instance

    Raises:
        ValueError: If document type not supported
    """
    if doc_type == DocumentType.MARKDOWN:
        return MarkdownEditor()
    elif doc_type == DocumentType.TEXT:
        return TextEditor()
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
