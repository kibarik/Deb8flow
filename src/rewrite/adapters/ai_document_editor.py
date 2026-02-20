"""
AI-powered document editor using LLM for intelligent content improvement.

This editor uses LLM to intelligently rewrite document sections
based on recommendations, rather than mechanical text replacement.
"""
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..domain.entities import RevisionItem
from ..domain.value_objects import DocumentType, RevisionAction
from ..domain.change_record import ChangeRecord


logger = logging.getLogger(__name__)


@dataclass
class AIEditConfig:
    """Configuration for AI document editing."""
    model: str = "gpt-4o"
    temperature: float = 0.3  # Lower for more consistent rewrites
    max_tokens: int = 2000
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class AIDocumentEditor:
    """
    AI-powered document editor using LLM.

    Processes document sections through LLM to intelligently
    incorporate recommendations while improving quality.
    """

    def __init__(
        self,
        config: Optional[AIEditConfig] = None,
        prompt_template_path: Optional[Path] = None
    ):
        """
        Initialize AI document editor.

        Args:
            config: AI editing configuration
            prompt_template_path: Path to prompt template (default: built-in)
        """
        self.config = config or AIEditConfig()
        self.prompt_template = self._load_prompt_template(prompt_template_path)

        # Initialize LLM
        llm_kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if self.config.api_key:
            llm_kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            llm_kwargs["base_url"] = self.config.base_url

        self.llm = ChatOpenAI(**llm_kwargs)

    def _load_prompt_template(self, path: Optional[Path]) -> str:
        """Load prompt template from file or use default."""
        if path and path.exists():
            return path.read_text(encoding="utf-8")

        # Use built-in template
        default_path = Path(__file__).parent.parent.parent.parent / "src" / "prompts" / "rewrite" / "section_rewrite.md"
        if default_path.exists():
            return default_path.read_text(encoding="utf-8")

        # Fallback template
        return """Rewrite the following document section based on recommendations:

## Original Section
{original_section}

## Section Name
{section_name}

## Recommendations
{recommendations}

Rewrite the section incorporating all recommendations. Output only the rewritten content."""

    async def rewrite_section(
        self,
        section_name: str,
        original_content: str,
        recommendations: List[str]
    ) -> Tuple[str, Optional[ChangeRecord]]:
        """
        Rewrite a section using AI based on recommendations.

        Args:
            section_name: Name of the section to rewrite
            original_content: Original section content
            recommendations: List of recommendations to apply

        Returns:
            Tuple of (new_content, change_record)
        """
        if not recommendations:
            return original_content, None

        # Build prompt
        prompt = self.prompt_template.format(
            original_section=original_content,
            section_name=section_name,
            recommendations="\n".join(f"- {r}" for r in recommendations)
        )

        try:
            # Call LLM
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert technical document editor."),
                HumanMessage(content=prompt)
            ])

            new_content = response.content.strip()

            # Create change record
            change_record = ChangeRecord(
                revision_id="AI_REWRITE",
                section=section_name,
                action="UPDATE",
                before=original_content,
                after=new_content
            )

            logger.info(f"AI rewrote section '{section_name}' ({len(original_content)} -> {len(new_content)} chars)")
            return new_content, change_record

        except Exception as e:
            logger.error(f"AI rewrite failed for section '{section_name}': {e}")
            return original_content, None

    def group_revisions_by_section(
        self,
        revisions: List[RevisionItem]
    ) -> dict[str, List[str]]:
        """
        Group revisions by section for batch processing.

        Args:
            revisions: List of revision items

        Returns:
            Dict mapping section names to lists of recommendations
        """
        sections: dict[str, List[str]] = {}

        for revision in revisions:
            if revision.section not in sections:
                sections[revision.section] = []
            sections[revision.section].append(revision.content)

        return sections


class AIMarkdownEditor:
    """
    AI-powered markdown editor with section-based intelligent rewriting.

    Parses markdown into sections and rewrites each section using LLM
    based on accumulated recommendations.
    """

    # Header patterns
    SECTION_PATTERN = r'^(#{1,6})\s+(.+)$'

    def __init__(self, ai_config: Optional[AIEditConfig] = None):
        """
        Initialize AI markdown editor.

        Args:
            ai_config: AI editing configuration
        """
        from .document_editor import MarkdownEditor
        self.base_editor = MarkdownEditor()
        self.ai_editor = AIDocumentEditor(config=ai_config)

    def find_section(
        self,
        content: str,
        section_name: str
    ) -> Optional[Tuple[int, int, str]]:
        """
        Find a section by name with fuzzy matching.

        Args:
            content: Full document content
            section_name: Name of section to find

        Returns:
            Tuple of (start_pos, end_pos, section_content) or None
        """
        section_range = self.base_editor.find_section(content, section_name)
        if section_range:
            start, end = section_range
            return start, end, content[start:end]
        return None

    async def apply_revision(
        self,
        content: str,
        revision: RevisionItem
    ) -> tuple[str, Optional[ChangeRecord]]:
        """
        Apply a revision using AI-powered rewriting.

        For now, accumulates revisions for batch processing.
        Call `apply_all_revisions` for actual AI rewriting.

        Args:
            content: Full document content
            revision: Revision to apply

        Returns:
            Tuple of (content, change_record)
        """
        # For individual revisions, defer to batch processing
        # This is a placeholder - actual work happens in apply_all_revisions
        return content, None

    async def apply_all_revisions(
        self,
        content: str,
        revisions: List[RevisionItem]
    ) -> Tuple[str, List[ChangeRecord]]:
        """
        Apply all revisions using AI-powered section rewriting.

        Args:
            content: Full document content
            revisions: List of revisions to apply

        Returns:
            Tuple of (new_content, list_of_change_records)
        """
        import re

        # Group revisions by section
        section_revisions = self.ai_editor.group_revisions_by_section(revisions)

        if not section_revisions:
            return content, []

        # If sections don't match document structure, apply to entire document
        # Check if any section matches a document heading
        sections = self._parse_sections(content)
        section_names = {title for _, title, _, _ in sections}

        # Find matching sections
        matched_sections = {}
        unmatched_sections = {}

        for section_name, recommendations in section_revisions.items():
            matching_doc_section = self._find_matching_section(section_name, section_names)
            if matching_doc_section:
                matched_sections[matching_doc_section] = recommendations
            else:
                unmatched_sections[section_name] = recommendations

        # If we have unmatched sections, apply all recommendations to entire document
        if unmatched_sections and not matched_sections:
            logger.info("No matching document sections found, applying AI rewrite to entire document")
            return await self._rewrite_entire_document(content, revisions)

        # Process matched sections
        changes: List[ChangeRecord] = []
        new_content_parts = []

        for section_name, recommendations in matched_sections.items():
            section_info = self._find_section_info_by_name(sections, section_name)
            if not section_info:
                continue

            level, title, start, end = section_info
            original_section_content = content[start:end]

            # Rewrite section using AI
            new_section_content, change_record = await self.ai_editor.rewrite_section(
                section_name=title,
                original_content=original_section_content,
                recommendations=recommendations
            )

            if change_record:
                changes.append(change_record)
                new_content_parts.append((start, end, new_section_content))

        # Build new content
        if not new_content_parts:
            return content, []

        # Sort by start position and apply replacements
        new_content_parts.sort(key=lambda x: x[0])
        result = content
        offset = 0

        for start, end, new_section in new_content_parts:
            adj_start = start + offset
            adj_end = end + offset

            result = result[:adj_start] + new_section + result[adj_end:]
            offset += len(new_section) - (end - start)

        return result, changes

    async def _rewrite_entire_document(
        self,
        content: str,
        revisions: List[RevisionItem]
    ) -> Tuple[str, List[ChangeRecord]]:
        """
        Rewrite entire document using AI with all recommendations.

        Args:
            content: Full document content
            revisions: List of revisions to apply

        Returns:
            Tuple of (new_content, change_record)
        """
        # Collect all recommendations
        all_recommendations = [rev.content for rev in revisions]

        # Rewrite entire document
        try:
            new_content, change_record = await self.ai_editor.rewrite_section(
                section_name="Весь документ",
                original_content=content,
                recommendations=all_recommendations
            )

            if change_record and new_content and new_content.strip():
                return new_content, [change_record]
            else:
                logger.warning("AI rewrite produced no changes, returning original content")
                return content, []
        except Exception as e:
            logger.error(f"AI rewrite failed: {e}")
            # Return original content on error
            return content, []

    def _find_matching_section(self, revision_section: str, document_sections: set) -> Optional[str]:
        """
        Find matching document section for revision section.

        Args:
            revision_section: Section name from revision
            document_sections: Set of document section names

        Returns:
            Matching section name or None
        """
        # Direct match
        if revision_section in document_sections:
            return revision_section

        # Case-insensitive match
        for doc_section in document_sections:
            if revision_section.lower() == doc_section.lower():
                return doc_section

        # Partial match
        for doc_section in document_sections:
            if revision_section.lower() in doc_section.lower() or doc_section.lower() in revision_section.lower():
                return doc_section

        return None

    def _find_section_info_by_name(
        self,
        sections: List[Tuple[str, str, int, int]],
        section_name: str
    ) -> Optional[Tuple[str, str, int, int]]:
        """Find section info by exact name match."""
        for level, title, start, end in sections:
            if title.lower() == section_name.lower():
                return level, title, start, end
        return None

    def _parse_sections(
        self,
        content: str
    ) -> List[Tuple[str, str, int, int]]:
        """
        Parse markdown content into sections.

        Returns list of (level, title, start_pos, end_pos).
        """
        sections = []
        pattern = re.compile(self.SECTION_PATTERN, re.MULTILINE)
        matches = list(pattern.finditer(content))

        if not matches:
            return [("0", "root", 0, len(content))]

        # Add section from start to first header
        if matches[0].start() > 0:
            sections.append(("0", "root", 0, matches[0].start()))

        # Add each section
        for i, match in enumerate(matches):
            level, title = match.groups()
            start = match.end() + 1  # Start after header line
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections.append((str(len(level)), title.strip(), start, end))

        return sections

    def _find_section_info(
        self,
        sections: List[Tuple[str, str, int, int]],
        section_name: str
    ) -> Optional[Tuple[str, str, int, int]]:
        """Find section info by name with fuzzy matching."""
        for level, title, start, end in sections:
            if section_name.lower() in title.lower() or title.lower() in section_name.lower():
                return level, title, start, end
        return None
