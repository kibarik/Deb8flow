"""
Document editor for applying revisions to source documents.

Supports markdown (section-based), text (keyword-based), and DOCX editing.
"""
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from docx import Document
from docx.shared import Pt

from ..domain.entities import RevisionItem
from ..domain.value_objects import DocumentType, RevisionAction
from ..domain.change_record import ChangeRecord


logger = logging.getLogger(__name__)


class BaseEditor(ABC):
    """Abstract base for document editors."""

    @abstractmethod
    def apply_revision(
        self,
        content: str,
        revision: RevisionItem
    ) -> tuple[str, Optional[ChangeRecord]]:
        """
        Apply a single revision to document content.

        Returns:
            Tuple of (new_content, change_record)
            change_record is None if revision was not applied
        """
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

    def apply_revision(
        self,
        content: str,
        revision: RevisionItem
    ) -> tuple[str, Optional[ChangeRecord]]:
        """
        Apply revision to markdown content with validation.

        Args:
            content: Original document content
            revision: Revision to apply

        Returns:
            Tuple of (modified_content, change_record)
            change_record is None if revision could not be applied
        """
        try:
            before_content = content

            if revision.action == RevisionAction.DELETE:
                new_content = self._delete_content(content, revision)
            elif revision.action == RevisionAction.INSERT:
                pos = self.find_target_location(content, revision)
                new_content = self._insert_content(content, revision.content, pos)
            elif revision.action == RevisionAction.UPDATE:
                new_content = self._update_content(content, revision, self.find_target_location(content, revision))
            else:
                logger.warning(f"Unknown action {revision.action}, skipping")
                return content, None

            # Validate result is not empty
            if not new_content or not new_content.strip():
                logger.warning(f"Revision {revision.id} resulted in empty content, skipping")
                return content, None

            # Extract the actual change for review
            before_text = self._extract_changed_text(before_content, new_content, revision, is_before=True)
            after_text = self._extract_changed_text(before_content, new_content, revision, is_before=False)

            change_record = ChangeRecord(
                revision_id=revision.id,
                section=revision.section,
                action=revision.action.value,
                before=before_text,
                after=after_text,
                line_number=None  # Could be enhanced to track line numbers
            )

            return new_content, change_record

        except Exception as e:
            logger.error(f"Failed to apply revision {revision.id}: {e}")
            return content, None  # Return original on error

    def _extract_changed_text(
        self,
        before_content: str,
        after_content: str,
        revision: RevisionItem,
        is_before: bool
    ) -> str:
        """
        Extract the relevant changed text for review.

        For INSERT: returns the inserted content (after)
        For DELETE: returns the deleted content (before)
        For UPDATE: returns context showing the change
        """
        if revision.action == RevisionAction.INSERT:
            return revision.content if is_before else ""  # Empty before, full content after
        elif revision.action == RevisionAction.DELETE:
            return revision.content if not is_before else ""  # Full content before, empty after
        else:  # UPDATE
            # Try to find and show the relevant section
            section = self.find_section(before_content, revision.section)
            if section:
                start, end = section
                return before_content[start:end] if is_before else after_content[start:end]
            return revision.content


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

    def apply_revision(
        self,
        content: str,
        revision: RevisionItem
    ) -> tuple[str, Optional[ChangeRecord]]:
        """Apply revision to text content."""
        pos = self.find_target_location(content, revision)
        before_content = content
        new_content = content
        before_text = ""
        after_text = ""

        if revision.action == RevisionAction.DELETE:
            # Find and remove line containing keyword
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if revision.section.lower() in line.lower():
                    before_text = line
                    lines.pop(i)
                    break
            new_content = '\n'.join(lines)
            after_text = ""

        elif revision.action == RevisionAction.INSERT:
            before_text = ""
            after_text = revision.content
            new_content = content[:pos] + revision.content + '\n' + content[pos:]

        elif revision.action == RevisionAction.UPDATE:
            # Find line with keyword and replace
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if revision.section.lower() in line.lower():
                    before_text = line
                    lines[i] = revision.content
                    after_text = revision.content
                    break
            new_content = '\n'.join(lines)

        change_record = ChangeRecord(
            revision_id=revision.id,
            section=revision.section,
            action=revision.action.value,
            before=before_text,
            after=after_text
        )

        return new_content, change_record


class DocxEditor(BaseEditor):
    """
    Editor for Word .docx files with paragraph-based editing.

    Uses python-docx library to read and modify Word documents.
    """

    def __init__(self):
        """Initialize DOCX editor."""
        self.doc = None
        self.file_path = None

    def load_document(self, file_path: Path) -> None:
        """Load DOCX document from file."""
        self.file_path = file_path
        self.doc = Document(str(file_path))

    def save_document(self, file_path: Path) -> None:
        """Save DOCX document to file."""
        self.doc.save(str(file_path))

    def get_text_content(self) -> str:
        """Extract all text content from document."""
        text_parts = []
        for para in self.doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return '\n'.join(text_parts)

    def find_target_paragraph(self, revision: RevisionItem) -> Optional[int]:
        """
        Find the paragraph index that best matches the revision section.

        Args:
            revision: Revision with section reference

        Returns:
            Paragraph index or None if no match found
        """
        if not self.doc:
            return None

        keywords = [revision.section]
        if revision.context:
            keywords.append(revision.context)

        # Search for best matching paragraph
        best_idx = None
        best_score = 0.0

        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.lower()
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text:
                    # Calculate score based on position of match
                    score = 1.0
                    if text.startswith(keyword_lower):
                        score = 1.0
                    elif keyword_lower in text:
                        score = 0.7

                    if score > best_score:
                        best_score = score
                        best_idx = i

        return best_idx

    def find_target_location(self, content: str, revision: RevisionItem) -> int:
        """Find character position (not used for DOCX)."""
        return 0

    def apply_revision(
        self,
        content: str,
        revision: RevisionItem
    ) -> tuple[str, Optional[ChangeRecord]]:
        """
        Apply revision to DOCX document.

        Note: For DOCX, this modifies the document object directly.
        The content parameter is ignored.

        Args:
            content: Ignored for DOCX (uses document object)
            revision: Revision to apply

        Returns:
            Tuple of (original_content, change_record)
            DOCX modifications are in-place on the document object
        """
        if not self.doc:
            logger.error("Document not loaded")
            return content, None

        target_idx = self.find_target_paragraph(revision)

        # Get before/after text for change record
        before_text = ""
        after_text = ""

        if target_idx is not None and target_idx < len(self.doc.paragraphs):
            before_text = self.doc.paragraphs[target_idx].text

        if revision.action == RevisionAction.INSERT:
            self._insert_paragraph(revision, target_idx)
            after_text = revision.content

        elif revision.action == RevisionAction.UPDATE:
            self._update_paragraph(revision, target_idx)
            after_text = revision.content

        elif revision.action == RevisionAction.DELETE:
            self._delete_paragraph(revision, target_idx)
            after_text = ""  # Empty after delete

        change_record = ChangeRecord(
            revision_id=revision.id,
            section=revision.section,
            action=revision.action.value,
            before=before_text,
            after=after_text
        )

        return content, change_record

    def _insert_paragraph(self, revision: RevisionItem, target_idx: Optional[int]) -> None:
        """Insert a new paragraph with revision content."""
        new_para = self.doc.add_paragraph(revision.content)

        if target_idx is not None and target_idx + 1 < len(self.doc.paragraphs):
            # Move new paragraph to after target
            target_para = self.doc.paragraphs[target_idx + 1]
            target_para._element.addprevious(new_para._element)

    def _update_paragraph(self, revision: RevisionItem, target_idx: Optional[int]) -> None:
        """Update paragraph with revision content."""
        if target_idx is not None:
            para = self.doc.paragraphs[target_idx]
            para.text = revision.content
        else:
            # Add new paragraph if no match found
            self.doc.add_paragraph(revision.content)

    def _delete_paragraph(self, revision: RevisionItem, target_idx: Optional[int]) -> None:
        """Delete paragraph that matches revision content."""
        if target_idx is not None:
            # Remove paragraph by clearing its content
            para = self.doc.paragraphs[target_idx]
            p = para._element
            p.getparent().remove(p)
        else:
            logger.warning(f"Could not find target paragraph for deletion: {revision.content}")


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
    elif doc_type == DocumentType.DOCX:
        return DocxEditor()
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
